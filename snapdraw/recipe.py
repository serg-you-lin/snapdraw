"""
snapdraw/recipe.py
------------------
La ricetta di snapdraw: `detect_frame(doc)` → `FrameLayout`.

Stesso schema di forge D62 (`heal()` è una ricetta sopra passi pubblici):
qui c'è solo la composizione di default, i passi stanno nei loro moduli e
sono pubblici — `find_frame` e `rejected_border` (`frame.py`),
`find_titleblock` e `extend_titleblock` (`titleblock.py`), `tag_layout`
(`tag.py`). Chi vuole un'altra lettura li compone a mano (per esempio solo
la cornice, o il cartiglio con una cornice nota da `add_frame`).

Gira sulla geometria GREZZA di `doc` (`forge.load_dxf(...)`) e **non
presuppone nessuna lettura a valle**: `heal()`, `island()` o niente del tutto
sono scelte del chiamante. snapdraw interpreta, forge trasforma la topologia
(`frame_heal_forge_architecture.md`).

Uso tipico:

    import forge

    import snapdraw as sd

    doc = forge.load_dxf("disegno.dxf")
    layout = sd.detect_frame(doc)   # cornice + cartiglio, doc non mutato
    sd.tag_layout(doc, layout)      # marca gli Edge → role="frame" / "title_block"
    result = forge.island(doc)          # oppure forge.heal(doc): li lasciano fuori entrambi
"""

from __future__ import annotations

from .frame import find_frame, rejected_border
from .model import FrameLayout
from .titleblock import extend_titleblock, find_titleblock


def detect_frame(doc) -> FrameLayout:
    """
    Rileva cornice e cartiglio nella geometria grezza di `doc`.

    Compone `find_frame`, `find_titleblock` + `extend_titleblock` (il
    cartiglio si prende le tabelle attaccate, MAP D15) e raccoglie i flag
    di incertezza. Cornice e cartiglio sono indipendenti: il cartiglio può
    stare fuori da una cornice, o la cornice può mancare; la cornice trovata
    è solo un bonus di punteggio per il cartiglio. Se la cornice manca ma un
    riquadro non accettato racchiude il cartiglio, lo dice nei flag
    (`rejected_border`): quel riquadro resta nel disegno.

    Non muta `doc`: individua soltanto. Per riportare le decisioni a forge
    (settare `edge.role`) usa `sd.tag_layout(doc, layout)`.
    """
    layout = FrameLayout()

    layout.frame = find_frame(doc)
    if layout.frame is None:
        layout.flags.append("frame: uncertain")

    title_block = find_titleblock(doc, frame=layout.frame)
    if title_block is None:
        layout.flags.append("title_block: uncertain")

    # sul cartiglio prima dell'estensione: le tabelle attaccate possono
    # uscire dal riquadro (B1250136, la tabella di distribuzione a sinistra)
    if layout.frame is None and (border := rejected_border(doc, title_block)) is not None:
        b = ", ".join(f"{v:.0f}" for v in border.bbox)
        layout.flags.append(f"frame: rejected border ({b}) encloses the title block, left in the drawing")

    if title_block is not None:
        title_block = extend_titleblock(title_block, doc, frame=layout.frame)
    layout.title_block = title_block

    return layout
