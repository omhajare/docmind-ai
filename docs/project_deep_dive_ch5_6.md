
# CHAPTER 5: THE COMPLETE DATA FLOW — A REQUEST'S JOURNEY

I am tracing the most complex action: a user submitting a Deep Research topic, through every layer, to downloading the DOCX report.

**Step 1: User types a topic in ResearchInput.tsx and clicks Submit**
- Zod validates topic length (1-300 chars) via `researchSchema`
- `researchApi.start(topic)` sends `POST /api/v1/research` with body `{ topic: "..." }`
- Data shape at this point: `{ topic: string }`

**Step 2: Request hits the research router (`research.py:19-34`)**
- `@limiter.limit(AI_LIMIT)` checks: has this IP made 10+ AI requests this minute? If yes, 429.
- `Depends(get_current_user)` extracts and verifies JWT from Authorization header.
- `research_service.start_job(user_id, topic)` is called.
- `background_tasks.add_task(research_service.run_research_agent, job_id, topic, user_id)` schedules the agent.
- Returns `202 Accepted` with `{ job_id, status: "queued" }`.

What could go wrong: Rate limit exceeded (429), expired JWT (401), or an active job already exists for this user (409 — `find_active_by_user()` prevents concurrent jobs).

**Step 3: Frontend starts polling (`ResearchPage.tsx:47`)**
- `setInterval(() => pollStatus(jobId), 3000)` — every 3 seconds
- `GET /api/v1/research/{job_id}/status` returns current job state
- `ProgressStepper.tsx` renders the current node with a spinning indicator and typewriter text

**Step 4: Background — Planner Node (`nodes/planner.py`)**
- Checks cancellation: `if job["status"] == "cancelled": return state`
- Updates DB status to "planning"
- Sends `PLANNER_PROMPT` with the topic to Gemini 2.5 Flash
- LLM returns 5 sub-questions (one per line)
- Updates state: `sub_questions = ["How does...", "What are...", ...]`
- Updates progress in DB: `{ current_step: "Breaking down topic...", steps_done: 1, total_steps: 6 }`

**Step 5: Background — Researcher Node (`nodes/researcher.py`)**
- For each of the 5 sub-questions (sequentially):
  - Calls `rag_search(user_id, question)` — embeds query, searches ChromaDB
  - Gets back `{ chunks, top_score, collection_empty }`
  - If `should_use_web_search(top_score, collection_empty)` — i.e., score < 0.65 or empty — calls `web_search(question)`
  - Formats document chunks as `"[filename.pdf p.N] chunk_text..."` and web results as `"[Web: title](url) snippet"`
  - Sends to Gemini with a research prompt, gets synthesized findings
  - Stores findings in `state["research_findings"][question] = "..."`
  - Collects `top_score` into `state["chunk_scores"]`
- Updates progress: `{ current_step: "Researching 'What are...' (3/5)", steps_done: 2 }`

**Step 6: Background — Reflector Node (`nodes/reflector.py`)**
- Sends ALL findings + original topic to Gemini with `REFLECTOR_PROMPT`
- Gemini responds with either "NO_GAPS" or a list of gaps
- If gaps: `state["reflection_gaps"] = ["Missing coverage of...", ...]`
- Increments `state["iteration_count"]`

**Step 7: Background — Conditional Edge (`graph.py:31-38`)**
```python
def _should_fill_gaps(state: AgentState) -> str:
    gaps = state.get("reflection_gaps", [])
    iteration = state.get("iteration_count", 0)
    max_iter = settings.MAX_REFLECTION_ITERATIONS  # 3
    if gaps and iteration < max_iter:
        return "gap_filler"
    return "synthesizer"
```
If there ARE gaps AND we have NOT looped 3 times → go to gap_filler → loops back to reflector.
If no gaps OR exhausted iterations → go to synthesizer.

**Step 8: Background — Gap Filler Node (if triggered)**
- For each gap: generates a targeted question via `GAP_FILLER_PROMPT`
- Runs `rag_search` + `web_search` for that question
- Stores findings under `"[Gap Fill] {question}"` key
- Returns to reflector (which may find more gaps or say NO_GAPS)

