"""
framer/frame.py
---------------
Rilevamento della cornice di formato.

Porta l'algoritmo del vecchio `core/classification/frame_detector.py` di forge
(rimosso in forge MAP D24 perché girava *prima* di heal — cioè è roba del
consumatore, vedi FRAMER.md) e lo riscrive sugli `Edge` / `LineSeg` di forge
invece che su `RawSegment` propri.

Algoritmo:
    1. tra i rettangoli chiusi (`geometry.find_rectangles`), tieni quelli con
       rapporto dei lati ≈ √2 (formati ISO), tolleranza ±5%;
    2. per ognuno calcola il contenimento: frazione della geometria restante
       che sta dentro la sua bbox;
    3. tieni i candidati con contenimento ≥ 80%; tra questi prendi il più
       grande — quella è la cornice;
    4. conservativo: se nessuno supera la soglia, ritorna None. Meglio un
       cluster sporco che buttare via la geometria di un pezzo.
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

    Ritorna un `FrameInfo` con gli `Edge` del riquadro, oppure `None` se non
    c'è un candidato convincente (il chiamante mette "frame: uncertain" nei
    flag e non marca niente).
    """
    candidates = [r for r in find_rectangles(doc) if is_iso_ratio(r)]
    if not candidates:
        return None

    scored = [(r, containment(r, doc)) for r in candidates]
    valid = [(r, c) for r, c in scored if c >= containment_threshold]
    if not valid:
        return None

    rect, cont = max(valid, key=lambda rc: rc[0].area)
    return FrameInfo(
        edges=list(rect.edges),
        bbox=rect.bbox,
        iso_format=iso_format(rect),
        containment=cont,
        confidence=_confidence(rect, cont, n_candidates=len(valid)),
    )


def _confidence(rect: Rect, cont: float, n_candidates: int) -> float:
    """
    Confidenza grezza: parte dal contenimento, penalizza se più candidati
    hanno passato la soglia (cornice ambigua) o se il formato ISO non torna.
    """
    score = cont
    if n_candidates > 1:
        score -= 0.15
    if iso_format(rect) is None:
        score -= 0.10
    return max(0.0, min(1.0, score))
