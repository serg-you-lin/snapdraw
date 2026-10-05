"""
snapdraw
--------
Rilevamento automatico di cornice e cartiglio nei disegni tecnici impaginati.

snapdraw è un **consumatore di forge**: usa `forge.load_dxf` come motore, fa il
suo lavoro geometrico sulla geometria grezza, e riporta le decisioni a forge
settando `edge.role` prima della lettura di forge — `heal` o `island`, scelta
del chiamante (aggancio "opzione B", forge D30).
Non modifica forge e non ragiona dentro forge: forge resta neutro e
deterministico, snapdraw si adatta (vedi SNAPDRAW.md nel repo di forge, DESIGN.md
qui).

Workflow di rilevamento — `detect_frame` è una ricetta sopra passi pubblici
(`find_frame`, `find_titleblock`), stesso schema di `forge.heal` (forge D62):

    import forge

    import snapdraw as sd

    # regole di ruolo al caricamento: assi e costruzione (MAP D17)
    doc = forge.load_dxf("disegno.dxf", role_rules=sd.load_rules("generic"))
    layout = sd.detect_frame(doc)    # cornice + cartiglio sulla geometria grezza
    fields = sd.read_titleblock(layout)   # campi del cartiglio, per regex su un vocabolario ISO generico

    # solo se servono le viste: marca, poi leggi per isole (MAP D14)
    sd.tag_layout(doc, layout)       # marca gli Edge → role="frame" / "title_block"
    result = forge.island(doc)

Workflow di generazione (il verso "aggiungi" — un disegno senza cornice):

    doc = forge.load_dxf("pezzo_nudo.dxf")
    sd.add_frame(doc)                            # cornice ISO attorno alla geometria esistente
    sd.add_title_block(doc, fields={"material": "S235JR", "quantity": "2"})
    result = forge.heal(doc)
    forge.to_dxf(result, doc).saveas("pezzo_framed.dxf")

Stato: pre-alpha. `find_frame` e `find_titleblock`/`read_titleblock` sono
portati e funzionanti (soglie ancora grezze, da tarare su fixture reali); la
generazione (`add_frame`, `add_title_block`) è vettoriale, senza
logo/immagine — vedi TODO.md.
"""

from __future__ import annotations

from .frame import extend_frame, find_frame, rejected_border
from .generate import DEFAULT_TITLE_BLOCK_TEMPLATE, add_frame, add_title_block
from .features import (describe_features, diameter_callouts, feature_contours, feature_metadata, feature_trace,
                       group_features, parse_callout, read_features, tag_features, view_scales)
from .model import (BBox, Callout, Cell, Feature, FeatureGroup, FeatureLayout, FieldSlot, FrameInfo, FrameLayout,
                    TitleBlock, TitleBlockTemplate, Trace, View, ViewLayout)
from .roles import (CONSTRUCTION, COUNTERBORE, COUNTERSINK, FRAME, HOLE, OPENING, SEATED_HOLE, SLOT, THREADED_HOLE,
                    TITLE_BLOCK)
from .rules import load_rules, rules_from_dict
from .recipe import detect_frame
from .render import render_view, render_views, view_edges
from .tag import tag_layout
from .titleblock import extend_titleblock, find_titleblock, read_titleblock
from .views import classify_view, principal_view, projection_mates, read_views, view_depth

try:
    from importlib.metadata import version as _pkg_version, PackageNotFoundError
    try:
        __version__ = _pkg_version("snapdraw")
    except PackageNotFoundError:
        __version__ = "0.0.0+dev"
except ImportError:  # pragma: no cover
    __version__ = "0.0.0+dev"

__all__ = [
    "detect_frame",
    "find_frame",
    "extend_frame",
    "rejected_border",
    "find_titleblock",
    "extend_titleblock",
    "tag_layout",
    "load_rules",
    "rules_from_dict",
    "read_titleblock",
    "read_views",
    "classify_view",
    "projection_mates",
    "principal_view",
    "view_depth",
    "View",
    "ViewLayout",
    "render_views",
    "render_view",
    "view_edges",
    "read_features",
    "describe_features",
    "tag_features",
    "feature_metadata",
    "view_scales",
    "feature_contours",
    "feature_trace",
    "diameter_callouts",
    "parse_callout",
    "group_features",
    "Feature",
    "Callout",
    "Trace",
    "FeatureGroup",
    "FeatureLayout",
    "add_frame",
    "add_title_block",
    "FrameLayout",
    "FrameInfo",
    "TitleBlock",
    "Cell",
    "BBox",
    "FieldSlot",
    "TitleBlockTemplate",
    "DEFAULT_TITLE_BLOCK_TEMPLATE",
    "FRAME",
    "TITLE_BLOCK",
    "CONSTRUCTION",
    "HOLE",
    "THREADED_HOLE",
    "COUNTERSINK",
    "COUNTERBORE",
    "SEATED_HOLE",
    "SLOT",
    "OPENING",
]
