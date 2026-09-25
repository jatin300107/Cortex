import json
from backend.memory.extraction.structural import   _reconstruct
from backend.memory.db.datapoints import NODE_TYPES , ExtractionResult
from backend.exceptions import HeirarchyExtractionError

CONTAINMENT_EDGES = [
    "DirectoryContainsDirectory",
    "DirectoryContainsFile",
    "FileContainsClass",
    "FileContainsFunction",
    "ClassContainsFunction",
]


def get_directory_tree(kuzu_conn, directory_id: str, max_depth: int = 10) -> list[ExtractionResult]:
    """
    Single query, walks the full containment hierarchy from a directory:
    subdirectories, files, classes, functions, class methods, at any depth,
    in one Kuzu round-trip instead of N+1 traverse() calls.
    """
    try:

        edge_pattern = CONTAINMENT_EDGES[0] if len(CONTAINMENT_EDGES) == 1 else "|:".join(CONTAINMENT_EDGES)
        query = (
            f"MATCH (d:Directory {{id: $id}})"
            f"-[:{edge_pattern}*1..{max_depth}]->(n) "
            f"RETURN DISTINCT n, labels(n)"
        )

        response = kuzu_conn.execute(query, {"id": directory_id})
        rows = response.rows_as_dict().get_all()
    except Exception as e:
        raise HeirarchyExtractionError(f"Failed to get directory tree for {directory_id}: {e}")
    try:
        return [
            ExtractionResult(node=_reconstruct(row, node_key="n"), matched_via="structural")
            for row in rows
        ]
    except Exception as e:
        raise HeirarchyExtractionError(
            f"Node reconstruction failed while building tree for {directory_id}: {type(e).__name__}: {e}"
        ) from e