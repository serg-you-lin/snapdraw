"""
snapdraw/features.py
--------------------
Le feature delle viste: su ogni vista ortogonale, ogni contorno interno
isolato letto con `forge.geometry.contour_shape` — cerchio → foro, stadio → asola,
rettangolo/poligono → apertura — con la traccia nelle viste compagne
(passante, cieco, profondità), la quota agganciata e la scala della vista.

forge dice "cerchio", mai "foro". Qui lo si legge come foro incrociando le
viste e la notazione: convenzione di disegno, come le viste (D18). Trapano,
laser o fresa non si decide qui: è sapere di processo (snapbend).

Passante per convenzione (D19): una feature senza indicazioni (nessuna
traccia che si ferma su un fondo) è passante; su una lamiera tagliata al
laser un foro cieco non esiste. Le nascoste si omettono spesso: la loro
assenza non fa un cieco.

Isolato: un contorno interno non circolare è una feature se non tocca il
contorno esterno né un contorno vicino (se non quelli che contiene o da cui
è contenuto). Le facce che nascono dalle linee che attraversano una vista
(una piega, uno smusso visto di fianco) toccano i vicini: non sono aperture.
Un cerchio resta un foro anche se tocca il bordo (una sede tangente al lato
del pezzo).

Passi pubblici (`view_scales`, `feature_contours`, `feature_trace`,
`diameter_callouts`, `parse_callout`, `group_features`) e una ricetta,
`read_features(doc, result, views)`. `tag_features` le attacca al risultato
per chi esporta.

    result = forge.island(doc)
    views = sd.read_views(result)
    features = sd.read_features(doc, result, views)
    sd.describe_features(features)   # "2 fori passanti Ø5,3 +0,05/0, profondità 4; ..."
    sd.tag_features(result, features)  # cluster.detected["view_features"], per to_dxf
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

import forge
from forge.core.geometry.axis import merge_intervals
from forge.core.primitives.segments import ArcSeg, LineSeg
from forge.model.detected import DetectedFeatures

from .model import Callout, Feature, FeatureGroup, FeatureLayout, Trace, ViewLayout
from .roles import (CONSTRUCTION, COUNTERBORE, COUNTERSINK, FRAME, HOLE, OPENING, SEATED_HOLE, SLOT, THREADED_HOLE,
                    TITLE_BLOCK)
from .views import ORTHOGRAPHIC, view_depth

WALL_TOLERANCE = 0.1     # mm — una parete sta al bordo della forma entro questo
SPAN_TOLERANCE = 1.0     # mm — stessa tolleranza dei compagni di proiezione (views.MATE_TOLERANCE)
TOUCH_TOLERANCE = 0.05   # mm — due contorni più vicini di così si toccano: non è una feature isolata
SCALE_AGREEMENT = 0.01   # scarto relativo massimo fra le scale lette da quote diverse
COLLECTION = "view_features"   # nome sotto cui `tag_features` le attacca a `cluster.detected`
# Cresta del filetto: un arco attorno al foro (`forge.geometry.arcs_around`), a ~270°,
# poco più grande — per le metriche diametro nominale / preforo ~1.1–1.3.
THREAD_SWEEP, THREAD_SWEEP_TOLERANCE = 270.0, 35.0   # gradi
THREAD_MAX_RADIUS_RATIO = 1.6
THREAD_CENTER_TOLERANCE = 1.0   # mm

KINDS = {"circle": "hole", "stadium": "slot"}   # ogni altra forma: "opening"
PLAIN, THREADED, COUNTERBORED, COUNTERSUNK, SEATED = "plain", "threaded", "counterbore", "countersink", "seated"
FACE, BOTTOM = "face", "bottom"   # come finisce una parete: su una faccia o sul fondo di un cieco

_NOT_GEOMETRY = {FRAME, TITLE_BLOCK, CONSTRUCTION}
_NUMBER = r"[+-]?\d+(?:[.,]\d+)?"
_CALLOUT = re.compile(rf"^\s*(?:(?P<times>\d+)\s*[x×X]\s*)?(?P<designation>[Ø∅]|M)\s*(?P<value>{_NUMBER})\s*(?P<rest>.*?)\s*$")
_COUNT = re.compile(r"(?:n\s*[°º.]\s*(?P<n>\d+)|(?P<m>\d+)\s*(?=fori|holes|pz))\s*(?:fori|holes|pz)?", re.I)
_STACKED = re.compile(rf"^(?P<upper>{_NUMBER})\s*\^\s*(?P<lower>{_NUMBER})")
_SYMMETRIC = re.compile(rf"^±\s*(?P<value>{_NUMBER})")
_WRITTEN = re.compile(rf"^\s*(?:[Ø∅R]\s*)?(?P<value>\d+(?:[.,]\d+)?)")
_VIEW = re.compile(r"^clusters\[(\d+)\]")


def view_scales(result, views: ViewLayout, agreement: float = SCALE_AGREEMENT) -> Tuple[Dict[int, Optional[float]], List[str]]:
    """
    La scala di ogni vista: valore scritto / valore misurato, il più
    frequente sulle quote agganciate alla vista (lineari, diametri, raggi;
    non gli angoli, non i filetti M, che cadono sul nocciolo). Quote della
    stessa vista che non concordano: "scale: view <i> mixed". Una vista
    senza quote prende la scala del foglio, se tutte le viste quotate
    concordano ("scale: view <i> from sheet"), altrimenti None.
    """
    ratios: Dict[int, List[float]] = {}
    for dimension in result.annotations:
        if not isinstance(dimension, forge.Dimension) or dimension.dim_type == "angular" \
                or not dimension.measured_value:
            continue
        written = _WRITTEN.match(dimension.display_text)
        refs = dimension.references or forge.dimension_references(result, dimension)
        view = _VIEW.match(refs[0]) if refs else None
        if written is None or view is None or _number(written["value"]) == 0:
            continue
        ratios.setdefault(int(view.group(1)), []).append(_number(written["value"]) / dimension.measured_value)

    scales, flags = {}, []
    for index, values in ratios.items():
        mode = _mode(values, agreement)
        if any(abs(v - mode) > agreement * mode for v in values):
            flags.append(f"scale: view {index} mixed")
        scales[index] = mode
    sheet = list(scales.values())
    sheet_scale = sheet[0] if sheet and all(abs(s - sheet[0]) <= agreement * sheet[0] for s in sheet) else None
    for view in views.views:
        if view.kind == ORTHOGRAPHIC and view.index not in scales:
            scales[view.index] = sheet_scale
            if sheet_scale is not None:
                flags.append(f"scale: view {view.index} from sheet")
    return scales, flags


def feature_contours(result, view: int, tolerance: float = TOUCH_TOLERANCE) -> List[Tuple[int, object, object]]:
    """
    (indice, contorno, forma) dei contorni interni della vista con una forma
    (`forge.geometry.contour_shape` non None): i cerchi sempre, le altre forme solo se
    isolate — non toccano l'esterno né un vicino che non le contiene e non è
    contenuto in loro.
    """
    cluster = result.clusters[view]
    inners = cluster.inners
    outer = cluster.outer.polygon.exterior
    candidates = []
    for j, inner in enumerate(inners):
        shape = forge.geometry.contour_shape(inner)
        if shape is None or inner.polygon is None:
            continue
        if shape.kind == "circle":
            candidates.append((j, inner, shape))
            continue
        ring = inner.polygon.exterior
        if ring.distance(outer) <= tolerance:
            continue
        touching = any(k != j and other.polygon is not None
                       and ring.distance(other.polygon.exterior) <= tolerance
                       and not other.polygon.contains(inner.polygon) and not inner.polygon.contains(other.polygon)
                       for k, other in enumerate(inners))
        if not touching:
            candidates.append((j, inner, shape))
    return candidates


def feature_trace(doc, views: ViewLayout, view: int, bounds, tolerance: float = WALL_TOLERANCE) -> List[Trace]:
    """
    Le tracce di una forma (riquadro `bounds`) nelle viste compagne di
    `view`: due pareti rettilinee ai bordi della forma — orizzontali nei
    compagni in altezza, verticali in quelli in larghezza. Qualunque tipo di
    linea: nascosta in una vista, continua in una sezione.

    Pareti fra due facce (del pezzo o bordi della vista) → passante,
    profondità = lunghezza: su una lamiera piegata è lo spessore dell'ala;
    pareti della stessa lunghezza fra una faccia e un fondo (una linea o una
    punta che le chiude) → cieco. Pareti senza né l'una né l'altro non sono
    una traccia: linee che per caso stanno a quella quota.
    """
    by_index = {v.index: v for v in views.views}
    this = by_index[view]
    traces = []
    for axis, mates in ((1, this.height_mates), (0, this.width_mates)):
        for index in mates:
            found = _trace_in(doc, by_index[index].bbox, axis, bounds[axis], bounds[axis + 2], tolerance)
            if found is not None:
                traces.append(Trace(view=index, through=found[0], length=found[1]))
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


def parse_callout(dimension) -> Optional[Callout]:
    """
    Il testo di una quota di diametro: "Ø"/"M", il valore, la tolleranza
    ("+0,05^-0" impilata, "±0,1") e quante feature copre ("n°30 fori",
    "16 fori", "4xØ5"). Quello che segue e non si legge resta in `rest`.
    Una quota di diametro senza simbolo ("15") vale Ø. None se il testo non
    comincia con Ø o M (dopo un eventuale "4x").
    """
    text = dimension.display_text
    m = _CALLOUT.match(text)
    if m is None and dimension.dim_type == "diameter":
        # una quota di diametro senza simbolo scritto ("15") è un Ø lo stesso
        m = _CALLOUT.match("Ø" + text.strip())
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
    count = int(m["times"]) if m["times"] else None
    many = _COUNT.search(rest)
    if many:
        count = int(many["n"] or many["m"])
        rest = (rest[:many.start()] + rest[many.end():]).strip()
    return Callout(text=text, designation=designation, nominal=_number(m["value"]),
                   measured=dimension.measured_value, upper=upper, lower=lower, count=count, rest=rest)


def group_features(features: List[Feature]) -> List[FeatureGroup]:
    """Raggruppa per tipo, misura (scritta o disegnata), tolleranza, sede, passante e profondità."""
    groups: Dict[tuple, FeatureGroup] = {}
    for f in features:
        c = f.callout
        size = (f.diameter,) if f.kind == "hole" else f.size
        key = (f.kind, f.hole_type, c.designation if c else None, tuple(_round(v) for v in size),
               c.upper if c else None, c.lower if c else None, c is None,
               _round(f.outer_shape.length * (f.scale or 1.0)) if f.outer_shape else None,
               _round(f.seat_depth), f.through, _round(f.depth))
        groups.setdefault(key, FeatureGroup(features=[], kind=f.kind, hole_type=f.hole_type)).features.append(f)
    return sorted(groups.values(), key=lambda g: (list(KINDS.values()).index(g.kind) if g.kind in KINDS.values()
                                                  else 9, -g.count))


def read_features(doc, result, views: ViewLayout) -> FeatureLayout:
    """
    Ricetta: la scala di ogni vista; per ogni vista ortogonale i contorni
    isolati, le coppie concentriche (foro + sede) unite, il filetto
    dall'arco di cresta, la quota, la traccia nelle compagne; passante per
    traccia o per convenzione. Poi le quote di diametro che forge non ha
    agganciato (misurate sulla cresta, un arco aperto) si agganciano dal
    centro, e un richiamo "n°N fori" vale per i fori uguali della sua vista.
    Misure alla scala della vista; i gruppi. Non muta `doc` né `result`.
    """
    layout = FeatureLayout()
    ortho = [v for v in views.views if v.kind == ORTHOGRAPHIC]
    if not ortho:
        layout.flags.append("features: no orthographic view")
        return layout
    layout.scales, flags = view_scales(result, views)
    layout.flags += flags
    callouts = diameter_callouts(result)
    arcs = [e.segment for e in doc.edges if isinstance(e.segment, ArcSeg) and e.role not in _NOT_GEOMETRY]

    for view in ortho:
        found = [(f"clusters[{view.index}].inners[{j}]", inner, shape) for j, inner, shape in feature_contours(result, view.index)]
        depth, _ = view_depth(views.views, view.index)
        for path, inner, shape, seat in _pair_concentric(found):
            feature = _feature(doc, views, view.index, path, inner, shape, callouts, depth, layout.scales, arcs)
            if seat is not None:
                seat_traces = feature_trace(doc, views, view.index, seat[1].polygon.bounds)
                conical = _conical(doc, views, view.index, seat[1].polygon.bounds, inner.polygon.bounds)
                if not conical and seat_traces and all(t.through for t in seat_traces):
                    # una sede passante non è una sede: due fori concentrici, ognuno per sé
                    alone = _feature(doc, views, view.index, *seat, callouts, depth, layout.scales, arcs)
                    for f, other in ((feature, alone), (alone, feature)):
                        f.flags.append(f"concentric: {other.path}")
                    layout.features.append(alone)
                else:
                    _read_seat(feature, seat, seat_traces, conical, bool(_mates(views, view.index)))
            layout.features.append(feature)

    _anchor_by_center(result, layout.features)
    _share_callouts(layout.features)
    for feature in layout.features:
        if feature.callout is not None and feature.callout.designation == "M":
            feature.hole_type = THREADED
        feature.role = _role(feature)
        _to_scale(feature)
    layout.groups = group_features(layout.features)
    return layout


def tag_features(result, layout: FeatureLayout):
    """
    Attacca le feature ai loro cluster (`cluster.detected["view_features"]`,
    lo stesso overlay di forge D44) e toglie i loro contorni da
    `cluster.inners`, come fa `detect_flat` con i fori: così un exporter li
    scrive una volta sola, sul layer del ruolo. **Muta** `result`; i `path`
    delle feature si riferiscono alla lettura di prima.
    """
    taken = {id(c) for f in layout.features for c in f.contours}
    for index, cluster in enumerate(result.clusters):
        mine = [f for f in layout.features if f.view == index]
        if not mine:
            continue
        cluster.detected = cluster.detected or DetectedFeatures()
        cluster.detected.attach(COLLECTION, mine)
        cluster.inners = [c for c in cluster.inners if id(c) not in taken]
    return result


def feature_metadata(cluster) -> dict:
    """
    Le feature di un cluster come dati, per il JSON di forge:
    `forge.save_json(result, path, extra_metadata=sd.feature_metadata)` dopo
    `tag_features`. Vuoto se il cluster non ne ha.
    """
    features = cluster.features(COLLECTION)
    return {COLLECTION: [f.to_dict() for f in features]} if features else {}


def describe_features(layout: FeatureLayout) -> str:
    """I gruppi come li scriverebbe una persona: "2 fori passanti Ø5,3 +0,05/0, profondità 4"."""
    return "; ".join(_describe(g) for g in layout.groups)


# ---------------------------------------------------------------------------

def _pair_concentric(found):
    """
    (percorso, contorno, forma, sede) — nei gruppi di cerchi concentrici
    (`forge.geometry.concentric_groups`) ogni cerchio prende come sede il più piccolo
    dei cerchi più grandi ancora liberi (lamatura, svasatura); gli altri
    contorni passano da soli con sede None.
    """
    by_id = {id(item[1]): item for item in found}
    seats, used = {}, set()
    for group in forge.geometry.concentric_groups([inner for _, inner, _ in found], tolerance=WALL_TOLERANCE):
        members = [by_id[id(c)] for c in group.items]
        for i, (path, _, shape) in enumerate(members):
            if path in used:
                continue
            other = next((m for m in members[i + 1:]
                          if m[0] not in used and m[2].diameter > shape.diameter + WALL_TOLERANCE), None)
            if other is not None:
                seats[path] = other
                used.add(other[0])
    return [(path, inner, shape, seats.get(path)) for path, inner, shape in found if path not in used]


def _feature(doc, views, view: int, path: str, contour, shape, callouts, depth, scales, arcs) -> Feature:
    """Una feature da un contorno: tipo dalla forma, filetto, quota, traccia e profondità (senza sede)."""
    feature = Feature(kind=KINDS.get(shape.kind, "opening"), view=view, path=path, shape=shape,
                      contours=[contour], hidden=_is_hidden(contour), scale=scales.get(view))
    if feature.kind == "hole":
        feature.hole_type = PLAIN
        crest = _thread_crest(shape, arcs)
        if crest is not None:
            feature.hole_type, feature.thread_diameter = THREADED, 2 * crest.radius
        _read_callout(feature, callouts.get(path))
    _read_depth(feature, feature_trace(doc, views, view, contour.polygon.bounds), depth)
    return feature


def _thread_crest(shape, arcs) -> Optional[ArcSeg]:
    """L'arco di cresta del filetto attorno al foro: ~270°, poco più grande (`forge.geometry.arcs_around`)."""
    found = forge.geometry.arcs_around(tuple(shape.center), shape.diameter / 2, arcs, tolerance=THREAD_CENTER_TOLERANCE)
    return next((a.arc for a in found if abs(a.sweep - THREAD_SWEEP) < THREAD_SWEEP_TOLERANCE
                 and a.radius_ratio <= THREAD_MAX_RADIUS_RATIO), None)


