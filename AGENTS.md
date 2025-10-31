# AGENTS.md — Agent Heuristics & Operating Guide

Scope: Entire repository. This file defines conventions, patterns, and guardrails for agents and humans working on this codebase. Keep outputs terse; prefer structure over prose. Optimize for token and time efficiency.

- Roadmap & TODOs live in `PLAN.md`. Update that file (not @todo.md) when interfaces, dependencies, or targets change, then reflect any operating guidance deltas here.

- ReAct migration (2025-10-31): staged orchestrator is being replaced by a model-driven loop. System prompt advertises tools; the model emits `<tool_call>` blocks; orchestrator parses, executes, and feeds `<tool_response>` back until `<answer>` terminates. CodeSearch remains available but no longer drives the flow.

- ReAct entrypoint (`src/tongyi_orchestrator.py`): **[INTEGRATED]** Uses `ReActParser` to support natural-language Thought/Action/Observation blocks alongside structured JSON tool calls. Dispatch chain: OpenRouter `tool_calls` → JSON fallback (`{"tool": ..., "parameters": ...}`) → ReAct natural-language parsing. All routes execute via `tool_registry` and enforce `delegation_policy` budgets.
  - Natural-language ReAct responses are normalized via `src/react_parser.py` during dispatch (lines 235–283 in `tongyi_orchestrator.py`); parser extracts Thought/Action/Observation blocks and JSON tool calls with consistent parameter binding.
- Legacy staged loop slated for removal after ReAct stabilization; keep Markov state (Q, R_t, O_t) and compression discipline in new executor.
- `src/adaptive_planner.py`: Manifest builder and tiered stage planner with concurrency caps.
- `src/delegation_policy.py`: Delegation budgets, compression, and metrics for delegate tool.
- `src/delegation_clients.py`: OpenRouter client helper (uses `OPENROUTER_API_KEY`).
- `src/verifier_gate.py`: Evidence quality control enforcing citation requirements (constructor now uses sentinel to respect explicit `None` clients; fallback validation deterministic for tests).
- `src/code_search.py`: Optional local evidence tool; still provides def/use citations but no longer gatekeeps search. Expose via `tool_registry` so the model can request targeted local scans.
- `src/data_iterator.py`: Dataset refinement loop that pairs CAS-backed caching with VerifierGate checks; use for slow, high-quality DeepResearch dataset generation.
- `src/symbol_index.py`: AST-based symbol indexer for Python definitions/usages (def+use evidence).
- `src/file_read.py`: Snippet extractor with line context helpers.
- `src/scholar_adapter.py`: Scholar tool scaffold with provider fallbacks, retries, rate limiting.
- `src/sandbox_exec.py`: Sandboxed Python subprocess runner with timeout and stdout/stderr caps.
- `src/cas_store.py`: Content-addressable store (CAS) for blobs + provenance metadata.
- `src/drift_monitor.py`: Cosine drift and adaptive pruning recommendations.
- `src/load_test.py`: Synthetic load harness for throughput/latency checks.
- `schemas/`: JSON Schemas for `evidence`, `paper_meta`, `artifact_blob`, `drift_tick`, `load_report`.

## Core Principles
- Minimal context: prompts reconstruct state from Q (question), R_t (compressed report), O_t (last observation).
- Evidence first: every claim maps to at least two independent sources before synthesis.
- Deterministic scaffolds: seeds fixed; retries and backoff encoded; outputs machine‑checkable.
- Token discipline: keep R_t within 6–8K tokens; compress at every loop with extract‑then‑abstract.
- Don’t over‑refactor; make surgical changes aligned to the architecture.

## Execution Modes
- ReAct Mode (sequential): for focused, path‑dependent tasks (codebase traversal, single site deep‑read). Keep tool calls ≤ 32 unless needed.
- Heavy Mode (parallel): for broad web/lit surveys. Fan out search/visit; verify; compress.

## Contracts & Interfaces
- PaperMeta (see `schemas/paper_meta.schema.json`)
- Evidence (see `schemas/evidence.schema.json`)
- ArtifactBlob (see `schemas/artifact_blob.schema.json`)
- DriftTick (see `schemas/drift_tick.schema.json`)
- LoadReport (see `schemas/load_report.schema.json`)

## Tooling Heuristics
- CodeSearch (`src/code_search.py`): tokenized term match; respects file-size cap; pass stage paths to limit scope.
- FileRead (`src/file_read.py`): use for line-context evidence; default ±3 lines; trim before writing to R_t.
- Scholar: primary Semantic Scholar/Crossref; fallbacks arXiv/OpenAlex; unify to PaperMeta.
- Python (sandbox): wall-clock ≤ 60s; stdout/stderr ≤ 64KB; no network; seeded RNG.
- File Parser: prefer layout-aware parsers; chunk tables separately; store blobs in CAS.

## Fault Tolerance
- Retries: ≤ 3 attempts; exponential backoff with jitter; classify errors (4xx≠429 → permanent; 429/5xx → transient).
- Rate limiting: token bucket per host; shared global budget; reduce concurrency on sustained throttling.
- Circuit breakers: by host; open after repeated transient failures; half‑open probes.

## Caching & Dedup
- Key: `sha256(body)+parser_ver` (CAS). URL canonicalization: normalize scheme, strip tracking params, resolve redirects.
- Cache TTLs vary by domain class (news < docs < standards). For benchmarks, freeze caches.

