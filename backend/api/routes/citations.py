"""Citation graph and BibTeX export routes for Rezno AI."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["citations"])


def _get_citations_fn():
    try:
        from backend.integrations.citations import get_citations
        return get_citations
    except ImportError:
        pass

    try:
        import sys
        from pathlib import Path
        v1_dir = str(Path(__file__).resolve().parent.parent.parent / "Version_1")
        if v1_dir not in sys.path:
            sys.path.insert(0, v1_dir)
        from citations import get_citations  # type: ignore
        return get_citations
    except Exception as exc:
        logger.warning(f"Could not import get_citations: {exc}")
        return None


def _get_bibtex_fn():
    try:
        from backend.integrations.bibtex import generate_bibtex
        return generate_bibtex
    except ImportError:
        pass

    try:
        import sys
        from pathlib import Path
        v1_dir = str(Path(__file__).resolve().parent.parent.parent / "Version_1")
        if v1_dir not in sys.path:
            sys.path.insert(0, v1_dir)
        from bibtex import generate_bibtex  # type: ignore
        return generate_bibtex
    except Exception as exc:
        logger.warning(f"Could not import generate_bibtex: {exc}")
        return None


def _get_ranked_paper_class():
    try:
        from backend.core.models import RankedPaper
        return RankedPaper
    except ImportError:
        pass

    try:
        import sys
        from pathlib import Path
        v1_dir = str(Path(__file__).resolve().parent.parent.parent / "Version_1")
        if v1_dir not in sys.path:
            sys.path.insert(0, v1_dir)
        from models import RankedPaper  # type: ignore
        return RankedPaper
    except Exception:
        return None


def _to_ranked_paper(item: Any):
    """Safely convert dict or paper-like object into a RankedPaper instance."""
    RankedPaper = _get_ranked_paper_class()
    if RankedPaper is None:
        # Simple fallback object if models cannot be imported
        class DummyPaper:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        RankedPaper = DummyPaper

    if isinstance(item, RankedPaper):
        return item

    if isinstance(item, dict):
        arxiv_id = str(item.get("arxiv_id", "") or item.get("id", "paper"))
        title = str(item.get("title", "Untitled"))
        authors = item.get("authors") or []
        if isinstance(authors, str):
            authors = [a.strip() for a in authors.split(",")]
        summary = str(item.get("summary", ""))
        published = str(item.get("published", "2024"))
        pdf_url = str(item.get("pdf_url") or (f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else ""))
        abs_url = str(item.get("abs_url") or (f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""))
        primary_category = str(item.get("primary_category", "cs.AI"))
        categories = item.get("categories") or [primary_category]
        relevance_score = float(item.get("relevance_score", 1.0))
        status = item.get("status", "unreviewed")
        note = item.get("note", None)

        try:
            return RankedPaper(
                arxiv_id=arxiv_id,
                title=title,
                authors=authors,
                summary=summary,
                published=published,
                pdf_url=pdf_url,
                abs_url=abs_url,
                primary_category=primary_category,
                categories=categories,
                relevance_score=relevance_score,
                status=status,
                note=note,
            )
        except Exception:
            # If Pydantic strict validation fails on any edge case, return dummy
            class FallbackPaper:
                pass
            p = FallbackPaper()
            p.arxiv_id = arxiv_id
            p.title = title
            p.authors = authors
            p.published = published
            p.pdf_url = pdf_url
            p.abs_url = abs_url
            return p

    return item


class BibtexRequest(BaseModel):
    papers: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of paper objects with at least arxiv_id, title, authors, published",
    )


@router.get("/citations/{arxiv_id}")
async def get_paper_citations(arxiv_id: str):
    """Retrieve forward citations and backward references for a given arXiv ID."""
    citations_fn = _get_citations_fn()
    if citations_fn is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Citations service unavailable", "references": [], "citations": []},
        )

    try:
        # Run blocking network call in threadpool
        data = await asyncio.to_thread(citations_fn, arxiv_id)
        return JSONResponse(content=data)
    except Exception as exc:
        logger.warning(f"Error fetching citations for {arxiv_id}: {exc}")
        return JSONResponse(
            content={"arxiv_id": arxiv_id, "references": [], "citations": [], "error": str(exc)}
        )


@router.post("/bibtex")
async def generate_bibtex_endpoint(request: Request):
    """Generate BibTeX entries for an array of paper objects."""
    bibtex_fn = _get_bibtex_fn()
    if bibtex_fn is None:
        raise HTTPException(status_code=503, detail="BibTeX generation service unavailable")

    try:
        body = await request.json()
    except Exception:
        body = {}

    papers_raw = []
    if isinstance(body, dict):
        papers_raw = body.get("papers", [])
    elif isinstance(body, list):
        papers_raw = body

    if not isinstance(papers_raw, list):
        raise HTTPException(status_code=400, detail="Expected list of papers or JSON object with 'papers' list")

    ranked_papers = [_to_ranked_paper(p) for p in papers_raw]
    bibtex_output = bibtex_fn(ranked_papers)

    return JSONResponse(
        content={
            "bibtex": bibtex_output,
            "count": len(ranked_papers),
        }
    )