def _mates(views, view: int) -> List[int]:
    this = next(v for v in views.views if v.index == view)
    return this.height_mates + this.width_mates


def _anchor_by_center(result, features: List[Feature], tolerance: float = 0.5) -> None:
    """
    Le quote di diametro che forge non ha agganciato: i due punti misurati
    stanno ai capi di un diametro, quindi il loro punto medio è il centro. Si
    agganciano al foro con quel centro e quel raggio (del foro, o della cresta
    del filetto), se non ha già una quota.
    """
    holes = [f for f in features if f.kind == "hole"]
    for dimension in result.annotations:
        if not isinstance(dimension, forge.Dimension) or dimension.dim_type != "diameter" \
                or len(dimension.measured_points) != 2:
            continue
        if dimension.references or forge.dimension_references(result, dimension):
            continue
        (x1, y1), (x2, y2) = dimension.measured_points
        center, radius = ((x1 + x2) / 2, (y1 + y2) / 2), math.dist((x1, y1), (x2, y2)) / 2
        for hole in holes:
            radii = [hole.shape.diameter / 2] + ([hole.thread_diameter / 2] if hole.thread_diameter else [])
            if hole.callout is None and math.dist(hole.center, center) <= tolerance \
                    and any(abs(r - radius) <= tolerance for r in radii):
                hole.flags = [f for f in hole.flags if f != "callout: missing"]
                _read_callout(hole, dimension)
                hole.flags.append("callout: anchored by center")
                break


