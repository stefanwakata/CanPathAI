"""Citation collection and enforcement. Pure stdlib — unit-testable.

Every tool call registers the sources it used. After the agent answers,
`ensure_citations` appends a Sources section when the model forgot one —
citations are mandatory in every response.
"""
import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SourceRef:
    label: str
    source: str
    url: str | None = None


@dataclass
class CitationTracker:
    refs: list[SourceRef] = field(default_factory=list)

    def add(self, label: str, source: str, url: str | None = None) -> None:
        ref = SourceRef(label=label.strip(), source=source.strip(), url=url)
        if ref not in self.refs:
            self.refs.append(ref)

    def as_dicts(self) -> list[dict]:
        return [{"label": r.label, "source": r.source, "url": r.url} for r in self.refs]


_SOURCES_HEADER_RX = re.compile(
    r"(^|\n)\s*[#>*_\-\s]*(sources?|références?)\s*[:*]", re.IGNORECASE
)


def has_sources_section(text: str) -> bool:
    return bool(_SOURCES_HEADER_RX.search(text or ""))


def format_sources(refs: list[SourceRef], lang: str = "en") -> str:
    if not refs:
        return ""
    lines = ["\n\n**Sources:**"]
    for r in refs:
        if r.url:
            lines.append(f"- [{r.label}]({r.url})")
        else:
            lines.append(f"- {r.label} — {r.source}")
    return "\n".join(lines)


def ensure_citations(answer: str, tracker: CitationTracker, lang: str = "en") -> str:
    """Guarantee the answer carries a Sources section when sources were used."""
    if not tracker.refs:
        return answer
    if has_sources_section(answer):
        return answer
    return answer + format_sources(tracker.refs, lang=lang)
