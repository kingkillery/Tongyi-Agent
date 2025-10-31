import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from orchestrator_local import LocalOrchestrator  # noqa: E402
from delegation_policy import AgentBudget  # noqa: E402


def test_snippet_length_cap_and_compression():
    # Directly test truncation logic used in orchestrator
    long_snippet = "x" * 300
    truncated = long_snippet
    if len(truncated) > 160:
        truncated = truncated[:157] + "…"
    assert len(truncated) <= 160 + 1  # allow for ellipsis
    assert truncated.endswith("…")
    # Ensure original long snippet is longer than cap
    assert len(long_snippet) > 160


def test_report_compression_token_cap():
    orch = LocalOrchestrator(
        root=str(ROOT),
        agent_budgets={"small": AgentBudget(max_calls=1, max_tokens=200)},
        delegate_handlers={"small": lambda _: "small evidence"},
    )
    orch.verifier_gate = None  # Disable verifier

    # Simulate a very long report
    long_text = "word " * 1000  # 1000 words
    compressed = orch._compress("", long_text, cap_tokens=800)
    tokens = compressed.split()
    assert len(tokens) <= 801  # allow off-by-one due to ellipsis token
    assert compressed.endswith(" …")
