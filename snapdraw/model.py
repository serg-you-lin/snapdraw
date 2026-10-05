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
from typing import Dict, List, Optional, Tuple

# BBox = (xmin, ymin, xmax, ymax)
BBox = Tuple[float, float, float, float]


@dataclass
class FrameInfo:
    """
    La cornice di formato: il riquadro esterno del foglio.

    edges       : gli Edge di doc.edges che compongono il riquadro
    bbox        : (xmin, ymin, xmax, ymax) del riquadro
    inner_bbox  : il riquadro più interno (la squadratura) se la cornice ha più
                  bordi, o None; fra i due sta la fascia della cornice
    iso_format  : formato ISO riconosciuto dalle dimensioni ("A4", "A3", ...) o None
    containment : frazione della geometria restante contenuta nella bbox (0..1)
    confidence  : 0..1 — quanto snapdraw è sicuro che questo sia la cornice
    """
    edges:       list
    bbox:        BBox
    inner_bbox:  Optional[BBox] = None
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
    has_text   : False se è una griglia vuota presa perché sta nell'angolo in basso a destra della cornice (MAP D32)
    """
    edges:      list
    bbox:       BBox
    cells:      List[Cell] = field(default_factory=list)
    confidence: float = 0.0
    has_text:   bool = True


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
    Un'isola di `sheet_islands(...)` letta come vista del foglio.

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
class Callout:
    """
    La quota di diametro agganciata a una feature, letta.

    text        : il testo come sul disegno (`display_text`), es. "∅5,3+0,05^-0"
    designation : "Ø" o "M" (filetto)
    nominal     : il valore scritto, es. 5.3
    measured    : la misura della geometria (`measured_value`), in unità del disegno
    upper/lower : scostamenti di tolleranza scritti, o None
    count       : quante feature uguali copre ("n°30 fori", "4xØ5"), o None
    rest        : testo dopo valore e tolleranza non letto ("" se tutto letto)
    """
    text:        str
    designation: str
    nominal:     float
    measured:    float
    upper:       Optional[float] = None
    lower:       Optional[float] = None
    count:       Optional[int] = None
    rest:        str = ""


@dataclass
class Trace:
    """
    La traccia di una feature in una vista compagna: le due pareti (linee
    parallele ai bordi della forma, lungo l'asse della compagna).

    view    : indice della vista compagna
    through : le pareti vanno da faccia a faccia
    length  : lunghezza delle pareti, in unità del disegno
    """
    view:    int
    through: bool
    length:  float


@dataclass
class Feature:
    """
    Un contorno interno di una vista ortogonale letto come feature.

    kind      : "hole" (cerchio) / "slot" (stadio: asola) / "opening"
                (ogni altra forma: rettangolo, poligono, forma libera) —
                dalla forma di `forge.geometry.contour_shape` (`shape.kind`), un
                fatto geometrico
    hole_type : solo per i fori — "plain", "threaded" (arco di cresta a ~270°
                o quota M), "counterbore" (lamatura: sede concentrica con
                pareti cieche nella compagna), "countersink" (svasatura: linee
                oblique dalla sede al foro nella compagna), "seated" (sede
                concentrica senza prova del tipo); None per il resto
    role      : il ruolo con cui la feature si etichetta (`snapdraw.roles`):
                per i fori uno per tipo (`hole`, `threaded_hole`,
                `countersink`, `counterbore`, `seated_hole`)
    view      : indice della vista (cluster) dove sta
    path      : percorso del contorno in `result` al momento della lettura,
                es. "clusters[0].inners[2]" (`tag_features` lo sposta dopo)
    shape     : la `forge.geometry.ContourShape` del contorno
    contours  : i contorni della feature (il foro, e la sede se c'è) — la
                geometria che un exporter scrive
    outer_path/outer_shape : la sede concentrica di una lamatura/svasatura
    hidden    : il contorno è disegnato tratteggiato (la feature sta dall'altra parte)
    thread_diameter : diametro dell'arco di cresta del filetto, in unità del disegno
    callout   : la quota di diametro agganciata, o None
    traces    : le tracce trovate nelle viste compagne
    through   : passante? — da traccia, o per convenzione se il disegno non dice niente
    drawn_depth : profondità in unità del disegno
    depth     : profondità alla scala della vista, o None se la scala non si legge
    seat_depth : profondità della sede di una lamatura, alla scala della vista
    scale     : scala della vista usata per le misure (scritto / misurato)
    source    : "trace" o "convention"
    confidence: 0..1
    flags     : "callout: missing", "trace: inconsistent", ...
    """
    kind:        str
    view:        int
    path:        str
    shape:       object
    contours:    list = field(default_factory=list)
    hole_type:   Optional[str] = None
    role:        str = ""
    outer_path:  Optional[str] = None
    outer_shape: object = None
    hidden:      bool = False
    thread_diameter: Optional[float] = None
    callout:     Optional[Callout] = None
    traces:      List[Trace] = field(default_factory=list)
    through:     Optional[bool] = None
    drawn_depth: Optional[float] = None
    depth:       Optional[float] = None
    seat_depth:  Optional[float] = None
    scale:       Optional[float] = None
    source:      str = ""
    confidence:  float = 0.0
    flags:       List[str] = field(default_factory=list)

    @property
    def center(self) -> Tuple[float, float]:
        return tuple(self.shape.center)

    @property
    def segments(self) -> list:
        """Il contorno principale (il foro), per chi vuole un solo contorno."""
        return self.contours[0].segments if self.contours else []

    @property
    def size(self) -> Tuple[float, float]:
        """(lunghezza, larghezza) alla scala della vista, o disegnate se la scala manca."""
        k = self.scale or 1.0
        return self.shape.length * k, self.shape.width * k

    @property
    def diameter(self) -> Optional[float]:
        """Il diametro di un foro: quello scritto nella quota, o il disegnato alla scala della vista."""
        if self.kind != "hole":
            return None
        if self.callout is not None:
            return self.callout.nominal
        return self.shape.diameter * (self.scale or 1.0)

    def to_dict(self) -> dict:
        """La feature come dati: niente geometria, i contorni restano nel risultato di forge."""
        r = lambda v: None if v is None else round(v, 4)
        c = self.callout
        return {
            "kind": self.kind, "hole_type": self.hole_type, "role": self.role,
            "view": self.view, "path": self.path, "shape": self.shape.to_dict(),
            "diameter": r(self.diameter), "size": [r(v) for v in self.size],
            "thread_diameter": r(self.thread_diameter),
            "seat": None if self.outer_shape is None else {"path": self.outer_path, "shape": self.outer_shape.to_dict(),
                                                           "depth": r(self.seat_depth)},
            "callout": None if c is None else {"text": c.text, "designation": c.designation, "nominal": c.nominal,
                                               "upper": c.upper, "lower": c.lower, "count": c.count, "rest": c.rest},
            "through": self.through, "depth": r(self.depth), "drawn_depth": r(self.drawn_depth),
            "scale": r(self.scale), "hidden": self.hidden,
            "source": self.source, "confidence": self.confidence, "flags": list(self.flags),
        }


@dataclass
class FeatureGroup:
    """Feature uguali: stesso tipo, stessa misura e tolleranza, stesso passante e profondità."""
    features:  List[Feature]
    kind:      str
    hole_type: Optional[str]

    @property
    def count(self) -> int:
        return len(self.features)

    @property
    def first(self) -> Feature:
        return self.features[0]


@dataclass
class FeatureLayout:
    """
    Il risultato di `sd.read_features(doc, result, views)`.

    features : una Feature per contorno interno riconosciuto, su tutte le viste ortogonali
    groups   : le feature raggruppate come le direbbe una distinta
    scales   : vista → scala (scritto / misurato dalle sue quote), None se la vista non ha quote
    flags    : "scale: view 2 mixed", "features: no orthographic view", ...
    """
    features: List[Feature] = field(default_factory=list)
    groups:   List[FeatureGroup] = field(default_factory=list)
    scales:   Dict[int, Optional[float]] = field(default_factory=dict)
    flags:    List[str] = field(default_factory=list)

    def of_kind(self, kind: str) -> List[Feature]:
        return [f for f in self.features if f.kind == kind]

    def to_dict(self) -> dict:
        return {"features": [f.to_dict() for f in self.features],
                "scales": {str(k): v for k, v in sorted(self.scales.items())},
                "flags": list(self.flags)}
