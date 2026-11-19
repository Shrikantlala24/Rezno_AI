import reflex as rx

from app.states.conversation_state import ConversationState
from app.states.workspace_state import WorkspaceState


def section_label(text: str) -> rx.Component:
    return rx.el.p(
        text,
        class_name="mb-[10px] mt-4 text-xs uppercase tracking-[0.11em] text-[var(--muted-foreground)] first:mt-0",
    )


def help_text(text: str) -> rx.Component:
    return rx.el.p(
        text,
        class_name="mt-[6px] text-xs leading-relaxed text-[var(--muted-foreground)]",
    )


def slider_row(
    label: str,
    value: rx.Var[int],
    minimum: str,
    maximum: str,
    step: str,
    on_change: rx.event.EventType,
    hint: str,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.label(
                label,
                class_name="text-sm text-[var(--foreground)]",
            ),
            rx.el.span(
                value.to_string(),
                class_name="text-sm text-[var(--muted-foreground)]",
            ),
            class_name="mb-2 flex items-center justify-between gap-3",
        ),
        rx.el.input(
            type="range",
            min=minimum,
            max=maximum,
            step=step,
            default_value=value.to_string(),
            on_change=on_change.throttle(300),
            class_name="h-[6px] w-full cursor-pointer appearance-none rounded-full bg-[var(--secondary)] accent-[var(--primary)]",
        ),
        help_text(hint),
        class_name="mb-4",
    )


def length_button(value: str, label: str) -> rx.Component:
    return rx.el.button(
        label,
        on_click=lambda: ConversationState.set_response_length(value),
        class_name=rx.cond(
            ConversationState.response_length == value,
            "h-8 flex-1 rounded-full bg-[var(--primary)] text-xs uppercase tracking-[0.08em] text-[var(--primary-foreground)] transition-all duration-150",
            "h-8 flex-1 rounded-full text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)] transition-all duration-150 hover:text-[var(--foreground)]",
        ),
    )


def response_section() -> rx.Component:
    return rx.el.div(
        section_label("Response"),
        rx.el.div(
            length_button("brief", "Brief"),
            length_button("standard", "Standard"),
            length_button("detailed", "Detailed"),
            class_name="flex items-center gap-1 rounded-full border border-[var(--border)] bg-[var(--secondary)] p-[3px]",
        ),
        rx.match(
            ConversationState.response_length,
            ("brief", help_text("1–2 sentences · tight evidence.")),
            ("detailed", help_text("5–8 sentences · expanded evidence.")),
            help_text("3–5 sentences · balanced evidence."),
        ),
    )


def stat_tile(label: str, value: rx.Var[int]) -> rx.Component:
    return rx.el.div(
        rx.el.p(
            label,
            class_name="text-xs uppercase tracking-[0.1em] text-[var(--muted-foreground)]",
        ),
        rx.el.p(
            value.to_string(),
            class_name="mt-1 text-xl text-[var(--foreground)]",
        ),
        class_name="w-full rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--card)] px-3 py-[10px]",
    )


def citation_ids_block() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon(
                "chevron-right",
                class_name=rx.cond(
                    WorkspaceState.show_citation_ids,
                    "h-3 w-3 rotate-90 transition-transform duration-150",
                    "h-3 w-3 transition-transform duration-150",
                ),
            ),
            rx.el.span(
                f"Citation IDs · {WorkspaceState.citation_ids.length()}"
            ),
            on_click=WorkspaceState.toggle_citation_ids,
            class_name="flex w-full items-center gap-2 px-3 py-[9px] text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)] transition-all duration-150 hover:bg-[var(--accent)] hover:text-[var(--accent-foreground)] focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
        ),
        rx.cond(
            WorkspaceState.show_citation_ids,
            rx.el.div(
                rx.foreach(
                    WorkspaceState.citation_ids,
                    lambda citation_id: rx.el.p(
                        citation_id,
                        class_name="text-xs leading-relaxed text-[var(--foreground)]",
                    ),
                ),
                class_name="ra-scroll max-h-[140px] overflow-y-auto border-t border-[var(--border)] px-3 py-2",
            ),
            rx.fragment(),
        ),
        class_name="mt-3 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--secondary)]",
    )


def session_section() -> rx.Component:
    return rx.el.div(
        section_label("Session"),
        rx.el.div(
            stat_tile("Messages", ConversationState.message_count),
            stat_tile("Runs", WorkspaceState.run_count),
            class_name="grid grid-cols-2 gap-2",
        ),
        rx.cond(
            WorkspaceState.citation_ids.length() > 0,
            citation_ids_block(),
            rx.fragment(),
        ),
        rx.el.button(
            rx.icon("trash-2", class_name="h-[14px] w-[14px]"),
            rx.el.span("Clear session"),
            on_click=ConversationState.clear_session,
            class_name="mt-3 flex h-9 w-full items-center justify-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--card)] text-sm text-[var(--foreground)] transition-all duration-150 hover:bg-[var(--accent)] hover:text-[var(--accent-foreground)] focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
        ),
    )


def settings_popover() -> rx.Component:
    return rx.popover.root(
        rx.popover.trigger(
            rx.el.button(
                rx.icon("settings", class_name="h-4 w-4"),
                title="Research settings",
                class_name="flex h-9 w-9 items-center justify-center rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--card)] text-[var(--foreground)] transition-all duration-150 hover:bg-[var(--accent)] hover:text-[var(--accent-foreground)] focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
            ),
        ),
        rx.popover.content(
            rx.el.div(
                rx.el.p(
                    "Settings",
                    class_name="text-sm font-medium tracking-[-0.01em] text-[var(--foreground)]",
                ),
                rx.el.p(
                    "research controls · response · session",
                    class_name="mt-1 text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)]",
                ),
                section_label("Pipeline controls"),
                slider_row(
                    "Papers per query",
                    ConversationState.per_query,
                    "10",
                    "150",
                    "10",
                    ConversationState.set_per_query.debounce(200),
                    "Candidate retrieval depth for every generated query.",
                ),
                slider_row(
                    "Ranking top-k",
                    ConversationState.top_k,
                    "5",
                    "50",
                    "5",
                    ConversationState.set_top_k.debounce(200),
                    "Number of papers retained after ranking.",
                ),
                slider_row(
                    "Query variants",
                    ConversationState.num_queries,
                    "1",
                    "6",
                    "1",
                    ConversationState.set_num_queries.debounce(200),
                    "Parallel formulations used to widen retrieval.",
                ),
                response_section(),
                session_section(),
                class_name="ra-scroll max-h-[min(78vh,760px)] w-full overflow-y-auto",
            ),
            side="bottom",
            align="end",
            class_name="w-[390px] max-w-[calc(100vw-32px)] rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--popover)] p-4 text-[var(--popover-foreground)] shadow-[var(--shadow-float)]",
        ),
    )
