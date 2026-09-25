import os
import kuzu
import lancedb
KUZU_DB_PATH = os.environ.get("KUZU_DB_PATH", "./kuzu_db")
LANCEDB_PATH = os.environ.get("LANCEDB_PATH", "./lancedb")
if not KUZU_DB_PATH or not LANCEDB_PATH:
    raise ValueError("Invalid or missing KUZU_DB_PATH or LANCEDB_PATH")

def get_kuzu_connection() -> kuzu.Connection:
    db = kuzu.Database(KUZU_DB_PATH)
    conn = kuzu.Connection(db)
    return conn

def get_lancedb_connection() -> "lancedb.LanceDB":
    db = lancedb.connect(LANCEDB_PATH)
    return db