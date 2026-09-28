"""CanPath AI agent: native tool-calling loop on Claude via langchain-anthropic.

Uses only langchain-core APIs (bind_tools + message types), which are stable
across langchain 0.2/0.3/1.x — no dependency on the legacy AgentExecutor.
"""
import logging
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.agent.citations import CitationTracker, ensure_citations
from app.agent.memory import memory_store
from app.agent.tools import make_tools
from app.core.config import get_settings
from app.core.i18n import normalize_lang

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 8

SYSTEM_PROMPT = """You are CanPath AI, a bilingual (French/English) assistant that helps skilled \
immigrants, international students (PGWP holders) and career changers understand their real \
employment prospects in Canada by crossing IRCC immigration data with Statistics Canada and \
Job Bank labour-market data.

Rules:
1. ALWAYS answer in the user's language: {language_name}. Keep the same language for chart titles.
2. Ground every factual claim in tool results. Use query_database for numbers (admissions, wages, \
unemployment, outlooks, processing times) and search_documents for rules and qualitative context. \
Never invent statistics.
3. CITATIONS ARE MANDATORY: end every answer with a "**Sources:**" section listing the datasets \
and documents you used (they are named in tool outputs' `source` fields and passage headers).
4. When a comparison or trend would help, call create_visualization with the rows you queried.
5. If data is missing or a query returns nothing, say so honestly and suggest what you could \
answer instead. Do not extrapolate beyond the data's coverage period.
6. You provide statistical context, not legal advice. For case-specific immigration decisions, \
recommend a licensed immigration consultant (RCIC) or lawyer.
7. Be concise and concrete: lead with the answer, then the numbers behind it.

Style — write like a knowledgeable human, not a brochure:
- Plain prose first. Short bullet lists only when listing genuinely distinct items. NEVER use markdown tables (the interface cannot render them) and NEVER use emojis.
- No section headers for short answers. No "In summary" / "En résumé" closings — when the answer is done, stop.
- Minimal bold: at most one or two key figures, never bold every label.
- Avoid formula sentences: no "It's not just X, it's Y", no "Great news!", no "Il est important de noter que". State the fact directly.
- Vary sentence length. Two examples are fine; you don't need three of everything.

User profile (may be empty): {profile}"""

_LANG_NAMES = {"fr": "français", "en": "English"}


def _build_llm() -> ChatAnthropic:
    s = get_settings()
    return ChatAnthropic(
        model=s.anthropic_model,
        api_key=s.anthropic_api_key,
        max_tokens=s.max_tokens,
        temperature=0.2,
    )


def _get_chroma():
    try:
        from app.ingestion.rag_pipeline import get_chroma_collection

        return get_chroma_collection()
    except Exception as exc:  # chroma store absent in some deployments
        logger.warning("Chroma unavailable: %s", exc)
        return None


def _text_of(message: AIMessage) -> str:
    """Extract plain text from an AIMessage (str or Anthropic content blocks)."""
    content = message.content
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts)


def run_agent(
    message: str,
    session_id: str | None = None,
    language: str | None = None,
    profile: dict | None = None,
) -> dict[str, Any]:
    """Run one conversational turn. Returns answer + citations + visualizations."""
    sid, state = memory_store.get_or_create(session_id)
    if profile:
        memory_store.set_profile(sid, profile)
    lang = normalize_lang(language, fallback_text=message)

    tracker = CitationTracker()
    viz_sink: list[dict[str, Any]] = []
    tools = make_tools(tracker, viz_sink, chroma_collection=_get_chroma())
    tools_by_name = {t.name: t for t in tools}
    llm = _build_llm().bind_tools(tools)

    messages: list = [SystemMessage(SYSTEM_PROMPT.format(
        language_name=_LANG_NAMES[lang], profile=state.profile or {},
    ))]
    for m in state.messages:
        messages.append(HumanMessage(m["content"]) if m["role"] == "human"
                        else AIMessage(m["content"]))
    messages.append(HumanMessage(message))

    response = llm.invoke(messages)
    for _ in range(MAX_TOOL_ROUNDS):
        if not getattr(response, "tool_calls", None):
            break
        messages.append(response)
        for call in response.tool_calls:
            tool = tools_by_name.get(call["name"])
            if tool is None:
                output = f"Unknown tool: {call['name']}"
            else:
                try:
                    output = tool.invoke(call["args"])
                except Exception as exc:
                    logger.exception("Tool %s failed", call["name"])
                    output = f"Tool error: {exc}"
            messages.append(ToolMessage(content=str(output), tool_call_id=call["id"]))
        response = llm.invoke(messages)

    answer = ensure_citations(_text_of(response), tracker, lang=lang)

    memory_store.append(sid, "human", message)
    memory_store.append(sid, "ai", answer)

    return {
        "session_id": sid,
        "answer": answer,
        "language": lang,
        "citations": tracker.as_dicts(),
        "visualizations": viz_sink,
    }
