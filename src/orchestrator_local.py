"""Local-first orchestrator integrating adaptive planner and delegation policy.

This module demonstrates how the Markovian loop consumes staged plans and
delegation budgets without needing external network calls. It keeps the logic
minimal so future tools (CodeSearch, FileRead, etc.) can plug in without
rewriting the control flow.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from adaptive_planner import PlanStage, build_manifest, plan_stages
from delegation_policy import AgentBudget, DelegationPolicy
from delegation_clients import load_openrouter_client, AgentClientError
from config import DEFAULT_TONGYI_CONFIG, DEFAULT_MODEL_ROUTER
from code_search import CodeSearch, SearchHit
from file_read import read_snippet
from verifier_gate import VerifierGate, Claim
from sandbox_exec import run_snippet, ExecResult
from scholar_adapter import ScholarAdapter, PaperMeta
from csv_utils import sniff_csv, suggest_cleaning_steps, clean_csv, CSVInfo
from md_utils import parse_markdown, suggest_md_cleaning, clean_markdown, MDInfo


@dataclass
class LoopState:
    question: str
    report: str = ""
    last_observation: str = ""


class DelegateTool:
    """Thin wrapper over DelegationPolicy; handlers supplied per agent."""

    def __init__(self, policy: DelegationPolicy, handlers: Dict[str, Callable[[str], str]]):
        self.policy = policy
        self.handlers = handlers

    def run(self, agent_id: str, prompt: str) -> Optional[str]:
        if not self.policy.allow(agent_id):
            return None
        handler = self.handlers.get(agent_id)
        if not handler:
            return None
        raw_response = handler(prompt)
        compressed = self.policy.record(agent_id, raw_response)
        return compressed


class LocalOrchestrator:
    def __init__(
        self,
        root: str = ".",
        agent_budgets: Optional[Dict[str, AgentBudget]] = None,
        delegate_handlers: Optional[Dict[str, Callable[[str], str]]] = None,
    ):
        self.root = os.path.abspath(root)
        self.manifest = build_manifest(root)
        self.stages: List[PlanStage] = plan_stages(self.manifest)
        self.policy = DelegationPolicy(
            agent_budgets=agent_budgets
            or {
                "tongyi": AgentBudget(max_calls=3, max_tokens=1200),
                "small": AgentBudget(max_calls=2, max_tokens=400),
                "sandbox": AgentBudget(max_calls=2, max_tokens=600),
                "scholar": AgentBudget(max_calls=2, max_tokens=500),
                "csv_cleaner": AgentBudget(max_calls=2, max_tokens=800),
                "md_cleaner": AgentBudget(max_calls=2, max_tokens=700),
            }
        )
        self.code_search = CodeSearch(root=self.root)
        self.verifier_gate = VerifierGate()
        self.scholar = ScholarAdapter()
        handlers = delegate_handlers or self._build_default_delegate_handlers()
        self.delegate_tool = DelegateTool(self.policy, handlers)

    def run(self, question: str) -> str:
        state = LoopState(question=question)
        for stage in self.stages:
            self._process_stage(stage, state)
            if self._is_answer_sufficient(state):
                break
        return self._synthesize(state)

    def _process_stage(self, stage: PlanStage, state: LoopState) -> None:
        if stage.name == "manifest":
            state.last_observation = f"Manifest scanned: {len(self.manifest)} files"
        else:
            hits = self._collect_hits(stage, state.question)
            if not hits:
                # Fallback to repository-wide search so verification can still attach citations
                hits = self.code_search.search(state.question, max_results=4)
            if hits:
                observation_lines = []
                for hit in hits:
                    rel = os.path.relpath(hit.path, self.root)
                    snippet = read_snippet(hit.path, start=hit.line, end=hit.line).text.replace("\n", " ").strip()
                    if len(snippet) > 160:
                        snippet = snippet[:157] + "…"
                    observation_lines.append(f"{rel}:{hit.line} {snippet}")
                raw_observation = f"Stage {stage.name} hits: {' | '.join(observation_lines)}"
                # Verify claims before adding to report
                verified_observation = self._verify_and_add_claims(state, raw_observation)
                state.last_observation = verified_observation
            else:
                state.last_observation = f"Stage {stage.name} no matches for query"
        state.report = self._compress(state.report, state.last_observation)

        # Example delegation usage near stage boundary
        if stage.name == "tier1":
            for agent_id in ("small", "tongyi"):
                response = self.delegate_tool.run(
                    agent_id,
                    self._build_delegate_prompt(state.question, stage.paths[:20], stage.name),
                )
                if response:
                    state.last_observation = f"Delegate {agent_id} -> {response}"
                    state.report = self._compress(state.report, state.last_observation)
        # Sandbox delegation example: simple calculations or data processing
        if stage.name == "tier2":
            # Simple heuristic: if question asks to compute/evaluate, use sandbox
            q_lower = state.question.lower()
            if any(word in q_lower for word in ["compute", "calculate", "evaluate", "run", "execute"]):
                demo_code = "result = sum(range(10))\nprint(f'sum(0..9)={result}')"
                prompt = f"code={demo_code}\nseed=42\ntimeout=10"
                response = self.delegate_tool.run("sandbox", prompt)
                if response:
                    state.last_observation = f"Delegate sandbox -> {response}"
                    state.report = self._compress(state.report, state.last_observation)
            # Scholar delegation: if question asks for papers/literature
            if any(word in q_lower for word in ["paper", "literature", "survey", "review", "recent", "state-of-the-art"]):
                # Extract a simple query from the question
                query = state.question.strip("?")
                prompt = f"query={query}\nk=3"
                response = self.delegate_tool.run("scholar", prompt)
                if response:
                    state.last_observation = f"Delegate scholar -> {response}"
                    state.report = self._compress(state.report, state.last_observation)
            # CSV cleaning: only if explicitly requested
            if any(word in q_lower for word in ["clean csv", "process csv", "clean the csv", "clean the data"]):
                # Try to detect CSV file mentions in the question
                words = state.question.split()
                csv_candidates = [w for w in words if w.lower().endswith(".csv")]
                if csv_candidates:
                    csv_path = csv_candidates[0]
                    out_path = csv_path.replace(".csv", "_cleaned.csv")
                    prompt = f"csv_path={csv_path}\noutput_path={out_path}"
                    response = self.delegate_tool.run("csv_cleaner", prompt)
                    if response:
                        state.last_observation = f"Delegate csv_cleaner -> {response}"
                        state.report = self._compress(state.report, state.last_observation)
            # Markdown cleaning: only if explicitly requested
            if any(word in q_lower for word in ["clean markdown", "process markdown", "clean the markdown", "clean the dump"]):
                words = state.question.split()
                md_candidates = [w for w in words if w.lower().endswith(".md")]
                if md_candidates:
                    md_path = md_candidates[0]
                    out_path = md_path.replace(".md", "_cleaned.md")
                    prompt = f"md_path={md_path}\noutput_path={out_path}"
                    response = self.delegate_tool.run("md_cleaner", prompt)
                    if response:
                        state.last_observation = f"Delegate md_cleaner -> {response}"
                        state.report = self._compress(state.report, state.last_observation)

    def _compress(self, report: str, addition: str, cap_tokens: int = 800) -> str:
        text = (report + "\n" + addition).strip()
        tokens = text.split()
        if len(tokens) <= cap_tokens:
            return text
        truncated = " ".join(tokens[:cap_tokens]) + " …"
        return truncated

    def _verify_and_add_claims(self, state: LoopState, observation_text: str) -> str:
        """Verify the observation as a whole and append citations if valid.

        Avoid splitting on '.' which may break file paths like 'file.py:123'.
        """
        if not self.verifier_gate:
            return observation_text
        pattern = re.compile(r'([\w/\\\.-]+\.(py|md|json)):(\d+)')
        sources: list[str] = []
        for match in pattern.finditer(observation_text):
            file_path = match.group(1)
            line_no = match.group(3)
            src = f"{file_path}:{line_no}"
            if src not in sources:
                sources.append(src)

        if sources:
            claim = self.verifier_gate.verify_claim(observation_text, sources)
            if claim.verified:
                return f"{observation_text} [{', '.join(sources)}]"
        return observation_text

    def _is_answer_sufficient(self, state: LoopState) -> bool:
        return state.report.count("file") >= 5  # placeholder heuristic

    def _synthesize(self, state: LoopState) -> str:
        return f"Q: {state.question}\nReport:\n{state.report}\nLast Observation: {state.last_observation}"

    def _collect_hits(self, stage: PlanStage, question: str) -> List[SearchHit]:
        # Limit search to manageable subset of paths for speed.
        paths = stage.paths[:200]
        return self.code_search.search(question, paths=paths, max_results=4)

    def _build_delegate_prompt(self, question: str, paths: List[str], stage_name: str) -> str:
        rel_paths = [os.path.relpath(p, self.root) for p in paths]
        return f"question={question}\nstage={stage_name}\nfiles={','.join(rel_paths)}"

    def _delegate_small(self, prompt: str) -> str:
        parts = {k: v for k, _, v in (line.partition("=") for line in prompt.splitlines())}
        question = parts.get("question", "")
        files = [f for f in parts.get("files", "").split(",") if f]
        full_paths = [os.path.join(self.root, f) for f in files]
        hits = self.code_search.search(question, paths=full_paths or None, max_results=3)
        if not hits:
            return "no hits"
        summaries = []
        for hit in hits:
            rel = os.path.relpath(hit.path, self.root)
            summaries.append(f"{rel}:{hit.line}")
        return "small agent evidence " + ", ".join(summaries)

    def _delegate_sandbox(self, prompt: str) -> str:
        """Parse and execute code in the sandbox."""
        # Expected prompt format (simple key=value):
        # code=<python code>
        # input_json=<json dict> (optional)
        # timeout=<int seconds> (optional)
        # seed=<int> (optional)
        parts = {k: v for k, _, v in (line.partition("=") for line in prompt.splitlines())}
        code = parts.get("code", "").strip()
        if not code:
            return "sandbox_error: no code provided"
        try:
            input_json = json.loads(parts.get("input_json", "{}"))
        except json.JSONDecodeError:
            input_json = {}
        timeout = int(parts.get("timeout", 30))
        seed = int(parts.get("seed", 1337))
        result: ExecResult = run_snippet(code, input_json=input_json, timeout_s=timeout, seed=seed, base_dir=self.root)
        summary = {
            "ok": result.ok,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "ms": result.duration_ms,
            "isolated": result.isolated,
            "container": result.container_id,
        }
        return json.dumps(summary, ensure_ascii=False, separators=(",", ":"))

    def _delegate_scholar(self, prompt: str) -> str:
        """Parse and retrieve literature via ScholarAdapter."""
        # Expected prompt format (simple key=value):
        # query=<search query>
        # k=<int max results> (optional, default 5)
        parts = {k: v for k, _, v in (line.partition("=") for line in prompt.splitlines())}
        query = parts.get("query", "").strip()
        if not query:
            return "scholar_error: no query provided"
        k = int(parts.get("k", 5))
        try:
            papers: List[PaperMeta] = self.scholar.search(query, k=k)
            if not papers:
                return "scholar: no results"
            summaries = []
            for p in papers:
                line = f"{p.title} ({p.year}) — {', '.join(p.authors[:3])}{' et al.' if len(p.authors) > 3 else ''}"
                if p.venue:
                    line += f" {p.venue}"
                if p.doi:
                    line += f" doi:{p.doi}"
                summaries.append(line)
            return "scholar: " + " | ".join(summaries)
        except Exception as exc:
            return f"scholar_error: {exc}"

    def _delegate_csv_cleaner(self, prompt: str) -> str:
        """Clean a CSV using sandboxed csv_utils."""
        # Expected prompt format:
        # csv_path=<relative path to CSV>
        # output_path=<relative path for cleaned CSV>
        parts = {k: v for k, _, v in (line.partition("=") for line in prompt.splitlines())}
        csv_rel = parts.get("csv_path", "").strip()
        out_rel = parts.get("output_path", "").strip()
        if not csv_rel or not out_rel:
            return "csv_error: csv_path and output_path required"
        csv_path = os.path.join(self.root, csv_rel)
        output_path = os.path.join(self.root, out_rel)
        if not os.path.exists(csv_path):
            return f"csv_error: file not found {csv_rel}"
        # Step 1: sniff schema in sandbox
        sniff_code = f"""
