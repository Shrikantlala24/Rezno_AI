"""Compare tab state: pick two research runs and diff their result sets."""

import logging
from typing import TypedDict

import reflex as rx


class RunOption(TypedDict):
    id: str
    label: str


class PaperRef(TypedDict):
    arxiv_id: str
    title: str


class CompareState(rx.State):
    """Selection for the two runs being compared. Data lives in WorkspaceState."""

    run_a_id: str = ""
    run_b_id: str = ""

    # ------------------------------------------------------------- data reads

    async def _runs(self) -> list[dict]:
        from app.states.workspace_state import WorkspaceState

        try:
            workspace = await self.get_state(WorkspaceState)
            return [dict(run) for run in workspace.runs]
        except Exception as e:
            logging.exception(f"Error: {e}")
            return []

    def _resolve(self, runs: list[dict]) -> tuple[dict | None, dict | None]:
        if len(runs) < 2:
            return None, None
        by_id = {str(run["id"]): run for run in runs}
        run_a = by_id.get(self.run_a_id) or runs[0]
        run_b = by_id.get(self.run_b_id)
        if run_b is None or str(run_b["id"]) == str(run_a["id"]):
            run_b = next(
                (r for r in reversed(runs) if str(r["id"]) != str(run_a["id"])),
                runs[-1],
            )
        return run_a, run_b

    def _papers(self, run: dict | None) -> dict[str, str]:
        if not run:
            return {}
        out: dict[str, str] = {}
        try:
            for paper in run["papers"]:
                out[str(paper["arxiv_id"])] = str(paper["title"])
        except Exception as e:
            logging.exception(f"Error: {e}")
        return out

    def _concepts(self, run: dict | None) -> set[str]:
        if not run:
            return set()
        try:
            return {str(c) for c in list(run["concepts"])}
        except Exception as e:
            logging.exception(f"Error: {e}")
            return set()

    # ---------------------------------------------------------- computed vars

    @rx.var
    async def options(self) -> list[RunOption]:
        runs = await self._runs()
        out: list[RunOption] = []
        for run in runs:
            query = str(run.get("query", "") or "untitled run")
            label = query if len(query) <= 38 else f"{query[:37]}…"
            out.append(
                RunOption(
                    id=str(run["id"]),
                    label=f"{label} · {run.get('timestamp', '')}",
                )
            )
        return out

    @rx.var
    async def pair_ready(self) -> bool:
        runs = await self._runs()
        return len(runs) > 1

    @rx.var
    async def value_a(self) -> str:
        runs = await self._runs()
        run_a, _ = self._resolve(runs)
        return str(run_a["id"]) if run_a else ""

    @rx.var
    async def value_b(self) -> str:
        runs = await self._runs()
        _, run_b = self._resolve(runs)
        return str(run_b["id"]) if run_b else ""

    @rx.var
    async def query_a(self) -> str:
        runs = await self._runs()
        run_a, _ = self._resolve(runs)
        return str(run_a.get("query", "")) if run_a else ""

    @rx.var
    async def query_b(self) -> str:
        runs = await self._runs()
        _, run_b = self._resolve(runs)
        return str(run_b.get("query", "")) if run_b else ""

    @rx.var
    async def shared_papers(self) -> list[PaperRef]:
        runs = await self._runs()
        run_a, run_b = self._resolve(runs)
        papers_a = self._papers(run_a)
        papers_b = self._papers(run_b)
        return [
            PaperRef(arxiv_id=pid, title=title)
            for pid, title in papers_a.items()
            if pid in papers_b
        ]

    @rx.var
    async def only_a_papers(self) -> list[PaperRef]:
        runs = await self._runs()
        run_a, run_b = self._resolve(runs)
        papers_a = self._papers(run_a)
        papers_b = self._papers(run_b)
        return [
            PaperRef(arxiv_id=pid, title=title)
            for pid, title in papers_a.items()
            if pid not in papers_b
        ]

    @rx.var
    async def only_b_papers(self) -> list[PaperRef]:
        runs = await self._runs()
        run_a, run_b = self._resolve(runs)
        papers_a = self._papers(run_a)
        papers_b = self._papers(run_b)
        return [
            PaperRef(arxiv_id=pid, title=title)
            for pid, title in papers_b.items()
            if pid not in papers_a
        ]

    @rx.var
    async def shared_count(self) -> int:
        return len(await self.shared_papers)

    @rx.var
    async def only_a_count(self) -> int:
        return len(await self.only_a_papers)

    @rx.var
    async def only_b_count(self) -> int:
        return len(await self.only_b_papers)

    @rx.var
    async def shared_concepts(self) -> list[str]:
        runs = await self._runs()
        run_a, run_b = self._resolve(runs)
        return sorted(self._concepts(run_a) & self._concepts(run_b))

    # --------------------------------------------------------------- events

    @rx.event
    def set_run_a(self, value: str):
        self.run_a_id = value

    @rx.event
    def set_run_b(self, value: str):
        self.run_b_id = value
