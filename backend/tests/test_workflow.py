"""Test LangGraph workflow compilation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_workflow_compiles():
    """Test that the LangGraph RAG pipeline compiles successfully."""
    from workflows.rag_pipeline import build_rag_pipeline

    pipeline = build_rag_pipeline()
    assert pipeline is not None

    # Check that all expected nodes exist
    graph = pipeline.get_graph()
    node_names = set(graph.nodes.keys())
    required = {"query_rewriter", "metadata_extractor", "retriever", "answer_generator", "increment_retry"}
    assert required.issubset(node_names), f"Missing nodes: {required - node_names}"
    print(f"Pipeline nodes: {node_names}")
