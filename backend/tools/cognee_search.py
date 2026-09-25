from dotenv import load_dotenv
load_dotenv()
from backend.exceptions import QueryMemoryError
from backend.memory.ingestion.generate_embeddings import embed_texts
from backend.logger.logger_setup import logger_setup
logger = logger_setup()
from fastapi import HTTPException
from backend.memory.extraction.sematic_extract import semantic_extract
from backend.memory.extraction.hierarchy import get_directory_tree
from backend.memory.extraction.structural import get_relations
from backend.memory.db.datapoints import ExtractionResult
from backend.memory.db import get_kuzu_connection, get_lancedb_connection
# repo_name
# dataset_name=repo_name
# dataset_name=repo_name
def query_memory(
    query_text: str,
    
    
    top_k: int = 10,
) -> list[dict]:
    """
    Orchestrator tool exposed to the agent. Given a raw query, returns a merged
    context bundle: each hit's own content plus its relation info (lightweight
    edge/target for normal nodes, full content for ReasoningNode hits).
    """
    lancedb_table,kuzu_conn = get_lancedb_connection(), get_kuzu_connection()
    try:
        query_vector = embed_texts([query_text])[0]
    except Exception as e:
        raise QueryMemoryError(f"Failed to embed query '{query_text}': {e}") from e

    hits = semantic_extract(query_vector, lancedb_table, kuzu_conn, top_k=top_k)

    if not hits:
        return []

    relations = get_relations(kuzu_conn, hits)

    context = []
    for hit in hits:
        node = hit.node
        context.append({
            "id": node.id,
            "type": type(node).__name__,
            "content": node.model_dump(),
            "score": hit.score,
            "matched_via": hit.matched_via,
            "relations": relations.get(node.id, []),
        })

    return context