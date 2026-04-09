import json
import re
from core.state import RAGState
from core.llm import llm
from core.prompts import METADATA_EXTRACTION_PROMPT
from config import COMPANY_ALIASES


def metadata_extractor(state: RAGState) -> dict:
    """Node 2: Extract company_names, year, quarter from the question."""
    question = state.get("question", "")
    prompt = METADATA_EXTRACTION_PROMPT.format(question=question)

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()

        # Try to parse JSON from response
        json_match = re.search(r"\{[^}]+\}", content)
        if json_match:
            metadata = json.loads(json_match.group())
        else:
            metadata = {}
    except (json.JSONDecodeError, Exception):
        metadata = {}

    # Support both new (company_names list) and old (company_name string) formats
    company_names = metadata.get("company_names", [])
    if not company_names:
        single = metadata.get("company_name", "")
        if single:
            company_names = [single]

    # Normalize company names through aliases
    company_names = [
        COMPANY_ALIASES.get(name.lower(), name.lower())
        for name in company_names
        if name
    ]

    year = metadata.get("year", "") or ""
    quarter = metadata.get("quarter", "") or ""

    # Keep backward compat: single company -> company_name field
    primary_company = company_names[0] if company_names else ""

    print(f"[METADATA_EXTRACTOR] companies={company_names}, year={year}, quarter={quarter}")

    steps = state.get("workflow_steps", [])
    steps.append("metadata_extractor")

    return {
        "company_name": primary_company or None,
        "company_names": company_names if company_names else None,
        "year": year or None,
        "quarter": quarter or None,
        "workflow_steps": steps,
    }
