
"""Evaluate short AI answers against human-labeled references."""

import re
from typing import Any

ABSTAIN = "INSUFFICIENT_EVIDENCE"

#Fix the Case 03 scoring issue
#This is a small improvement,not a complete solution to detecting semantically equivalent answers. Later we need more robust evaluation methods.
ABSTENTION_PHRASES = [
    ABSTAIN,
    "I don't know",
    "I do not know",
    "Not specified",
    "The reference does not say",
]



def normalize(text: str) -> str:
    """Remove capitalization and punctuation differences."""
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold()))


def score_answer(answer: str, case: dict[str, Any]) -> dict[str, Any]:
    """Evaluate accuracy, abstention, and formatting separately."""

    actual = normalize(answer)
    strict_abstention = actual == normalize(ABSTAIN)

    semantic_abstention = actual in {
        normalize(phrase) for phrase in ABSTENTION_PHRASES
    }

    answerable = bool(case["answerable"])

    accepted = {
        normalize(value) for value in case["accepted_answers"]
    }

    if answerable:
        if semantic_abstention:
            outcome = "UNNECESSARY_ABSTENTION"
        elif actual in accepted:
            outcome = "CORRECT_ANSWER"
        else:
            outcome = "MISMATCH_REVIEW"

    else:
        if strict_abstention:
            outcome = "CORRECT_ABSTENTION"
        elif semantic_abstention:
            outcome = "ABSTENTION_FORMAT_VIOLATION"
        else:
            outcome = "UNSUPPORTED_RESPONSE"

    return {
        "outcome": outcome,
        "passed": outcome in {
            "CORRECT_ANSWER",
            "CORRECT_ABSTENTION",
        },
        "needs_review": outcome in {
            "MISMATCH_REVIEW",
            "UNSUPPORTED_RESPONSE",
        },
    }
