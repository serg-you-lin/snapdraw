"""
framer/geometry.py
------------------
Le primitive geometriche di Framer, scritte sugli `Edge` di forge.

Un `Edge` (`forge.core.topology.edge.Edge`) porta `start` / `end` (endpoint già
arrotondati alla tolerance da forge) e `segment` (primitiva nativa: `LineSeg`,
`ArcSeg`, ...). Cornice e cartiglio sono fatti di segmenti dritti, quindi qui
si guardano solo i `LineSeg`.

Nessuna decisione semantica: trova rettangoli, misura contenimento, riconosce
un formato ISO. Chi decide "questa è la cornice" è `frame.py`.
"""

from __future__ import annotations

import math
from typing import List, Optional

from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize, unary_union

from forge.core.primitives.segments import LineSeg

from .model import BBox

ISO_RATIO = math.sqrt(2)          # ≈ 1.41421 — rapporto lato lungo / lato corto dei formati ISO
RATIO_TOLERANCE = 0.05            # ±5% sul rapporto
RECT_AREA_TOLERANCE = 0.02       # scarto max fra area del poligono e area del suo envelope
CONTAINMENT_MARGIN_FACTOR = 0.02  # margine sulla bbox, frazione del lato corto

# Formati ISO in mm (lato corto, lato lungo). Il disegno può essere in
# qualsiasi unità: il riconoscimento del formato è best-effort e assume mm.
_ISO_FORMATS = {
    "A0": (841.0, 1189.0),
    "A1": (594.0, 841.0),
    "A2": (420.0, 594.0),
    "A3": (297.0, 420.0),
    "A4": (210.0, 297.0),
    "A5": (148.0, 210.0),
}
_ISO_SIZE_TOLERANCE = 0.03        # ±3% sulle dimensioni nominali


class Rect:
    """Un rettangolo candidato: il poligono shapely e gli Edge che lo bordano."""

    def __init__(self, polygon: Polygon, edges: list):
        self.polygon = polygon
        self.edges = edges

    @property
    def bbox(self) -> BBox:
        return tuple(self.polygon.bounds)  # (xmin, ymin, xmax, ymax)

    @property
    def area(self) -> float:
        return self.polygon.area

    @property
    def long_side(self) -> float:
        minx, miny, maxx, maxy = self.polygon.bounds
        return max(maxx - minx, maxy - miny)

    @property
    def short_side(self) -> float:
        minx, miny, maxx, maxy = self.polygon.bounds
        return min(maxx - minx, maxy - miny)

    @property
    def ratio(self) -> float:
        s = self.short_side
        return (self.long_side / s) if s else 0.0


def line_edges(doc) -> list:
    """Gli Edge di doc.edges il cui segmento è un LineSeg."""
    return [e for e in doc.edges if isinstance(e.segment, LineSeg)]


def find_rectangles(doc) -> List[Rect]:
    """
    Trova i rettangoli chiusi nella geometria grezza.

    Fa il `polygonize` dell'unione nodata di tutti i LineSeg: gestisce con lo
    stesso passaggio il rettangolo disegnato come polilinea chiusa e quello
    fatto di 4 LINE separate. Tiene i poligoni che coincidono col proprio
    envelope (rettangoli axis-aligned) entro `RECT_AREA_TOLERANCE`.
    """
    edges = line_edges(doc)
    if len(edges) < 4:
        return []

    strings = [LineString([e.start, e.end]) for e in edges]
    merged = unary_union(strings)
    rects: List[Rect] = []

    seen: set = set()
    for poly in polygonize(merged):
        if poly.is_empty or poly.area <= 0:
            continue
        # `polygonize` restituisce il riquadro esterno con i pezzi interni come
        # buchi: si guarda solo l'anello esterno per decidere se è un rettangolo
        # e per raccogliere gli Edge che lo bordano.
        shell = Polygon(poly.exterior)
        env = shell.envelope
        if env.area <= 0:
            continue
        if abs(shell.area - env.area) / env.area > RECT_AREA_TOLERANCE:
            continue  # non è un rettangolo axis-aligned

        key = tuple(round(v, 3) for v in shell.bounds)
        if key in seen:
            continue
        seen.add(key)

        boundary = shell.exterior.buffer(_edge_match_tol(shell))
        owned = [e for e, s in zip(edges, strings) if boundary.contains(s)]
        rects.append(Rect(polygon=shell, edges=owned))

    return rects


def is_iso_ratio(rect: Rect, tolerance: float = RATIO_TOLERANCE) -> bool:
    """True se il rapporto dei lati è ≈ √2 (formati ISO)."""
    return abs(rect.ratio - ISO_RATIO) <= tolerance


def containment(rect: Rect, doc) -> float:
    """
    Frazione degli Edge esterni al rettangolo i cui endpoint stanno dentro la
    sua bbox (con un piccolo margine). 1.0 = il rettangolo racchiude tutto.
    """
    minx, miny, maxx, maxy = rect.polygon.bounds
    margin = rect.short_side * CONTAINMENT_MARGIN_FACTOR
    minx, miny, maxx, maxy = minx - margin, miny - margin, maxx + margin, maxy + margin

    owned = {id(e) for e in rect.edges}
    others = [e for e in doc.edges if id(e) not in owned]
    if not others:
        return 0.0

    def inside(pt) -> bool:
        return minx <= pt[0] <= maxx and miny <= pt[1] <= maxy

    n_in = sum(1 for e in others if inside(e.start) and inside(e.end))
    return n_in / len(others)


def iso_format(rect: Rect, tolerance: float = _ISO_SIZE_TOLERANCE) -> Optional[str]:
    """Formato ISO dedotto dalle dimensioni del rettangolo, o None. Assume mm."""
    short, long_ = rect.short_side, rect.long_side
    for name, (s_nom, l_nom) in _ISO_FORMATS.items():
        if (abs(short - s_nom) / s_nom <= tolerance
                and abs(long_ - l_nom) / l_nom <= tolerance):
            return name
    return None


def _edge_match_tol(poly: Polygon) -> float:
    """Tolleranza per decidere se un Edge giace sul bordo di un poligono."""
    minx, miny, maxx, maxy = poly.bounds
    return max(maxx - minx, maxy - miny) * 1e-4 + 1e-6
