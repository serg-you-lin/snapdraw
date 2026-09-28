"""
snapdraw/geometry.py
--------------------
Le primitive geometriche di snapdraw, scritte sugli `Edge` di forge.

Un `Edge` (`forge.core.topology.edge.Edge`) porta `start` / `end` (endpoint già
arrotondati alla tolerance da forge) e `segment` (primitiva nativa: `LineSeg`,
`ArcSeg`, ...). Cornice e cartiglio sono fatti di segmenti dritti, quindi qui
si guardano solo i `LineSeg`.

Nessuna decisione semantica: trova rettangoli di bordo, misura contenimento,
riconosce un formato ISO. Chi decide "questa è la cornice" è `frame.py`.

Il rilevamento rettangoli **non** usa `polygonize`: su un disegno reale il bordo
della cornice è coperto di tacche di graduazione (le zone A/B/C/1/2/3) che
spezzano ogni faccia pulita — `polygonize` restituisce un poligono da 45 punti
con 13 buchi, non un rettangolo. Si cercano invece i **lati** direttamente:
linee axis-aligned lunghe almeno una frazione della dimensione del disegno, che
coprono per intero i quattro lati di un rettangolo. Così una cornice a doppio
bordo dà due rettangoli, non zero.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from shapely.geometry import box

from forge.core.primitives.segments import LineSeg

from .model import BBox

ISO_RATIO = math.sqrt(2)          # ≈ 1.41421 — rapporto lato lungo / lato corto dei formati ISO
RATIO_TOLERANCE = 0.05            # ±5% sul rapporto

BORDER_MIN_SIDE_FRACTION = 0.30   # un lato di cornice è lungo ≥ 30% della dimensione maggiore del disegno
AXIS_EPS = 0.5                    # mm — scarto per considerare una linea orizzontale / verticale
COORD_CLUSTER_TOL = 1.5          # mm — due bordi più vicini di così sono lo stesso bordo
SIDE_COVERAGE = 0.85            # frazione minima di un lato coperta da linee collineari
CONTAINMENT_MARGIN_FACTOR = 0.02  # margine sulla bbox, frazione del lato corto
TEXT_BORDER_TOL = 0.5            # mm — un testo sul bordo di un rettangolo conta come dentro

# Formati ISO in mm (lato corto, lato lungo). Il disegno può essere in
# qualsiasi unità: il riconoscimento del formato è best-effort e assume mm.
# `margin`: quanto il riquadro di squadratura rientra dal bordo carta (per lato).
_ISO_FORMATS = {
    "A0": (841.0, 1189.0),
    "A1": (594.0, 841.0),
    "A2": (420.0, 594.0),
    "A3": (297.0, 420.0),
    "A4": (210.0, 297.0),
    "A5": (148.0, 210.0),
}
_ISO_SIZE_TOLERANCE = 0.03        # ±3% sulle dimensioni nominali
_ISO_MARGINS = (0.0, 5.0, 10.0, 20.0, 25.0)   # rientri tipici del riquadro di squadratura


class Rect:
    """Un rettangolo candidato: il poligono shapely e gli Edge che lo bordano."""

    def __init__(self, polygon, edges: list):
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


# ---------------------------------------------------------------------------
# Rilevamento rettangoli di bordo
# ---------------------------------------------------------------------------

def find_rectangles(
    doc,
    min_side_fraction: float = BORDER_MIN_SIDE_FRACTION,
    min_side_length: Optional[float] = None,
) -> List[Rect]:
    """
    Trova i rettangoli axis-aligned "di bordo": quelli i cui quattro lati sono
    coperti da linee lunghe. Prende sia il riquadro esterno sia quello di
    squadratura di una cornice a doppio bordo.

    La soglia di lunghezza minima di un lato è, di norma, una frazione della
    dimensione del disegno (`min_side_fraction`) — funziona per la cornice,
    che per definizione occupa quasi tutto il foglio. Un cartiglio no: la sua
    dimensione assoluta (decine di mm) non scala con l'estensione del
    disegno, quindi un rettangolo piccolo può valere una frazione minuscola
    su un disegno grande. `min_side_length` (mm, assoluto) sostituisce la
    frazione quando è dato — lo usa `titleblock.py`.

    Non usa `polygonize` — vedi il docstring del modulo.
    """
    edges = line_edges(doc)
    if len(edges) < 4:
        return []

    if min_side_length is not None:
        min_len = min_side_length
    else:
        xs_all = [p[0] for e in edges for p in (e.start, e.end)]
        ys_all = [p[1] for e in edges for p in (e.start, e.end)]
        big = max(max(xs_all) - min(xs_all), max(ys_all) - min(ys_all))
        if big <= 0:
            return []
        min_len = big * min_side_fraction

    horiz, vert = _axis_lines(edges)
    long_h = [h for h in horiz if (h[2] - h[1]) >= min_len]
    long_v = [v for v in vert if (v[2] - v[1]) >= min_len]
    if len(long_h) < 2 or len(long_v) < 2:
        return []

    ys = _cluster_coords([h[3] for h in long_h])
    xs = _cluster_coords([v[3] for v in long_v])

    rects: List[Rect] = []
    seen: set = set()
    for i in range(len(ys)):
        for j in range(i + 1, len(ys)):
            y_lo, y_hi = ys[i], ys[j]
            for k in range(len(xs)):
                for m in range(k + 1, len(xs)):
                    x_lo, x_hi = xs[k], xs[m]
                    if not _sides_covered(x_lo, y_lo, x_hi, y_hi, horiz, vert):
                        continue
                    key = (round(x_lo, 1), round(y_lo, 1), round(x_hi, 1), round(y_hi, 1))
                    if key in seen:
                        continue
                    seen.add(key)
                    poly = box(x_lo, y_lo, x_hi, y_hi)
                    rects.append(Rect(polygon=poly, edges=_edges_on_border(x_lo, y_lo, x_hi, y_hi, edges)))
    return rects


def _axis_lines(edges, eps: float = AXIS_EPS):
    """
    Divide gli Edge dritti in orizzontali e verticali.

    horiz: (edge, x_lo, x_hi, y)   —  vert: (edge, y_lo, y_hi, x)
    """
    horiz, vert = [], []
    for e in edges:
        (x0, y0), (x1, y1) = e.start, e.end
        if abs(y0 - y1) <= eps and abs(x0 - x1) > eps:
            horiz.append((e, min(x0, x1), max(x0, x1), (y0 + y1) / 2.0))
        elif abs(x0 - x1) <= eps and abs(y0 - y1) > eps:
            vert.append((e, min(y0, y1), max(y0, y1), (x0 + x1) / 2.0))
    return horiz, vert


def _cluster_coords(values, tol: float = COORD_CLUSTER_TOL) -> List[float]:
    """Fonde coordinate più vicine di `tol` nel loro valore medio."""
    out: List[float] = []
    for v in sorted(values):
        if out and v - out[-1] <= tol:
            continue
        out.append(v)
    return out


def _coverage(segments: List[Tuple[float, float]], lo: float, hi: float) -> float:
    """Frazione di [lo, hi] coperta dall'unione degli intervalli `segments`."""
    if hi <= lo:
        return 0.0
    clipped = sorted(
        (max(lo, a), min(hi, b)) for a, b in segments if min(hi, b) > max(lo, a)
    )
    covered, cur = 0.0, None
    for a, b in clipped:
        if cur is None:
            cur = [a, b]
        elif a <= cur[1]:
            cur[1] = max(cur[1], b)
        else:
            covered += cur[1] - cur[0]
            cur = [a, b]
    if cur:
        covered += cur[1] - cur[0]
    return covered / (hi - lo)