def _share_callouts(features: List[Feature], tolerance: float = WALL_TOLERANCE) -> None:
    """
    Un richiamo che dice quante feature copre ("n°30 fori") vale per i fori
    uguali della sua vista: stesso diametro disegnato, stesso filetto, senza
    quota propria. Se il numero scritto non torna con quelli trovati: flag.
    """
    for source in [f for f in features if f.callout is not None and f.callout.count]:
        same = [f for f in features if f.kind == source.kind and f.view == source.view
                and abs(f.shape.length - source.shape.length) <= tolerance
                and (f.thread_diameter is None) == (source.thread_diameter is None)]
        for f in same:
            if f.callout is None:
                f.callout = source.callout
                f.flags = [x for x in f.flags if x != "callout: missing"] + [f"callout: shared from {source.path}"]
        if len(same) != source.callout.count:
            source.flags.append(f"callout: {source.callout.count} written, {len(same)} found")


def _read_callout(feature: Feature, dimension) -> None:
    if dimension is None:
        feature.flags.append("callout: missing")
        return
    feature.callout = parse_callout(dimension)
    if feature.callout is None:
        feature.flags.append(f"callout: unread '{dimension.display_text}'")
    elif feature.callout.rest:
        feature.flags.append(f"callout: unread '{feature.callout.rest}'")


