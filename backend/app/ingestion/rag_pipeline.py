"""PDF/HTML → ChromaDB ingestion pipeline.

Fetches unstructured sources (IRCC pages, StatCan analytical reports, Job Bank
trend pages, local PDFs), extracts clean text, chunks it, and upserts into a
persistent ChromaDB collection with source metadata for citations.
"""
import hashlib
import logging
import re
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.ingestion.chunking import chunk_text
from app.ingestion.embeddings import get_embedding_function
from app.ingestion.sources import RAG_DOCUMENTS

logger = logging.getLogger(__name__)


def get_chroma_collection():
    import chromadb

    settings = get_settings()
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return client.get_or_create_collection(
        name=settings.chroma_collection,
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )


def html_to_text(html: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()
    main = soup.find("main") or soup.body or soup
    text = main.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def pdf_to_text(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages)


def upsert_document(collection, *, key: str, text: str, title: str, url: str, lang: str = "en") -> int:
    chunks = chunk_text(text, metadata={"doc_key": key, "title": title, "url": url, "lang": lang})
    if not chunks:
        logger.warning("No chunks for %s", key)
        return 0
    # Deterministic ids → idempotent upsert
    ids = [f"{key}:{c.metadata['chunk_index']}:{hashlib.sha1(c.text.encode()).hexdigest()[:10]}"
           for c in chunks]
    # Remove previous version of the doc before inserting the new one
    existing = collection.get(where={"doc_key": key})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
    collection.add(
        ids=ids,
        documents=[c.text for c in chunks],
        metadatas=[c.metadata for c in chunks],
    )
    return len(chunks)


BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-CA,en;q=0.9,fr-CA;q=0.8",
}


def fetch_html(url: str, retries: int = 3) -> str:
    """Fetch a page with a browser-like UA and retries (canada.ca throttles bots)."""
    timeout = httpx.Timeout(connect=15, read=90, write=30, pool=15)
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as c:
                resp = c.get(url, headers=BROWSER_HEADERS)
                resp.raise_for_status()
                return resp.text
        except Exception as exc:  # timeout / 5xx / reset — retry
            last_exc = exc
            logger.warning("fetch_html attempt %d/%d failed for %s: %s",
                           attempt + 1, retries, url, exc)
    raise last_exc  # type: ignore[misc]


def run_rag_ingestion(local_pdf_dir: str | None = None) -> dict[str, int]:
    """Ingest all registered web documents plus any local PDFs."""
    collection = get_chroma_collection()
    results: dict[str, int] = {}

    raw_dir = Path(local_pdf_dir or get_settings().data_raw_dir)
    for doc in RAG_DOCUMENTS:
        try:
            try:
                text = html_to_text(fetch_html(doc["url"]))
            except Exception as fetch_exc:
                # Some canada.ca pages block non-browser clients (Akamai).
                # Fall back to a bundled snapshot in data/raw/<key>.txt|.html.
                local = next((f for ext in (".txt", ".html")
                              if (f := raw_dir / f"{doc['key']}{ext}").exists()), None)
                if local is None:
                    raise fetch_exc
                logger.warning("Fetch failed for %s (%s); using local snapshot %s",
                               doc["key"], fetch_exc, local.name)
                content = local.read_text(encoding="utf-8", errors="replace")
                text = html_to_text(content) if local.suffix == ".html" else content
            n = upsert_document(
                collection, key=doc["key"], text=text,
                title=doc["title_en"], url=doc["url"],
            )
            results[doc["key"]] = n
            logger.info("Ingested %s: %d chunks", doc["key"], n)
        except Exception as exc:
            logger.error("RAG ingestion failed for %s: %s", doc["key"], exc)
            results[doc["key"]] = 0

    pdf_dir = Path(local_pdf_dir or get_settings().data_raw_dir)
    if pdf_dir.exists():
        for pdf in sorted(pdf_dir.glob("*.pdf")):
            key = f"pdf:{pdf.stem}"
            try:
                n = upsert_document(
                    collection, key=key, text=pdf_to_text(pdf),
                    title=pdf.stem.replace("_", " "), url=str(pdf.name),
                )
                results[key] = n
            except Exception as exc:
                logger.error("PDF ingestion failed for %s: %s", pdf, exc)
                results[key] = 0
    return results