def _sides_covered(x_lo, y_lo, x_hi, y_hi, horiz, vert, tol: float = 2 * AXIS_EPS) -> bool:
    """True se tutti e 4 i lati del rettangolo sono coperti ≥ SIDE_COVERAGE."""
    for y in (y_lo, y_hi):
        segs = [(h[1], h[2]) for h in horiz if abs(h[3] - y) <= tol]
        if _coverage(segs, x_lo, x_hi) < SIDE_COVERAGE:
            return False
    for x in (x_lo, x_hi):
        segs = [(v[1], v[2]) for v in vert if abs(v[3] - x) <= tol]
        if _coverage(segs, y_lo, y_hi) < SIDE_COVERAGE:
            return False
    return True


def _edges_on_border(x_lo, y_lo, x_hi, y_hi, edges, tol: float = 2 * AXIS_EPS) -> list:
    """
    Gli Edge che giacciono su uno dei 4 lati del rettangolo — i lati veri più
    le tacche di graduazione collineari (anche loro sono arredo di cornice).
    """
    owned = []
    for e in edges:
        (x0, y0), (x1, y1) = e.start, e.end
        on_h = abs(y0 - y1) <= tol and (abs((y0 + y1) / 2 - y_lo) <= tol or abs((y0 + y1) / 2 - y_hi) <= tol) \
            and min(x0, x1) >= x_lo - tol and max(x0, x1) <= x_hi + tol
        on_v = abs(x0 - x1) <= tol and (abs((x0 + x1) / 2 - x_lo) <= tol or abs((x0 + x1) / 2 - x_hi) <= tol) \
            and min(y0, y1) >= y_lo - tol and max(y0, y1) <= y_hi + tol
        if on_h or on_v:
            owned.append(e)
    return owned


