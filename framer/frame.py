"""
framer/frame.py
---------------
Rilevamento della cornice di formato.

Porta l'algoritmo del vecchio `core/classification/frame_detector.py` di forge
(rimosso in forge MAP D24 perché girava *prima* di heal — cioè è roba del
consumatore, vedi FRAMER.md) e lo riscrive sugli `Edge` / `LineSeg` di forge.

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

from .geometry import (
    Rect, containment, find_rectangles, is_iso_ratio, iso_format,
)
from .model import FrameInfo

CONTAINMENT_THRESHOLD = 0.80


def detect_frame(doc, containment_threshold: float = CONTAINMENT_THRESHOLD) -> Optional[FrameInfo]:
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
        for e in rect.edges:
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


def _confidence(rect: Rect, cont: float, n_borders: int) -> float:
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
