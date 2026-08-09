import reflex as rx

from app.components.force_graph import force_graph_2d
from app.states.graph_state import GraphEdgeUI, GraphNodeUI, GraphState


def control_button(
    icon: str, label: str, on_click: rx.event.EventType
) -> rx.Component:
    return rx.el.button(
        rx.icon(icon, class_name="h-[14px] w-[14px]"),
        on_click=on_click,
        title=label,
        class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--card)] text-[var(--foreground)] transition-all duration-150 hover:bg-[var(--accent)] hover:text-[var(--accent-foreground)] focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
    )


def layout_button(value: str, label: str) -> rx.Component:
    return rx.el.button(
        label,
        on_click=lambda: GraphState.set_layout_mode(value),
        class_name=rx.cond(
            GraphState.layout_mode == value,
            "h-[26px] rounded-full bg-[var(--primary)] px-3 text-xs uppercase tracking-[0.08em] text-[var(--primary-foreground)] transition-all duration-150",
            "h-[26px] rounded-full px-3 text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)] transition-all duration-150 hover:text-[var(--foreground)]",
        ),
    )


def graph_toolbar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            layout_button("force", "Force"),
            layout_button("radial", "Radial"),
            class_name="flex items-center gap-1 rounded-full border border-[var(--border)] bg-[var(--secondary)] p-[3px]",
        ),
        rx.el.div(
            rx.el.span(
                GraphState.zoom_label,
                class_name="w-[42px] text-center text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)]",
            ),
            control_button("zoom-out", "Zoom out", GraphState.zoom_out),
            control_button("zoom-in", "Zoom in", GraphState.zoom_in),
            control_button("crosshair", "Reset view", GraphState.reset_view),
            control_button("refresh-cw", "Re-layout", GraphState.relayout),
            control_button(
                "download", "Download graph", GraphState.download_graph
            ),
            rx.cond(
                GraphState.fullscreen,
                control_button(
                    "minimize-2",
                    "Exit fullscreen",
                    GraphState.toggle_fullscreen,
                ),
                control_button(
                    "maximize-2", "Fullscreen", GraphState.toggle_fullscreen
                ),
            ),
            class_name="flex flex-wrap items-center gap-[6px]",
        ),
        class_name="flex shrink-0 flex-wrap items-center justify-between gap-4 pb-3",
    )


def legend_chip(
    label: str,
    swatch_class: str,
    active: rx.Var[bool],
    on_click: rx.event.EventType,
) -> rx.Component:
    return rx.el.button(
        rx.el.span(class_name=swatch_class),
        rx.el.span(label),
        on_click=on_click,
        class_name=rx.cond(
            active,
            "flex h-7 w-fit items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--card)] px-[10px] text-xs uppercase tracking-[0.08em] text-[var(--foreground)] transition-all duration-150 hover:bg-[var(--accent)] focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
            "flex h-7 w-fit items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--secondary)] px-[10px] text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)] line-through transition-all duration-150 hover:text-[var(--foreground)] focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
        ),
    )


def graph_legend() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                class_name="h-[11px] w-[11px] rounded-full bg-[var(--graph-paper)]"
            ),
            rx.el.span("papers"),
            class_name="flex w-fit items-center gap-2 text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)]",
        ),
        rx.el.div(
            rx.el.span(
                class_name="h-[9px] w-[9px] rounded-full bg-[var(--graph-concept)]"
            ),
            rx.el.span("concepts"),
            class_name="flex w-fit items-center gap-2 text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)]",
        ),
        legend_chip(
            "mentions",
            "h-[2px] w-4 rounded-full bg-[var(--graph-mentions)]",
            GraphState.show_mentions,
            GraphState.toggle_mentions,
        ),
        legend_chip(
            "similar",
            "h-[2px] w-4 rounded-full bg-[var(--graph-similar)]",
            GraphState.show_similar,
            GraphState.toggle_similar,
        ),
        class_name="flex shrink-0 flex-wrap items-center gap-4 border-t border-[var(--border)] pt-3",
    )


def edge_line(edge: GraphEdgeUI) -> rx.Component:
    return rx.el.div(
        class_name=edge["line_class"],
        style={
            "left": f"{edge['x']}px",
            "top": f"{edge['y']}px",
            "width": f"{edge['length']}px",
            "transform": f"rotate({edge['angle']}deg)",
            "transform-origin": "0 50%",
        },
    )


def node_dot(node: GraphNodeUI) -> rx.Component:
    return rx.el.button(
        rx.el.span(class_name=node["dot_class"]),
        rx.el.span(node["label"], class_name=node["label_class"]),
        on_click=lambda: GraphState.click_node(node["id"]),
        title=node["label"],
        class_name="absolute -translate-x-1/2 -translate-y-1/2 focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] rounded-full",
        style={
            "left": f"{node['x']}px",
            "top": f"{node['y']}px",
            "position": "absolute",
        },
    )


