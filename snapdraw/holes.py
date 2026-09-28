"""
snapdraw/holes.py
-----------------
I fori della vista principale: per ogni cerchio (`forge.contour_shape`) la
traccia nelle viste compagne, la quota di diametro agganciata, e se è
passante e quanto è profondo.

forge dice "cerchio", mai "foro". Qui lo si legge come foro incrociando le
viste e la notazione — convenzione di disegno, come le viste (D18). Trapano o
laser non si decide qui: è sapere di processo (snapbend).

Passante per convenzione: un foro senza indicazioni (nessuna traccia che si
ferma prima della faccia opposta) è passante; su una lamiera tagliata al
laser un foro cieco non esiste. Le linee nascoste si omettono spesso, la
loro assenza non fa un foro cieco.

Stesso schema di `read_views`: passi pubblici (`principal_circles`,
`hole_trace`, `diameter_callouts`, `parse_callout`, `callout_scale`,
`group_holes`) e una ricetta, `read_holes(doc, result, views)`.

    result = forge.island(doc)
    views = sd.read_views(result)
    holes = sd.read_holes(doc, result, views)
    sd.describe_holes(holes)   # "2 fori passanti Ø5,3 +0,05/0, profondità 4; ..."
"""

from __future__ import annotations

import math
import re
from typing import Dict, List, Optional, Tuple

import forge
from forge.core.primitives.segments import LineSeg

from .model import Hole, HoleCallout, HoleGroup, HoleLayout, HoleTrace, ViewLayout
from .roles import CONSTRUCTION, FRAME, TITLE_BLOCK

WALL_TOLERANCE = 0.1     # mm — una parete sta alla quota del bordo del cerchio entro questo
SPAN_TOLERANCE = 1.0     # mm — stessa tolleranza dei compagni di proiezione (views.MATE_TOLERANCE)
SCALE_AGREEMENT = 0.01   # scarto relativo massimo fra le scale lette da quote diverse

_NOT_GEOMETRY = {FRAME, TITLE_BLOCK, CONSTRUCTION}
FACE, BOTTOM = "face", "bottom"   # come finisce una parete: su una faccia o sul fondo di un cieco
_NUMBER = r"[+-]?\d+(?:[.,]\d+)?"
_CALLOUT = re.compile(rf"^\s*(?P<designation>[Ø∅]|M)\s*(?P<value>{_NUMBER})\s*(?P<rest>.*?)\s*$")
_STACKED = re.compile(rf"^(?P<upper>{_NUMBER})\s*\^\s*(?P<lower>{_NUMBER})")
_SYMMETRIC = re.compile(rf"^±\s*(?P<value>{_NUMBER})")


def principal_circles(result, views: ViewLayout) -> List[Tuple[str, Tuple[float, float], float]]:
    """(percorso, centro, diametro) di ogni `inner` circolare della vista principale."""
    if views.principal is None:
        return []
    circles = []
    for j, inner in enumerate(result.clusters[views.principal].inners):
        shape = forge.contour_shape(inner)
        if shape is not None and shape.kind == "circle":
            circles.append((f"clusters[{views.principal}].inners[{j}]", tuple(shape.center), shape.diameter))
    return circles


def hole_trace(doc, views: ViewLayout, center: Tuple[float, float], diameter: float,
               tolerance: float = WALL_TOLERANCE) -> List[HoleTrace]:
    """
    Le tracce del cerchio nelle viste compagne della principale: due pareti
    rettilinee, una per bordo del cerchio, dentro la vista compagna. Nei
    compagni in altezza (laterale) le pareti sono orizzontali alla y del
    cerchio ± r, nei compagni in larghezza (pianta) verticali alla x ± r.
    Qualunque tipo di linea: nascosta in una vista, continua in una sezione.

    Pareti fra due facce (del pezzo o bordi della vista) → passante,
    profondità = lunghezza: su una lamiera piegata è lo spessore dell'ala;
    pareti della stessa lunghezza che partono da una faccia e hanno il fondo
    (una linea o una punta che le chiude) → cieco. Pareti che si fermano
    senza fondo non sono una traccia: linee che per caso stanno a quella
    quota.
    Una parete che coincide col bordo della vista non si distingue dal
    contorno e non conta.
    """
    if views.principal is None:
        return []
    by_index = {v.index: v for v in views.views}
    principal = by_index[views.principal]
    r = diameter / 2
    traces = []
    for axis, mates in ((1, principal.height_mates), (0, principal.width_mates)):
        for index in mates:
            bbox = by_index[index].bbox
            trace = _trace_in(doc, bbox, axis, center[axis], r, tolerance)
            if trace is not None:
                traces.append(HoleTrace(view=index, through=trace[0], length=trace[1]))
    return traces


def diameter_callouts(result) -> Dict[str, object]:
    """Percorso dell'elemento quotato → la quota di diametro che lo misura (`forge.dimension_references`)."""
    callouts = {}
    for annotation in result.annotations:
        if isinstance(annotation, forge.Dimension) and annotation.dim_type == "diameter":
            refs = annotation.references or forge.dimension_references(result, annotation)
            if len(refs) == 1:
                callouts.setdefault(refs[0], annotation)
    return callouts


