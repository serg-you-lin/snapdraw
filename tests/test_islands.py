"""
tests/test_islands.py
---------------------
Golden delle isole sui fogli di `tests/examples/islands/` (giudicati giusti
da Federico, MAP D30-D31): un test per foglio, generato a runtime, che rilegge
le isole e le confronta col golden `json/<nome>.json`. Se fallisce: prima si
capisce se il codice ha ragione, mai il contrario (`generate_islands.py`).
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from islands_reading import GOLDEN, read_islands, sheets  # noqa: E402
from test_regression import _compare  # noqa: E402


class TestIslands(unittest.TestCase):
    pass


def _make_test(dxf: Path, golden: Path):
    def test(self):
        expected = json.loads(golden.read_text(encoding="utf-8"))
        _compare(self, expected, read_islands(dxf), dxf.stem)
    return test


# golden fermi apposta: topo 0.14.0 (D101-D103) cambia la lettura per isole di
# questi fogli e i golden di topo stessi sono fermi finché i dubbi su D103
# (fantasmi, inner annidati) non sono chiariti — si rigenerano insieme a quelli
# di topo, guardando prima i DXF; allora questa lista si svuota
KNOWN_STALE = {"anch_02", "anch_03", "anch_06", "anch_07"}

for _dxf in sheets():
    _golden = GOLDEN / f"{_dxf.stem}.json"
    if _golden.exists():
        _test = _make_test(_dxf, _golden)
        if _dxf.stem in KNOWN_STALE:
            _test = unittest.expectedFailure(_test)
        setattr(TestIslands, f"test_{_dxf.stem}", _test)


if __name__ == "__main__":
    unittest.main()
