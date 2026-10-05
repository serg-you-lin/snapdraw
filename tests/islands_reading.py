"""
tests/islands_reading.py
------------------------
Le isole di un foglio, ridotte a un dict confrontabile: per ogni isola il
riquadro del contorno esterno e quanti contorni interni ha, più le linee
aperte che stanno fuori da ogni isola. La usano `generate_islands.py` (scrive
il golden) e `test_islands.py` (lo confronta).

Fogli in `examples/islands/`: solo quelli che Federico ha giudicato giusti
sulla pagina "Scala delle isole" (5 ottobre, forge D99, MAP D30-D31). Le
viste 3D col contorno a otto (anch_07, anch_08) non ci sono finché non
sono giuste.
"""

from pathlib import Path

import forge
import snapdraw as sd

ISLANDS = Path(__file__).parent / "examples" / "islands"
GOLDEN = ISLANDS / "json"
RULES = "generic"


def read_islands(path: Path) -> dict:
    """Le isole di un foglio come le legge snapdraw oggi (cornice e cartiglio tolti)."""
    doc = forge.load_dxf(str(path), role_rules=sd.load_rules(RULES))
    sd.tag_layout(doc, sd.detect_frame(doc))
    result = sd.sheet_islands(doc)
    return {
        "islands": [{"bbox": [round(float(v), 3) for v in c.outer.polygon.bounds], "inners": len(c.inners)}
                    for c in result.clusters],
        "open_outside": sum(1 for t in result.trash_entities
                            if t.role == "unknown" and getattr(t, "cluster_ref", None) is None),
    }
