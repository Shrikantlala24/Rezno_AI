import reflex as rx

from app.states.workspace_state import (
    CitationEntry,
    PaperItem,
    WorkspaceState,
)


def status_badge(paper: PaperItem) -> rx.Component:
    return rx.el.span(
        f"screening · {paper['status']}",
        class_name=rx.match(
            paper["status"],
            (
                "keep",
                "w-fit whitespace-nowrap rounded-full border border-[var(--border)] bg-[var(--secondary)] px-[9px] py-[3px] text-xs uppercase tracking-[0.08em] text-[var(--graph-paper)]",
            ),
            (
                "maybe",
                "w-fit whitespace-nowrap rounded-full border border-[var(--border)] bg-[var(--secondary)] px-[9px] py-[3px] text-xs uppercase tracking-[0.08em] text-[var(--mark-coral)]",
            ),
            (
                "skip",
                "w-fit whitespace-nowrap rounded-full border border-[var(--border)] bg-[var(--secondary)] px-[9px] py-[3px] text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)] line-through",
            ),
            "w-fit whitespace-nowrap rounded-full border border-[var(--border)] bg-[var(--secondary)] px-[9px] py-[3px] text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)]",
        ),
    )


def screening_button(paper: PaperItem, value: str, label: str) -> rx.Component:
    return rx.el.button(
        label,
        on_click=lambda: WorkspaceState.set_status(paper["arxiv_id"], value),
        class_name=rx.cond(
            paper["status"] == value,
            "h-8 rounded-full border border-[var(--primary)] bg-[var(--primary)] px-4 text-xs uppercase tracking-[0.08em] text-[var(--primary-foreground)] transition-all duration-150 focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
            "h-8 rounded-full border border-[var(--border)] bg-[var(--card)] px-4 text-xs uppercase tracking-[0.08em] text-[var(--foreground)] transition-all duration-150 hover:bg-[var(--accent)] hover:text-[var(--accent-foreground)] focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
        ),
    )


def citation_row(
    paper: PaperItem, entry: CitationEntry, index: int
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(
                entry["title"],
                class_name="text-sm leading-snug text-[var(--foreground)]",
            ),
            rx.el.p(
                rx.el.span(entry["year"]),
                rx.cond(
                    entry["authors"] != "",
                    rx.el.span(f" · {entry['authors']}"),
                    rx.fragment(),
                ),
                class_name="mt-1 text-xs text-[var(--muted-foreground)]",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.cond(
            entry["arxiv_id"] != "",
            rx.el.button(
                "Add",
                on_click=lambda: WorkspaceState.add_citation_paper(
                    paper["arxiv_id"], index
                ),
                class_name="h-8 shrink-0 rounded-full border border-[var(--border)] bg-[var(--card)] px-3 text-xs uppercase tracking-[0.08em] text-[var(--foreground)] transition-all duration-150 hover:bg-[var(--accent)] hover:text-[var(--accent-foreground)] focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
            ),
            rx.el.span(
                "no arxiv id",
                class_name="shrink-0 text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)]",
            ),
        ),
        class_name="flex items-start gap-3 border-t border-[var(--border)] px-3 py-[10px] first:border-t-0",
    )


def citation_group(paper: PaperItem, kind: str, label: str) -> rx.Component:
    return rx.el.div(
        rx.el.p(
            label,
            class_name="px-3 py-2 text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)]",
        ),
        rx.el.div(
            rx.foreach(
                WorkspaceState.citations_by_paper.get(paper["arxiv_id"], []),
                lambda entry, index: rx.cond(
                    entry["kind"] == kind,
                    citation_row(paper, entry, index),
                    rx.fragment(),
                ),
            ),
            class_name="border-t border-[var(--border)]",
        ),
        class_name="border-t border-[var(--border)] first:border-t-0",
    )


def citation_panel(paper: PaperItem) -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon(
                "chevron-right",
                class_name=rx.cond(
                    WorkspaceState.expanded_citations.contains(
                        paper["arxiv_id"]
                    ),
                    "h-3 w-3 rotate-90 transition-transform duration-150",
                    "h-3 w-3 transition-transform duration-150",
                ),
            ),
            rx.el.span("Citation chaining"),
            on_click=lambda: WorkspaceState.toggle_citations(paper["arxiv_id"]),
            class_name="flex w-full items-center gap-2 px-3 py-[9px] text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)] transition-all duration-150 hover:bg-[var(--accent)] hover:text-[var(--accent-foreground)] focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
        ),
        rx.cond(
            WorkspaceState.expanded_citations.contains(paper["arxiv_id"]),
            rx.el.div(
                rx.el.div(
                    rx.el.button(
                        rx.cond(
                            WorkspaceState.fetching_citations.contains(
                                paper["arxiv_id"]
                            ),
                            rx.el.div(
                                class_name="h-[13px] w-[13px] animate-spin rounded-full border-2 border-[var(--border)] border-t-[var(--foreground)]"
                            ),
                            rx.icon("link", class_name="h-[14px] w-[14px]"),
                        ),
                        rx.el.span(
                            rx.cond(
                                WorkspaceState.fetching_citations.contains(
                                    paper["arxiv_id"]
                                ),
                                "Fetching citation data…",
                                "Fetch references and citing papers",
                            )
                        ),
                        on_click=lambda: WorkspaceState.fetch_citations(
                            paper["arxiv_id"]
                        ),
                        disabled=WorkspaceState.fetching_citations.contains(
                            paper["arxiv_id"]
                        ),
                        class_name="flex h-9 items-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--card)] px-3 text-sm text-[var(--foreground)] transition-all duration-150 hover:bg-[var(--accent)] hover:text-[var(--accent-foreground)] focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] disabled:pointer-events-none disabled:opacity-50",
                    ),
                    rx.cond(
                        WorkspaceState.fetched_citations.contains(
                            paper["arxiv_id"]
                        ),
                        rx.fragment(),
                        rx.el.p(
                            "Pull references and forward citations from Semantic Scholar.",
                            class_name="mt-2 text-xs leading-relaxed text-[var(--muted-foreground)]",
                        ),
                    ),
                    class_name="px-3 py-3",
                ),
                rx.cond(
                    WorkspaceState.fetched_citations.contains(
                        paper["arxiv_id"]
                    ),
                    rx.cond(
                        WorkspaceState.citations_by_paper.get(
                            paper["arxiv_id"], []
                        ).length()
                        > 0,
                        rx.el.div(
                            citation_group(paper, "reference", "References"),
                            citation_group(paper, "citing", "Citing papers"),
                        ),
                        rx.el.p(
                            "No citation data available.",
                            class_name="border-t border-[var(--border)] px-3 py-3 text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)]",
                        ),
                    ),
                    rx.fragment(),
                ),
                class_name="border-t border-[var(--border)]",
            ),
            rx.fragment(),
        ),
        class_name="mt-3 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--secondary)]",
    )


