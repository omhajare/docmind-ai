"""LangGraph StateGraph definition for the Deep Research agent."""

from typing import TypedDict
from langgraph.graph import StateGraph, END

from config import get_settings
from agent.nodes.planner import planner_node
from agent.nodes.researcher import researcher_node
from agent.nodes.reflector import reflector_node
from agent.nodes.gap_filler import gap_filler_node
from agent.nodes.synthesizer import synthesizer_node
from agent.nodes.writer import writer_node

settings = get_settings()


class AgentState(TypedDict, total=False):
    user_id: str
    job_id: str
    topic: str
    sub_questions: list[str]
    research_findings: dict[str, str]
    reflection_gaps: list[str]
    iteration_count: int
    chunk_scores: list[float]
    web_used: bool
    final_synthesis: str
    report_path: str


def _should_fill_gaps(state: dict) -> str:
    """Conditional edge: go to gap_filler or synthesizer."""
    gaps = state.get("reflection_gaps", [])
    iteration = state.get("iteration_count", 0)

    if len(gaps) > 0 and iteration < settings.MAX_REFLECTION_ITERATIONS:
        return "gap_filler"
    return "synthesizer"


def build_research_graph() -> StateGraph:
    """Build and compile the research agent graph."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("reflector", reflector_node)
    graph.add_node("gap_filler", gap_filler_node)
    graph.add_node("synthesizer", synthesizer_node)
    graph.add_node("writer", writer_node)

    # Add edges
    graph.set_entry_point("planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "reflector")
    graph.add_conditional_edges("reflector", _should_fill_gaps, {
        "gap_filler": "gap_filler",
        "synthesizer": "synthesizer",
    })
    graph.add_edge("gap_filler", "reflector")
    graph.add_edge("synthesizer", "writer")
    graph.add_edge("writer", END)

    return graph.compile()


# Compile once at module level — reused across requests
research_graph = build_research_graph()
