import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.scholar_adapter import ScholarAdapter, PaperMeta  # noqa: E402


def test_paper_meta_schema():
    # Ensure PaperMeta matches expected schema
    p = PaperMeta(
        id="test",
        title="Test Paper",
        authors=["Alice", "Bob"],
        venue="Test Conf",
        year=2025,
        abstract="Test abstract",
        doi="10.1000/test",
        url="https://example.com/test",
        pdf_url="https://example.com/test.pdf",
        source="test"
    )
    assert p.id == "test"
    assert p.authors == ["Alice", "Bob"]
    assert p.source == "test"


def test_semantic_scholar_provider():
    mock_response = {
        "data": [
            {
                "paperId": "abc123",
                "title": "Semantic Test",
                "authors": [{"name": "Alice"}],
                "venue": "Test Venue",
                "year": 2024,
                "abstract": "An abstract",
                "doi": "10.1000/abc",
                "url": "https://semanticscholar.org/abc",
                "openAccessPdf": {"url": "https://semanticscholar.org/abc.pdf"}
            }
        ]
    }
    with patch('src.scholar_adapter._http_get_json', return_value=mock_response) as mock_get:
        adapter = ScholarAdapter()
        adapter.cb["semantic_scholar"].call = lambda f, *a, **k: f(*a, **k)
        papers = adapter._semantic_scholar("test query")
        assert len(papers) == 1
        p = papers[0]
        assert p.title == "Semantic Test"
        assert p.source == "semantic_scholar"
        assert p.pdf_url == "https://semanticscholar.org/abc.pdf"
        mock_get.assert_called_once()


def test_crossref_provider():
    mock_response = {
        "message": {
            "items": [
                {
                    "DOI": "10.1000/def",
                    "title": ["Crossref Test"],
                    "author": [{"given": "Bob", "family": "Smith"}],
                    "published-print": {"date-parts": [[2023]]},
                    "URL": "https://api.crossref.org/works/10.1000/def"
                }
            ]
        }
    }
    with patch('src.scholar_adapter._http_get_json', return_value=mock_response) as mock_get:
        adapter = ScholarAdapter()
        adapter.cb["crossref"].call = lambda f, *a, **k: f(*a, **k)
        papers = adapter._crossref("test query")
        assert len(papers) == 1
        p = papers[0]
        assert p.title == "Crossref Test"
        assert p.source == "crossref"
        assert p.authors == ["Bob Smith"]
        mock_get.assert_called_once()


def test_arxiv_provider():
    mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <title>ArXiv Test</title>
    <author><name>Charlie</name></author>
    <published>2025-01-01T00:00:00Z</published>
    <summary>ArXiv abstract</summary>
    <id>http://arxiv.org/abs/2501.00001</id>
    <link title="pdf" href="http://arxiv.org/pdf/2501.00001.pdf"/>
  </entry>
</feed>"""
    with patch('src.scholar_adapter._http_get_xml') as mock_get:
        mock_root = MagicMock()
        mock_root.findall.return_value = [
            MagicMock(
                find=lambda tag, ns=None: {
                    "atom:title": MagicMock(text="ArXiv Test"),
                    "atom:author": MagicMock(find=lambda t, ns=None: MagicMock(text="Charlie") if t=="atom:name" else None),
                    "atom:published": MagicMock(text="2025-01-01T00:00:00Z"),
                    "atom:summary": MagicMock(text="ArXiv abstract"),
                    "atom:id": MagicMock(text="http://arxiv.org/abs/2501.00001"),
                }[tag],
                findall=lambda tag, ns=None: {
                    "atom:author": [MagicMock(find=lambda t, ns=None: MagicMock(text="Charlie") if t=="atom:name" else None)],
                    "atom:link": [MagicMock(get=lambda k: "pdf" if k=="title" else "http://arxiv.org/pdf/2501.00001.pdf")],
                }[tag]
            )
        ]
        mock_get.return_value = mock_root
        adapter = ScholarAdapter()
        adapter.cb["arxiv"].call = lambda f, *a, **k: f(*a, **k)
        papers = adapter._arxiv("test query")
        assert len(papers) == 1
        p = papers[0]
        assert p.title == "ArXiv Test"
        assert p.source == "arxiv"
        assert p.pdf_url == "http://arxiv.org/pdf/2501.00001.pdf"


def test_openalex_provider():
    mock_response = {
        "results": [
            {
                "id": "https://openalex.org/W123",
                "title": "OpenAlex Test",
                "authorships": [{"author": {"display_name": "Dana"}}],
                "publication_year": 2022,
                "primary_location": {"source": {"display_name": "Open Venue"}},
                "abstract_inverted_index": {"Test": [0], "abstract": [1]},
                "doi": "10.1000/open",
                "open_access": {"oa_url": "https://openalex.org/W123.pdf"}
            }
        ]
    }
    with patch('src.scholar_adapter._http_get_json', return_value=mock_response) as mock_get:
        adapter = ScholarAdapter()
        adapter.cb["openalex"].call = lambda f, *a, **k: f(*a, **k)
        papers = adapter._openalex("test query")
        assert len(papers) == 1
        p = papers[0]
        assert p.title == "OpenAlex Test"
        assert p.source == "openalex"
        assert p.abstract == "Test abstract"
        mock_get.assert_called_once()


def test_search_with_fallbacks_and_deduplication():
    # Mock providers to return overlapping papers
    def mock_semantic(q):
        return [PaperMeta(id="1", title="Paper A", authors=[], venue=None, year=2025, abstract=None, doi=None, url=None, pdf_url=None, source="semantic_scholar")]
    def mock_crossref(q):
        return [PaperMeta(id="2", title="Paper A", authors=[], venue=None, year=2025, abstract=None, doi=None, url=None, pdf_url=None, source="crossref")]
    def mock_arxiv(q):
        return [PaperMeta(id="3", title="Paper B", authors=[], venue=None, year=2025, abstract=None, doi=None, url=None, pdf_url=None, source="arxiv")]
    def mock_openalex(q):
        return []  # empty
    adapter = ScholarAdapter()
    adapter._semantic_scholar = mock_semantic
    adapter._crossref = mock_crossref
    adapter._arxiv = mock_arxiv
    adapter._openalex = mock_openalex
    papers = adapter.search("test", k=5)
    # Should deduplicate by title+year, returning only Paper A and Paper B
    titles = {p.title for p in papers}
    assert titles == {"Paper A", "Paper B"}
    # Paper A should come from semantic_scholar (first provider)
    assert next(p for p in papers if p.title == "Paper A").source == "semantic_scholar"


def test_circuit_breaker_opens_on_failures():
    adapter = ScholarAdapter()
    breaker = adapter.cb["semantic_scholar"]
    # Force failures
    failing_func = lambda: (_ for _ in ()).throw(Exception("fail"))
    for _ in range(adapter.cb["semantic_scholar"].failure_threshold):
        try:
            breaker.call(failing_func)
        except Exception:
            pass
    # Now circuit should be open
    try:
        breaker.call(failing_func)
        assert False, "Expected circuit breaker open exception"
    except Exception as e:
        assert "open" in str(e).lower()
