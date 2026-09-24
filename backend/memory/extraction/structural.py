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
    except Exception as e:
        raise RowReconstructionErrror(f"Failed to reconstruct node from row {row}: {e}.")


    return node_cls(**node_data)


def traverse(kuzu_conn, node_id: str, edge_label: str, direction: Literal["out", "in"] = "out") -> list[ExtractionResult]:
    src, tgt = REL_TABLES[edge_label]
    if direction == "out":
        query = f"MATCH (a:{src} {{id: $id}})-[:{edge_label}]->(b:{tgt}) RETURN b, labels(b)"
    else:
        query = f"MATCH (a:{tgt} {{id: $id}})<-[:{edge_label}]-(b:{src}) RETURN b, labels(b)"
    try:
        response = kuzu_conn.execute(query, {"id": node_id})
        rows = response.rows_as_dict().get_all()
    except Exception as e:
        raise GraphQueryError(f"Failed to traverse edge '{edge_label}' from node '{node_id}': {e}")
    try:
        return [
            ExtractionResult(node=_reconstruct(row, node_key="b"), matched_via="structural")
            for row in rows
        ]
    except Exception as e:
        raise GraphQueryError(f"Failed to reconstruct nodes from traversal of edge '{edge_label}' from node '{node_id}': {e}")