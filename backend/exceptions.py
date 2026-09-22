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