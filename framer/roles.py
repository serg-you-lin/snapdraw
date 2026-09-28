"""
framer/roles.py
----------------
Vocabolario di ruolo di framer — cornice e cartiglio. Prima viveva inline in
`tag.py`; ora sta a sé, sullo stesso schema con cui forge stesso registra il
vocabolario manifatturiero di `detect()` (`forge/tools/manufacturing_role.py`,
forge D47 "roles out of core"): un consumatore costruisce i propri ruoli e la
propria palette **fuori** da forge, con gli stessi meccanismi pubblici
(`forge.register_role_style`) che forge userebbe per sé — nessun trattamento
privilegiato.

`CONSTRUCTION` (assi, linee di costruzione — assegnato al caricamento dalle
regole di `rules/`, MAP D16/D17) idem: non è contorno di pezzo,
`heal()`/`island()` lo lasciano fuori.

`FRAME` e `TITLE_BLOCK` sono decorazione, non topologia di pezzo: non serve
un `is_structural` qui (a differenza di `hole`/`countersink`/`threaded_hole`
in forge) — il default di `heal()` già li tiene fuori dal grafo.
"""

from __future__ import annotations

import forge

FRAME = forge.normalize_role("frame")
TITLE_BLOCK = forge.normalize_role("title_block")
CONSTRUCTION = forge.normalize_role("construction")

LAYER_FRAME = "Frame"
LAYER_TITLE_BLOCK = "TitleBlock"
LAYER_CONSTRUCTION = "Construction"


def register_defaults() -> None:
    """
    Registra colore + nome layer di default per `frame`/`title_block` —
    gira all'import di questo modulo (quindi automaticamente quando `framer`
    viene importato, dato che `framer/__init__.py` importa `tag`, che importa
    questo modulo). Zero stato da settare a mano in ogni script chiamante.
    """
    forge.register_role_style(FRAME, forge.RoleStyle(color=(20, 20, 20), layer_name=LAYER_FRAME))
    forge.register_role_style(TITLE_BLOCK, forge.RoleStyle(color=(20, 20, 20), layer_name=LAYER_TITLE_BLOCK))
    forge.register_role_style(CONSTRUCTION, forge.RoleStyle(color=(200, 60, 30), layer_name=LAYER_CONSTRUCTION))


register_defaults()
