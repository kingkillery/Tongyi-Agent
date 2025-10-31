"""
Scholar Adapter with Fallbacks
--------------------------------
Purpose: Robust academic retrieval with retries, rate limits, and provider fallbacks.

Providers sketched (HTTP integration points are stubbed to keep this offline-safe):
- primary: semantic_scholar (by API), crossref
- fallbacks: arxiv (api), openalex (optional)

All calls enforce:
- timeout_s: 60
- retries: up to 3 with jittered backoff
- per-host token bucket (simple in-process)

Output Schema (PaperMeta):
{
  "id": str,
  "title": str,
  "authors": [str],
  "venue": str | None,
  "year": int | None,
  "abstract": str | None,
  "doi": str | None,
  "url": str | None,
  "pdf_url": str | None,
  "source": str
}
"""
from __future__ import annotations

import hashlib
import json
import random
import threading
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import urllib.parse
import urllib.request


DEFAULT_TIMEOUT_S = 60
MAX_RETRIES = 3


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout_s: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_s
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        self.lock = threading.Lock()

    def call(self, func, *args, **kwargs):
        with self.lock:
            if self.state == "open":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "half-open"
                else:
                    raise Exception("Circuit breaker is open")
        try:
            result = func(*args, **kwargs)
            with self.lock:
                self.failure_count = 0
                self.state = "closed"
            return result
        except Exception as e:
            with self.lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
            raise


class RateLimiter:
    def __init__(self, rate_per_s: float, capacity: int):
        self.rate = rate_per_s
        self.capacity = capacity
        self.tokens = capacity
        self.ts = time.time()
        self.lock = threading.Lock()

    def acquire(self, cost: int = 1) -> None:
        with self.lock:
            now = time.time()
            elapsed = now - self.ts
            self.ts = now
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            if self.tokens < cost:
                need = cost - self.tokens
                wait_s = need / self.rate if self.rate > 0 else 0.0
                time.sleep(max(0.0, wait_s))
                self.tokens = max(0.0, self.tokens - cost)
            else:
                self.tokens -= cost


def _jitter_backoff(attempt: int, base: float = 0.6, cap: float = 5.0) -> float:
    return min(cap, base * (2 ** (attempt - 1))) * (0.5 + random.random())