def _read_depth(feature: Feature, traces: List[Trace], view_depth_value: Optional[float]) -> None:
    """Passante e profondità disegnata: dalla traccia, altrimenti per convenzione."""
    feature.traces = traces
    blind = {round(t.length, 2) for t in traces if not t.through}
    if traces and all(t.through for t in traces):
        feature.through, feature.drawn_depth, feature.source, feature.confidence = True, traces[0].length, "trace", 0.9
    elif traces and len(blind) == 1 and not any(t.through for t in traces):
        feature.through, feature.drawn_depth, feature.source, feature.confidence = False, traces[0].length, "trace", 0.9
    elif traces:
        feature.flags.append("trace: inconsistent")
    else:
        feature.through, feature.drawn_depth, feature.source, feature.confidence = True, view_depth_value, "convention", 0.6
    if feature.through and feature.drawn_depth is None:
        feature.flags.append("depth: no companion view")


def _read_seat(feature: Feature, seat, traces: List[Trace], conical: bool, has_mates: bool) -> None:
    """
    La sede concentrica (non passante: quella la separa `read_features`),
    solo su prova: linee oblique dalla sede al foro → svasatura (il cono è la
    prova più forte: pareti alla stessa quota possono essere di un'altra
    feature sulla stessa fila); pareti cieche nella compagna → lamatura,
    profondità della sede = loro lunghezza; nessuna delle due → "seated",
    tipo non determinato. Due cerchi concentrici visti di faccia sono uguali
    per una lamatura e una svasatura.
    """
    path, contour, shape = seat
    feature.outer_path, feature.outer_shape = path, shape
    feature.contours.append(contour)
    if conical:
        feature.hole_type = COUNTERSUNK
    elif traces:
        feature.hole_type, feature.seat_depth = COUNTERBORED, traces[0].length
        if any(t.through for t in traces):
            feature.flags.append("counterbore: seat traces inconsistent")
    else:
        feature.hole_type = SEATED
        feature.flags.append("seat: type not determined" + ("" if has_mates else " (no companion views)"))


