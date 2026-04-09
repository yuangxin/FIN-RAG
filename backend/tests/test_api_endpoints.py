"""Test FastAPI endpoints."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_app_imports():
    """Test that FastAPI app can be imported."""
    from main import app
    assert app is not None
    assert app.title == "FinRAG"


def test_health_endpoint():
    """Test the health check endpoint."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_documents_list():
    """Test listing documents endpoint."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
