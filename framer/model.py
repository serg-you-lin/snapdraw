"""
framer/model.py
---------------
Il dominio di Framer: cosa vuol dire "cornice" e "cartiglio" in un disegno
impaginato, e cosa Framer restituisce a chi lo chiama.

Nessuna dipendenza da forge o da un formato: dataclass pure. Gli `Edge` che
questi oggetti trattengono (`FrameInfo.edges`, `TitleBlock.edges`) sono
riferimenti agli `Edge` di `forge.load_dxf(...).edges` — Framer li individua e
li marca, non ne fa copie.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# BBox = (xmin, ymin, xmax, ymax)
BBox = Tuple[float, float, float, float]


@dataclass
class FrameInfo:
    """
    La cornice di formato: il riquadro esterno del foglio.

    edges       : gli Edge di doc.edges che compongono il riquadro
    bbox        : (xmin, ymin, xmax, ymax) del riquadro
    iso_format  : formato ISO riconosciuto dalle dimensioni ("A4", "A3", ...) o None
    containment : frazione della geometria restante contenuta nella bbox (0..1)
    confidence  : 0..1 — quanto Framer è sicuro che questo sia la cornice
    """
    edges:       list
    bbox:        BBox
    iso_format:  Optional[str] = None
    containment: float = 0.0
    confidence:  float = 0.0


@dataclass
class Cell:
    """Una cella del cartiglio: un rettangolo interno e il testo che racchiude."""
    bbox: BBox
    text: str = ""


@dataclass
class TitleBlock:
    """
    Il cartiglio: il riquadro delle informazioni, suddiviso in celle.

    edges      : gli Edge di doc.edges che compongono il riquadro (bordo + griglia)
    bbox       : (xmin, ymin, xmax, ymax) del riquadro
    cells      : le celle interne con il testo contenuto (vuoto finché
                 detect_titleblock è uno stub)
    confidence : 0..1
    """
    edges:      list
    bbox:       BBox
    cells:      List[Cell] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class FrameLayout:
    """
    Il risultato di `framer.detect(doc)`.

    frame       : la cornice, o None se Framer non l'ha individuata con sicurezza
    title_block : il cartiglio, o None
    flags       : diagnostica non bloccante — "frame: uncertain",
                  "title_block: uncertain", "multiple_frames", ...
    """
    frame:       Optional[FrameInfo] = None
    title_block: Optional[TitleBlock] = None
    flags:       List[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return self.frame is None and self.title_block is None