def _conical(doc, views, view: int, seat_bounds, hole_bounds, tolerance: float = WALL_TOLERANCE) -> bool:
    """
    Nelle compagne, per ognuno dei due lati una linea obliqua che va dal
    bordo della sede al bordo del foro: il cono di una svasatura visto di
    fianco.
    """
    by_index = {v.index: v for v in views.views}
    this = by_index[view]
    lines = [e.segment for e in doc.edges if isinstance(e.segment, LineSeg) and e.role not in _NOT_GEOMETRY]
    for axis, mates in ((1, this.height_mates), (0, this.width_mates)):
        for index in mates:
            x0, y0, x1, y1 = by_index[index].bbox
            inside = [s for s in lines if all(x0 - tolerance <= p[0] <= x1 + tolerance and y0 - tolerance <= p[1] <= y1 + tolerance
                                              for p in (s.start, s.end))]
            sides = [(seat_bounds[axis], hole_bounds[axis]), (seat_bounds[axis + 2], hole_bounds[axis + 2])]
            if all(any(_joins(s, axis, outer, inner, tolerance) for s in inside) for outer, inner in sides):
                return True
    return False


def _joins(seg, axis: int, a: float, b: float, tolerance: float) -> bool:
    """Il segmento va dalla quota `a` alla quota `b` lungo `axis` (in un verso o nell'altro), non parallelo all'asse."""
    p, q = seg.start[axis], seg.end[axis]
    along = 1 - axis
    oblique = abs(seg.end[along] - seg.start[along]) > tolerance
    return oblique and (abs(p - a) <= tolerance and abs(q - b) <= tolerance or abs(p - b) <= tolerance and abs(q - a) <= tolerance)


