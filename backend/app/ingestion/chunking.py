"""Text chunking for RAG ingestion. Pure stdlib — unit-testable."""
import re
from dataclasses import dataclass, field


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


def _split_sentences(text: str) -> list[str]:
    # Simple sentence splitter that respects common abbreviations poorly but predictably.
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ü0-9])", text)
    return [p.strip() for p in parts if p.strip()]


def chunk_text(
    text: str,
    *,
    chunk_size: int = 900,
    overlap: int = 150,
    metadata: dict | None = None,
) -> list[Chunk]:
    """Split text into overlapping chunks along paragraph/sentence boundaries.

    - chunk_size / overlap are in characters.
    - Paragraphs are kept together when possible; long paragraphs are split
      on sentence boundaries; pathological unbroken text is hard-split.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
    metadata = metadata or {}
    text = re.sub(r"[ \t]+", " ", text or "").strip()
    if not text:
        return []

    # Build units: paragraphs, splitting oversized ones into sentences.
    units: list[str] = []
    for para in re.split(r"\n{2,}", text):
        para = para.replace("\n", " ").strip()
        if not para:
            continue
        if len(para) <= chunk_size:
            units.append(para)
        else:
            for sent in _split_sentences(para):
                while len(sent) > chunk_size:  # pathological: no sentence breaks
                    units.append(sent[:chunk_size])
                    sent = sent[chunk_size - overlap:]
                if sent:
                    units.append(sent)

    chunks: list[Chunk] = []
    current = ""
    for unit in units:
        if current and len(current) + 1 + len(unit) > chunk_size:
            chunks.append(Chunk(text=current, metadata=dict(metadata)))
            carry = current[-overlap:] if overlap else ""
            if len(carry) + 1 + len(unit) > chunk_size:
                carry = ""  # overlap would overflow the next chunk
            current = carry
        current = f"{current} {unit}".strip() if current else unit
    if current:
        chunks.append(Chunk(text=current, metadata=dict(metadata)))

    for i, c in enumerate(chunks):
        c.metadata["chunk_index"] = i
    return chunks
