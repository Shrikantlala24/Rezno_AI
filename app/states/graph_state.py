"""Concept graph presentation state: layout, zoom, filters, selection."""

import json
import logging
from typing import TypedDict

import reflex as rx

from app.graph_layout import CANVAS_H, CANVAS_W, degrees, positions

_DOT_BASE = "block rounded-full border transition-all duration-150"
_LABEL_BASE = (
    "absolute left-[15px] top-1/2 -translate-y-1/2 max-w-[150px] truncate "
    "whitespace-nowrap text-xs transition-all duration-150"
)


class GraphNodeUI(TypedDict):
    id: str
    label: str
    type: str
    x: float
    y: float
    degree: int
    pdf_url: str
    abs_url: str
    dot_class: str
    label_class: str


class GraphEdgeUI(TypedDict):
    id: str
    x: float
    y: float
    length: float
    angle: float
    line_class: str


class SelectedNode(TypedDict):
    id: str
    label: str
    type: str
    degree: str
    pdf_url: str
    abs_url: str


class GraphState(rx.State):
    """View controls for the concept graph. Data lives in WorkspaceState."""

    layout_mode: str = "force"
    layout_seed: int = 0
    zoom: float = 1.0
    selected_node_id: str = ""
    hovered_node_id: str = ""
    show_mentions: bool = True
    show_similar: bool = True
    fullscreen: bool = False

    canvas_width: float = CANVAS_W
    canvas_height: float = CANVAS_H

    # ------------------------------------------------------------- data reads

    async def _graph_data(self) -> tuple[list[dict], list[dict], str]:
        """Raw nodes/edges of the active workspace run, plus its id."""
        from app.states.workspace_state import WorkspaceState

        try:
            workspace = await self.get_state(WorkspaceState)
            runs = workspace.runs
            if not runs:
                return [], [], ""
            run = runs[-1]
            for candidate in runs:
                if candidate["id"] == workspace.selected_run_id:
                    run = candidate
            run_id = str(run["id"])
            try:
                nodes = [dict(n) for n in list(run["nodes"])]
            except Exception as e:
                logging.exception(f"Error: {e}")
                nodes = []
            try:
                edges = [dict(e) for e in list(run["edges"])]
            except Exception as e:
                logging.exception(f"Error: {e}")
                edges = []
            return nodes, edges, run_id
        except Exception as e:
            logging.exception(f"Error: {e}")
            return [], [], ""

    def _visible_edges(self, edges: list[dict]) -> list[dict]:
        out: list[dict] = []
        for edge in edges:
            kind = str(edge.get("type", "MENTIONS")).upper()
            if kind == "SIMILAR_TO" and not self.show_similar:
                continue
            if kind != "SIMILAR_TO" and not self.show_mentions:
                continue
            out.append(edge)
        return out

    def _neighbors(self, edges: list[dict]) -> set[str]:
        if not self.selected_node_id:
            return set()
        found: set[str] = set()
        for edge in edges:
            source = str(edge.get("source", ""))
            target = str(edge.get("target", ""))
            if source == self.selected_node_id:
                found.add(target)
            if target == self.selected_node_id:
                found.add(source)
        return found

    # ---------------------------------------------------------- computed vars

    @rx.var
    async def has_graph(self) -> bool:
        nodes, _, _ = await self._graph_data()
        return len(nodes) > 0

    @rx.var
    async def paper_node_count(self) -> int:
        nodes, _, _ = await self._graph_data()
        return len([n for n in nodes if n.get("type") == "paper"])

    @rx.var
    async def concept_node_count(self) -> int:
        nodes, _, _ = await self._graph_data()
        return len([n for n in nodes if n.get("type") != "paper"])

    @rx.var
    async def visible_edge_count(self) -> int:
        _, edges, _ = await self._graph_data()
        return len(self._visible_edges(edges))

    @rx.var
    async def fg_graph_data(self) -> dict[str, list[dict]]:
        """Graph data in the { nodes, links } shape react-force-graph-2d expects."""
        nodes, all_edges, _ = await self._graph_data()
        if not nodes:
            return {"nodes": [], "links": []}

        edges = self._visible_edges(all_edges)
        from app.graph_layout import degrees
        degree_map = degrees(nodes, edges)

        # Node colours: paper = teal, concept = purple
        fg_nodes = []
        for n in nodes:
            node_id = str(n.get("id", ""))
            is_paper = n.get("type") == "paper"
            deg = int(degree_map.get(node_id, 0))
            fg_nodes.append({
                "id": node_id,
                "name": str(n.get("label", node_id)),
                "type": n.get("type", "concept"),
                "val": max(1, deg),        # controls relative node size
                "color": "#1a7a6e" if is_paper else "#7c5cbf",
                "pdf_url": str(n.get("pdf_url", "") or ""),
                "abs_url": str(n.get("abs_url", "") or ""),
            })

        # Link colours: mentions = teal, similar = purple
        fg_links = []
        for e in edges:
            kind = str(e.get("type", "MENTIONS")).upper()
            fg_links.append({
                "source": str(e.get("source", "")),
                "target": str(e.get("target", "")),
                "type": kind,
                "color": "rgba(26,122,110,0.5)" if kind != "SIMILAR_TO" else "rgba(124,92,191,0.4)",
            })

        return {"nodes": fg_nodes, "links": fg_links}

    # ------------------------------------------------- force-graph callbacks

    @rx.event
    async def on_fg_node_click(self, node: dict):
        """Called when the user clicks a node in the force graph."""
        node_id = str(node.get("id", "") if node else "")
        if not node_id:
            return
        # Reuse existing click_node logic (handles selection + PDF open)
        yield GraphState.click_node(node_id)

    @rx.event
    def on_fg_node_hover(self, node: dict | None):
        """Called when the user hovers over / leaves a node."""
        self.hovered_node_id = str(node.get("id", "") if node else "")

    @rx.event
    def on_fg_node_drag_end(self, node: dict):
        """Called when a drag gesture finishes (node position pinned by library)."""
        # Position is maintained by the JS physics engine; nothing to do in
        # Python state for now, but the handler is wired so it can be extended.
        pass

    @rx.var
    async def graph_nodes(self) -> list[GraphNodeUI]:
        nodes, all_edges, _ = await self._graph_data()
        if not nodes:
            return []
        edges = self._visible_edges(all_edges)
        placed = positions(
            nodes,
            edges,
            self.layout_mode,
            self.layout_seed,
            self.canvas_width,
            self.canvas_height,
        )
        degree_map = degrees(nodes, edges)
        neighbors = self._neighbors(all_edges)
        has_selection = bool(self.selected_node_id)

        out: list[GraphNodeUI] = []
        for node in nodes:
            node_id = str(node.get("id", ""))
            if node_id not in placed:
                continue
            x, y = placed[node_id]
            is_paper = node.get("type") == "paper"
            selected = node_id == self.selected_node_id
            related = node_id in neighbors
            dim = has_selection and not selected and not related

            if is_paper:
                color = "bg-[var(--graph-paper)] border-[var(--graph-paper)]"
                size = "h-[15px] w-[15px]"
            else:
                color = (
                    "bg-[var(--graph-concept)] border-[var(--graph-concept)]"
                )
                size = "h-[11px] w-[11px]"
            if selected:
                ring = " ring-[3px] ring-[var(--ring)] scale-125"
            elif related:
                ring = " ring-2 ring-[var(--border)]"
            else:
                ring = ""
            opacity = " opacity-20" if dim else ""

            label_tone = (
                "text-[var(--foreground)]"
                if selected or related or not has_selection
                else "text-[var(--muted-foreground)]"
            )
            label_weight = " font-semibold" if selected else ""
            label_opacity = " opacity-20" if dim else ""

            out.append(
                GraphNodeUI(
                    id=node_id,
                    label=str(node.get("label", "") or node_id),
                    type="paper" if is_paper else "concept",
                    x=x,
                    y=y,
                    degree=int(degree_map.get(node_id, 0)),
                    pdf_url=str(node.get("pdf_url", "") or ""),
                    abs_url=str(node.get("abs_url", "") or ""),
                    dot_class=f"{_DOT_BASE} {size} {color}{ring}{opacity}",
                    label_class=(
                        f"{_LABEL_BASE} {label_tone}"
                        f"{label_weight}{label_opacity}"
                    ),
                )
            )
        return out

    @rx.var
    async def graph_edges(self) -> list[GraphEdgeUI]:
        nodes, all_edges, _ = await self._graph_data()
        if not nodes:
            return []
        edges = self._visible_edges(all_edges)
        placed = positions(
            nodes,
            edges,
            self.layout_mode,
            self.layout_seed,
            self.canvas_width,
            self.canvas_height,
        )
        neighbors = self._neighbors(all_edges)
        has_selection = bool(self.selected_node_id)

        import math

        out: list[GraphEdgeUI] = []
        for index, edge in enumerate(edges):
            source = str(edge.get("source", ""))
            target = str(edge.get("target", ""))
            if source not in placed or target not in placed:
                continue
            x1, y1 = placed[source]
            x2, y2 = placed[target]
            length = math.hypot(x2 - x1, y2 - y1)
            angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
            kind = str(edge.get("type", "MENTIONS")).upper()
            color = (
                "bg-[var(--graph-similar)]"
                if kind == "SIMILAR_TO"
                else "bg-[var(--graph-mentions)]"
            )
            thickness = "h-[2px]" if kind == "SIMILAR_TO" else "h-[1.5px]"
            touched = source == self.selected_node_id or (
                target == self.selected_node_id
            )
            near = source in neighbors or target in neighbors
            if has_selection and not touched:
                opacity = " opacity-25" if near else " opacity-10"
            elif touched:
                opacity = " opacity-100"
            else:
                opacity = " opacity-70"
            out.append(
                GraphEdgeUI(
                    id=str(edge.get("id", f"e{index}")),
                    x=x1,
                    y=y1,
                    length=round(length, 2),
                    angle=round(angle, 3),
                    line_class=(
                        "absolute origin-left rounded-full "
                        f"{thickness} {color}{opacity}"
                    ),
                )
            )
        return out

    @rx.var
    async def selected_node(self) -> SelectedNode:
        empty = SelectedNode(
            id="", label="", type="", degree="0", pdf_url="", abs_url=""
        )
        if not self.selected_node_id:
            return empty
        nodes = await self.graph_nodes
        for node in nodes:
            if node["id"] == self.selected_node_id:
                return SelectedNode(
                    id=node["id"],
                    label=node["label"],
                    type=node["type"],
                    degree=str(node["degree"]),
                    pdf_url=node["pdf_url"],
                    abs_url=node["abs_url"],
                )
        return empty

    @rx.var
    def scaled_width(self) -> float:
        return round(self.canvas_width * self.zoom, 2)

    @rx.var
    def scaled_height(self) -> float:
        return round(self.canvas_height * self.zoom, 2)

    @rx.var
    def zoom_label(self) -> str:
        return f"{int(round(self.zoom * 100))}%"

    # --------------------------------------------------------------- events

    @rx.event
    def set_layout_mode(self, mode: str):
        self.layout_mode = mode

    @rx.event
    def relayout(self):
        self.layout_seed += 1

    @rx.event
    def zoom_in(self):
        self.zoom = min(round(self.zoom + 0.2, 2), 2.4)

    @rx.event
    def zoom_out(self):
        self.zoom = max(round(self.zoom - 0.2, 2), 0.6)

    @rx.event
    def reset_view(self):
        self.zoom = 1.0
        self.selected_node_id = ""

    @rx.event
    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen

    @rx.event
    def toggle_mentions(self):
        self.show_mentions = not self.show_mentions

    @rx.event
    def toggle_similar(self):
        self.show_similar = not self.show_similar

    @rx.event
    def clear_selection(self):
        self.selected_node_id = ""

    @rx.event
    async def click_node(self, node_id: str):
        if self.selected_node_id == node_id:
            self.selected_node_id = ""
            return
            
        self.selected_node_id = node_id
        nodes, _, _ = await self._graph_data()
        for node in nodes:
            if str(node.get("id", "")) != node_id:
                continue
            if node.get("type") != "paper":
                return
            url = str(node.get("pdf_url", "") or node.get("abs_url", "") or "")
            if url:
                return rx.call_script(
                    f"window.open('{url}', '_blank', 'noopener')"
                )
            return rx.toast("No PDF available for this paper.", duration=2500)

    @rx.event
    async def download_graph(self):
        nodes, edges, run_id = await self._graph_data()
        if not nodes:
            return rx.toast("No graph to export yet.", duration=2500)
        try:
            payload = json.dumps(
                {"run_id": run_id, "nodes": nodes, "edges": edges}, indent=2
            )
        except Exception as e:
            logging.exception(f"Error: {e}")
            return rx.toast("Graph export failed.", duration=3000)
        return rx.download(
            data=payload, filename=f"concept_graph_{run_id or 'run'}.json"
        )
