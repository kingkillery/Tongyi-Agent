"""Adaptive planner staging logic for local-first research loop.

Phases
------
1) Manifest scan (sequential) — gather file metadata (size, hash hint, mtime).
2) Tiered exploration — prioritize high-signal directories (src/, schemas/, docs/) before low-value dirs.
3) Concurrency throttle — dynamically adjust fan-out per tier based on file counts and observed latency.

The planner outputs `PlanStage` objects describing the phase, target paths, and
concurrency caps. Execution loop can consume these sequentially while honoring
per-stage budgets.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, List, Tuple

HIGH_SIGNAL_DIRS = ("src", "schemas", "docs")


@dataclass
class ManifestEntry:
    path: str
    size: int
    mtime: float


@dataclass
class PlanStage:
    name: str
    paths: List[str]
    max_concurrency: int
    notes: str


def build_manifest(root: str = ".") -> List[ManifestEntry]:
    entries: List[ManifestEntry] = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            path = os.path.join(dirpath, fname)
            try:
                stat = os.stat(path)
            except (FileNotFoundError, PermissionError, OSError):
                continue
            entries.append(ManifestEntry(path=path, size=stat.st_size, mtime=stat.st_mtime))
    return entries


def _tier_paths(entries: Iterable[ManifestEntry]) -> Tuple[List[str], List[str]]:
    tier1: List[str] = []
    tier2: List[str] = []
    for entry in entries:
        rel = entry.path.replace("\\", "/")
        parts = rel.split("/")
        if len(parts) == 0:
            continue
        if parts[0] in HIGH_SIGNAL_DIRS:
            tier1.append(entry.path)
        else:
            tier2.append(entry.path)
    return (sorted(tier1), sorted(tier2))


def plan_stages(entries: List[ManifestEntry], base_concurrency: int = 16) -> List[PlanStage]:
    tier1, tier2 = _tier_paths(entries)
    # limit concurrency proportionally to volume to avoid overwhelming IO
    def cap(paths: List[str]) -> int:
        if not paths:
            return 0
        return max(4, min(base_concurrency, max(4, len(paths) // 8)))

    stages: List[PlanStage] = [
        PlanStage(name="manifest", paths=[], max_concurrency=1, notes="sequential metadata scan"),
        PlanStage(name="tier1", paths=tier1, max_concurrency=cap(tier1), notes="high-signal dirs first"),
        PlanStage(name="tier2", paths=tier2, max_concurrency=max(2, cap(tier2) // 2), notes="remaining dirs throttled"),
    ]
    return stages


if __name__ == "__main__":
    manifest = build_manifest()
    stages = plan_stages(manifest)
    for stage in stages:
        print(stage.name, len(stage.paths), "max_concurrency", stage.max_concurrency, stage.notes)
