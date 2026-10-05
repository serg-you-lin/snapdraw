"""
tests/test_rules.py
-------------------
Test delle regole di ruolo (MAP D17): `rules/<nome>.json` → `forge.RoleRule`,
da passare a `forge.load_dxf(role_rules=...)`.

Il caso vero è `vista_pianta_assi` (tests/examples/rules, copia anonimizzata
di un disegno reale): la vista in pianta mancava perché i suoi assi la
legavano alle quote. Con le regole
generiche gli assi sono `construction` al caricamento e `forge.island()` la
ritrova.
"""

import json
import tempfile
import unittest
from pathlib import Path

import forge
import snapdraw as sd

EXAMPLES = Path(__file__).resolve().parent / "examples" / "rules"


class TestLoadRules(unittest.TestCase):

    def test_generic_prima_il_tratto_e_punto(self):
        rules = sd.load_rules("generic")
        self.assertEqual(rules[0].role, sd.CONSTRUCTION)
        self.assertEqual(rules[0].dash, "chain")

    def test_lista_di_nomi_diventa_una_regola_per_voce(self):
        rules = sd.rules_from_dict({"rules": [
            {"role": "construction", "name_contains": ["axis", "assi"]},
        ]})
        self.assertEqual([r.name_contains for r in rules], ["axis", "assi"])
        self.assertTrue(all(r.role == sd.CONSTRUCTION for r in rules))

    def test_campo_sconosciuto_alza(self):
        # un refuso non deve diventare una regola che non matcha mai
        with self.assertRaises(ValueError):
            sd.rules_from_dict({"rules": [{"role": "construction", "name_contain": "axis"}]})

    def test_composizione_studio_prima_del_generico(self):
        # lo studio mette le sue regole prima: vince la prima che corrisponde
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "studio_x.json").write_text(json.dumps({
                "name": "studio_x",
                "rules": [{"role": "bending", "name": "PIEGHE", "dash": "chain"}],
            }), encoding="utf-8")
            rules = sd.load_rules("studio_x", folder=tmp) + sd.load_rules("generic")
        self.assertEqual(rules[0].role, "bending")
        self.assertEqual(rules[1].role, sd.CONSTRUCTION)


class TestRegoleSuDisegnoVero(unittest.TestCase):

    def _island_bounds(self, role_rules):
        doc = forge.load_dxf(str(EXAMPLES / "vista_pianta_assi.dxf"), role_rules=role_rules)
        sd.tag_layout(doc, sd.detect_frame(doc))
        return [tuple(round(v) for v in c.outer.polygon.bounds) for c in sd.sheet_islands(doc).clusters]

    def test_la_vista_in_pianta_ritorna(self):
        plan_view = (36, 218, 136, 268)
        self.assertNotIn(plan_view, self._island_bounds(()))
        self.assertIn(plan_view, self._island_bounds(sd.load_rules("generic")))


if __name__ == "__main__":
    unittest.main()
