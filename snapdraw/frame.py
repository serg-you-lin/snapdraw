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

from typing import Optional

from forge.core.geometry.axis import CoveredRectangle

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
        iso_format=iso_format(largest),
        containment=largest_cont,
        confidence=_confidence(largest, largest_cont, n_borders=len(kept)),
    )


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
