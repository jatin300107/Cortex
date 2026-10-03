AGENT_FIELDS = {
    "Directory": ("path",),
    "File": ("path", "language"),
    "Class": ("name", "file_path", "methods", "docstring", "body_summary"),
    "Function": ("name", "file_path", "args", "return_type",
                 "docstring", "body_summary", "calls"),
    "Session": ("query", "answer", "timestamp"),
    "ReasoningNode": ("intent", "reasoning_chain", "conclusion",
                      "suggested_because", "blocked_by"),
    "ErrorResolutionNode": ("function_name", "error_type", "error_description",
                            "root_cause", "fix_applied", "status"),
    "Blocker": ("description", "status"),
}

# Reasoning content is the whole point of those hits, so clip it less
CLIP = {"ReasoningNode": 1500, "ErrorResolutionNode": 1500, "Session": 800}
DEFAULT_CLIP = 500


def slim_node(node: DataPoint) -> dict:
    type_name = type(node).__name__
    fields = AGENT_FIELDS[type_name]  # KeyError on an unlisted type is deliberate
    data = node.model_dump(mode="json", include=set(fields))
    limit = CLIP.get(type_name, DEFAULT_CLIP)

    out = {}
    for k in fields:
        v = data.get(k)
        if v in (None, "", [], {}):
            continue
        if isinstance(v, str) and len(v) > limit:
            v = v[:limit] + "..."
        out[k] = v
    return out