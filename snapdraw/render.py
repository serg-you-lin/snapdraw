"""
snapdraw/render.py
------------------
Il ritaglio delle viste: un PNG per vista, per far guardare un modello
(Pippo). snapdraw misura, non guarda (D18): qui non si interpreta niente, si
disegnano gli edge di una vista così come sono.

Cosa rende un'immagine utile a un modello, dall'esperimento di forge:
- una vista per immagine, ritagliata: sul foglio intero le viste si
  confondono;
- l'indice del cluster stampato sopra, così "la vista 2 è la frontale" si
  ricollega alla geometria;
- niente quote né testi: il modello leggerebbe i numeri invece della forma,
  e il numero lo dà già forge, più preciso.

Passi pubblici (`view_edges`, `render_view`) e una ricetta, `render_views`.

    views = sd.read_views(sd.sheet_islands(doc))
    sd.render_views(doc, views, "out/viste")   # out/viste/view_0.png, view_1.png, ...
"""

from __future__ import annotations

import os
from typing import List

from .model import BBox, ViewLayout
from .roles import CONSTRUCTION, FRAME, TITLE_BLOCK

IMAGE_SIZE = 800        # px — lato lungo dell'immagine
MARGIN = 0.05           # margine attorno alla vista, frazione del lato lungo
MIN_ASPECT = 0.25       # lato corto minimo / lato lungo: una vista sottile si allarga col bianco, non si deforma
LINE_WIDTH = 1.2        # px
EDGE_TOLERANCE = 0.5    # mm — un edge sta nella vista se esce dal riquadro al più di tanto

_NOT_DRAWN = {FRAME, TITLE_BLOCK, CONSTRUCTION}
_DASHES = {"uniform": (4, 3), "chain": (8, 3, 2, 3)}


def view_edges(doc, bbox: BBox, tolerance: float = EDGE_TOLERANCE) -> list:
    """
    Gli edge di `doc` interamente dentro `bbox`: contorni, linee nascoste,
    pieghe. Quello che esce dal riquadro (richiami di quota, assi) resta
    fuori; cornice, cartiglio e costruzione non si disegnano mai.
    """
    x0, y0, x1, y1 = bbox[0] - tolerance, bbox[1] - tolerance, bbox[2] + tolerance, bbox[3] + tolerance
    edges = []
    for edge in doc.edges:
        if edge.role in _NOT_DRAWN:
            continue
        points = edge.segment.discretize()
        if points and all(x0 <= x <= x1 and y0 <= y <= y1 for x, y in points):
            edges.append(edge)
    return edges


def render_view(edges: list, bbox: BBox, label: str, path: str, size: int = IMAGE_SIZE) -> None:
    """
    Disegna `edges` in un PNG ritagliato su `bbox`, nero su bianco, con
    `label` in alto a sinistra. Il tratteggio resta tratteggio (una linea
    nascosta si vede nascosta). Scala uguale sui due assi.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    long_side = max(width, height, 1e-9)
    pad = MARGIN * long_side
    half_w = max(width, MIN_ASPECT * long_side) / 2 + pad
    half_h = max(height, MIN_ASPECT * long_side) / 2 + pad
    cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    scale = size / (2 * max(half_w, half_h))
    dpi = 100
    fig = plt.figure(figsize=(2 * half_w * scale / dpi, 2 * half_h * scale / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(cx - half_w, cx + half_w)
    ax.set_ylim(cy - half_h, cy + half_h)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")
    for edge in edges:
        xs, ys = zip(*edge.segment.discretize())
        dashes = _DASHES.get(edge.style.dash_kind if edge.style else "continuous")
        line, = ax.plot(xs, ys, color="black", linewidth=LINE_WIDTH * 72 / dpi, solid_capstyle="round")
        if dashes:
            line.set_dashes(dashes)
    ax.text(0.01, 0.99, label, transform=ax.transAxes, ha="left", va="top",
            fontsize=14, color="#c00000", fontweight="bold")
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    fig.savefig(path, dpi=dpi, facecolor="white")
    plt.close(fig)


def render_views(doc, views: ViewLayout, folder: str, size: int = IMAGE_SIZE) -> List[str]:
    """
    Ricetta: un PNG per vista in `folder` (`view_<indice>.png`), ritagliato
    sul riquadro della vista, con l'indice del cluster stampato sopra.
    Tutte le viste, anche assonometrie e simboli: guardarle è il lavoro di
    chi riceve l'immagine. Restituisce i percorsi scritti.
    """
    paths = []
    for view in views.views:
        path = os.path.join(folder, f"view_{view.index}.png")
        render_view(view_edges(doc, view.bbox), view.bbox, str(view.index), path, size)
        paths.append(path)
    return paths
