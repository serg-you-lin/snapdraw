"""
framer/tag.py
-------------
Riporta il layout rilevato a forge: setta `edge.role` sugli `Edge` di
`doc.edges` che compongono cornice e cartiglio.

È l'aggancio "opzione B" chiuso in forge D30: un consumatore marca la geometria
**prima** di `forge.heal`, e heal tiene quegli edge fuori dal grafo
(`_split_labeled` estrae ogni ruolo deciso e non strutturale). La geometria non
si perde — finisce in `trash_entities` col ruolo intatto e l'output DXF la
riscrive nativa sul layer di destinazione.

Lo slug passa da `forge.normalize_role`: `"frame"` è un ruolo che forge
conosce (`ContourRole.FRAME`), `"title_block"` è uno slug custom che forge
conserva senza classificarlo (D27).
"""

from __future__ import annotations

import forge

from .model import FrameLayout

FRAME_ROLE = forge.normalize_role("frame")
TITLE_BLOCK_ROLE = forge.normalize_role("title_block")


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
