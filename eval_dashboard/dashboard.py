"""DocMind AI — RAGAS Evaluation Dashboard"""

import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

EVAL_BACKEND_URL = os.getenv("EVAL_BACKEND_URL", "http://localhost:8000")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
EVAL_PASS_THRESHOLD = float(os.getenv("EVAL_PASS_THRESHOLD", "0.70"))


def _get_token():
    """Get a temporary access token for API calls."""
    if "api_token" not in st.session_state:
        try:
            resp = requests.post(
                f"{EVAL_BACKEND_URL}/api/v1/auth/login",
                json={"email": "eval@docmind.ai", "password": "EvalPass@123!"},
                timeout=10,
            )
            if resp.status_code == 401:
                requests.post(
                    f"{EVAL_BACKEND_URL}/api/v1/auth/register",
                    json={"email": "eval@docmind.ai", "password": "EvalPass@123!", "full_name": "Eval Bot"},
                    timeout=10,
                )
                resp = requests.post(
                    f"{EVAL_BACKEND_URL}/api/v1/auth/login",
                    json={"email": "eval@docmind.ai", "password": "EvalPass@123!"},
                    timeout=10,
                )
            st.session_state.api_token = resp.json()["access_token"]
        except Exception:
            st.session_state.api_token = ""
    return st.session_state.api_token


st.set_page_config(page_title="DocMind AI — RAGAS Evaluation", layout="wide")
st.title("📊 DocMind AI — RAGAS Evaluation Dashboard")
st.caption("RAG quality metrics: Faithfulness, Answer Relevancy, Context Precision")

# ─── Historical Results ──────────────────────────────────────
st.header("Historical Results")

try:
    # Fetch eval results from the backend database
    # For now, show from session state (stored after runs)
    if "eval_history" not in st.session_state:
        st.session_state.eval_history = []

    if st.session_state.eval_history:
        df = pd.DataFrame(st.session_state.eval_history)
        avg_df = df.groupby("run_id").agg({
            "faithfulness": "mean",
            "answer_relevancy": "mean",
            "context_precision": "mean",
        }).reset_index()
        avg_df.index = range(1, len(avg_df) + 1)
        avg_df.index.name = "Run"

        fig = px.line(avg_df, y=["faithfulness", "answer_relevancy", "context_precision"],
                      title="Average Metric Scores Across Runs",
                      labels={"value": "Score", "variable": "Metric"})
        fig.add_hline(y=EVAL_PASS_THRESHOLD, line_dash="dash", line_color="red",
                      annotation_text=f"Pass Threshold ({EVAL_PASS_THRESHOLD})")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(avg_df.style.applymap(
            lambda v: f"color: {'green' if v >= EVAL_PASS_THRESHOLD else 'red'}" if isinstance(v, float) else "",
            subset=["faithfulness", "answer_relevancy", "context_precision"]
        ))
    else:
        st.info("No evaluation runs yet. Enter the admin password below to run an evaluation.")
except Exception as e:
    st.error(f"Error loading history: {e}")

st.divider()

# ─── Admin Section ───────────────────────────────────────────
st.header("🔐 Admin — Run Evaluation")

admin_pw = st.text_input("Admin Password", type="password")
is_admin = admin_pw == ADMIN_PASSWORD and ADMIN_PASSWORD != ""

if not is_admin and admin_pw:
    st.error("Invalid admin password")

