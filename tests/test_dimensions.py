
from eval_lab.dimensions import evaluate_dimensions


def test_correct_factual_answer():
    case = {
        "answerable": True,
        "accepted_answers": ["14 calendar days"],
    }

    result = evaluate_dimensions("14 calendar days", case)

    assert result["factual_status"] == "VERIFIED_MATCH"
    assert result["format_passed"] is True
    assert result["overall_passed"] is True


def test_correct_fact_but_bad_abstention_format():
    case = {
        "answerable": False,
        "accepted_answers": [],
    }

    result = evaluate_dimensions("I do not know.", case)

    assert result["factual_status"] == "APPROPRIATE_ABSTENTION"
    assert result["format_passed"] is False
    assert result["overall_passed"] is False


def test_correct_abstention_format():
    case = {
        "answerable": False,
        "accepted_answers": [],
    }

    result = evaluate_dimensions(
        "INSUFFICIENT_EVIDENCE", case
    )

    assert result["factual_status"] == "APPROPRIATE_ABSTENTION"
    assert result["format_passed"] is True
    assert result["overall_passed"] is True


def test_wrong_factual_answer():
    case = {
        "answerable": True,
        "accepted_answers": ["14 calendar days"],
    }

    result = evaluate_dimensions("30 days", case)

    assert result["factual_status"] == "NEEDS_HUMAN_REVIEW"
    assert result["overall_passed"] is False
    assert result["needs_review"] is True


def test_correct_receipt_variation():
    case = {
        "answerable": True,
        "accepted_answers": [
            "A receipt",
            "Receipt",
            "A receipt is required.",
        ],
    }

    result = evaluate_dimensions(
        "A receipt is required.", case
    )

    assert result["factual_status"] == "VERIFIED_MATCH"
    assert result["overall_passed"] is True
