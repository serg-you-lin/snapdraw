"""
tests/test_views.py
-------------------
Test della lettura delle viste: classificazione, compagni di proiezione,
vista principale, profondità, simboli. Fogli costruiti con
`forge.load_geometry` e letti con `forge.island`.
"""

import math
import unittest

import forge
import snapdraw as sd


def _rect(x, y, w, h):
    return {"type": "polygon",
            "points": [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]}


def _iso_box(x, y, a, b, c):
    """Assonometria isometrica di un parallelepipedo a×b×c: il contorno esagonale
    e i tre spigoli interni verso il vertice vicino."""
    c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))
    ex, ey = (a * c30, a * s30), (-b * c30, b * s30)
    o = (x + b * c30, y)
    p = lambda *v: (o[0] + sum(t[0] for t in v), o[1] + sum(t[1] for t in v))
    up = (0, c)
    hexagon = [p(), p(ex), p(ex, up), p(ex, ey, up), p(ey, up), p(ey)]
    edges = [{"type": "line", "start": hexagon[i], "end": hexagon[(i + 1) % 6]} for i in range(6)]
    edges += [{"type": "line", "start": p(up), "end": q} for q in (p(), p(ex, up), p(ey, up))]
    return edges


def _read(entities):
    return sd.read_views(forge.island(forge.load_geometry(entities)))


class TestReadViews(unittest.TestCase):

    def test_terna_frontale_laterale_pianta(self):
        # frontale 100x50, laterale 3x50 alla stessa altezza, pianta 100x3 sotto
        layout = _read([_rect(0, 100, 100, 50), _rect(150, 100, 3, 50), _rect(0, 50, 100, 3)])
        principal = layout.views[layout.principal]
        self.assertEqual((round(principal.width), round(principal.height)), (100, 50))
        self.assertEqual(len(principal.height_mates), 1)
        self.assertEqual(len(principal.width_mates), 1)
        self.assertAlmostEqual(layout.depth, 3.0)
        self.assertEqual(layout.flags, [])

    def test_assonometria_non_ha_compagni(self):
        layout = _read([_rect(0, 100, 100, 50), _rect(150, 100, 3, 50), *_iso_box(300, 100, 60, 40, 30)])
        kinds = sorted(v.kind for v in layout.views)
        self.assertEqual(kinds, ["orthographic", "orthographic", "pictorial"])
        iso = next(v for v in layout.views if v.kind == "pictorial")
        self.assertEqual((iso.height_mates, iso.width_mates), ([], []))

    def test_solo_frontale_e_laterale_principale_da_una_proiezione(self):
        layout = _read([_rect(0, 0, 180, 27), _rect(250, 0, 5, 27)])
        self.assertEqual(round(layout.views[layout.principal].width), 180)
        self.assertAlmostEqual(layout.depth, 5.0)
        self.assertIn("principal: single projection", layout.flags)

    def test_vista_unica_e_la_principale(self):
        layout = _read([_rect(0, 0, 1180, 65)])
        self.assertEqual(layout.principal, 0)
        self.assertIsNone(layout.depth)
        self.assertEqual(layout.flags, [])

    def test_isola_minuscola_isolata_e_un_simbolo(self):
        layout = _read([_rect(0, 100, 46, 48), _rect(80, 100, 3, 48),
                        {"type": "circle", "center": (200, 20), "radius": 2.1}])
        symbol = [v for v in layout.views if v.kind == "symbol"]
        self.assertEqual(len(symbol), 1)
        self.assertAlmostEqual(symbol[0].width, 4.2, places=1)

    def test_compagni_discordi_niente_profondita(self):
        # due laterali alla stessa altezza ma larghe 3 e 20: la profondità non è una
        layout = _read([_rect(0, 100, 100, 50), _rect(150, 100, 3, 50),
                        _rect(200, 100, 20, 50), _rect(0, 50, 100, 3)])
        self.assertIsNone(layout.depth)
        self.assertIn("depth: inconsistent", layout.flags)

    def test_nessuna_vista_ortogonale(self):
        layout = _read(_iso_box(0, 0, 60, 40, 30))
        self.assertIsNone(layout.principal)
        self.assertIn("principal: uncertain", layout.flags)


if __name__ == "__main__":
    unittest.main()
