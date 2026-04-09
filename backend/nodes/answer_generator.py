import json
import re

from core.state import RAGState
from core.llm import llm
from core.prompts import ANSWER_GENERATION_PROMPT, CHART_DATA_EXTRACTION_PROMPT

# Non-streaming LLM for chart extraction (avoids streaming JSON tokens to frontend)
from langchain_openai import ChatOpenAI
from config import DEEPSEEK_API_KEY, LLM_MODEL, LLM_BASE_URL, LLM_TEMPERATURE
_chart_llm = ChatOpenAI(
    model=LLM_MODEL,
    api_key=DEEPSEEK_API_KEY,
    base_url=LLM_BASE_URL,
    temperature=LLM_TEMPERATURE,
    streaming=False,
)


def answer_generator(state: RAGState) -> dict:
    """Node 4: Generate answer with citations from retrieved documents."""
    question = state.get("question", "")
    documents = state.get("documents", [])

    # Format documents for the prompt
    docs_text = ""
    citations = []
    for i, doc in enumerate(documents):
        page_no = doc.metadata.get("page_no", "?")
        section = doc.metadata.get("section", "")
        chunk_type = doc.metadata.get("chunk_type", "text")

        docs_text += f"\n--- [Page {page_no}] ({section}, {chunk_type}) ---\n"
        docs_text += doc.page_content
        docs_text += "\n"

        citations.append({
            "page_no": page_no,
            "section": section,
            "chunk_type": chunk_type,
            "snippet": doc.page_content[:200],
        })

    prompt = ANSWER_GENERATION_PROMPT.format(question=question, documents=docs_text)
    response = llm.invoke(prompt)
    answer = response.content.strip()

    # Extract chart data if the question involves comparison
    chart_data = None
    try:
        chart_prompt = CHART_DATA_EXTRACTION_PROMPT.format(
            question=question, documents=docs_text
        )
        chart_response = _chart_llm.invoke(chart_prompt)
        chart_text = chart_response.content.strip()
        # Extract JSON (may be wrapped in markdown code block)
        json_match = re.search(r'\{[\s\S]*\}', chart_text)
        if json_match:
            parsed = json.loads(json_match.group())
            if parsed.get("need_chart") and parsed.get("data"):
                chart_data = {
                    "chart_type": parsed.get("chart_type", "bar"),
                    "title": parsed.get("title", ""),
                    "x_key": parsed.get("x_key", ""),
                    "data": parsed["data"],
                    "series": parsed.get("series", []),
                }
                print(f"[CHART] Generated {parsed['chart_type']} chart: {parsed.get('title', '')}")
            else:
                print("[CHART] No chart needed for this question")
    except Exception as e:
        print(f"[CHART] Failed to extract chart data: {e}")

    steps = state.get("workflow_steps", [])
    steps.append("answer_generator")

    return {
        "answer": answer,
        "citations": citations,
        "chart_data": chart_data,
        "workflow_steps": steps,
    }