def parse_callout(dimension) -> Optional[HoleCallout]:
    """
    Il testo di una quota di diametro: "Ø"/"M", il valore e la tolleranza
    ("+0,05^-0" impilata, "±0,1"). Quello che segue e non si legge resta in
    `rest`. None se il testo non comincia con Ø o M.
    """
    text = dimension.display_text
    m = _CALLOUT.match(text)
    if m is None:
        return None
    designation = "Ø" if m["designation"] in "Ø∅" else "M"
    rest, upper, lower = m["rest"], None, None
    stacked, symmetric = _STACKED.match(rest), _SYMMETRIC.match(rest)
    if stacked:
        upper, lower = _number(stacked["upper"]), _number(stacked["lower"])
        rest = rest[stacked.end():].strip()
    elif symmetric:
        upper = _number(symmetric["value"])
        lower = -upper
        rest = rest[symmetric.end():].strip()
    return HoleCallout(text=text, designation=designation, nominal=_number(m["value"]),
                       measured=dimension.measured_value, upper=upper, lower=lower, rest=rest)


def callout_scale(holes: List[Hole], agreement: float = SCALE_AGREEMENT) -> Tuple[Optional[float], List[str]]:
    """
    Valore scritto / valore misurato, sulle quote Ø (i filetti M no: la
    quota cade sul cerchio di nocciolo, non sul nominale). Se le quote non
    concordano: None + "scale: inconsistent"; senza quote: None.
    """
    ratios = [h.callout.nominal / h.callout.measured for h in holes
              if h.callout and h.callout.designation == "Ø" and h.callout.measured]
    if not ratios:
        return None, []
    if max(ratios) - min(ratios) > agreement * max(ratios):
        return None, ["scale: inconsistent"]
    return sum(ratios) / len(ratios), []


def group_holes(holes: List[Hole]) -> List[HoleGroup]:
    """Raggruppa per quota scritta, tolleranza, passante e profondità; senza quota, per diametro disegnato."""
    groups: Dict[tuple, HoleGroup] = {}
    for h in holes:
        c = h.callout
        depth = None if h.depth is None else round(h.depth, 2)
        if c is not None:
            key = (c.designation, c.nominal, c.upper, c.lower, h.through, depth)
            fields = dict(designation=c.designation, diameter=c.nominal, upper=c.upper, lower=c.lower)
        else:
            key = (None, round(h.drawn_diameter, 2), None, None, h.through, depth)
            fields = dict(designation=None, diameter=None, upper=None, lower=None)
        if key not in groups:
            groups[key] = HoleGroup(holes=[], through=h.through, depth=h.depth, **fields)
        groups[key].holes.append(h)
    return sorted(groups.values(), key=lambda g: -g.count)


def read_holes(doc, result, views: ViewLayout) -> HoleLayout:
    """
    Ricetta: i cerchi della vista principale, la loro quota di diametro, la
    traccia nelle viste compagne; passante per traccia o per convenzione; la
    profondità alla scala delle quote; i gruppi. Non muta `doc` né `result`.

    Cerchi concentrici (lamatura, svasatura) restano fori separati con il
    flag "concentric: <percorso>": metterli insieme non si fa ancora.
    """
    layout = HoleLayout()
    if views.principal is None:
        layout.flags.append("holes: no principal view")
        return layout
    callouts = diameter_callouts(result)
    for path, center, diameter in principal_circles(result, views):
        hole = Hole(path=path, center=center, drawn_diameter=diameter)
        dimension = callouts.get(path)
        if dimension is None:
            hole.flags.append("callout: missing")
        else:
            hole.callout = parse_callout(dimension)
            if hole.callout is None:
                hole.flags.append(f"callout: unread '{dimension.display_text}'")
            elif hole.callout.rest:
                hole.flags.append(f"callout: unread '{hole.callout.rest}'")
        _read_depth(hole, hole_trace(doc, views, center, diameter), views.depth)
        layout.holes.append(hole)

    for hole in layout.holes:
        for other in layout.holes:
            if other is not hole and math.dist(other.center, hole.center) <= WALL_TOLERANCE:
                hole.flags.append(f"concentric: {other.path}")

    layout.scale, flags = callout_scale(layout.holes)
    layout.flags += flags
    for hole in layout.holes:
        if hole.drawn_depth is not None and layout.scale is not None:
            hole.depth = hole.drawn_depth * layout.scale
        elif hole.drawn_depth is not None:
            hole.flags.append("depth: scale unknown")
    layout.groups = group_holes(layout.holes)
    return layout


def describe_holes(layout: HoleLayout) -> str:
    """I gruppi come li scriverebbe una persona: "2 fori passanti Ø5,3 +0,05/0, profondità 4"."""
    parts = []
    for g in layout.groups:
        noun = "foro" if g.count == 1 else "fori"
        kind = {True: " passante" if g.count == 1 else " passanti",
                False: " cieco" if g.count == 1 else " ciechi"}.get(g.through, "")
        if g.diameter is not None:
            size = f" {g.designation}{_fmt(g.diameter)}"
            if g.upper is not None:
                size += f" {_signed(g.upper)}/{_signed(g.lower)}"
        else:
            size = " (quota mancante)"
        depth = f", profondità {_fmt(g.depth)}" if g.depth is not None else ""
        parts.append(f"{g.count} {noun}{kind}{size}{depth}")
    return "; ".join(parts)


