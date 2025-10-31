"""
Drift Monitor + Adaptive Pruning
--------------------------------
Computes cosine drift between successive compressed reports (R_{t-1}, R_t)
using a simple bag-of-words vectorizer (no external deps). Provides an
adaptive policy that recommends compression aggressiveness and verification
threshold adjustments when drift exceeds configured thresholds.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def _bow(text: str) -> Dict[str, int]:
    v: Dict[str, int] = {}
    for tok in TOKEN_RE.findall(text.lower()):
        v[tok] = v.get(tok, 0) + 1
    return v


def _cosine(a: Dict[str, int], b: Dict[str, int]) -> float:
    if not a or not b:
        return 0.0
    dot = 0.0
    for k, va in a.items():
        vb = b.get(k)
        if vb:
            dot += va * vb
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


@dataclass
class DriftTick:
    step: int
    cosine_sim: float
    drift_rate: float  # 1 - cosine
    action: str        # advisory


class DriftMonitor:
    def __init__(self, warn_threshold: float = 0.98, danger_threshold: float = 0.95):
        self.warn = warn_threshold
        self.danger = danger_threshold

    def measure(self, step: int, prev: str, curr: str) -> DriftTick:
        a = _bow(prev)
        b = _bow(curr)
        sim = _cosine(a, b)
        drift = 1.0 - sim
        if sim < self.danger:
            action = "increase_compression;raise_verify_k;reduce_concurrency"
        elif sim < self.warn:
            action = "increase_compression_slight;prefer_high_authority_sources"
        else:
            action = "stable"
        return DriftTick(step=step, cosine_sim=sim, drift_rate=drift, action=action)


if __name__ == "__main__":
    dm = DriftMonitor()
    t1 = "OpenAI Codex CLI logs RUST_LOG info; Markov state {Q,R,O}."
    t2 = "Markovian state keeps Q, report, last observation; logging configured via RUST_LOG."
    tick = dm.measure(3, t1, t2)
    print(tick)

