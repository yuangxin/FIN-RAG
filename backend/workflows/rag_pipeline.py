from langgraph.graph import StateGraph, END
from core.state import RAGState
from nodes.query_rewriter import query_rewriter
from nodes.metadata_extractor import metadata_extractor
from nodes.retriever import retriever
from nodes.answer_generator import answer_generator
from edges.route_after_retrieval import route_after_retrieval


def _increment_retry(state: RAGState) -> dict:
    """Helper to increment retry count on loop back."""
    return {"retry_count": state.get("retry_count", 0) + 1}


def build_rag_pipeline():
    """Build and compile the LangGraph RAG pipeline."""
    graph = StateGraph(RAGState)

    # Add nodes
    graph.add_node("query_rewriter", query_rewriter)
    graph.add_node("metadata_extractor", metadata_extractor)
    graph.add_node("retriever", retriever)
    graph.add_node("answer_generator", answer_generator)
    graph.add_node("increment_retry", _increment_retry)

    # Set entry point
    graph.set_entry_point("query_rewriter")

    # Add edges
    graph.add_edge("query_rewriter", "metadata_extractor")
    graph.add_edge("metadata_extractor", "retriever")
    graph.add_conditional_edges(
        "retriever",
        route_after_retrieval,
        {
            "answer_generator": "answer_generator",
            "query_rewriter": "increment_retry",
        },
    )
    graph.add_edge("increment_retry", "query_rewriter")
    graph.add_edge("answer_generator", END)

    return graph.compile()


# Compiled pipeline singleton
rag_pipeline = build_rag_pipeline()