if is_admin:
    st.success("Admin authenticated")

    tab1, tab2 = st.tabs(["📋 Batch Evaluation", "🧪 Live Test"])

    with tab1:
        st.subheader("Run Batch Evaluation")
        st.caption("Tests against the hardcoded dataset of 10 Q&A pairs")

        if st.button("▶️ Run Evaluation", type="primary"):
            with st.spinner("Running RAGAS evaluation... This may take a few minutes."):
                try:
                    from test_dataset import TEST_DATASET
                    from ragas_runner import run_evaluation

                    # Get answers from the backend for each question
                    qa_pairs = []
                    for item in TEST_DATASET:
                        try:
                            # Use web search since we may not have docs
                            resp = requests.post(
                                f"{EVAL_BACKEND_URL}/api/v1/chat/sessions",
                                json={},
                                headers={"Authorization": f"Bearer {_get_token()}"},
                                timeout=10,
                            )
                            session_id = resp.json()["id"]

                            resp = requests.post(
                                f"{EVAL_BACKEND_URL}/api/v1/chat/{session_id}/messages",
                                json={"query": item["question"]},
                                headers={"Authorization": f"Bearer {_get_token()}"},
                                timeout=30,
                            )
                            msg = resp.json()
                            answer = msg.get("content", "")
                            sources = msg.get("sources", {})
                            contexts = []
                            for ds in sources.get("document_sources", []):
                                contexts.append(ds.get("chunk_preview", ""))
                            for ws in sources.get("web_sources", []):
                                contexts.append(ws.get("snippet", ""))
                            if not contexts:
                                contexts = ["No context available"]

                            qa_pairs.append({
                                "question": item["question"],
                                "answer": answer,
                                "contexts": contexts,
                            })
                        except Exception as e:
                            st.warning(f"Skipped: {item['question']} — {e}")

                    if qa_pairs:
                        result = run_evaluation(qa_pairs)
                        st.session_state.eval_history.extend(result["results"])

                        st.success(f"Evaluation complete! Run ID: {result['run_id'][:8]}")
                        st.json(result["averages"])

                        for r in result["results"]:
                            with st.expander(f"Q: {r['question'][:60]}..."):
                                cols = st.columns(3)
                                for col, metric in zip(cols, ["faithfulness", "answer_relevancy", "context_precision"]):
                                    score = r[metric]
                                    color = "🟢" if score >= EVAL_PASS_THRESHOLD else "🔴"
                                    col.metric(metric.replace("_", " ").title(), f"{color} {score:.2f}")
                    else:
                        st.error("No Q&A pairs could be evaluated")

                except Exception as e:
                    st.error(f"Evaluation failed: {e}")

    with tab2:
        st.subheader("Live Test")
        st.caption("Enter a question and see its RAGAS scores in real-time")

        question = st.text_input("Question", placeholder="e.g., What is machine learning?")
        if st.button("Test", disabled=not question):
            with st.spinner("Getting answer and computing metrics..."):
                try:
                    resp = requests.post(
                        f"{EVAL_BACKEND_URL}/api/v1/chat/sessions",
                        json={},
                        headers={"Authorization": f"Bearer {_get_token()}"},
                        timeout=10,
                    )
                    session_id = resp.json()["id"]

                    resp = requests.post(
                        f"{EVAL_BACKEND_URL}/api/v1/chat/{session_id}/messages",
                        json={"query": question},
                        headers={"Authorization": f"Bearer {_get_token()}"},
                        timeout=30,
                    )
                    msg = resp.json()
                    answer = msg.get("content", "")
                    sources = msg.get("sources", {})
                    contexts = []
                    for ds in sources.get("document_sources", []):
                        contexts.append(ds.get("chunk_preview", ""))
                    for ws in sources.get("web_sources", []):
                        contexts.append(ws.get("snippet", ""))
                    if not contexts:
                        contexts = ["No context available"]

                    st.text_area("Answer", answer, height=200)

                    from ragas_runner import run_evaluation
                    result = run_evaluation([{
                        "question": question,
                        "answer": answer,
                        "contexts": contexts,
                    }])

                    cols = st.columns(3)
                    for col, metric in zip(cols, ["faithfulness", "answer_relevancy", "context_precision"]):
                        score = result["results"][0][metric]
                        color = "🟢" if score >= EVAL_PASS_THRESHOLD else "🔴"
                        col.metric(metric.replace("_", " ").title(), f"{color} {score:.2f}")

                except Exception as e:
                    st.error(f"Test failed: {e}")
