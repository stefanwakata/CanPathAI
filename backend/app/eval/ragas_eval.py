"""RAGAS evaluation: faithfulness, answer relevancy, context precision.

Runs the golden testset through the live agent, scores with RAGAS (using the
same Anthropic model as judge via langchain), writes results JSON consumed by
GET /stats and the frontend dashboard.

Usage: python -m app.eval.ragas_eval [--limit N]
"""
import argparse
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import get_settings
from app.eval.testset import TESTSET

logger = logging.getLogger(__name__)


def _collect_contexts(question: str, k: int = 4) -> list[str]:
    from app.ingestion.rag_pipeline import get_chroma_collection

    res = get_chroma_collection().query(query_texts=[question], n_results=k)
    return res.get("documents", [[]])[0] or [""]


def run_eval(limit: int | None = None) -> dict:
    from datasets import Dataset
    from langchain_anthropic import ChatAnthropic
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from ragas import evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import answer_relevancy, context_precision, faithfulness

    from app.agent.agent import run_agent

    items = TESTSET[:limit] if limit else TESTSET
    records = {"question": [], "answer": [], "contexts": [], "ground_truth": []}
    for item in items:
        logger.info("Evaluating: %s", item["question"])
        result = run_agent(item["question"], language=item.get("lang"))
        records["question"].append(item["question"])
        records["answer"].append(result["answer"])
        records["contexts"].append(_collect_contexts(item["question"]))
        records["ground_truth"].append(item["ground_truth"])

    settings = get_settings()
    judge = LangchainLLMWrapper(ChatAnthropic(
        model=settings.anthropic_model, api_key=settings.anthropic_api_key, max_tokens=1024,
    ))
    emb = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    )
    scores = evaluate(
        Dataset.from_dict(records),
        metrics=[faithfulness, answer_relevancy, context_precision],
        llm=judge, embeddings=emb,
    )
    metrics = {k: round(float(v), 4) for k, v in scores.items() if isinstance(v, (int, float))}

    payload = {
        "metrics": metrics,
        "n_questions": len(items),
        "evaluated_at": datetime.now(UTC).isoformat(),
        "model": settings.anthropic_model,
    }
    out = Path(settings.ragas_results_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("RAGAS results written to %s: %s", out, metrics)
    return payload


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    print(json.dumps(run_eval(args.limit), indent=2))