def _http_get_json(url: str, timeout_s: int = DEFAULT_TIMEOUT_S, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "scholar-adapter/1.0"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        data = resp.read()
        ctype = resp.headers.get("Content-Type", "application/json")
        if "json" not in ctype:
            # best-effort JSON decode
            return json.loads(data.decode("utf-8", errors="ignore"))
        return json.loads(data)


def _http_get_xml(url: str, timeout_s: int = DEFAULT_TIMEOUT_S, headers: Optional[Dict[str, str]] = None) -> ET.Element:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "scholar-adapter/1.0"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        data = resp.read()
        return ET.fromstring(data.decode("utf-8", errors="ignore"))


def _norm_query(q: str) -> str:
    return " ".join(q.lower().split())


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class PaperMeta:
    id: str
    title: str
    authors: List[str]
    venue: Optional[str]
    year: Optional[int]
    abstract: Optional[str]
    doi: Optional[str]
    url: Optional[str]
    pdf_url: Optional[str]
    source: str


class ScholarAdapter:
    def __init__(self, timeout_s: int = DEFAULT_TIMEOUT_S):
        # simple per-host rate limits
        self.rl = {
            "semantic_scholar": RateLimiter(rate_per_s=2.0, capacity=5),
            "crossref": RateLimiter(rate_per_s=5.0, capacity=10),
            "arxiv": RateLimiter(rate_per_s=2.0, capacity=5),
            "openalex": RateLimiter(rate_per_s=10.0, capacity=20),
        }
        self.cb = {
            "semantic_scholar": CircuitBreaker(),
            "crossref": CircuitBreaker(),
            "arxiv": CircuitBreaker(),
            "openalex": CircuitBreaker(),
        }
        self.timeout_s = timeout_s

    # -------- Providers (sketched) --------
    def _semantic_scholar(self, query: str) -> List[PaperMeta]:
        self.rl["semantic_scholar"].acquire()
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": 10,
            "fields": "title,authors,venue,year,abstract,doi,url,openAccessPdf"
        }
        encoded = urllib.parse.urlencode(params)
        full_url = f"{url}?{encoded}"
        raw = self.cb["semantic_scholar"].call(_http_get_json, full_url, timeout_s=self.timeout_s)
        papers = []
        for item in raw.get("data", []):
            authors = [a.get("name", "") for a in item.get("authors", []) if a.get("name")]
            pdf_url = None
            if item.get("openAccessPdf") and item["openAccessPdf"].get("url"):
                pdf_url = item["openAccessPdf"]["url"]
            papers.append(PaperMeta(
                id=item.get("paperId", ""),
                title=item.get("title", ""),
                authors=authors,
                venue=item.get("venue"),
                year=item.get("year"),
                abstract=item.get("abstract"),
                doi=item.get("doi"),
                url=item.get("url"),
                pdf_url=pdf_url,
                source="semantic_scholar"
            ))
        return papers

    def _crossref(self, query: str) -> List[PaperMeta]:
        self.rl["crossref"].acquire()
        url = "https://api.crossref.org/works"
        params = {
            "query": query,
            "limit": 10,
            "select": "title,author,published-print,DOI,URL,link"
        }
        encoded = urllib.parse.urlencode(params)
        full_url = f"{url}?{encoded}"
        raw = self.cb["crossref"].call(_http_get_json, full_url, timeout_s=self.timeout_s)
        papers = []
        for item in raw.get("message", {}).get("items", []):
            authors = []
            if "author" in item:
                authors = [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in item["author"] if a.get("family")]
            year = None
            if item.get("published-print") and item["published-print"].get("date-parts"):
                year = item["published-print"]["date-parts"][0][0]
            papers.append(PaperMeta(
                id=item.get("DOI", ""),
                title=" ".join(item.get("title", [])),
                authors=authors,
                venue=None,  # Crossref doesn't provide a simple venue field
                year=year,
                abstract=None,  # Crossref doesn't provide abstracts
                doi=item.get("DOI"),
                url=item.get("URL"),
                pdf_url=None,
                source="crossref"
            ))
        return papers

    def _arxiv(self, query: str) -> List[PaperMeta]:
        self.rl["arxiv"].acquire()
        # arXiv API expects query in format: ti:"title terms" OR au:"author name"
        # We'll use a simple all: search
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": 10
        }
        encoded = urllib.parse.urlencode(params)
        full_url = f"{url}?{encoded}"
        root = self.cb["arxiv"].call(_http_get_xml, full_url, timeout_s=self.timeout_s)
        papers = []
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        for entry in root.findall("atom:entry", ns):
            title_elem = entry.find("atom:title", ns)
            title = title_elem.text.strip() if title_elem is not None else ""
            # Extract authors
            authors = []
            for author in entry.findall("atom:author", ns):
                name_elem = author.find("atom:name", ns)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())
            # Year from published
            year = None
            published_elem = entry.find("atom:published", ns)
            if published_elem is not None and published_elem.text:
                try:
                    year = int(published_elem.text[:4])
                except ValueError:
                    pass
            # Abstract
            abstract_elem = entry.find("atom:summary", ns)
            abstract = abstract_elem.text.strip() if abstract_elem is not None else None
            # arXiv ID and URL
            id_elem = entry.find("atom:id", ns)
            paper_id = id_elem.text.split("/")[-1] if id_elem is not None else ""
            url_link = id_elem.text if id_elem is not None else None
            # PDF URL (usually exists)
            pdf_url = None
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "pdf":
                    pdf_url = link.get("href")
                    break
            papers.append(PaperMeta(
                id=paper_id,
                title=title,
                authors=authors,
                venue=None,  # arXiv preprints have no venue
                year=year,
                abstract=abstract,
                doi=None,  # arXiv IDs are not DOIs
                url=url_link,
                pdf_url=pdf_url,
                source="arxiv"
            ))
        return papers

    def _openalex(self, query: str) -> List[PaperMeta]:
        # OpenAlex has generous limits; we can be less aggressive
        url = "https://api.openalex.org/works"
        params = {
            "search": query,
            "per-page": 10,
            "select": "id,title,authorships,publication_year,primary_location,abstract_inverted_index,doi,open_access"
        }
        encoded = urllib.parse.urlencode(params)
        full_url = f"{url}?{encoded}"
        raw = self.cb["openalex"].call(_http_get_json, full_url, timeout_s=self.timeout_s)
        papers = []
        for item in raw.get("results", []):
            authors = [a["author"]["display_name"] for a in item.get("authorships", []) if a.get("author") and a["author"].get("display_name")]
            venue = None
            if item.get("primary_location") and item["primary_location"].get("source") and item["primary_location"]["source"].get("display_name"):
                venue = item["primary_location"]["source"]["display_name"]
            # Reconstruct abstract from inverted index if available
            abstract = None
            if item.get("abstract_inverted_index"):
                inv = item["abstract_inverted_index"]
                # Flatten inverted index
                tokens = []
                for word, positions in inv.items():
                    for pos in positions:
                        tokens.append((pos, word))
                tokens.sort()
                abstract = " ".join(word for _, word in tokens)
            pdf_url = None
            if item.get("open_access") and item["open_access"].get("oa_url"):
                pdf_url = item["open_access"]["oa_url"]
            papers.append(PaperMeta(
                id=item.get("id", "").split("/")[-1],
                title=item.get("title", ""),
                authors=authors,
                venue=venue,
                year=item.get("publication_year"),
                abstract=abstract,
                doi=item.get("doi"),
                url=item.get("id"),
                pdf_url=pdf_url,
                source="openalex"
            ))
        return papers

    # -------- Orchestration with retries/fallbacks --------
    def search(self, query: str, k: int = 10) -> List[PaperMeta]:
        q = _norm_query(query)
        providers = [self._semantic_scholar, self._crossref, self._arxiv, self._openalex]
        results: List[PaperMeta] = []
        seen = set()
        for provider in providers:
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    papers = provider(q)
                    for p in papers:
                        key = (p.title.lower(), p.year or 0)
                        if key in seen:
                            continue
                        seen.add(key)
                        results.append(p)
                        if len(results) >= k:
                            return results
                    break  # provider succeeded (even if empty)
                except Exception:
                    time.sleep(_jitter_backoff(attempt))
                    continue
        return results


if __name__ == "__main__":
    sa = ScholarAdapter()
    out = sa.search("large context retrieval compression 2025", k=5)
    print(json.dumps([p.__dict__ for p in out], indent=2))