def paper_meta(paper: PaperItem, index: int) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "file-text",
                    class_name="h-[15px] w-[15px] text-[var(--muted-foreground)]",
                ),
                class_name="grid h-7 w-7 shrink-0 place-items-center rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--secondary)]",
            ),
            rx.el.div(
                rx.el.p(
                    f"{index + 1} · {paper['primary_category']} · {paper['published']}",
                    class_name="mb-1 text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)]",
                ),
                rx.el.p(
                    paper["title"],
                    class_name="mb-[6px] break-words text-lg font-semibold leading-snug tracking-[-0.03em] text-[var(--foreground)]",
                ),
                rx.el.p(
                    paper["arxiv_id"],
                    class_name="text-xs text-[var(--muted-foreground)]",
                ),
                rx.el.p(
                    paper["author_line"],
                    class_name="text-xs leading-relaxed text-[var(--muted-foreground)]",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex min-w-0 flex-1 gap-[10px]",
        ),
        rx.el.span(
            f"{paper['relevance_score']:.3f}",
            class_name="shrink-0 pt-[2px] text-sm uppercase tracking-[0.04em] text-[var(--foreground)]",
        ),
        class_name="flex items-start justify-between gap-3",
    )


def paper_links(paper: PaperItem) -> rx.Component:
    return rx.el.div(
        rx.el.a(
            "Abstract",
            href=paper["abs_url"],
            target="_blank",
            class_name="text-xs text-[var(--link)] hover:underline",
        ),
        rx.el.span("·", class_name="text-xs text-[var(--muted-foreground)]"),
        rx.cond(
            paper["pdf_url"] != "",
            rx.el.a(
                "PDF",
                href=paper["pdf_url"],
                target="_blank",
                class_name="text-xs text-[var(--link)] hover:underline",
            ),
            rx.el.span(
                "PDF unavailable",
                class_name="text-xs text-[var(--muted-foreground)]",
            ),
        ),
        class_name="mt-[10px] flex items-center gap-[10px] border-t border-[var(--border)] pt-[10px]",
    )


