import json
import logging
import urllib.request
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def get_citations(arxiv_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch references (backward) and citations (forward) from Semantic Scholar Graph API.

    Returns:
        {"references": [...], "citations": [...]}
    """
    clean_id = arxiv_id.split("v")[0]
    url = (
        f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{clean_id}"
        f"?fields=citations,references"
    )

    req = urllib.request.Request(
        url, headers={"User-Agent": "ResearchAgentPrototype/1.0"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

            def parse_item(item: Dict) -> Dict[str, Any]:
                ext_ids = item.get("externalIds") or {}
                item_arxiv = (
                    ext_ids.get("ArXiv")
                    or ext_ids.get("arXiv")
                    or item.get("paperId", "")
                )
                authors = [
                    a.get("name", "")
                    for a in item.get("authors", [])
                    if a.get("name")
                ]
                return {
                    "arxiv_id": item_arxiv,
                    "title": item.get("title") or "Untitled",
                    "authors": authors,
                    "year": str(item.get("year") or ""),
                    "raw": item,
                }

            references = [
                parse_item(ref)
                for ref in data.get("references", [])
                if ref and ref.get("title")
            ]
            citations = [
                parse_item(cit)
                for cit in data.get("citations", [])
                if cit and cit.get("title")
            ]
            return {"references": references, "citations": citations}
    except Exception as e:
        logger.warning(f"Semantic Scholar lookup failed for arXiv:{clean_id}: {e}")
        return {"references": [], "citations": []}
