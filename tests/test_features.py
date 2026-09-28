"""
tests/test_features.py
----------------------
Test della lettura delle feature sulle viste: fori, asole, aperture su ogni
vista ortogonale; traccia nelle viste compagne (passante, cieco, ala di
lamiera); sede concentrica (lamatura, svasatura); quota di diametro; scala
per vista; le facce di una vista non sono aperture; `tag_features`. Fogli
costruiti con `forge.load_geometry` e letti con `forge.island`; il caso vero
è `regr_05` (leva_01, tests/examples/regression).
"""

import unittest
from pathlib import Path

import forge
import snapdraw as sd
from forge.model.style import EdgeStyle

REGRESSION = Path(__file__).parent / "examples" / "regression"
HIDDEN = EdgeStyle(linetype="HIDDEN", linetype_pattern=(1.0, 0.5, -0.25))


def _rect(x, y, w, h):
    return {"type": "polyline", "closed": True,
            "points": [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]}


def _walls(x0, x1, y, r):
    """Le due pareti nascoste di una feature alta 2r alla quota y, da x0 a x1."""
    return [{"type": "line", "start": (x0, y - r), "end": (x1, y - r)},
            {"type": "line", "start": (x0, y + r), "end": (x1, y + r)}]


def _stadium(cx, cy, length, width):
    """Un'asola orizzontale: due semicerchi e due lati."""
    r = width / 2
    a, b = cx - length / 2 + r, cx + length / 2 - r
    return [{"type": "line", "start": (a, cy - r), "end": (b, cy - r)},
            {"type": "arc", "center": (b, cy), "radius": r, "start_angle": -90, "end_angle": 90},
            {"type": "line", "start": (b, cy + r), "end": (a, cy + r)},
            {"type": "arc", "center": (a, cy), "radius": r, "start_angle": 90, "end_angle": 270}]


def _load(entities, hidden=0, dimensions=()):
    doc = forge.load_geometry(entities)
    if hidden:
        for edge in doc.edges[-hidden:]:
            edge.style = HIDDEN
    doc.annotations.extend(dimensions)
    result = forge.island(doc)
    return doc, result, sd.read_views(result)


def _read(entities, hidden=0, dimensions=()):
    doc, result, views = _load(entities, hidden, dimensions)
    return sd.read_features(doc, result, views)


def _diameter(text, center, r):
    return forge.Dimension(position=(center[0] + 10, center[1] + 10), source_kind="DIMENSION",
                           dim_type="diameter", text_override=text, measured_value=2 * r,
                           measured_points=[(center[0] - r, center[1]), (center[0] + r, center[1])])


# frontale 100x50 con un foro r=3 in (30, 25), laterale 5x50 a destra
FRONT = [_rect(0, 0, 100, 50), {"type": "circle", "center": (30, 25), "radius": 3}]
SIDE = _rect(150, 0, 5, 50)