def graph_canvas() -> rx.Component:
    """Force-directed interactive graph canvas via react-force-graph-2d."""
    return rx.el.div(
        # Empty state — shown when no graph data is available yet
        rx.cond(
            GraphState.has_graph,
            # react-force-graph-2d renders a WebGL/Canvas element directly.
            # Drag, zoom, pan, and physics are all handled by the library in
            # the browser — no Python roundtrip for any of those interactions.
            force_graph_2d(
                graph_data=GraphState.fg_graph_data,
                # Sizing: fill the container minus some padding
                width=920,
                height=500,
                # Node appearance
                node_label="name",
                node_color="color",
                node_val="val",
                node_rel_size=4,
                # Link appearance
                link_color="color",
                link_width=1.5,
                link_directional_particles=2,
                link_directional_particle_speed=0.005,
                # Interaction
                enable_node_drag=True,
                enable_zoom_interaction=True,
                enable_pan_interaction=True,
                # Let physics settle quickly; 0 = always active
                cool_down_ticks=120,
                # Background matches the card token (transparent lets CSS show through)
                background_color="rgba(0,0,0,0)",
                # Python event callbacks
                on_node_click=GraphState.on_fg_node_click,
                on_node_hover=GraphState.on_fg_node_hover,
                on_node_drag_end=GraphState.on_fg_node_drag_end,
            ),
            # Placeholder while no graph data exists
            rx.el.div(
                rx.icon("share-2", class_name="h-8 w-8 text-[var(--muted-foreground)] mb-3"),
                rx.el.p(
                    "Run a search to generate the concept graph.",
                    class_name="text-sm text-[var(--muted-foreground)] text-center max-w-[260px]",
                ),
                class_name="flex flex-col items-center justify-center h-full w-full",
            ),
        ),
        class_name=rx.cond(
            GraphState.fullscreen,
            "ra-scroll min-h-0 w-full flex-1 overflow-auto rounded-[var(--radius-xl)] border border-[var(--border)] bg-[var(--card)]",
            "ra-scroll h-[520px] w-full min-w-[300px] overflow-hidden rounded-[var(--radius-xl)] border border-[var(--border)] bg-[var(--card)] max-[899px]:h-[380px]",
        ),
    )


def selection_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(
                f"{GraphState.selected_node['type']} node · {GraphState.selected_node['degree']} connections",
                class_name="text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)]",
            ),
            rx.el.p(
                GraphState.selected_node["label"],
                class_name="mt-1 break-words text-sm leading-snug text-[var(--foreground)]",
            ),
            rx.cond(
                GraphState.selected_node["type"] == "paper",
                rx.el.div(
                    rx.cond(
                        GraphState.selected_node["abs_url"] != "",
                        rx.el.a(
                            "Abstract",
                            href=GraphState.selected_node["abs_url"],
                            target="_blank",
                            class_name="text-xs text-[var(--link)] hover:underline",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        GraphState.selected_node["pdf_url"] != "",
                        rx.el.a(
                            "PDF",
                            href=GraphState.selected_node["pdf_url"],
                            target="_blank",
                            class_name="text-xs text-[var(--link)] hover:underline",
                        ),
                        rx.fragment(),
                    ),
                    rx.el.span(
                        GraphState.selected_node["id"],
                        class_name="text-xs text-[var(--muted-foreground)]",
                    ),
                    class_name="mt-2 flex flex-wrap items-center gap-3",
                ),
                rx.fragment(),
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.button(
            rx.icon("x", class_name="h-[14px] w-[14px]"),
            on_click=GraphState.clear_selection,
            title="Clear selection",
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--card)] text-[var(--foreground)] transition-all duration-150 hover:bg-[var(--accent)] hover:text-[var(--accent-foreground)] focus-visible:outline-hidden focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]",
        ),
        class_name="mt-3 flex shrink-0 items-start justify-between gap-3 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--secondary)] p-3",
    )


def graph_caption() -> rx.Component:
    return rx.el.p(
        f"{GraphState.paper_node_count} papers · {GraphState.concept_node_count} concepts · {GraphState.visible_edge_count} edges — click a paper node to open its PDF",
        class_name="shrink-0 pb-3 text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)]",
    )


def graph_empty() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "share-2",
                class_name="h-[18px] w-[18px] text-[var(--muted-foreground)]",
            ),
            class_name="mx-auto mb-4 grid h-11 w-11 place-items-center rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--card)]",
        ),
        rx.el.p(
            "The concept graph appears after a search.",
            class_name="mb-2 text-lg tracking-[-0.02em] text-[var(--foreground)]",
        ),
        rx.el.p(
            "Paper and concept nodes are mapped once a run completes.",
            class_name="mx-auto max-w-[380px] text-sm leading-relaxed text-[var(--muted-foreground)]",
        ),
        class_name="ra-dotgrid flex min-h-[260px] flex-col items-center justify-center rounded-[var(--radius-xl)] border border-dashed border-[var(--border)] p-8 text-center",
    )


def graph_panel() -> rx.Component:
    return rx.el.div(
        graph_caption(),
        graph_toolbar(),
        graph_canvas(),
        rx.cond(
            GraphState.selected_node_id != "",
            selection_panel(),
            rx.fragment(),
        ),
        graph_legend(),
        class_name=rx.cond(
            GraphState.fullscreen,
            "fixed inset-3 z-50 flex flex-col overflow-hidden rounded-[var(--radius-xl)] border border-[var(--border)] bg-[var(--background)] p-4 shadow-[var(--shadow-float)]",
            "flex w-full min-w-0 flex-col",
        ),
    )


def graph_tab() -> rx.Component:
    return rx.cond(GraphState.has_graph, graph_panel(), graph_empty())
