# PLAN.md — Roadmap & Milestones

Scope: Repository‑wide delivery plan. Keep this document short and current. Update when interfaces, dependencies, or targets change.

## Objectives (Q4–Q1 2025)

### Primary: Beta Release of Tongyi CLI Tool
- Ship production-ready interactive CLI for deep research using small, capable models.
- Achieve 100% test pass rate (currently 87% - 84/96 passing).
- Fix critical blockers preventing beta release.
- Deliver robust CLI tool for public use.

### Secondary: ReAct Loop & DeepResearch Core
- Complete dual-mode (ReAct + Heavy) agentic loop using Tongyi DeepResearch via OpenRouter.
- Maintain bounded context with Markovian state (Q, R_t, O_t) and rigorous verification.
- Hit performance targets: ≥5 concurrent queries/agent, low drift (<2%), ≥90% cross-source consistency.
- Harden risk controls for scanning, verification, concurrency, and delegation before adding new capabilities.

## Current State (2025-12-23)

### CLI Readiness Assessment
- **Test Coverage**: 96/96 passing (100% pass rate) - All tests passing
- **Critical Blockers**: None (all resolved)
- **Completed Features**:
  - Enhanced error handling with user-friendly messages (BETA-3 completed)
  - Retry mechanisms with exponential backoff for network failures
  - Graceful fallbacks for API failures
  - Improved input validation with clear error messages
- **Remaining Incomplete Implementations**:
  - `src/react_parser.py:157` - REACT parser logic
  - `src/md_utils.py:48` - Markdown processing
  - `src/orchestrator_base.py:81,93` - Base orchestrator methods
  - Minor cases in symbol_index.py, scholar_adapter.py

### Completed Features (Production-Ready)
- ✅ Rich interactive CLI with modern terminal UI
- ✅ Session management with history persistence
- ✅ Model management system (switch, search, list models)
- ✅ Tool registry (7+ tools: search_code, read_file, run_sandbox, search_papers, clean_csv, clean_markdown, summarize_results)
- ✅ Configuration management via INI files (models.ini)
- ✅ Agent Lightning integration (optional, requires installation)
- ✅ Security: path traversal protection, data sanitization, input validation
- ✅ Cross-platform support (Windows, macOS, Linux)
- ✅ Documentation: README.md, CLI_GUIDE.md, INSTALLATION_GUIDE.md, RELEASE_NOTES.md

### Completed DeepResearch Scaffolds
- Scholar adapter (stubs), Sandbox exec, CAS store, Drift monitor, Load harness
- JSON Schemas in `schemas/` for key artifacts (evidence, paper_meta, artifact_blob, drift_tick, load_report)
- AGENTS.md updated with verification workflow and SymbolIndex (2025-10-30)
- ReAct parser + data iterator guidance added (2025-10-31)
- Risk triage completed (2025-10-31)
- Local orchestrator wired to adaptive planner, delegation policy, CodeSearch/FileRead tools, and OpenRouter client
- VerifierGate constructor hardened with sentinel-based client handling
- CodeSearch now skips VCS/binary blobs when collecting evidence
- Local orchestrator falls back to repo-wide search when stage hits are empty
- Evaluation harness: JSONL fixtures and pytest checks for citation enforcement
- ReAct parser normalizes free-form Thought/Action/Observation blocks to structured tool calls
- Data iteration scaffold iteratively refines datasets with CAS-backed caching

### Known Gaps
- Current staged orchestrator is too rigid; migrating to DeepResearch-style ReAct loop where model plans tool usage end-to-end
- Sandbox STDIO_LIMIT constant missing (critical blocker)
- ClaudeAgentOrchestrator lacks concrete run() implementation (critical blocker)
- Some incomplete implementations with pass statements

## Workstreams

### BETA: Beta Release Preparation (Priority: CRITICAL, Target: 1-2 weeks)

