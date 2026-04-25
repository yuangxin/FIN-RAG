from core.state import RAGState
from core.vector_store import vector_store
from config import TOP_K, HYBRID_ALPHA, HYBRID_CANDIDATE_MULTIPLIER

# Keywords that indicate financial statement data is needed
FINANCIAL_KEYWORDS = [
    "income statement", "balance sheet", "cash flow", "net income", "revenue",
    "profit", "margin", "eps", "earnings", "return on", "ratio", "debt",
    "equity", "assets", "liabilities", "operating income", "cost of sales",
    "capital", "roc", "roe", "roa", "roi", "ebitda", "gross margin",
    "operating margin", "net margin", "free cash flow", "per share",
]

# Keywords that indicate risk/MD&A sections are needed
RISK_KEYWORDS = [
    "risk factor", "risk", "uncertainty", "challenge", "threat",
    "competitive", "regulation", "regulatory", "litigation", "legal",
    "cybersecurity", "data breach", "privacy", "supply chain disruption",
    "geopolitical", "tariff", "trade war", "macroeconomic",
    "key risk", "material risk", "concentration",
]


def _normalize_scores(scores: list[float]) -> list[float]:
    """Min-Max normalize scores to [0, 1]."""
    if not scores:
        return []
    min_s, max_s = min(scores), max(scores)
    if max_s == min_s:
        return [1.0] * len(scores)
    return [(s - min_s) / (max_s - min_s) for s in scores]


def _hybrid_rerank(query: str, docs_with_scores: list[tuple], top_k: int) -> list:
    """Rerank docs using weighted fusion of vector scores and BM25 scores."""
    if not docs_with_scores:
        return []

    docs = [d for d, s in docs_with_scores]
    vector_scores = [s for d, s in docs_with_scores]

    # BM25 scoring - tokenize on word boundaries for better matching
    from rank_bm25 import BM25Okapi
    import re
    tokenized_corpus = [re.findall(r'\b\w+\b', doc.page_content.lower()) for doc in docs]
    tokenized_query = re.findall(r'\b\w+\b', query.lower())
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_scores = bm25.get_scores(tokenized_query).tolist()

    # Normalize: vector distance (lower=better) → convert to similarity (higher=better)
    norm_vector = _normalize_scores([-s for s in vector_scores])
    norm_bm25 = _normalize_scores(bm25_scores)

    # Weighted fusion
    fused = [
        (HYBRID_ALPHA * v + (1 - HYBRID_ALPHA) * b, doc)
        for doc, v, b in zip(docs, norm_vector, norm_bm25)
    ]
    fused.sort(key=lambda x: -x[0])

    return [doc for _, doc in fused[:top_k]]


def retriever(state: RAGState) -> dict:
    """Node 3: Retrieve documents using hybrid search (vector + BM25 reranking)."""
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

    # Fetch more candidates for BM25 reranking
    candidate_k = TOP_K * HYBRID_CANDIDATE_MULTIPLIER
    docs = []

    if company_names:
        per_company_k = max(candidate_k // len(company_names), 5)
        for company in company_names:
            company_filter = dict(filters)
            company_filter["company_name"] = company
            scored = vector_store.similarity_search_with_score(query, k=per_company_k, filters=company_filter)
            docs.extend(scored)
    elif single_company:
        filters["company_name"] = single_company
        scored = vector_store.similarity_search_with_score(query, k=candidate_k, filters=filters)
        docs = list(scored)
    else:
        scored = vector_store.similarity_search_with_score(query, k=candidate_k)
        docs = list(scored)

    # BM25 hybrid rerank
    docs = _hybrid_rerank(query, docs, TOP_K)

    # Supplemental search: financial keywords → item_8_financials
    combined_lower = (query + " " + original_question).lower()
    needs_financials = any(kw in combined_lower for kw in FINANCIAL_KEYWORDS)

    if needs_financials:
        companies_for_fin = company_names if company_names else ([single_company] if single_company else [])
        for company in companies_for_fin:
            section_filter = dict(filters)
            section_filter["company_name"] = company
            section_filter["section"] = "item_8_financials"
            fin_docs = vector_store.similarity_search(query, k=5, filters=section_filter)

            existing_pages = {doc.metadata.get("page_no") for doc in docs}
            for doc in fin_docs:
                if doc.metadata.get("page_no") not in existing_pages:
                    docs.append(doc)
                    existing_pages.add(doc.metadata.get("page_no"))

    # Supplemental search: risk keywords → item_1a_risk + item_7_mda
    needs_risk = any(kw in combined_lower for kw in RISK_KEYWORDS)

    if needs_risk:
        companies_for_risk = company_names if company_names else ([single_company] if single_company else [])
        for company in companies_for_risk:
            for section in ["item_1a_risk", "item_7_mda"]:
                section_filter = dict(filters)
                section_filter["company_name"] = company
                section_filter["section"] = section
                risk_scored = vector_store.similarity_search_with_score(query, k=8, filters=section_filter)
                risk_docs = _hybrid_rerank(query, risk_scored, 5)

                existing_pages = {doc.metadata.get("page_no") for doc in docs}
                for doc in risk_docs:
                    if doc.metadata.get("page_no") not in existing_pages:
                        docs.append(doc)
                        existing_pages.add(doc.metadata.get("page_no"))

    # Debug logging
    print(f"\n[RETRIEVER] Query: {query[:100]}")
    print(f"[RETRIEVER] Companies: {company_names or single_company or 'none'}")
    print(f"[RETRIEVER] Filters: {filters}")
    print(f"[RETRIEVER] Needs financials: {needs_financials} | Needs risk: {needs_risk}")
    print(f"[RETRIEVER] Hybrid reranked: {len(docs)} docs (alpha={HYBRID_ALPHA})")
    for i, doc in enumerate(docs[:3]):
        print(f"  Doc {i}: company={doc.metadata.get('company_name','')} section={doc.metadata.get('section','')} page={doc.metadata.get('page_no','')} type={doc.metadata.get('chunk_type','')} text={doc.page_content[:80]}...")

    steps = state.get("workflow_steps", [])
    steps.append("retriever")

    return {
        "documents": docs,
        "workflow_steps": steps,
    }
