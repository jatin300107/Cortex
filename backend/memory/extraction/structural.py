import json
from backend.memory.db.datapoints import NODE_TYPES, DataPoint, ExtractionResult
from backend.memory.db.kuzu import REL_TABLES
from typing import Literal
 
from backend.exceptions import RowReconstructionErrror , GraphQueryError

def _reconstruct(row: dict, node_key: str = "n") -> DataPoint:
    try:
        node_data = dict(row[node_key])
        label_key = f"labels({node_key})"
        labels = row.get(label_key)
        label = labels[0] if labels else None

        if label is None:
            raise ValueError(f"No label found in row for key '{label_key}': {row}")

        node_cls = NODE_TYPES.get(label)
        if node_cls is None:
            raise ValueError(f"Unknown node label '{label}', not in NODE_TYPES")

        if "metadata" in node_data and isinstance(node_data["metadata"], str):
            node_data["metadata"] = json.loads(node_data["metadata"])
        return node_cls(**node_data)
    except Exception as e:
        raise RowReconstructionErrror(f"Failed to reconstruct node from row {row}: {e}.") from e

def get_relations(kuzu_conn, hits: list[ExtractionResult]) -> dict[str, list]:
    """
    For each hit, returns lightweight relation info (edge_label, target type,
    target identifying field) with one batched Kuzu query across all non-reasoning
    node ids. ReasoningNode hits are excluded from the lightweight query and instead
    get full connected node content via traverse().
    """
    lightweight_ids = []
    reasoning_ids = []

    for hit in hits:
        node = hit.node
        if type(node).__name__ == "ReasoningNode":
            reasoning_ids.append(node.id)
        else:
            lightweight_ids.append(node.id)

    results: dict[str, list] = {}

    if lightweight_ids:
        query = (
            "MATCH (a)-[r]->(b) "
            "WHERE a.id IN $ids "
            "RETURN a.id AS source_id, label(r) AS edge_label, "
            "labels(b)[0] AS target_type, b.id AS target_id, "
            "coalesce(b.path, b.name) AS target_label"
        )
        try:
            response = kuzu_conn.execute(query, {"ids": lightweight_ids})
            rows = response.rows_as_dict().get_all()
        except Exception as e:
            raise GraphQueryError(f"Failed to fetch relations for {lightweight_ids}: {e}") from e

        for row in rows:
            results.setdefault(row["source_id"], []).append({
                "edge_label": row["edge_label"],
                "target_type": row["target_type"],
                "target_id": row["target_id"],
                "target_label": row["target_label"],
            })

    for node_id in reasoning_ids:
        edges = [e for e in ("RESOLVED_BY", "BLOCKED_BY") if e in REL_TABLES]
        try:
            results[node_id] = traverse(kuzu_conn, node_id, edges, expected_type="ReasoningNode", direction="out")
        except Exception as e:
            raise GraphQueryError(f"Failed to fetch full relation for reasoning node {node_id}: {e}") from e
       

    return results
    

def traverse(
    kuzu_conn,
    node_id: str,
    edge_labels: list[str],
    expected_type: str,
    direction: Literal["out", "in"] = "out",
) -> list[ExtractionResult]:
    if not edge_labels:
        return []

    for el in edge_labels:
        src, tgt = REL_TABLES[el]
        required = src if direction == "out" else tgt
        if expected_type != required:
            raise ValueError(
                f"Edge '{el}' expects source type '{required}' for direction '{direction}', "
                f"got '{expected_type}' for node '{node_id}'"
            )

    edge_pattern = edge_labels[0] if len(edge_labels) == 1 else "|:".join(edge_labels)

    if direction == "out":
        query = f"MATCH (a {{id: $id}})-[:{edge_pattern}]->(b) RETURN b, labels(b)"
    else:
        query = f"MATCH (a {{id: $id}})<-[:{edge_pattern}]-(b) RETURN b, labels(b)"

    try:
        response = kuzu_conn.execute(query, {"id": node_id})
        rows = response.rows_as_dict().get_all()
    except Exception as e:
        raise GraphQueryError(
            f"Failed to traverse edges {edge_labels} from node '{node_id}': {e}"
        ) from e

    try:
        return [
            ExtractionResult(node=_reconstruct(row, node_key="b"), matched_via="structural")
            for row in rows
        ]
    except Exception as e:
        raise GraphQueryError(
            f"Failed to reconstruct nodes from traversal of edges {edge_labels} from node '{node_id}': {e}"
        ) from e