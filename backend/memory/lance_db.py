import os
import lancedb
import pyarrow as pa
LANCEDB_PATH = os.environ.get("LANCEDB_PATH", "./lancedb")
EMBEDDING_DIM = 768 

def init_lancedb() -> lancedb.LanceDB: 
    db = lancedb.connect(LANCEDB_PATH)
 
    if "embeddings" not in db.list_tables():
        schema = pa.schema([
            pa.field("id", pa.string()),          
            pa.field("node_id", pa.string()),
            pa.field("node_type", pa.string()),
            pa.field("field_name", pa.string()),
            pa.field("text", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIM)),
        ])
        db.create_table("embeddings", schema=schema)
 
    return db