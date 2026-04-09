"""Test ChromaDB vector store operations."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_vector_store_init():
    """Test that vector store can be initialized."""
    from core.vector_store import VectorStore
    vs = VectorStore(persist_directory="./test_chroma_db")
    assert vs is not None


def test_add_and_search():
    """Test adding documents and searching."""
    from core.vector_store import VectorStore
    vs = VectorStore(persist_directory="./test_chroma_db")

    chunks = [
        {
            "text": "Apple Inc. reported total net sales of $383.3 billion for fiscal year 2023.",
            "metadata": {
                "company_name": "apple",
                "year": "2023",
                "page_no": 42,
                "section": "item_8_financials",
                "chunk_type": "table",
                "chunk_index": 0,
            },
        },
    ]

    vs.add_documents(chunks, doc_id="test_doc_1")
    results = vs.similarity_search("Apple 2023 revenue", k=5)
    assert len(results) > 0, "Should find at least one result"
    assert "383.3" in results[0].page_content
    print(f"Found: {results[0].page_content[:80]}")


def test_metadata_filter():
    """Test metadata filtering in search."""
    from core.vector_store import VectorStore
    vs = VectorStore(persist_directory="./test_chroma_db")

    results = vs.similarity_search(
        "revenue", k=5,
        filters={"company_name": "apple", "year": "2023"}
    )
    assert len(results) > 0

    # Non-matching filter should return empty
    results_empty = vs.similarity_search(
        "revenue", k=5,
        filters={"company_name": "nonexistent_company_xyz"}
    )
    assert len(results_empty) == 0


def test_delete_document():
    """Test document deletion."""
    from core.vector_store import VectorStore
    vs = VectorStore(persist_directory="./test_chroma_db")
    vs.delete_document("test_doc_1")

    results = vs.similarity_search("Apple 2023 revenue", k=5)
    # After deletion, should not find the doc
    assert all(r.metadata.get("doc_id") != "test_doc_1" for r in results)
