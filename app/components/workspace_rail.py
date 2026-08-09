import reflex as rx

from app.components.compare_tab import compare_tab
from app.components.graph_tab import graph_tab
from app.components.papers_tab import papers_tab
from app.components.settings_popover import settings_popover
from app.states.shell_state import ShellState
from app.states.workspace_state import WorkspaceState


def workspace_head() -> rx.Component:
    return rx.el.div(
        rx.el.span(
            "Research workspace",
            class_name="text-sm font-medium tracking-[-0.01em] text-[var(--foreground)]",
        ),
        rx.el.div(
            rx.el.span(
                "papers · graph · comparison",
                class_name="hidden text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)] min-[640px]:block",
            ),
            settings_popover(),
            class_name="flex items-center gap-3",
        ),
        class_name="flex shrink-0 items-center justify-between gap-3 pb-3",
    )


def status_banner() -> rx.Component:
    return rx.match(
        WorkspaceState.run_status,
        (
            "search_error",
            rx.el.div(
                rx.icon(
                    "triangle-alert",
                    class_name="h-4 w-4 shrink-0 text-[var(--destructive)]",
                ),
                rx.el.span(
                    "Search temporarily failed. Retry the question — no papers were returned.",
                    class_name="text-sm leading-relaxed text-[var(--foreground)]",
                ),
                class_name="mb-2 flex shrink-0 items-start gap-2 rounded-[var(--radius-lg)] border border-[var(--destructive)] bg-[var(--card)] px-3 py-[9px]",
            ),
        ),
        (
            "partial_results",
            rx.el.div(
                rx.icon(
                    "info",
                    class_name="h-4 w-4 shrink-0 text-[var(--muted-foreground)]",
                ),
                rx.el.span(
                    "Partial search results: at least one arXiv query failed.",
                    class_name="text-sm leading-relaxed text-[var(--foreground)]",
                ),
                class_name="mb-2 flex shrink-0 items-start gap-2 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--secondary)] px-3 py-[9px]",
            ),
        ),
        (
            "no_results",
            rx.el.div(
                rx.icon(
                    "info",
                    class_name="h-4 w-4 shrink-0 text-[var(--muted-foreground)]",
                ),
                rx.el.span(
                    "No papers found for this query.",
                    class_name="text-sm leading-relaxed text-[var(--foreground)]",
                ),
                class_name="mb-2 flex shrink-0 items-start gap-2 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--secondary)] px-3 py-[9px]",
            ),
        ),
        rx.fragment(),
    )


def run_counts() -> rx.Component:
    return rx.el.span(
        rx.el.strong(
            WorkspaceState.paper_count.to_string(),
            class_name="font-normal text-[var(--foreground)]",
        ),
        rx.el.span(" papers · "),
        rx.el.strong(
            WorkspaceState.node_count.to_string(),
            class_name="font-normal text-[var(--foreground)]",
        ),
        rx.el.span(" nodes · "),
        rx.el.strong(
            WorkspaceState.edge_count.to_string(),
            class_name="font-normal text-[var(--foreground)]",
        ),
        rx.el.span(" edges"),
        class_name="min-w-0 truncate",
    )


def run_selector() -> rx.Component:
    return rx.cond(
        WorkspaceState.run_count > 1,
        rx.el.div(
            rx.el.span(
                "Search Run:",
                class_name="shrink-0 text-xs font-medium uppercase tracking-[0.08em] text-[var(--muted-foreground)]",
            ),
            rx.el.select(
                rx.foreach(
                    WorkspaceState.run_options,
                    lambda option: rx.el.option(
                        option["label"],
                        value=option["id"],
                    ),
                ),
                value=WorkspaceState.selected_run_id,
                on_change=WorkspaceState.select_run,
                class_name="h-8 min-w-0 flex-1 truncate rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--card)] px-2 text-xs font-medium text-[var(--foreground)] focus:outline-hidden focus:ring-1 focus:ring-[var(--border)] cursor-pointer",
            ),
            class_name="mb-2 flex items-center gap-2 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--secondary)] p-2",
        ),
        rx.fragment(),
    )


def run_strip() -> rx.Component:
    return rx.el.div(
        status_banner(),
        run_selector(),
        rx.cond(
            WorkspaceState.has_run,
            rx.el.div(
                run_counts(),
                rx.el.span(
                    WorkspaceState.run_timestamp,
                    class_name="shrink-0",
                ),
                class_name="flex items-center justify-between gap-3 border-y border-[var(--border)] py-[9px] text-xs uppercase tracking-[0.07em] text-[var(--muted-foreground)]",
            ),
            rx.el.div(
                rx.el.span("no active research run"),
                rx.el.span("waiting"),
                class_name="flex items-center justify-between gap-3 border-y border-[var(--border)] py-[9px] text-xs uppercase tracking-[0.07em] text-[var(--muted-foreground)]",
            ),
        ),
        class_name="flex shrink-0 flex-col",
    )


def tab_button(tab: dict[str, str]) -> rx.Component:
    return rx.el.button(
        rx.el.span(tab["label"]),
        rx.el.span(
            class_name=rx.cond(
                ShellState.active_tab == tab["key"],
                "absolute inset-x-0 -bottom-px h-[2px] bg-[var(--foreground)]",
                "hidden",
            )
        ),
        on_click=lambda: ShellState.select_tab(tab["key"]),
        class_name=rx.cond(
            ShellState.active_tab == tab["key"],
            "relative px-3 pb-[10px] pt-2 text-sm font-medium text-[var(--foreground)] transition-colors duration-150",
            "relative px-3 pb-[10px] pt-2 text-sm text-[var(--muted-foreground)] transition-colors duration-150 hover:text-[var(--foreground)]",
        ),
    )


def tab_bar() -> rx.Component:
    return rx.el.div(
        rx.foreach(ShellState.tabs, tab_button),
        class_name="flex shrink-0 items-center gap-1 border-b border-[var(--border)]",
    )


def tab_content() -> rx.Component:
    return rx.el.div(
        rx.match(
            ShellState.active_tab,
            ("papers", papers_tab()),
            ("graph", graph_tab()),
            ("compare", compare_tab()),
            papers_tab(),
        ),
        class_name="ra-scroll min-h-0 w-full flex-1 overflow-y-auto py-4 pr-2 max-[899px]:max-h-[60vh]",
    )


def workspace_rail() -> rx.Component:
    return rx.el.section(
        workspace_head(),
        run_strip(),
        tab_bar(),
        tab_content(),
        class_name="flex w-full min-w-0 flex-1 flex-col min-[900px]:h-full min-[900px]:min-h-0 min-[900px]:w-[70%] min-[900px]:overflow-hidden",
    )
