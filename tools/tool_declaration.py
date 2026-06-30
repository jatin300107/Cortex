search_repo_declaration = {
    "type": "function",
    "name": "search_repo",
    "description": "Searches the repository's code structure. Use 'ast' mode when you already know the exact function or class name. Use 'grep' mode when you only have a code snippet or partial text and don't know the enclosing function/class name yet.",
    "parameters": {
        "type": "object",
        "properties": {
            "mode": {
                "type": "string",
                "enum": ["ast", "grep"],
                "description": "Search strategy: 'ast' for exact name lookup, 'grep' for raw text match when the name is unknown."
            },
            "query": {
                "type": "string",
                "description": "Function/class name for ast mode, or a code snippet/text fragment for grep mode."
            }
        },
        "required": ["mode", "query"]
    }
}

cognee_query_declaration = {
    "type": "function",
    "name": "cognee_query",
    "description": "Searches the knowledge graph of previously ingested code structure and session memory. Always try this before search_repo, since it may already contain the answer without needing to re-scan the repo.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language query describing what code structure, prior finding, or memory to retrieve."
            },
            "mode": {
                "type": "string",
                "enum": ["default", "triplet"],
                "description": "Use 'triplet' for relationship/connection-style questions (e.g. how X relates to Y, what calls what). Use 'default' for general lookups."
            }
        },
        "required": ["query" , "mode"]
    }
}