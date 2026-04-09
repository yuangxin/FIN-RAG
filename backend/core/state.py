from typing import TypedDict


class RAGState(TypedDict, total=False):
    question: str
    rewritten_question: str
    company_name: str | None
    company_names: list[str] | None
    year: str | None
    quarter: str | None
    documents: list
    answer: str
    citations: list[dict]
    retry_count: int
    workflow_steps: list[str]
    chart_data: dict | None
