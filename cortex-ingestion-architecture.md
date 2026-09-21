# Cortex Ingestion Pipeline — Architecture

## 1. Core principle

Store what matters, not everything. "Matters" = touched by agent activity: a file
gets read, edited, searched, or reasoned about. Full-repo upfront sweeps are
rejected — they collapse on large repos (memory, batch-failure blast radius,
time-to-first-usable-query) and index a mass of code nobody will ever query
(vendored deps, generated code, dead subtrees).

The one gap in pure lazy ingestion — semantic search can't find code nobody has
touched yet — is fixed at the **search layer**, not by pre-populating everything.
See §4.

## 2. Node types and creation triggers

| Node | Trigger | Notes |
|---|---|---|
| `Directory` | Parent dir of any file being ingested | Dedup: `path` (drop redundant `repo_name` if paths are already unique per repo) |
| `File` | Agent opens/reads/edits it, or a grep/AST hit lands in it | Needs `content_hash` field (not in original schema — add it) for staleness checks and incremental reindex |
| `Class` | AST walk of an ingested file | Dedup: `name` + `file_path` |
| `Function` | AST walk of an ingested file | Dedup: `name` + `file_path`. `access_count` increments on each graph hit |
| `Session` | Every agent query | Dedup: `session_id` (surrogate) |
| `ReasoningNode` | Agent reasoning step | **Fix applied:** dedup must include `session_id`, not `intent` alone — free-text `intent` alone collapses reasoning across unrelated sessions |
| `ErrorResolutionNode` | Error occurs during a session | Dedup: `session_id` + `function_name` + `error_type` |
| `Blocker` | Blocker identified during a session | Dedup on free text is fragile both directions (see thread) — accept the limitation or add a resolution step later; not fully solved |

All nodes inherit a `DataPoint` base that auto-computes a synthetic `id` (sha256
hash, truncated) from whichever fields are marked `Annotated[..., Dedup()]`. This
`id` is the join key used identically in Kuzu (as `PRIMARY KEY`) and LanceDB (as
the `merge_insert` match column) — computed once, in the model, never
independently in two places.

## 3. Edge types and resolution

Edges are a **separate base class (`Edge`), not `DataPoint`** — they don't need
dedup-hash identity, they need `source_id` / `target_id` resolved from already-
built node `id`s. Never embed the full nested node object inside an edge; that
duplicates and desyncs data that already lives on the node.

Edge Python classes stay granular (`FunctionCallsFunction`, `ClassCallsFunction`,
etc.) because you need the specific node-type pair to pick the right `MATCH`
labels at write time. Their Cypher relationship label collapses to the shared
semantic name (`CALLS`, `CONTAINS`, `ASKED_ABOUT`, `REFERENCES`, `BLOCKS`,
`IMPORTS`) via a `rel_label: ClassVar[str]` on each subclass — one Kuzu
`REL TABLE` can hold multiple FROM/TO type pairs under one label.

**Two-pass rule, non-negotiable:** all nodes for a batch must exist before any
edge in that batch is written. `MERGE ... MATCH (a)...(b)` fails silently
(zero rows, no error) if either endpoint doesn't exist yet. This applies across
the whole batch being ingested, not just within one file.

**Unresolved references at edge-write time** (e.g. `Function.calls` holds names,
not ids; a call target's file isn't known yet): build a name→id map after the
node pass, or fall back to two options for incremental/live ingestion:
1. Queue the edge, retry once the target is ingested.
2. Create a placeholder stub node immediately (`MERGE` handles empty-property
   stubs fine), fill it in when the real file is ingested.

Pick one before building the incremental path — not decided yet as of this doc.

## 4. Search routing

`SearchTool` no longer triggers ingestion as a side effect of matching — that
coupling was the original bug (semantic search blind to anything never grepped).

**Per-file freshness check**, using `File.content_hash`:

```
current_hash = hash(file on disk)
stored_hash  = graph's File.content_hash for that path
match  -> serve from graph (Kuzu + LanceDB), no reparse
missing/mismatch -> live AST/grep on that file, serve result,
                     kick off background ingestion for it
```

This routing is mechanical (hash comparison), not agent/LLM judgment calls.

**Search-miss handling (the semantic-blindness fix):** if a semantic query
returns nothing above similarity threshold, don't just report "not found" —
run a scoped live grep/AST fallback (current working directory, imports of
known files, or query terms as a grep pattern) and ingest whatever that
touches. This bounds the ingestion cost to what one query's fallback actually
finds, not the whole repo.

