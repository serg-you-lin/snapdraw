"""
tests/test_render.py
--------------------
Test del ritaglio delle viste: quali edge entrano in una vista, un PNG per
vista con le proporzioni della vista. Fogli costruiti con
`forge.load_geometry` e letti con `sd.sheet_islands`.
"""

import os
import tempfile
import unittest

import forge
import snapdraw as sd


def _rect(x, y, w, h):
    return {"type": "polygon",
            "points": [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]}


def _png_size(path):
    with open(path, "rb") as f:
        header = f.read(24)
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


class TestRender(unittest.TestCase):

    def setUp(self):
        # frontale 100x50 con un foro, laterale 5x50; un asse che esce dalla frontale
        self.doc = forge.load_geometry([
            _rect(0, 0, 100, 50), {"type": "circle", "center": (30, 25), "radius": 3}, _rect(150, 0, 5, 50),
            {"type": "line", "start": (30, -10), "end": (30, 60)},
        ])
        self.views = sd.read_views(sd.sheet_islands(self.doc))

    def test_nella_vista_solo_gli_edge_che_ci_stanno_dentro(self):
        front = next(v for v in self.views.views if round(v.width) == 100)
        edges = sd.view_edges(self.doc, front.bbox)
        kinds = sorted(type(e.segment).__name__ for e in edges)
        # i 4 lati e il foro; l'asse esce dal riquadro e resta fuori
        self.assertEqual(kinds, ["CircleSeg", "LineSeg", "LineSeg", "LineSeg", "LineSeg"])

    def test_un_png_per_vista_con_le_proporzioni_della_vista(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = sd.render_views(self.doc, self.views, tmp, size=400)
            self.assertEqual(sorted(os.path.basename(p) for p in paths), ["view_0.png", "view_1.png"])
            sizes = {round(v.width): _png_size(os.path.join(tmp, f"view_{v.index}.png")) for v in self.views.views}
        w, h = sizes[100]
        self.assertEqual(max(w, h), 400)
        self.assertGreater(w, h)
        # la laterale 5x50 è sottile: si allarga col bianco fino a 1:4, non oltre
        w, h = sizes[5]
        self.assertEqual(h, 400)
        self.assertAlmostEqual(w / h, (0.25 * 50 + 2 * 0.05 * 50) / (50 + 2 * 0.05 * 50), places=1)


if __name__ == "__main__":
    unittest.main()
