# Tongyi DeepResearch Skill Specification

## Skill Metadata

```yaml
name: tongyi-deepresearch
description: Use when performing deep research on complex technical topics requiring multi-step reasoning, evidence synthesis, and verification across multiple sources - applies Tongyi DeepResearch paper patterns for structured information-seeking with progressive context management and rigorous source quality control
version: 1.0.0
tdd_status: complete (red-green-refactor all phases)
paper_reference: https://arxiv.org/html/2510.24701v1
location: ~/.claude/skills/tongyi-deepresearch/
```

---

## Skill Purpose

Enable Claude instances to conduct **evidence-based deep research** on complex technical topics using a structured 7-phase methodology derived from the Tongyi DeepResearch paper, with mandatory verification, contradiction resolution, and progressive compression to prevent context overflow.

---

## What the Skill Delivers

### Against Baseline Failures

| Baseline Failure | Skill Solution | Mechanism |
|---|---|---|
| No equations for math topics | Phase 3B: Full-text extraction protocol | "For math topics, extract ALL equations or mark incomplete" |
| Contradictions ignored | Phase 5: Contradiction resolution (mandatory) | Track contradictions explicitly; assess evidence; resolve or mark INSUFFICIENT |
| Source mixing (T1/T4 equal) | Source hierarchy with enforcement | T1/T2 for evidence; T3/T4 context only |
| Linear context growth | Phase 4A: Compression checkpoints | After 3-5 sources, merge findings; discard redundancy |
| Reactive searches | Phase 2A: Strategic search → citation graphs | Surveys → landmarks → citation graph → targeted follow-up |
| Paywalls accepted | Phase 3A: Paywall strategy (5 methods) | Fallback chain: arXiv → faculty pages → PDFs → ResearchGate → semanticscholar |
| Breadth over depth | Phase 1A: Prioritize subgoals | "If time <50%, go DEEP on critical subgoals, not BROAD on secondary" |
| Unverified claims | Phase 3 & Phase 7: Verification checklist | All claims require T1/T2 sources or marked UNVERIFIED |
| No confidence levels | Phase 5B: Confidence calibration | Every claim rated HIGH/MED/LOW/UNVERIFIED with justification |
| No research log | Phase 4B: Research log maintenance | Comprehensive metadata for every source (tier, confidence, claims) |

---

## Core Principles

1. **Evidence First:** Every claim must be traceable to primary sources (T1/T2)
2. **Contradiction Resolution:** Contradictions trigger investigation, not listing both sides
3. **Progressive Compression:** Context managed via checkpoints, not linear accumulation
4. **Verification Mandatory:** No fallbacks to heuristics when budget tight
5. **Pressure-Resistant Rules:** Phases 1-3, verification, quality threshold cannot be bypassed
6. **Transparency:** Either COMPLETE (verified) or INCOMPLETE (specific gaps, not vague)

---

## The 7 Phases

### Phase 1: Strategic Planning
**Duration:** 2 minutes
**Output:** Search strategy with success criteria

**Protocol:**
- Parse question into 3-5 subgoals with success criteria
- Assign priority (CRITICAL, HIGH, MEDIUM, LOW)
- Build source quality hierarchy (T1 preferred, T3 acceptable, T4 forbidden)
- Estimate action budget and allocate per phase
- Identify known unknowns

**Mandatory:** Even under 5-minute deadline

### Phase 2: Systematic Search Strategy
**Duration:** 3-5 actions
**Output:** Evidence map with citation graph

**Protocol:**
1. Search for surveys/review papers first
2. Identify landmark papers from survey references
3. Build citation graph (forward + backward citations)
4. Use citation graph to target follow-up searches
5. Evolve searches based on findings (not blind repeat)

**Stages:**
- Round 1 (Actions 1-3): Broad (surveys, landmarks)
- Round 2 (Actions 4-8): Targeted (reconcile contradictions)
- Round 3 (Actions 9+): Narrow (fill gaps)

### Phase 3: Source Retrieval & Full-Text Access
**Duration:** 5-8 actions
**Output:** Full-text papers with extracted equations/data

**Paywall Strategy (Mandatory):**
1. Try arXiv preprint version
2. Search "[Author] [Institution]" for faculty pages
3. Search "[Paper title] filetype:pdf"
4. Check ResearchGate author profiles
5. Try semanticscholar.org (free PDFs often linked)

**Extraction Protocol:**
- Abstract: Identify main contribution
- Equations section: Capture ALL equations (if math topic)
- Results: Quantitative claims with confidence intervals
- Appendices: Proofs, detailed tables
- Research log entry: One-line summary with tier classification

