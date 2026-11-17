"""Deterministic, dependency-free layouts for the concept graph canvas.

The canvas is a fixed pixel coordinate space (see `CANVAS_W` / `CANVAS_H`);
zoom is applied in the UI with a CSS transform, so layout math never has to
know about the viewport.
"""

import logging
import math
import random

CANVAS_W: float = 960.0
CANVAS_H: float = 580.0
MARGIN: float = 56.0
MAX_NODES: int = 120


def _normalize(
    pos: dict[str, list[float]], width: float, height: float
) -> dict[str, tuple[float, float]]:
    if not pos:
        return {}
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = (max_x - min_x) or 1.0
    span_y = (max_y - min_y) or 1.0
    usable_w = width - 2 * MARGIN
    usable_h = height - 2 * MARGIN
    out: dict[str, tuple[float, float]] = {}
    for key, (x, y) in pos.items():
        nx = MARGIN + (x - min_x) / span_x * usable_w
        ny = MARGIN + (y - min_y) / span_y * usable_h
        out[key] = (round(nx, 2), round(ny, 2))
    return out


def _radial_positions(
    nodes: list[dict], width: float, height: float, seed: int
) -> dict[str, tuple[float, float]]:
    papers = [n for n in nodes if n.get("type") == "paper"]
    concepts = [n for n in nodes if n.get("type") != "paper"]
    cx, cy = width / 2, height / 2
    inner = min(width, height) * 0.20
    outer = min(width, height) * 0.40
    rotation = (seed % 12) * (math.pi / 6)
    pos: dict[str, list[float]] = {}

    for index, node in enumerate(papers):
        angle = rotation + 2 * math.pi * index / max(1, len(papers))
        pos[str(node["id"])] = [
            cx + inner * 1.35 * math.cos(angle),
            cy + inner * math.sin(angle),
        ]
    for index, node in enumerate(concepts):
        step = 2 * math.pi / max(1, len(concepts))
        angle = rotation + step * index + step / 2
        pos[str(node["id"])] = [
            cx + outer * 1.35 * math.cos(angle),
            cy + outer * math.sin(angle),
        ]
    return _normalize(pos, width, height)


def _force_positions(
    nodes: list[dict],
    edges: list[dict],
    width: float,
    height: float,
    seed: int,
) -> dict[str, tuple[float, float]]:
    rng = random.Random(1000 + seed)
    ids = [str(n["id"]) for n in nodes]
    count = len(ids)
    pos: dict[str, list[float]] = {
        node_id: [
            rng.uniform(0.15, 0.85) * width,
            rng.uniform(0.15, 0.85) * height,
        ]
        for node_id in ids
    }
    if count < 2:
        return _normalize(pos, width, height)

    known = set(ids)
    adjacency = [
        (str(e["source"]), str(e["target"]))
        for e in edges
        if str(e.get("source")) in known and str(e.get("target")) in known
    ]

    k = math.sqrt((width * height) / count)
    iterations = 220 if count <= 40 else (120 if count <= 80 else 70)
    temp = width / 9
    cooling = temp / (iterations + 1)

    for _ in range(iterations):
        disp: dict[str, list[float]] = {i: [0.0, 0.0] for i in ids}
        for a in range(count):
            for b in range(a + 1, count):
                ia, ib = ids[a], ids[b]
                dx = pos[ia][0] - pos[ib][0]
                dy = pos[ia][1] - pos[ib][1]
                dist = math.hypot(dx, dy) or 0.01
                repulse = (k * k) / dist
                ux, uy = dx / dist, dy / dist
                disp[ia][0] += ux * repulse
                disp[ia][1] += uy * repulse
                disp[ib][0] -= ux * repulse
                disp[ib][1] -= uy * repulse

        for source, target in adjacency:
            dx = pos[source][0] - pos[target][0]
            dy = pos[source][1] - pos[target][1]
            dist = math.hypot(dx, dy) or 0.01
            attract = (dist * dist) / k
            ux, uy = dx / dist, dy / dist
            disp[source][0] -= ux * attract
            disp[source][1] -= uy * attract
            disp[target][0] += ux * attract
            disp[target][1] += uy * attract

        for node_id in ids:
            dx, dy = disp[node_id]
            dist = math.hypot(dx, dy) or 0.01
            step = min(dist, temp)
            pos[node_id][0] += dx / dist * step
            pos[node_id][1] += dy / dist * step
        temp = max(temp - cooling, 0.01)

    return _normalize(pos, width, height)


def degrees(nodes: list[dict], edges: list[dict]) -> dict[str, int]:
    out = {str(n["id"]): 0 for n in nodes}
    for edge in edges:
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if source in out:
            out[source] += 1
        if target in out:
            out[target] += 1
    return out


_POSITION_CACHE: dict[str, dict[str, tuple[float, float]]] = {}


def positions(
    nodes: list[dict],
    edges: list[dict],
    mode: str,
    seed: int,
    width: float = CANVAS_W,
    height: float = CANVAS_H,
) -> dict[str, tuple[float, float]]:
    """Positions for every node, keyed by node id (memoized)."""
    try:
        capped = nodes[:MAX_NODES]
        node_ids = tuple(str(n.get("id")) for n in capped)
        edge_pairs = tuple((str(e.get("source")), str(e.get("target"))) for e in edges)
        cache_key = f"{node_ids}_{edge_pairs}_{mode}_{seed}_{width}_{height}"
        if cache_key in _POSITION_CACHE:
            return _POSITION_CACHE[cache_key]

        if mode == "radial":
            res = _radial_positions(capped, width, height, seed)
        else:
            res = _force_positions(capped, edges, width, height, seed)

        if len(_POSITION_CACHE) > 50:
            _POSITION_CACHE.clear()
        _POSITION_CACHE[cache_key] = res
        return res
    except Exception as e:
        logging.exception(f"Error: {e}")
        return {}
