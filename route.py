from typing import List

from llm import get_llm
from models import Route

PROMPT = """Classify the user's message in a research-paper chat.

Papers currently loaded in the conversation:
{papers}

Recent conversation:
{history}

User's new message: {message}

Choose one:
- "follow_up": the message asks about, compares, clarifies, or drills into the papers
  already loaded, or about anything already discussed above. Examples: "explain the
  second one", "how do these differ", "which is most cited", "summarize that again".
- "new_search": the message asks about a topic the loaded papers do not cover, and
  answering it would require searching arXiv for different papers.

If the message is on the same topic as the loaded papers and could plausibly be
answered from their abstracts, prefer "follow_up" — re-running the full search is the
expensive path and should be reserved for genuinely new topics."""


def route(message: str, papers: List, history: List[dict] | None = None) -> str:
    """new_search vs follow_up. No context means there is nothing to follow up on."""
    if not papers:
        return "new_search"

    titles = "\n".join(f"- [{p.arxiv_id}] {p.title}" for p in papers[:10])
    transcript = "\n".join(
        f"{m['role']}: {m['content'][:300]}" for m in (history or [])[-6:]
    ) or "(none)"

    model = get_llm().with_structured_output(Route)
    try:
        return model.invoke(
            PROMPT.format(papers=titles, history=transcript, message=message)
        ).intent
    except Exception:
        # a failed classification should degrade to the cheap path, not a full re-search
        return "follow_up"
