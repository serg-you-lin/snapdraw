"""
snapdraw/views.py
-----------------
Le viste di un foglio: quali isole di `forge.island(...)` sono viste
ortogonali, quali assonometrie, quali simboli; come si corrispondono per
proiezione; qual è la vista principale e che profondità ha il pezzo.

Nessuna immagine: solo conti sulle primitive che forge restituisce —
direzione dei LineSeg, bbox dei contorni esterni. La proiezione ortogonale è
una convenzione di disegno, come cornice e cartiglio: per questo sta qui e
non in forge.

Stesso schema di `detect_frame`: passi pubblici (`classify_view`,
`projection_mates`, `principal_view`, `view_depth`) e una ricetta,
`read_views(result)`.

    doc = forge.load_dxf("disegno.dxf", role_rules=sd.load_rules("generic"))
    sd.tag_layout(doc, sd.detect_frame(doc))
    views = sd.read_views(forge.island(doc))
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from forge.core.axis import axis_aligned_share

from .model import View, ViewLayout

ORTHOGRAPHIC = "orthographic"
PICTORIAL = "pictorial"
SYMBOL = "symbol"

AXIS_ANGLE_TOLERANCE = 2.0   # gradi — un LineSeg entro 2° da 0/90 è orizzontale/verticale
ORTHOGRAPHIC_SHARE = 0.5     # quota minima di lunghezza orizzontale/verticale per una vista ortogonale
MATE_TOLERANCE = 1.0         # mm — due viste in proiezione hanno la stessa estensione
SYMBOL_RATIO = 0.1           # un'isola senza compagni sotto 1/10 della dimensione minore della vista di riferimento


def classify_view(cluster, angle_tolerance: float = AXIS_ANGLE_TOLERANCE) -> str:
    """
    "orthographic" se almeno metà della lunghezza dei LineSeg (contorno e
    giri interni) è orizzontale o verticale, altrimenti "pictorial". Una
    vista ortogonale di un pezzo prismatico è fatta di orizzontali e
    verticali per costruzione, un'assonometria no. Un'isola senza LineSeg
    (solo archi e cerchi) resta "orthographic".
    """
    segments = list(cluster.outer.segments) + [s for inner in cluster.inners for s in inner.segments]
    share = axis_aligned_share(segments, angle_tolerance)
    return ORTHOGRAPHIC if share is None or share >= ORTHOGRAPHIC_SHARE else PICTORIAL


def projection_mates(views: List[View], tolerance: float = MATE_TOLERANCE) -> Dict[int, Tuple[List[int], List[int]]]:
    """
    Per ogni vista ortogonale: (height_mates, width_mates). Stessa
    estensione verticale → frontale e laterale; stessa estensione
    orizzontale → frontale e pianta. Le assonometrie non hanno compagni.
    """
    ortho = [v for v in views if v.kind == ORTHOGRAPHIC]
    mates = {}
    for v in ortho:
        height = [w.index for w in ortho if w is not v
                  and abs(w.bbox[1] - v.bbox[1]) <= tolerance and abs(w.bbox[3] - v.bbox[3]) <= tolerance]
        width = [w.index for w in ortho if w is not v
                 and abs(w.bbox[0] - v.bbox[0]) <= tolerance and abs(w.bbox[2] - v.bbox[2]) <= tolerance]
        mates[v.index] = (height, width)
    return mates


def principal_view(views: List[View]) -> Tuple[Optional[int], List[str]]:
    """
    La vista con compagni in tutte e due le direzioni (la più grande, se più
    d'una). Altrimenti: l'unica vista ortogonale del foglio; oppure la più
    grande con compagni in una sola direzione, con il flag
    "principal: single projection". Se nessuna: None + "principal: uncertain".
    """
    ortho = [v for v in views if v.kind == ORTHOGRAPHIC]
    both = [v for v in ortho if v.height_mates and v.width_mates]
    if both:
        return max(both, key=_area).index, []
    if len(ortho) == 1:
        return ortho[0].index, []
    one = [v for v in ortho if v.height_mates or v.width_mates]
    if one:
        return max(one, key=_area).index, ["principal: single projection"]
    return None, ["principal: uncertain"]


def view_depth(views: List[View], principal: Optional[int],
               tolerance: float = MATE_TOLERANCE) -> Tuple[Optional[float], List[str]]:
    """
    La terza dimensione della vista principale: la larghezza dei compagni in
    altezza, l'altezza dei compagni in larghezza. Se non concordano entro
    `tolerance`: None + "depth: inconsistent"; senza compagni: None.
    """
    if principal is None:
        return None, []
    by_index = {v.index: v for v in views}
    p = by_index[principal]
    values = [by_index[i].width for i in p.height_mates] + [by_index[i].height for i in p.width_mates]
    if not values:
        return None, []
    if max(values) - min(values) > tolerance:
        return None, ["depth: inconsistent"]
    return sum(values) / len(values), []


def read_views(result, tolerance: float = MATE_TOLERANCE) -> ViewLayout:
    """
    Ricetta: classifica ogni cluster, trova i compagni di proiezione, la
    vista principale, i simboli e la profondità. Non muta `result`.

    Simbolo: un'isola senza compagni la cui dimensione maggiore sta sotto
    `SYMBOL_RATIO` della dimensione minore della vista di riferimento (la
    principale, o la più grande se manca) — una lettera di un logo, un
    segno di rugosità. Il rapporto è una soglia scelta, non una legge
    geometrica.
    """
    views = [View(index=i, bbox=tuple(c.outer.polygon.bounds), kind=classify_view(c))
             for i, c in enumerate(result.clusters)]
    for index, (height, width) in projection_mates(views, tolerance).items():
        views[index].height_mates, views[index].width_mates = height, width

    layout = ViewLayout(views=views)
    reference = _reference(views)
    if reference is not None:
        limit = SYMBOL_RATIO * min(reference.width, reference.height)
        for v in views:
            if v is not reference and not v.height_mates and not v.width_mates \
                    and max(v.width, v.height) < limit:
                v.kind = SYMBOL

    layout.principal, flags = principal_view(views)
    layout.flags += flags
    layout.depth, flags = view_depth(views, layout.principal, tolerance)
    layout.flags += flags
    return layout


def _reference(views: List[View]) -> Optional[View]:
    """La vista che fa da metro per i simboli: la principale, o la più grande."""
    principal, _ = principal_view(views)
    if principal is not None:
        return views[principal]
    return max(views, key=_area) if views else None


def _area(view: View) -> float:
    return view.width * view.height
