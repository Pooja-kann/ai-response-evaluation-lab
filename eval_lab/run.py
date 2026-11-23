"""Run a synthetic offline demonstration or a real OpenAI API evaluation.

Example:
    python -m eval_lab.run --mode demo
    python -m eval_lab.run --mode api --model gpt-5.4-mini
"""

import argparse
import csv
import json
import os
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .prompts import PROMPTS, question_input
from .scoring import ABSTAIN, score_answer

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "cases.json"
OUTPUT = ROOT / "results"


def offline_demo_answer(case: dict, prompt_version: str) -> str:
    """Fixed SIMULATED responses to exercise the evaluator. NOT model results."""
    idx = int(case["id"].split("-")[1])
    if prompt_version == "baseline":
        # Intentionally mix correct answers, ambiguity, and mistakes.
        if idx in {3, 9}:
            return "I don't know"
        if idx == 5:
            return "30 days"
        if idx == 7:
            return "It depends on your plan"
        if idx == 10:
            return "$299"
    else:
        if idx == 5:
            return "14 calendar days"  # accepted wording variant
        if idx == 8:
            return "Not specified"  # intentionally fails the strict abstention format
    return case["accepted_answers"][0] if case["answerable"] else ABSTAIN


def real_model_answer(client, case: dict, prompt_version: str, model: str):
    start = time.perf_counter()
    response = client.responses.create(
        model=model,
        instructions=PROMPTS[prompt_version],
        input=question_input(case),
        max_output_tokens=120,
        store=False,
    )
    latency = round(time.perf_counter() - start, 3)
    # Usage may be absent for some response types.
    usage = getattr(response, "usage", None)
    tokens_in = getattr(usage, "input_tokens", None)
    tokens_out = getattr(usage, "output_tokens", None)
    return (response.output_text or "").strip(), latency, tokens_in, tokens_out


def metrics(rows):
    counts = Counter(r["outcome"] for r in rows)
    total = len(rows)
    return {
        "total_cases": total,
        "passed": sum(r["passed"] for r in rows),
        "pass_rate": round(100 * sum(r["passed"] for r in rows) / total, 1) if total else 0,
        "outcomes": dict(counts),
        "manual_review_count": sum(r["needs_review"] for r in rows),
    }


def write_reports(rows, metadata):
    OUTPUT.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = f"{metadata['mode']}_{timestamp}"
    csv_file, md_file, json_file = (OUTPUT / f"{stem}.{e}" for e in ("csv", "md", "json"))
    fields = ["case_id", "prompt", "question", "model_answer", "expected", "outcome", "passed", "needs_review", "latency_seconds", "input_tokens", "output_tokens"]
    with csv_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    report = {"metadata": metadata, "by_prompt": {p: metrics([r for r in rows if r["prompt"] == p]) for p in PROMPTS}, "rows": rows}
    json_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = ["# Evaluation Run", "", f"Mode: **{metadata['mode']}**", f"Model: **{metadata['model']}**", ""]
    if metadata["mode"] == "demo":
        lines += ["> This run uses simulated responses, NOT real model outputs. Do not cite these metrics as model performance.", ""]
    lines += ["| Prompt | Passed | Total | Pass rate | Review cases |", "|---|---:|---:|---:|---:|"]
    for p, m in report["by_prompt"].items():
        lines.append(f"| {p} | {m['passed']} | {m['total_cases']} | {m['pass_rate']}% | {m['manual_review_count']} |")
    lines += ["", "## Case details", "", "| Case | Prompt | Output | Outcome |", "|---|---|---|---|"]
    for row in rows:
        value = row["model_answer"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {row['case_id']} | {row['prompt']} | {value} | {row['outcome']} |")
    lines += ["", "## Evaluation limitations", "", "- This is short-answer exact-match scoring, not verified general factuality detection.", "- Any different-but-correct wording becomes MISMATCH_REVIEW and should be reviewed by a person.", "- UNSUPPORTED_RESPONSE means the reference did not answer the question; it is only a proxy for unsupported claims.", "- The reference excerpts and answer labels here are fictional, human-authored examples.", "- Repeated real API runs, human review, and a larger held-out dataset are necessary for credible model conclusions."]
    md_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_file, md_file, json_file, report


def main():
    parser = argparse.ArgumentParser(description="Short-answer AI evaluation lab")
    parser.add_argument("--mode", choices=("demo", "api"), default="demo")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"))
    parser.add_argument("--limit", type=int, default=0, help="Optional number of cases; 0=all")
    args = parser.parse_args()
    cases = json.loads(DATASET.read_text(encoding="utf-8"))
    if args.limit < 0:
        parser.error("--limit must be >= 0")
    if args.limit:
        cases = cases[:args.limit]
    client = None
    if args.mode == "api":
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
        if not os.getenv("OPENAI_API_KEY"):
            parser.error("OPENAI_API_KEY missing. Create .env from .env.example and add your key.")
        from openai import OpenAI
        client = OpenAI()
    rows = []
    for prompt in PROMPTS:
        for case in cases:
            if args.mode == "demo":
                answer = offline_demo_answer(case, prompt)
                latency, input_tokens, output_tokens = None, None, None
            else:
                try:
                    answer, latency, input_tokens, output_tokens = real_model_answer(client, case, prompt, args.model)
                except Exception as e:
                    raise RuntimeError(f"API request failed for {case['id']}/{prompt}: {e}") from e
            grade = score_answer(answer, case)
            rows.append({
                "case_id": case["id"], "prompt": prompt, "question": case["question"],
                "model_answer": answer, "expected": case["accepted_answers"][0] if case["answerable"] else ABSTAIN,
                "latency_seconds": latency, "input_tokens": input_tokens,
                "output_tokens": output_tokens, **grade,
            })
    metadata = {"mode": args.mode, "model": args.model if args.mode == "api" else "simulated (no API)", "dataset_size": len(cases), "prompts": list(PROMPTS)}
    csv_file, md_file, json_file, report = write_reports(rows, metadata)
    for p, summary in report["by_prompt"].items():
        print(f"{p}: {summary['passed']}/{summary['total_cases']} passed ({summary['pass_rate']}%)")
    print(f"\nWrote:\n  {csv_file}\n  {md_file}\n  {json_file}")
    if args.mode == "demo":
        print("NOTE: SIMULATED OUTPUTS ONLY. These scores do not represent real model performance.")


if __name__ == "__main__":
    main()
