"""DocMind AI — RAGAS Evaluation Dashboard (Rebuilt)

Fully dynamic: admin uploads test PDFs, enters/generates questions,
runs dual-pass evaluation (RAG-Only + Full Pipeline), persists to DB.
"""

import os
import uuid

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

EVAL_BACKEND_URL = os.getenv("EVAL_BACKEND_URL", "http://localhost:8000")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
EVAL_PASS_THRESHOLD = float(os.getenv("EVAL_PASS_THRESHOLD", "0.70"))

API = f"{EVAL_BACKEND_URL}/api/v1"


# ─── Auth Helpers ────────────────────────────────────────────

def _get_token() -> str:
    """Get or refresh the eval bot access token."""
    # If we have a token, verify it's still valid
    if "api_token" in st.session_state and st.session_state.api_token:
        try:
            resp = requests.get(f"{API}/health", timeout=5)
            if resp.status_code == 200:
                return st.session_state.api_token
        except Exception:
            pass
        del st.session_state["api_token"]

    # Login or register the eval bot
    try:
        creds = {"email": "eval@docmind.ai", "password": "EvalPass@123!"}
        resp = requests.post(f"{API}/auth/login", json=creds, timeout=10)
        if resp.status_code == 401:
            requests.post(
                f"{API}/auth/register",
                json={**creds, "full_name": "Eval Bot"},
                timeout=10,
            )
            resp = requests.post(f"{API}/auth/login", json=creds, timeout=10)
        resp.raise_for_status()
        st.session_state.api_token = resp.json()["access_token"]
    except Exception as e:
        st.session_state.api_token = ""
        st.error(f"Failed to authenticate eval bot: {e}")
    return st.session_state.get("api_token", "")


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_get_token()}"}


def _admin_headers() -> dict:
    return {"X-Admin-Password": st.session_state.get("admin_pw", "")}


# ─── Page Config ─────────────────────────────────────────────

st.set_page_config(page_title="DocMind AI — RAGAS Evaluation", layout="wide")
st.title("📊 DocMind AI — RAGAS Evaluation Dashboard")
st.caption("RAG quality metrics: Faithfulness, Answer Relevancy, Context Utilization")

# ─── Admin Auth ──────────────────────────────────────────────

admin_pw = st.text_input("Admin Password", type="password", key="admin_pw_input")
if admin_pw:
    st.session_state["admin_pw"] = admin_pw

is_admin = (
    st.session_state.get("admin_pw", "") == ADMIN_PASSWORD
    and ADMIN_PASSWORD != ""
)

if not is_admin:
    if admin_pw:
        st.error("Invalid admin password")
    else:
        st.info("Enter the admin password to access evaluation tools.")
    st.stop()

st.success("Admin authenticated")
st.divider()

# ─── Section 1: Test Document Management ────────────────────

st.header("📄 Step 1: Upload Test Documents")
st.caption("Upload PDFs that the evaluation questions will be tested against.")

# Upload
uploaded_files = st.file_uploader(
    "Upload PDF files",
    type=["pdf"],
    accept_multiple_files=True,
    key="pdf_uploader",
)

if uploaded_files:
    for f in uploaded_files:
        with st.spinner(f"Uploading {f.name}..."):
            try:
                files = {"file": (f.name, f.getvalue(), "application/pdf")}
                resp = requests.post(
                    f"{API}/documents/upload",
                    files=files,
                    headers=_auth_headers(),
                    timeout=60,
                )
                if resp.status_code == 201:
                    st.success(f"✅ {f.name} uploaded ({resp.json()['document']['chunk_count']} chunks)")
                elif resp.status_code == 409:
                    st.warning(f"⚠️ Document limit reached. Delete existing documents first.")
                else:
                    st.error(f"❌ {f.name}: {resp.json().get('detail', resp.text)}")
            except Exception as e:
                st.error(f"❌ {f.name}: {e}")

