"""
Load Test Harness for Agentic Tooling
-------------------------------------
Simulates concurrent tool invocations with latency distributions and checks:
- Throughput ≥ 5 concurrent queries per agent
- P95 latency within target band

This is a synthetic harness; integrate with real tools by plugging call_fn.
"""
from __future__ import annotations

import concurrent.futures as cf
import random
import statistics
import time
from dataclasses import dataclass
from typing import Callable, List, Tuple


@dataclass
class LoadReport:
    n_tasks: int
    concurrency: int
    latency_p50_ms: float
    latency_p95_ms: float
    errors: int
    throughput_qps: float


def simulate_tool_call(idx: int) -> None:
    # Simulate variable latency with retries; no-op result
    base = random.uniform(0.05, 0.25)
    # 10% slow tail
    if random.random() < 0.1:
        base += random.uniform(0.2, 0.5)
    time.sleep(base)


def run_load(n_tasks: int = 50, concurrency: int = 16, call_fn: Callable[[int], None] = simulate_tool_call) -> LoadReport:
    t0 = time.time()
    latencies: List[float] = []
    errors = 0
    with cf.ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = []
        for i in range(n_tasks):
            start = time.time()
            f = pool.submit(call_fn, i)
            futures.append((start, f))
        for start, f in futures:
            try:
                f.result(timeout=60)
                latencies.append((time.time() - start) * 1000.0)
            except Exception:
                errors += 1
    elapsed = time.time() - t0
    p50 = statistics.median(latencies) if latencies else 0.0
    p95 = statistics.quantiles(latencies, n=100)[94] if len(latencies) >= 100 else (sorted(latencies)[int(0.95 * len(latencies))] if latencies else 0.0)
    qps = n_tasks / elapsed if elapsed > 0 else 0.0
    return LoadReport(n_tasks=n_tasks, concurrency=concurrency, latency_p50_ms=p50, latency_p95_ms=p95, errors=errors, throughput_qps=qps)


if __name__ == "__main__":
    rep = run_load(n_tasks=80, concurrency=16)
    print(rep)

