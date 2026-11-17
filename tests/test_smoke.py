"""Basic smoke tests for Rezno AI testing infrastructure."""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def test_repository_structure_and_docs():
    """Verify testing infrastructure, repository structure, and documentation."""
    assert os.path.exists(REPO_ROOT)
    assert os.path.exists(os.path.join(REPO_ROOT, "DECISIONS.md"))
    assert os.path.exists(os.path.join(REPO_ROOT, "PROJECT.md"))
    assert os.path.exists(os.path.join(REPO_ROOT, "GEMINI.md"))
    assert os.path.exists(os.path.join(REPO_ROOT, "AGENTS.md"))
    assert os.path.exists(os.path.join(REPO_ROOT, "pyproject.toml"))
    assert os.path.exists(os.path.join(REPO_ROOT, "requirements.txt"))
    assert os.path.isdir(os.path.join(REPO_ROOT, "backend"))
    assert os.path.isdir(os.path.join(REPO_ROOT, "Version_1"))
    assert os.path.isdir(os.path.join(REPO_ROOT, "frontend"))
    assert os.path.isdir(os.path.join(REPO_ROOT, "tests"))
