import reflex as rx

from app.states.theme_state import ThemeState


def theme_toggle() -> rx.Component:
    return rx.el.button(
        rx.cond(
            ThemeState.dark,
            rx.icon("sun", class_name="h-4 w-4"),
            rx.icon("moon", class_name="h-4 w-4"),
        ),
        on_click=ThemeState.toggle_theme,
        title="Toggle theme",
        class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--card)] text-[var(--foreground)] transition-all duration-150 hover:bg-[var(--accent)] hover:text-[var(--accent-foreground)] focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
    )


def session_status() -> rx.Component:
    return rx.el.div(
        rx.el.span(
            class_name="h-[7px] w-[7px] rounded-full bg-[var(--graph-concept)]"
        ),
        rx.el.span("session active"),
        class_name="hidden items-center gap-2 text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)] min-[900px]:flex",
    )


def header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "flask-conical",
                    class_name="h-4 w-4 text-[var(--mark-coral)]",
                ),
                class_name="grid h-[30px] w-[30px] place-items-center rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--card)]",
            ),
            rx.el.div(
                rx.el.h1(
                    "Research Agent",
                    class_name="text-xl font-medium leading-none tracking-[-0.05em] text-[var(--foreground)]",
                ),
                rx.el.p(
                    "arXiv retrieval · ranking · synthesis · citation intelligence",
                    class_name="mt-2 text-xs uppercase tracking-[0.11em] text-[var(--muted-foreground)]",
                ),
            ),
            class_name="flex min-w-0 items-center gap-3",
        ),
        rx.el.div(
            session_status(),
            theme_toggle(),
            class_name="flex items-center gap-3",
        ),
        class_name="flex shrink-0 items-end justify-between gap-4 border-b border-[var(--border)] pb-4 pt-1",
    )
