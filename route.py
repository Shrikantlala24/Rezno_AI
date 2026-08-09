import re
from typing import List, Tuple

from llm import get_llm
from models import Route

PROMPT = """Classify the user's message in a research-paper chat.

Papers currently loaded in the conversation:
{papers}

Recent conversation:
{history}

User's new message: {message}

Choose one:
- "follow_up_grounded": the message asks about, compares, clarifies, or drills into the papers
  already loaded, or about specific findings/abstracts in loaded papers. Examples: "explain paper 2",
  "how do these differ", "summarize their findings", "what method did the first paper use".
- "follow_up_general": the message asks a general conceptual, background, or foundational question
  (e.g., "what is a neural node", "explain attention simply") that is not specific to the loaded paper abstracts
  and does NOT require searching arXiv for new research papers.
- "new_search": the message asks about a topic the loaded papers do not cover, and
  answering it requires searching arXiv for different research papers.

If the message is on the same topic as the loaded papers and could plausibly be
answered from their abstracts, prefer "follow_up_grounded". If it is a general question answerable without paper context, choose "follow_up_general"."""


def route(message: str, papers: List, history: List | None = None) -> Tuple[str, bool]:
    """Classify into new_search, follow_up_grounded, or follow_up_general.

    Returns:
        Tuple[intent, is_fallback]
    """
    if not papers:
        return "new_search", False

    normalized = message.lower().strip()
    if re.search(r"\b(paper|papers|these|them|first|second|compare|difference|abstract|finding|result)\b", normalized):
        return "follow_up_grounded", False
    if re.match(r"^(what is|what are|explain|define|how does)\b", normalized):
        return "follow_up_general", False

    titles = "\n".join(f"- [{p.arxiv_id}] {p.title}" for p in papers[:10])
    transcript = "\n".join(
        f"{m.role if hasattr(m, 'role') else m['role']}: {(m.content if hasattr(m, 'content') else m['content'])[:300]}"
        for m in (history or [])[-6:]
    ) or "(none)"

    model = get_llm().with_structured_output(Route)
    try:
        res = model.invoke(
            PROMPT.format(papers=titles, history=transcript, message=message)
        )
        return res.intent, False
    except Exception:
        # On router failure, default to follow_up_general with fallback flag set to True
        return "follow_up_general", True