**Step 9: Background — Synthesizer Node (`nodes/synthesizer.py`)**
- Concatenates ALL findings (including gap-fill findings)
- Sends to Gemini with `SYNTHESIZER_PROMPT`
- Gets a multi-paragraph narrative with executive summary
- Stores in `state["final_synthesis"]`

**Step 10: Background — Writer Node (`nodes/writer.py`)**
- Computes confidence score:
  ```python
  avg_score = sum(chunk_scores) / len(chunk_scores) if chunk_scores else 0.0
  if web_used:
      avg_score -= settings.WEB_SEARCH_PENALTY  # 0.10
  # >= 0.70 = "high", >= 0.45 = "medium", else "low"
  ```
- Creates report directory: `backend/reports/{user_id}/`
- Calls `docx_writer.generate_report()` which creates a 7-section Word document:
  1. Title page with colored confidence badge
  2. Executive Summary (first 3 paragraphs)
  3. Research Sub-Questions list
  4. Findings per sub-question
  5. Coverage Gaps Analysis
  6. Full Synthesis
  7. References (extracted via regex from findings)
- Updates job in DB: `status="complete"`, `report_path`, `confidence`, `confidence_score`

**Step 11: Frontend detects completion**
- Next poll returns `status: "complete"` with `report_path` and confidence data
- `ProgressStepper` shows all steps with green checkmarks
- `ReportDownloadCard` appears with a download button

**Step 12: User clicks Download**
- `researchApi.download(jobId)` sends `GET /api/v1/research/{job_id}/download`
- Backend validates ownership, returns `FileResponse` with DOCX media type
- Frontend creates a blob URL and triggers browser download: `docmind_report_{job_id[:8]}.docx`

---

# CHAPTER 6: THE AI STACK — EXPLAINED FROM ZERO

## CONCEPT: Embeddings

**THE SIMPLE VERSION:**
Imagine every sentence is a point in a city. Similar sentences live in the same neighborhood. "The cat sat on the mat" lives near "A kitten was resting on a rug" — same neighborhood. But "Stock prices rose 5%" lives across town. An embedding is the GPS coordinate of a sentence.

**THE TECHNICAL VERSION:**
An embedding model converts text into a high-dimensional numeric vector (e.g., 768 numbers). Semantically similar texts produce vectors that point in similar directions. This enables mathematical comparison of meaning.

**HOW IT LIVES IN THIS CODE:**
`rag/indexer.py` uses `GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")` to embed chunks during indexing. `agent/tools.py` calls `get_embedding(query)` to embed user queries at search time. ChromaDB stores and indexes these vectors for fast nearest-neighbor search.

**INTERVIEW QUESTIONS:**
1. "What embedding model do you use and why?" — "Gemini embedding-001 because it comes from the same provider as our LLM, requiring only one API key. The embeddings are high-quality and the model is optimized for retrieval tasks."
2. "What dimensionality are your embeddings?" — "768 dimensions, determined by the Gemini embedding model. We don't control this."
3. "Could you use a different embedding model?" — "Yes, but we would need to re-embed all existing documents. Embeddings from different models are not compatible — you cannot search Model A's vectors with a Model B query embedding."

## CONCEPT: Vector Database (ChromaDB)

**THE SIMPLE VERSION:**
Imagine a library where books are not organized by genre or author, but by meaning. Books about "cooking Italian food" are physically next to books about "making pasta from scratch." A vector database is that library — it stores embeddings and lets you find the nearest neighbors to any query.

**THE TECHNICAL VERSION:**
ChromaDB stores vectors with associated metadata and documents. It uses HNSW (Hierarchical Navigable Small World) indexing for approximate nearest-neighbor search with cosine distance.

**HOW IT LIVES IN THIS CODE:**
`rag/retriever.py` creates per-user collections: `collection_name = f"user_{user_id}"` with `hnsw:space = "cosine"`. Search returns distances, which are converted to similarity scores: `score = max(0.0, 1.0 - distance)`. The project uses `PersistentClient` locally (data saved to `backend/.chroma/`) and `CloudClient` in production.

**INTERVIEW QUESTIONS:**
1. "Why per-user collections instead of one shared collection?" — "Data isolation. User A's search never touches User B's vectors. No metadata filtering needed, simpler deletion (drop the collection), and no risk of data leakage."
2. "What is HNSW?" — "Hierarchical Navigable Small World — a graph-based index that trades perfect recall for speed. It finds approximate nearest neighbors in O(log n) instead of O(n) brute force."