def paper_body(paper: PaperItem, index: int) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            paper_meta(paper, index),
            paper_links(paper),
            class_name="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--card)] p-[14px]",
        ),
        rx.el.p(
            paper["summary"],
            class_name="mt-[10px] text-sm leading-relaxed text-[var(--foreground)]",
        ),
        rx.el.div(
            rx.el.div(
                screening_button(paper, "keep", "Keep"),
                screening_button(paper, "maybe", "Maybe"),
                screening_button(paper, "skip", "Skip"),
                class_name="flex flex-wrap items-center gap-2",
            ),
            status_badge(paper),
            class_name="mt-[12px] flex flex-wrap items-center justify-between gap-3",
        ),
        rx.el.input(
            placeholder="Add a short screening note…",
            default_value=paper["note"],
            on_change=lambda value: WorkspaceState.set_note(
                paper["arxiv_id"], value
            ),
            class_name="mt-[10px] h-9 w-full rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--card)] px-3 text-sm text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
        ),
        citation_panel(paper),
        class_name="border-t border-[var(--border)] p-[14px]",
    )


def paper_row(paper: PaperItem, index: int) -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon(
                "chevron-right",
                class_name=rx.cond(
                    WorkspaceState.expanded_papers.contains(paper["arxiv_id"]),
                    "h-3 w-3 shrink-0 rotate-90 transition-transform duration-150",
                    "h-3 w-3 shrink-0 transition-transform duration-150",
                ),
            ),
            rx.el.span(
                f"{index + 1}",
                class_name="shrink-0 text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)]",
            ),
            rx.el.span(
                paper["title"],
                class_name="min-w-0 flex-1 truncate text-left text-sm text-[var(--foreground)]",
            ),
            rx.cond(
                paper["status"] != "unreviewed",
                rx.el.span(
                    paper["status"],
                    class_name="shrink-0 text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)]",
                ),
                rx.fragment(),
            ),
            on_click=lambda: WorkspaceState.toggle_paper(paper["arxiv_id"]),
            class_name="flex w-full items-center gap-[10px] px-3 py-[11px] transition-all duration-150 hover:bg-[var(--accent)] focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
        ),
        rx.cond(
            WorkspaceState.expanded_papers.contains(paper["arxiv_id"]),
            paper_body(paper, index),
            rx.fragment(),
        ),
        class_name="overflow-hidden rounded-[var(--radius-xl)] border border-[var(--border)] bg-[var(--card)]",
    )


def papers_head() -> rx.Component:
    return rx.el.div(
        rx.el.p(
            f"{WorkspaceState.paper_count} papers · ranked evidence set · {WorkspaceState.kept_count} kept",
            class_name="text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)]",
        ),
        rx.el.button(
            rx.icon("download", class_name="h-[14px] w-[14px]"),
            rx.el.span("Download BibTeX"),
            on_click=WorkspaceState.download_bibtex,
            class_name="flex h-9 shrink-0 items-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--card)] px-3 text-sm text-[var(--foreground)] transition-all duration-150 hover:bg-[var(--accent)] hover:text-[var(--accent-foreground)] focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
        ),
        class_name="flex flex-wrap items-center justify-between gap-3 pb-3",
    )


def papers_empty() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "file-text",
                class_name="h-[18px] w-[18px] text-[var(--muted-foreground)]",
            ),
            class_name="mx-auto mb-4 grid h-11 w-11 place-items-center rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--card)]",
        ),
        rx.el.p(
            "No papers in this workspace yet.",
            class_name="mb-2 text-lg tracking-[-0.02em] text-[var(--foreground)]",
        ),
        rx.el.p(
            "Run a research question to populate the ranked evidence set.",
            class_name="mx-auto max-w-[380px] text-sm leading-relaxed text-[var(--muted-foreground)]",
        ),
        class_name="flex min-h-[260px] flex-col items-center justify-center rounded-[var(--radius-xl)] border border-[var(--border)] bg-[var(--card)] p-8 text-center",
    )


def papers_tab() -> rx.Component:
    return rx.cond(
        WorkspaceState.paper_count > 0,
        rx.el.div(
            papers_head(),
            rx.el.div(
                rx.foreach(
                    WorkspaceState.selected_papers,
                    lambda paper, index: rx.el.div(
                        paper_row(paper, index),
                        key=paper["arxiv_id"],
                    ),
                ),
                class_name="flex flex-col gap-3",
            ),
            class_name="flex w-full flex-col",
        ),
        papers_empty(),
    )
