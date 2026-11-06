"""File-type dispatch loaders for the Pearlz knowledge base."""

from __future__ import annotations

import csv
import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)

logger = logging.getLogger("supportpearlz.ingestion")

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".md", ".txt", ".csv"}

DOC_TYPE_BY_KEYWORD: list[tuple[str, str]] = [
    ("warranty", "policy"),
    ("refund", "policy"),
    ("return", "policy"),
    ("shipping", "policy"),
    ("privacy", "policy"),
    ("faq", "faq"),
    ("pricing", "pricing"),
    ("price", "pricing"),
    ("troubleshooting", "guide"),
    ("installation", "guide"),
    ("manual", "manual"),
    ("service", "policy"),
    ("maintenance", "policy"),
    ("handbook", "guide"),
    ("changelog", "guide"),
    ("release", "guide"),
]


def infer_doc_type(filename: str) -> str:
    stem = filename.lower()
    for keyword, doc_type in DOC_TYPE_BY_KEYWORD:
        if keyword in stem:
            return doc_type
    return "guide"


def infer_product_line(filename: str, text: str = "") -> str:
    blob = f"{filename} {text[:2000]}".lower()
    if "aquapearl 500" in blob or "aquapearl500" in blob or "ap500" in blob:
        return "AquaPearl 500 Pro"
    if "aquapearl 300" in blob or "aquapearl300" in blob or "ap300" in blob:
        return "AquaPearl 300"
    if "aeropearl" in blob:
        return "AeroPearl Mini"
    return "all"


