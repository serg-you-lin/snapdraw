"""
snapdraw/model.py
-----------------
Il dominio di snapdraw: cosa vuol dire "cornice" e "cartiglio" in un disegno
impaginato, e cosa snapdraw restituisce a chi lo chiama.

Nessuna dipendenza da forge o da un formato: dataclass pure. Gli `Edge` che
questi oggetti trattengono (`FrameInfo.edges`, `TitleBlock.edges`) sono
riferimenti agli `Edge` di `forge.load_dxf(...).edges` — snapdraw li individua e
li marca, non ne fa copie.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# BBox = (xmin, ymin, xmax, ymax)
BBox = Tuple[float, float, float, float]


@dataclass
class FrameInfo:
    """
    La cornice di formato: il riquadro esterno del foglio.

    edges       : gli Edge di doc.edges che compongono il riquadro
    bbox        : (xmin, ymin, xmax, ymax) del riquadro
    iso_format  : formato ISO riconosciuto dalle dimensioni ("A4", "A3", ...) o None
    containment : frazione della geometria restante contenuta nella bbox (0..1)
    confidence  : 0..1 — quanto snapdraw è sicuro che questo sia la cornice
    """
    edges:       list
    bbox:        BBox
    iso_format:  Optional[str] = None
    containment: float = 0.0
    confidence:  float = 0.0


@dataclass
class Cell:
    """Una cella del cartiglio: un rettangolo interno e il testo che racchiude."""
    bbox: BBox
    text: str = ""


@dataclass
class TitleBlock:
    """
    Il cartiglio: il riquadro delle informazioni, suddiviso in celle.

    edges      : gli Edge di doc.edges che compongono il riquadro (bordo + griglia)
    bbox       : (xmin, ymin, xmax, ymax) del riquadro
    cells      : le celle interne con il testo contenuto
    confidence : 0..1
    """
    edges:      list
    bbox:       BBox
    cells:      List[Cell] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class FieldSlot:
    """
    Una cella di un `TitleBlockTemplate`: nome canonico del campo, bbox
    RELATIVA all'angolo in basso a sinistra del cartiglio (origine (0,0) —
    non ancora piazzata su un foglio reale), etichetta statica stampata.
    """
    name:  str
    bbox:  BBox
    label: str = ""


@dataclass
class TitleBlockTemplate:
    """
    Il design di un cartiglio da generare: righe strette impilate in
    verticale, come un cartiglio reale (preso a riferimento un template ISO
    scaricato, MAP D9) — non celle larghe affiancate.

    Un consumatore può costruirsene uno proprio (stesso spirito di
    `snapdraw/roles.py` — costruzione esterna, snapdraw non impone un solo
    design) e passarlo a `generate.add_title_block(..., template=...)`.

    `fields` : una `FieldSlot` per riga (bbox piena larghezza, righe
               impilate dall'alto in basso). Etichetta piccola in alto nella
               riga, valore più grande sotto — non affiancati.
    """
    width:  float
    height: float
    fields: List[FieldSlot] = field(default_factory=list)


@dataclass
class FrameLayout:
    """
    Il risultato di `sd.detect_frame(doc)`.

    frame       : la cornice, o None se snapdraw non l'ha individuata con sicurezza
    title_block : il cartiglio, o None
    flags       : diagnostica non bloccante — "frame: uncertain",
                  "title_block: uncertain", "multiple_frames", ...
    """
    frame:       Optional[FrameInfo] = None
    title_block: Optional[TitleBlock] = None
    flags:       List[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return self.frame is None and self.title_block is None


@dataclass
class View:
    """
    Un'isola di `forge.island(...)` letta come vista del foglio.

    index        : posizione in `result.clusters`
    bbox         : (xmin, ymin, xmax, ymax) del contorno esterno
    kind         : "orthographic" / "pictorial" / "symbol"
    height_mates : viste ortogonali con la stessa estensione verticale (frontale ↔ laterale)
    width_mates  : viste ortogonali con la stessa estensione orizzontale (frontale ↔ pianta)
    """
    index:        int
    bbox:         BBox
    kind:         str
    height_mates: List[int] = field(default_factory=list)
    width_mates:  List[int] = field(default_factory=list)

    @property
    def width(self) -> float:
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> float:
        return self.bbox[3] - self.bbox[1]


@dataclass
class ViewLayout:
    """
    Il risultato di `sd.read_views(result)`.

    views     : una View per cluster, stesso ordine di `result.clusters`
    principal : indice della vista principale, o None se incerta
    depth     : la terza dimensione letta dalle viste compagne della
                principale, o None — è un fatto di proiezione, non uno
                spessore: che sia lamiera lo decide chi legge sopra
    flags     : "principal: uncertain", "principal: single projection",
                "depth: inconsistent", ...
    """
    views:     List[View] = field(default_factory=list)
    principal: Optional[int] = None
    depth:     Optional[float] = None
    flags:     List[str] = field(default_factory=list)


@dataclass
class HoleCallout:
    """
    La quota di diametro agganciata a un cerchio, letta.

    text        : il testo come sul disegno (`display_text`), es. "∅5,3+0,05^-0"
    designation : "Ø" o "M" (filetto)
    nominal     : il valore scritto, es. 5.3
    upper/lower : scostamenti di tolleranza scritti, o None
    measured    : la misura della geometria (`measured_value`), in unità del disegno
    rest        : testo dopo valore e tolleranza non letto ("" se tutto letto)
    """
    text:        str
    designation: str
    nominal:     float
    measured:    float
    upper:       Optional[float] = None
    lower:       Optional[float] = None
    rest:        str = ""


@dataclass
class HoleTrace:
    """
    La traccia di un foro in una vista compagna: le due pareti (linee
    parallele distanti un diametro) alla quota del cerchio.

    view    : indice della vista compagna
    through : le pareti attraversano tutta la vista
    length  : lunghezza delle pareti, in unità del disegno
    """
    view:    int
    through: bool
    length:  float


@dataclass
class Hole:
    """
    Un cerchio della vista principale letto come foro.

    path           : percorso in `result`, es. "clusters[0].inners[2]"
    center         : centro nel disegno
    drawn_diameter : diametro misurato sulla geometria
    callout        : la quota di diametro agganciata, o None
    traces         : le tracce trovate nelle viste compagne
    through        : passante? — da traccia, o per convenzione se il disegno non dice niente
    drawn_depth    : profondità in unità del disegno (traccia, o profondità delle viste)
    depth          : profondità alla scala delle quote, o None se la scala non si legge
    source         : "trace" o "convention"
    flags          : "callout: missing", "trace: inconsistent", ...
    """
    path:           str
    center:         Tuple[float, float]
    drawn_diameter: float
    callout:        Optional[HoleCallout] = None
    traces:         List[HoleTrace] = field(default_factory=list)
    through:        Optional[bool] = None
    drawn_depth:    Optional[float] = None
    depth:          Optional[float] = None
    source:         str = ""
    flags:          List[str] = field(default_factory=list)


@dataclass
class HoleGroup:
    """Fori uguali: stessa quota, stessa tolleranza, stesso tipo e profondità."""
    holes:       List[Hole]
    designation: Optional[str]
    diameter:    Optional[float]
    upper:       Optional[float]
    lower:       Optional[float]
    through:     Optional[bool]
    depth:       Optional[float]

    @property
    def count(self) -> int:
        return len(self.holes)


@dataclass
class HoleLayout:
    """
    Il risultato di `sd.read_holes(doc, result, views)`.

    holes  : un Hole per cerchio della vista principale
    groups : i fori raggruppati come li direbbe una distinta
    scale  : valore scritto / valore misurato dalle quote di diametro (0.8 = geometria a 1,25:1), o None
    flags  : "holes: no principal view", "scale: inconsistent", ...
    """
    holes:  List[Hole] = field(default_factory=list)
    groups: List[HoleGroup] = field(default_factory=list)
    scale:  Optional[float] = None
    flags:  List[str] = field(default_factory=list)