# Show existing documents
try:
    resp = requests.get(f"{API}/documents", headers=_auth_headers(), timeout=10)
    if resp.status_code == 200:
        doc_data = resp.json()
        docs = doc_data.get("documents", [])
        if docs:
            st.write(f"**{len(docs)} document(s) uploaded** ({doc_data.get('document_limit', '?')} max)")
            for doc in docs:
                col1, col2, col3 = st.columns([4, 2, 1])
                col1.write(f"📄 {doc['filename']}")
                col2.write(f"{doc['chunk_count']} chunks • {doc.get('file_size_kb', '?')} KB")
                if col3.button("🗑️", key=f"del_doc_{doc['id']}", help="Delete document"):
                    resp = requests.delete(
                        f"{API}/documents/{doc['id']}",
                        headers=_auth_headers(),
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        st.rerun()
        else:
            st.warning("No documents uploaded yet. Upload PDFs above to begin.")
except Exception as e:
    st.error(f"Failed to load documents: {e}")

st.divider()

# ─── Section 2: Question Management ─────────────────────────

st.header("❓ Step 2: Add Test Questions")
st.caption("Enter questions manually or auto-generate from uploaded documents.")

# Initialize questions list in session state
if "eval_questions" not in st.session_state:
    st.session_state.eval_questions = []

col_manual, col_auto = st.columns(2)

with col_manual:
    st.subheader("Manual Input")
    manual_input = st.text_area(
        "Enter questions (one per line)",
        height=150,
        placeholder="How does RAG enhance LLMs?\nWhat is semantic search?\nExplain vector embeddings.",
    )
    if st.button("➕ Add Questions", key="add_manual"):
        new_qs = [q.strip() for q in manual_input.strip().split("\n") if q.strip()]
        if new_qs:
            st.session_state.eval_questions.extend(new_qs)
            st.success(f"Added {len(new_qs)} question(s)")
            st.rerun()

with col_auto:
    st.subheader("Auto-Generate")
    st.caption("Generates questions from your uploaded documents using AI.")
    if st.button("🤖 Auto-Generate Questions", key="auto_gen"):
        try:
            resp = requests.get(f"{API}/documents", headers=_auth_headers(), timeout=10)
            docs = resp.json().get("documents", [])
            if not docs:
                st.error("Upload documents first!")
            else:
                generated = []
                for doc in docs:
                    resp = requests.get(
                        f"{API}/documents/{doc['id']}/suggested-questions",
                        headers=_auth_headers(),
                        timeout=30,
                    )
                    if resp.status_code == 200:
                        for q in resp.json():
                            generated.append(q["question"])
                if generated:
                    st.session_state.eval_questions.extend(generated)
                    st.success(f"Generated {len(generated)} question(s) from {len(docs)} document(s)")
                    st.rerun()
                else:
                    st.warning("No questions could be generated.")
        except Exception as e:
            st.error(f"Auto-generation failed: {e}")

# Display current questions with remove buttons
if st.session_state.eval_questions:
    st.write(f"**{len(st.session_state.eval_questions)} question(s) ready:**")
    questions_to_keep = []
    for i, q in enumerate(st.session_state.eval_questions):
        col1, col2 = st.columns([9, 1])
        col1.write(f"{i + 1}. {q}")
        if not col2.button("✕", key=f"rm_q_{i}", help="Remove"):
            questions_to_keep.append(q)

    if len(questions_to_keep) != len(st.session_state.eval_questions):
        st.session_state.eval_questions = questions_to_keep
        st.rerun()

    if st.button("🗑️ Clear All Questions", key="clear_qs"):
        st.session_state.eval_questions = []
        st.rerun()
else:
    st.info("No questions added yet. Add questions above.")

st.divider()

# ─── Section 3: Run Evaluation ──────────────────────────────

st.header("🚀 Step 3: Run Evaluation")

questions = st.session_state.eval_questions

if not questions:
    st.warning("Add at least one question before running evaluation.")
    st.stop()

# Check documents exist
try:
    resp = requests.get(f"{API}/documents", headers=_auth_headers(), timeout=10)
    doc_count = len(resp.json().get("documents", []))
except Exception:
    doc_count = 0

if doc_count == 0:
    st.warning("Upload at least one document before running evaluation.")
    st.stop()

st.write(f"Ready to evaluate **{len(questions)} questions** against **{doc_count} documents**.")
st.caption("This runs two passes: RAG-Only (no web search) and Full Pipeline (with web search fallback).")

if st.button("▶️ Run Dual-Pass Evaluation", type="primary", key="run_eval"):
    run_id = str(uuid.uuid4())
    created_sessions = []

    # ─── Helper: run one pass ────────────────────────────
    def run_pass(pass_name: str, rag_only: bool) -> list[dict]:
        qa_pairs = []
        for i, question in enumerate(questions):
            st.text(f"  [{pass_name}] Question {i + 1}/{len(questions)}: {question[:60]}...")
            try:
                # Create session
                resp = requests.post(
                    f"{API}/chat/sessions",
                    json={"title": f"[Eval] {question[:30]}"},
                    headers=_auth_headers(),
                    timeout=10,
                )
                resp.raise_for_status()
                session_id = resp.json()["id"]
                created_sessions.append(session_id)

                # Send message
                url = f"{API}/chat/{session_id}/messages"
                if rag_only:
                    url += "?rag_only=true"
                resp = requests.post(
                    url,
                    json={"query": question},
                    headers=_auth_headers(),
                    timeout=60,
                )
                resp.raise_for_status()
                msg = resp.json()
                answer = msg.get("content", "")
                sources = msg.get("sources") or {}

                # Extract contexts
                contexts = []
                for ds in sources.get("document_sources", []):
                    preview = ds.get("chunk_preview", "")
                    if preview:
                        contexts.append(preview)
                for ws in sources.get("web_sources", []):
                    snippet = ws.get("snippet", "")
                    if snippet:
                        contexts.append(snippet)
                if not contexts:
                    contexts = ["No context available"]

                qa_pairs.append({
                    "question": question,
                    "answer": answer,
                    "contexts": contexts,
                })
            except Exception as e:
                st.warning(f"  Skipped: {question[:40]}... — {e}")
        return qa_pairs

    # ─── Execute both passes ─────────────────────────────
    with st.spinner("Running evaluation... This may take several minutes."):
        progress = st.empty()

        # Pass 1: RAG-Only
        progress.info("🔵 **Pass 1/2: RAG-Only** (web search disabled)")
        rag_only_pairs = run_pass("RAG-Only", rag_only=True)

        # Pass 2: Full Pipeline
        progress.info("🟠 **Pass 2/2: Full Pipeline** (web search enabled)")
        full_pairs = run_pass("Full Pipeline", rag_only=False)

        progress.info("⏳ Running RAGAS scoring...")

        # Score both passes
        rag_result = None
        full_result = None
        try:
            from ragas_runner import run_evaluation

            if rag_only_pairs:
                rag_result = run_evaluation(rag_only_pairs, eval_mode="rag_only")
                rag_result["run_id"] = run_id  # Same run_id for both passes
            if full_pairs:
                full_result = run_evaluation(full_pairs, eval_mode="full_pipeline")
                full_result["run_id"] = run_id
        except Exception as e:
            st.error(f"RAGAS scoring failed: {e}")

        # Persist to DB
        for res in [rag_result, full_result]:
            if res:
                try:
                    requests.post(
                        f"{API}/eval/results",
                        json={
                            "run_id": res["run_id"],
                            "eval_mode": res["eval_mode"],
                            "results": res["results"],
                        },
                        headers=_admin_headers(),
                        timeout=30,
                    )
                except Exception as e:
                    st.warning(f"Failed to persist {res['eval_mode']} results: {e}")

        # Cleanup sessions
        progress.info("🧹 Cleaning up eval sessions...")
        for sid in created_sessions:
            try:
                requests.delete(
                    f"{API}/chat/sessions/{sid}",
                    headers=_auth_headers(),
                    timeout=5,
                )
            except Exception:
                pass

        progress.success(f"✅ Evaluation complete! Run ID: {run_id[:8]}")

    # ─── Display Results ─────────────────────────────────
    if rag_result or full_result:
        st.subheader("Results")

        col_rag, col_full = st.columns(2)

        for col, result, label, color in [
            (col_rag, rag_result, "🔵 RAG-Only", "blue"),
            (col_full, full_result, "🟠 Full Pipeline", "orange"),
        ]:
            with col:
                st.markdown(f"### {label}")
                if result:
                    avgs = result["averages"]
                    for metric in ["faithfulness", "answer_relevancy", "context_precision"]:
                        score = avgs.get(metric, 0)
                        icon = "🟢" if score >= EVAL_PASS_THRESHOLD else "🔴"
                        st.metric(
                            metric.replace("_", " ").title(),
                            f"{icon} {score:.4f}",
                        )

                    st.caption("Per-question breakdown:")
                    for idx, r in enumerate(result["results"]):
                        with st.expander(f"Q: {r['question'][:50]}..."):
                            mcols = st.columns(3)
                            for mc, m in zip(mcols, ["faithfulness", "answer_relevancy", "context_precision"]):
                                s = r[m]
                                ic = "🟢" if s >= EVAL_PASS_THRESHOLD else "🔴"
                                mc.metric(m.replace("_", " ").title(), f"{ic} {s:.4f}")
                            st.text_area("Answer", r.get("answer", ""), height=100, disabled=True,
                                         key=f"ans_{result['eval_mode']}_{idx}")
                else:
                    st.warning("No results for this pass.")

st.divider()

# ─── Section 4: Historical Results ───────────────────────────

st.header("📈 Historical Results")

try:
    resp = requests.get(f"{API}/eval/runs", headers=_admin_headers(), timeout=10)
    if resp.status_code == 200:
        runs = resp.json()
        if runs:
            # Build DataFrame
            df = pd.DataFrame(runs)
            df["evaluated_at"] = pd.to_datetime(df["evaluated_at"])
            df["date"] = df["evaluated_at"].dt.strftime("%Y-%m-%d %H:%M")

            # Chart
            fig = px.bar(
                df,
                x="date",
                y=["avg_faithfulness", "avg_answer_relevancy", "avg_context_precision"],
                color="eval_mode",
                barmode="group",
                title="Evaluation Scores Over Time",
                labels={"value": "Score", "variable": "Metric"},
            )
            fig.add_hline(
                y=EVAL_PASS_THRESHOLD,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Pass Threshold ({EVAL_PASS_THRESHOLD})",
            )
            st.plotly_chart(fig, use_container_width=True)

            # Table
            display_df = df[["run_id", "eval_mode", "question_count", "avg_faithfulness",
                             "avg_answer_relevancy", "avg_context_precision", "passed_count", "date"]].copy()
            display_df["run_id"] = display_df["run_id"].str[:8]
            st.dataframe(
                display_df.style.map(
                    lambda v: f"color: {'green' if v >= EVAL_PASS_THRESHOLD else 'red'}" if isinstance(v, float) else "",
                    subset=["avg_faithfulness", "avg_answer_relevancy", "avg_context_precision"],
                ),
                use_container_width=True,
            )

            # Delete run buttons
            for run in runs:
                rid = run["run_id"]
                if st.button(f"🗑️ Delete run {rid[:8]} ({run['eval_mode']})", key=f"del_run_{rid}_{run['eval_mode']}"):
                    requests.delete(
                        f"{API}/eval/runs/{rid}",
                        headers=_admin_headers(),
                        timeout=10,
                    )
                    st.rerun()
        else:
            st.info("No evaluation runs yet. Run an evaluation above.")
    elif resp.status_code == 403:
        st.error("Invalid admin password for fetching history.")
except Exception as e:
    st.error(f"Failed to load history: {e}")

st.divider()

# ─── Section 5: Cleanup Tools ────────────────────────────────

st.header("🧹 Cleanup Tools")

col_clean1, col_clean2 = st.columns(2)

with col_clean1:
    if st.button("🗑️ Delete All Eval Sessions", key="cleanup_sessions"):
        try:
            resp = requests.delete(
                f"{API}/eval/sessions/cleanup",
                headers=_admin_headers(),
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                st.success(f"Deleted {data['sessions_deleted']} eval session(s)")
            else:
                st.error(resp.json().get("detail", "Cleanup failed"))
        except Exception as e:
            st.error(f"Cleanup failed: {e}")

with col_clean2:
    if st.button("🗑️ Delete All Eval Documents", key="cleanup_docs"):
        try:
            resp = requests.get(f"{API}/documents", headers=_auth_headers(), timeout=10)
            docs = resp.json().get("documents", [])
            deleted = 0
            for doc in docs:
                r = requests.delete(
                    f"{API}/documents/{doc['id']}",
                    headers=_auth_headers(),
                    timeout=10,
                )
                if r.status_code == 200:
                    deleted += 1
            st.success(f"Deleted {deleted} document(s)")
            st.rerun()
        except Exception as e:
            st.error(f"Cleanup failed: {e}")
