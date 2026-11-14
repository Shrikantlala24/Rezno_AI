"""Conversation rail state: message thread, in-flight run, submit orchestration."""

import asyncio
import logging
import time
import uuid
from typing import TypedDict

import reflex as rx

MAX_RUNS: int = 10

_SCROLL_SCRIPT: str = """
const el = document.getElementById('ra-conversation-scroll');
if (el) { el.scrollTop = el.scrollHeight; }
const log = document.getElementById('ra-thinking-log');
if (log) { log.scrollTop = log.scrollHeight; }
"""


class Claim(TypedDict):
    claim: str
    arxiv_id: str
    supporting_sentence: str


class Message(TypedDict):
    id: str
    role: str
    content: str
    intent: str
    search_run_id: str
    is_unsourced: bool
    is_fallback: bool
    is_error: bool
    response_length: str
    claims: list[Claim]


def _message(
    role: str,
    content: str,
    intent: str = "",
    search_run_id: str = "",
    is_unsourced: bool = False,
    is_fallback: bool = False,
    is_error: bool = False,
    response_length: str = "standard",
    claims: list[Claim] | None = None,
) -> Message:
    return Message(
        id=uuid.uuid4().hex,
        role=role,
        content=content,
        intent=intent,
        search_run_id=search_run_id,
        is_unsourced=is_unsourced,
        is_fallback=is_fallback,
        is_error=is_error,
        response_length=response_length,
        claims=claims or [],
    )


def _execute_turn(
    question: str,
    history: list[dict],
    run: dict | None,
    settings: dict[str, str | int],
    on_progress,
) -> dict:
    """Route the question and run the matching backend call (blocking)."""
    from app import research_backend as rb

    try:
        context_papers = list(run.get("papers") or []) if run else []
        backend_history = rb.history_for_backend(history)
        intent, is_fallback = rb.route(
            question, context_papers, backend_history
        )
        label = str(intent).replace("_", " ")
        on_progress(f"Route: {label}{' · fallback' if is_fallback else ''}")

        response_length = str(settings.get("response_length", "standard"))
        top_k = int(settings.get("top_k", 5))

        if intent == "new_search":
            result = rb.run_pipeline(
                question,
                top_k=top_k,
                per_query=int(settings.get("per_query", 10)),
                num_queries=int(settings.get("num_queries", 4)),
                response_length=response_length,
                on_progress=on_progress,
            )
            synthesis = getattr(result, "synthesis", None)
            papers = list(getattr(result, "papers", None) or [])
            summary = str(getattr(synthesis, "summary", "") or "").strip()
            run_payload = {
                "id": f"run_{int(time.time() * 1000)}",
                "query": question,
                "papers": papers,
                "result": result,
                "timestamp": time.strftime("%H:%M:%S"),
                "search_status": str(
                    getattr(result, "search_status", "ok") or "ok"
                ),
            }
            return {
                "status": "ok",
                "intent": "new_search",
                "content": summary or "Search temporarily failed.",
                "claims": rb.claims_of(synthesis),
                "is_unsourced": len(papers) == 0,
                "is_fallback": False,
                "response_length": response_length,
                "run": run_payload,
                "run_id": run_payload["id"],
            }

        if intent == "follow_up_grounded":
            on_progress(
                "Answering from papers already in context — no new search"
            )
            synthesis = rb.follow_up(
                question,
                backend_history,
                list(run.get("papers") or []) if run else [],
                rb.concepts_for_result(run.get("result")) if run else [],
                top_n=top_k,
                response_length=response_length,
            )
            return {
                "status": "ok",
                "intent": "follow_up_grounded",
                "content": str(getattr(synthesis, "summary", "") or ""),
                "claims": rb.claims_of(synthesis),
                "is_unsourced": False,
                "is_fallback": False,
                "response_length": response_length,
                "run": None,
                "run_id": str(run.get("id", "")) if run else "",
            }

        on_progress(
            "Answering using live web search — not from retrieved papers"
        )
        answer = rb.follow_up_general(question, backend_history)
        return {
            "status": "ok",
            "intent": "follow_up_general",
            "content": str(answer or ""),
            "claims": [],
            "is_unsourced": True,
            "is_fallback": bool(is_fallback),
            "response_length": response_length,
            "run": None,
            "run_id": "",
        }
    except Exception as e:
        logging.exception(f"Error: {e}")
        return {
            "status": "error",
            "detail": f"{e.__class__.__name__}: {e}",
        }


