from cognee.infrastructure.engine import DataPoint , Embeddable , Dedup
from typing import Annotated

class Directory(DataPoint):
    path: Annotated[str ,Dedup()]
    repo_name : Annotated[str, Dedup()]

class File(DataPoint):
    path : Annotated[str , Dedup()]
    language : str
    repo_name : Annotated[str, Dedup()]
    access_count : int 

