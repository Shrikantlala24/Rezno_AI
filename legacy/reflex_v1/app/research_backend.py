"""Thin adapter over the already-implemented research modules.

`pipeline`, `route`, `synthesize`, and `models` are supplied by the host
project. They are imported lazily-tolerantly here: if they cannot be
reached (missing module, missing API key at import time), the UI surfaces
a real error state instead of fabricating a successful answer.
"""

import importlib
import logging
from types import SimpleNamespace

BACKEND_AVAILABLE: bool = True
BACKEND_ERROR: str = ""

try:  # pragma: no cover - depends on host environment
    ChatMessage = importlib.import_module("models").ChatMessage
    run_pipeline = importlib.import_module("pipeline").run_pipeline
    route = importlib.import_module("route").route
    synthesize_module = importlib.import_module("synthesize")
    follow_up = synthesize_module.follow_up
    follow_up_general = synthesize_module.follow_up_general
except Exception as e:  # pragma: no cover
    logging.exception(f"Error: {e}")
    ChatMessage = None  # type: ignore
    run_pipeline = None  # type: ignore
    route = None  # type: ignore
    follow_up = None  # type: ignore
    follow_up_general = None  # type: ignore
    BACKEND_AVAILABLE = False
    BACKEND_ERROR = (
        "The research pipeline is not reachable from this environment "
        f"({e.__class__.__name__}: {e}). No search was performed."
    )


try:  # pragma: no cover - optional companion modules
    get_citations = importlib.import_module("citations").get_citations
except Exception as e:  # pragma: no cover
    logging.exception(f"Error: {e}")
    get_citations = None  # type: ignore

try:  # pragma: no cover - optional companion modules
    generate_bibtex = importlib.import_module("bibtex").generate_bibtex
except Exception as e:  # pragma: no cover
    logging.exception(f"Error: {e}")
    generate_bibtex = None  # type: ignore


def to_chat_message(message: dict):
    """Convert a stored message dict into the backend `ChatMessage` model."""
    if ChatMessage is None:
        return message
    try:
        return ChatMessage(
            role=message.get("role", "assistant"),
            content=message.get("content", ""),
        )
    except Exception as e:
        logging.exception(f"Error: {e}")
        return message


def history_for_backend(messages: list[dict]) -> list:
    """Message history in the shape the backend router/synthesizer expects."""
    return [to_chat_message(m) for m in messages]


def concepts_for_result(result) -> list[str]:
    """Deduplicated concept strings across every insight of a pipeline result."""
    seen: dict[str, None] = {}
    try:
        for insight in getattr(result, "insights", None) or []:
            for concept in getattr(insight, "concepts", None) or []:
                seen.setdefault(concept, None)
    except Exception as e:
        logging.exception(f"Error: {e}")
    return list(seen)


def claims_of(synthesis) -> list[dict]:
    """Normalize `Synthesis.claims` into plain dicts for the UI layer."""
    out: list[dict] = []
    try:
        for claim in getattr(synthesis, "claims", None) or []:
            out.append(
                {
                    "claim": str(getattr(claim, "claim", "")),
                    "arxiv_id": str(getattr(claim, "arxiv_id", "")),
                    "supporting_sentence": str(
                        getattr(claim, "supporting_sentence", "")
                    ),
                }
            )
    except Exception as e:
        logging.exception(f"Error: {e}")
    return out
