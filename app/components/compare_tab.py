import reflex as rx

from app.states.compare_state import CompareState, PaperRef, RunOption


def run_select(
    label: str,
    value: rx.Var[str],
    on_change: rx.event.EventType,
    query: rx.Var[str],
) -> rx.Component:
    return rx.el.div(
        rx.el.label(
            label,
            class_name="mb-2 block text-xs uppercase tracking-[0.1em] text-[var(--muted-foreground)]",
        ),
        rx.el.div(
            rx.el.select(
                rx.foreach(
                    CompareState.options,
                    lambda option: rx.el.option(
                        option["label"], value=option["id"]
                    ),
                ),
                value=value,
                on_change=on_change,
                class_name="h-9 w-full appearance-none rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--card)] pl-3 pr-8 text-sm text-[var(--foreground)] transition-all duration-150 hover:bg-[var(--accent)] focus:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
            ),
            rx.icon(
                "chevron-down",
                class_name="pointer-events-none absolute right-3 top-1/2 h-3 w-3 -translate-y-1/2 text-[var(--muted-foreground)]",
            ),
            class_name="relative w-full",
        ),
        rx.el.p(
            query,
            class_name="mt-2 line-clamp-2 text-xs leading-relaxed text-[var(--muted-foreground)]",
        ),
        class_name="w-full min-w-0",
    )


def metric_tile(label: str, value: rx.Var[int], accent: str) -> rx.Component:
    return rx.el.div(
        rx.el.p(
            label,
            class_name="text-xs uppercase tracking-[0.1em] text-[var(--muted-foreground)]",
        ),
        rx.el.p(value.to_string(), class_name=accent),
        class_name="w-full rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--card)] px-3 py-[12px]",
    )


def paper_ref_row(paper: PaperRef) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            paper["arxiv_id"],
            class_name="shrink-0 text-xs uppercase tracking-[0.06em] text-[var(--muted-foreground)]",
        ),
        rx.el.span(
            paper["title"],
            class_name="min-w-0 flex-1 break-words text-sm leading-snug text-[var(--foreground)]",
        ),
        class_name="flex items-start gap-3 border-t border-[var(--border)] px-3 py-[10px] first:border-t-0",
    )


def paper_ref_list(
    title: str, papers: rx.Var[list[PaperRef]], empty_copy: str
) -> rx.Component:
    return rx.el.div(
        rx.el.p(
            title,
            class_name="px-3 py-[9px] text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)]",
        ),
        rx.cond(
            papers.length() > 0,
            rx.el.div(
                rx.foreach(papers, paper_ref_row),
                class_name="border-t border-[var(--border)]",
            ),
            rx.el.p(
                empty_copy,
                class_name="border-t border-[var(--border)] px-3 py-[10px] text-xs leading-relaxed text-[var(--muted-foreground)]",
            ),
        ),
        class_name="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--secondary)]",
    )


def concept_tag(concept: str) -> rx.Component:
    return rx.el.span(
        concept,
        class_name="w-fit whitespace-nowrap rounded-full border border-[var(--border)] bg-[var(--card)] px-[9px] py-[3px] text-xs text-[var(--graph-concept)]",
    )


def shared_concepts_block() -> rx.Component:
    return rx.el.div(
        rx.el.p(
            f"Shared concepts · {CompareState.shared_concepts.length()}",
            class_name="mb-[10px] text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)]",
        ),
        rx.cond(
            CompareState.shared_concepts.length() > 0,
            rx.el.div(
                rx.foreach(CompareState.shared_concepts, concept_tag),
                class_name="flex flex-wrap items-center gap-2",
            ),
            rx.el.p(
                "These two runs share no concepts.",
                class_name="text-xs leading-relaxed text-[var(--muted-foreground)]",
            ),
        ),
        class_name="mt-3 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--card)] p-3",
    )


def compare_empty() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "columns-3",
                class_name="h-[18px] w-[18px] text-[var(--muted-foreground)]",
            ),
            class_name="mx-auto mb-4 grid h-11 w-11 place-items-center rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--card)]",
        ),
        rx.el.p(
            "Nothing to compare yet.",
            class_name="mb-2 text-lg tracking-[-0.02em] text-[var(--foreground)]",
        ),
        rx.el.p(
            "Run at least two searches to compare result sets, shared papers, and shared concepts.",
            class_name="mx-auto max-w-[380px] text-sm leading-relaxed text-[var(--muted-foreground)]",
        ),
        class_name="ra-dotgrid flex min-h-[260px] flex-col items-center justify-center rounded-[var(--radius-xl)] border border-dashed border-[var(--border)] p-8 text-center",
    )


def compare_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            run_select(
                "Run A",
                CompareState.value_a,
                CompareState.set_run_a,
                CompareState.query_a,
            ),
            run_select(
                "Run B",
                CompareState.value_b,
                CompareState.set_run_b,
                CompareState.query_b,
            ),
            class_name="grid w-full grid-cols-1 gap-4 min-[640px]:grid-cols-2",
        ),
        rx.el.div(
            metric_tile(
                "Shared papers",
                CompareState.shared_count,
                "mt-1 text-2xl text-[var(--graph-paper)]",
            ),
            metric_tile(
                "Unique to A",
                CompareState.only_a_count,
                "mt-1 text-2xl text-[var(--foreground)]",
            ),
            metric_tile(
                "Unique to B",
                CompareState.only_b_count,
                "mt-1 text-2xl text-[var(--foreground)]",
            ),
            class_name="mt-4 grid w-full grid-cols-1 gap-3 min-[520px]:grid-cols-3",
        ),
        rx.el.div(
            paper_ref_list(
                "Papers in both",
                CompareState.shared_papers,
                "No papers overlap between these runs.",
            ),
            class_name="mt-4",
        ),
        rx.el.div(
            paper_ref_list(
                "Unique to run A",
                CompareState.only_a_papers,
                "Every paper in run A also appears in run B.",
            ),
            paper_ref_list(
                "Unique to run B",
                CompareState.only_b_papers,
                "Every paper in run B also appears in run A.",
            ),
            class_name="mt-3 grid w-full grid-cols-1 gap-3 min-[900px]:grid-cols-2",
        ),
        shared_concepts_block(),
        class_name="flex w-full min-w-0 flex-col",
    )


def compare_tab() -> rx.Component:
    return rx.cond(CompareState.pair_ready, compare_panel(), compare_empty())
