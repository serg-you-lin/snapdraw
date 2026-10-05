"""
snapdraw/geometry.py
--------------------
Le letture geometriche di snapdraw sugli `Edge` di forge: rettangoli di bordo,
contenimento, formato ISO, griglia di un cartiglio, densità di testo. La
geometria pura (rettangoli coperti da tratti, linee che attraversano un
rettangolo) è di forge, `forge.core.geometry.axis` (forge MAP.md D94); qui restano le
soglie di disegno e il significato.

Nessuna decisione semantica: chi decide "questa è la cornice" è `frame.py`.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from forge.core.geometry.axis import CoveredRectangle, covered_rectangles, items_inside, spanning_lines
from forge.core.primitives.segments import LineSeg

ISO_RATIO = math.sqrt(2)          # ≈ 1.41421 — rapporto lato lungo / lato corto dei formati ISO
RATIO_TOLERANCE = 0.05            # ±5% sul rapporto

BORDER_MIN_SIDE_FRACTION = 0.30   # un lato di cornice è lungo ≥ 30% della dimensione maggiore del disegno
AXIS_EPS = 0.5                    # mm — scarto per considerare una linea orizzontale / verticale
COORD_CLUSTER_TOL = 1.5          # mm — due bordi più vicini di così sono lo stesso bordo
SIDE_COVERAGE = 0.85            # frazione minima di un lato coperta da linee collineari
CONTAINMENT_MARGIN_FACTOR = 0.02  # margine sulla bbox, frazione del lato corto
MARK_TOUCH_TOL = 0.5              # mm — un segno parte dal lato del rettangolo se il suo capo ci sta entro questa distanza
MARK_MAX_FRACTION = 0.10          # una tacca è corta: al massimo questa frazione del lato corto del rettangolo
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
) -> List[CoveredRectangle]:
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

    Il lavoro geometrico è `forge.core.axis.covered_rectangles`.
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

    return list(covered_rectangles(edges, min_len, eps=AXIS_EPS, cluster_tolerance=COORD_CLUSTER_TOL,
                                   coverage=SIDE_COVERAGE))


# ---------------------------------------------------------------------------
# Misure
# ---------------------------------------------------------------------------

def is_iso_ratio(rect: CoveredRectangle, tolerance: float = RATIO_TOLERANCE) -> bool:
    """True se il rapporto dei lati è ≈ √2 (formati ISO)."""
    return abs(rect.ratio - ISO_RATIO) <= tolerance


def containment(rect: CoveredRectangle, doc) -> float:
    """
    Frazione degli Edge esterni al rettangolo i cui endpoint stanno dentro la
    sua bbox (con un piccolo margine). 1.0 = il rettangolo racchiude tutto.
    Una tacca — un edge corto che parte da un lato e va verso l'esterno — è
    un segno del rettangolo stesso (i riferimenti di una cornice): non conta
    (MAP D33).
    """
    owned = {id(e) for e in rect.items}
    others = [e for e in doc.edges if id(e) not in owned and not _is_tick(e, rect.bbox)]
    if not others:
        return 0.0
    margin = rect.short_side * CONTAINMENT_MARGIN_FACTOR
    return len(items_inside(rect.bbox, others, margin)) / len(others)


def marked_sides(bounds, edges, tol: float = MARK_TOUCH_TOL) -> set:
    """I lati di `bounds` da cui parte almeno una tacca (edge corto verso l'esterno)."""
    x0, y0, x1, y1 = bounds
    sides = set()
    for e in edges:
        if not _is_tick(e, bounds, tol):
            continue
        p = e.start if _on_side(e.start, bounds, tol) else e.end
        sides.update(n for n, d in (("left", abs(p[0] - x0)), ("right", abs(p[0] - x1)),
                                    ("bottom", abs(p[1] - y0)), ("top", abs(p[1] - y1))) if d <= tol)
    return sides


def _is_tick(edge, bounds, tol: float = MARK_TOUCH_TOL) -> bool:
    """Una tacca del rettangolo: parte da un lato, va fuori, ed è corta."""
    short = min(bounds[2] - bounds[0], bounds[3] - bounds[1])
    length = math.dist(edge.start, edge.end)
    return length <= MARK_MAX_FRACTION * short and _mark_outside(edge, bounds, tol)


def _on_side(p, bounds, tol: float) -> bool:
    x0, y0, x1, y1 = bounds
    inside = x0 - tol <= p[0] <= x1 + tol and y0 - tol <= p[1] <= y1 + tol
    return inside and min(abs(p[0] - x0), abs(p[0] - x1), abs(p[1] - y0), abs(p[1] - y1)) <= tol


def _mark_outside(edge, bounds, tol: float = MARK_TOUCH_TOL) -> bool:
    """Un capo dell'edge sta su un lato di `bounds`, l'altro fuori."""
    x0, y0, x1, y1 = bounds

    def outside(p):
        return p[0] < x0 - tol or p[0] > x1 + tol or p[1] < y0 - tol or p[1] > y1 + tol

    a, b = edge.start, edge.end
    return (_on_side(a, bounds, tol) and outside(b)) or (_on_side(b, bounds, tol) and outside(a))


def iso_format(rect: CoveredRectangle, tolerance: float = _ISO_SIZE_TOLERANCE) -> Optional[str]:
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


def grid_dividers(rect: CoveredRectangle, doc, coverage: float = GRID_COVERAGE) -> Tuple[List[float], List[float]]:
    """
    Linee dritte STRETTAMENTE interne a `rect` (bordo escluso) che lo
    attraversano per almeno `coverage` della larghezza/altezza — i divisori
    di riga/colonna di un rettangolo suddiviso in una griglia di celle (il
    segnale più forte di un cartiglio, DESIGN.md). Una sola riga di divisori
    (nessuna colonna, o viceversa) conta: il nostro stesso `generate.py`
    produce un cartiglio a righe piene, senza colonne.

    Ritorna `(row_ys, col_xs)`, ciascuna ordinata, bordo del rettangolo
    escluso. Il lavoro geometrico è `forge.core.axis.spanning_lines`.
    """
    return spanning_lines(rect.bbox, line_edges(doc), coverage=coverage, eps=AXIS_EPS,
                          cluster_tolerance=COORD_CLUSTER_TOL)


def annotation_density_ratio(rect: CoveredRectangle, doc) -> float:
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
