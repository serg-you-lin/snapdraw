"""
tests/test_frame.py
-------------------
Test del rilevamento cornice e dell'aggancio a forge.

Le fixture qui sono sintetiche, costruite con `forge.load_geometry`: un
rettangolo con rapporto ISO √2 che racchiude due "pezzi". Le fixture su DXF
reali (un A3/A4 con cornice e cartiglio veri) vanno in `tests/examples/` — vedi
TODO.md.
"""

import unittest

import forge
import snapdraw as sd
from snapdraw.frame import find_frame


def _rect(x0, y0, x1, y1, role="unknown"):
    return {
        "type": "polyline", "closed": True, "role": role,
        "points": [(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
    }


def _framed_doc(frame_role="unknown"):
    # cornice con rapporto A3 (420 x 297, ratio ≈ 1.414) + due pezzi dentro
    return forge.load_geometry([
        _rect(0, 0, 420, 297, role=frame_role),
        _rect(30, 30, 130, 130, role="outer"),
        _rect(200, 30, 300, 130, role="outer"),
    ])


def _unframed_doc():
    # due pezzi, nessun riquadro che li racchiude
    return forge.load_geometry([
        _rect(30, 30, 130, 130, role="outer"),
        _rect(200, 30, 300, 130, role="outer"),
    ])


class TestFindFrame(unittest.TestCase):

    def test_trova_la_cornice_iso_che_racchiude_i_pezzi(self):
        frame = find_frame(_framed_doc())
        self.assertIsNotNone(frame)
        self.assertEqual(frame.iso_format, "A3")
        self.assertGreaterEqual(frame.containment, 0.80)
        self.assertEqual(len(frame.edges), 4)

    def test_nessuna_cornice_su_un_disegno_senza_riquadro(self):
        self.assertIsNone(find_frame(_unframed_doc()))

    def test_conservativo_ratio_non_iso(self):
        # riquadro quadrato che racchiude tutto: rapporto 1.0, non ISO
        doc = forge.load_geometry([
            _rect(0, 0, 400, 400),
            _rect(30, 30, 130, 130, role="outer"),
        ])
        self.assertIsNone(find_frame(doc))


class TestDetectFrameRecipe(unittest.TestCase):

    def test_flag_frame_uncertain_quando_non_trova(self):
        layout = sd.detect_frame(_unframed_doc())
        self.assertIsNone(layout.frame)
        self.assertIn("frame: uncertain", layout.flags)

    def test_title_block_uncertain_su_disegno_senza_cartiglio(self):
        # _framed_doc() ha una cornice ma nessun cartiglio (niente griglia
        # interna, nessuna annotazione) — vedi tests/test_titleblock.py per
        # il rilevamento vero e proprio.
        layout = sd.detect_frame(_framed_doc())
        self.assertIsNone(layout.title_block)
        self.assertIn("title_block: uncertain", layout.flags)


    def test_riquadro_non_iso_attorno_al_cartiglio_viene_segnalato(self):
        # un modello aziendale non ISO (rapporto 2) che racchiude cartiglio e
        # pezzo: non è una cornice, ma resta nel disegno e va detto (B1250136)
        doc = forge.load_geometry([
            _rect(0, 0, 300, 600),
            _rect(60, 250, 200, 400, role="outer"),
        ])
        sd.add_title_block(doc, anchor=(290.0, 10.0))
        for e in doc.edges:  # il cartiglio va trovato, non preso come già deciso
            e.role = "unknown" if e.role == sd.TITLE_BLOCK else e.role
        layout = sd.detect_frame(doc)
        self.assertIsNone(layout.frame)
        self.assertIsNotNone(layout.title_block)
        self.assertTrue(any("rejected border" in f for f in layout.flags))

    def test_nessun_avviso_senza_cartiglio(self):
        # il rettangolo di un pezzo nudo non è un riquadro di impaginazione
        layout = sd.detect_frame(forge.load_geometry([_rect(0, 0, 300, 600)]))
        self.assertFalse(any("rejected border" in f for f in layout.flags))


class TestTagLayoutIntegration(unittest.TestCase):
    """L'aggancio: marca gli Edge, heal esclude la cornice dai cluster."""

    def test_senza_snapdraw_la_cornice_e_un_cluster(self):
        result = forge.heal(_framed_doc())
        # la cornice fa da outer e si mangia tutto: un solo cluster
        self.assertEqual(len(result.clusters), 1)

    def test_con_snapdraw_emergono_i_due_pezzi(self):
        doc = _framed_doc()
        layout = sd.detect_frame(doc)
        n = sd.tag_layout(doc, layout)
        self.assertEqual(n, 4)

        result = forge.heal(doc)
        self.assertEqual(len(result.clusters), 2)
        # la geometria della cornice non si perde: è in trash col ruolo intatto
        # (role è lo slug di consumatore "frame", non un ContourRole — D31/D47)
        self.assertTrue(
            any(getattr(t, "role", "") == "frame" for t in result.trash_entities)
        )


if __name__ == "__main__":
    unittest.main()
