# PLAN.md — Roadmap & Milestones

Scope: Repository‑wide delivery plan. Keep this document short and current. Update when interfaces, dependencies, or milestones change.

## Objectives (Q4–Q1)
- Ship dual-mode (ReAct + Heavy) agentic loop using Tongyi DeepResearch via OpenRouter.
- Maintain bounded context with Markovian state (Q, R_t, O_t) and rigorous verification.
- Hit performance targets: ≥5 concurrent queries/agent, low drift (<2%), ≥90% cross-source consistency.
- Harden risk controls for scanning, verification, concurrency, and delegation before adding new capabilities.

## Current State
- Implemented scaffolds: Scholar adapter (stubs), Sandbox exec, CAS store, Drift monitor, Load harness.
- JSON Schemas in `schemas/` for key artifacts.
- AGENTS.md updated with verification workflow and SymbolIndex (2025-10-30).
- Risk triage completed (2025-10-31); prioritizing high-effort controls H1–H2 next.
- Local orchestrator wired to adaptive planner, delegation policy, CodeSearch/FileRead tools, and OpenRouter client (optional via `OPENROUTER_API_KEY`).
- VerifierGate constructor hardened with sentinel-based client handling; fallback validation now deterministic for tests (2025-10-31).
- CodeSearch now skips VCS/binary blobs when collecting evidence, preventing noisy citations (2025-10-31).
- Local orchestrator falls back to repo-wide search when stage hits are empty so verification can still cite evidence (2025-10-31).
- Evaluation harness added: JSONL fixtures and pytest checks for citation enforcement.

## Workstreams
1) Scholar Integration (H1)
   - Integrate providers (Semantic Scholar, Crossref, arXiv) with API keys and TOS.
   - Add reranker (bge‑small) and NLI verifier (deberta‑v3‑mnli small) gates.
   - Tests: metadata normalization, rate‑limit handling, fallback correctness.

2) Sandbox Enforcement (H2)
   - Optional: containerized isolation (Docker/cgroups); resource caps, no‑net.
   - Determinism: fixed seeds, stdout/stderr caps, audit logs.

3) Artifact Store (H3)
   - Wire CAS in fetchers/parsers; canonical URL normalization.
   - TTL policies per domain class; offline benchmark cache freeze.

4) Drift & Compression (H4)
   - Hook DriftMonitor into orchestrator; adaptive compression + verify‑k.
   - Metrics export for drift and R_t token size.

5) Load & Evaluation (H5)
   - Expand load harness with real tools; P50/P95 dashboards.
   - Evaluation runner for JSONL I/O; reproducible seeds and caches.

Risk Control Initiatives (active)
- H1 Delegation policy engine (in-flight): govern multi-model routing and budgets.
- H2 Adaptive planner stages (in-flight): stage manifests → tiered scans → throttled breadth.
- M-series controls queued after H1/H2: manifest + tiered scan, verifier gates, concurrency semaphores, contention telemetry.

## Milestones (Dates TBD)
- M1: Provider integration + smoke tests pass.
- M2: Orchestrator end‑to‑end (ReAct + Heavy) with drift gating.
- M3: Evaluation suite green on baseline tasks.
- M4: Load test meets throughput/latency targets.

## Risks & Mitigations
- Rate limits → per-host buckets, backoff, cache; fallback providers.
- Parser brittleness → reader-mode fallback, domain rules.
- Drift under saturation → adaptive compression, raise verify-k, reduce concurrency.
- False consensus → independent-domain requirement; hash-based dedup.
- Latency blowup from over-scan → manifest + tiered scanning, observation token caps.
- Weak claims entering report → verifier gate (def+use or two cites + NLI entailment).
- File I/O contention → per-path concurrency semaphore and autoshedding.
- Delegation prompt bloat → strict budget, compress responses before merging.

## Quick Commands
- Smokes: `python src/sandbox_exec.py` | `python src/cas_store.py` | `python src/drift_monitor.py` | `python src/load_test.py`
- Scholar stub: `python src/scholar_adapter.py`

## Next Agent Prompt
Context:
- Local orchestrator (src/orchestrator_local.py) now uses adaptive planner, CodeSearch, FileRead, and delegation policy.
- Delegation handlers include local "small" search summarizer and optional OpenRouter Tongyi client (requires OPENROUTER_API_KEY).
- Risk controls prioritize strict evidence verification before synthesis and controlled concurrency. VerifierGate is live; CodeSearch provides symbol-level evidence.

Your Objectives:
1. Wire CAS caching for AST index results (M2 continuation):
   - Cache per-file symbol summaries using `src/cas_store.py` with a parser version key.
   - Load from cache to reduce parse overhead under load.
2. Parameterize VerifierGate model usage (M3 refinement):
   - Default to Tongyi model from config; fallback to basic heuristics if unavailable.
   - Keep tests deterministic via `VerifierGate(tongyi_client=None)`.
3. Snippet and token discipline (M4 hygiene):
   - Ensure snippet length caps are enforced; add tests around compression and citation formatting.
4. Evaluation harness utilities:
   - Add CLI runner for JSONL fixtures; emit summary of verified/total claims.

Constraints:
- Maintain Markovian state (Q, R_t, O_t) and token limits.
- Preserve delegation budgets; avoid expanding prompts unnecessarily.
- Keep all documentation (AGENTS.md / PLAN.md) synchronized with changes.

Deliverables:
- CAS-backed AST caching.
- Verifier model parameterization (Tongyi-first; fallback-basic).
- Evaluation assets + passing tests (done); add CLI runner.
- Documentation updates reflecting new behaviors (done; continue to maintain).
