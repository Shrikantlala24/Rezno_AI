"""Native Google GenAI SDK integration with rate limiting and exponential backoff.

Replaces LangChain entirely with direct calls to google-genai.
Free-tier rate limits:
- Gemini Flash (gemini-2.5-flash): 5 RPM
- Gemini Flash-Lite (gemini-2.5-flash-lite): 15 RPM
"""

import logging
import os
import threading
import time
from collections import deque
from typing import Any, Callable, Optional, Type, TypeVar

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

load_dotenv()

# Harmonize API key if GEMINI_API_KEY is provided without GOOGLE_API_KEY
if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Model definitions per task allocation
MODEL_FLASH = "gemini-3.8-flash"
MODEL_FLASH_LITE = "gemini-3.5-flash-lite"

MODEL_MAP = {
    "flash": MODEL_FLASH,
    "flash_lite": MODEL_FLASH_LITE,
    "flash-lite": MODEL_FLASH_LITE,
}


def resolve_model(model_type: str = "flash_lite") -> str:
    """Resolve model_type alias to full Gemini model ID with optional env override."""
    override = os.environ.get("LLM_MODEL")
    if override:
        return override
    return MODEL_MAP.get(model_type, model_type)


class RateLimiter:
    """Sliding-window timestamp rate limiter to enforce free-tier RPM quotas.

    Tracks request timestamps within a 60-second window to prevent bursts exceeding
    5 RPM (Flash) or 15 RPM (Flash-Lite).
    """

    def __init__(
        self,
        max_requests: int,
        window_seconds: float = 60.0,
        time_fn: Optional[Callable[[], float]] = None,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.timestamps: deque[float] = deque()
        self.lock = threading.Lock()
        self.time_fn = time_fn or time.time

    def acquire(self) -> None:
        """Block until a request slot is available in the current window."""
        with self.lock:
            now = self.time_fn()
            # Evict timestamps outside the window
            while self.timestamps and (now - self.timestamps[0]) >= self.window_seconds:
                self.timestamps.popleft()

            while len(self.timestamps) >= self.max_requests:
                oldest = self.timestamps[0]
                sleep_needed = self.window_seconds - (now - oldest) + 0.05
                if sleep_needed > 0:
                    logger.warning(
                        "Rate limit reached (%d/%d req per %.1fs). Throttling for %.2fs...",
                        len(self.timestamps),
                        self.max_requests,
                        self.window_seconds,
                        sleep_needed,
                    )
                    time.sleep(sleep_needed)
                now = self.time_fn()
                while self.timestamps and (now - self.timestamps[0]) >= self.window_seconds:
                    self.timestamps.popleft()

            self.timestamps.append(self.time_fn())

    def reset(self) -> None:
        """Clear all recorded timestamps."""
        with self.lock:
            self.timestamps.clear()


# Model-specific rate limiters
_flash_limiter = RateLimiter(max_requests=5, window_seconds=60.0)
_flash_lite_limiter = RateLimiter(max_requests=15, window_seconds=60.0)


def get_limiter_for_model(model_type: str) -> RateLimiter:
    """Return the rate limiter instance associated with the specified model."""
    resolved = resolve_model(model_type).lower()
    if "lite" in resolved:
        return _flash_lite_limiter
    return _flash_limiter


def _is_rate_limit_error(exc: Exception) -> bool:
    """Check if an exception represents an HTTP 429 or RESOURCE_EXHAUSTED rate limit."""
    if isinstance(exc, errors.APIError):
        if getattr(exc, "code", None) == 429:
            return True
        status = str(getattr(exc, "status", "")).upper()
        if "RESOURCE_EXHAUSTED" in status:
            return True
        msg = str(getattr(exc, "message", "")).lower()
        if "rate limit" in msg or "quota" in msg or "resource_exhausted" in msg:
            return True
    exc_str = str(exc).lower()
    return "429" in exc_str or "resource_exhausted" in exc_str or "rate limit" in exc_str or "quota exceeded" in exc_str


def _execute_with_retry(
    fn: Callable[[], Any],
    max_retries: int = 3,
    initial_delay: float = 4.0,
    backoff_factor: float = 2.0,
) -> Any:
    """Execute a function with exponential backoff on errors.APIError or HTTP 429."""
    delay = initial_delay
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as exc:
            is_retryable = isinstance(exc, errors.APIError) or _is_rate_limit_error(exc)
            if not is_retryable or attempt >= max_retries:
                raise
            logger.warning(
                "Gemini API call failed (%s); retrying in %.1fs (attempt %d/%d)...",
                exc,
                delay,
                attempt + 1,
                max_retries,
            )
            time.sleep(delay)
            delay *= backoff_factor


def generate_structured(
    prompt: str,
    schema: Type[T],
    model_type: str = "flash_lite",
    temperature: float = 0.0,
    client: Optional[genai.Client] = None,
) -> T:
    """Generate structured Pydantic object from prompt using Google GenAI SDK.

    Args:
        prompt: Text prompt to send to the model.
        schema: Pydantic model class defining the desired JSON output structure.
        model_type: 'flash_lite' (default, 15 RPM) or 'flash' (5 RPM).
        temperature: Sampling temperature (default 0.0 for deterministic extraction).
        client: Optional pre-configured genai.Client instance.

    Returns:
        Validated instance of schema (T).
    """
    limiter = get_limiter_for_model(model_type)
    limiter.acquire()

    if client is None:
        client = genai.Client()

    model_name = resolve_model(model_type)
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=temperature,
    )

    def _call():
        return client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )

    response = _execute_with_retry(_call)
    parsed = getattr(response, "parsed", None)
    if parsed is not None:
        return parsed
    text = getattr(response, "text", None)
    if text:
        return schema.model_validate_json(text)
    raise ValueError(f"Failed to extract structured {schema.__name__} from model response: {response}")


def generate_text(
    prompt: str,
    model_type: str = "flash_lite",
    temperature: float = 0.0,
    client: Optional[genai.Client] = None,
) -> str:
    """Generate freeform text response using Google GenAI SDK.

    Args:
        prompt: Text prompt to send to the model.
        model_type: 'flash_lite' (default, 15 RPM) or 'flash' (5 RPM).
        temperature: Sampling temperature.
        client: Optional pre-configured genai.Client instance.

    Returns:
        Generated text string.
    """
    limiter = get_limiter_for_model(model_type)
    limiter.acquire()

    if client is None:
        client = genai.Client()

    model_name = resolve_model(model_type)
    config = types.GenerateContentConfig(
        temperature=temperature,
    )

    def _call():
        return client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )

    response = _execute_with_retry(_call)
    text = getattr(response, "text", None)
    return text.strip() if text is not None else str(response).strip()


def get_llm(*args, **kwargs):
    """Deprecated shim for historical LangChain get_llm callers."""
    raise DeprecationWarning(
        "LangChain get_llm() is eliminated. Use generate_structured() or generate_text() instead."
    )
