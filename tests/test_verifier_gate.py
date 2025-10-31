import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.verifier_gate import VerifierGate  # type: ignore  # noqa: E402


def test_verifier_gate_citation_and_independence_no_client():
    # Force fallback by passing tongyi_client=None
    vg = VerifierGate(tongyi_client=None)

    # Two independent local files should pass basic validation
    claim = vg.verify_claim(
        "Delegation budgets control token usage",
        ["src/delegation_policy.py:70", "src/orchestrator_local.py:100"],
    )
    assert claim.verified is True
    assert claim.confidence >= 0.8


def test_verifier_gate_insufficient_citations():
    vg = VerifierGate(tongyi_client=None)
    claim = vg.verify_claim(
        "System is fast",
        ["src/orchestrator_local.py:1"],
    )
    assert claim.verified is False


def test_verifier_gate_independent_sources_same_domain_files():
    vg = VerifierGate(tongyi_client=None)
    # Different files count as independent for local sources
    claim = vg.verify_claim(
        "Uses CodeSearch and Verifier",
        ["src/code_search.py:10", "src/verifier_gate.py:10"],
    )
    assert claim.verified is True
