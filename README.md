# AI Response Evaluation Lab

A small, reproducible Python project demonstrating **evaluation-driven AI development**. It measures how well short answers follow a fictional reference document, compares two prompt versions, and flags ambiguous or unsupported responses for manual review.


## Interactive Evaluation Dashboard

The Streamlit dashboard visualizes LLM evaluation results,
compares prompt strategies, and separates factual assessment
from instruction-format compliance.

![AI Response Evaluation Dashboard](docs/images/dashboard-overview.png)

### Key Features

- Compare baseline and evidence-first prompt strategies.
- Evaluate factual correctness against human-approved answers.
- Identify abstention and instruction-format violations.
- Analyze response latency and token consumption.
- Re-score previously saved responses without additional API calls.
- Export evaluation results in CSV and JSON formats.

## Features

- Offline `demo` mode with **simulated responses** (never presented as real LLM results).
- Live OpenAI Responses API integration with API key set locally.
- Ten synthetic, human-labeled test cases, including unanswerable questions.
- Two prompt strategies: `baseline` and `evidence_first`.
- Deterministic short-answer matching and explicit review flags.
- CSV, JSON, and Markdown summary reports.
- Seven automated `pytest` tests.

## Architecture

```text
Reference snippets + question + accepted answers
                     |
                     v
          Prompt strategy selector
                     |
           demo / Responses API
                     |
                     v
           Deterministic grader
                     |
                     v
          CSV + JSON + Markdown
                     |
                     v
               Human review
```

## Install on Windows (PowerShell)

Requires Python 3.10+.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python -m eval_lab.run --mode demo
```

If PowerShell blocks activation, run commands with `\.venv\Scripts\python.exe` without activating:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m eval_lab.run --mode demo
```

The demo is offline, free, and deterministic. Its metrics reflect **only simulated answers**, not any actual AI model.

## Run with an actual model

1. Make an API key at the [OpenAI developer platform](https://platform.openai.com/api-keys) and configure billing/usage limits as appropriate. API usage is billed separately from ChatGPT subscriptions.
2. Copy `.env.example` to `.env` in the project directory.
3. Edit `.env` and replace `your_api_key_here` with your key. **Never commit or share `.env`.**
4. Run:

```powershell
python -m eval_lab.run --mode api --model gpt-5.4-mini --limit 3
```

After verifying the first three examples, rerun without `--limit` to evaluate the whole dataset. Each full run creates two prompt conditions × ten cases = **20 API requests**. Costs and model access depend on your account and model choice.

## Results

The program creates files in `results/`: a detailed CSV, a machine-readable JSON report, and a Markdown summary. Demo outputs and API results should never be mixed in a report or represented as equivalent.

## Scoring caveats

- This evaluator does **normalized exact-match** on short answers, not comprehensive factuality checking.
- Correct paraphrases outside `accepted_answers` are marked `MISMATCH_REVIEW` until humans verify them.
- For questions without an answer in the reference, a response other than `INSUFFICIENT_EVIDENCE` is `UNSUPPORTED_RESPONSE`; this is only an *unsupported-response proxy*, not proof of a specific hallucination.
- The model may generate a long answer containing both a correct phrase and an incorrect claim. This grader does **not** certify such answers as factual.
- Prompt tests should eventually use a larger, held-out, human-reviewed evaluation dataset and multiple independent runs.
- The built-in dataset is fictional and does not contain real company or client data.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for enhancements including human-labeled free-form evaluation, citation matching, token-cost comparisons, regression checks, and CI.

## Technology

Python, JSON, OpenAI Responses API (optional), pytest, CSV reporting.

## Academic and privacy integrity

An original standalone portfolio exercise. No restricted course submissions, client secrets, API tokens, or personal information should be published.
