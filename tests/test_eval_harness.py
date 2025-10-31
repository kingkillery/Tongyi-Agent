import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from delegation_policy import AgentBudget  # noqa: E402
from orchestrator_local import LocalOrchestrator  # noqa: E402
from verifier_gate import VerifierGate  # noqa: E402


def test_eval_harness_repo_qa_fixture():
    fixture = ROOT / "tests" / "fixtures" / "repo_qa.jsonl"
    assert fixture.exists()

    orch = LocalOrchestrator(
        root=str(ROOT),
        agent_budgets={
            "small": AgentBudget(max_calls=1, max_tokens=200),
            "tongyi": AgentBudget(max_calls=1, max_tokens=200),
        },
        delegate_handlers={
            "small": lambda _: "small evidence",
            "tongyi": lambda _: "tongyi evidence",
        },
    )
    # Force fallback verification for deterministic tests
    orch.verifier_gate = VerifierGate(tongyi_client=None)

    with open(fixture, "r", encoding="utf-8") as fh:
        lines = [json.loads(l) for l in fh if l.strip()]

    found_with_citations = 0
    for row in lines:
        q = row["q"]
        out = orch.run(q)
        if "[" in out and "]" in out:
            found_with_citations += 1
    # Expect at least one verified claim with citations across the fixture
    assert found_with_citations >= 1
