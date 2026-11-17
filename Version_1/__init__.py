"""Version_1 backward-compatibility package.

Re-exports core and integration modules from the modern backend package.
"""
import sys, os
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
