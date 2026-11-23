
"""Evaluate factual evidence and instruction compliance separately."""

from typing import Any

from eval_lab.scoring import score_answer, normalize, ABSTAIN


def evaluate_dimensions(
    answer: str,
    case: dict[str, Any],
) -> dict[str, Any]:
    """Return independent evaluation dimensions."""

    original = score_answer(answer, case)
    outcome = original["outcome"]

    # An exact match to a human-approved reference answer
    # provides evidence of correctness for this dataset.
    if outcome == "CORRECT_ANSWER":
        factual_status = "VERIFIED_MATCH"

    elif outcome in {
        "CORRECT_ABSTENTION",
        "ABSTENTION_FORMAT_VIOLATION",
    }:
        factual_status = "APPROPRIATE_ABSTENTION"

    elif outcome == "UNNECESSARY_ABSTENTION":
        factual_status = "MISSED_ANSWER"

    elif outcome == "UNSUPPORTED_RESPONSE":
        factual_status = "UNSUPPORTED"

    else:
        factual_status = "NEEDS_HUMAN_REVIEW"

    # The output-format rule is strict for unanswerable
    # questions. Other short answers may use natural language.
    if not case["answerable"]:
        format_passed = (
            normalize(answer) == normalize(ABSTAIN)
        )
    else:
        format_passed = (
            outcome != "UNNECESSARY_ABSTENTION"
        )

    # An unresolved factual assessment cannot be an
    # automatic overall pass.
    factual_passed = factual_status in {
        "VERIFIED_MATCH",
        "APPROPRIATE_ABSTENTION",
    }

    overall_passed = factual_passed and format_passed

    return {
        "factual_status": factual_status,
        "format_passed": format_passed,
        "overall_passed": overall_passed,
        "needs_review": (
            factual_status == "NEEDS_HUMAN_REVIEW"
        ),
        "original_outcome": outcome,
    }
