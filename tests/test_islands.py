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

from islands_reading import GOLDEN, ISLANDS, read_islands  # noqa: E402
from test_regression import _compare  # noqa: E402


class TestIslands(unittest.TestCase):
    pass


def _make_test(dxf: Path, golden: Path):
    def test(self):
        expected = json.loads(golden.read_text(encoding="utf-8"))
        _compare(self, expected, read_islands(dxf), dxf.stem)
    return test


for _dxf in sorted(ISLANDS.glob("*.dxf")):
    _golden = GOLDEN / f"{_dxf.stem}.json"
    if _golden.exists():
        setattr(TestIslands, f"test_{_dxf.stem}", _make_test(_dxf, _golden))


if __name__ == "__main__":
    unittest.main()
