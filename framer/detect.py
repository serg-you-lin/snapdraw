"""
framer/detect.py
----------------
L'orchestratore di Framer: `detect(doc)` → `FrameLayout`.

Gira sulla geometria GREZZA di `doc` (`forge.load_dxf(...)`), **prima** di
`forge.heal`. Combina il rilevamento cornice e quello cartiglio, che sono
indipendenti (il cartiglio può stare fuori da una cornice, o la cornice può
mancare), e raccoglie i flag di incertezza.

Uso tipico:

    import forge, framer

    doc = forge.load_dxf("disegno.dxf")
    layout = framer.detect(doc)
    framer.tag_layout(doc, layout)      # marca gli Edge di cornice/cartiglio
    result = forge.heal(doc)            # heal li esclude → l'outer vero emerge
"""

from __future__ import annotations

from .frame import detect_frame
from .model import FrameLayout
from .titleblock import detect_titleblock


def detect(doc) -> FrameLayout:
    """
    Rileva cornice e cartiglio nella geometria grezza di `doc`.

    Non muta `doc`: individua soltanto. Per riportare le decisioni a forge
    (settare `edge.role`) usa `framer.tag_layout(doc, layout)`.
    """
    layout = FrameLayout()

    layout.frame = detect_frame(doc)
    if layout.frame is None:
        layout.flags.append("frame: uncertain")

    layout.title_block = detect_titleblock(doc, frame=layout.frame)
    if layout.title_block is None:
        layout.flags.append("title_block: uncertain")

    return layout
