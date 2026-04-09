from core.state import RAGState
from core.llm import llm
from core.prompts import QUERY_REWRITE_PROMPT
from core.terminology import terminology_dict
from config import TERMINOLOGY_EXPAND_QUERIES


def query_rewriter(state: RAGState) -> dict:
    """Node 1: Rewrite the user's question for better retrieval."""
    question = state.get("question", "")

    # Dictionary-based term expansion before LLM (fast, deterministic)
    if TERMINOLOGY_EXPAND_QUERIES:
        expanded = terminology_dict.expand_query(question)
    else:
        expanded = question

    prompt = QUERY_REWRITE_PROMPT.format(question=expanded)
    response = llm.invoke(prompt)
    rewritten = response.content.strip()

    print(f"\n[QUERY_REWRITER] Original: {question}")
    print(f"[QUERY_REWRITER] Rewritten: {rewritten}")

    steps = state.get("workflow_steps", [])
    steps.append("query_rewriter")

    return {
        "rewritten_question": rewritten,
        "workflow_steps": steps,
    }
