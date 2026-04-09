"""Test embedding model initialization and output."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_embedding_import():
    """Test that embedding model can be imported."""
    from core.embeddings import embedding_model
    assert embedding_model is not None


def test_embedding_dimension():
    """Test that embedding produces correct dimension."""
    from core.embeddings import embedding_model
    vec = embedding_model.embed_query("Apple 2023 revenue")
    assert len(vec) == 384, f"Expected 384 dimensions, got {len(vec)}"


def test_embedding_similarity():
    """Test that semantically similar texts have higher similarity."""
    from core.embeddings import embedding_model
    import numpy as np

    vec1 = embedding_model.embed_query("Apple revenue growth 2023")
    vec2 = embedding_model.embed_query("Apple net sales increased")
    vec3 = embedding_model.embed_query("The weather is nice today")

    sim_12 = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    sim_13 = np.dot(vec1, vec3) / (np.linalg.norm(vec1) * np.linalg.norm(vec3))

    assert sim_12 > sim_13, f"Related texts should be more similar: {sim_12:.3f} vs {sim_13:.3f}"
    print(f"Similar texts: {sim_12:.3f}, Unrelated: {sim_13:.3f}")
