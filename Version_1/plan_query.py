import logging
import re
from functools import lru_cache
from typing import List

from llm import get_llm
from models import QueryPlan

PROMPT = """Convert this research question into arXiv API search queries.

Question: {query}

arXiv search is Lucene keyword matching over titles and abstracts only — there is
no full-text index and no semantic understanding. A raw question performs badly.
Your job is to produce queries whose keywords actually appear in the abstracts of
the relevant papers.

Write 3-4 query variants that differ in strategy, for example:
- the canonical technical term for the topic (what the papers call themselves)
- a well-known method or model name in this area, if one exists
- a broader phrasing scoped by category

Syntax:
- Field prefixes: all:, ti:, abs:, cat:
- Operators: AND, OR, ANDNOT
- Quote multi-word phrases: abs:"retrieval augmented generation"
- Scope with cat: when the field is obvious (cs.CL, cs.LG, cs.CV, cs.AI, cs.IR, stat.ML)
- Add submittedDate:[YYYYMMDDHHMM TO YYYYMMDDHHMM] ONLY if the question asks for
  recent/latest work

Rules:
- Use terminology the papers themselves use, not the user's phrasing
- Keep each variant focused; do not AND together many terms or you get zero results
- Vary specificity: at least one narrow variant and one broader variant"""

logger = logging.getLogger(__name__)
_VALID_QUERY = re.compile(r'^[\w\s:\-\[\]".]+$', re.ASCII)


def is_valid_arxiv_query(query: str) -> bool:
    """Return whether a planner-produced query is safe to send to arXiv.

    Args:
        query: Candidate Lucene-style arXiv query.

    Returns:
        True when the query is nonempty, bounded, and uses the supported character set.
    """
    return bool(query and len(query) <= 300 and _VALID_QUERY.fullmatch(query))


@lru_cache(maxsize=128)
def _plan_query_cached(query: str, num_queries: int) -> tuple[str, ...]:
    """NL question -> arXiv boolean query variants. Falls back to raw query on failure."""
    model = get_llm().with_structured_output(QueryPlan)
    try:
        plan = model.invoke(PROMPT.format(query=query))
    except Exception as error:
        logger.warning("query planning failed; using original query: %s", error)
        return (query,)

    variants = []
    for candidate in plan.queries:
        normalized = candidate.strip() if candidate else ""
        if is_valid_arxiv_query(normalized):
            variants.append(normalized)
        elif normalized:
            logger.warning("skipping malformed planner query: %r", normalized)
    return tuple(variants[:num_queries] or [query])


def plan_query(query: str, num_queries: int = 4) -> List[str]:
    """Expand a question once per exact query/session process, with raw fallback."""
    return list(_plan_query_cached(query.strip(), num_queries))