**What AST/grep remain permanently responsible for**, even post-ingestion:
- Arbitrary substring/text matches not captured as a node property (a TODO
  comment, an exact string literal).
- Structural patterns not modeled in the schema (e.g. "every function with a
  bare `except:`") — extending the schema for every conceivable query is
  unbounded; grep is the intended fallback for the long tail.
- The live-filesystem ground truth during the gap between an edit and its
  re-ingestion.

## 5. Cost controls (embedding, since that's the actual concern — not LLM summarization)

1. **Don't embed trivial functions.** Skip getters/wrappers/short bodies with no
   docstring; exact name/graph lookup already covers them. This is the highest-
   leverage cut — boilerplate is usually the majority of functions by count.
2. **Dedup by content hash before embedding** — identical/near-identical bodies
   (copy-paste, generated code) reuse one vector instead of paying twice.
3. **Batch embedding calls** — don't loop one call per function; send lists.
4. **Truncate long bodies** fed to the embedder (signature + docstring + first
   N lines) rather than full multi-hundred-line bodies.
5. **Consider a smaller/code-specific embedding model** as a swap once 1–4 are
   in place, not before — measure first.

(Separately, if LLM-based `body_summary` generation is ever added on top of raw-
text embedding: gate it behind a complexity/no-docstring threshold, batch
requests, and use a cheap model — but this is a different cost center from
embedding and wasn't the one flagged as the actual concern.)

## 6. Version 1 scope (locked)

Build only this first. Everything in §7 stays deferred until this works end to end:

1. Code graph (`File`/`Class`/`Function`/`CALLS`/`CONTAINS`), lazily ingested on
   agent access (read/edit/search) — not a full-repo sweep. This part is settled;
   do not revisit the sweep-vs-lazy question again without new evidence from
   actually running v1.
2. `ReasoningNode` from agent activity only, triggered by concrete events (fix-
   follows-error, blocker-resolved) — no git-commit-derived source yet.
3. No embedding cost tuning, no commit-insight pipeline, no stub/queue
   resolution strategy for unresolved call edges. Accept dangling or skipped
   edges for now. Let real usage surface which gap actually matters before
   building a fix for it.

## 6a. ReasoningNode source tagging (decided, not yet built)

Two sources exist and must never be merged into one undifferentiated pool:

- **Agent reasoning** — real, actually happened, irreplaceable once the session
  ends. This is the source v1 builds.
- **Git-commit LLM insight** — an LLM's guess at why a diff is an improvement,
  generated from the diff + commit message. This is *inferred*, not *stated* —
  when the commit message itself contains no real explanation, the LLM
  fabricates a plausible-sounding "why" that is indistinguishable from a real
  captured decision once stored. Deferred out of v1 (see §7); if built later,
  it must carry a `source: "git_llm"` field (or be a distinct node type
  entirely) so nothing downstream treats it as equivalent to real captured
  reasoning.

Rationale for deferring the git-commit source rather than building it now: it's
regenerable on demand from the diff at any time by any agent, so it doesn't need
upfront ingestion cost the way agent reasoning does (agent reasoning is lost the
moment the session ends; commit insight is not). If built at all, it's a
candidate for an on-demand `explain_commit(sha)` tool outside the persistent
graph, not a pipeline that fires an LLM call on every commit regardless of
whether anyone ever asks about it.

## 7. Open items / not yet decided


- `Blocker` dedup on free-text `description` is acknowledged fragile in both
  directions (over-merges within a session, under-merges across sessions) —
  no fix chosen yet.
- Call/method reference resolution strategy (queue-and-retry vs. stub node) —
  not chosen yet, needs deciding before the incremental path is built.
- `content_hash` field needs to be formally added to the `File` model — it's
  relied on in §4 but wasn't in the original schema draft.
- Directory/subtree-scoped ingestion boundaries (e.g. skip vendored deps by
  default) — mentioned as a mitigation, not designed in detail.
  - Git-commit LLM insight source: noise filtering for low-content commit
  messages, whether to pull PR descriptions/linked issues in addition to
  `git log`, and whether it's built as part of this pipeline at all versus a
  separate on-demand tool (see §6a). Explicitly out of v1 scope.
