
"""Interactive dashboard for AI Response Evaluation Lab.

Visualizes saved evaluation reports without making API calls.
Run with: python -m streamlit run dashboard.py
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


# -------------------------------------------------
# PAGE CONFIGURATION
# -------------------------------------------------

st.set_page_config(
    page_title="AI Response Evaluation Lab",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 AI Response Evaluation Lab")
st.caption(
    "LLM evaluation | Prompt comparison | "
    "Factual assessment | Instruction compliance"
)

st.divider()


# -------------------------------------------------
# LOAD REPORTS
# -------------------------------------------------

def load_report(path):
    """Load and validate a JSON evaluation report."""
    with open(path, encoding="utf-8") as file:
        report = json.load(file)

    validate_report(report)
    return report


def validate_report(report):
    """Check the basic structure of an evaluation report."""
    if not isinstance(report, dict):
        raise ValueError("Report must be a JSON object.")

    if not isinstance(report.get("metadata"), dict):
        raise ValueError("Missing report metadata.")

    if not isinstance(report.get("rows"), list):
        raise ValueError("Missing evaluation rows.")

    required = {
        "case_id",
        "prompt",
        "model_answer",
        "factual_status",
        "format_passed",
        "overall_passed",
    }

    for index, row in enumerate(report["rows"]):
        if not isinstance(row, dict):
            raise ValueError(f"Invalid row: {index}")

        missing = required - set(row)
        if missing:
            raise ValueError(
                f"Row {index} missing fields: {sorted(missing)}"
            )


st.sidebar.header("Evaluation Reports")

report_files = sorted(
    RESULTS.glob("*.json"),
    reverse=True,
) if RESULTS.exists() else []

source = st.sidebar.radio(
    "Report source",
    ["Local report", "Upload JSON"],
)

report = None

if source == "Local report":
    if report_files:
        chosen = st.sidebar.selectbox(
            "Select an evaluation run",
            report_files,
            format_func=lambda path: path.name,
        )

        try:
            report = load_report(chosen)
        except (OSError, ValueError, KeyError) as error:
            st.error(f"Unable to load report: {error}")
            st.stop()
    else:
        st.info(
            "No local reports found. Run an evaluation "
            "or upload a JSON report."
        )
        st.stop()

else:
    uploaded = st.sidebar.file_uploader(
        "Upload a saved evaluation report",
        type=["json"],
    )

    if uploaded is None:
        st.info("Upload a JSON report to begin.")
        st.stop()

    try:
        report = json.load(uploaded)
        validate_report(report)
    except (ValueError, KeyError, TypeError) as error:
        st.error(f"Invalid JSON report: {error}")
        st.stop()


# -------------------------------------------------
# REPORT METADATA
# -------------------------------------------------

metadata = report["metadata"]

mode = metadata.get("mode", "unknown")
original_mode = metadata.get("source_mode", mode)
model = metadata.get("model", "Unknown")

st.subheader("Experiment Overview")

col1, col2, col3 = st.columns(3)

col1.metric("Model", str(model))
col2.metric("Report mode", str(mode).upper())
col3.metric("Original mode", str(original_mode).upper())

if original_mode == "demo":
    st.warning(
        "SIMULATED DATA: These results are not "
        "measurements of actual model performance."
    )
elif mode == "rescore":
    st.info(
        "This report re-evaluates saved responses. "
        "No new model inference was performed. "
        "Scores may reflect updated answer labels."
    )
else:
    st.success("Report from an API evaluation run.")

st.caption(
    "Results describe the selected evaluation sample, "
    "not general model reliability."
)


# -------------------------------------------------
# PREPARE DATA
# -------------------------------------------------

df = pd.DataFrame(report["rows"])

if df.empty:
    st.warning("This report has no evaluation rows.")
    st.stop()

# Normalize boolean and numeric data for calculations.
for column in ["format_passed", "overall_passed"]:
    df[column] = df[column].map(
        lambda value: value is True
        or str(value).lower() == "true"
    )

for column in [
    "latency_seconds",
    "input_tokens",
    "output_tokens",
]:
    if column not in df:
        df[column] = None

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce",
    )

positive_statuses = {
    "VERIFIED_MATCH",
    "APPROPRIATE_ABSTENTION",
}

df["factual_passed"] = df["factual_status"].isin(
    positive_statuses
)

if "needs_review" not in df.columns:
    df["needs_review"] = False


# -------------------------------------------------
# SUMMARY METRICS
# -------------------------------------------------

st.divider()
st.subheader("Evaluation Summary")

total = len(df)

overall_rate = 100 * df["overall_passed"].mean()
factual_rate = 100 * df["factual_passed"].mean()
format_rate = 100 * df["format_passed"].mean()

m1, m2, m3, m4 = st.columns(4)

m1.metric("Responses evaluated", total)
m2.metric("Overall pass", f"{overall_rate:.1f}%")
m3.metric("Factual assessment", f"{factual_rate:.1f}%")
m4.metric("Format compliance", f"{format_rate:.1f}%")

st.caption(
    "Factual assessment is based on human-approved "
    "answers and heuristic abstention classification. "
    "It is not independent verification of arbitrary claims."
)


# -------------------------------------------------
# PROMPT COMPARISON
# -------------------------------------------------

st.divider()
st.subheader("Prompt Strategy Comparison")

comparison = (
    df.groupby("prompt")
    .agg(
        overall=("overall_passed", "mean"),
        factual=("factual_passed", "mean"),
        format=("format_passed", "mean"),
        responses=("case_id", "count"),
    )
    .reset_index()
)

for column in ["overall", "factual", "format"]:
    comparison[column] = (
        comparison[column] * 100
    ).round(1)

chart_data = comparison.set_index("prompt")[
    ["overall", "factual", "format"]
]

st.bar_chart(
    chart_data,
    y_label="Pass rate (%)",
)

st.dataframe(
    comparison.rename(
        columns={
            "prompt": "Prompt",
            "overall": "Overall %",
            "factual": "Factual %",
            "format": "Format %",
            "responses": "Responses",
        }
    ),
    hide_index=True,
    use_container_width=True,
)

st.caption(
    "Small differences may be caused by sample size, "
    "prompt variation, or evaluation limitations."
)


# -------------------------------------------------
# FAILURE CATEGORY ANALYSIS
# -------------------------------------------------

st.divider()
st.subheader("Response Classification")

status_counts = (
    df["factual_status"]
    .value_counts()
    .rename_axis("Status")
    .reset_index(name="Count")
)

st.bar_chart(
    status_counts.set_index("Status")["Count"]
)

st.dataframe(
    status_counts,
    hide_index=True,
    use_container_width=True,
)


# -------------------------------------------------
# RESPONSE EXPLORER
# -------------------------------------------------

st.divider()
st.subheader("Individual Response Explorer")

available_prompts = sorted(
    df["prompt"].dropna().unique().tolist()
)

selected_prompts = st.multiselect(
    "Filter by prompt",
    available_prompts,
    default=available_prompts,
)

available_statuses = sorted(
    df["factual_status"].dropna().unique().tolist()
)

selected_statuses = st.multiselect(
    "Filter by factual status",
    available_statuses,
    default=available_statuses,
)

filtered = df[
    df["prompt"].isin(selected_prompts)
    & df["factual_status"].isin(selected_statuses)
]

only_failures = st.checkbox(
    "Show only responses that did not pass"
)

if only_failures:
    filtered = filtered[
        ~filtered["overall_passed"]
    ]

visible_columns = [
    "case_id",
    "prompt",
    "model_answer",
    "factual_status",
    "format_passed",
    "overall_passed",
]

st.dataframe(
    filtered[visible_columns],
    hide_index=True,
    use_container_width=True,
)

st.caption(
    f"Showing {len(filtered)} of {len(df)} responses."
)

if not filtered.empty:
    st.markdown("#### Inspect a Response")

    choices = filtered.index.tolist()

    selected_index = st.selectbox(
        "Select a response",
        choices,
        format_func=lambda index: (
            f"{df.loc[index, 'case_id']} — "
            f"{df.loc[index, 'prompt']}"
        ),
    )

    selected = df.loc[selected_index]

    st.write("**Question:**")
    st.write(selected.get("question", ""))

    st.write("**Model response:**")
    st.code(
        str(selected["model_answer"]),
        language=None,
    )

    st.write("**Expected answer:**")
    st.write(selected.get("expected", ""))

    st.write("**Factual assessment:**")
    st.write(selected["factual_status"])

    st.write("**Format compliant:**")
    st.write(bool(selected["format_passed"]))

    st.write("**Overall passed:**")
    st.write(bool(selected["overall_passed"]))


# -------------------------------------------------
# LATENCY AND TOKEN USAGE
# -------------------------------------------------

st.divider()
st.subheader("API Usage and Performance")

latency = df["latency_seconds"].dropna()
input_tokens = df["input_tokens"].dropna()
output_tokens = df["output_tokens"].dropna()

p1, p2, p3 = st.columns(3)

p1.metric(
    "Average latency",
    f"{latency.mean():.2f} s"
    if not latency.empty else "N/A",
)

p2.metric(
    "Input tokens",
    f"{int(input_tokens.sum()):,}"
    if not input_tokens.empty else "N/A",
)

p3.metric(
    "Output tokens",
    f"{int(output_tokens.sum()):,}"
    if not output_tokens.empty else "N/A",
)

if not latency.empty:
    st.markdown("#### Latency by Prompt")

    latency_by_prompt = (
        df.groupby("prompt")["latency_seconds"]
        .mean()
        .dropna()
    )

    st.bar_chart(latency_by_prompt)

st.caption(
    "Saved usage and latency values are inherited "
    "from the original responses. Re-scoring does not "
    "generate additional API requests."
)


# -------------------------------------------------
# DOWNLOAD RESULTS
# -------------------------------------------------

st.divider()
st.subheader("Export Evaluation Data")

st.download_button(
    label="Download filtered responses (CSV)",
    data=filtered.to_csv(index=False),
    file_name="evaluation_filtered.csv",
    mime="text/csv",
)

st.download_button(
    label="Download full report (JSON)",
    data=json.dumps(report, indent=2),
    file_name="evaluation_report.json",
    mime="application/json",
)


# -------------------------------------------------
# FOOTER
# -------------------------------------------------

st.divider()

st.caption(
    "AI Response Evaluation Lab | "
    "Python, LLM APIs, automated testing, "
    "responsible AI evaluation, and CI/CD."
)
