"""Delegation policy engine for multi-model routing.

Responsibilities
----------------
- Enforce per-task delegation budgets (max calls, max tokens) per agent_id.
- Track usage and refuse further calls when limits hit.
- Compress delegated responses before they enter shared context (Markov R_t).
- Provide basic instrumentation hooks for observability.

This module is intentionally lightweight so it can be called as a tool. The
compressor is deterministic and truncates at sentence boundaries to keep token
growth in check. Swap with a learned summarizer later if needed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


def _truncate(text: str, max_tokens: int) -> str:
    """Naive token approximation (whitespace split) to keep runtime simple."""
    tokens = text.split()
    if len(tokens) <= max_tokens:
        return text
    return " ".join(tokens[:max_tokens]) + " …"


def _compress(text: str, max_tokens: int = 120) -> str:
    if not text:
        return ""
    shortened = _truncate(text, max_tokens)
    # attempt to trim at sentence boundary for readability
    last_period = shortened.rfind(".")
    if last_period != -1 and last_period > 20:
        return shortened[: last_period + 1]
    return shortened


@dataclass
class AgentBudget:
    max_calls: int
    max_tokens: int
    calls_used: int = 0
    tokens_used: int = 0

    def consume(self, tokens: int) -> None:
        self.calls_used += 1
        self.tokens_used += tokens

    def remaining_calls(self) -> int:
        return max(0, self.max_calls - self.calls_used)

    def remaining_tokens(self) -> int:
        return max(0, self.max_tokens - self.tokens_used)

    def at_limit(self) -> bool:
        return self.calls_used >= self.max_calls or self.tokens_used >= self.max_tokens


@dataclass
class DelegationPolicy:
    agent_budgets: Dict[str, AgentBudget]
    default_tokens: int = 400
    trace_id: Optional[str] = None
    metrics: Dict[str, int] = field(default_factory=dict)

    def allow(self, agent_id: str) -> bool:
        budget = self.agent_budgets.get(agent_id)
        if not budget:
            return False
        allowed = not budget.at_limit()
        if not allowed:
            self._inc_metric(f"deny.{agent_id}")
        return allowed

    def record(self, agent_id: str, response_text: str) -> str:
        budget = self.agent_budgets.get(agent_id)
        if not budget:
            raise ValueError(f"unknown agent_id {agent_id}")
        compressed = _compress(response_text, max_tokens=min(budget.remaining_tokens(), self.default_tokens))
        compressed_tokens = len(compressed.split())
        budget.consume(compressed_tokens)
        self._inc_metric(f"calls.{agent_id}")
        self._inc_metric("calls.total")
        return compressed

    def remaining(self, agent_id: str) -> tuple[int, int]:
        budget = self.agent_budgets.get(agent_id)
        if not budget:
            return (0, 0)
        return (budget.remaining_calls(), budget.remaining_tokens())

    def _inc_metric(self, key: str, inc: int = 1) -> None:
        self.metrics[key] = self.metrics.get(key, 0) + inc


if __name__ == "__main__":  # simple smoke test
    policy = DelegationPolicy(
        agent_budgets={
            "tongyi": AgentBudget(max_calls=3, max_tokens=1200),
            "small": AgentBudget(max_calls=2, max_tokens=400),
        },
        trace_id="demo",
    )
    sample = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 10
    if policy.allow("tongyi"):
        out = policy.record("tongyi", sample)
        print("compressed", len(out.split()), "tokens", "remaining", policy.remaining("tongyi"))
