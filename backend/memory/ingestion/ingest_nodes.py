import json
from typing import get_type_hints, get_args
from backend.memory.db.datapoints import DataPoint, Embeddable
from backend.memory.db.edges import Edge
from backend.memory.db.kuzu import REL_TABLES
from backend.exceptions import NodeIngestionError
from backend.exceptions import EdgeIngestionError , MissingEndpointError
from backend.memory.ingestion.generate_embeddings import embed_texts
 
def _get_embeddable_fields(cls) -> list[str]:
    hints = get_type_hints(cls, include_extras=True)
    return [f for f, t in hints.items() if any(isinstance(a, Embeddable) for a in get_args(t))]


def _build_embedding_text(node: DataPoint) -> str:
    # Full context, not fragments: pulls every Embeddable field for this node type
    # and joins them, so the node's whole meaning goes into one vector.
    fields = _get_embeddable_fields(type(node))
    parts = [str(getattr(node, f)) for f in fields if getattr(node, f, None)]
    return "\n".join(parts)


def _serialize_properties(node: DataPoint) -> dict:
    props = node.model_dump()
    for k, v in props.items():
        if isinstance(v, dict):
            props[k] = json.dumps(v)  # Kuzu has no native dict/map property type
    return props


def ingest_node(conn, lancedb_table, node: DataPoint, embed_fn):
    label = type(node).__name__
    props = _serialize_properties(node)

    set_clause = ", ".join(f"n.{k} = ${k}" for k in props if k != "id")
    conn.execute(f"MERGE (n:{label} {{id: $id}}) SET {set_clause}", props)

    text = _build_embedding_text(node)
    if text:
        vector = embed_fn(text)
        row = [{"id": node.id, "node_type": label, "text": text, "vector": vector}]
        lancedb_table.merge_insert("id") \
            .when_matched_update_all() \
            .when_not_matched_insert_all() \
            .execute(row)


def ingest_nodes(conn, lancedb_table, nodes: list[DataPoint]):
    texts_by_node = {}
    for node in nodes:
        text = _build_embedding_text(node)
        if text:
            texts_by_node[node.id] = text

    ids = list(texts_by_node.keys())
    vectors = embed_texts([texts_by_node[i] for i in ids])
    vector_by_id = dict(zip(ids, vectors))

    embedding_rows = []
    try:
        conn.execute("BEGIN TRANSACTION")
        for node in nodes:
            label = type(node).__name__
            props = _serialize_properties(node)
            set_clause = ", ".join(f"n.{k} = ${k}" for k in props if k != "id")
            conn.execute(f"MERGE (n:{label} {{id: $id}}) SET {set_clause}", props)

            if node.id in vector_by_id:
                embedding_rows.append({
                    "id": node.id,
                    "node_type": label,
                    "text": texts_by_node[node.id],
                    "vector": vector_by_id[node.id],
                })
        conn.execute("COMMIT")
    except Exception as e:
        conn.execute("ROLLBACK")
        raise NodeIngestionError(f"Error ingesting nodes, rolled back: {e}") from e

    if embedding_rows:
        lancedb_table.merge_insert("id") \
            .when_matched_update_all() \
            .when_not_matched_insert_all() \
            .execute(embedding_rows)
   


def ingest_edge(conn, edge: Edge):
    rel = type(edge).__name__
    src_label, tgt_label = REL_TABLES[rel]
    query = f"""
        MATCH (s:{src_label} {{id: $source_id}}), (t:{tgt_label} {{id: $target_id}})
        MERGE (s)-[r:{rel}]->(t)
    """
    conn.execute(query, {"source_id": edge.source_id, "target_id": edge.target_id})



def ingest_edges(conn, edges: list[Edge]):
    try:
        conn.execute("BEGIN TRANSACTION")
        for edge in edges:
            rel = type(edge).__name__
            src_label, tgt_label = REL_TABLES[rel]

            check = conn.execute(
                f"""
                MATCH (s:{src_label} {{id: $source_id}})
                OPTIONAL MATCH (t:{tgt_label} {{id: $target_id}})
                RETURN s.id, t.id
                """,
                {"source_id": edge.source_id, "target_id": edge.target_id},
            )
            # source didn't match at all -> zero rows back
            if not check.has_next():
                raise MissingEndpointError(rel, edge.source_id, edge.target_id, "source")
            src_found, tgt_found = check.get_next()
            if tgt_found is None:
                raise MissingEndpointError(rel, edge.source_id, edge.target_id, "target")

            conn.execute(
                f"""
                MATCH (s:{src_label} {{id: $source_id}}), (t:{tgt_label} {{id: $target_id}})
                MERGE (s)-[r:{rel}]->(t)
                """,
                {"source_id": edge.source_id, "target_id": edge.target_id},
            )
        conn.execute("COMMIT")
    except MissingEndpointError:
        conn.execute("ROLLBACK")
        raise
    except Exception as e:
        conn.execute("ROLLBACK")
        raise EdgeIngestionError(f"Error ingesting edges, rolled back: {e}") from e

def ingest_batch(conn, lancedb_table, nodes: list[DataPoint], edges: list[Edge], embed_fn):
    ingest_nodes(conn, lancedb_table, nodes, embed_fn)
    ingest_edges(conn, edges)
    