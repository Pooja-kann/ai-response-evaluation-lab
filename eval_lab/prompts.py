"""Two prompt versions to compare on the same fixed evaluation dataset."""

PROMPTS = {
    "baseline": (
        "You are an assistant answering questions for a fictional company. "
        "Use the provided reference information. Reply briefly. "
        "If the reference does not contain the answer, say you do not know. "
        "For a question you can answer, reply with the answer only."
    ),
    "evidence_first": (
        "You answer questions using ONLY the supplied reference text. "
        "Do not invent policies or facts. If the answer is not explicitly in the "
        "reference, reply with exactly INSUFFICIENT_EVIDENCE and nothing else. "
        "Otherwise provide only the shortest factual answer (no introductory text)."
    ),
}


def question_input(case: dict) -> str:
    return f"Reference:\n{case['reference']}\n\nQuestion: {case['question']}"
