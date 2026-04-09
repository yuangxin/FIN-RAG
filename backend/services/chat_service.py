from workflows.rag_pipeline import rag_pipeline


def ask_question(question: str) -> dict:
    """Run the RAG pipeline on a question and return the result."""
    initial_state = {
        "question": question,
        "retry_count": 0,
        "workflow_steps": [],
    }
    result = rag_pipeline.invoke(initial_state)

    return {
        "answer": result.get("answer", ""),
        "citations": result.get("citations", []),
        "chart_data": result.get("chart_data"),
        "workflow_steps": result.get("workflow_steps", []),
        "metadata": {
            "company_name": result.get("company_name"),
            "year": result.get("year"),
        },
    }
