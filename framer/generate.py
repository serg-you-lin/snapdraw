"""
framer/generate.py
-------------------
Il verso "aggiungi": genera cornice e cartiglio e li appende a un
`ForgeDocument` esistente — l'opposto di `detect_frame` + `tag_layout` (che li riconoscono su
geometria già disegnata). Annotato come
idea futura in `forge/FRAMER.md` ("Il verso 'aggiungi'") e in `TODO.md`; qui
diventa codice.

Cornice e cartiglio sono presi a riferimento da due file in `templates/`
(uno fatto a mano da Federico, uno scaricato — MAP D9): la cornice ha un
doppio bordo con una lineetta di demarcazione al centro di ogni lato (il
segno di centratura standard ISO 5457, non solo estetica); il cartiglio ha
etichetta piccola sopra, valore più grande sotto, non affiancati. Le celle
restano dati (`TitleBlockTemplate`/`FieldSlot`), non disegno hard-coded —
facile ritararle ancora se cambia il riferimento.

Puramente forge-nativo: la geometria passa da `forge.load_geometry` (stesso
meccanismo pubblico con cui `bendly` porta uno sviluppo generato a
`ForgeDocument`, forge MAP D32) e il testo da `forge.Note` — zero accesso a
`Edge`/`LineSeg` interni, zero ezdxf. Frame e griglia del cartiglio portano
`role` (`framer.roles.FRAME`/`TITLE_BLOCK`) fin dalla costruzione: non serve
chiamare `tag_layout` per questa geometria, e colore/layer arrivano gratis
dalla registrazione di `roles.py` (MAP D7).

Un solo template di cartiglio condiviso per tutti i formati/orientamenti:
A3/A4, orizzontale/verticale non cambiano la sua geometria, solo dove lo si
ancora sul foglio. `add_frame` sceglie da solo il formato ISO più piccolo che
contiene la geometria esistente più un margine più lo spazio per il
cartiglio — nessun formato da passare a mano.

Il logo/immagine (dati del chiamante, mai nel repo — stesso principio di
`data_injector`/`profiles/`) resta fuori da questo giro: forge non ha un
concetto di immagine nel suo modello neutro, andrebbe inserito in un secondo
giro direttamente sul `Drawing` ezdxf restituito da `to_dxf()`.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import forge

from .geometry import _ISO_FORMATS as _ISO_SHEET_SIZES
from .model import BBox, Cell, FieldSlot, FrameInfo, TitleBlock, TitleBlockTemplate
from .roles import FRAME, TITLE_BLOCK

_ROW_H = 10.0
_N_ROWS = 5
_TB_WIDTH = 90.0

DEFAULT_TITLE_BLOCK_TEMPLATE = TitleBlockTemplate(
    width=_TB_WIDTH,
    height=_ROW_H * _N_ROWS,
    fields=[
        # righe impilate dall'alto in basso, non celle affiancate — riga i
        # parte a height - i*_ROW_H e scende di _ROW_H, piena larghezza.
        FieldSlot(name="drawing_number", bbox=(0.0, 4 * _ROW_H, _TB_WIDTH, 5 * _ROW_H), label="N. DISEGNO"),
        FieldSlot(name="position",       bbox=(0.0, 3 * _ROW_H, _TB_WIDTH, 4 * _ROW_H), label="POS."),
        FieldSlot(name="material",       bbox=(0.0, 2 * _ROW_H, _TB_WIDTH, 3 * _ROW_H), label="MATERIALE"),
        FieldSlot(name="thickness",      bbox=(0.0, 1 * _ROW_H, _TB_WIDTH, 2 * _ROW_H), label="SP."),
        FieldSlot(name="quantity",       bbox=(0.0, 0 * _ROW_H, _TB_WIDTH, 1 * _ROW_H), label="Q.TÀ"),
    ],
)

DEFAULT_MARGIN = 10.0
_CELL_PADDING = 2.0
_LABEL_HEIGHT = 1.8
_VALUE_HEIGHT = 3.0
_BORDER_GAP = 5.0  # distanza fra bordo esterno e interno della cornice — ISO 5457
_ZONE_TARGET = 50.0  # lunghezza di zona indicativa della griglia di riferimento — ISO 5457


def add_frame(
    doc,
    margin: float = DEFAULT_MARGIN,
    title_block_template: Optional[TitleBlockTemplate] = None,
) -> FrameInfo:
    """
    Genera una cornice ISO attorno alla geometria corrente di `doc` e la
    appende (mutazione in place, stesso idioma di `tag_layout`). Sceglie da
    solo il formato/orientamento ISO (A4..A0) più piccolo che contiene la
    geometria esistente con `margin` su ogni lato più lo spazio per un
    cartiglio (`title_block_template`, default `DEFAULT_TITLE_BLOCK_TEMPLATE`
    — passa lo stesso template a `add_title_block` per coerenza) lungo il
    basso, senza sovrapporsi alla geometria. Doppio bordo (esterno + interno
    inset di `_BORDER_GAP`) con una lineetta di centratura al centro di ogni
    lato — vedi `_frame_entities`, MAP D9.

    `ValueError` se `doc.edges` è vuoto (niente attorno a cui costruire una
    cornice) o se nemmeno A0 basta — conservativo, non si inventa un formato.
    """
    title_block_template = title_block_template or DEFAULT_TITLE_BLOCK_TEMPLATE
    part_bbox = _doc_bbox(doc)
    if part_bbox is None:
        raise ValueError("add_frame(): doc.edges è vuoto, niente attorno a cui costruire una cornice")

    pxmin, pymin, pxmax, pymax = part_bbox
    pw, ph = pxmax - pxmin, pymax - pymin

    required_w = max(pw + 2 * margin, title_block_template.width + 2 * margin)
    required_h = ph + title_block_template.height + 3 * margin

    candidates = []
    for name, (short, long_) in _ISO_SHEET_SIZES.items():
        candidates.append((short * long_, name, long_, short))  # orizzontale
        candidates.append((short * long_, name, short, long_))  # verticale
    candidates.sort(key=lambda c: c[0])

    fit = next((c for c in candidates if c[2] >= required_w and c[3] >= required_h), None)
    if fit is None:
        raise ValueError(
            f"add_frame(): nessun formato ISO (fino ad A0) contiene "
            f"{pw:.0f}x{ph:.0f} mm con margine {margin}"
        )
    _, iso_name, sheet_w, sheet_h = fit

    # Centrata sulla larghezza che il PEZZO richiede (pw + 2*margin), non su
    # `required_w` — quando è il cartiglio a dettare la larghezza del foglio
    # (pezzi piccoli), il pezzo va comunque centrato, non spinto da un lato.
    part_w_needed = pw + 2 * margin
    slack_w = sheet_w - part_w_needed
    frame_xmin = pxmin - margin - slack_w / 2.0
    frame_xmax = frame_xmin + sheet_w

    # In verticale niente centratura: il cartiglio resta a filo del margine
    # inferiore (convenzione reale), l'eventuale spazio in più va tutto sopra
    # il pezzo come margine extra.
    frame_ymin = pymin - (2 * margin + title_block_template.height)
    frame_ymax = frame_ymin + sheet_h

    entities = _frame_entities(frame_xmin, frame_ymin, frame_xmax, frame_ymax)
    generated = forge.load_geometry(entities)
    doc.edges.extend(generated.edges)

    return FrameInfo(
        edges=list(generated.edges),
        bbox=(frame_xmin, frame_ymin, frame_xmax, frame_ymax),
        iso_format=iso_name,
        containment=1.0,
        confidence=1.0,
    )


def add_title_block(
    doc,
    fields:   Optional[Dict[str, str]] = None,
    anchor:   Optional[Tuple[float, float]] = None,
    margin:   float = DEFAULT_MARGIN,
    template: Optional[TitleBlockTemplate] = None,
) -> TitleBlock:
    """
    Genera un cartiglio e lo appende a `doc` (mutazione in place, stesso
    idioma di `tag_layout`). Ritorna il `TitleBlock` creato, con le celle
    già a bbox assoluta e il testo composto — già taggato `role="title_block"`,
    non serve `tag_layout` per questa geometria.

    `fields`  : {nome_campo: valore} — dati del chiamante, mai nel repo. Un
                nome che non corrisponde a nessun `FieldSlot` del template
                alza `ValueError` (protezione da typo).
    `anchor`  : angolo in basso a destra del cartiglio. Se `None`, si usa
                l'angolo in basso a destra della bbox corrente di `doc.edges`
                (meno `margin`) — agnostico rispetto a formato/orientamento
                del foglio: se `add_frame(doc)` è già stato chiamato, quella
                bbox è la cornice, e il cartiglio finisce nel suo angolo.
                `ValueError` se `doc.edges` è vuoto e `anchor` non è dato:
                niente punto a caso.
    `template`: design del cartiglio, default `DEFAULT_TITLE_BLOCK_TEMPLATE`.
                Un consumatore può passarne uno proprio (stesso spirito di
                `roles.py` — costruzione esterna).
    """
    template = template or DEFAULT_TITLE_BLOCK_TEMPLATE
    fields = fields or {}

    valid_names = {f.name for f in template.fields}
    unknown = set(fields) - valid_names
    if unknown:
        raise ValueError(
            f"add_title_block(): campi sconosciuti {sorted(unknown)} — validi: {sorted(valid_names)}"
        )

    doc_bbox = _doc_bbox(doc)
    if anchor is None:
        if doc_bbox is None:
            raise ValueError("add_title_block(): doc.edges è vuoto, serve un anchor esplicito")
        _, min_y, max_x, _ = doc_bbox
        anchor = (max_x - margin, min_y + margin)

    if doc_bbox is not None:
        min_x, min_y, max_x, max_y = doc_bbox
        bl_x, bl_y = anchor[0] - template.width, anchor[1]
        if bl_x < min_x or bl_y < min_y or anchor[0] > max_x or bl_y + template.height > max_y:
            raise ValueError(
                "add_title_block(): il cartiglio non entra nella bbox di doc con questo anchor/margin"
            )

    entities, cells, notes = _place(template, anchor, fields)

    generated = forge.load_geometry(entities)
    doc.edges.extend(generated.edges)
    doc.annotations.extend(notes)

    bbox = (anchor[0] - template.width, anchor[1], anchor[0], anchor[1] + template.height)
    return TitleBlock(edges=list(generated.edges), bbox=bbox, cells=cells, confidence=1.0)


def _zone_count(length: float) -> int:
    """
    Quante zone su un lato lungo `length` — ISO 5457: lunghezza di zona fra
    25 e 75 mm, indicativamente 50 mm. Un formato più grande ha più zone,
    quindi più lineette: è la stessa griglia di riferimento, non decorazione
    diversa per formato.
    """
    return max(2, round(length / _ZONE_TARGET))


def _frame_entities(xmin: float, ymin: float, xmax: float, ymax: float) -> list:
    """
    Pura: bbox esterna della cornice → entità per `forge.load_geometry` —
    bordo esterno, bordo interno inset di `_BORDER_GAP`, la lineetta di
    centratura al centro di ogni lato (presa dal template fatto a mano da
    Federico in `templates/`, MAP D9), e le lineette della griglia di
    riferimento ISO 5457 che dividono ogni lato in zone — un formato più
    grande ha più zone, quindi più lineette (MAP D10). La lineetta di
    centratura non si duplica se cade su un confine di zona.
    """
    ixmin, iymin, ixmax, iymax = xmin + _BORDER_GAP, ymin + _BORDER_GAP, xmax - _BORDER_GAP, ymax - _BORDER_GAP
    width, height = xmax - xmin, ymax - ymin
    mid_x, mid_y = (xmin + xmax) / 2.0, (ymin + ymax) / 2.0

    def rect(x0, y0, x1, y1):
        return {"type": "polyline", "points": [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "closed": True, "role": FRAME}

    def tick(x0, y0, x1, y1):
        return {"type": "line", "start": (x0, y0), "end": (x1, y1), "role": FRAME}

    entities = [
        rect(xmin, ymin, xmax, ymax),
        rect(ixmin, iymin, ixmax, iymax),
        tick(mid_x, ymax, mid_x, iymax),   # centratura, sopra
        tick(mid_x, ymin, mid_x, iymin),   # centratura, sotto
        tick(xmin, mid_y, ixmin, mid_y),   # centratura, sinistra
        tick(xmax, mid_y, ixmax, mid_y),   # centratura, destra
    ]

    n_x, n_y = _zone_count(width), _zone_count(height)
    for k in range(1, n_x):
        x = xmin + k * width / n_x
        if abs(x - mid_x) > 1e-6:
            entities.append(tick(x, ymax, x, iymax))
            entities.append(tick(x, ymin, x, iymin))
    for k in range(1, n_y):
        y = ymin + k * height / n_y
        if abs(y - mid_y) > 1e-6:
            entities.append(tick(xmin, y, ixmin, y))
            entities.append(tick(xmax, y, ixmax, y))

    return entities


def _doc_bbox(doc) -> Optional[BBox]:
    """bbox corrente di doc.edges, o None se non c'è geometria."""
    points = [p for e in doc.edges for p in (e.start, e.end)]
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _place(template: TitleBlockTemplate, anchor: Tuple[float, float], fields: Dict[str, str]):
    """
    Pura: template + anchor + valori → entità per `forge.load_geometry`,
    `Cell` a bbox assoluta, `forge.Note` per il testo di ogni riga.

    Etichetta e valore sono due `Note` separate impilate, non affiancate:
    etichetta piccola in alto nella riga, valore più grande sotto — lo stesso
    schema del template ISO scaricato in `templates/` (MAP D9), non una
    stringa unica "etichetta: valore".
    """
    bl_x, bl_y = anchor[0] - template.width, anchor[1]

    def to_abs(bbox: BBox) -> BBox:
        x0, y0, x1, y1 = bbox
        return (bl_x + x0, bl_y + y0, bl_x + x1, bl_y + y1)

    corners = [
        (bl_x, bl_y), (bl_x + template.width, bl_y),
        (bl_x + template.width, bl_y + template.height), (bl_x, bl_y + template.height),
    ]
    entities = [{"type": "polyline", "points": corners, "closed": True, "role": TITLE_BLOCK}]

    # divisori orizzontali fra le righe (i confini che coincidono col
    # perimetro, 0 e height, sono già il rettangolo esterno — non duplicarli)
    row_ys = sorted({f.bbox[1] for f in template.fields} | {f.bbox[3] for f in template.fields})
    for y in row_ys[1:-1]:
        entities.append({
            "type": "line",
            "start": (bl_x, bl_y + y), "end": (bl_x + template.width, bl_y + y),
            "role": TITLE_BLOCK,
        })

    cells = []
    notes = []
    for f in template.fields:
        abs_bbox = to_abs(f.bbox)
        value = fields.get(f.name) or "-"
        x = abs_bbox[0] + _CELL_PADDING
        row_top = abs_bbox[3]
        label_y = row_top - _CELL_PADDING - _LABEL_HEIGHT
        value_y = label_y - _CELL_PADDING - _VALUE_HEIGHT

        cells.append(Cell(bbox=abs_bbox, text=f"{f.label}: {value}"))
        notes.append(forge.Note(position=(x, label_y), text=f.label, height=_LABEL_HEIGHT, layer=TITLE_BLOCK))
        notes.append(forge.Note(position=(x, value_y), text=str(value), height=_VALUE_HEIGHT, layer=TITLE_BLOCK))

    return entities, cells, notes
