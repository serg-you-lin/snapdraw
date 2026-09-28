"""
tests/test_regression.py
------------------------
Regressione sui fogli reali di `tests/examples/regression/` (ripuliti dei
dati del cliente): un test per foglio, generato a runtime, che rilegge il
foglio e lo confronta col golden `json/<nome>.json`.

Cosa protegge: cornice e riquadro del cartiglio trovati dove erano, il
numero di isole, le viste e la principale, la profondità, i fori. Se un test
fallisce: prima si capisce se il codice ha ragione, mai il contrario
(`generate_regression.py`).

`known_wrong` nel golden: {chiave: perché} per le letture che oggi sono
sbagliate. Il golden porta la verità, il test controlla che l'errore ci sia
ancora — quando si sistema, il test fallisce e la voce si toglie.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from regression_reading import GOLDEN, REGRESSION, read_sheet  # noqa: E402

TOL = 0.01   # mm — bbox, profondità; scala adimensionale, stessa tolleranza


def _compare(case, expected, actual, where="foglio"):
    """Confronto ricorsivo: numeri entro TOL, tutto il resto uguale."""
    if isinstance(expected, dict):
        case.assertEqual(sorted(expected), sorted(actual), f"{where}: chiavi diverse")
        for key in expected:
            _compare(case, expected[key], actual[key], f"{where}.{key}")
    elif isinstance(expected, list):
        case.assertEqual(len(expected), len(actual), f"{where}: lunghezze diverse")
        for i, (e, a) in enumerate(zip(expected, actual)):
            _compare(case, e, a, f"{where}[{i}]")
    elif isinstance(expected, float) and not isinstance(expected, bool):
        case.assertAlmostEqual(expected, actual, delta=TOL, msg=where)
    else:
        case.assertEqual(expected, actual, where)


def _make_test(dxf: Path, golden: Path):
    def test(self):
        expected = json.loads(golden.read_text(encoding="utf-8"))
        known_wrong = expected.pop("known_wrong", {})
        actual = read_sheet(dxf)
        for key, why in known_wrong.items():
            # errore noto: il golden ha la verità, snapdraw sbaglia ancora. Se ora torna,
            # il test lo dice: si toglie la voce da known_wrong, non si abbassa il golden
            self.assertNotEqual(expected.pop(key), actual.pop(key),
                                f"{dxf.stem}.{key} ora è giusto ({why}): toglilo da known_wrong")
        _compare(self, expected, actual, dxf.stem)
    return test


class TestRegression(unittest.TestCase):

    def test_ogni_foglio_ha_il_suo_golden(self):
        # un foglio aggiunto senza golden non deve passare inosservato
        missing = [p.name for p in REGRESSION.glob("*.dxf") if not (GOLDEN / f"{p.stem}.json").exists()]
        self.assertEqual(missing, [], "lancia tests/generate_regression.py")


for _dxf in sorted(REGRESSION.glob("*.dxf")):
    _golden = GOLDEN / f"{_dxf.stem}.json"
    if _golden.exists():
        setattr(TestRegression, f"test_{_dxf.stem}", _make_test(_dxf, _golden))


if __name__ == "__main__":
    unittest.main()
