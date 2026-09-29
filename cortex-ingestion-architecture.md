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

## Retrieval Layer — Design Decisions

### traverse()
- Multi-label edge syntax in Kuzu requires a colon before every label after the first: `EDGE1|:EDGE2|:EDGE3`, not `EDGE1|EDGE2|EDGE3`. Same bug existed in `get_directory_tree`'s `CONTAINMENT_EDGES` join — both fixed.
- `traverse()` requires an explicit `expected_type` argument (the calling node's type) rather than looking it up itself. Reason: Kuzu allows untyped node patterns (`(a {id: $id})` with no label), so nothing stops a caller from passing a mismatched node_id/edge_label pair — it would silently return an empty list instead of erroring. `expected_type` is checked against `REL_TABLES[edge_label]` in plain Python before any query runs, so a caller mistake fails loud and fast, before touching Kuzu.
- Callers always have the type available already, since anything upstream of `traverse()` (e.g. `get_relations`) works from `ExtractionResult` objects that already carry a fully reconstructed, typed `DataPoint`. No caller ever has a bare untyped id.

### get_relations()
- For most node types: return lightweight relation info only — edge label, target type, target identifying field (name/path) — not full target content. Avoids pulling full content for every relation of every top-k hit, which would balloon token usage fast.
- Exception: `ReasoningNode` hits get full connected content (`Blocker`/`ErrorResolutionNode`) via `traverse()`, not the lightweight path. Reasoning content without its resolution is incomplete on its own.
- Batched in one Kuzu query across all non-reasoning-node ids at once (not one query per hit), same batching principle as `get_directory_tree`.

### query_memory() (agent-facing tool)
- Orchestrates: embed query → `semantic_extract` (top-k) → `get_relations` → merge into flat context list → return.
- LLM-facing signature is `query_text` + `top_k` only. DB connections and `embed_texts` are pulled via module-level getters/imports inside the function body, never passed as tool parameters, since the LLM can't and shouldn't populate infra objects.
- Repo/dataset scoping (`get_kuzu_connection()`, `get_lancedb_connection()`) is currently unscoped/single-repo. Deliberately deferred — to be addressed when multi-repo support is actually built.

### Function.calls resolution
- `Function.calls` stores callee **names**, not ids, by design.
- Resolving a call chain (e.g. "how is auth implemented" → main function → helper) means the agent issues a **second** `query_memory` call using the callee name plus surrounding context (not just the bare name in isolation).
- This works because embeddings are built from each function's own content (docstring/body), so two same-named functions in different contexts (e.g. admin `verify_token` vs user `verify_token`) still resolve correctly when the follow-up query includes context, not just the identifier. Semantic search disambiguates on content, not on name uniqueness.
- Multi-hop resolution via repeated tool calls is treated as normal agent behavior, not a design flaw.

### Retrieval routing: graph hit vs fallback
- If the target already has a node in the graph (ingested), semantic search returns it directly — the node carries its own `file_path`.
- If not yet ingested (stale graph, or genuinely unindexed), fallback is structural exploration: read directory structure, use naming/path conventions to guess likely files, open and read directly. Same approach a coding agent uses without an index.
- This makes **ingestion freshness** the critical dependency for the whole routing decision — a stale graph produces false negatives (looks like "not in codebase" when it's just "not yet indexed"), not a clean signal to fall back. A last-ingested timestamp or git-hook-triggered re-ingest is needed to distinguish "genuinely absent" from "just stale," and is the most important unresolved piece for this system to be trustworthy.

### Known typo fixes (already applied)
- `RowReconstructionErrror` → corrected.
- `HeirarchyExtractionError` → corrected.

### Rate limiting / retry (Gemini API calls)
- Free tier: 5 RPM ceiling on the strongest Flash model, 250K TPM (TPM is not the bottleneck, RPM is).
- Design choice: Cortex ships using whatever tier the running user's own API key has. No RPM handling baked in as a permanent constraint, since a paid-tier user hits no ceiling. Free-tier users (including dev/testing) hit the same limits Cortex's own logic can smooth over, not eliminate.
- Retry strategy: exponential backoff with jitter, not a fixed wait. Fixed delays either overpay when a rate limit clears fast, or underpay when it doesn't clear and needs a longer wait. Backoff (e.g. 2s → 4s → 8s → 16s, plus random jitter) adapts to both cases and avoids retry collisions if multiple calls are in flight.
- Capped retry count (e.g. 5 attempts) — no infinite retry loop. On exhaustion, raise a real error (`QueryMemoryError` or similar) rather than hanging silently inside the agent loop.
- Applied narrowly: wraps only the actual network call site (the Gemini request itself), not the surrounding function, so already-succeeded work (semantic search, graph traversal) doesn't get needlessly retried alongside a failed API call.