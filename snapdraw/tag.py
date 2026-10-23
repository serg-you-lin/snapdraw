"""
snapdraw/tag.py
---------------
Riporta il layout rilevato a topo: setta `edge.role` sugli `Edge` di
`doc.edges` che compongono cornice e cartiglio.

È l'aggancio "opzione B" chiuso in topo D30: un consumatore marca la geometria
**prima** di `topo.heal`, e heal tiene quegli edge fuori dal grafo
(`_split_labeled` estrae ogni ruolo deciso e non strutturale). La geometria non
si perde — finisce in `loose` col ruolo intatto e l'output DXF la
scrive sul layer che le dà `roles.LAYERS` (`Frame`, `TitleBlock`), passato a
`to_dxf`, non su `Trash` (topo D31, D128).

`"frame"` e `"title_block"` sono **entrambi** slug di consumatore: topo non li
conosce (`ContourRole.FRAME` è stato rimosso in D31), li conserva e basta. Gli
slug e il loro stile (colore/layer) sono costruiti in `roles.py` — qui si
importano soltanto, mai definiti inline (topo D47, "roles out of core": lo
stesso schema con cui topo costruisce il proprio vocabolario di `detect()`).
"""

from __future__ import annotations

import math
from typing import List

import topo

from .model import FrameLayout
from .roles import CONSTRUCTION
from .roles import FRAME as FRAME_ROLE
from .roles import TITLE_BLOCK as TITLE_BLOCK_ROLE

CENTER_TOLERANCE = 0.01    # mm — un capo (o il punto medio) della linea sta sul centro del cerchio entro questo
CENTER_MARK_REACH = 2.0    # una linea del segno arriva al massimo a questi raggi dal centro; oltre è un asse
PERPENDICULAR_TOLERANCE = 1.0   # gradi


def tag_layout(doc, layout: FrameLayout) -> int:
    """
    Setta `edge.role` sugli Edge di cornice e cartiglio in `layout`.

    Muta `doc.edges` in-place (gli Edge sono gli stessi oggetti che `layout`
    trattiene). Ritorna il numero di Edge marcati.
    """
    n = 0
    if layout.frame is not None:
        for edge in layout.frame.edges:
            edge.role = FRAME_ROLE
            n += 1
    if layout.title_block is not None:
        for edge in layout.title_block.edges:
            edge.role = TITLE_BLOCK_ROLE
            n += 1
    return n


def tag_center_marks(doc) -> List[str]:
    """
    I segni di centro disegnati a tratto continuo diventano `construction`
    (MAP D40). Un segno di centro: almeno due linee ancora senza ruolo, con un
    capo o il punto medio sul centro di un cerchio, che non vanno oltre
    `CENTER_MARK_REACH` raggi, e due di loro perpendicolari; con loro i
    prolungamenti dei bracci. Senza, croce e prolungamenti tagliano il
    cerchio in archi e il foro non è più un pezzo chiuso (topo
    D162). Muta `doc.edges`; ritorna un flag per segno, per vederli.
    """
    lines = [e for e in doc.edges if isinstance(e.segment, topo.primitives.LineSeg) and e.role == "unknown"]
    flags = []
    for circle in (e.segment for e in doc.edges if isinstance(e.segment, topo.primitives.CircleSeg)):
        mark = [e for e in lines if _from_center(e.segment, circle)]
        if len(mark) < 2 or not any(_perpendicular(a.segment, b.segment) for a in mark for b in mark):
            continue
        mark += [e for arm in mark for e in lines if e not in mark and _extends(e.segment, arm.segment, circle.center)]
        for edge in mark:
            edge.role = CONSTRUCTION
        lines = [e for e in lines if e.role == "unknown"]
        x, y = circle.center
        flags.append(f"center mark: ({x:.2f}, {y:.2f}) r={circle.radius:.2f}, {len(mark)} lines")
    return flags


def _extends(line, arm, center) -> bool:
    """
    Il prolungamento di un braccio (il simbolo di SolidWorks ne ha uno per
    braccio): parte dal capo lontano del braccio, sulla stessa retta, verso
    l'esterno, e non è più lungo del braccio.
    """
    tip = max((arm.start, arm.end), key=lambda p: math.dist(p, center))
    near = min((line.start, line.end), key=lambda p: math.dist(p, tip))
    far = line.end if near is line.start else line.start
    return (math.dist(near, tip) <= CENTER_TOLERANCE and math.dist(far, center) > math.dist(tip, center)
            and math.dist(near, far) <= math.dist(arm.start, arm.end) + CENTER_TOLERANCE
            and not _perpendicular(line, arm) and abs(_turn(line, arm)) <= PERPENDICULAR_TOLERANCE)


def _turn(a, b) -> float:
    """L'angolo fra le due rette, in gradi, ridotto a (-90, 90]."""
    ta = math.atan2(a.end[1] - a.start[1], a.end[0] - a.start[0])
    tb = math.atan2(b.end[1] - b.start[1], b.end[0] - b.start[0])
    d = math.degrees(ta - tb) % 180
    return d - 180 if d > 90 else d


def _from_center(line, circle) -> bool:
    """La linea parte dal centro del cerchio (o ci passa nel mezzo) e resta entro `CENTER_MARK_REACH` raggi."""
    middle = ((line.start[0] + line.end[0]) / 2, (line.start[1] + line.end[1]) / 2)
    on_center = any(math.dist(p, circle.center) <= CENTER_TOLERANCE for p in (line.start, line.end, middle))
    reach = max(math.dist(p, circle.center) for p in (line.start, line.end))
    return on_center and reach <= CENTER_MARK_REACH * circle.radius


def _perpendicular(a, b) -> bool:
    ta = math.atan2(a.end[1] - a.start[1], a.end[0] - a.start[0])
    tb = math.atan2(b.end[1] - b.start[1], b.end[0] - b.start[0])
    return abs(abs(math.degrees(ta - tb)) % 180 - 90) <= PERPENDICULAR_TOLERANCE
