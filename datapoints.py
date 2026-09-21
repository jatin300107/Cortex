import hashlib
from datetime import datetime
from typing import Annotated, ClassVar, Literal, get_type_hints, get_args
from pydantic import BaseModel, model_validator


class Dedup:
    pass

class Embeddable:
    pass


class DataPoint(BaseModel):
    id: str = ""

    @model_validator(mode="after")
    def _set_id(self):
        if not self.id:
            hints = get_type_hints(type(self), include_extras=True)
            dedup_fields = [
                f for f, t in hints.items()
                if any(isinstance(a, Dedup) for a in get_args(t))
            ]
            raw = "::".join(str(getattr(self, f)) for f in dedup_fields)
            self.id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return self


class Directory(DataPoint):
    path: Annotated[str, Dedup()]
    repo_name: str


class File(DataPoint):
    path: Annotated[str, Dedup()]
    language: str
    repo_name: str
    access_count: int = 0


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
    session_id: Annotated[int, Dedup()]
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