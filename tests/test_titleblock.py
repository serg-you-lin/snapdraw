"""
tests/test_titleblock.py
-------------------------
Test del rilevamento cartiglio e della lettura dei campi.

Bootstrap "round-trip": prima di avere fixture DXF reali con un cartiglio
vero (TODO.md), il modo più veloce per testare `find_titleblock` è
rilevare un cartiglio generato da `sd.generate.add_title_block` — le
`forge.Note` di etichetta/valore che scrive sono lo stesso tipo di
annotazione che un cartiglio vero avrebbe.
"""

import unittest

import forge
import snapdraw as sd
from snapdraw.model import Cell, TitleBlock
from snapdraw.titleblock import _FIELD_PATTERNS, extend_titleblock, find_titleblock, read_titleblock


def _part_doc(w=200.0, h=100.0):
    return forge.load_geometry([{
        "type": "polygon", "role": "outer",
        "points": [(0, 0), (w, 0), (w, h), (0, h)],
    }])


class TestDetectTitleblockRoundTrip(unittest.TestCase):
    """Genera un cartiglio con generate.py, verifica che find_titleblock lo trovi."""

    def test_trova_il_cartiglio_generato_con_la_cornice(self):
        doc = _part_doc()
        frame = sd.add_frame(doc)
        sd.add_title_block(doc, fields={"material": "S235JR", "quantity": "2"})

        tb = find_titleblock(doc, frame=frame)
        self.assertIsNotNone(tb)
        self.assertGreaterEqual(tb.confidence, 0.6)
        self.assertGreaterEqual(len(tb.cells), 5)  # i 5 campi del template di default

    def test_trova_il_cartiglio_generato_senza_cornice(self):
        # il cartiglio non è per forza dentro una cornice (DESIGN.md) — deve
        # trovarlo anche senza passare `frame`.
        doc = _part_doc()
        sd.add_title_block(doc, anchor=(200.0, 0.0))

        tb = find_titleblock(doc, frame=None)
        self.assertIsNotNone(tb)

    def test_i_valori_scritti_si_ritrovano_nei_campi_letti(self):
        doc = _part_doc()
        frame = sd.add_frame(doc)
        sd.add_title_block(doc, fields={
            "material": "S235JR", "quantity": "3", "drawing_number": "tavola_08",
        })

        tb = find_titleblock(doc, frame=frame)
        fields = read_titleblock(tb)

        self.assertEqual(fields["material"]["value"], "S235JR")
        self.assertEqual(fields["quantity"]["value"], "3")
        self.assertEqual(fields["drawing_number"]["value"], "tavola_08")
        # non passati -> placeholder "-" -> nessun valore vero, non un dato inventato
        self.assertIsNone(fields["position"]["value"])


class TestDetectTitleblockConservativo(unittest.TestCase):

    def test_nessun_cartiglio_su_un_pezzo_nudo(self):
        # solo un rettangolo, nessuna griglia interna, nessuna annotazione
        self.assertIsNone(find_titleblock(_part_doc()))

    def test_un_rettangolo_senza_griglia_non_basta(self):
        doc = forge.load_geometry([
            {"type": "polygon", "role": "unknown",
             "points": [(0, 0), (90, 0), (90, 50), (0, 50)]},
        ])
        self.assertIsNone(find_titleblock(doc))

    def test_doppio_bordo_inset_non_e_una_griglia(self):
        # una cornice a doppia squadratura non deve passare come cartiglio
        # solo perché ha un "divisore" per lato (MAP D9 / _is_genuine_grid)
        doc = _part_doc()
        frame = sd.add_frame(doc)
        self.assertIsNone(find_titleblock(doc, frame=frame))


