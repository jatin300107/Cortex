from cognee.infrastructure.engine import DataPoint
from datapoints import Function , Class , Session , Directory , File , ErrorResolutionNode , ReasoningNode , Blocker
class FunctionCallsFunction(DataPoint):
    source: Function
    target: Function

class FunctionCallsClass(DataPoint):
    source: Function
    target: Class

class ClassCallsFunction(DataPoint):
    source: Class
    target: Function

class ClassCallsClass(DataPoint):
    source: Class
    target: Class

# ASKED_ABOUT
class SessionAskedAboutFunction(DataPoint):
    source: Session
    target: Function

class SessionAskedAboutFile(DataPoint):
    source: Session
    target: File

class SessionAskedAboutClass(DataPoint):
    source: Session
    target: Class

# REFERENCES
class ReasoningReferencesFunction(DataPoint):
    source: ReasoningNode
    target: Function

class ReasoningReferencesFile(DataPoint):
    source: ReasoningNode
    target: File

class ReasoningReferencesClass(DataPoint):
    source: ReasoningNode
    target: Class

# BLOCKS
class BlockerBlocksFunction(DataPoint):
    source: Blocker
    target: Function

class BlockerBlocksFile(DataPoint):
    source: Blocker
    target: File

# CONTAINS
class DirectoryContainsFile(DataPoint):
    source: Directory
    target: File

class FileContainsClass(DataPoint):
    source: File
    target: Class

class FileContainsFunction(DataPoint):
    source: File
    target: Function

class ClassContainsFunction(DataPoint):
    source: Class
    target: Function

# IMPORTS
class Imports(DataPoint):
    source: File
    target: File



class SessionProducedReasoning(DataPoint):
    source: Session
    target: ReasoningNode



class LedTo(DataPoint):
    source: ReasoningNode
    target: ReasoningNode

# ERROR
class OccurredIn(DataPoint):
    source: ErrorResolutionNode
    target: Function

class ResolvedIn(DataPoint):
    source: ErrorResolutionNode
    target: Session


class RaisedIn(DataPoint):
    source: Blocker
    target: Session