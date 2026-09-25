from backend.memory.db.datapoints import ExtractionResult
from backend.memory.extraction.structural import _reconstruct
from backend.exceptions import LanceDBQueryError


def semantic_extract(query_vector: list[float], lancedb_table, kuzu_conn, top_k: int = 10) -> list[ExtractionResult]:
    try:
        hits = lancedb_table.search(query_vector).limit(top_k).to_list()

    except Exception as e:
        raise LanceDBQueryError(f"Failed to search LanceDB table {lancedb_table.name}: {e}")

    results = []
    for hit in hits:
        query = f"MATCH (n:{hit['node_type']} {{id: $id}}) RETURN n, labels(n)"
        response = kuzu_conn.execute(query, {"id": hit["id"]})
        rows = response.rows_as_dict().get_all()
        if not rows:
            continue  # LanceDB has the vector but Kuzu node is gone — stale entry, don't crash on it
        try:
            results.append(ExtractionResult(
                node=_reconstruct(rows[0], node_key="n"),
                score=hit.get("_distance"),
                matched_via="semantic"
            ))
        except Exception as e:
            raise LanceDBQueryError(f"Failed to reconstruct node from LanceDB hit {hit}: {e}") from e
    return results

