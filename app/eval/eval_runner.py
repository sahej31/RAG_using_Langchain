"""Offline evaluation of RAG pipelines.

Usage:
    python -m app.eval.eval_runner
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

from app.core.config import settings
from app.rag.pipelines import get_pipelines, PipelineId


@dataclass
class EvalResult:
    question: str
    reference: str
    pipeline_id: str
    answer: str
    lexical_overlap: float


def tokenize(text: str) -> List[str]:
    return [t.lower() for t in text.split() if t.strip()]


def lexical_overlap_score(pred: str, ref: str) -> float:
    """Simple Jaccard-like overlap between sets of tokens."""
    p_tokens = set(tokenize(pred))
    r_tokens = set(tokenize(ref))
    if not p_tokens or not r_tokens:
        return 0.0
    inter = len(p_tokens & r_tokens)
    union = len(p_tokens | r_tokens)
    return inter / union


def load_eval_questions() -> List[Dict[str, str]]:
    path = os.path.join(settings.eval_dir, "qa.jsonl")
    if not os.path.exists(path):
        raise RuntimeError(f"Eval file not found at {path}")
    items: List[Dict[str, str]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def main():
    pipelines = get_pipelines()
    questions = load_eval_questions()
    pipeline_ids: List[PipelineId] = ["bm25", "vector", "hybrid"]

    all_results: List[EvalResult] = []

    for pipeline_id in pipeline_ids:
        print(f"Evaluating pipeline: {pipeline_id}")
        scores: List[float] = []
        for i, qa in enumerate(questions, start=1):
            q = qa["question"]
            ref = qa["answer"]
            out = pipelines.answer(q, pipeline_id)
            pred = out["answer"]
            score = lexical_overlap_score(pred, ref)
            scores.append(score)
            result = EvalResult(
                question=q,
                reference=ref,
                pipeline_id=pipeline_id,
                answer=pred,
                lexical_overlap=score,
            )
            all_results.append(result)
            print(f"  [{i}/{len(questions)}] score={score:.3f}")

        if scores:
            avg = sum(scores) / len(scores)
            print(f"Average lexical overlap for {pipeline_id}: {avg:.3f}")
        print()

    os.makedirs(settings.eval_dir, exist_ok=True)
    results_path = os.path.join(settings.eval_dir, "results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in all_results], f, indent=2, ensure_ascii=False)

    print(f"Saved detailed results to: {results_path}")


if __name__ == "__main__":
    main()
