from cognee.infrastructure.engine import DataPoint , Embeddable , Dedup
from typing import Annotated , Literal
from datetime import datetime
class Directory(DataPoint):
    path: Annotated[str ,Dedup()]
    repo_name : Annotated[str, Dedup()]

class File(DataPoint):
    path : Annotated[str , Dedup()]
    language : str
    repo_name : Annotated[str, Dedup()]
    access_count : int 

class Class(DataPoint):
    name: Annotated[str, Dedup()]
    file_path: Annotated[str, Dedup()]
    methods: list[str] = []
    docstring: Annotated[str | None, Embeddable()] = None
    body_summary: Annotated[str | None, Embeddable()] = None
    metadata: dict = {"index_fields": ["name", "file_path", "docstring", "body_summary"]}


class Function(DataPoint):
    name: Annotated[str, Dedup()]
    file_path: Annotated[str, Dedup()]
    repo_name: str
    args: list[str] = []
    return_type: str | None = None
    docstring: Annotated[str | None, Embeddable()] = None
    body_summary: Annotated[str | None, Embeddable()] = None
    calls: list[str] = []
    access_count: int = 0
    metadata: dict = {"index_fields": ["name", "file_path", "docstring", "body_summary"]}

class Session(DataPoint):
    session_id: Annotated[int, Dedup()]
    query: Annotated[str | None, Embeddable()] = None
    answer: Annotated[str | None, Embeddable()] = None
    timestamp: datetime

class ReasoningNode(DataPoint):
    
    intent: Annotated[str, Dedup()]
    reasoning_chain: Annotated[str | None, Embeddable()] = None
    conclusion: Annotated[str | None, Embeddable()] = None
    suggested_because: str | None = None
    blocked_by: str | None = None
    metadata: dict = {"index_fields": ["intent", "reasoning_chain", "conclusion"]}

class ErrorResolutionNode(DataPoint):
    session_id: Annotated[int, Dedup()]
    function_name: Annotated[str, Dedup()]
    error_type: Annotated[str, Dedup()]
    error_description: Annotated[str | None, Embeddable()] = None
    root_cause: Annotated[str | None, Embeddable()] = None
    fix_applied: Annotated[str | None, Embeddable()] = None
    status: Literal["open", "resolved"] = "open"

class Blocker(DataPoint):
    description: Annotated[str, Dedup()]
    created_in: Annotated[int, Dedup()]
    status: Literal["open", "resolved"] = "open"
    metadata: dict = {"index_fields": ["description"]}