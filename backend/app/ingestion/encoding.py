"""Robust decoding of government CSV files.

IRCC serves its open-data CSVs as binary streams that may be UTF-8 with BOM,
UTF-16 (LE/BE), or Latin-1. This module sniffs and decodes reliably.
Pure stdlib — unit-testable without third-party deps.
"""
import codecs

_BOMS = [
    (codecs.BOM_UTF8, "utf-8-sig"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
]
# utf-16 without BOM is caught by the NUL-byte heuristic below; keeping it out
# of the candidates avoids false positives (any even-length bytes "decode" as utf-16).
_CANDIDATES = ["utf-8", "cp1252", "latin-1"]


def sniff_encoding(raw: bytes) -> str:
    """Best-effort encoding detection for a raw byte payload."""
    for bom, enc in _BOMS:
        if raw.startswith(bom):
            return enc
    # Heuristic: many NUL bytes → UTF-16 without BOM
    sample = raw[:4096]
    if sample and sample.count(b"\x00") > len(sample) // 4:
        return "utf-16-le" if sample[1:2] == b"\x00" else "utf-16-be"
    for enc in _CANDIDATES:
        try:
            raw[:65536].decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "latin-1"  # never fails


def decode_bytes(raw: bytes) -> str:
    """Decode a raw payload to text, normalizing newlines."""
    text = raw.decode(sniff_encoding(raw), errors="replace")
    return text.replace("\r\n", "\n").replace("\r", "\n").lstrip("﻿")


def sniff_delimiter(text: str) -> str:
    """Detect CSV delimiter from the first non-empty line."""
    for line in text.split("\n"):
        if line.strip():
            counts = {d: line.count(d) for d in [",", ";", "\t", "|"]}
            best = max(counts, key=counts.get)
            return best if counts[best] > 0 else ","
    return ","
