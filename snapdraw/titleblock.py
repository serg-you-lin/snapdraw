"""
snapdraw/titleblock.py
----------------------
Rilevamento del cartiglio e lettura delle sue celle.

`find_titleblock`: il segnale forte è la griglia interna
(`geometry.grid_dividers`) — un rettangolo senza divisori interni non è mai un
cartiglio, qualunque altro segnale abbia. Densità di annotazioni e posizione
rispetto alla cornice sono bonus, non requisiti (DESIGN.md: "nessuno
sufficiente da solo", ma la griglia resta filtro, gli altri sono solo punteggio).

`extend_titleblock`: il rettangolo scelto da `find_titleblock` è di rado
tutto il cartiglio — tabella revisioni sopra, blocchi di celle a fianco più
alti o più bassi. Il cartiglio si estende alle linee dritte collegate a lui
(MAP D15).

`read_titleblock`: vocabolario ISO piccolo, per regex, contro il testo di ogni
cella — non posizionale. Deciso con Federico: niente nomenclatura di cliente
(resta ai `profiles/` privati, DESIGN.md "Cosa NON ci va"), solo termini
generici IT/EN da cartiglio ISO 7200.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from shapely.geometry import LineString
from shapely.strtree import STRtree

import forge
from forge.core.geometry.axis import CoveredRectangle, axis_lines, items_inside

from .geometry import TEXT_BORDER_TOL, annotation_density_ratio, find_rectangles, grid_dividers, line_edges
from .model import Cell, FrameInfo, TitleBlock

TITLEBLOCK_MIN_SIDE = 40.0             # mm — lato minimo assoluto plausibile (vedi geometry.find_rectangles)
CONFIDENCE_THRESHOLD = 0.6             # conservativo: sotto questa soglia, None
MAX_DOMINANT_SEGMENT_FRACTION = 0.6    # vedi _is_genuine_grid
MIN_FILLED_CELL_FRACTION = 0.8         # vedi find_titleblock: scarta griglie con troppe celle vuote
EXTEND_TOUCH_TOL = 1.0                 # mm — due linee si toccano se più vicine di così (vedi extend_titleblock)
FRAME_TOUCH_TOL = 1.0                  # mm — un lato del cartiglio sta sul bordo interno della cornice (MAP D31)


def find_titleblock(doc, frame: Optional[FrameInfo] = None) -> Optional[TitleBlock]:
    """
    Delimita il cartiglio nella geometria grezza di `doc`.

    Il cartiglio **non è per forza dentro una cornice**: il rilevamento parte
    da un rettangolo qualsiasi con una griglia interna. Con la cornice, il
    rettangolo deve avere almeno un lato sul suo bordo interno (MAP D31);
    l'angolo in basso a destra resta un bonus di punteggio.

    `find_rectangles` su un disegno con più linee parallele (le righe del
    cartiglio) restituisce anche ogni sotto-rettangolo nidificato (una riga
    sola, due righe, ...) e ogni combinazione che arriva a toccare geometria
    vicina (per esempio la cornice, se il cartiglio le sta appena dentro) —
    stesso principio della cornice a doppio bordo. Due filtri tengono buoni
    solo i candidati veri:

    - `_is_genuine_grid`: scarta un secondo bordo inset scambiato per griglia
      (il segmento centrale fra i due bordi non è una cella, è il resto del
      riquadro);
    - `MIN_FILLED_CELL_FRACTION`: scarta una griglia "gonfiata" con righe
      vuote annesse da geometria vicina — un cartiglio vero ha (quasi) tutte
      le celle con del testo dentro, anche solo un placeholder.

    Fra i candidati che passano entrambi e hanno punteggio sopra
    `CONFIDENCE_THRESHOLD`, tiene il **più grande** (stesso criterio di
    `frame.find_frame`): è quello che racchiude l'intero cartiglio, non una
    sua riga.
    """
    kept: List[Tuple[CoveredRectangle, List[Cell], float]] = []
    border = None if frame is None else (frame.inner_bbox or frame.bbox)

    for rect in find_rectangles(doc, min_side_length=TITLEBLOCK_MIN_SIDE):
        # con la cornice, il cartiglio sta sul suo bordo interno (MAP D31)
        if border is not None and not forge.geometry.sides_on_border(rect.bbox, border, FRAME_TOUCH_TOL):
            continue
        row_ys, col_xs = grid_dividers(rect, doc)
        if not _is_genuine_grid(row_ys, col_xs, rect):
            continue

        cells = _build_cells(rect, row_ys, col_xs, doc)
        filled = sum(1 for c in cells if c.text)
        if not cells or filled / len(cells) < MIN_FILLED_CELL_FRACTION:
            continue

        density = annotation_density_ratio(rect, doc)
        score = _confidence(row_ys, col_xs, density, rect, frame)
        if score >= CONFIDENCE_THRESHOLD:
            kept.append((rect, cells, score))

    if not kept:
        return None

    rect, cells, score = max(kept, key=lambda k: k[0].area)
    return TitleBlock(edges=_edges_inside(rect.bbox, doc), bbox=rect.bbox, cells=cells, confidence=score)


def extend_titleblock(title_block: TitleBlock, doc, frame: Optional[FrameInfo] = None) -> TitleBlock:
    """
    Estende `title_block` alle tabelle attaccate: ogni linea orizzontale o
    verticale di `doc` che tocca (entro `EXTEND_TOUCH_TOL`) il cartiglio o una
    linea già presa, a catena. Poi, come D12, si prende tutto quello che sta
    dentro l'area estesa (simboli, loghi).

    Perché: `find_titleblock` sceglie un rettangolo con i quattro lati coperti,
    e una tabella revisioni più stretta del cartiglio, o un blocco di celle a
    fianco più alto, ne resta fuori — la sua riga chiusa diventa un'isola per
    `forge.island()` (MAP D15, 16 disegni su 19 dei `complete_drawings`).

    Limite: una linea si prende solo se sta tutta dentro il riquadro del
    cartiglio allargato del suo lato maggiore. Senza, la catena risale i lati
    di un riquadro che condivide il bordo col cartiglio (un modello aziendale
    non ISO, scartato come cornice) e si mangia il foglio. Le linee di
    `frame` restano fuori: il cartiglio sta quasi sempre nell'angolo della
    cornice e la tocca.

    Ritorna un nuovo `TitleBlock`: `edges` estesi, `bbox` l'area estesa,
    `cells` e `confidence` quelli del rettangolo di partenza (la griglia letta
    da `read_titleblock` non cambia). Non muta `doc`.
    """
    xmin, ymin, xmax, ymax = title_block.bbox
    reach = max(xmax - xmin, ymax - ymin)
    env = (xmin - reach, ymin - reach, xmax + reach, ymax + reach)

    taken = {id(e) for e in title_block.edges}
    if frame is not None:
        taken |= {id(e) for e in frame.edges}

    def in_env(e) -> bool:
        return all(env[0] <= p[0] <= env[2] and env[1] <= p[1] <= env[3] for p in (e.start, e.end))

    horiz, vert = axis_lines([e for e in line_edges(doc) if e.role == "unknown"])
    candidates = [t.item for t in horiz + vert if id(t.item) not in taken and in_env(t.item)]
    if not candidates:
        return title_block
    geoms = [LineString([e.start, e.end]) for e in candidates]
    tree = STRtree(geoms)

    frontier = [LineString([e.start, e.end]) for e in title_block.edges if e.start != e.end]
    added: list = []
    while frontier:
        g = frontier.pop()
        for j in tree.query(g, predicate="dwithin", distance=EXTEND_TOUCH_TOL):
            e = candidates[j]
            if id(e) in taken:
                continue
            taken.add(id(e))
            added.append(e)
            frontier.append(geoms[j])

    if not added:
        return title_block

    pts = [p for e in added for p in (e.start, e.end)]
    bbox = (min(xmin, *(p[0] for p in pts)), min(ymin, *(p[1] for p in pts)),
            max(xmax, *(p[0] for p in pts)), max(ymax, *(p[1] for p in pts)))
    frame_ids = {id(e) for e in frame.edges} if frame is not None else set()
    edges = [e for e in _edges_inside(bbox, doc) if id(e) not in frame_ids]
    return TitleBlock(edges=edges, bbox=bbox, cells=title_block.cells, confidence=title_block.confidence)


_CONTAINMENT_TOL = 0.5  # mm — tolleranza sul bordo: un divisore/simbolo a filo non deve perdersi per un arrotondamento


def _edges_inside(bbox: Tuple[float, float, float, float], doc) -> list:
    """
    Tutti gli Edge di `doc.edges` (qualunque tipo di segmento — griglia,
    simboli, loghi, non solo il bordo trovato da `find_rectangles`) i cui
    endpoint stanno dentro `bbox`.

    Chiamato solo sul cartiglio già scelto: tutto ciò che ci sta
    geometricamente dentro è cartiglio, non un pezzo a sé — deve andare sul
    layer `title_block` con lui, non finire in `trash_entities` (o peggio,
    in un cluster spurio) solo perché nessuno l'ha marcato.
    """
    return items_inside(bbox, doc.edges, _CONTAINMENT_TOL)


def _is_genuine_grid(row_ys: List[float], col_xs: List[float], rect: CoveredRectangle) -> bool:
    """
    True se almeno un asse è suddiviso in segmenti **comparabili**, non
    dominati da uno solo. Distingue una vera griglia di celle da un secondo
    bordo inset (cornice a doppia squadratura, MAP D9): quello produce
    anch'esso 2 "divisori" per lato, ma il segmento centrale fra i due è
    quasi tutto il lato — non una cella, il resto del riquadro.
    """
    xmin, ymin, xmax, ymax = rect.bbox

    def dominant_ok(dividers: List[float], lo: float, hi: float) -> bool:
        if not dividers or hi <= lo:
            return False
        bounds = sorted([lo] + dividers + [hi])
        longest = max(b - a for a, b in zip(bounds, bounds[1:]))
        return longest <= MAX_DOMINANT_SEGMENT_FRACTION * (hi - lo)

    return dominant_ok(row_ys, ymin, ymax) or dominant_ok(col_xs, xmin, xmax)


def _confidence(row_ys: List[float], col_xs: List[float], density: float, rect: CoveredRectangle, frame: Optional[FrameInfo]) -> float:
    """
    Confidenza grezza, stesso spirito additivo di `frame._confidence` — da
    tarare sulle fixture reali (TODO.md), non ancora disponibili.
    """
    score = 0.3  # ha una griglia interna genuina: già un segnale forte, base
    score += min(0.2, 0.04 * (len(row_ys) + len(col_xs)))  # più celle, più tipico
    score += min(0.3, 0.1 * density)  # più denso di testo della media, più tipico

    if frame is not None:
        fxmin, fymin, fxmax, fymax = frame.bbox
        rxmin, rymin, rxmax, rymax = rect.bbox
        if fxmin - 1e-6 <= rxmin and rxmax <= fxmax + 1e-6 and fymin - 1e-6 <= rymin and rymax <= fymax + 1e-6:
            score += 0.1
            if (rxmax - fxmax) ** 2 + (rymin - fymin) ** 2 <= ((fxmax - fxmin) * 0.25) ** 2:
                score += 0.1  # vicino all'angolo in basso a destra della cornice

    return max(0.0, min(1.0, score))


def _build_cells(rect: CoveredRectangle, row_ys: List[float], col_xs: List[float], doc) -> List[Cell]:
    """
    I divisori tagliano `rect` in celle; ogni cella raccoglie il testo delle
    annotazioni che contiene, dall'alto in basso. Con `TEXT_BORDER_TOL` sul
    bordo: un MTEXT agganciato a sinistra ha il punto d'inserimento
    esattamente sul bordo della cella, e un arrotondamento lo buttava fuori
    (`sviluppo_01`, cartiglio perso — MAP D15). Un testo sul
    divisore fra due celle finisce in entrambe: meglio un doppione che un
    campo perso.
    """
    tol = TEXT_BORDER_TOL
    xmin, ymin, xmax, ymax = rect.bbox
    xs = sorted([xmin] + col_xs + [xmax])
    ys = sorted([ymin] + row_ys + [ymax])

    cells = []
    for i in range(len(ys) - 1):
        y_lo, y_hi = ys[i], ys[i + 1]
        for j in range(len(xs) - 1):
            x_lo, x_hi = xs[j], xs[j + 1]
            inside = sorted(
                (a for a in doc.annotations
                 if x_lo - tol <= a.position[0] <= x_hi + tol
                 and y_lo - tol <= a.position[1] <= y_hi + tol and a.display_text),
                key=lambda a: -a.position[1],
            )
            text = " ".join(a.display_text for a in inside)
            cells.append(Cell(bbox=(x_lo, y_lo, x_hi, y_hi), text=text))
    return cells


# ---------------------------------------------------------------------------
# Lettura campi — vocabolario ISO generico, per regex (non nomenclatura cliente)
# ---------------------------------------------------------------------------

_FIELD_PATTERNS: Dict[str, str] = {
    "drawing_number": r"N\.?\s*DISEGNO|DISEGNO\s*N[O°.]?|DWG\.?\s*N[O°]?|DRAWING\s*N[O°]?",
    "revision":       r"REV(?:ISIONE)?\.?",
    "scale":          r"SCALA|SCALE",
    "material":       r"MATERIALE?|MATERIAL",
    "thickness":      r"SPESSORE|SP\.?|THICKNESS",
    "quantity":       r"QUANTIT[AÀ]|Q\.?T[AÀ]|QTY",
    "position":       r"POSIZIONE|POS\.?",
    "title":          r"TITOLO|TITLE|DESCRIZIONE|DESCRIPTION|DENOMINAZIONE",
    # aggiunti dopo il primo giro su un disegno reale (MAP D11 appunti) — non
    # servono a Pippo (che ricava lo spessore dallo sviluppo, non dal
    # cartiglio), ma senza un'etichetta nota nel vocabolario il loro testo
    # finisce impastato nel valore del campo precedente (`_split_labeled_text`)
    "drawn_by":       r"DISEGN(?:ATO)?\.?",
    "checked_by":     r"CONTR(?:OLLATO)?\.?",
    "date":           r"DATA|DATE",
    "sheet":          r"FOGLIO|SHEET",
}

# Un solo pattern con un gruppo nominato per campo — permette di trovare PIÙ
# etichette nello stesso testo di cella in un colpo solo (vedi _split_labeled_text).
_LABEL_REGEX = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in _FIELD_PATTERNS.items()),
    re.IGNORECASE,
)


def read_titleblock(layout) -> dict:
    """
    Legge le celle del cartiglio → dict dei campi
    (`{material: {"value", "source", "confidence"}, ...}`) più `"unresolved"`
    (i nomi di `_FIELD_PATTERNS` non trovati in nessuna cella).

    Cerca nel testo di ogni cella OGNI etichetta del vocabolario (ISO 7200
    generico, non nomenclatura di cliente — quella resta ai `profiles/`
    privati), non solo la prima: un cartiglio reale spesso ha divisori di
    colonna troppo corti per essere una griglia genuina a sé (coprono una
    riga, non l'intero cartiglio — `geometry.grid_dividers` li scarta), quindi
    una cella può raccogliere più campi insieme, non uno solo. Il valore di
    ogni etichetta trovata è il testo fra la fine di quell'etichetta e
    l'inizio della prossima etichetta (di qualunque campo) o la fine della
    cella. Nessun match → `None` + il nome in `unresolved`, mai una
    supposizione.

    `layout`: una `FrameLayout` (l'output di `sd.detect_frame`), o un
    `TitleBlock` direttamente.
    """
    title_block = layout.title_block if hasattr(layout, "title_block") else layout

    if title_block is None:
        return {"unresolved": list(_FIELD_PATTERNS)}

    result: dict = {}
    for i, cell in enumerate(title_block.cells):
        for name, found in _split_labeled_text(cell.text, i).items():
            result.setdefault(name, found)  # la prima cella che lo trova vince

    result["unresolved"] = [name for name in _FIELD_PATTERNS if name not in result]
    return result


def _split_labeled_text(text: str, cell_index: int) -> Dict[str, dict]:
    """Ogni etichetta trovata in `text` → valore = il testo fino alla prossima etichetta (o fine stringa)."""
    matches = list(_LABEL_REGEX.finditer(text))
    result = {}
    for i, m in enumerate(matches):
        end_value = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        value = text[m.end():end_value].strip(" :\t-")
        result[m.lastgroup] = {
            "value": value or None,
            "source": f"title_block:cell[{cell_index}]",
            "confidence": 0.9 if m.start() == 0 else 0.6,
        }
    return result
