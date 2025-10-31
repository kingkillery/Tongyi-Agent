from delegation_policy import AgentBudget, DelegationPolicy


def test_delegation_budget_enforced():
    policy = DelegationPolicy(agent_budgets={"agent": AgentBudget(max_calls=1, max_tokens=10)})
    assert policy.allow("agent") is True
    compressed = policy.record("agent", "token token token token")
    assert compressed
    assert policy.allow("agent") is False
    assert policy.metrics["calls.agent"] == 1
    assert policy.metrics["deny.agent"] == 1
