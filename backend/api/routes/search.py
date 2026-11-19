"""Search and synthesis API routes for Rezno AI."""

import asyncio
from datetime import datetime
import json
import logging
from typing import Any, Callable, Dict, List, Optional
import uuid

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(..., description="Academic search prompt or natural language query")
    top_k: int = Field(20, description="Number of ranked papers to return")
    per_query: int = Field(40, description="Candidates retrieved per query variation")
    num_queries: int = Field(3, description="Number of query expansions generated")
    response_length: str = Field("standard", description="Length of synthesis: brief, standard, or detailed")


def _get_pipeline_fn() -> Optional[Callable]:
    """Retrieve run_pipeline from backend.core.pipeline or fallback."""
    try:
        from backend.core.pipeline import run_pipeline
        return run_pipeline
    except ImportError:
        pass

    try:
        import sys
        from pathlib import Path
        v1_dir = str(Path(__file__).resolve().parent.parent.parent / "Version_1")
        if v1_dir not in sys.path:
            sys.path.insert(0, v1_dir)
        from pipeline import run_pipeline  # type: ignore
        return run_pipeline
    except Exception as exc:
        logger.warning(f"Could not import run_pipeline: {exc}")
        return None


def _get_models():
    """Retrieve models from backend.core.models or fallback."""
    try:
        from backend.core.models import Synthesis, SupportedClaim
        return Synthesis, SupportedClaim
    except ImportError:
        pass

    try:
        import sys
        from pathlib import Path
        v1_dir = str(Path(__file__).resolve().parent.parent.parent / "Version_1")
        if v1_dir not in sys.path:
            sys.path.insert(0, v1_dir)
        from models import Synthesis, SupportedClaim  # type: ignore
        return Synthesis, SupportedClaim
    except Exception:
        return None, None


def serialize_item(item: Any) -> Any:
    """Recursively serialize Pydantic models, dataclasses, and primitives."""
    if item is None:
        return None
    if hasattr(item, "model_dump"):
        return item.model_dump()
    if hasattr(item, "dict"):
        return item.dict()
    if hasattr(item, "__dict__"):
        return {k: serialize_item(v) for k, v in item.__dict__.items() if not k.startswith("_")}
    if isinstance(item, list):
        return [serialize_item(x) for x in item]
    if isinstance(item, dict):
        return {k: serialize_item(v) for k, v in item.items()}
    return item


def format_search_result(result: Any, query: str = "") -> Dict[str, Any]:
    """Format PipelineResult into standard JSON response format."""
    if isinstance(result, dict):
        return result

    run_id = f"run-{uuid.uuid4().hex[:8]}"
    timestamp = datetime.now().strftime("%d %b %Y %H:%M")

    raw_papers = getattr(result, "papers", [])
    papers_data = [serialize_item(p) for p in raw_papers]

    for p in papers_data:
        if isinstance(p, dict) and "authors" in p and "author_line" not in p:
            authors = p.get("authors") or []
            if len(authors) > 3:
                p["author_line"] = ", ".join(authors[:3]) + " et al."
            else:
                p["author_line"] = ", ".join(authors)

    raw_graph = getattr(result, "graph", None)
    graph_data = serialize_item(raw_graph) if raw_graph else {"nodes": [], "edges": []}

    raw_synthesis = getattr(result, "synthesis", None)
    if raw_synthesis:
        synthesis_data = serialize_item(raw_synthesis)
    else:
        synthesis_data = {
            "summary": "No synthesis generated.",
            "citations": [p["arxiv_id"] for p in papers_data[:5] if "arxiv_id" in p],
            "claims": [],
        }

    return {
        "id": run_id,
        "query": getattr(result, "query", query),
        "queries": getattr(result, "queries", [query]),
        "candidate_count": getattr(result, "candidate_count", len(papers_data)),
        "papers": papers_data,
        "insights": [serialize_item(i) for i in getattr(result, "insights", [])],
        "graph": graph_data,
        "synthesis": synthesis_data,
        "search_status": getattr(result, "search_status", "success"),
        "search_error": getattr(result, "search_error", None),
        "timestamp": timestamp,
    }


def build_fallback_search_result(query: str, error: Optional[str] = None) -> Dict[str, Any]:
    """Create a structured fallback response when pipeline fails completely."""
    return {
        "id": f"run-{uuid.uuid4().hex[:8]}",
        "query": query,
        "queries": [query],
        "candidate_count": 0,
        "papers": [],
        "insights": [],
        "graph": {"nodes": [], "edges": []},
        "synthesis": {
            "summary": f"Research run degraded: {error or 'Pipeline unavailable'}. Please verify backend configuration and network access.",
            "citations": [],
            "claims": [],
        },
        "search_status": "search_error",
        "search_error": error,
        "timestamp": datetime.now().strftime("%d %b %Y %H:%M"),
    }