def _role(feature: Feature) -> str:
    """Un ruolo per tipo di foro (si vede nell'export, lo usa chi sviluppa il pezzo); asola e apertura il loro."""
    if feature.kind == "hole":
        return {THREADED: THREADED_HOLE, COUNTERBORED: COUNTERBORE, COUNTERSUNK: COUNTERSINK,
                SEATED: SEATED_HOLE}.get(feature.hole_type, HOLE)
    return {"slot": SLOT}.get(feature.kind, OPENING)


def _to_scale(feature: Feature) -> None:
    """Profondità alla scala della vista; senza scala, flag e profondità disegnata soltanto."""
    if feature.scale is None:
        if feature.drawn_depth is not None:
            feature.flags.append("depth: scale unknown")
        return
    if feature.drawn_depth is not None:
        feature.depth = feature.drawn_depth * feature.scale
    if feature.seat_depth is not None:
        feature.seat_depth *= feature.scale


def _is_hidden(contour) -> bool:
    """Il contorno è tutto tratteggio uniforme: la feature si vede in trasparenza."""
    styles = [s for s in (contour.styles or []) if s is not None]
    return bool(styles) and all(s.dash_kind == "uniform" for s in styles)


def _trace_in(doc, bbox, axis: int, lo_level: float, hi_level: float,
              tolerance: float) -> Optional[Tuple[bool, float]]:
    """
    Le due pareti dentro `bbox` alle quote `lo_level`/`hi_level` lungo
    `axis` (1 = pareti orizzontali). (passante, lunghezza) o None.
    """
    lo, hi = bbox[axis], bbox[axis + 2]
    along = 1 - axis
    start, end = bbox[along], bbox[along + 2]
    walls = []
    for level in (lo_level, hi_level):
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
        walls.append(merge_intervals(intervals, tolerance))
    if not all(len(w) == 1 for w in walls):
        return None
    (a1, b1), (a2, b2) = walls[0][0], walls[1][0]
    if abs(a1 - a2) > SPAN_TOLERANCE or abs(b1 - b2) > SPAN_TOLERANCE:
        return None
    ends = []
    for e in ((a1 + a2) / 2, (b1 + b2) / 2):
        low = _end_kind(doc, axis, along, e, lo_level, -1, (start, end), tolerance)
        high = _end_kind(doc, axis, along, e, hi_level, +1, (start, end), tolerance)
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
    opposto alla feature — una linea che la attraversa, un edge che da lì va
    verso l'esterno (anche obliquo: uno smusso, un raccordo), o il bordo
    della vista; "bottom" se da lì partono solo edge verso l'altra parete —
    il fondo di un cieco, piatto o a punta; None altrimenti.
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