**Failure Condition:** If abstract-only and cannot access full text after 5 methods, mark "PAYWALL - source inaccessible" and reduce confidence to LOW

### Phase 4: Progressive Compression & State Management
**Duration:** Continuous (after every 3-5 sources)
**Output:** Compressed report (≤6-8K tokens) + research log

**Compression Checkpoints:**
After every 3-5 sources, create compression checkpoint:
1. Merge new findings into report
2. Remove redundant details
3. Keep: equations, contradictions, landmark papers, key data
4. Discard: duplicate findings, dead-end searches

**Research Log Format:**
```
{
  paper: "Title",
  authors: ["Author1", "Author2"],
  year: 2024,
  venue: "ICML/NeurIPS/arXiv",
  tier: "T1/T2/T3",
  url: "DOI or link",
  key_claims: ["Claim1", "Claim2"],
  equations: true,
  confidence: "HIGH/MED/LOW",
  notes: "Usage notes"
}
```

### Phase 5: Contradiction Detection & Resolution
**Duration:** 2-3 actions (when contradictions found)
**Output:** Resolved contradictions or marked INSUFFICIENT

**When Contradiction Detected:**
```
CONTRADICTION:
Claim A: [statement] (Papers: X, Y, Equation: E1)
vs
Claim B: [statement] (Papers: Z, W, Equation: E2)

Hypothesis:
- Different assumptions? → Investigate
- Different domains? → Investigate
- Different counting methods? → Investigate
- One might be wrong? → Assess evidence

Resolution Status:
RESOLVED: Evidence favors Claim A due to [reasons]
or
CONDITIONAL: Claim A if [condition], Claim B if [other condition]
or
INSUFFICIENT: Cannot resolve due to [specific gap]
```

**Confidence Calibration:**
| Level | When to Assign | Example |
|---|---|---|
| HIGH | T1 peer-reviewed, multiple confirmations, clear equations | "Chinchilla: D_opt = 20*N_opt" [Hoffmann ICML 2022, replicated] |
| MEDIUM | T1 newer/less cited, or T2 + multiple sources, or consensus from T3 | "Inference scales 5-10x training" [recent preprints, emerging consensus] |
| LOW | Single source, contradicted, or T1 unavailable | "Data exhaustion by 2026" [some predict, others say 2032] |
| UNVERIFIED | Stated but source not checked, or T3/T4 only | "o1 achieved 92% on AIME" [from news, need original paper] |

**Cannot use:** "Both are valid" or "Too uncertain to say" without systematic investigation

### Phase 6: Iterative Refinement
**Duration:** Variable (until quality ≥0.7)
**Output:** High-quality synthesis meeting threshold

**Protocol:**
- Use DataIterator or equivalent refinement loop
- Quality threshold: 0.7 minimum (NOT configurable lower)
- Max iterations: 5 (NOT configurable below 3)
- Verification required on all iterations
- Stop when: Quality ≥0.7 achieved

**If Budget Exhausted:** Return INCOMPLETE with specific gaps, not "ran out of budget"

### Phase 7: Pre-Completion Verification
**Duration:** 5 minutes (before any answer)
**Output:** COMPLETE (checklist passes) or INCOMPLETE (gaps documented)

**Mandatory Checklist:**
```
☐ Main question directly answered (not just related info)
☐ ALL factual claims have ≥2 independent sources (T1/T2) OR marked UNVERIFIED
☐ ALL contradictions resolved (RESOLVED/CONDITIONAL) OR marked INSUFFICIENT with reason
☐ Source quality meets hierarchy (≥50% T1 for research claims)
☐ Quality score ≥0.7 on final synthesis
☐ No placeholder TODOs or "needs more research" without specifics
☐ Research log complete with sources, tiers, confidence levels
```

**If Any Item Fails:**
- Return INCOMPLETE status
- Document failed items specifically
- List critical gaps preventing completion
- Specify resources needed (e.g., "+2 search_papers for verification")

---

## Pressure-Resistant Rules (MANDATORY)

These rules CANNOT be bypassed under ANY pressure:

### Rule 1: Phases 1-3 Never Optional
- ❌ Skip Phase 1 due to time pressure
- ✅ Execute Phase 1 first. If time exhausted, return INCOMPLETE

### Rule 2: Verification Has No Fallback
- ❌ Use basic verifier when LLM verification unavailable
- ✅ Use full verification or mark claim UNVERIFIED