class TestTitleblockAssorbeInteriore(unittest.TestCase):
    """
    Il cartiglio deve "mangiarsi" tutto quello che gli sta geometricamente
    dentro (griglia, simboli, loghi), non solo il proprio bordo — altrimenti
    quella geometria non taggata finisce spersa in trash_entities invece che
    sul layer title_block (Federico, MAP D12).
    """

    def _symbol(self, x0, y0, x1, y1):
        return {
            "type": "polygon", "role": "unknown",
            "points": [(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
        }

    def test_un_simbolo_isolato_dentro_il_cartiglio_viene_marcato(self):
        doc = forge.load_geometry([{
            "type": "polygon", "role": "outer",
            "points": [(0, 0), (200, 0), (200, 100), (0, 100)],
        }])
        frame = sd.add_frame(doc)
        sd.add_title_block(doc)

        # un "simbolo" isolato (mai un pezzo vero) piazzato dentro il cartiglio,
        # non collegato a nient'altro — non lo scrive add_title_block, lo aggiungo
        # a mano come farebbe un simbolo di rugosità/saldatura sul disegno reale.
        n_before = len(doc.edges)
        symbol = forge.load_geometry([self._symbol(160, -40, 165, -35)])
        doc.edges.extend(symbol.edges)

        tb = find_titleblock(doc, frame=frame)
        self.assertIsNotNone(tb)
        # tutti e 4 gli edge del simbolo sono dentro tb.edges
        self.assertEqual(len(doc.edges), n_before + 4)
        tb_edge_ids = {id(e) for e in tb.edges}
        self.assertTrue(all(id(e) in tb_edge_ids for e in symbol.edges))

    def test_dopo_heal_il_simbolo_e_in_trash_col_ruolo_title_block(self):
        doc = forge.load_geometry([{
            "type": "polygon", "role": "outer",
            "points": [(0, 0), (200, 0), (200, 100), (0, 100)],
        }])
        sd.add_frame(doc)
        sd.add_title_block(doc)
        doc.edges.extend(forge.load_geometry([self._symbol(160, -40, 165, -35)]).edges)

        layout = sd.detect_frame(doc)
        sd.tag_layout(doc, layout)
        result = forge.heal(doc)

        # il simbolo non è un cluster a sé: è finito in trash col ruolo title_block
        from snapdraw.roles import TITLE_BLOCK
        symbol_in_trash = [
            t for t in result.trash_entities
            if getattr(t, "role", "") == TITLE_BLOCK
            and any(160 <= p[0] <= 165 for seg in t.segments for p in (seg.start, seg.end))
        ]
        self.assertTrue(symbol_in_trash, "il simbolo dentro il cartiglio non è finito in trash con role=title_block")
        self.assertEqual(len(result.clusters), 1)  # solo il pezzo — il simbolo non è un cluster a sé


class TestExtendTitleblock(unittest.TestCase):
    """
    Il cartiglio si prende le tabelle attaccate (MAP D15): una tabella
    revisioni più stretta sopra il cartiglio restava fuori dal rettangolo di
    `find_titleblock` e diventava un'isola per `forge.island()`.
    """

    def _rect(self, x0, y0, x1, y1):
        return {"type": "polygon", "role": "unknown",
                "points": [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]}

    def _doc_con_striscia(self):
        doc = _part_doc()
        sd.add_title_block(doc, anchor=(200.0, 0.0))
        tb = find_titleblock(doc)
        xmin, ymin, xmax, ymax = tb.bbox
        # striscia più stretta del cartiglio, appoggiata sul suo lato superiore
        strip = forge.load_geometry([self._rect(xmin + 5, ymax, xmax - 20, ymax + 8)])
        doc.edges.extend(strip.edges)
        return doc, tb, strip

    def test_la_striscia_attaccata_entra_nel_cartiglio(self):
        doc, tb, strip = self._doc_con_striscia()
        ext = extend_titleblock(tb, doc)
        ids = {id(e) for e in ext.edges}
        self.assertTrue(all(id(e) in ids for e in strip.edges))
        self.assertGreater(ext.bbox[3], tb.bbox[3])
        # la griglia letta resta quella del rettangolo di partenza
        self.assertEqual(ext.cells, tb.cells)

    def test_la_linea_lunga_del_riquadro_non_entra(self):
        # un lato di riquadro che parte dall'angolo del cartiglio e sale per
        # tutto il foglio: la catena non deve risalirlo (B1250136)
        doc = _part_doc()
        sd.add_title_block(doc, anchor=(200.0, 0.0))
        tb = find_titleblock(doc)
        xmin, ymin, xmax, ymax = tb.bbox
        side = forge.load_geometry([{"type": "line", "role": "unknown",
                                      "start": (xmin, ymin), "end": (xmin, ymin + 20 * (ymax - ymin))}])
        doc.edges.extend(side.edges)
        ext = extend_titleblock(tb, doc)
        self.assertNotIn(id(side.edges[0]), {id(e) for e in ext.edges})

    def test_senza_niente_attaccato_resta_uguale(self):
        doc = _part_doc()
        sd.add_title_block(doc, anchor=(200.0, 0.0))
        tb = find_titleblock(doc)
        self.assertIs(extend_titleblock(tb, doc), tb)


class TestTestoSulBordoCella(unittest.TestCase):

    def test_testo_agganciato_sul_bordo_sinistro_conta(self):
        # MTEXT agganciato a sinistra: il punto d'inserimento cade
        # esattamente sul bordo (sviluppo_01, cartiglio perso)
        grid = [{"type": "polygon", "role": "unknown",
                 "points": [(0, 0), (80, 0), (80, 45), (0, 45)]}]
        grid += [{"type": "line", "role": "unknown", "start": (0, y), "end": (80, y)} for y in (15, 30)]
        # il pezzo, lontano: senza, la densità di testo del riquadro è la media
        grid.append({"type": "polygon", "role": "outer",
                     "points": [(200, 0), (400, 0), (400, 200), (200, 200)]})
        doc = forge.load_geometry(grid)
        doc.annotations.extend(
            forge.Note(position=(0.0 - 1e-9, y), text=t, height=3.0)
            for y, t in ((5, "Materiale: S235JR"), (20, "Codice: sviluppo_01"), (35, "Scala 1:1"))
        )
        tb = find_titleblock(doc)
        self.assertIsNotNone(tb)
        self.assertTrue(all(c.text for c in tb.cells))


class TestReadTitleblock(unittest.TestCase):
    """Il vocabolario per regex, isolato da find_titleblock."""

    def test_riconosce_le_etichette_italiane_e_inglesi(self):
        tb = TitleBlock(edges=[], bbox=(0, 0, 90, 50), cells=[
            Cell(bbox=(0, 40, 90, 50), text="MATERIALE S235JR"),
            Cell(bbox=(0, 30, 90, 40), text="SCALE 1:2"),
            Cell(bbox=(0, 20, 90, 30), text="DWG NO 12345"),
        ])
        fields = read_titleblock(tb)
        self.assertEqual(fields["material"]["value"], "S235JR")
        self.assertEqual(fields["scale"]["value"], "1:2")
        self.assertEqual(fields["drawing_number"]["value"], "12345")

    def test_campo_non_trovato_e_unresolved_non_indovinato(self):
        tb = TitleBlock(edges=[], bbox=(0, 0, 90, 10), cells=[
            Cell(bbox=(0, 0, 90, 10), text="MATERIALE S235JR"),
        ])
        fields = read_titleblock(tb)
        self.assertNotIn("revision", fields)
        self.assertIn("revision", fields["unresolved"])

    def test_nessun_cartiglio_tutti_unresolved(self):
        fields = read_titleblock(sd.FrameLayout())
        self.assertEqual(set(fields["unresolved"]), set(_FIELD_PATTERNS))


if __name__ == "__main__":
    unittest.main()
