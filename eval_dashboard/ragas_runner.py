"""RAGAS metric computation logic."""

import os
import uuid

from ragas import evaluate, EvaluationDataset, SingleTurnSample
from ragas.metrics import Faithfulness, ResponseRelevancy
from ragas.metrics._context_precision import ContextUtilization
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def _get_ragas_llm():
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY)
    return LangchainLLMWrapper(llm)


def _get_ragas_embeddings():
    emb = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=GEMINI_API_KEY)
    return LangchainEmbeddingsWrapper(emb)


def run_evaluation(qa_pairs: list[dict]) -> dict:
    """Run RAGAS evaluation on a list of Q&A pairs.

    Each pair should have: question, answer, contexts (list of strings)

    Returns: { run_id, results: [...], averages: { faithfulness, answer_relevancy, context_utilization } }
    """
    run_id = str(uuid.uuid4())

    samples = []
    for p in qa_pairs:
        samples.append(SingleTurnSample(
            user_input=p["question"],
            response=p["answer"],
            retrieved_contexts=p["contexts"],
        ))

    dataset = EvaluationDataset(samples=samples)

    metrics = [Faithfulness(), ResponseRelevancy(), ContextUtilization()]

    evaluator_llm = _get_ragas_llm()
    evaluator_embeddings = _get_ragas_embeddings()

    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
    )

    df = result.to_pandas()

    results = []
    for _, row in df.iterrows():
        results.append({
            "run_id": run_id,
            "question": row.get("user_input", ""),
            "answer": row.get("response", ""),
            "faithfulness": float(row.get("faithfulness", 0)),
            "answer_relevancy": float(row.get("answer_relevancy", 0)),
            "context_precision": float(row.get("context_utilization", 0)),
        })

    averages = {
        "faithfulness": df["faithfulness"].mean() if "faithfulness" in df else 0,
        "answer_relevancy": df["answer_relevancy"].mean() if "answer_relevancy" in df else 0,
        "context_precision": df["context_utilization"].mean() if "context_utilization" in df else 0,
    }

    return {"run_id": run_id, "results": results, "averages": averages}