class TestHoles(unittest.TestCase):

    def test_senza_indicazioni_passante_per_convenzione(self):
        hole, = _read([*FRONT, SIDE]).features
        self.assertEqual((hole.kind, hole.hole_type, hole.role), ("hole", "plain", sd.HOLE))
        self.assertTrue(hole.through)
        self.assertEqual(hole.source, "convention")
        self.assertAlmostEqual(hole.drawn_depth, 5.0)
        self.assertIn("callout: missing", hole.flags)

    def test_pareti_nascoste_da_faccia_a_faccia_passante(self):
        hole, = _read([*FRONT, SIDE, *_walls(150, 155, 25, 3)], hidden=2).features
        self.assertEqual(hole.source, "trace")
        self.assertTrue(hole.through)
        self.assertEqual(len(hole.traces), 1)

    def test_pareti_col_fondo_foro_cieco(self):
        # laterale spessa 20, pareti lunghe 8 dalla faccia sinistra, chiuse dal fondo
        bottom = {"type": "line", "start": (158, 22), "end": (158, 28)}
        hole, = _read([*FRONT, _rect(150, 0, 20, 50), *_walls(150, 158, 25, 3), bottom], hidden=3).features
        self.assertFalse(hole.through)
        self.assertAlmostEqual(hole.drawn_depth, 8.0)

    def test_pareti_senza_fondo_non_sono_una_traccia(self):
        # due linee alla quota del foro che si fermano a metà: niente fondo → convenzione
        hole, = _read([*FRONT, _rect(150, 0, 20, 50), *_walls(150, 158, 25, 3)], hidden=2).features
        self.assertTrue(hole.through)
        self.assertEqual(hole.source, "convention")

    def test_ala_con_smusso_passante_spessore_ala(self):
        # lamiera piegata: laterale 20x50, il foro passa un'ala spessa 1 fra x=150 e x=151;
        # a x=151 la faccia prosegue in obliquo (smusso), non è un fondo
        chamfer = [{"type": "line", "start": (151, 22), "end": (156, 17)},
                   {"type": "line", "start": (151, 28), "end": (156, 33)}]
        hole, = _read([*FRONT, _rect(150, 0, 20, 50), *chamfer, *_walls(150, 151, 25, 3)], hidden=2).features
        self.assertTrue(hole.through)
        self.assertEqual(hole.source, "trace")
        self.assertAlmostEqual(hole.drawn_depth, 1.0)

    def test_sede_cieca_concentrica_e_una_lamatura(self):
        # foro r=3 passante, sede r=6 profonda 2 dalla faccia sinistra della laterale 10x50
        seat = [{"type": "circle", "center": (30, 25), "radius": 6}]
        step = [{"type": "line", "start": (152, 19), "end": (152, 22)}, {"type": "line", "start": (152, 28), "end": (152, 31)}]
        entities = [*FRONT, *seat, _rect(150, 0, 10, 50), *step, *_walls(150, 152, 25, 6), *_walls(152, 160, 25, 3)]
        hole, = _read(entities, hidden=6).features
        self.assertEqual((hole.hole_type, hole.role), ("counterbore", sd.HOLE))
        self.assertAlmostEqual(hole.seat_depth, 2.0)
        self.assertTrue(hole.through)
        self.assertEqual(len(hole.contours), 2)

    def test_sede_senza_prova_resta_non_determinata(self):
        # due cerchi concentrici visti di faccia: lamatura e svasatura sono uguali, non si indovina
        hole, = _read([*FRONT, {"type": "circle", "center": (30, 25), "radius": 5}, SIDE]).features
        self.assertEqual((hole.hole_type, hole.role), ("seated", sd.HOLE))
        self.assertAlmostEqual(hole.outer_shape.diameter, 10.0)
        self.assertIn("seat: type not determined", hole.flags)

    def test_linee_oblique_dalla_sede_al_foro_una_svasatura(self):
        # laterale 10x50: il cono va da r=5 sulla faccia sinistra a r=3 due mm dentro
        cone = [{"type": "line", "start": (150, 20), "end": (152, 22)}, {"type": "line", "start": (150, 30), "end": (152, 28)}]
        entities = [*FRONT, {"type": "circle", "center": (30, 25), "radius": 5}, _rect(150, 0, 10, 50), *cone,
                    *_walls(152, 160, 25, 3)]
        hole, = _read(entities, hidden=4).features
        self.assertEqual((hole.hole_type, hole.role), ("countersink", sd.HOLE))

    def test_quota_m_e_un_filetto(self):
        hole, = _read([*FRONT, SIDE], dimensions=[_diameter("M<>", (30, 25), 3)]).features
        self.assertEqual((hole.hole_type, hole.role), ("threaded", sd.HOLE))

    def test_arco_di_cresta_a_270_gradi_e_un_filetto(self):
        # convenzione ISO: il preforo chiuso, la cresta come arco aperto di ~3/4 di giro
        crest = {"type": "arc", "center": (30, 25), "radius": 3.6, "start_angle": 0, "end_angle": 270}
        layout = _read([*FRONT, crest, SIDE])
        hole, = layout.features
        self.assertEqual((hole.hole_type, hole.role), ("threaded", sd.HOLE))
        self.assertAlmostEqual(hole.thread_diameter, 7.2)
        self.assertEqual(sd.describe_features(layout), "1 foro filettato passante M≈7,2, profondità 5 (disegnata)")

    def test_quota_sulla_cresta_si_aggancia_dal_centro(self):
        # la quota M6 misura la cresta (un arco aperto): forge non la aggancia, snapdraw sì dal centro
        crest = {"type": "arc", "center": (30, 25), "radius": 3.6, "start_angle": 0, "end_angle": 270}
        hole, = _read([*FRONT, crest, SIDE], dimensions=[_diameter("M6", (30, 25), 3.6)]).features
        self.assertEqual((hole.callout.designation, hole.callout.nominal), ("M", 6.0))
        self.assertIn("callout: anchored by center", hole.flags)

    def test_n_fori_vale_per_i_fori_uguali_della_vista(self):
        # tre fori uguali, una quota "Ø6 n°3 fori" sul primo: vale per tutti e tre
        holes = [{"type": "circle", "center": (x, 25), "radius": 3} for x in (20, 50, 80)]
        layout = _read([_rect(0, 0, 100, 50), *holes, SIDE], dimensions=[_diameter("Ø6 n°3 fori", (20, 25), 3)])
        self.assertEqual([f.callout.nominal if f.callout else None for f in layout.features], [6.0, 6.0, 6.0])
        self.assertEqual(layout.features[0].callout.count, 3)
        self.assertFalse(any("written" in flag for f in layout.features for flag in f.flags))
        self.assertEqual(sd.describe_features(layout), "3 fori passanti Ø6, profondità 5")


