# Cortex

**An AI coding agent that remembers your repository investigation — across sessions, not just within one.**

Built for the WeMakeDevs × Cognee Hackathon — *The Hangover Part AI: Where's My Context?*

---

## The Problem

Every time an AI coding assistant starts a new session, it starts from zero. Contributors on large open-source codebases re-explain architecture, re-trace execution paths, and re-discover the same implementation details every single conversation — because nothing persists between sessions.

Cortex fixes that by giving the agent a persistent, queryable memory of everything it has ever explored in your repository.

---

## How It Works

Every query follows the same loop: **check memory first, explore only if needed, learn from what you find.**

```mermaid
flowchart TD
    A[Developer Query] --> B[Gemini: Understand Intent]
    B --> C{Choose Retrieval Mode}
    C -->|Default| D[cognee_query: default]
    C -->|Relational| E[cognee_query: triplet]
    D --> F{Memory Sufficient?}
    E --> F
    F -->|Yes| G[Generate Response]
    F -->|No| H[search_repo tool]
    H --> I{Choose Search Mode}
    I -->|Known symbol| J[AST mode]
    I -->|Unknown/partial| K[Grep mode]
    J --> L[Discover New Knowledge]
    K --> L
    L --> M[cognee remember:<br/>ingest into memory]
    M --> G
    G --> N[Response to Developer]

    style D fill:#4a4a8a,stroke:#333,color:#fff
    style E fill:#4a4a8a,stroke:#333,color:#fff
    style M fill:#4a4a8a,stroke:#333,color:#fff
    style C fill:#8a6a2a,stroke:#333,color:#fff
    style I fill:#8a6a2a,stroke:#333,color:#fff
    style F fill:#8a6a2a,stroke:#333,color:#fff
```

1. **Memory first.** Gemini queries Cognee before touching the repository — `default` mode for direct facts, `triplet` mode when the question is relational ("how does this connect to the auth flow we explored earlier?").
2. **Explore only on a miss.** If memory doesn't have the answer, Cortex searches the actual repo using `search_repo`, in either `AST` mode (known symbols — functions, classes, definitions) or `grep` mode (partial snippets, log lines, unknown identifiers).
3. **Learn automatically.** Whatever gets discovered — file content and folder structure, stored as separate linked facts — is written back into Cognee's knowledge graph. The next query, next session, next contributor benefits from it.

The repository's code stays in Git. The *understanding* of the repository lives in Cognee.

---
## Why Cognee (Not a Vector Store)

Cortex needed two different kinds of retrieval, and a plain vector database only gives you one of them.

- **Direct facts** ("where is `authenticate_user` implemented") are a similarity-search problem — a vector store handles this fine.
- **Relational questions** ("how does this connect to the auth flow we explored earlier") aren't. Similarity search returns *similar* chunks, not *connected* ones — it can't tell you that two pieces of code are linked unless their embeddings happen to be close, which they often aren't.

That's why `cognee_query` has a `triplet` mode: Cognee's knowledge graph lets Cortex traverse actual relationships between explored facts — this file calls that function, this function was discovered while investigating that bug — instead of guessing from vector distance. A vector-only setup would've forced every query into "find similar text," even the ones that were fundamentally about *connections*, not *similarity*.

We also split ingestion into two datasets — `repo_name` for code structure and `{repo_name}_memory` for reasoning/conversation history — so the graph keeps "what the code is" separate from "what we learned about it." That distinction only matters if the underlying store can represent structured relationships in the first place.

## Why This Matters

> **Day 1** — "Where is `authenticate_user` implemented?" → Cortex explores, stores the authentication architecture.
> **Day 3** — "How does refresh token validation work?" → Cortex already knows the auth flow, explores only the missing piece.
> **Day 7** — "Continue our authentication investigation." → Cortex picks up exactly where it left off — no re-explaining, no re-exploring.

This is the actual problem open-source contributors face on large codebases: not a lack of AI assistance, but AI assistance with no memory of the last conversation.

---

## Stack

- **Orchestration:** Gemini function calling (`gemini-2.5-flash-lite`)
- **Memory:** Cognee — `remember` / `recall` (default + triplet modes)
- **Repository search:** `search_repo` — AST and grep modes
- **Output:** Structured `CortexResponse` schema on every call

---

## Engineering Notes

Building on Cognee 1.0 during an active development cycle meant debugging the memory layer itself, not just calling it:

- **`add_data_points`-only ingestion silently failed.** `GRAPH_COMPLETION` was returning `None` because writing via `add_data_points` alone never populated the vector store — data existed in the graph but wasn't retrievable. Fixed by routing ingestion through `remember()` instead.
- **`DatabaseNotCreatedError` / 403 `PermissionDeniedError`.** Traced to `ENABLE_BACKEND_ACCESS_CONTROL` — without setting it to `false`, Cognee's access control blocks dataset reads/writes in a way that looks like a memory bug, not a config issue.
- **Rejected `only_context=True` on `recall()`.** It returns raw, unstructured context dumps that the orchestration layer can't reliably parse — we kept structured retrieval through `CortexResponse` instead, even though the raw-context path looked like a shortcut early on.
- **Custom `DataPoint` schema abandoned.** An early attempt to define a custom schema for file content never actually embedded — content was stored but invisible to retrieval. Switched to separate `remember()` calls for file content and folder structure instead.

**Scoped out:** GitHub integration (PR/issue-linked memory) was cut to keep the core memory loop — the actual thing being judged — stable and fully tested, rather than shipping a second, half-working feature.

---

## Demo

*(video link here)*

---

## Run Locally

```bash
git clone <repo-url>
cd cortex
pip install -r requirements.txt
cp .env.example .env   # fill in the values below
python function_calling.py
```

### .env Structure

```bash
# Gemini — orchestration / function calling
GEMINI_API_KEY=

# Cognee — LLM used internally for cognify / GRAPH_COMPLETION
LLM_API_KEY=
LLM_PROVIDER=
LLM_MODEL=

# Cognee — embeddings
EMBEDDING_API_KEY=
EMBEDDING_PROVIDER=
EMBEDDING_MODEL=

# Required — without this, dataset creation and access will fail
ENABLE_BACKEND_ACCESS_CONTROL=false
```

`ENABLE_BACKEND_ACCESS_CONTROL=false` is required. Without it, Cognee's dataset access control blocks reads/writes in a way that's easy to misdiagnose as a memory or ingestion bug.
