import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from delegation_policy import AgentBudget  # noqa: E402
from orchestrator_local import LocalOrchestrator  # noqa: E402
from verifier_gate import VerifierGate  # noqa: E402


def test_orchestrator_sandbox_delegate():
    # Override delegates to control sandbox behavior
    def handler_sandbox(prompt: str) -> str:
        # Echo back the code field for test verification
        lines = prompt.splitlines()
        code_line = next((ln for ln in lines if ln.startswith("code=")), "")
        code = code_line.partition("=")[2] if code_line else ""
        return json.dumps({"ok": True, "stdout": f"executed: {code}", "stderr": "", "returncode": 0, "ms": 10, "isolated": False, "container": None}, separators=(",", ":"))

    orch = LocalOrchestrator(
        root=str(ROOT),
        agent_budgets={
            "sandbox": AgentBudget(max_calls=1, max_tokens=200),
        },
        delegate_handlers={
            "sandbox": handler_sandbox,
        },
    )
    orch.verifier_gate = None  # Disable verification for this test

    # Question that triggers sandbox heuristic
    result = orch.run("Compute the sum of 0 to 9")
    # Should contain sandbox delegation output
    assert "Delegate sandbox ->" in result
    # Should echo the executed code
    assert "executed:" in result


def test_orchestrator_sandbox_budget_enforcement():
    # Test that sandbox delegate respects call budget
    calls = {"sandbox": 0}
    def handler_sandbox(prompt: str) -> str:
        calls["sandbox"] += 1
        return json.dumps({"ok": True, "stdout": "ok", "stderr": "", "returncode": 0, "ms": 5, "isolated": False, "container": None}, separators=(",", ":"))

    orch = LocalOrchestrator(
        root=str(ROOT),
        agent_budgets={
            "sandbox": AgentBudget(max_calls=1, max_tokens=200),
        },
        delegate_handlers={
            "sandbox": handler_sandbox,
        },
    )
    orch.verifier_gate = None

    # First run should call sandbox
    orch.run("run something")
    assert calls["sandbox"] == 1
    # Second run should exceed budget and not call sandbox
    orch.run("run again")
    assert calls["sandbox"] == 1  # unchanged


def test_orchestrator_sandbox_error_handling():
    def handler_sandbox(prompt: str) -> str:
        return "sandbox_error: no code provided"

    orch = LocalOrchestrator(
        root=str(ROOT),
        agent_budgets={"sandbox": AgentBudget(max_calls=1, max_tokens=200)},
        delegate_handlers={"sandbox": handler_sandbox},
    )
    orch.verifier_gate = None

    result = orch.run("execute something")
    # Should include error message in observation
    assert "sandbox_error" in result
