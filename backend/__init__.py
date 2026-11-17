import os
import sys

# Ensure .venv site-packages are accessible even when invoked with system python3
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_venv_site_packages = os.path.join(
    _REPO_ROOT, ".venv", "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages"
)
if os.path.exists(_venv_site_packages) and _venv_site_packages not in sys.path:
    sys.path.insert(0, _venv_site_packages)

from backend.core.graph import build_graph
from backend.core.models import (
    ArxivPaper,
    ConceptGraph,
    RankedPaper,
    SupportedClaim,
    Synthesis,
)
from backend.core.pipeline import run_pipeline
from backend.core.rank import rank

__all__ = [
    "run_pipeline",
    "rank",
    "build_graph",
    "ArxivPaper",
    "RankedPaper",
    "Synthesis",
    "ConceptGraph",
    "SupportedClaim",
]
