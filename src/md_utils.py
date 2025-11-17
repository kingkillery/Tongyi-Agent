"""
Markdown Utilities for Cleaning Information Dumps
--------------------------------------------------
Provides helpers to parse, structure, and clean daily markdown dumps.
All functions are pure and avoid network/external calls.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from markdown import markdown
import yaml


logger = logging.getLogger(__name__)


@dataclass
class MDSection:
    title: str
    level: int
    content: str
    raw: str


@dataclass
class MDInfo:
    path: str
    sections: List[MDSection]
    frontmatter: Optional[Dict[str, Any]]
    word_count: int
    line_count: int


def parse_markdown(path: str) -> MDInfo:
    """Parse markdown into sections and extract frontmatter."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    # Split frontmatter
    frontmatter = None
    body = text
    if text.startswith("---\n"):
        try:
            fm_end = text.index("\n---\n", 4)
            frontmatter = yaml.safe_load(text[4:fm_end])
            body = text[fm_end + 5:]
        except (yaml.YAMLError, ValueError) as exc:
            logger.warning("Failed to parse markdown frontmatter in %s: %s", path, exc)
            frontmatter = None
            body = text
    # Split into sections by headings
    sections = []
    heading_re = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    parts = heading_re.split(body)
    # parts: [text_before, '#', 'Title', '##', 'Subtitle', ...]
    # Reconstruct sections
    current_level = 0
    current_title = ""
    current_content = parts[0] if parts else ""
    # Iterate over heading matches
    i = 1
    while i < len(parts):
        level = len(parts[i])
        title = parts[i + 1].strip()
        content_start = i + 2
        # Find next heading or end
        next_heading_idx = None
        for j in range(content_start, len(parts), 3):
            if j + 2 < len(parts) and parts[j].startswith("#"):
                next_heading_idx = j
                break
        if next_heading_idx is not None:
            content = "".join(parts[content_start:next_heading_idx])
        else:
            content = "".join(parts[content_start:])
        sections.append(MDSection(title=title, level=level, content=content.strip(), raw=f"{'#' * level} {title}\n{content.strip()}"))
        i = next_heading_idx if next_heading_idx is not None else len(parts)
    return MDInfo(
        path=path,
        sections=sections,
        frontmatter=frontmatter,
        word_count=len(body.split()),
        line_count=len(body.splitlines())
    )


def suggest_md_cleaning(info: MDInfo) -> List[Dict[str, Any]]:
    """Suggest cleaning steps for a markdown dump."""
    steps = []
    # Remove duplicate sections
    titles = [s.title.lower() for s in info.sections]
    for title, count in [(t, titles.count(t)) for t in set(titles)]:
        if count > 1:
            steps.append({"type": "dedupe_sections", "title": title, "reason": f"{count} duplicates"})
    # Normalize timestamps
    ts_patterns = [
        r"\b\d{1,2}:\d{2}\s*(AM|PM|am|pm)\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"
    ]
    has_timestamps = any(re.search(p, info.sections[0].raw) for p in ts_patterns) if info.sections else False
    if has_timestamps:
        steps.append({"type": "normalize_timestamps", "reason": "inconsistent timestamp formats"})
    # Collapse empty sections
    empty_sections = [s for s in info.sections if not s.content.strip()]
    if empty_sections:
        steps.append({"type": "collapse_empty_sections", "count": len(empty_sections)})
    # Sort sections by level/title if unstructured
    if info.sections and any(s.level > 2 for s in info.sections):
        steps.append({"type": "sort_sections", "reason": "deep subsections detected"})
    return steps


def clean_markdown(info: MDInfo, steps: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
    """Apply cleaning steps and write a cleaned markdown."""
    lines = []
    # Preserve frontmatter
    if info.frontmatter:
        lines.append("---")
        lines.extend(yaml.dump(info.frontmatter, default_flow_style=False).splitlines())
        lines.append("---")
        lines.append("")
    seen_titles = set()
    sections = info.sections[:]
    for step in steps:
        typ = step.get("type")
        if typ == "dedupe_sections":
            title = step.get("title", "").lower()
            # Keep first occurrence, remove others
            sections = [s for i, s in enumerate(sections) if s.title.lower() != title or i == sections.index([sec for sec in sections if sec.title.lower() == title][0])]
        elif typ == "normalize_timestamps":
            # Simple ISO normalization
            for s in sections:
                s.raw = re.sub(r"\b(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)\b", r"\1:\2 \3", s.raw)
                s.raw = re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", r"\3-\2-\1", s.raw)
        elif typ == "collapse_empty_sections":
            sections = [s for s in sections if s.content.strip()]
        elif typ == "sort_sections":
            sections.sort(key=lambda s: (s.level, s.title.lower()))
    # Write cleaned sections
    for s in sections:
        lines.append(s.raw)
        lines.append("")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return {
        "original_sections": len(info.sections),
        "cleaned_sections": len(sections),
        "output_path": output_path,
        "steps_applied": steps
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python md_utils.py <path_to_md>")
        sys.exit(1)
    path = sys.argv[1]
    info = parse_markdown(path)
    print(json.dumps(info.__dict__, default=str, indent=2))
    steps = suggest_md_cleaning(info)
    print("Suggested steps:", json.dumps(steps, indent=2))