**BETA-1: Fix Critical Test Failures**
- Define `STDIO_LIMIT = 64 * 1024` in `src/sandbox_exec.py` (fixes 5 tests)
- Implement abstract `run()` method in `ClaudeAgentOrchestrator` (fixes 6 tests)
- Fix API key validation test behavior (1 test)
- Goal: Achieve 100% test pass rate

**BETA-2: Complete Incomplete Implementations**
- Complete `src/react_parser.py:157` - REACT parser logic for natural-language blocks
- Complete `src/md_utils.py:48` - Markdown processing functions
- Implement missing methods in `src/orchestrator_base.py:81,93`
- Address remaining pass statements in symbol_index.py, scholar_adapter.py, model_manager.py

**BETA-3: Enhanced Error Handling** ✅ COMPLETED (2025-12-23)
- Add user-friendly error messages for common failure scenarios (API unavailability, invalid config)
- Implement graceful fallbacks for API failures (OpenRouter down, rate limits)
- Add retry mechanisms for network failures (exponential backoff with jitter)
- Improve input validation with clear, actionable error messages

**BETA-4: Configuration Validation Tool**
- Complete `config_validator.py` CLI tool (partially implemented)
- Add API key validation and connection testing
- Add model availability checking against OpenRouter
- Create setup troubleshooting guide and documentation
- Add --validate-config flag to CLI

**BETA-5: Beta Testing & Documentation**
- Add simple usage examples for beginners in README
- Create integration examples with other tools (IDEs, CI/CD)
- Write developer setup guide for contributors
- Create "First 5 Minutes" getting started guide
- Add FAQ section addressing common issues

**BETA-6: Performance Basics** ✅ COMPLETED (2025-12-23)
- Implement basic caching for repeated API calls
- Add response time improvements through smarter tool selection
- Optimize memory usage for large file processing
- Add performance metrics to status command

**BETA-7: Release Preparation** ✅ COMPLETED (2025-12-23)
- Version bump to v1.0.0-beta.1
- Create PyPI distribution package
- Write comprehensive release notes
- Prepare GitHub release with changelog
- Set up issue templates for beta testers

### 0) ReAct Loop Migration (H0) - Post-Beta
- Replace staged orchestrator with model-driven ReAct executor (system prompt + tool schema + iterative loop).
- Integrate `react_parser` into orchestrator to handle natural-language ReAct traces and feed consistent tool invocations.
- Expose local tools (search, visit/read, python, file parse) via unified registry; ensure sandbox + CAS integration remain accessible.
- Extend regression tests to cover parser/executor edge cases (malformed JSON, missing Thought/Action tags).
- Sunset brittle CodeSearch-only flow; keep CodeSearch as optional local evidence tool callable by model.

### 1) Scholar Integration (H1) - Post-Beta
- Integrate providers (Semantic Scholar, Crossref, arXiv) with API keys and TOS.
- Add reranker (bge‑small) and NLI verifier (deberta‑v3‑mnli small) gates.
- Tests: metadata normalization, rate‑limit handling, fallback correctness.

### 2) Sandbox Enforcement (H2) - Post-Beta
- Optional: containerized isolation (Docker/cgroups); resource caps, no‑net.
- Determinism: fixed seeds, stdout/stderr caps, audit logs.

### 3) Artifact Store (H3) - Post-Beta
- Wire CAS in fetchers/parsers; canonical URL normalization.
- TTL policies per domain class; offline benchmark cache freeze.

### 4) Drift & Compression (H4) - Post-Beta
- Hook DriftMonitor into orchestrator; adaptive compression + verify‑k.
- Metrics export for drift and R_t token size.

### 5) Load & Evaluation (H5) - Post-Beta
- Expand load harness with real tools; P50/P95 dashboards.
- Evaluation runner for JSONL I/O; reproducible seeds and caches.

### 6) DeepResearch Data Generation (H6) - Post-Beta
- Wire `DataIterator` into orchestration pipeline for slow/high-quality dataset curation workflows.
- Provide dataset-specific transform/quality recipes with reproducible seeds + CAS provenance.
- Add pytest coverage for iteration stats, CAS writes, and verifier fallback behaviors.

