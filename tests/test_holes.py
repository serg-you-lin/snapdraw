"""
tests/test_holes.py
-------------------
Test della lettura dei fori: cerchi della vista principale, traccia nelle
viste compagne, quota di diametro, passante per convenzione, scala delle
quote. Fogli costruiti con `forge.load_geometry` e letti con `forge.island`;
il caso vero è `leva_01` (tests/examples/complete_drawings).
"""

import unittest
from pathlib import Path

import forge
import framer
from forge.model.style import EdgeStyle

EXAMPLES = Path(__file__).parent / "examples" / "complete_drawings"
HIDDEN = EdgeStyle(linetype="HIDDEN", linetype_pattern=(1.0, 0.5, -0.25))


def _rect(x, y, w, h):
    return {"type": "polyline", "closed": True,
            "points": [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]}


def _walls(x0, x1, y, r):
    """Le due pareti nascoste di un foro di raggio r alla quota y, da x0 a x1."""
    return [{"type": "line", "start": (x0, y - r), "end": (x1, y - r)},
            {"type": "line", "start": (x0, y + r), "end": (x1, y + r)}]


def _read(entities, hidden=0, dimensions=()):
    doc = forge.load_geometry(entities)
    if hidden:
        for edge in doc.edges[-hidden:]:
            edge.style = HIDDEN
    doc.annotations.extend(dimensions)
    result = forge.island(doc)
    return framer.read_holes(doc, result, framer.read_views(result))


def _diameter(text, center, r):
    return forge.Dimension(position=(center[0] + 10, center[1] + 10), source_kind="DIMENSION",
                           dim_type="diameter", text_override=text, measured_value=2 * r,
                           measured_points=[(center[0] - r, center[1]), (center[0] + r, center[1])])


# frontale 100x50 con un foro r=3 in (30, 25), laterale 5x50 a destra
FRONT = [_rect(0, 0, 100, 50), {"type": "circle", "center": (30, 25), "radius": 3}]
SIDE = _rect(150, 0, 5, 50)


class TestReadHoles(unittest.TestCase):

    def test_senza_indicazioni_passante_per_convenzione(self):
        holes = _read([*FRONT, SIDE])
        hole, = holes.holes
        self.assertTrue(hole.through)
        self.assertEqual(hole.source, "convention")
        self.assertAlmostEqual(hole.drawn_depth, 5.0)
        self.assertIn("callout: missing", hole.flags)

    def test_pareti_nascoste_da_faccia_a_faccia_passante(self):
        holes = _read([*FRONT, SIDE, *_walls(150, 155, 25, 3)], hidden=2)
        hole, = holes.holes
        self.assertEqual(hole.source, "trace")
        self.assertTrue(hole.through)
        self.assertEqual(len(hole.traces), 1)

    def test_pareti_col_fondo_foro_cieco(self):
        # laterale spessa 20, pareti lunghe 8 dalla faccia sinistra, chiuse dal fondo
        bottom = {"type": "line", "start": (158, 22), "end": (158, 28)}
        holes = _read([*FRONT, _rect(150, 0, 20, 50), *_walls(150, 158, 25, 3), bottom], hidden=3)
        hole, = holes.holes
        self.assertFalse(hole.through)
        self.assertAlmostEqual(hole.drawn_depth, 8.0)

    def test_pareti_senza_fondo_non_sono_una_traccia(self):
        # due linee alla quota del foro che si fermano a metà: niente fondo → convenzione
        holes = _read([*FRONT, _rect(150, 0, 20, 50), *_walls(150, 158, 25, 3)], hidden=2)
        hole, = holes.holes
        self.assertTrue(hole.through)
        self.assertEqual(hole.source, "convention")

    def test_ala_con_smusso_passante_spessore_ala(self):
        # lamiera piegata: laterale 20x50, il foro passa un'ala spessa 1 fra x=150 e x=151;
        # a x=151 la faccia prosegue in obliquo (smusso), non è un fondo
        chamfer = [{"type": "line", "start": (151, 22), "end": (156, 17)},
                   {"type": "line", "start": (151, 28), "end": (156, 33)}]
        holes = _read([*FRONT, _rect(150, 0, 20, 50), *chamfer, *_walls(150, 151, 25, 3)], hidden=2)
        hole, = holes.holes
        self.assertTrue(hole.through)
        self.assertEqual(hole.source, "trace")
        self.assertAlmostEqual(hole.drawn_depth, 1.0)

    def test_cerchi_concentrici_segnalati(self):
        holes = _read([*FRONT, {"type": "circle", "center": (30, 25), "radius": 5}, SIDE])
        self.assertEqual(len(holes.holes), 2)
        self.assertTrue(all(any(f.startswith("concentric:") for f in h.flags) for h in holes.holes))

    def test_quota_agganciata_e_scala(self):
        # geometria a 1,25:1: Ø6 disegnato, Ø4,8 scritto → profondità 5 disegnata = 4
        holes = _read([*FRONT, SIDE], dimensions=[_diameter("Ø4,8+0,05^-0", (30, 25), 3)])
        hole, = holes.holes
        self.assertEqual((hole.callout.designation, hole.callout.nominal), ("Ø", 4.8))
        self.assertEqual((hole.callout.upper, hole.callout.lower), (0.05, 0.0))
        self.assertAlmostEqual(holes.scale, 0.8)
        self.assertAlmostEqual(hole.depth, 4.0)
        self.assertEqual(framer.describe_holes(holes), "1 foro passante Ø4,8 +0,05/0, profondità 4")

    def test_senza_vista_principale_niente_fori(self):
        holes = _read([_rect(0, 0, 10, 10), _rect(300, 300, 7, 13)])
        self.assertEqual(holes.holes, [])


@unittest.skipUnless((EXAMPLES / "leva_01.dxf").exists(), "disegno reale non presente")
class TestLevaInox(unittest.TestCase):

    def test_due_da_5_3_e_uno_da_4_3_passanti_profondita_4(self):
        doc = forge.load_dxf(str(EXAMPLES / "leva_01.dxf"), role_rules=framer.load_rules("generic"))
        framer.tag_layout(doc, framer.detect_frame(doc))
        result = forge.island(doc)
        holes = framer.read_holes(doc, result, framer.read_views(result))
        self.assertAlmostEqual(holes.scale, 0.8)
        self.assertTrue(all(h.through and h.source == "convention" for h in holes.holes))
        self.assertEqual(framer.describe_holes(holes),
                         "2 fori passanti Ø5,3 +0,05/0, profondità 4; 1 foro passante Ø4,3 +0,05/0, profondità 4")


if __name__ == "__main__":
    unittest.main()
