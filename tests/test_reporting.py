
"""Regression tests for evaluation reports and offline re-scoring."""

import csv
import json
import sys

import pytest

from eval_lab import run


# Sample evaluation records for testing
@pytest.fixture
def sample_rows():
    return [
        {
            "case_id": "case-01",
            "prompt": "baseline",
            "question": "What is the refund period?",
            "model_answer": "14 calendar days",
            "expected": "14 calendar days",
            "outcome": "CORRECT_ANSWER",
            "passed": True,
            "needs_review": False,
            "factual_status": "VERIFIED_MATCH",
            "format_passed": True,
            "overall_passed": True,
            "original_outcome": "CORRECT_ANSWER",
            "latency_seconds": 0.5,
            "input_tokens": 20,
            "output_tokens": 8,
        },
        {
            "case_id": "case-03",
            "prompt": "baseline",
            "question": "What is the CEO's favorite color?",
            "model_answer": "I do not know.",
            "expected": "INSUFFICIENT_EVIDENCE",
            "outcome": "ABSTENTION_FORMAT_VIOLATION",
            "passed": False,
            "needs_review": False,
            "factual_status": "APPROPRIATE_ABSTENTION",
            "format_passed": False,
            "overall_passed": False,
            "original_outcome": "ABSTENTION_FORMAT_VIOLATION",
            "latency_seconds": 0.6,
            "input_tokens": 22,
            "output_tokens": 6,
        },
    ]


@pytest.fixture
def report_metadata():
    return {
        "mode": "demo",
        "model": "simulated (no API)",
        "dataset_size": 2,
        "prompts": ["baseline", "evidence_first"],
    }


# Test 1: Verify overall and dimension-specific metrics
def test_metrics_calculation(sample_rows):
    result = run.metrics(sample_rows)

    assert result["total_cases"] == 2
    assert result["passed"] == 1
    assert result["pass_rate"] == 50.0
    assert result["factual_pass_rate"] == 100.0
    assert result["format_pass_rate"] == 50.0
    assert result["manual_review_count"] == 0


# Test 2: Verify CSV report columns and values
def test_csv_report(tmp_path, monkeypatch, sample_rows, report_metadata):
    monkeypatch.setattr(run, "OUTPUT", tmp_path)

    csv_file, _, _, _ = run.write_reports(
        sample_rows, report_metadata
    )

    assert csv_file.exists()

    with csv_file.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

        assert "factual_status" in reader.fieldnames
        assert "format_passed" in reader.fieldnames
        assert "overall_passed" in reader.fieldnames

    assert len(rows) == 2
    assert rows[0]["factual_status"] == "VERIFIED_MATCH"
    assert rows[1]["format_passed"] == "False"


# Test 3: Verify JSON report content
def test_json_report(tmp_path, monkeypatch, sample_rows, report_metadata):
    monkeypatch.setattr(run, "OUTPUT", tmp_path)

    _, _, json_file, _ = run.write_reports(
        sample_rows, report_metadata
    )

    report = json.loads(json_file.read_text(encoding="utf-8"))

    assert "metadata" in report
    assert "by_prompt" in report
    assert "rows" in report

    baseline = report["by_prompt"]["baseline"]

    assert baseline["factual_pass_rate"] == 100.0
    assert baseline["format_pass_rate"] == 50.0
    assert report["rows"][1]["overall_passed"] is False


# Test 4: Verify Markdown report includes both dimensions
def test_markdown_report(
    tmp_path, monkeypatch, sample_rows, report_metadata
):
    monkeypatch.setattr(run, "OUTPUT", tmp_path)

    _, md_file, _, _ = run.write_reports(
        sample_rows, report_metadata
    )

    content = md_file.read_text(encoding="utf-8")

    assert "Factual pass" in content
    assert "Format pass" in content
    assert "APPROPRIATE_ABSTENTION" in content
    assert "VERIFIED_MATCH" in content
    assert "50.0%" in content


# Test 5: Verify offline re-scoring preserves model responses
# and never requests a new model answer.
def test_rescore_without_api(tmp_path, monkeypatch):
    dataset = [
        {
            "id": "case-02",
            "question": "What is required to request a refund?",
            "reference": "A receipt is required.",
            "answerable": True,
            "accepted_answers": [
                "A receipt",
                "A receipt is required.",
            ],
        }
    ]

    dataset_file = tmp_path / "cases.json"
    dataset_file.write_text(
        json.dumps(dataset), encoding="utf-8"
    )

    saved_report = {
        "metadata": {
            "mode": "api",
            "model": "test-model",
            "dataset_size": 1,
            "prompts": ["baseline", "evidence_first"],
        },
        "rows": [
            {
                "case_id": "case-02",
                "prompt": "baseline",
                "question": dataset[0]["question"],
                "model_answer": "A receipt is required.",
                "expected": "A receipt",
                "outcome": "MISMATCH_REVIEW",
                "passed": False,
                "needs_review": True,
                "latency_seconds": 0.8,
                "input_tokens": 25,
                "output_tokens": 7,
            }
        ],
    }

    source = tmp_path / "original.json"
    source.write_text(
        json.dumps(saved_report), encoding="utf-8"
    )

    monkeypatch.setattr(run, "DATASET", dataset_file)
    monkeypatch.setattr(run, "OUTPUT", tmp_path / "reports")

    def api_must_not_be_called(*args, **kwargs):
        raise AssertionError("Unexpected paid API request!")

    monkeypatch.setattr(
        run, "real_model_answer", api_must_not_be_called
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "eval_lab.run",
            "--mode",
            "rescore",
            "--source",
            str(source),
        ],
    )

    run.main()

    output_files = list((tmp_path / "reports").glob("*.json"))

    assert len(output_files) == 1

    report = json.loads(
        output_files[0].read_text(encoding="utf-8")
    )

    result = report["rows"][0]

    assert result["model_answer"] == "A receipt is required."
    assert result["factual_status"] == "VERIFIED_MATCH"
    assert result["overall_passed"] is True
    assert result["input_tokens"] == 25
    assert result["output_tokens"] == 7
    assert report["metadata"]["source_mode"] == "api"