## CONCEPT: LangGraph Agentic Workflow

**THE SIMPLE VERSION:**
Think of it like a flowchart in a doctor's office. Step 1: take vitals. Step 2: see nurse. Step 3: see doctor. Step 4: doctor checks results — if something is wrong, go back to Step 2 for more tests. If everything is fine, go to Step 5: prescribe. That "go back" decision is a conditional edge. LangGraph builds these flowcharts for AI.

**THE TECHNICAL VERSION:**
LangGraph is a framework for building stateful, multi-step AI applications as directed graphs. Nodes are functions that transform a shared state dict. Edges define the flow, including conditional edges that route based on state values.

**HOW IT LIVES IN THIS CODE:**
`agent/graph.py` defines a `StateGraph(AgentState)` with 6 nodes. The `AgentState` TypedDict carries: `topic`, `sub_questions`, `research_findings`, `reflection_gaps`, `iteration_count`, `chunk_scores`, `web_used`, `final_synthesis`. The graph is compiled once at module load (`research_graph = graph.compile()`) and reused for every request.

**INTERVIEW QUESTIONS:**
1. "Why not just use a for loop?" — "A loop cannot express conditional branching cleanly. LangGraph's conditional edges make the reflect→gap-fill loop a first-class construct, not a nested if-statement buried in a function."
2. "How do you handle cancellation?" — "Every node checks `research_repository.find_by_id(job_id)` at entry. If status is 'cancelled', the node returns state unchanged and the graph completes without further processing."
3. "What prevents infinite loops?" — "The conditional edge `_should_fill_gaps` checks `iteration_count < MAX_REFLECTION_ITERATIONS (3)`. Even if the reflector always finds gaps, we cap at 3 iterations."

## CONCEPT: Prompt Engineering

**THE SIMPLE VERSION:**
When you ask someone a question, HOW you ask matters. "Tell me about dogs" gets a different answer than "As a veterinarian, explain the top 3 health concerns for golden retrievers over age 8, citing medical studies." Prompt engineering is crafting that question precisely.

**HOW IT LIVES IN THIS CODE:**
`agent/prompts.py` contains 6 named prompt constants. Every prompt uses XML-style tags (`<document_context>`, `<research_topic>`) to structure the input. The `QA_SYSTEM_PROMPT` has 7 explicit rules including "prioritize document context" and "cite filename and page number." The `REFLECTOR_PROMPT` has a specific sentinel response: "If no gaps exist, respond with exactly: NO_GAPS" — this makes parsing deterministic.

**CRITIQUE:** The prompts are good but could be better. They don't use few-shot examples (showing the LLM example input/output pairs), which would improve consistency. The reflector's "NO_GAPS" sentinel is brittle — if the LLM says "No gaps found" instead, the code would treat it as a gap description.

## CONCEPT: RAGAS Evaluation

**THE SIMPLE VERSION:**
Imagine grading a student's exam, but instead of a human teacher, you hire another AI to grade it. RAGAS is that AI grader. It checks three things: Did the student use their notes correctly? (faithfulness) Did they actually answer the question? (relevancy) Did they read the right pages? (context utilization)

**HOW IT LIVES IN THIS CODE:**
`eval_dashboard/ragas_runner.py` creates `SingleTurnSample` objects with `user_input`, `response`, and `retrieved_contexts`. RAGAS evaluates them using Gemini as the judge LLM. The dashboard runs a "dual-pass" test: Pass 1 with `rag_only=true` (pure RAG), Pass 2 with web search enabled. This isolates whether good answers come from documents or web fallback.

**INTERVIEW QUESTIONS:**
1. "How do you know your RAG system works?" — "We built a RAGAS evaluation pipeline that measures faithfulness, answer relevancy, and context utilization. We run dual-pass tests to isolate RAG quality from web-search quality."
2. "What is faithfulness?" — "Whether every factual claim in the generated answer can be traced back to the retrieved context. A faithfulness of 0.85 means 85% of claims are grounded."
3. "Why dual-pass?" — "A high score on full-pipeline might mask poor RAG quality if the web search is compensating. RAG-only mode shows the true retrieval quality."
