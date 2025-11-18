"""
Agent Budget Configuration
---------------------------
Centralized budget limits for all tools and delegation agents.
"""
from delegation_policy import AgentBudget

# Default agent budgets for tool-based orchestrators
DEFAULT_AGENT_BUDGETS = {
    "search_code": AgentBudget(max_calls=10, max_tokens=2000),
    "read_file": AgentBudget(max_calls=20, max_tokens=1000),
    "run_sandbox": AgentBudget(max_calls=5, max_tokens=1500),
    "search_papers": AgentBudget(max_calls=3, max_tokens=1000),
    "clean_csv": AgentBudget(max_calls=2, max_tokens=800),
    "clean_markdown": AgentBudget(max_calls=2, max_tokens=800),
    "summarize_results": AgentBudget(max_calls=5, max_tokens=1200),
}

# Default budgets for delegation-based orchestrators
DEFAULT_DELEGATION_BUDGETS = {
    "tongyi": AgentBudget(max_calls=3, max_tokens=1200),
    "small": AgentBudget(max_calls=2, max_tokens=400),
    "sandbox": AgentBudget(max_calls=2, max_tokens=600),
    "scholar": AgentBudget(max_calls=2, max_tokens=500),
    "csv_cleaner": AgentBudget(max_calls=2, max_tokens=800),
    "md_cleaner": AgentBudget(max_calls=2, max_tokens=700),
}
