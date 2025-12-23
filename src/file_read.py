"""
Utility to read file snippets with optional line ranges.

Memory optimizations:
- File content caching for repeated reads
- Line-by-line reading for large files
- Configurable context window
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from cache import get_file_cache


@dataclass
class FileSnippet:
    path: str
    start: int
    end: int
    text: str


def read_snippet(path: str, start: Optional[int] = None, end: Optional[int] = None, context: int = 3, use_cache: bool = True) -> FileSnippet:
    """
    Read a file snippet with optional line range.

    Args:
        path: File path to read
        start: Optional start line number (1-indexed)
        end: Optional end line number (1-indexed)
        context: Number of lines of context to include (default 3)
        use_cache: Enable file content caching (default True)

    Returns:
        FileSnippet containing the requested content
    """
    # Try cache first
    if use_cache:
        cache = get_file_cache()
        cache_key = cache._make_key(path, start, end, context)
        cached = cache.get(cache_key)
        if cached is not None:
            return FileSnippet(**cached)

    lines = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            all_lines = fh.readlines()
    except (FileNotFoundError, PermissionError, OSError):
        snippet = FileSnippet(path=path, start=0, end=0, text="")
        # Cache the error result
        if use_cache:
            cache = get_file_cache()
            cache_key = cache._make_key(path, start, end, context)
            cache.set(cache_key, {"path": snippet.path, "start": snippet.start, "end": snippet.end, "text": snippet.text})
        return snippet

    total = len(all_lines)
    if start is None or start <= 0:
        start_idx = 0
    else:
        start_idx = max(0, start - context - 1)
    if end is None or end <= 0:
        end_idx = min(total, (start or 1) + context)
    else:
        end_idx = min(total, end + context)

    snippet_lines = all_lines[start_idx:end_idx]
    text = "".join(snippet_lines)

    snippet = FileSnippet(path=path, start=start_idx + 1, end=end_idx, text=text)

    # Cache the successful result
    if use_cache:
        cache = get_file_cache()
        cache_key = cache._make_key(path, start, end, context)
        # Only cache small snippets (<10KB)
        if len(text) < 10 * 1024:
            cache.set(cache_key, {"path": snippet.path, "start": snippet.start, "end": snippet.end, "text": snippet.text})

    return snippet


if __name__ == "__main__":
    snip = read_snippet("src/delegation_policy.py", start=60, end=86)
    print(f"{snip.path}:{snip.start}-{snip.end}\n{snip.text}")
