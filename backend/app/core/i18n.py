"""Lightweight FR/EN language detection (no external deps).

Used to pick the response language when the client does not send one.
"""
import re
import unicodedata

_FR_STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "et", "est", "sont", "je",
    "tu", "il", "elle", "nous", "vous", "ils", "elles", "mon", "ma", "mes", "que",
    "qui", "quoi", "pour", "dans", "avec", "sur", "pas", "plus", "quel", "quelle",
    "quels", "quelles", "comment", "combien", "pourquoi", "quand", "être", "avoir",
    "salaire", "emploi", "travail", "immigrant", "immigrants", "délai", "délais",
    "permis", "résident", "résidents", "année", "années", "où", "chez", "après",
}
_EN_STOPWORDS = {
    "the", "a", "an", "and", "is", "are", "i", "you", "he", "she", "we", "they",
    "my", "your", "what", "which", "who", "for", "in", "with", "on", "not", "how",
    "many", "much", "why", "when", "where", "be", "have", "do", "does", "can",
    "salary", "job", "jobs", "work", "immigrant", "immigrants", "wait", "permit",
    "resident", "residents", "year", "years", "after", "at",
}
_FR_ACCENTS = set("àâäéèêëîïôöùûüçœ")


def detect_language(text: str, default: str = "en") -> str:
    """Return 'fr' or 'en' for the given text."""
    if not text or not text.strip():
        return default
    lowered = text.lower()
    accents = sum(1 for ch in lowered if ch in _FR_ACCENTS)
    words = re.findall(r"[a-zà-öø-ÿ']+", lowered)
    if not words:
        return default
    fr_hits = sum(1 for w in words if w in _FR_STOPWORDS)
    en_hits = sum(1 for w in words if w in _EN_STOPWORDS)
    fr_score = fr_hits + 2 * accents
    if fr_score == 0 and en_hits == 0:
        return default
    return "fr" if fr_score >= en_hits else "en"


def normalize_lang(lang: str | None, fallback_text: str = "", default: str = "en") -> str:
    """Normalize a client-provided language code, falling back to detection."""
    if lang:
        code = unicodedata.normalize("NFKC", lang).strip().lower()[:2]
        if code in ("fr", "en"):
            return code
    return detect_language(fallback_text, default=default)