def normalise_whitespace(text: str) -> str:
    """Collapse runs of whitespace; preserve paragraph breaks lightly."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Strip repeated page headers/footers that look like "Page N of M"
    text = re.sub(r"(?m)^\s*Page\s+\d+\s+of\s+\d+\s*$", "", text)
    text = re.sub(r"(?m)^\s*Pearlz Home Systems\s*[—\-].*$", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


@dataclass
class IngestionReportRow:
    file_name: str
    detected_type: str
    status: str
    char_count: int = 0
    page_or_section_count: int = 0
    metadata_keys: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class IngestionResult:
    documents: list[Document]
    rows: list[IngestionReportRow]
    files_found: int = 0
    files_loaded: int = 0
    files_skipped: int = 0

    def summary(self) -> str:
        lines = [
            "=== Ingestion Report ===",
            f"Files found:   {self.files_found}",
            f"Files loaded:  {self.files_loaded}",
            f"Files skipped: {self.files_skipped}",
            f"Documents:     {len(self.documents)}",
            "",
            f"{'file':40} {'type':8} {'status':8} {'chars':>8} {'pages':>6}  metadata / reason",
            "-" * 100,
        ]
        for row in self.rows:
            meta = ",".join(row.metadata_keys) if row.metadata_keys else row.reason
            lines.append(
                f"{row.file_name[:40]:40} {row.detected_type:8} {row.status:8} "
                f"{row.char_count:8} {row.page_or_section_count:6}  {meta}"
            )
        return "\n".join(lines)


def _base_metadata(path: Path, doc_type: str, version: str = "2026.1") -> dict[str, Any]:
    return {
        "source": path.name,
        "source_path": str(path),
        "doc_type": doc_type,
        "product_line": infer_product_line(path.name),
        "version": version,
        "last_updated": "2026-01-15",
        "location": "",
    }


def load_pdf(path: Path) -> list[Document]:
    loader = PyPDFLoader(str(path))
    pages = loader.load()
    docs: list[Document] = []
    meta = _base_metadata(path, infer_doc_type(path.name))
    for page in pages:
        text = normalise_whitespace(page.page_content)
        if not text:
            continue
        page_no = page.metadata.get("page", 0)
        # PyPDFLoader is 0-indexed
        location = f"p.{int(page_no) + 1}"
        md = {**meta, **page.metadata}
        md.update(
            {
                "source": path.name,
                "doc_type": meta["doc_type"],
                "product_line": infer_product_line(path.name, text),
                "location": location,
                "page": int(page_no) + 1,
                "content_hash": content_hash(text),
            }
        )
        docs.append(Document(page_content=text, metadata=md))
    return docs


def load_docx(path: Path) -> list[Document]:
    loader = Docx2txtLoader(str(path))
    docs = loader.load()
    out: list[Document] = []
    meta = _base_metadata(path, infer_doc_type(path.name))
    for doc in docs:
        text = normalise_whitespace(doc.page_content)
        if not text:
            continue
        md = {**meta, **doc.metadata}
        md.update(
            {
                "source": path.name,
                "location": "document",
                "product_line": infer_product_line(path.name, text),
                "content_hash": content_hash(text),
            }
        )
        out.append(Document(page_content=text, metadata=md))
    return out


def load_markdown(path: Path) -> list[Document]:
    # Prefer plain text for reliability; fall back if unstructured fails
    try:
        loader = UnstructuredMarkdownLoader(str(path))
        docs = loader.load()
    except Exception:  # noqa: BLE001
        loader = TextLoader(str(path), encoding="utf-8")
        docs = loader.load()

    text = normalise_whitespace("\n\n".join(d.page_content for d in docs))
    if not text:
        return []

    # Split lightly by top-level headings so location metadata is useful
    sections = re.split(r"(?m)^(?=#{1,3}\s)", text)
    if len(sections) <= 1:
        meta = _base_metadata(path, infer_doc_type(path.name))
        meta.update(
            {
                "location": "full",
                "product_line": infer_product_line(path.name, text),
                "content_hash": content_hash(text),
            }
        )
        return [Document(page_content=text, metadata=meta)]

    out: list[Document] = []
    for block in sections:
        block = block.strip()
        if not block:
            continue
        heading_match = re.match(r"#{1,3}\s+(.+)", block)
        heading = heading_match.group(1).strip() if heading_match else "section"
        # Restore heading marker if stripped by split
        content = block if block.startswith("#") else f"## {block}"
        content = normalise_whitespace(content)
        meta = _base_metadata(path, infer_doc_type(path.name))
        meta.update(
            {
                "location": heading[:120],
                "section": heading[:120],
                "product_line": infer_product_line(path.name, content),
                "content_hash": content_hash(content),
            }
        )
        out.append(Document(page_content=content, metadata=meta))
    return out


def load_txt(path: Path) -> list[Document]:
    loader = TextLoader(str(path), encoding="utf-8")
    docs = loader.load()
    out: list[Document] = []
    meta = _base_metadata(path, infer_doc_type(path.name))
    for doc in docs:
        text = normalise_whitespace(doc.page_content)
        if not text:
            continue
        md = {**meta}
        md.update(
            {
                "location": "full",
                "product_line": infer_product_line(path.name, text),
                "content_hash": content_hash(text),
            }
        )
        out.append(Document(page_content=text, metadata=md))
    return out


def load_csv(path: Path) -> list[Document]:
    """Load each CSV row as a self-describing document so SKU and price stay together."""
    out: list[Document] = []
    meta_base = _base_metadata(path, "pricing")
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            return []
        for i, row in enumerate(reader, start=1):
            cleaned = {k: (v or "").strip() for k, v in row.items() if k}
            if not any(cleaned.values()):
                continue
            sku = cleaned.get("sku") or cleaned.get("SKU") or f"row-{i}"
            # Sentence form for better embeddings
            parts = [f"{k.replace('_', ' ')}: {v}" for k, v in cleaned.items() if v]
            text = f"Product pricing record. " + ". ".join(parts) + "."
            text = normalise_whitespace(text)
            md = {**meta_base}
            md.update(
                {
                    "location": f"row:{sku}",
                    "sku": sku,
                    "product_line": cleaned.get("product_name")
                    or cleaned.get("product_line")
                    or "all",
                    "content_hash": content_hash(text),
                }
            )
            out.append(Document(page_content=text, metadata=md))
    return out


LOADER_DISPATCH: dict[str, Callable[[Path], list[Document]]] = {
    ".pdf": load_pdf,
    ".docx": load_docx,
    ".md": load_markdown,
    ".txt": load_txt,
    ".csv": load_csv,
}


def load_knowledge_base(kb_path: Path) -> IngestionResult:
    """Walk `kb_path` recursively and load all supported files."""
    result = IngestionResult(documents=[], rows=[])
    if not kb_path.exists():
        raise FileNotFoundError(f"Knowledge base path not found: {kb_path}")

    files = sorted(
        p
        for p in kb_path.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    result.files_found = len(files)
    seen_hashes: set[str] = set()

    for path in files:
        ext = path.suffix.lower()
        loader = LOADER_DISPATCH.get(ext)
        row = IngestionReportRow(
            file_name=path.name,
            detected_type=ext.lstrip("."),
            status="pending",
        )
        if loader is None:
            row.status = "skipped"
            row.reason = f"unsupported extension {ext}"
            result.files_skipped += 1
            result.rows.append(row)
            continue

        try:
            docs = loader(path)
        except Exception as exc:  # noqa: BLE001 — per-file isolation
            logger.warning("Skipping unreadable file %s: %s", path.name, exc)
            row.status = "skipped"
            row.reason = str(exc)
            result.files_skipped += 1
            result.rows.append(row)
            continue

        if not docs:
            row.status = "skipped"
            row.reason = "empty after normalisation"
            result.files_skipped += 1
            result.rows.append(row)
            continue

        kept: list[Document] = []
        for doc in docs:
            if not doc.page_content.strip():
                continue
            if not doc.metadata.get("source"):
                doc.metadata["source"] = path.name
            if not doc.metadata.get("doc_type"):
                doc.metadata["doc_type"] = infer_doc_type(path.name)
            h = doc.metadata.get("content_hash") or content_hash(doc.page_content)
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            doc.metadata["content_hash"] = h
            kept.append(doc)

        if not kept:
            row.status = "skipped"
            row.reason = "duplicate content"
            result.files_skipped += 1
            result.rows.append(row)
            continue

        result.documents.extend(kept)
        result.files_loaded += 1
        row.status = "loaded"
        row.char_count = sum(len(d.page_content) for d in kept)
        row.page_or_section_count = len(kept)
        row.metadata_keys = sorted({k for d in kept for k in d.metadata.keys()})
        result.rows.append(row)

    return result
