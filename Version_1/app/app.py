import reflex as rx

from app.components.conversation_rail import conversation_rail
from app.components.header import header
from app.components.workspace_rail import workspace_rail


def index() -> rx.Component:
    return rx.el.div(
        rx.el.main(
            header(),
            rx.el.div(
                conversation_rail(),
                workspace_rail(),
                class_name="flex w-full flex-col gap-6 pt-4 min-[900px]:min-h-0 min-[900px]:flex-1 min-[900px]:flex-row min-[900px]:gap-8 min-[900px]:overflow-hidden",
            ),
            class_name="mx-auto flex w-full max-w-[1680px] flex-col px-4 pb-6 pt-[10px] min-[900px]:h-full min-[900px]:overflow-hidden min-[900px]:px-[26px] min-[900px]:pb-0",
        ),
        class_name="min-h-screen w-full bg-[var(--background)] text-[var(--foreground)] antialiased min-[900px]:h-screen min-[900px]:overflow-hidden",
    )


app = rx.App(
    stylesheets=["/tokens.css"],
)
app.add_page(index, route="/")
