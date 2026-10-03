class AIRequestError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(f"{self.msg}")

class NodeIngestionError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(f"{self.msg}")


class EdgeIngestionError(Exception):
    pass

class MissingEndpointError(EdgeIngestionError):
    def __init__(self, rel: str, source_id: str, target_id: str, missing: str):
        self.rel = rel
        self.source_id = source_id
        self.target_id = target_id
        self.missing = missing
        super().__init__(
            f"{rel}: cannot create edge, {missing} endpoint not found "
            f"(source_id={source_id}, target_id={target_id})"
        )

class EmbeddingError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(f"{self.msg}")

class HeirarchyExtractionError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(f"{self.msg}")

class LanceDBQueryError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(f"{self.msg}")

class RowReconstructionError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(f"{self.msg}")

class GraphQueryError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(f"{self.msg}")

class QueryMemoryError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(f"{self.msg}")

class FileParseError(Exception):
    """File could not be read or parsed into an AST."""
    def __init__(self, path: str, reason: str):
        self.path = path
        self.reason = reason
        super().__init__(f"Could not parse {path}: {reason}")


class DatapointBuildError(Exception):
    """AST was parsed but turning it into datapoints/edges failed."""
    def __init__(self, path: str, reason: str):
        self.path = path
        self.reason = reason
        super().__init__(f"Could not build datapoints for {path}: {reason}")


class FileIngestionError(Exception):
    """Node or edge ingestion failed for a file. Wraps the underlying error."""
    def __init__(self, path: str, cause: Exception):
        self.path = path
        self.cause = cause
        super().__init__(f"Ingestion failed for {path}: {cause}")