import sys; sys.path.insert(0, '/workspace')
from csv_utils import sniff_csv, suggest_cleaning_steps, clean_csv
info = sniff_csv('{csv_path}')
steps = suggest_cleaning_steps(info)
result = clean_csv(info, steps, '{output_path}')
print({{'info': info.__dict__, 'steps': steps, 'result': result}})
"""
        try:
            res = run_snippet(sniff_code, base_dir=self.root, timeout_s=30)
            if res.ok:
                # Parse stdout for JSON result
                out = res.stdout.strip()
                # Find the dict line
                for line in out.splitlines():
                    if line.startswith("{") and line.endswith("}"):
                        data = json.loads(line)
                        return f"csv_cleaned: rows={data['result']['cleaned_rows']} output={out_rel} steps={len(data['steps'])}"
                return "csv_error: could not parse result"
            else:
                return f"csv_error: {res.stderr}"
        except Exception as exc:
            return f"csv_error: {exc}"

    def _delegate_md_cleaner(self, prompt: str) -> str:
        """Clean a markdown dump using sandboxed md_utils."""
        # Expected prompt format:
        # md_path=<relative path to MD>
        # output_path=<relative path for cleaned MD>
        parts = {k: v for k, _, v in (line.partition("=") for line in prompt.splitlines())}
        md_rel = parts.get("md_path", "").strip()
        out_rel = parts.get("output_path", "").strip()
        if not md_rel or not out_rel:
            return "md_error: md_path and output_path required"
        md_path = os.path.join(self.root, md_rel)
        output_path = os.path.join(self.root, out_rel)
        if not os.path.exists(md_path):
            return f"md_error: file not found {md_rel}"
        # Run md_utils in sandbox
        clean_code = f"""
