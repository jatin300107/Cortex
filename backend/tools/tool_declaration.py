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
    "description": "Retrieves repository knowledge from Cognee's knowledge graph. "
    "Use ONLY when the user's request requires repository-specific information "
    "(functions, classes, files, architecture, previous implementation decisions, "
    "or previously learned repository knowledge).\n\n"

    "Do NOT use for greetings, casual conversation, thanks, or general questions.\n\n"

    "When calling this tool, rewrite the user's request into a clear, self-contained "
    "retrieval query. Preserve the user's intent, but do not invent facts or assume "
    "implementation details. Include only information explicitly provided by the "
    "user or established in the current conversation.\n\n"

    "If repository context is required, prefer this tool before search_repo.",
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