### Rule 3: Source Hierarchy Enforced
- ❌ Cite T3/T4 sources as evidence for research findings
- ✅ Require T1/T2 or mark CONFIDENCE: LOW with justification

### Rule 4: Contradictions Require Resolution
- ❌ "Experts disagree, both views are valid"
- ✅ Assess evidence quality per side; provide reasoned conclusion

### Rule 5: Quality Threshold Minimum 0.7
- ❌ Lower threshold to 0.5 to finish faster
- ✅ Accept INCOMPLETE status instead

### Rule 6: Completion Checklist Must Pass
- ❌ Return "Here's what I found + some gaps"
- ✅ Return COMPLETE (checklist passes) or INCOMPLETE (specific gaps)

---

## Forbidden Rationalizations (Zero Tolerance)

| Rationalization | Why Forbidden | Correct Action |
|---|---|---|
| **"Time pressure, skip Phase 1"** | Planning takes 2 min, saves 30 min | Execute Phase 1 first |
| **"Budget tight, use fallback verifier"** | Fallback misses quality issues | Use full verifier or mark UNVERIFIED |
| **"News articles agree, verified"** | News can misrepresent research | Access primary source or mark LOW confidence |
| **"Experts disagree, both valid"** | Lazy analysis; evidence varies | Assess evidence quality systematically |
| **"Lower threshold to finish faster"** | 0.5 quality = unverified claims | Accept INCOMPLETE instead |
| **"Documented gaps, partial answer OK"** | Gaps still unresolved | Mark INCOMPLETE with resource requirements |
| **"Topic is inherently uncertain"** | Not excuse to skip analysis | Do meta-analysis with distribution + methodology |
| **"Sources cite each other, independent"** | Citation laundering | Trace back to original source |
| **"Minor claim, skip verification"** | All claims need verification | Mark UNVERIFIED if cost too high |
| **"User will decide, present both sides"** | Abdicating responsibility | Assess evidence; provide reasoned conclusion |

---

## Completion Status Formats

### ✅ COMPLETE
```
RESEARCH COMPLETE: [Question]

ANSWER: [Direct 1-2 sentence answer]

KEY FINDINGS:
1. [Finding with confidence level and source]
2. [Finding with confidence level and source]

RESEARCH LOG:
| Source | Tier | Confidence | Key Claim |
|--------|------|------------|-----------|

UNRESOLVED CONTRADICTIONS: None

QUALITY SCORE: [0.7-1.0] (threshold: 0.7)
```

### ⚠️ INCOMPLETE
```
RESEARCH INCOMPLETE: [Question]

STATUS: Halted at Phase [#] due to [reason]

WHAT WE KNOW (verified, ≥0.7 confidence):
- [Claim 1] [Source]
- [Claim 2] [Source]

CRITICAL GAPS:
1. [Specific gap] - Would need [resource]
2. [Specific gap] - Would need [resource]

TO COMPLETE:
- [Action 1]: [estimated cost]
- [Action 2]: [estimated cost]

QUALITY SCORE: [<0.7] (threshold: 0.7, not met)
```

---

## Integration Points

### With Tongyi-Agent Components
- **ReActParser:** Parses research actions into tool calls
- **ToolRegistry:** Executes searches, file reads, code
- **VerifierGate:** Enforces source verification (Phase 3 & 7)
- **DataIterator:** Refinement loop (Phase 6)
- **DelegationPolicy:** Budget management (Phase 1 & 5)

### With Other Skills
- **REQUIRED:** superpowers:test-driven-development (foundation)
- **RECOMMENDED:** superpowers:systematic-debugging (for contradiction analysis)
- **OPTIONAL:** superpowers:dispatching-parallel-agents (for Heavy Mode)

---

## Success Criteria

Research using this skill is SUCCESSFUL when:
- ✅ Returns COMPLETE status (checklist passes)
- ✅ Contains equations/formulations (for math topics)
- ✅ Contradictions resolved or explicitly marked INSUFFICIENT
- ✅ All claims have T1/T2 sources or marked UNVERIFIED
- ✅ Confidence levels (HIGH/MED/LOW) assigned to every claim
- ✅ Research log provided with source metadata
- ✅ Quality score ≥0.7

Research is FAILED if:
- ❌ Returns partial answer without COMPLETE/INCOMPLETE status
- ❌ No equations for mathematical topics
- ❌ Contradictions listed without resolution
- ❌ Claims from T3/T4 sources without marking confidence
- ❌ No research log or source metadata
- ❌ Quality score <0.7 and not marked INCOMPLETE

---

## Example: Correct Usage

**Query:** "What are the latest scaling laws for LLMs, and when will data exhaust?"

