search_repo_declaration = {
    "type": "function",
    "name": "search_repo",
    "description": """Searches the repository's code structure. Use 'ast' mode when you already know the exact function or class name. Use 'grep' mode when you only have a code snippet or partial text and don't know the enclosing function/class name yet.
    After calling cognee_query, first determine whether the returned information fully answers the user's question.

Treat the Cognee response as authoritative.

DO NOT call search_repo simply to verify, expand, or restate information that Cognee has already provided.

Call search_repo ONLY if:
- Cognee returns no answer.
- Cognee explicitly indicates the information is unavailable.
- The user explicitly asks for the exact source code, full implementation, line numbers, or other repository details that are missing from Cognee's response.""",
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