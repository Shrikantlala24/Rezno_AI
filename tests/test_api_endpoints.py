"""Unit and integration tests for Rezno AI FastAPI service layer."""

import glob
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Ensure virtualenv site-packages are accessible even when invoked via system python3
for site_pkg in glob.glob(os.path.join(REPO_ROOT, ".venv", "lib", "python*", "site-packages")):
    if os.path.exists(site_pkg) and site_pkg not in sys.path:
        sys.path.insert(0, site_pkg)

from backend.api.main import app


@pytest.fixture
def client():
    """TestClient fixture for FastAPI application."""
    return TestClient(app)


def test_health_check_endpoint(client):
    """Verify GET /api/health returns 200 and expected health metadata."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"
    assert data.get("service") == "rezno-ai"
    assert data.get("version") == "0.2.0"


def test_frontend_mount_or_fallback(client):
    """Verify root path (/) serves frontend index.html or fallback."""
    response = client.get("/")
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    if "text/html" in content_type:
        assert "<title>" in response.text.lower()
    else:
        assert response.json().get("service") == "rezno-ai"


@patch("backend.api.routes.citations._get_citations_fn")
def test_citations_endpoint_mock(mock_fn_getter, client):
    """Verify GET /api/citations/{arxiv_id} returns references and citations."""
    mock_citations_fn = MagicMock(return_value={
        "references": [
            {"arxiv_id": "1607.06450", "title": "Layer Normalization", "authors": ["Ba", "Hinton"], "year": "2016"}
        ],
        "citations": [
            {"arxiv_id": "2305.14314", "title": "QLoRA", "authors": ["Dettmers"], "year": "2023"}
        ],
    })
    mock_fn_getter.return_value = mock_citations_fn

    response = client.get("/api/citations/2106.09685")
    assert response.status_code == 200
    data = response.json()
    assert "references" in data
    assert "citations" in data
    assert len(data["references"]) == 1
    assert data["references"][0]["arxiv_id"] == "1607.06450"
    assert data["citations"][0]["title"] == "QLoRA"


@patch("backend.api.routes.citations._get_citations_fn")
def test_citations_endpoint_error_handling(mock_fn_getter, client):
    """Verify GET /api/citations handles exceptions gracefully without 500 error."""
    mock_citations_fn = MagicMock(side_effect=Exception("Semantic Scholar API timeout"))
    mock_fn_getter.return_value = mock_citations_fn

    response = client.get("/api/citations/9999.99999")
    assert response.status_code == 200
    data = response.json()
    assert data.get("references") == []
    assert data.get("citations") == []
    assert "error" in data


def test_bibtex_endpoint_dict_payload(client):
    """Verify POST /api/bibtex generates formatted BibTeX from dictionary payload."""
    sample_papers = [
        {
            "arxiv_id": "2106.09685",
            "title": "LoRA: Low-Rank Adaptation of Large Language Models",
            "authors": ["Edward J. Hu", "Yelong Shen"],
            "published": "2021-06-17",
            "pdf_url": "https://arxiv.org/pdf/2106.09685.pdf",
            "abs_url": "https://arxiv.org/abs/2106.09685",
        }
    ]
    response = client.post("/api/bibtex", json={"papers": sample_papers})
    assert response.status_code == 200
    data = response.json()
    assert "bibtex" in data
    assert data.get("count") == 1
    assert "@article{2106_09685" in data["bibtex"]
    assert "title = {LoRA: Low-Rank Adaptation of Large Language Models}" in data["bibtex"]
    assert "author = {Edward J. Hu and Yelong Shen}" in data["bibtex"]


def test_bibtex_endpoint_list_payload(client):
    """Verify POST /api/bibtex also accepts a bare list of papers."""
    sample_papers = [
        {
            "arxiv_id": "1706.03762",
            "title": "Attention Is All You Need",
            "authors": ["Ashish Vaswani", "Noam Shazeer"],
            "published": "2017-06-12",
        }
    ]
    response = client.post("/api/bibtex", json=sample_papers)
    assert response.status_code == 200
    data = response.json()
    assert "@article{1706_03762" in data["bibtex"]
    assert data.get("count") == 1


def test_bibtex_endpoint_minimal_fields(client):
    """Verify POST /api/bibtex handles papers with minimal/missing fields."""
    minimal_paper = [{"arxiv_id": "2401.00001", "title": "New Paper"}]
    response = client.post("/api/bibtex", json={"papers": minimal_paper})
    assert response.status_code == 200
    data = response.json()
    assert "@article{2401_00001" in data["bibtex"]
    assert "title = {New Paper}" in data["bibtex"]


def test_bibtex_endpoint_empty_payload(client):
    """Verify POST /api/bibtex handles empty lists safely."""
    response = client.post("/api/bibtex", json={"papers": []})
    assert response.status_code == 200
    data = response.json()
    assert data.get("bibtex") == ""
    assert data.get("count") == 0


@patch("backend.api.routes.search.execute_pipeline")
def test_search_endpoint(mock_exec, client):
    """Verify POST /api/search delegates to pipeline and returns results dict."""
    mock_exec.return_value = {
        "id": "run-test-01",
        "query": "sliding window attention",
        "queries": ["sliding window attention"],
        "candidate_count": 5,
        "papers": [
            {
                "arxiv_id": "2004.05150",
                "title": "Longformer: The Long-Document Transformer",
                "authors": ["Iz Beltagy", "Matthew E. Peters"],
                "author_line": "Iz Beltagy, Matthew E. Peters",
                "summary": "Longformer is a transformer model for long documents.",
                "relevance_score": 0.89,
            }
        ],
        "insights": [],
        "graph": {"nodes": [], "edges": []},
        "synthesis": {
            "summary": "Longformer introduces local attention window.",
            "citations": ["2004.05150"],
            "claims": [],
        },
        "search_status": "success",
        "search_error": None,
        "timestamp": "17 Nov 2026 12:00",
    }

    payload = {
        "query": "sliding window attention",
        "top_k": 5,
        "per_query": 10,
        "num_queries": 2,
    }
    response = client.post("/api/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data.get("query") == "sliding window attention"
    assert len(data.get("papers", [])) == 1
    assert data["papers"][0]["arxiv_id"] == "2004.05150"
    mock_exec.assert_called_once_with(
        query="sliding window attention",
        top_k=5,
        per_query=10,
        num_queries=2,
        response_length="standard",
    )


def test_search_endpoint_validation_error(client):
    """Verify POST /api/search requires query field."""
    response = client.post("/api/search", json={})
    assert response.status_code == 422


@patch("backend.api.routes.search.execute_pipeline")
def test_synthesize_sse_endpoint(mock_exec, client):
    """Verify GET /api/synthesize streams SSE events ending with complete."""
    mock_exec.return_value = {
        "id": "run-sse-01",
        "query": "sparse attention",
        "queries": ["sparse attention"],
        "candidate_count": 1,
        "papers": [],
        "insights": [],
        "graph": {"nodes": [], "edges": []},
        "synthesis": {
            "summary": "Streaming synthesis complete.",
            "citations": [],
            "claims": [],
        },
        "search_status": "success",
        "search_error": None,
        "timestamp": "17 Nov 2026 12:00",
    }

    response = client.get("/api/synthesize?query=sparse+attention&top_k=5")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    assert "event: progress" in response.text
    assert "event: complete" in response.text
    assert "Streaming synthesis complete." in response.text


def test_synthesize_missing_query_parameter(client):
    """Verify GET /api/synthesize without query param returns 422."""
    response = client.get("/api/synthesize")
    assert response.status_code == 422