import sys; sys.path.insert(0, '/workspace')
from md_utils import parse_markdown, suggest_md_cleaning, clean_markdown
info = parse_markdown('{md_path}')
steps = suggest_md_cleaning(info)
result = clean_markdown(info, steps, '{output_path}')
print({{'info': info.__dict__, 'steps': steps, 'result': result}})
"""
        try:
            res = run_snippet(clean_code, base_dir=self.root, timeout_s=30)
            if res.ok:
                out = res.stdout.strip()
                for line in out.splitlines():
                    if line.startswith("{") and line.endswith("}"):
                        data = json.loads(line)
                        return f"md_cleaned: sections={data['result']['cleaned_sections']} output={out_rel} steps={len(data['steps'])}"
                return "md_error: could not parse result"
            else:
                return f"md_error: {res.stderr}"
        except Exception as exc:
            return f"md_error: {exc}"

    def _build_default_delegate_handlers(self) -> Dict[str, Callable[[str], str]]:
        handlers: Dict[str, Callable[[str], str]] = {"small": self._delegate_small, "sandbox": self._delegate_sandbox, "scholar": self._delegate_scholar, "csv_cleaner": self._delegate_csv_cleaner, "md_cleaner": self._delegate_md_cleaner}
        client = load_openrouter_client(
            api_key=DEFAULT_TONGYI_CONFIG.api_key,
            base_url=DEFAULT_TONGYI_CONFIG.base_url,
        )
        if client:
            router = DEFAULT_MODEL_ROUTER
            def _call_tongyi(prompt: str) -> str:
                try:
                    return client.chat(
                        prompt,
                        model=router.next_model(),
                        temperature=DEFAULT_TONGYI_CONFIG.temperature,
                        top_p=DEFAULT_TONGYI_CONFIG.top_p,
                        repetition_penalty=DEFAULT_TONGYI_CONFIG.repetition_penalty,
                        max_tokens=min(2048, DEFAULT_TONGYI_CONFIG.max_tokens),
                        system_prompt="You are a concise research assistant. Summarize evidence with citations if available.",
                    )
                except AgentClientError as exc:
                    return (
                        f"tongyi_error: {exc}. "
                        "Run 'python -m config_validator --check-openrouter' to troubleshoot OpenRouter connectivity."
                    )

            handlers["tongyi"] = _call_tongyi
        else:
            handlers["tongyi"] = (
                lambda prompt: "tongyi_unavailable: configure OPENROUTER_API_KEY and run the config validator to enable remote reasoning."
            )
        return handlers


def cli_main():
    """Entry point for tongyi-agent CLI."""
    import argparse
    parser = argparse.ArgumentParser(description="Run Tongyi Agent research assistant")
    parser.add_argument("question", nargs="*", help="Question to process")
    parser.add_argument("--root", default=".", help="Root directory to analyze")
    args = parser.parse_args()
    question = " ".join(args.question) if args.question else input("Question: ")
    orch = LocalOrchestrator(root=args.root)
    print(orch.run(question))


if __name__ == "__main__":
    cli_main()
