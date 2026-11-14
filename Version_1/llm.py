import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()

GEMINI_MODEL = "google_genai:gemini-3.1-flash-lite"
ANTHROPIC_MODEL = "anthropic:claude-sonnet-4-6"

_cache: dict[tuple[str, float], BaseChatModel] = {}


def _model_id() -> str:
    override = os.environ.get("LLM_MODEL")
    if override:
        return override
    if os.environ.get("GOOGLE_API_KEY"):
        return GEMINI_MODEL
    if os.environ.get("ANTHROPIC_API_KEY"):
        return ANTHROPIC_MODEL
    raise RuntimeError(
        "No LLM credentials found. Set GOOGLE_API_KEY (preferred) or ANTHROPIC_API_KEY "
        "in a .env file, or set LLM_MODEL to a provider:model string."
    )


def get_llm(temperature: float = 0.0) -> BaseChatModel:
    """The only place a chat model is constructed. LangChain is a wrapper here, not a chain."""
    key = (_model_id(), temperature)
    if key not in _cache:
        _cache[key] = init_chat_model(key[0], temperature=temperature)
    return _cache[key]
