"""Reflex custom component wrapping react-force-graph-2d.

react-force-graph-2d renders a WebGL/Canvas 2D force-directed graph.
Physics (node repulsion, edge springs, drag, zoom, pan) runs entirely
in the browser at 60fps — no Python roundtrip for layout updates.

Reflex will automatically install the npm package when it compiles the
.web directory. No manual npm install needed.
"""

from typing import Any

import reflex as rx


class ForceGraph2D(rx.Component):
    """Wraps the default export from react-force-graph-2d."""

    library = "react-force-graph-2d"
    tag = "ForceGraph2D"
    is_default = True

    # ------------------------------------------------------------------ data
    # Expected shape: { nodes: [{id, name, color, val, ...}],
    #                   links: [{source, target, color, ...}] }
    graph_data: rx.Var[dict[str, list[dict[str, Any]]]]

    # ---------------------------------------------------------------- sizing
    width: rx.Var[int]
    height: rx.Var[int]

    # ----------------------------------------------------------- node styling
    # JS accessor string: which field on a node object gives the label
    node_label: rx.Var[str]
    # JS accessor string: which field gives the node colour
    node_color: rx.Var[str]
    # JS accessor string: which field gives the relative node size
    node_val: rx.Var[str]
    # Base node radius multiplier
    node_rel_size: rx.Var[int]

    # ----------------------------------------------------------- link styling
    link_color: rx.Var[str]
    link_width: rx.Var[float]
    # Animated particles flowing along edges (0 = none)
    link_directional_particles: rx.Var[int]
    link_directional_particle_speed: rx.Var[float]

    # ---------------------------------------------------- interaction toggles
    enable_node_drag: rx.Var[bool]
    enable_zoom_interaction: rx.Var[bool]
    enable_pan_interaction: rx.Var[bool]
    # Cool-down: how many ticks before the simulation freezes
    cool_down_ticks: rx.Var[int]

    # ------------------------------------------------- background (optional)
    background_color: rx.Var[str]

    # ------------------------------------------------------ event callbacks
    # Each handler receives the raw JS node/link object as a dict.
    # Reflex serialises it and delivers it to the matching @rx.event method.
    on_node_click: rx.EventHandler[lambda node, event: [node]]
    on_node_hover: rx.EventHandler[lambda node, prev_node: [node]]
    on_node_drag_end: rx.EventHandler[lambda node, translate, event: [node]]
    on_link_click: rx.EventHandler[lambda link, event: [link]]


# Convenience factory (matches the naming pattern used in other components)
force_graph_2d = ForceGraph2D.create
