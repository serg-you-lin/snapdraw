"""
tests/regression_reading.py
---------------------------
La lettura di un foglio reale, ridotta a un dict confrontabile:
cornice, riquadro del cartiglio, isole, viste, fori. La usano
`generate_regression.py` (scrive il golden) e `test_regression.py` (lo
confronta) — la stessa funzione da tutte e due le parti.

Nessuna confidenza nel golden: è un numero che si ritara, i fatti no.
"""

from pathlib import Path

import forge
import snapdraw as sd

REGRESSION = Path(__file__).parent / "examples" / "regression"
GOLDEN = REGRESSION / "json"
RULES = "generic"


def read_sheet(path: Path) -> dict:
    """Cornice, cartiglio, viste e fori di un foglio, come li legge snapdraw oggi."""
    doc = forge.load_dxf(str(path), role_rules=sd.load_rules(RULES))
    layout = sd.detect_frame(doc)
    sd.tag_layout(doc, layout)
    result = forge.island(doc)
    views = sd.read_views(result)
    holes = sd.read_holes(doc, result, views)

    frame = layout.frame
    title_block = layout.title_block
    return {
        "frame": None if frame is None else {"bbox": _r(frame.bbox), "iso_format": frame.iso_format},
        # i campi del cartiglio no, per ora: la lettura non è affidabile (MAP, "Problemi visti"),
        # fissarla nel golden vorrebbe dire dichiarare giusta una lettura sbagliata
        "title_block": None if title_block is None else {"bbox": _r(title_block.bbox)},
        "frame_flags": layout.flags,
        "clusters": len(result.clusters),
        "views": [{"kind": v.kind, "bbox": _r(v.bbox)} for v in views.views],
        "principal": views.principal,
        "depth": _r(views.depth),
        "view_flags": views.flags,
        "holes": {
            "summary": sd.describe_holes(holes),
            "scale": _r(holes.scale),
            "flags": holes.flags,
            "holes": [{"path": h.path, "through": h.through, "source": h.source, "drawn_depth": _r(h.drawn_depth)}
                      for h in holes.holes],
        },
    }


def _r(value):
    """Arrotonda a 3 decimali, anche dentro tuple; None resta None."""
    if value is None:
        return None
    if isinstance(value, (tuple, list)):
        return [round(float(v), 3) for v in value]
    return round(float(value), 3)
