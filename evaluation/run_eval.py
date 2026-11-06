"""Run the SupportPearlz evaluation harness.

Usage:
    python -m evaluation.run_eval
    python -m evaluation.run_eval --limit 5
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.chains.rag_chain import build_agent
from src.config import load_settings
from src.utils.logging_setup import setup_logging


def score_case(case: dict, answer: str, answered: bool, refusal: bool, sources: list[str]) -> dict:
    """Heuristic auto-score; manual review still expected for the report."""
    expected = case.get("expected_behaviour")
    key = (case.get("expected_key_fact") or "").lower()
    text = (answer or "").lower()
    source_blob = " ".join(sources).lower()
    gt = (case.get("ground_truth_source") or "").lower()

    correctness = 0.0
    groundedness = 0.0
    citation_accuracy = 0.0
    notes: list[str] = []

    if expected == "refuse":
        if refusal or not answered:
            correctness = 1.0
            groundedness = 1.0
            citation_accuracy = 1.0
        else:
            correctness = 0.0
            notes.append("Expected refusal but system answered")
            if key and key in text:
                notes.append("May have hallucinated adjacent content")
    elif expected in {"answer", "refuse_or_ground", "clarify_or_list"}:
        if key and key in text:
            correctness = 1.0
        elif key:
            correctness = 0.3 if answered else 0.0
            notes.append(f"Missing key fact: {key}")
        else:
            correctness = 0.5 if answered else 0.0

        if refusal and expected == "answer":
            correctness = min(correctness, 0.2)
            notes.append("Unexpected refusal on answerable question")

        if gt:
            citation_accuracy = 1.0 if any(gt in s.lower() or gt.split(".")[0] in s.lower() for s in sources) else 0.0
            if citation_accuracy == 0 and sources:
                notes.append("Citations present but ground-truth source not listed")
            elif not sources and expected == "answer":
                notes.append("No citations on answered question")
        else:
            citation_accuracy = 1.0 if not sources else 0.7

        # Groundedness proxy: answered with citations, or explicit partial language
        if answered and sources:
            groundedness = 0.9
        elif answered and ("documentation does not" in text or "not cover" in text):
            groundedness = 0.8
        elif refusal and expected != "answer":
            groundedness = 1.0
        else:
            groundedness = 0.4
            notes.append("Weak groundedness signal")
    else:
        notes.append(f"Unknown expected_behaviour: {expected}")

    verdict = "pass" if correctness >= 0.8 and groundedness >= 0.7 else (
        "partial" if correctness >= 0.4 else "fail"
    )
    fault_stage = None
    if verdict != "pass":
        if expected == "refuse" and answered:
            fault_stage = "prompt_or_gate"
        elif key and key not in text and not refusal:
            fault_stage = "retrieval_or_generation"
        elif citation_accuracy < 0.5:
            fault_stage = "citation"
        else:
            fault_stage = "unknown"

    return {
        "correctness": round(correctness, 2),
        "groundedness": round(groundedness, 2),
        "citation_accuracy": round(citation_accuracy, 2),
        "verdict": verdict,
        "fault_stage": fault_stage,
        "notes": notes,
        "source_blob": source_blob[:200],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--questions",
        type=Path,
        default=ROOT / "evaluation" / "test_questions.json",
    )
    args = parser.parse_args()

    settings = load_settings()
    setup_logging(settings.log_level, settings.log_file)
    settings.require_llm_credentials()

    cases = json.loads(args.questions.read_text(encoding="utf-8"))
    if args.limit:
        cases = cases[: args.limit]

    agent = build_agent(settings)
    results = []

    # Track conversation dependencies
    for case in cases:
        agent.reset_session()
        for setup_q in case.get("setup_questions") or []:
            agent.ask(setup_q)

        depends = case.get("depends_on")
        if depends:
            prior = next((c for c in cases if c["id"] == depends), None)
            if prior:
                agent.ask(prior["question"])

        response = agent.ask(case["question"])
        citations = [f"{c.source} ({c.location})" for c in response.citations]
        scored = score_case(
            case,
            response.answer,
            response.answered,
            response.refusal,
            citations,
        )
        results.append(
            {
                "id": case["id"],
                "category": case["category"],
                "question": case["question"],
                "expected_behaviour": case["expected_behaviour"],
                "answer": response.answer,
                "citations": citations,
                "confidence": response.confidence.value,
                "answered": response.answered,
                "refusal": response.refusal,
                "rewritten_query": response.rewritten_query,
                "flags": response.flags,
                **scored,
            }
        )
        print(
            f"{case['id']:6} {scored['verdict']:7} corr={scored['correctness']:.2f} "
            f"| {case['question'][:60]}"
        )

    # Aggregates
    n = len(results) or 1
    unans = [r for r in results if r["category"] == "unanswerable"]
    refusal_rate = (
        sum(1 for r in unans if r["refusal"] or not r["answered"]) / len(unans)
        if unans
        else None
    )
    # Hallucination proxy: unanswerable that answered with confident content
    hallucinations = sum(
        1
        for r in results
        if r["category"] in {"unanswerable", "adversarial"}
        and r["answered"]
        and not r["refusal"]
        and r["expected_behaviour"] == "refuse"
    )

    aggregate = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_cases": len(results),
        "mean_correctness": round(sum(r["correctness"] for r in results) / n, 3),
        "mean_groundedness": round(sum(r["groundedness"] for r in results) / n, 3),
        "mean_citation_accuracy": round(sum(r["citation_accuracy"] for r in results) / n, 3),
        "pass_rate": round(sum(1 for r in results if r["verdict"] == "pass") / n, 3),
        "refusal_rate_unanswerable": None if refusal_rate is None else round(refusal_rate, 3),
        "hallucination_count": hallucinations,
        "by_category": {},
    }
    categories = sorted({r["category"] for r in results})
    for cat in categories:
        subset = [r for r in results if r["category"] == cat]
        aggregate["by_category"][cat] = {
            "n": len(subset),
            "pass_rate": round(sum(1 for r in subset if r["verdict"] == "pass") / len(subset), 3),
        }

    out_dir = ROOT / "evaluation" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"eval_{stamp}.json"
    payload = {"aggregate": aggregate, "results": results}
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Readable table
    table_path = out_dir / f"eval_{stamp}.txt"
    lines = [
        "SupportPearlz Evaluation Results",
        f"Generated: {aggregate['timestamp']}",
        f"Cases: {aggregate['n_cases']}",
        f"Mean correctness: {aggregate['mean_correctness']}",
        f"Mean groundedness: {aggregate['mean_groundedness']}",
        f"Mean citation accuracy: {aggregate['mean_citation_accuracy']}",
        f"Pass rate: {aggregate['pass_rate']}",
        f"Refusal rate (unanswerable): {aggregate['refusal_rate_unanswerable']}",
        f"Hallucination count: {aggregate['hallucination_count']}",
        "",
        f"{'ID':6} {'Verdict':8} {'Corr':5} {'Ground':6} {'Cite':5} Category / Question",
        "-" * 100,
    ]
    for r in results:
        lines.append(
            f"{r['id']:6} {r['verdict']:8} {r['correctness']:<5} {r['groundedness']:<6} "
            f"{r['citation_accuracy']:<5} {r['category']} | {r['question'][:50]}"
        )
        if r.get("fault_stage"):
            lines.append(f"       fault_stage={r['fault_stage']} notes={r.get('notes')}")
    table_path.write_text("\n".join(lines), encoding="utf-8")

    print("\n" + "\n".join(lines[:12]))
    print(f"\nWrote {json_path}")
    print(f"Wrote {table_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