class TestOtherShapes(unittest.TestCase):

    def test_stadio_e_un_asola(self):
        slot, = _read([_rect(0, 0, 100, 50), *_stadium(50, 25, 20, 8), SIDE]).features
        self.assertEqual((slot.kind, slot.role), ("slot", sd.SLOT))
        self.assertAlmostEqual(slot.size[0], 20.0)
        self.assertAlmostEqual(slot.size[1], 8.0)
        self.assertTrue(slot.through)

    def test_rettangolo_isolato_e_un_apertura(self):
        opening, = _read([_rect(0, 0, 100, 50), _rect(40, 20, 30, 10), SIDE]).features
        self.assertEqual((opening.kind, opening.role), ("opening", sd.OPENING))

    def test_forma_libera_isolata_e_un_apertura(self):
        # una cava a L: né cerchio né stadio né rettangolo, ma un'apertura lo stesso
        cava = {"type": "polyline", "closed": True, "points": [(40, 20), (60, 20), (60, 26), (48, 26), (48, 32), (40, 32)]}
        opening, = _read([_rect(0, 0, 100, 50), cava, SIDE]).features
        self.assertEqual((opening.kind, opening.role, opening.shape.kind), ("opening", sd.OPENING, "polygon"))

    def test_cerchio_tangente_al_bordo_resta_un_foro(self):
        # la sede di un foro d'angolo tocca il lato del pezzo: è sempre un foro
        holes = [{"type": "circle", "center": (6, 6), "radius": 1.75}, {"type": "circle", "center": (6, 6), "radius": 6}]
        hole, = _read([_rect(0, 0, 100, 50), *holes, SIDE]).features
        self.assertAlmostEqual(hole.outer_shape.diameter, 12.0)

    def test_le_facce_di_una_vista_non_sono_aperture(self):
        # una linea che attraversa la frontale la divide in due facce: nessuna apertura
        line = {"type": "line", "start": (60, 0), "end": (60, 50)}
        features = _read([_rect(0, 0, 100, 50), line, SIDE]).features
        self.assertEqual([f for f in features if f.kind == "opening"], [])

    def test_feature_su_ogni_vista_non_solo_la_principale(self):
        # frontale 100x50, pianta 100x20 sotto con un foro: il foro è nella pianta
        plan = [_rect(0, -40, 100, 20), {"type": "circle", "center": (50, -30), "radius": 4}]
        features = _read([_rect(0, 0, 100, 50), *plan, SIDE]).features
        self.assertEqual(len(features), 1)
        self.assertNotEqual(features[0].view, 0)


