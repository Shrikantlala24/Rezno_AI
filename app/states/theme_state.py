import reflex as rx


class ThemeState(rx.State):
    """Session-scoped light/dark theme. Light on first load."""

    dark: bool = False

    @rx.var
    def root_class(self) -> str:
        base = "min-h-screen w-full bg-[var(--background)] text-[var(--foreground)] antialiased min-[900px]:h-screen min-[900px]:overflow-hidden"
        return f"dark {base}" if self.dark else base

    @rx.event
    def toggle_theme(self):
        self.dark = not self.dark