## Context & Drift Control
- State S_t = {Q, R_t, O_t}. Never replay full histories into prompts.
- Update: O_t = summarized observation with citations; R_t = compress(R_{t-1} ⊕ O_t) under token cap.
- DriftMonitor (`src/drift_monitor.py`): compute cosine; if low, increase compression, raise verify‑k, reduce concurrency.

## Concurrency & Budgets
- Per call timeout: 60s. Max tool calls per task: 128.
- Heavy Mode: limit per-phase budget (search 40%, visit 40%, verify 10%, reserve 10%).
- Planner stages (`src/adaptive_planner.py`): manifest → tier1 (`src/`, `schemas/`, `docs/`) → tier2 (rest). Honor `max_concurrency` and autoshed if latency spikes.
- Thread pool: 16–32 typical; per-host concurrency ≤ 4.
- Delegate budgets: configure via `DelegationPolicy.agent_budgets`; default tongyi=3×1200 tokens, small=2×400.

## Verification & Synthesis
- Use VerifierGate (`src/verifier_gate.py`) to enforce evidence quality before claims enter R_t
- Verification rules: (1) ≥2 citations OR def+use pair, (2) independent sources, (3) LLM validation
- Claim extraction: Regex-based extraction of `file.py:123` sources from observations
- Verified claims: Only claims passing all three verification rules enter compressed report; citations appended in brackets
- Unverified claims: Filtered out or kept without source citations (non-factual statements)
- Tongyi DeepResearch: Built-in reasoning used for validation via OpenRouter client; fallback to basic heuristics when unavailable
- Independent sources: Different local files count as independent; domains tracked for web sources
- Synthesis must include only verified claims with citation identifiers.
- Evidence sources: SymbolIndex provides def+use evidence; CodeSearch provides text matches.

## Logging & Observability
- Minimal structured fields: `trace_id, tool, latency_ms, retries, bytes, status`.
- Delegation metrics: `DelegationPolicy.metrics` exposes `calls.*` and `deny.*`; harvest when debugging budgets.
- Persist artifacts to CAS; link evidence via content keys.
- For TUI usage, see Codex `RUST_LOG` behavior; otherwise log inline.

## Performance Targets (acceptance checks)
- Throughput ≥ 5 concurrent queries/agent; verify via `src/load_test.py`.
- Memory degradation < 2% over 100+ turns (track drift and token counts of R_t).
- Cross‑source consistency ≥ 90% on factual retrieval (Verifier scoring).

## Local Commands (smoke tests)
- `python src/sandbox_exec.py` → JSON summary of execution.
- `python src/cas_store.py` → prints CAS key + metadata.
- `python src/drift_monitor.py` → prints `DriftTick(...)`.
- `python src/load_test.py` → prints `LoadReport(...)`.
- `python src/scholar_adapter.py` → prints `[]` (stubs; wire providers to enable).

## Style & Patches
- Language: Python for tools; keep functions small; avoid one‑letter vars.
- Error handling: catch, classify, retry or fail fast; never swallow exceptions silently.
- Patches: avoid unrelated changes; preserve public interfaces; update schemas when formats evolve.

## Adding a New Tool (template)
1) Define input/output schema in `schemas/`.
2) Implement tool in `src/` with:
   - `execute_with_retry` pattern (retries, timeout, jitter)
   - rate limiter bucket and host circuit breaker
   - CAS writes for large artifacts
3) Add smoke test under module `__main__` printing concise JSON.

- Orchestrator entrypoint: `src/orchestrator_local.py` (calls planner stages + delegation policy within Markov loop).
- Register delegate handlers when instantiating `LocalOrchestrator`; default handlers include local search summarizer and OpenRouter Tongyi call if `OPENROUTER_API_KEY` is set.
- Set `OPENROUTER_API_KEY` (and optional base URL) in env to enable Tongyi delegate; otherwise handler returns `tongyi_unavailable`.
- OpenRouter client config: set model `alibaba/tongyi-deepresearch-30b-a3b` with parameters: temperature=0.85, top_p=0.95, repetition_penalty=1.1, max_tokens=8192, context_length=131072.
- Keep prompts compact; use builder functions that accept `Q, R_t, O_t` only.
- Heavy Mode planner must fold results layer-by-layer into R_t; verify before synthesis.

## Pitfalls & Remedies
- Rate limits: lower concurrency; expand cache use; rotate providers.
- Parser brittleness: fallback to reader-mode/plain-text; log domain for rule updates.
- False consensus: collapse near-duplicates by domain+hash; require independent domains.
- Drift spikes: increase compression and verification k; pause frontier expansion.
- Large PDFs: pre-detect size; chunk and parse selectively; cap time per file.
- Delegation budgets exceeded: `DelegationPolicy.allow` returns False; compress delegate responses before merging into `R_t`.

## Security & Privacy
- No secrets in logs; redact headers; never print tokens.
- Sandboxed exec is best‑effort; for production isolation, use containers or OS‑level constraints.

## Definition of Done (per change)
- Interfaces stable; schemas updated if needed.
- Smoke tests pass; no secret leakage; logs are minimal.
- Performance acceptance checks considered (throughput/latency, drift bounds).
