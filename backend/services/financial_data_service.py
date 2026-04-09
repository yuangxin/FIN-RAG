import json
import re
from core.llm import llm
from core.vector_store import vector_store
from core.prompts import FINANCIAL_DATA_EXTRACTION_PROMPT
from services.document_service import get_document_info

# Cache extracted financial data per document
_financial_data_cache: dict[str, dict] = {}


def extract_financial_data(doc_id: str) -> dict:
    """Extract structured financial metrics from a document for charts."""
    if doc_id in _financial_data_cache:
        return _financial_data_cache[doc_id]

    doc_info = get_document_info(doc_id)
    if not doc_info:
        return {"error": "Document not found"}

    # Retrieve all chunks for this document
    results = vector_store.get_document_chunks(doc_id)
    if not results or not results.get("documents"):
        return {"error": "No chunks found for document"}

    # Focus on table chunks and financial statement sections
    docs_text = ""
    for doc_content, doc_meta in zip(results["documents"], results.get("metadatas", [])):
        if not doc_meta:
            continue
        section = doc_meta.get("section", "")
        chunk_type = doc_meta.get("chunk_type", "")

        # Prioritize financial statement tables
        if "item_8" in section or chunk_type == "table" or "item_7" in section:
            docs_text += f"\n--- ({section}, {chunk_type}) ---\n{doc_content}\n"

    if not docs_text.strip():
        # Fallback: use all available chunks
        for doc_content in results["documents"][:20]:
            docs_text += doc_content + "\n"

    prompt = FINANCIAL_DATA_EXTRACTION_PROMPT.format(documents=docs_text)
    response = llm.invoke(prompt)
    content = response.content.strip()

    # Parse JSON from response
    try:
        json_match = re.search(r"\{[\s\S]+\}", content)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = {"company_name": doc_info.get("company_name", ""), "data_points": []}
    except json.JSONDecodeError:
        data = {"company_name": doc_info.get("company_name", ""), "data_points": []}

    _financial_data_cache[doc_id] = data
    return data
