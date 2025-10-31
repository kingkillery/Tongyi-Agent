import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from delegation_policy import AgentBudget  # noqa: E402
from orchestrator_local import LocalOrchestrator  # noqa: E402
from verifier_gate import VerifierGate  # noqa: E402


def test_orchestrator_verifies_claims_with_citations():
    # Override delegates to avoid network
    def handler_small(prompt: str) -> str:
        return "small evidence"

    def handler_tongyi(prompt: str) -> str:
        return "tongyi evidence"

    orch = LocalOrchestrator(
        root=str(ROOT),
        agent_budgets={
            "small": AgentBudget(max_calls=1, max_tokens=200),
            "tongyi": AgentBudget(max_calls=1, max_tokens=200),
        },
        delegate_handlers={
            "small": handler_small,
            "tongyi": handler_tongyi,
        },
    )
    # Force fallback verification (no network)
    orch.verifier_gate = VerifierGate(tongyi_client=None)

    result = orch.run("delegation policy")
    # Expect bracketed citations appended by verifier in report
    assert "[" in result and "]" in result
