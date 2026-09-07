"""
framer
------
Rilevamento automatico di cornice e cartiglio nei disegni tecnici impaginati.

Framer è un **consumatore di forge**: usa `forge.load_dxf` come motore, fa il
suo lavoro geometrico sulla geometria grezza, e riporta le decisioni a forge
settando `edge.role` prima di `forge.heal` (aggancio "opzione B", forge D30).
Non modifica forge e non ragiona dentro forge: forge resta neutro e
deterministico, Framer si adatta (vedi FRAMER.md nel repo di forge, DESIGN.md
qui).

Workflow:

    import forge, framer

    doc = forge.load_dxf("disegno.dxf")
    layout = framer.detect(doc)          # cornice + cartiglio sulla geometria grezza
    framer.tag_layout(doc, layout)       # marca gli Edge → role="frame" / "title_block"
    result = forge.heal(doc)             # heal li esclude: l'outer vero dei pezzi emerge,
                                         # il cartiglio non è un cluster
    fields = framer.read_titleblock(layout)   # (stub) campi del cartiglio

Stato: pre-alpha. `detect_frame` è portato e funzionante; il rilevamento
cartiglio e la lettura delle celle sono stub — vedi TODO.md.
"""

from __future__ import annotations

from .detect import detect
from .model import BBox, Cell, FrameInfo, FrameLayout, TitleBlock
from .tag import tag_layout
from .titleblock import read_titleblock

try:
    from importlib.metadata import version as _pkg_version, PackageNotFoundError
    try:
        __version__ = _pkg_version("framer")
    except PackageNotFoundError:
        __version__ = "0.0.0+dev"
except ImportError:  # pragma: no cover
    __version__ = "0.0.0+dev"

__all__ = [
    "detect",
    "tag_layout",
    "read_titleblock",
    "FrameLayout",
    "FrameInfo",
    "TitleBlock",
    "Cell",
    "BBox",
]
