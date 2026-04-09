from core.state import RAGState
from core.vector_store import vector_store
from config import TOP_K

# Keywords that indicate financial statement data is needed
FINANCIAL_KEYWORDS = [
    "income statement", "balance sheet", "cash flow", "net income", "revenue",
    "profit", "margin", "eps", "earnings", "return on", "ratio", "debt",
    "equity", "assets", "liabilities", "operating income", "cost of sales",
    "capital", "roc", "roe", "roa", "roi", "ebitda", "gross margin",
    "operating margin", "net margin", "free cash flow", "per share",
]


def retriever(state: RAGState) -> dict:
    """Node 3: Retrieve Top-K documents from ChromaDB with metadata filtering."""
    query = state.get("rewritten_question", "") or state.get("question", "")
    original_question = state.get("question", "")

    # Build metadata filters
    filters = {}
    year = state.get("year")
    quarter = state.get("quarter")

    if year:
        filters["year"] = year
    if quarter:
        filters["quarter"] = quarter

    # If retrying, relax filters (drop quarter, then year)
    retry_count = state.get("retry_count", 0)
    if retry_count >= 1 and "quarter" in filters:
        del filters["quarter"]
    if retry_count >= 2 and "year" in filters:
        del filters["year"]

    # Handle multi-company queries
    company_names = state.get("company_names") or []
    single_company = state.get("company_name")

    docs = []

    if company_names:
        # Search each company separately and merge results
        per_company_k = max(TOP_K // len(company_names), 5)
        for company in company_names:
            company_filter = dict(filters)
            company_filter["company_name"] = company
            company_docs = vector_store.similarity_search(query, k=per_company_k, filters=company_filter)
            docs.extend(company_docs)
    elif single_company:
        filters["company_name"] = single_company
        docs = vector_store.similarity_search(query, k=TOP_K, filters=filters)
    else:
        docs = vector_store.similarity_search(query, k=TOP_K)

    # Supplemental search: if the query mentions financial metrics,
    # also retrieve from Item 8 (Financial Statements) directly
    combined_lower = (query + " " + original_question).lower()
    needs_financials = any(kw in combined_lower for kw in FINANCIAL_KEYWORDS)

    if needs_financials:
        companies_for_fin = company_names if company_names else ([single_company] if single_company else [])
        for company in companies_for_fin:
            section_filter = dict(filters)
            section_filter["company_name"] = company
            section_filter["section"] = "item_8_financials"
            fin_docs = vector_store.similarity_search(query, k=5, filters=section_filter)

            # Deduplicate by page number
            existing_pages = {doc.metadata.get("page_no") for doc in docs}
            for doc in fin_docs:
                if doc.metadata.get("page_no") not in existing_pages:
                    docs.append(doc)
                    existing_pages.add(doc.metadata.get("page_no"))

    # Debug logging
    print(f"\n[RETRIEVER] Query: {query[:100]}")
    print(f"[RETRIEVER] Companies: {company_names or single_company or 'none'}")
    print(f"[RETRIEVER] Filters: {filters}")
    print(f"[RETRIEVER] Needs financials: {needs_financials}")
    print(f"[RETRIEVER] Found {len(docs)} docs")
    for i, doc in enumerate(docs[:3]):
        print(f"  Doc {i}: company={doc.metadata.get('company_name','')} section={doc.metadata.get('section','')} page={doc.metadata.get('page_no','')} type={doc.metadata.get('chunk_type','')} text={doc.page_content[:80]}...")

    steps = state.get("workflow_steps", [])
    steps.append("retriever")

    return {
        "documents": docs,
        "workflow_steps": steps,
    }