def _read_depth(hole: Hole, traces: List[HoleTrace], view_depth: Optional[float]) -> None:
    """Passante e profondità disegnata: dalla traccia, altrimenti per convenzione."""
    hole.traces = traces
    blind = {round(t.length, 2) for t in traces if not t.through}
    if traces and all(t.through for t in traces):
        hole.through, hole.drawn_depth, hole.source = True, traces[0].length, "trace"
    elif traces and len(blind) == 1 and not any(t.through for t in traces):
        hole.through, hole.drawn_depth, hole.source = False, traces[0].length, "trace"
    elif traces:
        hole.flags.append("trace: inconsistent")
    else:
        hole.through, hole.drawn_depth, hole.source = True, view_depth, "convention"
    if hole.through and hole.drawn_depth is None:
        hole.flags.append("depth: no companion view")


def _trace_in(doc, bbox, axis: int, center: float, r: float,
              tolerance: float) -> Optional[Tuple[bool, float]]:
    """
    Le due pareti dentro `bbox`, perpendicolari ad `axis` (1 = orizzontali a
    y = center ± r). (passante, lunghezza) o None se non ci sono entrambe.
    """
    lo, hi = bbox[axis], bbox[axis + 2]
    along = 1 - axis
    start, end = bbox[along], bbox[along + 2]
    walls = []
    for level in (center - r, center + r):
        if abs(level - lo) <= tolerance or abs(level - hi) <= tolerance or not lo < level < hi:
            return None
        intervals = []
        for edge in doc.edges:
            seg = edge.segment
            if edge.role in _NOT_GEOMETRY or not isinstance(seg, LineSeg):
                continue
            if abs(seg.start[axis] - level) > tolerance or abs(seg.end[axis] - level) > tolerance:
                continue
            a, b = sorted((seg.start[along], seg.end[along]))
            a, b = max(a, start), min(b, end)
            if b - a > tolerance:
                intervals.append((a, b))
        walls.append(_merge(intervals, tolerance))
    if not all(len(w) == 1 for w in walls):
        return None
    (a1, b1), (a2, b2) = walls[0][0], walls[1][0]
    if abs(a1 - a2) > SPAN_TOLERANCE or abs(b1 - b2) > SPAN_TOLERANCE:
        return None
    ends = []
    for e in ((a1 + a2) / 2, (b1 + b2) / 2):
        low = _end_kind(doc, axis, along, e, center - r, -1, (start, end), tolerance)
        high = _end_kind(doc, axis, along, e, center + r, +1, (start, end), tolerance)
        ends.append(low if low == high else None)
    if ends == [FACE, FACE]:
        return True, b1 - a1
    if sorted(ends, key=str) == [BOTTOM, FACE]:
        return False, b1 - a1
    return None


def _end_kind(doc, axis: int, along: int, e: float, level: float, outward: int,
              faces: Tuple[float, float], tolerance: float) -> Optional[str]:
    """
    Dove finisce una parete (coordinata `e` lungo la parete, alla quota
    `level`): "face" se lì la superficie prosegue oltre la parete, dal lato
    opposto al foro — una linea che la attraversa, un edge che da lì va verso
    l'esterno (anche obliquo: uno smusso, un raccordo), o il bordo della
    vista; "bottom" se da lì partono solo edge verso l'altra parete — il
    fondo di un foro cieco, piatto o a punta; None altrimenti.
    """
    if any(abs(e - f) <= tolerance for f in faces):
        return FACE
    bottom = False
    for edge in doc.edges:
        seg = edge.segment
        start, stop = getattr(seg, "start", None), getattr(seg, "end", None)
        if edge.role in _NOT_GEOMETRY or start is None or stop is None:
            continue
        if isinstance(seg, LineSeg) and abs(start[along] - e) <= tolerance and abs(stop[along] - e) <= tolerance:
            lo, hi = sorted((start[axis], stop[axis]))
            if lo - tolerance <= level <= hi + tolerance:
                beyond = (level - lo) if outward < 0 else (hi - level)
                if beyond > tolerance:
                    return FACE
        for p, q in ((start, stop), (stop, start)):
            if abs(p[along] - e) > tolerance or abs(p[axis] - level) > tolerance:
                continue
            step = (q[axis] - p[axis]) * outward
            if step > tolerance:
                return FACE
            if step < -tolerance:
                bottom = True
    return BOTTOM if bottom else None


def _merge(intervals, tolerance: float):
    """Unisce intervalli che si toccano o si sovrappongono."""
    merged = []
    for a, b in sorted(intervals):
        if merged and a <= merged[-1][1] + tolerance:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return merged


def _number(text: str) -> float:
    return float(text.replace(",", "."))


def _fmt(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def _signed(value: float) -> str:
    return "0" if value == 0 else (f"+{_fmt(value)}" if value > 0 else _fmt(value))
