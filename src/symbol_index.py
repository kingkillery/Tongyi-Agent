from __future__ import annotations

import ast
import os
import json
from dataclasses import dataclass
from typing import Dict, List, Set, Iterable, Tuple

from cas_store import CAS


@dataclass
class SymbolDef:
    name: str
    path: str
    line: int


@dataclass
class SymbolUse:
    name: str
    path: str
    line: int


class SymbolIndex:
    def __init__(self, root: str = ".", max_file_size: int = 256_000) -> None:
        self.root = os.path.abspath(root)
        self.max_file_size = max_file_size
        self._defs: Dict[str, List[Tuple[str, int]]] = {}
        self._uses: Dict[str, List[Tuple[str, int]]] = {}
        self._indexed_files: Set[str] = set()
        self._cas = CAS()
        self._parser_ver = "py-ast-v1"

    def index_paths(self, paths: Iterable[str]) -> None:
        for path in paths:
            if path in self._indexed_files:
                continue
            if not self._is_python_file(path):
                continue
            try:
                self._index_file(path)
                self._indexed_files.add(path)
            except Exception:
                continue

    def find_definitions(self, name: str) -> List[Tuple[str, int]]:
        key = name if name in self._defs else name.lower()
        return list(self._defs.get(key, []))

    def find_usages(self, name: str) -> List[Tuple[str, int]]:
        key = name if name in self._uses else name.lower()
        return list(self._uses.get(key, []))

    def _is_python_file(self, path: str) -> bool:
        if not path.endswith(".py"):
            return False
        try:
            size = os.path.getsize(path)
            if size > self.max_file_size:
                return False
        except OSError:
            return False
        return True

    def _index_file(self, path: str) -> None:
        # Read file bytes for cache key
        try:
            with open(path, "rb") as fh:
                file_bytes = fh.read()
        except OSError:
            return

        # Attempt to load cached summary keyed by file content + parser version
        key = self._cas.make_key(file_bytes, self._parser_ver)
        cached_blob, _meta = self._cas.get(key)
        if cached_blob:
            try:
                summary = json.loads(cached_blob.decode("utf-8"))
                defs = summary.get("defs", {})
                uses = summary.get("uses", {})
                for name, entries in defs.items():
                    self._defs.setdefault(name, []).extend((path, line) for line in entries)
                for name, entries in uses.items():
                    self._uses.setdefault(name, []).extend((path, line) for line in entries)
                return
            except (json.JSONDecodeError, KeyError, TypeError):
                # Cache corrupted; fall through to re-parse
                pass

        # Parse AST and build summary
        try:
            src_text = file_bytes.decode("utf-8", errors="ignore")
            tree = ast.parse(src_text)
        except (SyntaxError, UnicodeDecodeError):
            return

        defs_summary: Dict[str, List[int]] = {}
        uses_summary: Dict[str, List[int]] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                key = node.name.lower()
                defs_summary.setdefault(key, []).append(node.lineno)
                self._defs.setdefault(key, []).append((path, node.lineno))
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                key = node.id.lower()
                uses_summary.setdefault(key, []).append(node.lineno)
                self._uses.setdefault(key, []).append((path, node.lineno))

        # Store summary in CAS
        summary = {"defs": defs_summary, "uses": uses_summary}
        try:
            summary_bytes = json.dumps(summary, ensure_ascii=False).encode("utf-8")
            self._cas.put(
                summary_bytes,
                url=f"file://{path}",
                fetched_at=None,
                content_type="application/json",
                parser_ver=self._parser_ver,
            )
        except Exception:
            # CAS write failure is non-critical; indexing still succeeded in-memory
            pass