def _mode(values: List[float], agreement: float) -> float:
    """Il valore più frequente, contando uguali quelli entro `agreement` relativo."""
    best = max(values, key=lambda v: sum(abs(w - v) <= agreement * v for w in values))
    close = [w for w in values if abs(w - best) <= agreement * best]
    return sum(close) / len(close)


def _describe(g: FeatureGroup) -> str:
    f, n = g.first, g.count
    plural = n > 1
    noun = {"hole": ("foro", "fori"), "slot": ("asola", "asole"), "opening": ("apertura", "aperture")}[f.kind][plural]
    feminine = f.kind in ("slot", "opening")
    kind = {PLAIN: "", THREADED: " filettat", COUNTERBORED: " lamat", COUNTERSUNK: " svasat"}.get(g.hole_type, "")
    if kind:
        kind += ("e" if plural else "a") if feminine else ("i" if plural else "o")
    if g.hole_type == SEATED:
        kind = " con sede"
    through = {True: " passant" + ("i" if plural else "e"), False: " ciec" + (("he" if feminine else "hi") if plural else ("a" if feminine else "o"))}.get(f.through, "")
    text = f"{n} {noun}{kind}{through}"
    if f.kind == "hole":
        c = f.callout
        if c is not None:
            text += f" {c.designation}{_fmt(c.nominal)}"
            if c.upper is not None:
                text += f" {_signed(c.upper)}/{_signed(c.lower)}"
        elif f.thread_diameter is not None:
            text += f" M≈{_fmt(f.thread_diameter * (f.scale or 1.0))}"
        else:
            text += f" Ø≈{_fmt(f.diameter)}"
        if f.outer_shape is not None:
            seat = f"sede Ø≈{_fmt(f.outer_shape.length * (f.scale or 1.0))}"
            if f.seat_depth is not None:
                seat += f" prof. {_fmt(f.seat_depth)}"
            if g.hole_type == SEATED:
                seat += ", lamatura o svasatura"
            text += f" ({seat})"
    else:
        length, width = f.size
        text += f" {_fmt(length)}×{_fmt(width)}"
    depth = f.depth if f.depth is not None else f.drawn_depth
    if depth is not None:
        text += f", profondità {_fmt(depth)}" + ("" if f.depth is not None else " (disegnata)")
    return text


def _round(value):
    return None if value is None else round(value, 2)


def _number(text: str) -> float:
    return float(text.replace(",", "."))


def _fmt(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def _signed(value: float) -> str:
    return "0" if value == 0 else (f"+{_fmt(value)}" if value > 0 else _fmt(value))
