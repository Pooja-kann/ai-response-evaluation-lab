# Roadmap: From starter project to interview-ready portfolio

## V1 — Completed starter

- [x] Hand-labeled synthetic short-answer dataset
- [x] Prompt comparison harness
- [x] Simulated offline workflow
- [x] Real OpenAI API adapter (needs your own key and live test)
- [x] Conservative deterministic scorer
- [x] Tests and local reporting

## V2 — Stronger evaluation

- [ ] Expand to 30–50 diverse, independently written cases
- [ ] Separate development and held-out test sets
- [ ] Introduce structured evidence citation IDs with deterministic validity checks
- [ ] Add a CSV interface for double-annotated human review
- [ ] Track model tokens and estimate costs from dated, versioned price tables
- [ ] Compare prompt settings across at least 3 independent model runs
- [ ] Add confidence intervals or bootstrap intervals with enough cases

## V3 — Engineering polish

- [ ] Run pytest in GitHub Actions CI
- [ ] Add a Streamlit dashboard for side-by-side failures
- [ ] Add sample screenshots to README
- [ ] Document failure analysis and implement a justified prompt fix
- [ ] Add more adversarial tests (prompt injection in reference text, ambiguity, irrelevant reference excerpts)

## Interview talking points

- The difference between deterministic tests and subjective LLM-as-a-judge
- Why answerable vs. unanswerable cases matter
- Why exact-match metrics alone are insufficient for factuality claims
- How prompt changes can improve one metric while hurting another
- Why dev-set / test-set separation and repeated runs matter
