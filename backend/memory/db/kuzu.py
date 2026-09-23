import os
import kuzu

KUZU_DB_PATH = os.environ.get("KUZU_DB_PATH", "./kuzu_db")

NODE_TABLES = {
    "Directory": "path STRING, repo_name STRING",
    "File": "path STRING, language STRING, repo_name STRING, access_count INT64",
    "Class": "name STRING, file_path STRING, methods STRING[], docstring STRING, "
             "body_summary STRING, metadata STRING",
    "Function": "name STRING, file_path STRING, repo_name STRING, args STRING[], "
                "return_type STRING, docstring STRING, body_summary STRING, "
                "calls STRING[], access_count INT64, metadata STRING",
    "Session": "session_id INT64, query STRING, answer STRING, timestamp TIMESTAMP",
    "ReasoningNode": "session_id INT64, intent STRING, reasoning_chain STRING, "
                      "conclusion STRING, suggested_because STRING, blocked_by STRING, metadata STRING",
    "ErrorResolutionNode": "session_id INT64, function_name STRING, error_type STRING, "
                            "error_description STRING, root_cause STRING, fix_applied STRING, status STRING",
    "Blocker": "description STRING, created_in INT64, status STRING, metadata STRING",
}
 

REL_TABLES = {
    "FunctionCallsFunction": ("Function", "Function"),
    "FunctionCallsClass": ("Function", "Class"),
    "ClassCallsFunction": ("Class", "Function"),
    "ClassCallsClass": ("Class", "Class"),
    "SessionAskedAboutFunction": ("Session", "Function"),
    "SessionAskedAboutFile": ("Session", "File"),
    "SessionAskedAboutClass": ("Session", "Class"),
    "ReasoningReferencesFunction": ("ReasoningNode", "Function"),
    "ReasoningReferencesFile": ("ReasoningNode", "File"),
    "ReasoningReferencesClass": ("ReasoningNode", "Class"),
    "BlockerBlocksFunction": ("Blocker", "Function"),
    "BlockerBlocksFile": ("Blocker", "File"),
    "DirectoryContainsFile": ("Directory", "File"),
    "FileContainsClass": ("File", "Class"),
    "FileContainsFunction": ("File", "Function"),
    "ClassContainsFunction": ("Class", "Function"),
    "Imports": ("File", "File"),
}

def init_kuzu() -> kuzu.Connection:
    db = kuzu.Database(KUZU_DB_PATH)
    conn = kuzu.Connection(db)
 
    result = conn.execute("CALL show_tables() RETURN name;")
    existing = set()
    while result.has_next():
        existing.add(result.get_next()[0])
 
    for name, cols in NODE_TABLES.items():
        if name in existing:
            continue
        conn.execute(f"CREATE NODE TABLE {name}(id STRING, {cols}, PRIMARY KEY(id))")
 
    for name, (src, tgt) in REL_TABLES.items():
        if name in existing:
            continue
        conn.execute(f"CREATE REL TABLE {name}(FROM {src} TO {tgt})")
 
    return conn