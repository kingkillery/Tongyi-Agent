#!/usr/bin/env python3
"""CLI runner for JSONL evaluation fixtures.

Usage: python eval_runner.py tests/fixtures/repo_qa.jsonl
Emits a summary of verified/total claims.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_orchestrator(question: str) -> str:
    """Run orchestrator as a subprocess to avoid import issues."""
    code = f"""
import sys; sys.path.insert(0, '.')
from src.orchestrator_local import LocalOrchestrator
from src.verifier_gate import VerifierGate
orch = LocalOrchestrator()
orch.verifier_gate = VerifierGate(tongyi_client=None)  # enable deterministic verifier
print(orch.run({repr(question)}))
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )
    if result.returncode != 0:
        return f"Error: {result.stderr.strip()}"
    return result.stdout.strip()


def run_fixture(fixture_path: Path) -> dict:
    """Run orchestrator on all questions in a JSONL fixture."""
    results = []
    with open(fixture_path, "r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            item = json.loads(line)
            q = item["q"]
            out = run_orchestrator(q)
            has_citations = "[" in out and "]" in out
            results.append({"q": q, "output": out, "has_citations": has_citations})
    return {"total": len(results), "verified": sum(1 for r in results if r["has_citations"]), "results": results}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run evaluation on JSONL fixtures")
    parser.add_argument("fixture", type=Path, help="Path to JSONL fixture file")
    args = parser.parse_args()

    if not args.fixture.exists():
        sys.exit(f"Fixture not found: {args.fixture}")

    summary = run_fixture(args.fixture)
    print(f"Fixture: {args.fixture}")
    print(f"Total questions: {summary['total']}")
    print(f"Verified (with citations): {summary['verified']}")
    print(f"Rate: {summary['verified'] / summary['total']:.2%}" if summary["total"] else "N/A")
    # Optionally show per-item details
    for item in summary["results"]:
        status = "✓" if item["has_citations"] else "✗"
        print(f"  {status} {item['q']}")


if __name__ == "__main__":
    main()
