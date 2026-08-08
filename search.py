import logging
from typing import List

import arxiv

from models import ArxivPaper

logger = logging.getLogger(__name__)

_client = arxiv.Client(page_size=100, delay_seconds=3.0, num_retries=3)


def _to_paper(result: arxiv.Result) -> ArxivPaper:
    return ArxivPaper(
        arxiv_id=result.get_short_id(),
        title=result.title.strip().replace("\n", " "),
        authors=[a.name for a in result.authors],
        summary=result.summary.strip().replace("\n", " "),
        published=result.published.isoformat(),
        pdf_url=result.pdf_url or "",
        abs_url=result.entry_id,
        primary_category=result.primary_category,
        categories=result.categories,
    )


def search(queries: List[str], per_query: int = 80) -> List[ArxivPaper]:
    """Run each query variant, union results, dedupe by arxiv_id (first seen wins)."""
    seen: dict[str, ArxivPaper] = {}
    for q in queries:
        request = arxiv.Search(
            query=q,
            max_results=per_query,
            sort_by=arxiv.SortCriterion.Relevance,
        )
        try:
            for result in _client.results(request):
                paper = _to_paper(result)
                seen.setdefault(paper.arxiv_id, paper)
        except Exception as e:
            # arXiv rate-limits (429), timeouts, or empty pages. One bad
            # variant should cost us its results, not the whole search.
            logger.warning("arxiv query failed, skipping variant %r: %s", q, e)
    return list(seen.values())