# ---------------------------------------------------------------------------
# Misure
# ---------------------------------------------------------------------------

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
    """
    Formato ISO dedotto dalle dimensioni del rettangolo, o None. Assume mm.

    Confronta contro le dimensioni nominali del foglio **e** contro il foglio
    meno un rientro tipico del riquadro di squadratura (5, 10, 20, 25 mm per
    lato): un A2 con squadratura a 10 mm misura 574 × 400, non 594 × 420.
    """
    short, long_ = rect.short_side, rect.long_side
    for name, (s_nom, l_nom) in _ISO_FORMATS.items():
        for margin in _ISO_MARGINS:
            s_exp, l_exp = s_nom - 2 * margin, l_nom - 2 * margin
            if (abs(short - s_exp) / s_exp <= tolerance
                    and abs(long_ - l_exp) / l_exp <= tolerance):
                return name
    return None


# ---------------------------------------------------------------------------
# Griglia interna (cartiglio) e densità di annotazioni
# ---------------------------------------------------------------------------

GRID_COVERAGE = 0.85  # frazione minima di lato coperta da un divisore di riga/colonna


def grid_dividers(rect: Rect, doc, coverage: float = GRID_COVERAGE) -> Tuple[List[float], List[float]]:
    """
    Linee dritte STRETTAMENTE interne a `rect` (bordo escluso) che lo
    attraversano per almeno `coverage` della larghezza/altezza — i divisori
    di riga/colonna di un rettangolo suddiviso in una griglia di celle (il
    segnale più forte di un cartiglio, DESIGN.md). Una sola riga di divisori
    (nessuna colonna, o viceversa) conta: il nostro stesso `generate.py`
    produce un cartiglio a righe piene, senza colonne.

    Ritorna `(row_ys, col_xs)`, ciascuna ordinata, bordo del rettangolo
    escluso.
    """
    edges = line_edges(doc)
    horiz, vert = _axis_lines(edges)
    xmin, ymin, xmax, ymax = rect.bbox
    tol = 2 * AXIS_EPS

    row_ys = []
    for y in _cluster_coords([h[3] for h in horiz if ymin + tol < h[3] < ymax - tol]):
        segs = [(h[1], h[2]) for h in horiz if abs(h[3] - y) <= tol]
        if _coverage(segs, xmin, xmax) >= coverage:
            row_ys.append(y)

    col_xs = []
    for x in _cluster_coords([v[3] for v in vert if xmin + tol < v[3] < xmax - tol]):
        segs = [(v[1], v[2]) for v in vert if abs(v[3] - x) <= tol]
        if _coverage(segs, ymin, ymax) >= coverage:
            col_xs.append(x)

    return row_ys, col_xs


def annotation_density_ratio(rect: Rect, doc) -> float:
    """
    Quante volte più annotazioni per unità di area cadono dentro `rect`
    rispetto alla densità media dell'intero disegno (annotazioni + geometria,
    per una bbox totale robusta anche su un disegno senza testo fuori dal
    cartiglio). > 1 = più denso della media — un cartiglio impacchetta molto
    testo in poco spazio. 0 se il disegno non ha annotazioni o `rect` non ne
    contiene nessuna.
    """
    if not doc.annotations or rect.area <= 0:
        return 0.0

    # tolleranza sul bordo: un MTEXT agganciato a sinistra ha il punto
    # d'inserimento esattamente sul bordo (vedi titleblock._build_cells)
    minx, miny, maxx, maxy = rect.bbox
    t = TEXT_BORDER_TOL
    inside = sum(1 for a in doc.annotations
                 if minx - t <= a.position[0] <= maxx + t and miny - t <= a.position[1] <= maxy + t)
    if inside == 0:
        return 0.0

    xs = [a.position[0] for a in doc.annotations] + [p[0] for e in doc.edges for p in (e.start, e.end)]
    ys = [a.position[1] for a in doc.annotations] + [p[1] for e in doc.edges for p in (e.start, e.end)]
    total_area = (max(xs) - min(xs)) * (max(ys) - min(ys))
    if total_area <= 0:
        return 0.0

    global_density = len(doc.annotations) / total_area
    local_density = inside / rect.area
    return local_density / global_density
