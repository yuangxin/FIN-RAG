import logging
from langchain_chroma import Chroma
from langchain_core.documents import Document
from core.embeddings import embedding_model
from config import CHROMA_DIR, VECTOR_STORE_BATCH_SIZE

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, persist_directory: str = str(CHROMA_DIR)):
        self.vectorstore = Chroma(
            collection_name="financial_docs",
            embedding_function=embedding_model,
            persist_directory=persist_directory,
        )

    def add_documents(self, chunks: list[dict], doc_id: str):
        docs = [
            Document(
                page_content=chunk["text"],
                metadata={
                    "doc_id": doc_id,
                    "company_name": chunk["metadata"].get("company_name", ""),
                    "year": chunk["metadata"].get("year", ""),
                    "quarter": chunk["metadata"].get("quarter", ""),
                    "page_no": chunk["metadata"].get("page_no", 0),
                    "section": chunk["metadata"].get("section", ""),
                    "chunk_type": chunk["metadata"].get("chunk_type", "text"),
                    "chunk_index": chunk["metadata"].get("chunk_index", 0),
                    "detected_terms": chunk["metadata"].get("detected_terms", ""),
                },
            )
            for chunk in chunks
        ]

        # Batch insertion to avoid memory spikes with large documents
        for i in range(0, len(docs), VECTOR_STORE_BATCH_SIZE):
            batch = docs[i:i + VECTOR_STORE_BATCH_SIZE]
            logger.info("Adding batch %d/%d (%d chunks)",
                        i // VECTOR_STORE_BATCH_SIZE + 1,
                        (len(docs) + VECTOR_STORE_BATCH_SIZE - 1) // VECTOR_STORE_BATCH_SIZE,
                        len(batch))
            self.vectorstore.add_documents(batch)

    def similarity_search(self, query: str, k: int = 10, filters: dict | None = None):
        chroma_filter = self._build_filter(filters)
        kwargs = {"k": k}
        if chroma_filter:
            kwargs["filter"] = chroma_filter
        return self.vectorstore.similarity_search(query, **kwargs)

    def similarity_search_with_score(self, query: str, k: int = 10, filters: dict | None = None):
        """Return documents with cosine distance scores (lower = more similar)."""
        chroma_filter = self._build_filter(filters)
        kwargs = {"k": k}
        if chroma_filter:
            kwargs["filter"] = chroma_filter
        return self.vectorstore.similarity_search_with_score(query, **kwargs)

    def delete_document(self, doc_id: str):
        self.vectorstore.delete(where={"doc_id": doc_id})

    def get_document_chunks(self, doc_id: str) -> list[Document]:
        results = self.vectorstore.get(where={"doc_id": doc_id})
        return results

    def _build_filter(self, filters: dict | None) -> dict | None:
        if not filters:
            return None
        conditions = []
        for key, value in filters.items():
            if value is not None and value != "":
                conditions.append({key: value})
        if len(conditions) > 1:
            return {"$and": conditions}
        elif len(conditions) == 1:
            return conditions[0]
        return None


vector_store = VectorStore()
