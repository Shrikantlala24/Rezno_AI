import reflex as rx

from app.states.conversation_state import Claim, ConversationState, Message


def avatar(role: rx.Var[str]) -> rx.Component:
    return rx.el.div(
        rx.cond(
            role == "user",
            rx.icon("user", class_name="h-[13px] w-[13px] text-white"),
            rx.icon("sparkles", class_name="h-[13px] w-[13px] text-[#5A3B00]"),
        ),
        class_name=rx.cond(
            role == "user",
            "mt-[3px] grid h-7 w-7 shrink-0 place-items-center rounded-full bg-[var(--mark-coral)]",
            "mt-[3px] grid h-7 w-7 shrink-0 place-items-center rounded-full bg-[#F3C778]",
        ),
    )


def user_bubble(message: Message) -> rx.Component:
    return rx.el.div(
        message["content"],
        class_name="inline-block max-w-full whitespace-pre-wrap break-words rounded-[14px] rounded-br-[4px] bg-[var(--primary)] px-3 py-[10px] text-sm leading-relaxed tracking-[-0.01em] text-[var(--primary-foreground)]",
    )


def unsourced_note(message: Message) -> rx.Component:
    return rx.el.p(
        rx.cond(
            message["is_fallback"],
            "LIVE WEB SEARCH · ROUTER FALLBACK · NOT FROM RETRIEVED PAPERS",
            "LIVE WEB SEARCH · NOT FROM RETRIEVED PAPERS",
        ),
        class_name="mt-3 text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)]",
    )


def claim_row(claim: Claim) -> rx.Component:
    return rx.el.div(
        rx.el.p(
            claim["claim"],
            class_name="text-sm font-semibold leading-snug text-[var(--foreground)]",
        ),
        rx.el.p(
            rx.el.span(
                claim["arxiv_id"],
                class_name="text-[var(--foreground)]",
            ),
            rx.el.span(" · "),
            rx.el.span(
                f"“{claim['supporting_sentence']}”",
                class_name="italic",
            ),
            class_name="mt-1 text-xs leading-relaxed text-[var(--muted-foreground)]",
        ),
        class_name="border-t border-[var(--border)] px-3 py-[10px] first:border-t-0",
    )


def evidence_block(message: Message) -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon(
                "chevron-right",
                class_name=rx.cond(
                    ConversationState.expanded_evidence.contains(message["id"]),
                    "h-3 w-3 rotate-90 transition-transform duration-150",
                    "h-3 w-3 transition-transform duration-150",
                ),
            ),
            rx.el.span(
                f"Evidence · {message['claims'].length()} supporting",
            ),
            rx.cond(
                message["claims"].length() == 1,
                rx.el.span("claim"),
                rx.el.span("claims"),
            ),
            on_click=lambda: ConversationState.toggle_evidence(message["id"]),
            class_name="flex w-full items-center gap-2 rounded-[var(--radius-md)] px-3 py-[9px] text-xs uppercase tracking-[0.07em] text-[var(--muted-foreground)] transition-all duration-150 hover:bg-[var(--accent)] hover:text-[var(--accent-foreground)] focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
        ),
        rx.cond(
            ConversationState.expanded_evidence.contains(message["id"]),
            rx.el.div(
                rx.foreach(message["claims"], claim_row),
                class_name="border-t border-[var(--border)]",
            ),
            rx.fragment(),
        ),
        class_name="mt-3 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--secondary)]",
    )


def error_notice(message: Message) -> rx.Component:
    return rx.el.div(
        rx.icon(
            "triangle-alert",
            class_name="mt-[2px] h-4 w-4 shrink-0 text-[var(--destructive)]",
        ),
        rx.el.div(
            rx.el.p(
                "Research run failed",
                class_name="text-sm font-semibold text-[var(--foreground)]",
            ),
            rx.el.p(
                message["content"],
                class_name="mt-1 text-sm leading-relaxed text-[var(--muted-foreground)]",
            ),
        ),
        class_name="flex gap-3 rounded-[var(--radius-lg)] border border-[var(--destructive)] bg-[var(--card)] p-3",
    )


def assistant_body(message: Message) -> rx.Component:
    return rx.el.div(
        rx.cond(
            message["is_error"],
            error_notice(message),
            rx.el.div(
                rx.markdown(message["content"], class_name="ra-md"),
                rx.cond(
                    message["is_unsourced"],
                    unsourced_note(message),
                    rx.cond(
                        message["claims"].length() > 0,
                        evidence_block(message),
                        rx.fragment(),
                    ),
                ),
            ),
        ),
        class_name="min-w-0 flex-1",
    )


def message_row(message: Message) -> rx.Component:
    return rx.el.div(
        avatar(message["role"]),
        rx.cond(
            message["role"] == "user",
            rx.el.div(
                user_bubble(message),
                class_name="min-w-0 flex-1",
            ),
            assistant_body(message),
        ),
        class_name="flex w-full gap-3 py-[10px] ra-fade-up",
    )


def progress_line(line: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            class_name="mt-[7px] h-[3px] w-[3px] shrink-0 rounded-full bg-[var(--muted-foreground)]"
        ),
        rx.el.span(line, class_name="min-w-0 break-words"),
        class_name="flex gap-2 py-[3px] text-xs leading-relaxed text-[var(--muted-foreground)]",
    )


def thinking_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="mt-[3px] grid h-7 w-7 shrink-0 place-items-center rounded-full bg-[#F3C778]"
        ),
        rx.el.div(
            rx.el.button(
                rx.el.div(
                    class_name="h-[13px] w-[13px] shrink-0 animate-spin rounded-full border-2 border-[var(--border)] border-t-[var(--foreground)]"
                ),
                rx.el.span(
                    ConversationState.thinking_label,
                    class_name="text-sm font-medium tracking-[-0.01em] text-[var(--foreground)]",
                ),
                rx.icon(
                    "chevron-right",
                    class_name=rx.cond(
                        ConversationState.thinking_open,
                        "ml-auto h-3 w-3 rotate-90 text-[var(--muted-foreground)] transition-transform duration-150",
                        "ml-auto h-3 w-3 text-[var(--muted-foreground)] transition-transform duration-150",
                    ),
                ),
                on_click=ConversationState.toggle_thinking_open,
                class_name="flex w-full items-center gap-[10px] px-3 py-[11px] text-left transition-all duration-150 hover:bg-[var(--accent)] focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
            ),
            rx.cond(
                ConversationState.thinking_open,
                rx.el.div(
                    rx.foreach(ConversationState.progress_log, progress_line),
                    id="ra-thinking-log",
                    class_name="ra-scroll max-h-[220px] overflow-y-auto border-t border-[var(--border)] px-3 py-2",
                ),
                rx.fragment(),
            ),
            class_name="min-w-0 flex-1 overflow-hidden rounded-[var(--radius-xl)] border border-[var(--border)] bg-[var(--card)] shadow-[var(--shadow-float)]",
        ),
        class_name="flex w-full gap-3 py-[10px] ra-fade-up",
    )


def message_list() -> rx.Component:
    return rx.el.div(
        rx.foreach(
            ConversationState.messages,
            lambda message: rx.el.div(
                message_row(message),
                key=message["id"],
            ),
        ),
        rx.cond(ConversationState.is_thinking, thinking_card(), rx.fragment()),
        class_name="flex w-full flex-col pb-2 pt-1",
    )
