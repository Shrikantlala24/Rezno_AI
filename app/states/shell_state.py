import reflex as rx


class ShellState(rx.State):
    """Layout-shell state: workspace tab selection."""

    active_tab: str = "papers"
    tabs: list[dict[str, str]] = [
        {"key": "papers", "label": "Papers"},
        {"key": "graph", "label": "Concept graph"},
        {"key": "compare", "label": "Compare"},
    ]

    @rx.event
    def select_tab(self, key: str):
        self.active_tab = key
