"""Utility to read file snippets with optional line ranges."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class FileSnippet:
    path: str
    start: int
    end: int
    text: str


def read_snippet(path: str, start: Optional[int] = None, end: Optional[int] = None, context: int = 3) -> FileSnippet:
    lines = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            all_lines = fh.readlines()
    except (FileNotFoundError, PermissionError, OSError):
        return FileSnippet(path=path, start=0, end=0, text="")

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
    return FileSnippet(path=path, start=start_idx + 1, end=end_idx, text=text)


if __name__ == "__main__":
    snip = read_snippet("src/delegation_policy.py", start=60, end=86)
    print(f"{snip.path}:{snip.start}-{snip.end}\n{snip.text}")