def execute_pipeline(
    query: str,
    top_k: int = 20,
    per_query: int = 40,
    num_queries: int = 3,
    response_length: str = "standard",
    on_progress: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """Execute research pipeline with graceful degradation on missing LLM credentials."""
    run_pipeline = _get_pipeline_fn()
    Synthesis, _ = _get_models()

    if run_pipeline is None:
        return build_fallback_search_result(query, error="Pipeline implementation not found")

    try:
        # Full pipeline attempt (with query expansion and LLM synthesis)
        res = run_pipeline(
            query=query,
            top_k=top_k,
            per_query=per_query,
            num_queries=num_queries,
            response_length=response_length,
            on_progress=on_progress,
        )
        return format_search_result(res, query=query)
    except Exception as exc:
        err_msg = str(exc)
        is_llm_error = any(kw in err_msg.lower() for kw in ["credentials", "api_key", "llm_model", "quota", "rate limit"])
        if is_llm_error:
            logger.warning(f"LLM synthesis unavailable ({exc}); executing retrieval and dense ranking without LLM")
            if on_progress:
                on_progress("LLM unavailable: executing direct retrieval & dense ranking")
            try:
                # Degraded execution: bypass plan_query (expand=False) and analyze_research (with_synthesis=False)
                res = run_pipeline(
                    query=query,
                    top_k=top_k,
                    per_query=per_query,
                    num_queries=num_queries,
                    expand=False,
                    with_synthesis=False,
                    on_progress=on_progress,
                )
                summary_text = (
                    f"Retrieved and ranked {len(res.papers)} papers for '{query}'. "
                    "Note: LLM synthesis skipped due to unconfigured API keys (set GOOGLE_API_KEY in .env)."
                )
                citations = [p.arxiv_id for p in res.papers[:5]]
                if Synthesis:
                    res.synthesis = Synthesis(summary=summary_text, citations=citations, claims=[])
                else:
                    res.synthesis = {"summary": summary_text, "citations": citations, "claims": []}
                return format_search_result(res, query=query)
            except Exception as inner_exc:
                logger.error(f"Degraded retrieval failed: {inner_exc}")
                return build_fallback_search_result(query, error=str(inner_exc))
        else:
            logger.error(f"Pipeline error for query '{query}': {exc}")
            return build_fallback_search_result(query, error=str(exc))


@router.post("/search")
async def post_search(payload: SearchRequest):
    """Synchronous REST search endpoint executing the pipeline and returning full results."""
    result = await asyncio.to_thread(
        execute_pipeline,
        query=payload.query,
        top_k=payload.top_k,
        per_query=payload.per_query,
        num_queries=payload.num_queries,
        response_length=payload.response_length,
    )
    return JSONResponse(content=result)


@router.get("/synthesize")
async def get_synthesize(
    request: Request,
    query: str = Query(..., description="Research query prompt"),
    top_k: int = Query(20, description="Top ranked papers to return"),
    per_query: int = Query(40, description="arXiv candidates per query variation"),
    num_queries: int = Query(3, description="Number of query expansions"),
    response_length: str = Query("standard", description="Length of synthesis"),
):
    """Server-Sent Events (SSE) streaming endpoint yielding step progress and completion payload."""
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def on_progress(msg: str):
        loop.call_soon_threadsafe(
            queue.put_nowait,
            ("progress", {"step": msg, "message": msg}),
        )

    def worker():
        try:
            on_progress("Initializing research pipeline")
            result = execute_pipeline(
                query=query,
                top_k=top_k,
                per_query=per_query,
                num_queries=num_queries,
                response_length=response_length,
                on_progress=on_progress,
            )
            loop.call_soon_threadsafe(
                queue.put_nowait,
                ("complete", result),
            )
        except Exception as exc:
            logger.exception(f"Synthesis stream error: {exc}")
            fallback = build_fallback_search_result(query, error=str(exc))
            loop.call_soon_threadsafe(
                queue.put_nowait,
                ("complete", fallback),
            )
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    # Launch worker in thread pool
    asyncio.create_task(asyncio.to_thread(worker))

    async def event_generator():
        while True:
            # Check client disconnect
            if await request.is_disconnected():
                break

            item = await queue.get()
            if item is None:
                break

            event_type, event_data = item
            yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
