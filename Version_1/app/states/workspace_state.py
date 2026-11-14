"""Research workspace state: session-scoped runs, papers, screening, citations."""

import asyncio
import logging
from typing import TypedDict

import reflex as rx

MAX_RUNS: int = 10


class PaperItem(TypedDict):
    arxiv_id: str
    title: str
    authors: list[str]
    author_line: str
    summary: str
    published: str
    pdf_url: str
    abs_url: str
    primary_category: str
    relevance_score: float
    status: str
    note: str


class CitationEntry(TypedDict):
    kind: str
    title: str
    year: str
    authors: str
    arxiv_id: str


class GraphNode(TypedDict):
    id: str
    label: str
    type: str
    pdf_url: str
    abs_url: str


class GraphEdge(TypedDict):
    id: str
    source: str
    target: str
    type: str


class RunItem(TypedDict):
    id: str
    query: str
    timestamp: str
    search_status: str
    search_error: str
    node_count: int
    edge_count: int
    paper_node_count: int
    concept_node_count: int
    papers: list[PaperItem]
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    concepts: list[str]
    citation_ids: list[str]


class WorkspaceState(rx.State):
    """Everything the research workspace rail renders. Dies with the session."""

    runs: list[RunItem] = []
    selected_run_id: str = ""

    expanded_papers: list[str] = []
    expanded_citations: list[str] = []
    citations_by_paper: dict[str, list[CitationEntry]] = {}
    fetched_citations: list[str] = []
    fetching_citations: list[str] = []

    show_citation_ids: bool = False

    # ---------------------------------------------------------------- helpers

    def _current(self) -> RunItem | None:
        if not self.runs:
            return None
        for run in self.runs:
            if run["id"] == self.selected_run_id:
                return run
        return self.runs[-1]

    def _current_index(self) -> int:
        if not self.runs:
            return -1
        for index, run in enumerate(self.runs):
            if run["id"] == self.selected_run_id:
                return index
        return len(self.runs) - 1

    def _ingest_run(self, run: RunItem) -> None:
        """Append a serialized pipeline run and make it the active workspace."""
        self.runs.append(run)
        if len(self.runs) > MAX_RUNS:
            self.runs.pop(0)
        self.selected_run_id = str(run["id"])
        self.expanded_papers = []
        self.expanded_citations = []
        self.show_citation_ids = False
        self.runs = list(self.runs)

    def _reset(self) -> None:
        self.runs = []
        self.selected_run_id = ""
        self.expanded_papers = []
        self.expanded_citations = []
        self.citations_by_paper = {}
        self.fetched_citations = []
        self.fetching_citations = []
        self.show_citation_ids = False

    # ------------------------------------------------------------ computed

    @rx.var
    def has_run(self) -> bool:
        return len(self.runs) > 0

    @rx.var
    def run_count(self) -> int:
        return len(self.runs)

    @rx.var
    def selected_papers(self) -> list[PaperItem]:
        run = self._current()
        return list(run["papers"]) if run else []

    @rx.var
    def paper_count(self) -> int:
        run = self._current()
        return len(run["papers"]) if run else 0

    @rx.var
    def node_count(self) -> int:
        run = self._current()
        return int(run["node_count"]) if run else 0

    @rx.var
    def edge_count(self) -> int:
        run = self._current()
        return int(run["edge_count"]) if run else 0

    @rx.var
    def run_timestamp(self) -> str:
        run = self._current()
        return str(run["timestamp"]) if run else ""

    @rx.var
    def run_status(self) -> str:
        run = self._current()
        return str(run["search_status"]) if run else ""

    @rx.var
    def run_query(self) -> str:
        run = self._current()
        return str(run["query"]) if run else ""

    @rx.var
    def citation_ids(self) -> list[str]:
        run = self._current()
        return list(run["citation_ids"]) if run else []

    @rx.var
    def kept_count(self) -> int:
        run = self._current()
        if not run:
            return 0
        return len([p for p in run["papers"] if p["status"] == "keep"])

    @rx.var
    def run_options(self) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        for run in self.runs:
            query = str(run.get("query", "") or "Untitled search")
            label = query if len(query) <= 35 else f"{query[:34]}…"
            out.append(
                {
                    "id": str(run["id"]),
                    "label": f"{label} ({run.get('timestamp', '')})",
                }
            )
        return out

    # -------------------------------------------------------------- events

    @rx.event
    def select_run(self, run_id: str):
        self.selected_run_id = run_id
        self.expanded_papers = []
        self.expanded_citations = []

    @rx.event
    def toggle_paper(self, paper_id: str):
        if paper_id in self.expanded_papers:
            self.expanded_papers.remove(paper_id)
        else:
            self.expanded_papers.append(paper_id)

    @rx.event
    def toggle_citations(self, paper_id: str):
        if paper_id in self.expanded_citations:
            self.expanded_citations.remove(paper_id)
        else:
            self.expanded_citations.append(paper_id)

    @rx.event
    def toggle_citation_ids(self):
        self.show_citation_ids = not self.show_citation_ids

    @rx.event
    def set_status(self, paper_id: str, status: str):
        index = self._current_index()
        if index < 0:
            return
        for paper in self.runs[index]["papers"]:
            if paper["arxiv_id"] == paper_id:
                paper["status"] = status
        self.runs = list(self.runs)

    @rx.event
    def set_note(self, paper_id: str, note: str):
        index = self._current_index()
        if index < 0:
            return
        for paper in self.runs[index]["papers"]:
            if paper["arxiv_id"] == paper_id:
                paper["note"] = note
        self.runs = list(self.runs)

    @rx.event
    def download_bibtex(self):
        from app.workspace_serialize import bibtex_for

        run = self._current()
        if not run or not run["papers"]:
            return rx.toast("No papers to export yet.", duration=2500)
        try:
            data = bibtex_for([dict(p) for p in run["papers"]])
        except Exception as e:
            logging.exception(f"Error: {e}")
            return rx.toast("BibTeX export failed.", duration=3000)
        return rx.download(data=data, filename=f"papers_{run['id']}.bib")

    @rx.event(background=True)
    async def fetch_citations(self, paper_id: str):
        async with self:
            if paper_id in self.fetching_citations:
                return
            self.fetching_citations.append(paper_id)
            if paper_id not in self.expanded_citations:
                self.expanded_citations.append(paper_id)

        from app.workspace_serialize import citation_entries_for

        entries: list[CitationEntry] = []
        failed = False
        try:
            entries = await asyncio.to_thread(citation_entries_for, paper_id)
        except Exception as e:
            logging.exception(f"Error: {e}")
            failed = True

        async with self:
            if paper_id in self.fetching_citations:
                self.fetching_citations.remove(paper_id)
            if not failed:
                self.citations_by_paper[paper_id] = entries
                self.citations_by_paper = dict(self.citations_by_paper)
                if paper_id not in self.fetched_citations:
                    self.fetched_citations.append(paper_id)
                self.fetched_citations = list(self.fetched_citations)
            self.fetching_citations = list(self.fetching_citations)

        if failed:
            yield rx.toast(
                "Citation lookup failed for this paper.", duration=3000
            )

    @rx.event
    def add_citation_paper(self, paper_id: str, index: int):
        run_index = self._current_index()
        if run_index < 0:
            return
        entries = self.citations_by_paper.get(paper_id, [])
        if index < 0 or index >= len(entries):
            return
        entry = entries[index]
        new_id = str(entry["arxiv_id"])
        if not new_id:
            return
        papers = self.runs[run_index]["papers"]
        if any(p["arxiv_id"] == new_id for p in papers):
            return rx.toast(
                "That paper is already in this workspace.", duration=2500
            )
        source_score = 0.0
        for paper in papers:
            if paper["arxiv_id"] == paper_id:
                source_score = float(paper["relevance_score"])
        authors = [a.strip() for a in str(entry["authors"]).split(",") if a]
        note = (
            "Retrieved via reference citation chaining."
            if entry["kind"] == "reference"
            else "Retrieved via forward citation chaining."
        )
        papers.append(
            PaperItem(
                arxiv_id=new_id,
                title=str(entry["title"]),
                authors=authors,
                author_line=str(entry["authors"]),
                summary=note,
                published=str(entry["year"]),
                pdf_url="",
                abs_url=f"https://arxiv.org/abs/{new_id}",
                primary_category="cs.AI",
                relevance_score=round(source_score * 0.9, 3),
                status="unreviewed",
                note="",
            )
        )
        self.runs = list(self.runs)
        return rx.toast(f"Added {new_id} to the workspace.", duration=2500)

    @rx.event
    def clear_workspace(self):
        self._reset()