class ConversationState(rx.State):
    """Session-scoped conversation: messages, thinking status, settings."""

    messages: list[Message] = []
    composer_text: str = ""
    composer_key: int = 0

    is_thinking: bool = False
    thinking_label: str = "Thinking…"
    thinking_open: bool = True
    progress_log: list[str] = []

    expanded_evidence: list[str] = []

    per_query: int = 10
    top_k: int = 5
    num_queries: int = 4
    response_length: str = "standard"

    _runs: list = []
    _selected_run_id: str = ""

    @rx.var
    def show_empty_state(self) -> bool:
        return (len(self.messages) == 0) and (not self.is_thinking)

    @rx.var
    def message_count(self) -> int:
        return len(self.messages)

    @rx.var
    def run_count(self) -> int:
        return len(self._runs)

    def _selected_run(self) -> dict | None:
        if not self._runs:
            return None
        for run in self._runs:
            if run.get("id") == self._selected_run_id:
                return run
        return self._runs[-1]

    @rx.event
    def set_composer_text(self, value: str):
        self.composer_text = value

    @rx.event
    def set_per_query(self, value: str):
        try:
            self.per_query = int(float(value))
        except Exception as e:
            logging.exception(f"Error: {e}")

    @rx.event
    def set_top_k(self, value: str):
        try:
            self.top_k = int(float(value))
        except Exception as e:
            logging.exception(f"Error: {e}")

    @rx.event
    def set_num_queries(self, value: str):
        try:
            self.num_queries = int(float(value))
        except Exception as e:
            logging.exception(f"Error: {e}")

    @rx.event
    def set_response_length(self, value: str):
        self.response_length = value

    @rx.event
    def toggle_thinking_open(self):
        self.thinking_open = not self.thinking_open

    @rx.event
    def toggle_evidence(self, message_id: str):
        if message_id in self.expanded_evidence:
            self.expanded_evidence.remove(message_id)
        else:
            self.expanded_evidence.append(message_id)

    @rx.event
    def clear_conversation(self):
        self.messages = []
        self.progress_log = []
        self.expanded_evidence = []
        self.is_thinking = False
        self.composer_text = ""
        self.composer_key += 1
        self._runs = []
        self._selected_run_id = ""

    @rx.event
    async def clear_session(self):
        from app.states.workspace_state import WorkspaceState

        workspace = await self.get_state(WorkspaceState)
        workspace._reset()
        self.messages = []
        self.progress_log = []
        self.expanded_evidence = []
        self.is_thinking = False
        self.composer_text = ""
        self.composer_key += 1
        self._runs = []
        self._selected_run_id = ""

    @rx.event(background=True)
    async def submit(self):
        question = ""
        history: list[dict] = []
        run: dict | None = None
        settings: dict[str, str | int] = {}

        async with self:
            candidate = self.composer_text.strip()
            if candidate and not self.is_thinking:
                question = candidate
                self.composer_text = ""
                self.composer_key += 1
                self.messages.append(_message("user", question))
                self.is_thinking = True
                self.thinking_open = True
                self.thinking_label = "Thinking…"
                self.progress_log = ["Routing the question"]
                history = [dict(m) for m in self.messages[:-1]]
                run = self._selected_run()
                settings = {
                    "per_query": self.per_query,
                    "top_k": self.top_k,
                    "num_queries": self.num_queries,
                    "response_length": self.response_length,
                }

        if not question:
            yield rx.toast("Enter a research question first.", duration=2500)
            return

        yield rx.call_script(_SCROLL_SCRIPT)

        from app import research_backend as rb

        if not rb.BACKEND_AVAILABLE:
            async with self:
                self.is_thinking = False
                self.thinking_open = False
                self.messages.append(
                    _message("assistant", rb.BACKEND_ERROR, is_error=True)
                )
            yield rx.call_script(_SCROLL_SCRIPT)
            return

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[str] = asyncio.Queue()

        @rx.event
        def on_progress(line) -> None:
            try:
                loop.call_soon_threadsafe(queue.put_nowait, line)
            except Exception as e:
                logging.exception(f"Error: {e}")

        task = asyncio.create_task(
            asyncio.to_thread(
                _execute_turn, question, history, run, settings, on_progress
            )
        )

        while not task.done() or not queue.empty():
            lines_to_add: list[str] = []
            try:
                line = await asyncio.wait_for(queue.get(), timeout=0.1)
                lines_to_add.append(line)
                while not queue.empty():
                    lines_to_add.append(queue.get_nowait())
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.exception(f"Error reading progress queue: {e}")
                break

            if lines_to_add:
                async with self:
                    self.progress_log.extend(lines_to_add)
                    self.thinking_label = lines_to_add[-1]
                yield rx.call_script(_SCROLL_SCRIPT)

        try:
            result = await task
        except Exception as e:
            logging.exception(f"Error: {e}")
            result = {
                "status": "error",
                "detail": f"{e.__class__.__name__}: {e}",
            }

        async with self:
            self.is_thinking = False
            self.thinking_open = False
            if result.get("status") == "ok":
                self.thinking_label = "Answer ready"
                run_payload = result.get("run")
                if run_payload is not None:
                    self._runs.append(run_payload)
                    if len(self._runs) > MAX_RUNS:
                        self._runs.pop(0)
                    self._selected_run_id = str(run_payload["id"])
                    try:
                        from app.states.workspace_state import WorkspaceState
                        from app.workspace_serialize import run_to_ui

                        workspace = await self.get_state(WorkspaceState)
                        workspace._ingest_run(run_to_ui(run_payload))
                    except Exception as e:
                        logging.exception(f"Error: {e}")
                self.messages.append(
                    _message(
                        "assistant",
                        result.get("content"),
                        intent=str(result.get("intent", "")),
                        search_run_id=str(result.get("run_id", "")),
                        is_unsourced=bool(result.get("is_unsourced", False)),
                        is_fallback=bool(result.get("is_fallback", False)),
                        response_length=str(
                            result.get("response_length", "standard")
                        ),
                        claims=list(result.get("claims") or []),
                    )
                )
            else:
                self.messages.append(
                    _message(
                        "assistant",
                        "The research run failed before an answer could be "
                        f"produced. {result.get('detail', '')}",
                        is_error=True,
                    )
                )

        yield rx.call_script(_SCROLL_SCRIPT)
