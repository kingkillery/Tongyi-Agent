"""
PDF Tools for Tongyi Agent
Provides PDF processing capabilities using PyMuPDF and pdf-tools-mcp integration.
"""
from __future__ import annotations

import os
import tempfile
import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
import logging

try:
    import fitz  # PyMuPDF
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    logging.warning("PyMuPDF not available. PDF tools will be limited.")

logger = logging.getLogger(__name__)

@dataclass
class PDFInfo:
    """PDF document information."""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    page_count: int = 0
    is_encrypted: bool = False
    is_pdf: bool = True

@dataclass
class PDFTextContent:
    """Text content extracted from PDF."""
    text: str
    page_number: int
    bbox: Optional[List[float]] = None  # x0, y0, x1, y1

@dataclass
class PDFPageInfo:
    """Information about a PDF page."""
    page_number: int
    width: float
    height: float
    rotation: int
    text_content: List[PDFTextContent]

class PDFProcessor:
    """PDF processing utilities for Tongyi Agent."""

    def __init__(self, workspace_path: Optional[str] = None):
        self.workspace_path = workspace_path or os.getcwd()
        self.temp_dir = os.path.join(self.workspace_path, "temp_pdf")
        os.makedirs(self.temp_dir, exist_ok=True)

    def _resolve_path(self, path: str) -> str:
        """Resolve PDF path relative to workspace."""
        if os.path.isabs(path):
            full_path = path
        else:
            full_path = os.path.join(self.workspace_path, path)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"PDF file not found: {path}")

        return full_path

    def get_pdf_info(self, path: str) -> PDFInfo:
        """Extract metadata from PDF file."""
        if not PYPDF_AVAILABLE:
            return PDFInfo(
                title=os.path.basename(path),
                page_count=0,
                is_pdf=False,
                is_encrypted=False
            )

        full_path = self._resolve_path(path)

        try:
            doc = fitz.open(full_path)
            metadata = doc.metadata

            info = PDFInfo(
                title=metadata.get('title'),
                author=metadata.get('author'),
                subject=metadata.get('subject'),
                creator=metadata.get('creator'),
                producer=metadata.get('producer'),
                creation_date=metadata.get('creationDate'),
                modification_date=metadata.get('modDate'),
                page_count=doc.page_count,
                is_encrypted=doc.needs_pass,
                is_pdf=True
            )

            doc.close()
            return info

        except Exception as e:
            logger.error(f"Error reading PDF info from {path}: {e}")
            return PDFInfo(
                title=os.path.basename(path),
                page_count=0,
                is_pdf=False,
                is_encrypted=False
            )

    def extract_text(self, path: str, pages: Optional[List[int]] = None) -> List[PDFPageInfo]:
        """Extract text content from PDF pages."""
        if not PYPDF_AVAILABLE:
            raise ImportError("PyMuPDF is required for PDF text extraction")

        full_path = self._resolve_path(path)

        try:
            doc = fitz.open(full_path)
            pages_info = []

            # Determine which pages to process
            if pages is None:
                page_range = range(doc.page_count)
            else:
                page_range = [p - 1 for p in pages if 0 < p <= doc.page_count]

            for page_num in page_range:
                try:
                    page = doc[page_num]

                    # Extract text blocks
                    text_blocks = []
                    blocks = page.get_text("dict")["blocks"]

                    for block in blocks:
                        if "lines" in block:  # Text block
                            for line in block["lines"]:
                                for span in line["spans"]:
                                    text_content = PDFTextContent(
                                        text=span["text"],
                                        page_number=page_num + 1,
                                        bbox=span.get("bbox")
                                    )
                                    text_blocks.append(text_content)

                    page_info = PDFPageInfo(
                        page_number=page_num + 1,
                        width=page.rect.width,
                        height=page.rect.height,
                        rotation=page.rotation,
                        text_content=text_blocks
                    )
                    pages_info.append(page_info)

                except Exception as e:
                    logger.warning(f"Error processing page {page_num + 1}: {e}")
                    continue

            doc.close()
            return pages_info

        except Exception as e:
            logger.error(f"Error extracting text from PDF {path}: {e}")
            raise

    def extract_text_simple(self, path: str) -> str:
        """Extract all text from PDF as a simple string."""
        if not PYPDF_AVAILABLE:
            raise ImportError("PyMuPDF is required for PDF text extraction")

        full_path = self._resolve_path(path)

        try:
            doc = fitz.open(full_path)
            text = ""

            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_text = page.get_text()
                text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"

            doc.close()
            return text.strip()

        except Exception as e:
            logger.error(f"Error extracting simple text from PDF {path}: {e}")
            raise

    def search_in_pdf(self, path: str, query: str) -> List[Dict[str, Any]]:
        """Search for text within PDF pages."""
        if not PYPDF_AVAILABLE:
            raise ImportError("PyMuPDF is required for PDF text search")

        full_path = self._resolve_path(path)
        results = []

        try:
            doc = fitz.open(full_path)

            for page_num in range(doc.page_count):
                page = doc[page_num]
                text_instances = page.search_for(query)

                for instance in text_instances:
                    results.append({
                        "page": page_num + 1,
                        "bbox": list(instance),
                        "context": self._get_context_around_text(page, instance, query)
                    })

            doc.close()
            return results

        except Exception as e:
            logger.error(f"Error searching in PDF {path}: {e}")
            raise

    def _get_context_around_text(self, page, bbox, query, context_size=100) -> str:
        """Get text context around a search result."""
        try:
            # Extract text from a slightly larger area
            expanded_bbox = [
                max(0, bbox[0] - context_size),
                max(0, bbox[1] - 20),
                bbox[2] + context_size,
                bbox[3] + 20
            ]

            rect = fitz.Rect(expanded_bbox)
            text = page.get_text("text", clip=rect)
            return text.strip()

        except Exception:
            return f"Found '{query}' on page"

    def merge_pdfs(self, pdf_paths: List[str], output_path: str) -> str:
        """Merge multiple PDF files into one."""
        if not PYPDF_AVAILABLE:
            raise ImportError("PyMuPDF is required for PDF merging")

        # Resolve all input paths
        full_paths = [self._resolve_path(path) for path in pdf_paths]

        # Resolve output path
        if not os.path.isabs(output_path):
            full_output_path = os.path.join(self.workspace_path, output_path)
        else:
            full_output_path = output_path

        try:
            # Create output document
            output_doc = fitz.open()

            for pdf_path in full_paths:
                input_doc = fitz.open(pdf_path)
                output_doc.insert_pdf(input_doc)
                input_doc.close()

            output_doc.save(full_output_path)
            output_doc.close()

            return full_output_path

        except Exception as e:
            logger.error(f"Error merging PDFs: {e}")
            raise

    def download_pdf_from_url(self, url: str, filename: Optional[str] = None) -> str:
        """Download PDF from URL and save to temp directory."""
        try:
            import requests
            import uuid

            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            if not filename:
                filename = f"downloaded_{uuid.uuid4().hex[:8]}.pdf"

            filepath = os.path.join(self.temp_dir, filename)

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return filepath

        except Exception as e:
            logger.error(f"Error downloading PDF from {url}: {e}")
            raise

# Global PDF processor instance
_pdf_processor = None

def get_pdf_processor(workspace_path: Optional[str] = None) -> PDFProcessor:
    """Get or create PDF processor instance."""
    global _pdf_processor
    if _pdf_processor is None or workspace_path != _pdf_processor.workspace_path:
        _pdf_processor = PDFProcessor(workspace_path)
    return _pdf_processor