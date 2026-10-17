"""
snapdraw/roles.py
-----------------
Vocabolario di ruolo di snapdraw — cornice e cartiglio. Prima viveva inline in
`tag.py`; ora sta a sé, sullo stesso schema con cui topo stesso registra il
vocabolario manifatturiero di `detect()` (`topo/tools/manufacturing_role.py`,
topo D47 "roles out of core"): un consumatore costruisce i propri ruoli e la
propria palette **fuori** da topo, con gli stessi meccanismi pubblici
(`topo.register_role_style`) che topo userebbe per sé — nessun trattamento
privilegiato.

`CONSTRUCTION` (assi, linee di costruzione — assegnato al caricamento dalle
regole di `rules/`, MAP D16/D17) idem: non è contorno di pezzo,
`heal()`/`island()` lo lasciano fuori.

`FRAME` e `TITLE_BLOCK` sono decorazione, non topologia di pezzo: non serve
un `is_structural` qui (a differenza di `hole`/`countersink`/`threaded_hole`
in topo) — il default di `heal()` già li tiene fuori dal grafo.

Le feature delle viste (`features.py`, MAP D23): un ruolo per tipo di foro —
`HOLE` (foro semplice), `THREADED_HOLE`, `COUNTERSINK` (svasato),
`COUNTERBORE` (lamato, incassato), `SEATED_HOLE` (con sede, tipo non
determinato) — più `SLOT` e `OPENING`. `hole`, `threaded_hole`,
`countersink` hanno lo slug e il layer di topo. Si assegnano a feature già
lette, dopo `island()`: non sono ruoli di `Edge` e non toccano la lettura
delle isole. Il ruolo dice che cosa è la feature: chi sviluppa il pezzo da
tagliare (snapbend) sa dove metterla. I colori sono un default per guardare
(il foro viola, sovrascrive il magenta di topo per chi importa snapdraw);
chi esporta passa i suoi con `role_styles`.
"""

from __future__ import annotations

import topo

FRAME = topo.normalize_role("frame")
TITLE_BLOCK = topo.normalize_role("title_block")
CONSTRUCTION = topo.normalize_role("construction")

HOLE = topo.normalize_role("hole")
THREADED_HOLE = topo.normalize_role("threaded_hole")
COUNTERSINK = topo.normalize_role("countersink")
COUNTERBORE = topo.normalize_role("counterbore")
SEATED_HOLE = topo.normalize_role("seated_hole")
SLOT = topo.normalize_role("slot")
OPENING = topo.normalize_role("opening")

LAYER_FRAME = "Frame"
LAYER_TITLE_BLOCK = "TitleBlock"
LAYER_CONSTRUCTION = "Construction"

# ruolo, colore di default, layer (per gli slug in comune con topo, il layer di topo)
FEATURE_STYLES = [
    (HOLE,          (150, 0, 200),   "Hole"),
    (THREADED_HOLE, (0, 160, 160),   "ThreadHole"),
    (COUNTERSINK,   (40, 60, 220),   "Countersink"),
    (COUNTERBORE,   (200, 110, 230), "Counterbore"),
    (SEATED_HOLE,   (220, 40, 120),  "SeatedHole"),
    (SLOT,          (230, 120, 0),   "Slot"),
    (OPENING,       (0, 150, 70),    "Opening"),
]


def register_defaults() -> None:
    """
    Registra colore + nome layer di default per cornice, cartiglio, costruzione e feature —
    gira all'import di questo modulo (quindi automaticamente quando `snapdraw`
    viene importato, dato che `snapdraw/__init__.py` importa `tag`, che importa
    questo modulo). Zero stato da settare a mano in ogni script chiamante.
    """
    topo.register_role_style(FRAME, topo.RoleStyle(color=(20, 20, 20), layer_name=LAYER_FRAME))
    topo.register_role_style(TITLE_BLOCK, topo.RoleStyle(color=(20, 20, 20), layer_name=LAYER_TITLE_BLOCK))
    topo.register_role_style(CONSTRUCTION, topo.RoleStyle(color=(200, 60, 30), layer_name=LAYER_CONSTRUCTION))
    for role, color, layer in FEATURE_STYLES:
        topo.register_role_style(role, topo.RoleStyle(color=color, layer_name=layer))


register_defaults()
