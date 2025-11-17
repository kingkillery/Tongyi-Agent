# Tongyi Agent Stress Test – Error Log

**Date:** 2025-11-17

## Command Summary

| # | Command | Result | Notes |
| - | ------- | ------ | ----- |
| 1 | `python src\\load_test.py` | ✅ Pass | `LoadReport(n_tasks=80, concurrency=16, latency_p50_ms=656.92, latency_p95_ms=1198.37, errors=0, throughput_qps=64.82)` |
| 2 | `python -c "import sys; ... run_load(n_tasks=200, concurrency=32)"` | ✅ Pass | `LoadReport(... latency_p50_ms=909.32, latency_p95_ms=1405.89, errors=0, throughput_qps=141.60)` |
| 3 | `python eval_runner.py tests\\fixtures\\repo_qa.jsonl` | ❌ Fail | Windows console rejected UTF-8 checkmark (`UnicodeEncodeError: '\u2713' ...`). |
| 4 | `cmd /C "set PYTHONIOENCODING=utf-8 && python eval_runner.py ..."` | ✅ Pass | Fixture run succeeded: 4/4 questions verified with citations. |
| 5 | `python -c "... LocalOrchestrator ... ThreadPoolExecutor ..."` | ⚠️ Partial | 20 runs, 4 errors (`name 'json' is not defined` from sandbox delegate). |
| 6 | `python -m pytest -q` | ❌ Fail | `tests/test_tongyi_orchestrator.py::test_get_tool_usage_summary` expected 7 tools but found 11. |

## Detailed Failure Notes

### 1. UTF-8 Output Error (Command #3)
- **Trace:** `UnicodeEncodeError: 'charmap' codec can't encode character '\u2713' ... cp1252`.
- **Impact:** Evaluation runner aborted before summarizing per-question results.
- **Workaround:** Reran under `cmd` with `PYTHONIOENCODING=utf-8`, after which the fixture completed successfully (Command #4).

### 2. Sandbox Delegate Missing Import (Command #5)
- **Command Output (excerpt):**
  ```json
  {
    "total_runs": 20,
    "error_count": 4,
    "errors": [
      {
        "question": "How does the sandbox delegate run computations?",
        "status": "error",
        "error": "name 'json' is not defined",
        "duration_ms": 3127.6471614837646
      },
      { "question": "How does the sandbox delegate run computations?", "status": "error", "error": "name 'json' is not defined", "duration_ms": 2975.8639335632324 }
    ],
    "avg_ms": 2255.807316303253,
    "p95_ms": 3299.562692642212,
    "max_ms": 3603.532075881958
  }
  ```
- **Likely Cause:** `_delegate_sandbox` in `src/orchestrator_local.py` references `json` but the module is not imported at the file top. Under concurrent load, every sandbox invocation that tries to parse JSON fails immediately.
- **Effect:** Delegated sandbox operations cannot execute, limiting computation-heavy tasks.

### 3. Pytest Failure (Command #6)
- **Failure Snippet:**
  ```
  E       assert summary["total_tools"] == 7
  E       assert 11 == 7
  tests\test_tongyi_orchestrator.py:266
  ```
- **Context:** `TestTongyiOrchestrator.test_get_tool_usage_summary` now observes 11 registered tools, but the test still expects 7. Either the registry grew (e.g., new delegates or tools) or stale expectations need updating.
- **Additional Warnings:** Multiple `PytestReturnNotNoneWarning` notices and async fixture scope warning surfaced; no additional test failures observed.

### 4. UnicodeDecodeError During UTF-8 Mode Retry (Command #3 rerun)
- **Trace:** `UnicodeDecodeError: 'utf-8' codec can't decode byte 0x85 ...` followed by `AttributeError: 'NoneType' object has no attribute 'strip'` because subprocess stdout capture failed.
- **Resolution:** Switching to `cmd` with explicit `PYTHONIOENCODING` (Command #4) avoided the decode issue entirely.

## Next Steps (Suggested)
1. Import `json` inside `src/orchestrator_local.py` to unblock sandbox delegate calls and rerun the parallel stress harness.
2. Align `tests/test_tongyi_orchestrator.py::test_get_tool_usage_summary` with the current tool registry (update expected count or filter), then rerun `pytest -q`.
3. Consider forcing UTF-8 output (e.g., via `PYTHONIOENCODING` or `-X utf8`) inside `eval_runner.py` to keep fixtures portable across Windows consoles.