## Milestones

### Beta Release Milestones (Target: 2025-01-15)
- **BETA-M1**: Critical test failures fixed (100% pass rate) - ✅ COMPLETED (2025-12-23)
- **BETA-M2**: All incomplete implementations completed - IN PROGRESS
- **BETA-M3**: Configuration validation tool functional - IN PROGRESS
- **BETA-M4**: Beta documentation complete and PyPI package uploaded - PENDING
- **BETA-M5**: Public beta launch announcement - PENDING

### DeepResearch Core Milestones (Dates TBD, Post-Beta)
- M1: Provider integration + smoke tests pass.
- M2: Orchestrator end‑to‑end (ReAct + Heavy) with drift gating.
- M3: Evaluation suite green on baseline tasks.
- M4: Load test meets throughput/latency targets.

## Risks & Mitigations

### Beta Release Risks
- **Test failures blocking release** → Prioritize BETA-1, fix STDIO_LIMIT and ClaudeAgentOrchestrator immediately
- **Poor user experience** → Add BETA-3 (error handling) and BETA-5 (documentation)
- **Configuration complexity** → Complete BETA-4 (config validator) and simplify setup
- **Beta churn/feedback overhead** → Document scope clearly, manage expectations
- **API rate limits** → Implement caching (BETA-6), add clear rate limit messaging

### DeepResearch Risks
- Rate limits → per-host buckets, backoff, cache; fallback providers.
- Parser brittleness → reader-mode fallback, domain rules.
- Drift under saturation → adaptive compression, raise verify-k, reduce concurrency.
- False consensus → independent-domain requirement; hash-based dedup.
- Latency blowup from over-scan → manifest + tiered scanning, observation token caps.
- Weak claims entering report → verifier gate (def+use or two cites + NLI entailment).
- File I/O contention → per-path concurrency semaphore and autoshedding.
- Delegation prompt bloat → strict budget, compress responses before merging.

## Quick Commands

### Beta Testing
- `python -m pytest tests/ -q` → Run full test suite
- `python src/tongyi_agent/cli.py --help` → Verify CLI entry point
- `python src/tongyi_agent/cli.py` → Start interactive mode
- `python -m config_validator --check-openrouter` → Validate configuration

### DeepResearch Development
- Smokes: `python src/sandbox_exec.py` | `python src/cas_store.py` | `python src/drift_monitor.py` | `python src/load_test.py`
- Scholar stub: `python src/scholar_adapter.py`

## Next Agent Prompt

Context:
- Beta release is primary focus (2025-01-15 target) with critical test failures blocking progress
- DeepResearch core workstreams (H0-H6) are post-beta priorities
- CLI is production-ready feature-wise but needs bug fixes and polish

Beta Release Objectives (BETA-1 through BETA-7):
1. Fix critical test failures (STDIO_LIMIT, ClaudeAgentOrchestrator.run(), API key validation)
2. Complete all incomplete implementations (react_parser, md_utils, orchestrator_base, etc.)
3. Enhance error handling with user-friendly messages and graceful fallbacks
4. Complete configuration validation CLI tool
5. Add comprehensive documentation for beta testers
6. Implement basic performance optimizations (caching, memory)
7. Prepare and upload v1.0.0-beta.1 to PyPI

Constraints:
- Maintain all existing interfaces and backward compatibility
- Keep test coverage at or above 95%
- Document all breaking changes
- Ensure Windows, macOS, Linux compatibility
- Keep documentation (AGENTS.md / PLAN.md / README.md) synchronized

Deliverables:
- 100% test pass rate (96/96 tests passing)
- Complete implementation of all core modules (no pass statements in production code)
- User-friendly error messages and retry/fallback mechanisms
- Working `python -m config_validator --check-openrouter` command
- PyPI package `tongyi-cli-interactive` v1.0.0-beta.1
- Comprehensive beta documentation (setup guide, examples, FAQ)
