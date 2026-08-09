import reflex as rx

config = rx.Config(
    app_name="rezno",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(theme=rx.theme(appearance="light")),
    ],
)
