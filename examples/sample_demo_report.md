# Evaluation Run

Mode: **demo**
Model: **simulated (no API)**

> This run uses simulated responses, NOT real model outputs. Do not cite these metrics as model performance.

| Prompt | Passed | Total | Pass rate | Review cases |
|---|---:|---:|---:|---:|
| baseline | 5 | 10 | 50.0% | 5 |
| evidence_first | 9 | 10 | 90.0% | 1 |

## Case details

| Case | Prompt | Output | Outcome |
|---|---|---|---|
| case-01 | baseline | 14 calendar days | CORRECT_ANSWER |
| case-02 | baseline | A receipt | CORRECT_ANSWER |
| case-03 | baseline | I don't know | UNSUPPORTED_RESPONSE |
| case-04 | baseline | 7 days | CORRECT_ANSWER |
| case-05 | baseline | 30 days | MISMATCH_REVIEW |
| case-06 | baseline | Eastern Time | CORRECT_ANSWER |
| case-07 | baseline | It depends on your plan | UNSUPPORTED_RESPONSE |
| case-08 | baseline | INSUFFICIENT_EVIDENCE | CORRECT_ABSTENTION |
| case-09 | baseline | I don't know | MISMATCH_REVIEW |
| case-10 | baseline | $299 | UNSUPPORTED_RESPONSE |
| case-01 | evidence_first | 14 calendar days | CORRECT_ANSWER |
| case-02 | evidence_first | A receipt | CORRECT_ANSWER |
| case-03 | evidence_first | INSUFFICIENT_EVIDENCE | CORRECT_ABSTENTION |
| case-04 | evidence_first | 7 days | CORRECT_ANSWER |
| case-05 | evidence_first | 14 calendar days | CORRECT_ANSWER |
| case-06 | evidence_first | Eastern Time | CORRECT_ANSWER |
| case-07 | evidence_first | INSUFFICIENT_EVIDENCE | CORRECT_ABSTENTION |
| case-08 | evidence_first | Not specified | UNSUPPORTED_RESPONSE |
| case-09 | evidence_first | At the end of the current billing period | CORRECT_ANSWER |
| case-10 | evidence_first | INSUFFICIENT_EVIDENCE | CORRECT_ABSTENTION |

## Evaluation limitations

- This is short-answer exact-match scoring, not verified general factuality detection.
- Any different-but-correct wording becomes MISMATCH_REVIEW and should be reviewed by a person.
- UNSUPPORTED_RESPONSE means the reference did not answer the question; it is only a proxy for unsupported claims.
- The reference excerpts and answer labels here are fictional, human-authored examples.
- Repeated real API runs, human review, and a larger held-out dataset are necessary for credible model conclusions.
