"""Simple code search utility for local repositories.

Enhanced with a lightweight AST-based symbol index to surface
definitions/usages as evidence alongside plain text matches.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple

from symbol_index import SymbolIndex


@dataclass
class SearchHit:
    path: str
    line: int
    snippet: str


class CodeSearch:
    def __init__(self, root: str = ".", max_file_size: int = 256_000) -> None:
        self.root = os.path.abspath(root)
        self.max_file_size = max_file_size
        self._sym_index = SymbolIndex(root=self.root, max_file_size=max_file_size)

    def search(self, query: str, paths: Optional[Iterable[str]] = None, max_results: int = 10) -> List[SearchHit]:
        terms = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 2]
        if not terms:
            return []
        hits: List[SearchHit] = []
        target_paths: Iterable[str]
        if paths is None:
            target_paths = self._walk_all()
        else:
            target_paths = paths

        # 1) Include symbol-based hits (definitions/usages) first for higher-value evidence
        sym_hits = self._symbol_hits(terms, target_paths, max_results=max_results)
        hits.extend(sym_hits)

        for path in target_paths:
            if len(hits) >= max_results:
                break
            if not self._is_text_file(path):
                continue
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    for idx, line in enumerate(fh, start=1):
                        lower = line.lower()
                        if all(term in lower for term in terms):
                            snippet = line.strip()
                            if not self._has_hit(hits, path, idx):
                                hits.append(SearchHit(path=path, line=idx, snippet=snippet))
                            if len(hits) >= max_results:
                                break
            except (FileNotFoundError, PermissionError, OSError):
                continue
        return hits

    def _walk_all(self) -> Iterable[str]:
        for dirpath, _, filenames in os.walk(self.root):
            for fname in filenames:
                yield os.path.join(dirpath, fname)

    def _is_text_file(self, path: str) -> bool:
        try:
            size = os.path.getsize(path)
            if size > self.max_file_size:
                return False
        except OSError:
            return False

        path_obj = Path(path)
        # Skip common binary / metadata directories and extensions
        if any(part.startswith('.git') for part in path_obj.parts):
            return False
        if path_obj.suffix.lower() in {'.pyc', '.pyo', '.so', '.dll', '.exe'}:
            return False

        try:
            with open(path, 'rb') as fh:
                chunk = fh.read(1024)
                if b"\x00" in chunk:
                    return False
        except (FileNotFoundError, PermissionError, OSError):
            return False
        return True

    def _symbol_hits(self, terms: List[str], paths: Iterable[str], max_results: int) -> List[SearchHit]:
        # Index only the provided paths for performance
        self._sym_index.index_paths(paths)
        results: List[SearchHit] = []
        for t in terms:
            # find definitions
            for path, line in self._sym_index.find_definitions(t):
                snippet = self._read_line(path, line)
                if not self._has_hit(results, path, line):
                    results.append(SearchHit(path=path, line=line, snippet=snippet))
                    if len(results) >= max_results:
                        return results
            # find usages
            for path, line in self._sym_index.find_usages(t):
                snippet = self._read_line(path, line)
                if not self._has_hit(results, path, line):
                    results.append(SearchHit(path=path, line=line, snippet=snippet))
                    if len(results) >= max_results:
                        return results
        return results

    def _read_line(self, path: str, line_no: int) -> str:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                for idx, line in enumerate(fh, start=1):
                    if idx == line_no:
                        return line.strip()
        except (FileNotFoundError, PermissionError, OSError):
            return ""
        return ""

    def _has_hit(self, hits: List[SearchHit], path: str, line: int) -> bool:
        for h in hits:
            if h.path == path and h.line == line:
                return True
        return False


if __name__ == "__main__":
    cs = CodeSearch()
    for hit in cs.search("delegation policy", max_results=3):
        print(f"{hit.path}:{hit.line} {hit.snippet}")
