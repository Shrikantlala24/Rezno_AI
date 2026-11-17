"""Verification tests for frontend migration and static assets."""

import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(REPO_ROOT, "frontend")


def test_frontend_directory_exists():
    """Ensure frontend/ directory exists."""
    assert os.path.isdir(FRONTEND_DIR), "frontend/ directory must exist"


def test_core_files_exist():
    """Ensure core relocated static files exist in frontend/."""
    expected_files = [
        "index.html",
        "css/tokens.css",
        "css/app.css",
        "js/app.js",
        "js/graph.js",
        "js/icons.js",
        "js/mock_data.js",
        "js/state.js",
        "assets/vendor/force-graph.min.js",
        "assets/favicon.ico",
    ]
    for rel_file in expected_files:
        file_path = os.path.join(FRONTEND_DIR, rel_file)
        assert os.path.isfile(file_path), f"File {rel_file} must exist in frontend/"


def test_index_html_references():
    """Ensure all local src and href attributes in frontend/index.html resolve to real files."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    assert os.path.isfile(index_path)

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    matches = re.findall(r'(?:src|href)="([^"#:]+)"', content)
    for ref in matches:
        if ref.startswith("http") or ref.startswith("//") or ref == "about:blank":
            continue
        target_path = os.path.join(FRONTEND_DIR, ref)
        assert os.path.isfile(target_path), (
            f"Reference '{ref}' in frontend/index.html does not exist on disk at {target_path}"
        )


def test_state_js_has_resilient_hybrid_mode():
    """Ensure state.js defines Resilient Hybrid Mode methods and statuses."""
    state_path = os.path.join(FRONTEND_DIR, "js", "state.js")
    assert os.path.isfile(state_path)

    with open(state_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "probeHealth" in content
    assert "checkBackendHealth" in content
    assert "submitQuery" in content
    assert "executeSearch" in content
    assert "● arXiv connected (Live API)" in content
    assert "● arXiv connected (Mock Mode)" in content
