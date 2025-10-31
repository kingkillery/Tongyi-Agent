"""
Content-Addressable Store (CAS)
-------------------------------
Stores blobs under sha256(content)+parser_ver, plus metadata with provenance.
Directory layout (relative to base_dir):
  blobs/<sha256>  (raw bytes)
  meta/<sha256>.json  (metadata: url, fetched_at, content_type, size, parser_ver, outlinks)
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class BlobMeta:
    key: str
    url: Optional[str]
    fetched_at: Optional[str]
    content_type: Optional[str]
    size: int
    parser_ver: str
    outlinks: Optional[list[str]]


class CAS:
    def __init__(self, base_dir: str = "data/cas") -> None:
        self.base = base_dir
        os.makedirs(self._blobs_dir, exist_ok=True)
        os.makedirs(self._meta_dir, exist_ok=True)

    @property
    def _blobs_dir(self) -> str:
        return os.path.join(self.base, "blobs")

    @property
    def _meta_dir(self) -> str:
        return os.path.join(self.base, "meta")

    def _hash(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def make_key(self, content: bytes, parser_ver: str) -> str:
        return f"{self._hash(content)}:{parser_ver}"

    def _paths(self, key: str) -> tuple[str, str]:
        sha, _, _ver = key.partition(":")
        return (
            os.path.join(self._blobs_dir, sha),
            os.path.join(self._meta_dir, f"{sha}.json"),
        )

    def put(self, content: bytes, *, url: str | None, fetched_at: str | None, content_type: str | None, parser_ver: str, outlinks: list[str] | None = None) -> str:
        key = self.make_key(content, parser_ver)
        blob_path, meta_path = self._paths(key)
        if not os.path.exists(blob_path):
            with open(blob_path, "wb") as f:
                f.write(content)
        meta = BlobMeta(key=key, url=url, fetched_at=fetched_at, content_type=content_type, size=len(content), parser_ver=parser_ver, outlinks=outlinks)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta.__dict__, f, ensure_ascii=False, indent=2)
        return key

    def get(self, key: str) -> tuple[bytes | None, Dict[str, Any] | None]:
        blob_path, meta_path = self._paths(key)
        content = None
        meta = None
        if os.path.exists(blob_path):
            with open(blob_path, "rb") as f:
                content = f.read()
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        return content, meta


if __name__ == "__main__":
    cas = CAS()
    k = cas.put(b"example body", url="https://example.com", fetched_at="2025-10-30T00:00:00Z", content_type="text/plain", parser_ver="jina-1.0", outlinks=["https://example.com/a"])
    blob, meta = cas.get(k)
    print(k, len(blob or b""), meta and meta.get("content_type"))

