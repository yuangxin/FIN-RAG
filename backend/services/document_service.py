import logging
import uuid
from pathlib import Path
from config import DATA_DIR, TERMINOLOGY_ENRICH_CHUNKS, MAX_DOCUMENTS
from core.document_parser import parse_pdf
from core.vector_store import vector_store
from core.terminology import terminology_dict

logger = logging.getLogger(__name__)

# In-memory document registry (persists across requests, lost on restart)
_document_registry: dict[str, dict] = {}


def _restore_registry():
    """Restore document registry from ChromaDB on startup."""
    try:
        results = vector_store.vectorstore.get(include=["metadatas"])
        doc_ids = set()
        for m in results.get("metadatas", []):
            doc_ids.add(m.get("doc_id", ""))

        for doc_id in doc_ids:
            if not doc_id:
                continue
            chunks_meta = [m for m in results["metadatas"] if m.get("doc_id") == doc_id]
            if not chunks_meta:
                continue
            first = chunks_meta[0]
            _document_registry[doc_id] = {
                "id": doc_id,
                "filename": f"{first.get('company_name', 'unknown')}-{first.get('year', 'unknown')}.pdf",
                "chunk_count": len(chunks_meta),
                "company_name": first.get("company_name", ""),
                "year": first.get("year", ""),
                "total_pages": max(m.get("page_no", 0) for m in chunks_meta) if chunks_meta else 0,
            }
        print(f"[REGISTRY] Restored {len(_document_registry)} documents from ChromaDB")
    except Exception as e:
        print(f"[REGISTRY] Failed to restore: {e}")


# Auto-restore on module load
_restore_registry()


def process_upload(file_path: str, filename: str) -> dict:
    """Process an uploaded PDF: parse, chunk, embed, store."""
    # Check document limit
    if len(_document_registry) >= MAX_DOCUMENTS:
        return {"error": f"Document limit reached (max {MAX_DOCUMENTS}). Delete some documents first."}

    # Check for duplicate filename - delete old version first
    for doc_id, info in list(_document_registry.items()):
        if info.get("filename") == filename:
            print(f"[UPLOAD] Replacing existing document: {filename}")
            delete_document(doc_id)
            break

    doc_id = str(uuid.uuid4())

    # Parse PDF into chunks
    logger.info("Processing upload: %s", filename)
    chunks, doc_metadata = parse_pdf(file_path, doc_id)
    doc_metadata["doc_id"] = doc_id
    doc_metadata["chunk_count"] = len(chunks)

    if not chunks:
        return {"error": "No content could be extracted from the PDF"}

    # Enrich chunks with terminology expansions
    if TERMINOLOGY_ENRICH_CHUNKS:
        for chunk in chunks:
            enriched_text, detected = terminology_dict.enrich_chunk_text(chunk["text"])
            chunk["text"] = enriched_text
            chunk["metadata"]["detected_terms"] = ",".join(detected)

    # Store in vector database
    logger.info("Storing %d chunks in vector database", len(chunks))
    vector_store.add_documents(chunks, doc_id)

    # Register document
    _document_registry[doc_id] = {
        "id": doc_id,
        "filename": filename,
        "chunk_count": len(chunks),
        "company_name": doc_metadata.get("company_name", ""),
        "year": doc_metadata.get("year", ""),
        "total_pages": doc_metadata.get("total_pages", 0),
    }

    return _document_registry[doc_id]


def list_documents() -> list[dict]:
    """List all registered documents."""
    return list(_document_registry.values())


def delete_document(doc_id: str) -> bool:
    """Delete a document from registry and vector store."""
    if doc_id not in _document_registry:
        return False

    info = _document_registry.pop(doc_id)
    vector_store.delete_document(doc_id)

    # Also remove the file from disk
    filename = info.get("filename", "")
    file_path = DATA_DIR / filename
    if file_path.exists():
        file_path.unlink()

    return True


def get_document_info(doc_id: str) -> dict | None:
    """Get document info by ID."""
    return _document_registry.get(doc_id)
