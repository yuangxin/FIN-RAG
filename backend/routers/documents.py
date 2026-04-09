import asyncio
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from config import DATA_DIR
from services.document_service import process_upload, list_documents, delete_document, get_document_info

router = APIRouter(prefix="/api/documents", tags=["documents"])

DATA_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF, parse it, and store in vector database."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Save file to data directory
    file_path = DATA_DIR / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        result = await asyncio.to_thread(process_upload, str(file_path), file.filename)
        if "error" in result:
            raise HTTPException(status_code=422, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_documents():
    """List all uploaded documents."""
    return list_documents()


@router.delete("/{doc_id}")
async def remove_document(doc_id: str):
    """Delete a document by ID."""
    success = delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted", "doc_id": doc_id}


@router.get("/{doc_id}")
async def get_document(doc_id: str):
    """Get document info by ID."""
    info = get_document_info(doc_id)
    if not info:
        raise HTTPException(status_code=404, detail="Document not found")
    return info
