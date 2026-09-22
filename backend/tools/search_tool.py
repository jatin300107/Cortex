import ast
import re
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from backend.logger.logger_setup import logger
from backend.memory.datapoints import File, Class, Function
from backend.memory.edges import Edge, FileContainsFunction, FileContainsClass
from backend.agent.dataset import store_datasets
SKIP_DIRS = {"venv", ".venv", "env", ".git", "__pycache__", "node_modules", "dist", "build", "site-packages"}
from os import PathLike
class SearchTool:

    def __init__(self, repo_path: str | PathLike ):
        self.repo = Path(repo_path)
        self.repo_name = self.repo.name

        

    async def run(self, mode: str, query: str ) -> list[dict]:
        logger.info("Search started")
        
        if mode == "ast":
            return await self._ast_search(query)
        elif mode == "grep":
            return await self._grep_search(query)
        else:
            raise ValueError(f"Unknown mode: {mode}")

    async def _ast_search(self, query: str) -> list[dict]:
        results = []
        for file in self.repo.rglob("*.py"):
            if any(part in SKIP_DIRS for part in file.parts):
                continue
            try:
                source = file.read_text(encoding="utf-8")
                tree = ast.parse(source)
                matched = self._extract_matches(tree, source, query)
                if matched:
                    await self._build_file_datapoints(file)
                    results.extend(matched)
                    results.extend({"file_path" : file})
                    
            except Exception as e:
                logger.error(f"Failed to parse {file}: {e}")
        return results if results else [{"error": f"'{query}' not found via AST"}]

    async def _grep_search(self, query: str) -> list[dict]:
        results = []
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        for file in self.repo.rglob("*.py"):
            if any(part in SKIP_DIRS for part in file.parts):
                continue
            try:
                source = file.read_text(encoding="utf-8")
                lines = source.splitlines()
                for line_no, line in enumerate(lines, start=1):
                    if pattern.search(line):
                        tree = ast.parse(source)
                        name = self._find_enclosing_name(tree, line_no)
                        if name:
                            matched = self._extract_matches(tree, source, name)
                            if matched:
                                await self._build_file_datapoints(file)
                                results.extend(matched)
                                break
            except Exception:
                logger.exception("Grep search failed for file")
        return results if results else [{"status": "not_found", "query": query, "mode": "grep"}]

    def _find_enclosing_name(self, tree, line_no: int) -> str | None:
        best = None
        best_span = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start, end = node.lineno, node.end_lineno
                if start <= line_no <= end:
                    span = end - start
                    if best_span is None or span < best_span:
                        best = node.name
                        best_span = span
        return best
    def _extract_matches(self, tree, source: str, query: str) -> list[dict]:
        results = []
        lines = source.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == query:
                results.append({
                    "type": "function",
                    "name": node.name,
                    
                    "args": [arg.arg for arg in node.args.args],
                    "return_type": ast.unparse(node.returns) if node.returns else None,
                    "docstring": ast.get_docstring(node),
                    "body_code": "\n".join(lines[node.lineno - 1:node.end_lineno]),
                    "calls": self._extract_calls(node),
                    "line": node.lineno,
                })
            elif isinstance(node, ast.ClassDef) and node.name == query:
                results.append({
                    "type": "class",
                    "name": node.name,
                    "methods": [n.name for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))],
                    "docstring": ast.get_docstring(node),
                    "body_code": "\n".join(lines[node.lineno - 1:node.end_lineno]),
                    "line": node.lineno,
                })
        return results

    def _extract_calls(self, node) -> list[str]:
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        return calls 

    

    async def _build_file_datapoints(self, file: Path, tree, source: str) -> dict:
        lines = source.splitlines()
        rel_path = str(file.relative_to(self.repo))

        file_dp = File(
            path=rel_path,
            language="python",
            repo_name=self.repo_name,
            access_count=0,
        )

        class_dps: list[Class] = []
        function_dps: list[Function] = []
        contains_edges: list[Edge] = []
        call_edges_raw: list[tuple[str, str, str]] = []  # (caller_name, caller_file, callee_name)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn_dp = Function(
                    name=node.name,
                    file_path=rel_path,
                    repo_name=self.repo_name,
                    args=[arg.arg for arg in node.args.args],
                    return_type=ast.unparse(node.returns) if node.returns else None,
                    docstring=ast.get_docstring(node),
                    body_summary="\n".join(lines[node.lineno - 1:node.end_lineno]),
                    calls=self._extract_calls(node),
                    access_count=0,
                )
                function_dps.append(fn_dp)
                contains_edges.append(FileContainsFunction.from_nodes(file_dp, fn_dp))
                for callee_name in fn_dp.calls:
                    call_edges_raw.append((fn_dp.name, fn_dp.file_path, callee_name))

            elif isinstance(node, ast.ClassDef):
                cls_dp = Class(
                    name=node.name,
                    file_path=rel_path,
                    methods=[n.name for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))],
                    docstring=ast.get_docstring(node),
                    body_summary="\n".join(lines[node.lineno - 1:node.end_lineno]),
                )
                class_dps.append(cls_dp)
                contains_edges.append(FileContainsClass.from_nodes(file_dp, cls_dp))

        return {
            "file": file_dp,
            "classes": class_dps,
            "functions": function_dps,
            "contains_edges": contains_edges,
            "call_edges_raw": call_edges_raw,  
        }