class TestScaleAndTag(unittest.TestCase):

    def test_scala_per_vista_dalle_quote(self):
        # geometria a 1,25:1: Ø6 disegnato, Ø4,8 scritto → scala 0,8, profondità 5 disegnata = 4
        layout = _read([*FRONT, SIDE], dimensions=[_diameter("Ø4,8+0,05^-0", (30, 25), 3)])
        hole, = layout.features
        self.assertAlmostEqual(hole.scale, 0.8)
        self.assertAlmostEqual(hole.depth, 4.0)
        self.assertEqual((hole.callout.upper, hole.callout.lower), (0.05, 0.0))
        self.assertEqual(sd.describe_features(layout), "1 foro passante Ø4,8 +0,05/0, profondità 4")

    def test_senza_quote_misura_disegnata_col_simbolo_circa(self):
        layout = _read([*FRONT, SIDE])
        self.assertEqual(sd.describe_features(layout), "1 foro passante Ø≈6, profondità 5 (disegnata)")

    def test_tag_attacca_le_feature_e_toglie_i_contorni_dagli_inners(self):
        doc, result, views = _load([*FRONT, SIDE])
        layout = sd.read_features(doc, result, views)
        front = result.clusters[layout.features[0].view]
        self.assertEqual(len(front.inners), 1)
        sd.tag_features(result, layout)
        self.assertEqual(front.features("view_features"), layout.features)
        self.assertEqual(front.inners, [])

    def test_json_di_forge_porta_le_feature(self):
        # il gancio di forge: to_json(result, extra_metadata=sd.feature_metadata), dopo tag_features
        import json
        doc, result, views = _load([*FRONT, SIDE], dimensions=[_diameter("Ø6", (30, 25), 3)])
        layout = sd.read_features(doc, result, views)
        sd.tag_features(result, layout)
        parts = json.loads(forge.to_json(result, extra_metadata=sd.feature_metadata))
        text = json.dumps(parts)
        self.assertIn('"view_features"', text)
        self.assertIn('"hole_type": "plain"', text)
        self.assertIn('"nominal": 6.0', text)

    def test_senza_viste_ortogonali_niente_feature(self):
        layout = _read([{"type": "line", "start": (0, 0), "end": (10, 6)}, {"type": "line", "start": (10, 6), "end": (0, 12)},
                        {"type": "line", "start": (0, 12), "end": (0, 0)}])
        self.assertEqual(layout.features, [])


@unittest.skipUnless((REGRESSION / "regr_05.dxf").exists(), "fixture non presente")
class TestLevaInox(unittest.TestCase):

    def test_due_da_5_3_e_uno_da_4_3_passanti_profondita_4(self):
        doc = forge.load_dxf(str(REGRESSION / "regr_05.dxf"), role_rules=sd.load_rules("generic"))
        sd.tag_layout(doc, sd.detect_frame(doc))
        result = forge.island(doc)
        layout = sd.read_features(doc, result, sd.read_views(result))
        self.assertTrue(all(abs(s - 0.8) < 1e-6 for s in layout.scales.values() if s))
        self.assertEqual(sd.describe_features(layout),
                         "2 fori passanti Ø5,3 +0,05/0, profondità 4; 1 foro passante Ø4,3 +0,05/0, profondità 4")


if __name__ == "__main__":
    unittest.main()
