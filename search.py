import logging
from dataclasses import dataclass, field
from typing import Callable, List, Literal, Optional

import arxiv
import requests

from models import ArxivPaper

logger = logging.getLogger(__name__)

Progress = Optional[Callable[[str], None]]

ARXIV_HTTP_TIMEOUT = 25.0


class _TimeoutSession(requests.Session):
    """``requests.Session`` that injects a timeout into every HTTP request.

    The arxiv 2.2.0 client calls ``self._session.get(url, headers=...)``
    without a timeout, which means ``requests`` defaults to *no timeout*
    and the call can hang indefinitely.  By overriding ``request`` we
    can guarantee every HTTP operation is bounded.
    """

    def __init__(self, timeout: float = ARXIV_HTTP_TIMEOUT):
        super().__init__()
        self._timeout = timeout

    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", self._timeout)
        return super().request(method, url, **kwargs)


_CLIENT = arxiv.Client(page_size=100, delay_seconds=1.0, num_retries=2)
_CLIENT._session = _TimeoutSession()


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


@dataclass
class SearchResult:
    """Outcome of isolated arXiv query attempts.

    A zero-result response is deliberately distinct from a transport/API failure.
    """

    papers: List[ArxivPaper] = field(default_factory=list)
    status: Literal["success", "partial_results", "no_results", "search_error"] = "no_results"
    failed_queries: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def _search_one(query: str, per_query: int) -> tuple[List[ArxivPaper], Optional[str]]:
    """Execute a single arXiv query. Returns (papers, error_message)."""
    request = arxiv.Search(
        query=query,
        max_results=per_query,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    try:
        papers = [
            _to_paper(result)
            for result in _CLIENT.results(request)
        ]
        return papers, None
    except (
        requests.exceptions.ReadTimeout,
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
        arxiv.ArxivError,
        ConnectionError,
        OSError,
        ValueError,
    ) as error:
        return [], str(error)


def search(
    queries: List[str],
    per_query: int = 80,
    on_progress: Progress = None,
) -> SearchResult:
    """Run isolated arXiv queries concurrently with per-query failure isolation.

    Args:
        queries: List of arXiv boolean query strings.
        per_query: Max results to fetch per query.
        on_progress: Callback invoked before and after query batch execution.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    seen: dict[str, ArxivPaper] = {}
    failed_queries: List[str] = []
    errors: List[str] = []
    total = len(queries)

    if on_progress:
        on_progress(f"Searching arXiv ({total} queries in parallel)")

    max_workers = min(2, total) if total > 0 else 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_query = {
            executor.submit(_search_one, q, per_query): q for q in queries
        }
        completed_count = 0
        for future in as_completed(future_to_query):
            q = future_to_query[future]
            completed_count += 1
            if on_progress:
                on_progress(f"Fetched query variant {completed_count}/{total}")
            try:
                papers, error = future.result()
            except Exception as exc:
                papers, error = [], str(exc)

            if error:
                failed_queries.append(q)
                errors.append(error)
                logger.warning("arxiv query failure variant %r: %s", q, error)
            else:
                for paper in papers:
                    seen.setdefault(paper.arxiv_id, paper)

    papers = list(seen.values())
    if papers:
        status: Literal["success", "partial_results", "no_results", "search_error"] = (
            "partial_results" if failed_queries else "success"
        )
        logger.info(
            "Search complete: %d unique papers, %d failed queries",
            len(papers), len(failed_queries),
        )
    elif failed_queries:
        status = "search_error"
        logger.warning(
            "Search FAILED: all %d queries failed, no papers retrieved", total,
        )
    else:
        status = "no_results"
        logger.info("Search complete: 0 papers from all %d queries (successful zero-results)", total)

    return SearchResult(
        papers=papers, status=status, failed_queries=failed_queries, errors=errors
    )
