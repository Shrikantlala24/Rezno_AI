import reflex as rx

from app.components.message_list import message_list
from app.states.conversation_state import ConversationState


def rail_head() -> rx.Component:
    return rx.el.div(
        rx.el.span(
            "Conversation",
            class_name="text-sm font-medium tracking-[-0.01em] text-[var(--foreground)]",
        ),
        rx.el.span(
            "grounded synthesis",
            class_name="whitespace-nowrap text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)]",
        ),
        class_name="flex shrink-0 items-baseline justify-between gap-3 border-b border-[var(--border)] pb-3",
    )


def step_pill(label: str) -> rx.Component:
    return rx.el.span(
        label,
        class_name="rounded-full border border-[var(--border)] bg-[var(--card)] px-3 py-[7px] text-xs uppercase tracking-[0.1em] text-[var(--foreground)]",
    )


def flow_steps() -> rx.Component:
    return rx.el.div(
        step_pill("retrieve"),
        rx.icon(
            "arrow-right", class_name="h-3 w-3 text-[var(--muted-foreground)]"
        ),
        step_pill("rank"),
        rx.icon(
            "arrow-right", class_name="h-3 w-3 text-[var(--muted-foreground)]"
        ),
        step_pill("synthesize"),
        rx.icon(
            "arrow-right", class_name="h-3 w-3 text-[var(--muted-foreground)]"
        ),
        step_pill("map"),
        class_name="flex flex-wrap items-center justify-center gap-2",
    )


def empty_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "search",
                    class_name="h-[18px] w-[18px] text-[var(--foreground)]",
                ),
                class_name="mx-auto mb-4 grid h-11 w-11 place-items-center rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--card)]",
            ),
            rx.el.h2(
                "What are you researching?",
                class_name="mb-3 text-2xl leading-tight tracking-[-0.05em] text-[var(--foreground)]",
            ),
            rx.el.p(
                "Ask a question. The agent generates search variants, retrieves and ranks papers, synthesizes the evidence, and maps the concepts around the result set.",
                class_name="mx-auto mb-5 max-w-[420px] text-sm leading-relaxed text-[var(--muted-foreground)]",
            ),
            flow_steps(),
            class_name="max-w-[440px] ra-fade-up",
        ),
        class_name="flex min-h-[38vh] items-center justify-center px-4 py-6 text-center",
    )


def composer() -> rx.Component:
    return rx.el.div(
        rx.el.p(
            "Ask a research question",
            class_name="mb-2 text-xs uppercase tracking-[0.1em] text-[var(--muted-foreground)]",
        ),
        rx.el.div(
            rx.el.textarea(
                placeholder="Ask a research question…",
                default_value=ConversationState.composer_text,
                on_change=ConversationState.set_composer_text.debounce(250),
                rows="4",
                class_name="min-h-[88px] w-full resize-y rounded-[var(--radius-md)] border-0 bg-[var(--secondary)] p-3 text-sm leading-relaxed text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:bg-[var(--card)] focus:outline-hidden focus:ring-1 focus:ring-[var(--border)]",
            ),
            rx.el.button(
                rx.cond(
                    ConversationState.is_thinking,
                    rx.el.div(
                        class_name="h-[14px] w-[14px] animate-spin rounded-full border-2 border-[var(--primary-foreground)]/40 border-t-[var(--primary-foreground)]"
                    ),
                    rx.icon("send", class_name="h-4 w-4"),
                ),
                rx.el.span(
                    rx.cond(ConversationState.is_thinking, "Working…", "Send")
                ),
                on_click=ConversationState.submit,
                disabled=ConversationState.is_thinking,
                class_name="mt-2 flex h-9 w-full items-center justify-center gap-2 rounded-full bg-[var(--primary)] text-sm font-medium text-[var(--primary-foreground)] transition-all duration-150 hover:opacity-90 focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] disabled:pointer-events-none disabled:opacity-50",
            ),
            class_name="rounded-[var(--radius-xl)] border border-[var(--border)] bg-[var(--card)] p-[10px] shadow-[var(--shadow-float)]",
        ),
        class_name="shrink-0 pt-3 max-[899px]:sticky max-[899px]:bottom-0 max-[899px]:bg-[var(--background)] max-[899px]:pb-2",
    )


def conversation_rail() -> rx.Component:
    return rx.el.section(
        rail_head(),
        rx.el.div(
            rx.cond(
                ConversationState.show_empty_state,
                empty_state(),
                message_list(),
            ),
            id="ra-conversation-scroll",
            class_name="ra-scroll min-h-0 flex-1 overflow-y-auto pr-2 max-[899px]:max-h-[60vh]",
        ),
        composer(),
        class_name="flex w-full min-w-0 flex-col min-[900px]:h-full min-[900px]:min-h-0 min-[900px]:w-[30%] min-[900px]:overflow-hidden",
    )
