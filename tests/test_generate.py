"""
tests/test_generate.py
-----------------------
Test del verso "aggiungi": `add_frame`/`add_title_block` generano cornice e
cartiglio attorno a geometria esistente, invece di riconoscerli.
"""

import unittest

import forge
import snapdraw as sd
from snapdraw.generate import DEFAULT_TITLE_BLOCK_TEMPLATE
from snapdraw.roles import FRAME, TITLE_BLOCK


def _part_doc(w, h):
    """Un pezzo rettangolare w x h, angolo in basso a sinistra nell'origine."""
    return forge.load_geometry([{
        "type": "polyline", "closed": True, "role": "outer",
        "points": [(0, 0), (w, 0), (w, h), (0, h)],
    }])


class TestAddFrame(unittest.TestCase):

    def test_alza_valueerror_su_doc_vuoto(self):
        doc = forge.load_geometry([])
        with self.assertRaises(ValueError):
            sd.add_frame(doc)

    def test_racchiude_il_pezzo_con_margine_per_i_quattro_formati(self):
        # A4 orizzontale, A4 verticale, A3 orizzontale, A3 verticale — non 4
        # rami di codice diversi, solo 4 pezzi di dimensione diversa: l'unico
        # meccanismo (bbox + formato ISO più piccolo che ci sta) deve
        # funzionare per tutti.
        for w, h in [(200.0, 100.0), (100.0, 200.0), (380.0, 250.0), (250.0, 380.0)]:
            with self.subTest(w=w, h=h):
                doc = _part_doc(w, h)
                frame = sd.add_frame(doc)
                fxmin, fymin, fxmax, fymax = frame.bbox
                self.assertLessEqual(fxmin, 0.0)
                self.assertLessEqual(fymin, 0.0)
                self.assertGreaterEqual(fxmax, w)
                self.assertGreaterEqual(fymax, h)
                self.assertIsNotNone(frame.iso_format)

    def test_formato_piu_grande_ha_piu_lineette_di_zona(self):
        # ISO 5457: la griglia di riferimento ha più zone (quindi più
        # lineette) su un lato più lungo — un A0 deve avere più edge di
        # cornice di un A5, non lo stesso numero.
        doc_piccolo = _part_doc(200.0, 100.0)
        frame_piccolo = sd.add_frame(doc_piccolo)

        doc_grande = _part_doc(1100.0, 750.0)
        frame_grande = sd.add_frame(doc_grande)

        self.assertGreater(len(frame_grande.edges), len(frame_piccolo.edges))

    def test_edge_generati_hanno_role_frame(self):
        doc = _part_doc(200.0, 100.0)
        n_before = len(doc.edges)
        frame = sd.add_frame(doc)
        self.assertTrue(all(e.role == FRAME for e in frame.edges))
        self.assertEqual(len(doc.edges), n_before + len(frame.edges))

    def test_heal_tiene_la_cornice_fuori_dal_cluster(self):
        doc = _part_doc(200.0, 100.0)
        sd.add_frame(doc)
        result = forge.heal(doc)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.clusters), 1)  # solo il pezzo, non la cornice
        self.assertTrue(any(getattr(t, "role", "") == FRAME for t in result.trash_entities))


class TestAddTitleBlock(unittest.TestCase):

    def test_alza_valueerror_su_doc_vuoto_senza_anchor(self):
        doc = forge.load_geometry([])
        with self.assertRaises(ValueError):
            sd.add_title_block(doc)

    def test_alza_valueerror_su_campo_sconosciuto(self):
        doc = _part_doc(200.0, 100.0)
        sd.add_frame(doc)
        with self.assertRaises(ValueError):
            sd.add_title_block(doc, fields={"non_esiste": "x"})

    def test_finisce_nell_angolo_basso_destra_della_cornice(self):
        doc = _part_doc(200.0, 100.0)
        frame = sd.add_frame(doc)
        tb = sd.add_title_block(doc)
        txmin, tymin, txmax, tymax = tb.bbox
        self.assertLessEqual(txmax, frame.bbox[2])   # entro il lato destro della cornice
        self.assertGreaterEqual(tymin, frame.bbox[1])  # entro il lato basso della cornice

    def test_edge_generati_hanno_role_title_block(self):
        doc = _part_doc(200.0, 100.0)
        sd.add_frame(doc)
        tb = sd.add_title_block(doc)
        self.assertTrue(all(e.role == TITLE_BLOCK for e in tb.edges))

    def test_heal_tiene_il_cartiglio_fuori_dal_cluster(self):
        doc = _part_doc(200.0, 100.0)
        sd.add_frame(doc)
        sd.add_title_block(doc)
        result = forge.heal(doc)
        self.assertEqual(len(result.clusters), 1)
        self.assertTrue(any(getattr(t, "role", "") == TITLE_BLOCK for t in result.trash_entities))

    def test_fields_personalizzati_sovrascrivono_la_cella(self):
        doc = _part_doc(200.0, 100.0)
        sd.add_frame(doc)
        tb = sd.add_title_block(doc, fields={"material": "S235JR", "quantity": "2"})
        by_name = {f.name: c.text for f, c in zip(DEFAULT_TITLE_BLOCK_TEMPLATE.fields, tb.cells)}
        self.assertEqual(by_name["material"], "MATERIALE: S235JR")
        self.assertEqual(by_name["quantity"], "Q.TÀ: 2")
        # un campo non passato resta col placeholder "-", non vuoto
        self.assertEqual(by_name["position"], "POS.: -")


if __name__ == "__main__":
    unittest.main()
