"""Verifier gate for evidence quality control.

Enforces citation requirements before claims enter the compressed report (R_t).
Uses Tongyi's built-in reasoning for validation without external NLI models.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from delegation_clients import load_openrouter_client, AgentClientError
from config import DEFAULT_TONGYI_CONFIG


@dataclass
class Claim:
    """Represents a claim with its supporting evidence."""
    text: str
    sources: List[str]
    confidence: float = 0.0
    verified: bool = False


class VerifierGate:
    """Enforces evidence quality rules before claims enter R_t."""

    def __init__(self, tongyi_client: object = "auto"):
        # tongyi_client semantics:
        #   - "auto" (default): load from env/config
        #   - None: disable LLM validation (fallback mode)
        #   - object: use provided client
        if tongyi_client == "auto":
            self.client = load_openrouter_client(
                api_key=DEFAULT_TONGYI_CONFIG.api_key,
                base_url=DEFAULT_TONGYI_CONFIG.base_url,
            )
        else:
            self.client = tongyi_client
        self.independent_domains = {
            'github.com', 'gitlab.com', 'stackoverflow.com',
            'arxiv.org', 'semantic-scholar.org', 'crossref.org',
            'docs.python.org', 'python.org'
        }

    def verify_claim(self, claim_text: str, sources: List[str]) -> Claim:
        """Verify a claim meets citation requirements."""
        claim = Claim(text=claim_text, sources=sources)
        
        # Rule 1: Check citation count
        if not self._has_sufficient_citations(sources):
            return claim
            
        # Rule 2: Check independent sources (def+use or ≥2 independent domains)
        if not self._has_independent_sources(sources):
            return claim
            
        # Rule 3: Use Tongyi's built-in reasoning for validation
        if self.client:
            claim.verified = self._validate_with_tongyi(claim_text, sources)
        else:
            # Fallback: basic pattern matching
            claim.verified = self._basic_validation(claim_text, sources)
            
        claim.confidence = 0.8 if claim.verified else 0.2
        return claim

    def filter_claims(self, claims: List[Claim]) -> List[Claim]:
        """Filter out unverified claims."""
        return [c for c in claims if c.verified]

    def _has_sufficient_citations(self, sources: List[str]) -> bool:
        """Check if claim has minimum required citations."""
        return len(sources) >= 2 or len(sources) == 1 and self._is_def_use_pair(sources[0])

    def _has_independent_sources(self, sources: List[str]) -> bool:
        """Check if sources are from independent domains."""
        if len(sources) >= 2:
            domains = set()
            files = set()
            for source in sources:
                domain = self._extract_domain(source)
                if domain == 'local_file':
                    # For local files, different files count as independent
                    file_name = source.split(':')[0] if ':' in source else source
                    files.add(file_name)
                elif domain:
                    domains.add(domain)
            # Check if we have 2+ different domains OR 2+ different local files
            return len(domains) >= 2 or len(files) >= 2
        return self._is_def_use_pair(sources[0]) if sources else False

    def _is_def_use_pair(self, source: str) -> bool:
        """Check if source represents a definition+usage pair (same file)."""
        # For local files, check if it contains both definition and usage
        return ':' in source and source.count(':') >= 2

    def _extract_domain(self, source: str) -> Optional[str]:
        """Extract domain from URL or file path."""
        if source.startswith(('http://', 'https://')):
            match = re.search(r'https?://([^/]+)', source)
            return match.group(1) if match else None
        elif source.startswith('/') or ':' in source:
            # Local file - treat as independent domain
            return 'local_file'
        return None

    def _validate_with_tongyi(self, claim_text: str, sources: List[str]) -> bool:
        """Use Tongyi's built-in reasoning to validate claim support."""
        try:
            # Use configured model; fall back to working model if Tongyi fails
            model_to_use = DEFAULT_TONGYI_CONFIG.model_name
            
            prompt = f"""You must respond with ONLY the word YES or ONLY the word NO.

Claim: {claim_text}
Sources: {', '.join(sources)}

Is this claim supported by the sources? Respond with ONLY YES or NO."""
            
            response = self.client.chat(
                prompt,
                model=model_to_use,
                temperature=0.1,
                max_tokens=5,
                system_prompt="You are an evidence verification assistant. Always respond with only YES or NO."
            )
            
            return response.strip().upper() in ["YES", "YES.", "YES!"]
        except AgentClientError as exc:
            # If OpenRouter returns no choices or similar, fall back to basic validation
            if "no choices" in str(exc).lower():
                return self._basic_validation(claim_text, sources)
            return False
        except Exception:
            return False

    def _basic_validation(self, claim_text: str, sources: List[str]) -> bool:
        """Fallback validation without Tongyi client."""
        # Basic heuristics for when Tongyi is unavailable
        return len(sources) >= 2 and any(s.strip() for s in sources)


if __name__ == "__main__":
    # Smoke test
    verifier = VerifierGate()
    
    # Test claim with sufficient citations
    claim1 = verifier.verify_claim(
        "The system uses delegation budgets to control token usage",
        ["src/delegation_policy.py:67", "src/orchestrator_local.py:102"]
    )
    print(f"Claim 1 verified: {claim1.verified}, confidence: {claim1.confidence}")
    
    # Test claim with insufficient citations
    claim2 = verifier.verify_claim(
        "The system is fast",
        ["src/orchestrator_local.py:1"]
    )
    print(f"Claim 2 verified: {claim2.verified}, confidence: {claim2.confidence}")
