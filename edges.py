from datapoints import DataPoint
from pydantic import BaseModel
class Edge(BaseModel):
    source_id: str
    target_id: str

    @classmethod
    def from_nodes(cls, source: DataPoint, target: DataPoint, **kwargs):
        return cls(source_id=source.id, target_id=target.id, **kwargs)


class FunctionCallsFunction(Edge):
    pass

class FunctionCallsClass(Edge):
    pass

class ClassCallsFunction(Edge):
    pass

class ClassCallsClass(Edge):
    pass

class SessionAskedAboutFunction(Edge):
    pass

class SessionAskedAboutFile(Edge):
    pass

class SessionAskedAboutClass(Edge):
    pass

class ReasoningReferencesFunction(Edge):
    pass

class ReasoningReferencesFile(Edge):
    pass

class ReasoningReferencesClass(Edge):
    pass

class BlockerBlocksFunction(Edge):
    pass

class BlockerBlocksFile(Edge):
    pass

class DirectoryContainsFile(Edge):
    pass

class FileContainsClass(Edge):
    pass

class FileContainsFunction(Edge):
    pass

class ClassContainsFunction(Edge):
    pass

class Imports(Edge):
    pass