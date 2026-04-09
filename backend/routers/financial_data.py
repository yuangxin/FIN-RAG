from fastapi import APIRouter, HTTPException
from services.financial_data_service import extract_financial_data
from services.document_service import get_document_info

router = APIRouter(prefix="/api/financial-data", tags=["financial-data"])


@router.get("/{doc_id}")
async def get_financial_data(doc_id: str):
    """Extract structured financial metrics for chart rendering."""
    doc_info = get_document_info(doc_id)
    if not doc_info:
        raise HTTPException(status_code=404, detail="Document not found")

    data = extract_financial_data(doc_id)
    if "error" in data:
        raise HTTPException(status_code=422, detail=data["error"])

    return data
