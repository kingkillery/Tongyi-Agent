import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from delegation_policy import AgentBudget  # noqa: E402
from orchestrator_local import LocalOrchestrator  # noqa: E402


def test_orchestrator_uses_delegate_and_planner(tmp_path):
    root = ROOT

    calls = {"small": 0, "tongyi": 0}

    def handler_small(prompt: str) -> str:
        calls["small"] += 1
        return "small evidence"

    def handler_tongyi(prompt: str) -> str:
        calls["tongyi"] += 1
        return "tongyi evidence"

    orch = LocalOrchestrator(
        root=str(root),
        agent_budgets={
            "small": AgentBudget(max_calls=2, max_tokens=200),
            "tongyi": AgentBudget(max_calls=1, max_tokens=200),
        },
        delegate_handlers={
            "small": handler_small,
            "tongyi": handler_tongyi,
        },
    )
    result = orch.run("delegation budget")
    assert "small evidence" in result
    assert "tongyi evidence" in result
    assert calls["small"] >= 1
    assert calls["tongyi"] == 1
