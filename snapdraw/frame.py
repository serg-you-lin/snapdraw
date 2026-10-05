"""
snapdraw/frame.py
-----------------
Rilevamento della cornice di formato.

Porta l'algoritmo del vecchio `core/classification/frame_detector.py` di forge
(rimosso in forge MAP D24 perché girava *prima* di heal — cioè è roba del
consumatore, vedi SNAPDRAW.md) e lo riscrive sugli `Edge` / `LineSeg` di forge.

Algoritmo:
    1. tra i rettangoli di bordo (`geometry.find_rectangles`), tieni quelli con
       rapporto dei lati ≈ √2 (formati ISO), tolleranza ±5%;
    2. per ognuno calcola il **contenimento**: frazione della geometria
       restante che sta dentro la sua bbox;
    3. tieni **tutti** quelli con contenimento ≥ 80% — una cornice a doppio
       bordo ne ha due (riquadro esterno + squadratura), e vanno marcati
       entrambi, altrimenti il riquadro non marcato resta e `heal` lo prende
       come outer;
    4. conservativo: se nessuno supera la soglia, ritorna None. Meglio un
       cluster sporco che buttare via la geometria di un pezzo.

Il `FrameInfo` restituito porta gli `Edge` di **tutti** i rettangoli tenuti; la
bbox e il formato sono quelli del più grande.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from forge.core.geometry.axis import CoveredRectangle
from forge.core.geometry.measure import length_inside, segment_length

from .geometry import (
    AXIS_EPS, containment, find_rectangles, is_iso_ratio, iso_format,
)
from .model import FrameInfo

CONTAINMENT_THRESHOLD = 0.80


def find_frame(doc, containment_threshold: float = CONTAINMENT_THRESHOLD) -> Optional[FrameInfo]:
    """
    Rileva la cornice di formato nella geometria grezza di `doc`
    (`forge.load_dxf(...)`, prima di `heal`).

    Ritorna un `FrameInfo` con gli `Edge` di tutti i riquadri di bordo che
    racchiudono il disegno, oppure `None` se non c'è un candidato convincente
    (il chiamante mette "frame: uncertain" nei flag e non marca niente).
    """
    candidates = [r for r in find_rectangles(doc) if is_iso_ratio(r)]
    if not candidates:
        return None

    kept = [(r, c) for r in candidates if (c := containment(r, doc)) >= containment_threshold]
    if not kept:
        return None

    largest, largest_cont = max(kept, key=lambda rc: rc[0].area)
    # la squadratura lato per lato: il lato più interno fra i riquadri tenuti
    # (find_rectangles dà anche riquadri misti, lati del bordo esterno e
    # dell'interno insieme)
    inner = (max(r.bbox[0] for r, _ in kept), max(r.bbox[1] for r, _ in kept),
             min(r.bbox[2] for r, _ in kept), min(r.bbox[3] for r, _ in kept))

    seen: set = set()
    edges = []
    for rect, _ in kept:
        for e in rect.items:
            if id(e) not in seen:
                seen.add(id(e))
                edges.append(e)

    return FrameInfo(
        edges=edges,
        bbox=largest.bbox,
        inner_bbox=inner if inner != largest.bbox and inner[0] < inner[2] and inner[1] < inner[3] else None,
        iso_format=iso_format(largest),
        containment=largest_cont,
        confidence=_confidence(largest, largest_cont, n_borders=len(kept)),
    )


def extend_frame(frame: FrameInfo, doc) -> FrameInfo:
    """
    Estende `frame` a quello che sta nella sua fascia, fra bordo esterno e
    squadratura: lineette delle zone, segni di centratura, scritte (MAP D28).
    Un edge non marcato è della cornice se sta dentro il bordo esterno, ha
    un tratto nella fascia e dentro la squadratura entra al più quanto è
    larga la fascia.
    Senza squadratura non c'è fascia: ritorna `frame` com'è. Non muta `doc`.
    """
    if frame.inner_bbox is None:
        return frame
    ox0, oy0, ox1, oy1 = frame.bbox
    ix0, iy0, ix1, iy1 = frame.inner_bbox
    band = min(ix0 - ox0, iy0 - oy0, ox1 - ix1, oy1 - iy1)
    if band <= 0:
        return frame
    outer = (ox0 - AXIS_EPS, oy0 - AXIS_EPS, ox1 + AXIS_EPS, oy1 + AXIS_EPS)
    taken = {id(e) for e in frame.edges}
    extra = []
    for e in doc.edges:
        if e.role != "unknown" or id(e) in taken:
            continue
        total, inner = segment_length(e.segment), length_inside(e.segment, frame.inner_bbox)
        in_sheet = total - length_inside(e.segment, outer) <= AXIS_EPS
        if in_sheet and total - inner > AXIS_EPS and inner <= band:
            extra.append(e)
    if not extra:
        return frame
    return replace(frame, edges=frame.edges + extra)


def rejected_border(doc, title_block) -> Optional[CoveredRectangle]:
    """
    Il riquadro di bordo più grande che racchiude `title_block` ma che
    `find_frame` non ha accettato (rapporto non ISO, o contenimento sotto
    soglia) — o None. Da chiamare quando `find_frame` ha dato None.

    Non è una cornice e non si marca: serve solo a dirlo. Un riquadro così
    resta nel disegno e `forge.island()` lo prende come contorno esterno di
    tutte le viste, a meno che qualcosa non lo apra per caso (su `B1250136`
    lo apriva la marcatura del cartiglio, che ne condivide il lato
    inferiore — MAP D15). Senza cartiglio dentro non si segnala niente: il
    rettangolo di un pezzo nudo non è un riquadro di impaginazione.
    """
    if title_block is None:
        return None
    txmin, tymin, txmax, tymax = title_block.bbox
    tol = 2 * AXIS_EPS
    enclosing = [
        r for r in find_rectangles(doc)
        if r.bbox[0] - tol <= txmin and r.bbox[1] - tol <= tymin
        and txmax <= r.bbox[2] + tol and tymax <= r.bbox[3] + tol
        and r.area > (txmax - txmin) * (tymax - tymin) * 1.5
    ]
    return max(enclosing, key=lambda r: r.area) if enclosing else None


def _confidence(rect: CoveredRectangle, cont: float, n_borders: int) -> float:
    """
    Confidenza grezza: parte dal contenimento, bonus se il formato ISO torna,
    bonus se ci sono due bordi (cornice a doppia squadratura, molto tipica).
    """
    score = cont
    if iso_format(rect) is not None:
        score += 0.05
    if n_borders >= 2:
        score += 0.05
    return max(0.0, min(1.0, score))