### Phase 1: Planning (2 min)
```
Subgoals:
1. CRITICAL: 2024+ formulations with equations
2. HIGH: Reconcile Kaplan vs Hoffmann
3. MEDIUM: Data exhaustion timelines

Source hierarchy: T1 primary (ICML/NeurIPS), T2 acceptable (arXiv)
Budget: 15 actions, allocate 10-12 for research, 3 for verification
```

### Phase 2-3: Search & Retrieval (6-8 actions)
```
Action 1-2: Find survey papers
Action 3-4: Retrieve Kaplan (2020) and Hoffmann (2022) full papers
Action 5-6: Extract equations, build research log
Checkpoint 1: Merge findings, note equation discrepancy
```

### Phase 5: Resolve Contradiction (2 actions)
```
Found: Kaplan exponent 0.73, Hoffmann 0.50
Research: Found reconciliation paper
Result: RESOLVED - Different parameter counting, both correct

Confidence: HIGH (peer-reviewed reconciliation found)
```

### Phase 6: Refine (1-2 actions)
```
Quality: 0.75 (≥0.7 threshold met)
```

### Phase 7: Verify Before Answering
```
Checklist: All pass
Status: COMPLETE
Return: RESEARCH COMPLETE + findings + research log
```

---

## Testing & Validation

### Test Suites
1. **Baseline Comparison** (before/after skill)
   - Measure: equations, contradictions, source quality
   - Expected: 7x improvement

2. **Pressure Scenarios** (5 scenarios)
   - Time constraint, missing sources, conflicting opinions, uncertainty, budget
   - Expected: All phases followed despite pressure

3. **Loophole Resistance** (5 key vulnerabilities)
   - Test agents trying to rationalize shortcuts
   - Expected: Pressure-resistant rules hold

### Verification Command
```bash
# Test skill on research query
Query: "Research [complex topic with contradictory sources]"
Verify:
  [ ] Equations extracted (if applicable)
  [ ] Sources T1/T2/T3/T4 classified
  [ ] Contradictions resolved/marked INSUFFICIENT
  [ ] Confidence levels assigned
  [ ] Research log complete
  [ ] Status: COMPLETE or INCOMPLETE (not partial)
  [ ] Quality ≥0.7 (if COMPLETE)
```

---

## Maintenance & Evolution

### When Agents Violate the Skill
1. Document the rationalization used
2. Identify which pressure triggered violation
3. Add to forbidden rationalizations OR strengthen pressure-resistant rule
4. Re-test to verify fix
5. Update skill version

### When Paper's Recommendations Change
1. Update example implementations
2. Update references section
3. Verify existing phases still align
4. Do not change core phases without RE-testing

### When New Research Domains Emerge
1. Test skill on new domain
2. Document domain-specific challenges
3. Add new phase or sub-protocol if needed
4. Do not modify without testing

---

## Quick Reference

**7 Phases (Never Skip):**
1. Planning (2 min) → Subgoals, source hierarchy, budget
2. Search (3-5 actions) → Surveys, landmarks, citation graphs
3. Retrieval (5-8 actions) → Full text, equations, research log
4. Compression (Continuous) → Checkpoints every 3-5 sources
5. Contradiction (2-3 actions) → Resolution or INSUFFICIENT
6. Refinement (Variable) → Iterate until quality ≥0.7
7. Verification (5 min) → Checklist pass/fail → COMPLETE or INCOMPLETE

**Source Hierarchy:**
- T1: Peer-reviewed papers, official docs → Evidence
- T2: Preprints, tech reports → Evidence
- T3: Expert blogs, technical posts → Context only
- T4: News, social media, unverified → Forbidden

**Forbidden Rationalizations:** 10 (see table above)

**Pressure-Resistant Rules:** 6 (no exceptions)

**Completion Status:** COMPLETE or INCOMPLETE only (no partial answers)

---

## Paper Citation

**Tongyi DeepResearch: Towards Complex Reasoning for Real-World QA**
- URL: https://arxiv.org/html/2510.24701v1
- arXiv: https://arxiv.org/abs/2510.24701
- Paper sections: 3.1 (ReAct), 4 (data synthesis), 5 (GRPO), 6 (Heavy Mode)

---

## Status

✅ **Complete** - TDD Red-Green-Refactor cycle finished
- RED: 10 baseline failures documented
- GREEN: 7-phase skill implemented and tested
- REFACTOR: 5 pressure scenarios, loopholes identified and closed

🚀 **Ready for deployment** in Tongyi-Agent and research workflows

