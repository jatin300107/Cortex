import ast
import re
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
import cognee
from backend.logger.logger_setup import logger
from datapoints import (
    File, Function, Class, Directory )
from edges import (  FileContainsFunction, FileContainsClass, ClassContainsFunction , DirectoryContainsFile
)
from cognee.tasks.storage import add_data_points
from dotenv import load_dotenv
from backend.agent.dataset import store_datasets
SKIP_DIRS = {"venv", ".venv", "env", ".git", "__pycache__", "node_modules", "dist", "build", "site-packages"}

class SearchTool:

    def __init__(self, repo_path: str , dataset_id):
        self.repo = Path(repo_path)
        self.repo_name = self.repo.name
        self.dataset_id = dataset_id
        

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
                    await self._cognify_file(file, tree, source)
                    results.extend(matched)
                
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
                                await self._cognify_file(file, tree, source)
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

    

    async def _cognify_file(self, file: Path, tree, source: str) -> None:
        try:
            repo_name = self.repo.name
            lines = source.splitlines()
            node_set = []

            dir_node = Directory(path=str(file.parent), repo_name=repo_name)
            file_node = File(path=str(file), language="python", repo_name=repo_name, access_count=1)
            node_set.append(dir_node)
            node_set.append(file_node)
            node_set.append(DirectoryContainsFile(source=dir_node, target=file_node))

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    fn = Function(
                        name=node.name,
                        file_path=str(file),
                        repo_name=repo_name,
                        args=[arg.arg for arg in node.args.args],
                        return_type=ast.unparse(node.returns) if node.returns else None,
                        docstring=ast.get_docstring(node),
                        body_summary="\n".join(lines[node.lineno - 1:node.end_lineno]),
                        calls=self._extract_calls(node),
                        access_count=0
                    )
                    node_set.append(fn)
                    node_set.append(FileContainsFunction(source=file_node, target=fn))

                elif isinstance(node, ast.ClassDef):
                    cls = Class(
                        name=node.name,
                        file_path=str(file),
                        methods=[n.name for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))],
                        docstring=ast.get_docstring(node),
                        body_summary="\n".join(lines[node.lineno - 1:node.end_lineno]),
                    )
                    node_set.append(cls)
                    node_set.append(FileContainsClass(source=file_node, target=cls))

            
            await store_datasets(node_set=node_set , dataset_id=self.dataset_id)
        except Exception as e:
            logger.error(f"Failed to cognify {file}: {e}", exc_info=True)