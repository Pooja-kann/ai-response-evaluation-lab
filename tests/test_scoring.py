from eval_lab.scoring import normalize, score_answer

ANSWERABLE = {"answerable": True, "accepted_answers": ["14 days", "14 calendar days"]}
UNANSWERABLE = {"answerable": False, "accepted_answers": []}


def test_correct_short_answer():
    assert score_answer("14 days.", ANSWERABLE)["outcome"] == "CORRECT_ANSWER"


def test_correct_abstention():
    assert score_answer("INSUFFICIENT_EVIDENCE", UNANSWERABLE)["passed"]


def test_hallucination_proxy_flagged():
    assert score_answer("$99", UNANSWERABLE)["outcome"] == "UNSUPPORTED_RESPONSE"


def test_wrong_answer_flagged_for_review():
    assert score_answer("30 days", ANSWERABLE)["outcome"] == "MISMATCH_REVIEW"


def test_negation_not_marked_correct():
    assert not score_answer("Not 14 days", ANSWERABLE)["passed"]


def test_unnecessary_abstention():
    assert score_answer("INSUFFICIENT_EVIDENCE", ANSWERABLE)["outcome"] == "UNNECESSARY_ABSTENTION"


def test_normalize():
    assert normalize(" Eastern Time! ") == "eastern time"
#adding new test

def test_abstention_format_violation():
    result = score_answer("I don't know", UNANSWERABLE)

    assert result["outcome"] == "ABSTENTION_FORMAT_VIOLATION"
    assert result["passed"] is False


def test_unnecessary_natural_language_abstention():
    result = score_answer("I don't know", ANSWERABLE)

    assert result["outcome"] == "UNNECESSARY_ABSTENTION"

#Adding Reggresion Test

def test_expanded_abstention_phrase():
    result = score_answer("I do not know.", UNANSWERABLE)

    assert result["outcome"] == "ABSTENTION_FORMAT_VIOLATION"
    assert result["passed"] is False

# Case 02: Valid phrasing should pass
def test_receipt_requirement_correct():
    case = {
        "id": "case-02",
        "answerable": True,
        "accepted_answers": [
            "A receipt",
            "Receipt",
            "A receipt is required."
        ],
    }

    result = score_answer("A receipt is required.", case)

    assert result["outcome"] == "CORRECT_ANSWER"
    assert result["passed"] is True


# Case 02: Contradictory information must not pass
def test_receipt_requirement_incorrect():
    case = {
        "id": "case-02",
        "answerable": True,
        "accepted_answers": [
            "A receipt",
            "Receipt",
            "A receipt is required."
        ],
    }

    result = score_answer("A receipt is not required.", case)

    assert result["outcome"] == "MISMATCH_REVIEW"
    assert result["passed"] is False
