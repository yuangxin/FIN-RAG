from core.state import RAGState
from config import MAX_RETRIES


def route_after_retrieval(state: RAGState) -> str:
    """Conditional edge: decide whether to retry or generate answer."""
    documents = state.get("documents", [])
    retry_count = state.get("retry_count", 0)

    if len(documents) > 0:
        return "answer_generator"

    if retry_count < MAX_RETRIES:
        return "query_rewriter"

    return "answer_generator"
