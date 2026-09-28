"""
framer/tag.py
-------------
Riporta il layout rilevato a forge: setta `edge.role` sugli `Edge` di
`doc.edges` che compongono cornice e cartiglio.

È l'aggancio "opzione B" chiuso in forge D30: un consumatore marca la geometria
**prima** di `forge.heal`, e heal tiene quegli edge fuori dal grafo
(`_split_labeled` estrae ogni ruolo deciso e non strutturale). La geometria non
si perde — finisce in `trash_entities` col ruolo intatto e l'output DXF la
scrive sul layer registrato in `roles.py` (`Frame`, `TitleBlock`), non su
`Trash` (forge D31).

`"frame"` e `"title_block"` sono **entrambi** slug di consumatore: forge non li
conosce (`ContourRole.FRAME` è stato rimosso in D31), li conserva e basta. Gli
slug e il loro stile (colore/layer) sono costruiti in `roles.py` — qui si
importano soltanto, mai definiti inline (forge D47, "roles out of core": lo
stesso schema con cui forge costruisce il proprio vocabolario di `detect()`).
"""

from __future__ import annotations

from .model import FrameLayout
from .roles import FRAME as FRAME_ROLE
from .roles import TITLE_BLOCK as TITLE_BLOCK_ROLE


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
