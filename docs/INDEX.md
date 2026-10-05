# snapdraw — code index

**Generated file — do not edit by hand.** Regenerate with:

```
python scripts/gen_index.py
```

What this is: the lookup table of *what already exists* in the package, down to internal helpers. `docs/API.md` documents the public surface (`snapdraw.<name>`) with full cards; this file lists every module-level function and class so nothing gets rewritten because it was not found. Signatures and docstring lines come straight from the source, so they cannot drift.

`13` modules · `74` module-level functions · `13` classes · `2657` lines of code.

Sections: [Lookup](#lookup) · [Duplicate names](#duplicate-names) · [Dependency rule](#dependency-rule) · [By module](#by-module) · [Internal dependencies](#internal-dependencies)

---

## Lookup

Every module-level name in the package, alphabetically. **Search here before writing a new helper.**

| name | kind | location | what |
|---|---|---|---|
| `add_frame` | func | `snapdraw/generate.py:74` | Genera una cornice ISO attorno alla geometria corrente di `doc` e la |
| `add_title_block` | func | `snapdraw/generate.py:147` | Genera un cartiglio e lo appende a `doc` (mutazione in place, stesso |
| `_anchor_by_center` | func | `snapdraw/features.py:363` | Le quote di diametro che forge non ha agganciato: i due punti misurati |
| `annotation_density_ratio` | func | `snapdraw/geometry.py:156` | Quante volte più annotazioni per unità di area cadono dentro `rect` |
| `_area` | func | `snapdraw/views.py:160` |  |
| `_build_cells` | func | `snapdraw/titleblock.py:231` | I divisori tagliano `rect` in celle; ogni cella raccoglie il testo delle |
| `Callout` | class | `snapdraw/model.py:165` | La quota di diametro agganciata a una feature, letta. |
| `Cell` | class | `snapdraw/model.py:44` | Una cella del cartiglio: un rettangolo interno e il testo che racchiude. |
| `classify_view` | func | `snapdraw/views.py:52` | "orthographic" se almeno metà della lunghezza dei LineSeg (contorno e |
| `_confidence` | func | `snapdraw/frame.py:141` | Confidenza grezza: parte dal contenimento, bonus se il formato ISO torna, |
| `_confidence` | func | `snapdraw/titleblock.py:211` | Confidenza grezza, stesso spirito additivo di `frame._confidence` — da |
| `_conical` | func | `snapdraw/features.py:458` | Nelle compagne, per ognuno dei due lati una linea obliqua che va dal |
| `containment` | func | `snapdraw/geometry.py:102` | Frazione degli Edge esterni al rettangolo i cui endpoint stanno dentro la |
| `_describe` | func | `snapdraw/features.py:596` |  |
| `describe_features` | func | `snapdraw/features.py:308` | I gruppi come li scriverebbe una persona: "2 fori passanti Ø5,3 +0,05/0, profondità 4". |
| `detect_frame` | func | `snapdraw/recipe.py:37` | Rileva cornice e cartiglio nella geometria grezza di `doc`. |
| `diameter_callouts` | func | `snapdraw/features.py:170` | Percorso dell'elemento quotato → la quota di diametro che lo misura (`forge.dimension_references`). |
| `_doc_bbox` | func | `snapdraw/generate.py:264` | bbox corrente di doc.edges, o None se non c'è geometria. |
| `_edges_inside` | func | `snapdraw/titleblock.py:177` | Tutti gli Edge di `doc.edges` (qualunque tipo di segmento — griglia, |
| `_end_kind` | func | `snapdraw/features.py:554` | Dove finisce una parete (coordinata `e` lungo la parete, alla quota |
| `_expand` | func | `snapdraw/rules.py:73` | Una voce del JSON → una o più RoleRule (una per elemento di una lista). |
| `extend_frame` | func | `snapdraw/frame.py:84` | Estende `frame` a quello che sta nella sua fascia, fra bordo esterno e |
| `extend_titleblock` | func | `snapdraw/titleblock.py:110` | Estende `title_block` alle tabelle attaccate: ogni linea orizzontale o |
| `_feature` | func | `snapdraw/features.py:337` | Una feature da un contorno: tipo dalla forma, filetto, quota, traccia e profondità (senza sede). |
| `Feature` | class | `snapdraw/model.py:203` | Un contorno interno di una vista ortogonale letto come feature. |
| `feature_contours` | func | `snapdraw/features.py:116` | (indice, contorno, forma) dei contorni interni della vista con una forma |
| `feature_metadata` | func | `snapdraw/features.py:298` | Le feature di un cluster come dati, per il JSON di forge: |
| `feature_trace` | func | `snapdraw/features.py:146` | Le tracce di una forma (riquadro `bounds`) nelle viste compagne di |
| `FeatureGroup` | class | `snapdraw/model.py:305` | Feature uguali: stesso tipo, stessa misura e tolleranza, stesso passante e profondità. |
| `FeatureLayout` | class | `snapdraw/model.py:321` | Il risultato di `sd.read_features(doc, result, views)`. |
| `FieldSlot` | class | `snapdraw/model.py:69` | Una cella di un `TitleBlockTemplate`: nome canonico del campo, bbox |
| `find_frame` | func | `snapdraw/frame.py:42` | Rileva la cornice di formato nella geometria grezza di `doc` |
| `find_rectangles` | func | `snapdraw/geometry.py:55` | Trova i rettangoli axis-aligned "di bordo": quelli i cui quattro lati sono |
| `find_titleblock` | func | `snapdraw/titleblock.py:45` | Delimita il cartiglio nella geometria grezza di `doc`. |
| `_fmt` | func | `snapdraw/features.py:642` |  |
| `_frame_entities` | func | `snapdraw/generate.py:220` | Pura: bbox esterna della cornice → entità per `forge.load_geometry` — |
| `FrameInfo` | class | `snapdraw/model.py:23` | La cornice di formato: il riquadro esterno del foglio. |
| `FrameLayout` | class | `snapdraw/model.py:101` | Il risultato di `sd.detect_frame(doc)`. |
| `grid_dividers` | func | `snapdraw/geometry.py:140` | Linee dritte STRETTAMENTE interne a `rect` (bordo escluso) che lo |
| `group_features` | func | `snapdraw/features.py:215` | Raggruppa per tipo, misura (scritta o disegnata), tolleranza, sede, passante e profondità. |
| `_is_genuine_grid` | func | `snapdraw/titleblock.py:191` | True se almeno un asse è suddiviso in segmenti **comparabili**, non |
| `_is_hidden` | func | `snapdraw/features.py:506` | Il contorno è tutto tratteggio uniforme: la feature si vede in trasparenza. |
| `is_iso_ratio` | func | `snapdraw/geometry.py:97` | True se il rapporto dei lati è ≈ √2 (formati ISO). |
| `iso_format` | func | `snapdraw/geometry.py:115` | Formato ISO dedotto dalle dimensioni del rettangolo, o None. Assume mm. |
| `_joins` | func | `snapdraw/features.py:478` | Il segmento va dalla quota `a` alla quota `b` lungo `axis` (in un verso o nell'altro), non parallelo all'asse. |
| `line_edges` | func | `snapdraw/geometry.py:46` | Gli Edge di doc.edges il cui segmento è un LineSeg. |
| `load_rules` | func | `snapdraw/rules.py:50` | Legge `<folder>/<name>.json` (default `rules/` del repo) e ritorna le |
| `_mates` | func | `snapdraw/features.py:358` |  |
| `_mode` | func | `snapdraw/features.py:589` | Il valore più frequente, contando uguali quelli entro `agreement` relativo. |
| `_number` | func | `snapdraw/features.py:638` |  |
| `_pair_concentric` | func | `snapdraw/features.py:315` | (percorso, contorno, forma, sede) — nei gruppi di cerchi concentrici |
| `parse_callout` | func | `snapdraw/features.py:181` | Il testo di una quota di diametro: "Ø"/"M", il valore, la tolleranza |
| `_place` | func | `snapdraw/generate.py:274` | Pura: template + anchor + valori → entità per `forge.load_geometry`, |
| `principal_view` | func | `snapdraw/views.py:82` | La vista con compagni in tutte e due le direzioni (la più grande, se più |
| `projection_mates` | func | `snapdraw/views.py:65` | Per ogni vista ortogonale: (height_mates, width_mates). Stessa |
| `_read_callout` | func | `snapdraw/features.py:407` |  |
| `_read_depth` | func | `snapdraw/features.py:418` | Passante e profondità disegnata: dalla traccia, altrimenti per convenzione. |
| `read_features` | func | `snapdraw/features.py:230` | Ricetta: la scala di ogni vista; per ogni vista ortogonale i contorni |
| `_read_seat` | func | `snapdraw/features.py:434` | La sede concentrica (non passante: quella la separa `read_features`), |
| `read_titleblock` | func | `snapdraw/titleblock.py:293` | Legge le celle del cartiglio → dict dei campi |
| `read_views` | func | `snapdraw/views.py:120` | Ricetta: classifica ogni cluster, trova i compagni di proiezione, la |
| `_reference` | func | `snapdraw/views.py:152` | La vista che fa da metro per i simboli: la principale, o la più grande. |
| `register_defaults` | func | `snapdraw/roles.py:64` | Registra colore + nome layer di default per cornice, cartiglio, costruzione e feature — |
| `rejected_border` | func | `snapdraw/frame.py:115` | Il riquadro di bordo più grande che racchiude `title_block` ma che |
| `render_view` | func | `snapdraw/render.py:57` | Disegna `edges` in un PNG ritagliato su `bbox`, nero su bianco, con |
| `render_views` | func | `snapdraw/render.py:97` | Ricetta: un PNG per vista in `folder` (`view_<indice>.png`), ritagliato |
| `_role` | func | `snapdraw/features.py:486` | Un ruolo per tipo di foro (si vede nell'export, lo usa chi sviluppa il pezzo); asola e apertura il loro. |
| `_round` | func | `snapdraw/features.py:634` |  |
| `rules_from_dict` | func | `snapdraw/rules.py:61` | Come `load_rules`, da un dict già letto. |
| `_share_callouts` | func | `snapdraw/features.py:389` | Un richiamo che dice quante feature copre ("n°30 fori") vale per i fori |
| `sheet_islands` | func | `snapdraw/views.py:43` | Le isole di un foglio: `forge.island` con il `max_gap` scelto da |
| `_signed` | func | `snapdraw/features.py:646` |  |
| `_split_labeled_text` | func | `snapdraw/titleblock.py:327` | Ogni etichetta trovata in `text` → valore = il testo fino alla prossima etichetta (o fine stringa). |
| `tag_features` | func | `snapdraw/features.py:279` | Attacca le feature ai loro cluster (`cluster.detected["view_features"]`, |
| `tag_layout` | func | `snapdraw/tag.py:28` | Setta `edge.role` sugli Edge di cornice e cartiglio in `layout`. |
| `_thread_crest` | func | `snapdraw/features.py:351` | L'arco di cresta del filetto attorno al foro: ~270°, poco più grande (`forge.geometry.arcs_around`). |
| `TitleBlock` | class | `snapdraw/model.py:51` | Il cartiglio: il riquadro delle informazioni, suddiviso in celle. |
| `TitleBlockTemplate` | class | `snapdraw/model.py:81` | Il design di un cartiglio da generare: righe strette impilate in |
| `_to_scale` | func | `snapdraw/features.py:494` | Profondità alla scala della vista; senza scala, flag e profondità disegnata soltanto. |
| `Trace` | class | `snapdraw/model.py:188` | La traccia di una feature in una vista compagna: le due pareti (linee |
| `_trace_in` | func | `snapdraw/features.py:512` | Le due pareti dentro `bbox` alle quote `lo_level`/`hi_level` lungo |
| `View` | class | `snapdraw/model.py:120` | Un'isola di `sheet_islands(...)` letta come vista del foglio. |
| `view_depth` | func | `snapdraw/views.py:101` | La terza dimensione della vista principale: la larghezza dei compagni in |
| `view_edges` | func | `snapdraw/render.py:40` | Gli edge di `doc` interamente dentro `bbox`: contorni, linee nascoste, |
| `view_scales` | func | `snapdraw/features.py:79` | La scala di ogni vista: valore scritto / valore misurato, il più |
| `ViewLayout` | class | `snapdraw/model.py:146` | Il risultato di `sd.read_views(result)`. |
| `_zone_count` | func | `snapdraw/generate.py:210` | Quante zone su un lato lungo `length` — ISO 5457: lunghezza di zona fra |

## Duplicate names

Same name defined at module level in different modules. Not automatically a bug — but each one is either two implementations of one job (merge them) or two different jobs sharing a name (rename one).

| name | defined in |
|---|---|
| `_confidence` | `snapdraw/frame.py:141` · `snapdraw/titleblock.py:211` |

## Dependency rule

- `(root)` never imports `snapbend`, `ezdxf`

`TYPE_CHECKING`-only imports count as violations here and must be verified by hand.

**Clean** — no violation found.

## By module

### `snapdraw/` (root)

#### `snapdraw/__init__.py` — 127 lines

_snapdraw_

No module-level function or class.

#### `snapdraw/features.py` — 647 lines

_snapdraw/features.py_

- `view_scales(result, views: ViewLayout, agreement: float=SCALE_AGREEMENT) -> Tuple[Dict[int, Optional[float]], List[str]]` — L79 — La scala di ogni vista: valore scritto / valore misurato, il più
- `feature_contours(result, view: int, tolerance: float=TOUCH_TOLERANCE) -> List[Tuple[int, object, object]]` — L116 — (indice, contorno, forma) dei contorni interni della vista con una forma
- `feature_trace(doc, views: ViewLayout, view: int, bounds, tolerance: float=WALL_TOLERANCE) -> List[Trace]` — L146 — Le tracce di una forma (riquadro `bounds`) nelle viste compagne di
- `diameter_callouts(result) -> Dict[str, object]` — L170 — Percorso dell'elemento quotato → la quota di diametro che lo misura (`forge.dimension_references`).
- `parse_callout(dimension) -> Optional[Callout]` — L181 — Il testo di una quota di diametro: "Ø"/"M", il valore, la tolleranza
- `group_features(features: List[Feature]) -> List[FeatureGroup]` — L215 — Raggruppa per tipo, misura (scritta o disegnata), tolleranza, sede, passante e profondità.
- `read_features(doc, result, views: ViewLayout) -> FeatureLayout` — L230 — Ricetta: la scala di ogni vista; per ogni vista ortogonale i contorni
- `tag_features(result, layout: FeatureLayout)` — L279 — Attacca le feature ai loro cluster (`cluster.detected["view_features"]`,
- `feature_metadata(cluster) -> dict` — L298 — Le feature di un cluster come dati, per il JSON di forge:
- `describe_features(layout: FeatureLayout) -> str` — L308 — I gruppi come li scriverebbe una persona: "2 fori passanti Ø5,3 +0,05/0, profondità 4".
- `_pair_concentric(found)` — L315 — (percorso, contorno, forma, sede) — nei gruppi di cerchi concentrici
- `_feature(doc, views, view: int, path: str, contour, shape, callouts, depth, scales, arcs) -> Feature` — L337 — Una feature da un contorno: tipo dalla forma, filetto, quota, traccia e profondità (senza sede).
- `_thread_crest(shape, arcs) -> Optional[ArcSeg]` — L351 — L'arco di cresta del filetto attorno al foro: ~270°, poco più grande (`forge.geometry.arcs_around`).
- `_mates(views, view: int) -> List[int]` — L358
- `_anchor_by_center(result, features: List[Feature], tolerance: float=0.5) -> None` — L363 — Le quote di diametro che forge non ha agganciato: i due punti misurati
- `_share_callouts(features: List[Feature], tolerance: float=WALL_TOLERANCE) -> None` — L389 — Un richiamo che dice quante feature copre ("n°30 fori") vale per i fori
- `_read_callout(feature: Feature, dimension) -> None` — L407
- `_read_depth(feature: Feature, traces: List[Trace], view_depth_value: Optional[float]) -> None` — L418 — Passante e profondità disegnata: dalla traccia, altrimenti per convenzione.
- `_read_seat(feature: Feature, seat, traces: List[Trace], conical: bool, has_mates: bool) -> None` — L434 — La sede concentrica (non passante: quella la separa `read_features`),
- `_conical(doc, views, view: int, seat_bounds, hole_bounds, tolerance: float=WALL_TOLERANCE) -> bool` — L458 — Nelle compagne, per ognuno dei due lati una linea obliqua che va dal
- `_joins(seg, axis: int, a: float, b: float, tolerance: float) -> bool` — L478 — Il segmento va dalla quota `a` alla quota `b` lungo `axis` (in un verso o nell'altro), non parallelo all'asse.
- `_role(feature: Feature) -> str` — L486 — Un ruolo per tipo di foro (si vede nell'export, lo usa chi sviluppa il pezzo); asola e apertura il loro.
- `_to_scale(feature: Feature) -> None` — L494 — Profondità alla scala della vista; senza scala, flag e profondità disegnata soltanto.
- `_is_hidden(contour) -> bool` — L506 — Il contorno è tutto tratteggio uniforme: la feature si vede in trasparenza.
- `_trace_in(doc, bbox, axis: int, lo_level: float, hi_level: float, tolerance: float) -> Optional[Tuple[bool, float]]` — L512 — Le due pareti dentro `bbox` alle quote `lo_level`/`hi_level` lungo
- `_end_kind(doc, axis: int, along: int, e: float, level: float, outward: int, faces: Tuple[float, float], tolerance: float) -> Optional[str]` — L554 — Dove finisce una parete (coordinata `e` lungo la parete, alla quota
- `_mode(values: List[float], agreement: float) -> float` — L589 — Il valore più frequente, contando uguali quelli entro `agreement` relativo.
- `_describe(g: FeatureGroup) -> str` — L596
- `_round(value)` — L634
- `_number(text: str) -> float` — L638
- `_fmt(value: float) -> str` — L642
- `_signed(value: float) -> str` — L646

#### `snapdraw/frame.py` — 151 lines

_snapdraw/frame.py_

- `find_frame(doc, containment_threshold: float=CONTAINMENT_THRESHOLD) -> Optional[FrameInfo]` — L42 — Rileva la cornice di formato nella geometria grezza di `doc`
- `extend_frame(frame: FrameInfo, doc) -> FrameInfo` — L84 — Estende `frame` a quello che sta nella sua fascia, fra bordo esterno e
- `rejected_border(doc, title_block) -> Optional[CoveredRectangle]` — L115 — Il riquadro di bordo più grande che racchiude `title_block` ma che
- `_confidence(rect: CoveredRectangle, cont: float, n_borders: int) -> float` — L141 — Confidenza grezza: parte dal contenimento, bonus se il formato ISO torna,

#### `snapdraw/generate.py` — 320 lines

_snapdraw/generate.py_

- `add_frame(doc, margin: float=DEFAULT_MARGIN, title_block_template: Optional[TitleBlockTemplate]=None) -> FrameInfo` — L74 — Genera una cornice ISO attorno alla geometria corrente di `doc` e la
- `add_title_block(doc, fields: Optional[Dict[str, str]]=None, anchor: Optional[Tuple[float, float]]=None, margin: float=_BORDER_GAP, template: Optional[TitleBlockTemplate]=None) -> TitleBlock` — L147 — Genera un cartiglio e lo appende a `doc` (mutazione in place, stesso
- `_zone_count(length: float) -> int` — L210 — Quante zone su un lato lungo `length` — ISO 5457: lunghezza di zona fra
- `_frame_entities(xmin: float, ymin: float, xmax: float, ymax: float) -> list` — L220 — Pura: bbox esterna della cornice → entità per `forge.load_geometry` —
- `_doc_bbox(doc) -> Optional[BBox]` — L264 — bbox corrente di doc.edges, o None se non c'è geometria.
- `_place(template: TitleBlockTemplate, anchor: Tuple[float, float], fields: Dict[str, str])` — L274 — Pura: template + anchor + valori → entità per `forge.load_geometry`,

#### `snapdraw/geometry.py` — 185 lines

_snapdraw/geometry.py_

- `line_edges(doc) -> list` — L46 — Gli Edge di doc.edges il cui segmento è un LineSeg.
- `find_rectangles(doc, min_side_fraction: float=BORDER_MIN_SIDE_FRACTION, min_side_length: Optional[float]=None) -> List[CoveredRectangle]` — L55 — Trova i rettangoli axis-aligned "di bordo": quelli i cui quattro lati sono
- `is_iso_ratio(rect: CoveredRectangle, tolerance: float=RATIO_TOLERANCE) -> bool` — L97 — True se il rapporto dei lati è ≈ √2 (formati ISO).
- `containment(rect: CoveredRectangle, doc) -> float` — L102 — Frazione degli Edge esterni al rettangolo i cui endpoint stanno dentro la
- `iso_format(rect: CoveredRectangle, tolerance: float=_ISO_SIZE_TOLERANCE) -> Optional[str]` — L115 — Formato ISO dedotto dalle dimensioni del rettangolo, o None. Assume mm.
- `grid_dividers(rect: CoveredRectangle, doc, coverage: float=GRID_COVERAGE) -> Tuple[List[float], List[float]]` — L140 — Linee dritte STRETTAMENTE interne a `rect` (bordo escluso) che lo
- `annotation_density_ratio(rect: CoveredRectangle, doc) -> float` — L156 — Quante volte più annotazioni per unità di area cadono dentro `rect`

#### `snapdraw/model.py` — 341 lines

_snapdraw/model.py_

- **class** `FrameInfo` — L23 — La cornice di formato: il riquadro esterno del foglio.
- **class** `Cell` — L44 — Una cella del cartiglio: un rettangolo interno e il testo che racchiude.
- **class** `TitleBlock` — L51 — Il cartiglio: il riquadro delle informazioni, suddiviso in celle.
- **class** `FieldSlot` — L69 — Una cella di un `TitleBlockTemplate`: nome canonico del campo, bbox
- **class** `TitleBlockTemplate` — L81 — Il design di un cartiglio da generare: righe strette impilate in
- **class** `FrameLayout` — L101 — Il risultato di `sd.detect_frame(doc)`.
  - methods: `is_empty`
- **class** `View` — L120 — Un'isola di `sheet_islands(...)` letta come vista del foglio.
  - methods: `width`, `height`
- **class** `ViewLayout` — L146 — Il risultato di `sd.read_views(result)`.
- **class** `Callout` — L165 — La quota di diametro agganciata a una feature, letta.
- **class** `Trace` — L188 — La traccia di una feature in una vista compagna: le due pareti (linee
- **class** `Feature` — L203 — Un contorno interno di una vista ortogonale letto come feature.
  - methods: `center`, `segments`, `size`, `diameter`, `to_dict`
- **class** `FeatureGroup` — L305 — Feature uguali: stesso tipo, stessa misura e tolleranza, stesso passante e profondità.
  - methods: `count`, `first`
- **class** `FeatureLayout` — L321 — Il risultato di `sd.read_features(doc, result, views)`.
  - methods: `of_kind`, `to_dict`

#### `snapdraw/recipe.py` — 76 lines

_snapdraw/recipe.py_

- `detect_frame(doc) -> FrameLayout` — L37 — Rileva cornice e cartiglio nella geometria grezza di `doc`.

#### `snapdraw/render.py` — 109 lines

_snapdraw/render.py_

- `view_edges(doc, bbox: BBox, tolerance: float=EDGE_TOLERANCE) -> list` — L40 — Gli edge di `doc` interamente dentro `bbox`: contorni, linee nascoste,
- `render_view(edges: list, bbox: BBox, label: str, path: str, size: int=IMAGE_SIZE) -> None` — L57 — Disegna `edges` in un PNG ritagliato su `bbox`, nero su bianco, con
- `render_views(doc, views: ViewLayout, folder: str, size: int=IMAGE_SIZE) -> List[str]` — L97 — Ricetta: un PNG per vista in `folder` (`view_<indice>.png`), ritagliato

#### `snapdraw/roles.py` — 78 lines

_snapdraw/roles.py_

- `register_defaults() -> None` — L64 — Registra colore + nome layer di default per cornice, cartiglio, costruzione e feature —

#### `snapdraw/rules.py` — 79 lines

_snapdraw/rules.py_

- `load_rules(name: str, folder: Optional[Union[str, Path]]=None) -> List[forge.RoleRule]` — L50 — Legge `<folder>/<name>.json` (default `rules/` del repo) e ritorna le
- `rules_from_dict(data: dict, source: str='<dict>') -> List[forge.RoleRule]` — L61 — Come `load_rules`, da un dict già letto.
- `_expand(entry: dict) -> List[forge.RoleRule]` — L73 — Una voce del JSON → una o più RoleRule (una per elemento di una lista).

#### `snapdraw/tag.py` — 44 lines

_snapdraw/tag.py_

- `tag_layout(doc, layout: FrameLayout) -> int` — L28 — Setta `edge.role` sugli Edge di cornice e cartiglio in `layout`.

#### `snapdraw/titleblock.py` — 339 lines

_snapdraw/titleblock.py_

- `find_titleblock(doc, frame: Optional[FrameInfo]=None) -> Optional[TitleBlock]` — L45 — Delimita il cartiglio nella geometria grezza di `doc`.
- `extend_titleblock(title_block: TitleBlock, doc, frame: Optional[FrameInfo]=None) -> TitleBlock` — L110 — Estende `title_block` alle tabelle attaccate: ogni linea orizzontale o
- `_edges_inside(bbox: Tuple[float, float, float, float], doc) -> list` — L177 — Tutti gli Edge di `doc.edges` (qualunque tipo di segmento — griglia,
- `_is_genuine_grid(row_ys: List[float], col_xs: List[float], rect: CoveredRectangle) -> bool` — L191 — True se almeno un asse è suddiviso in segmenti **comparabili**, non
- `_confidence(row_ys: List[float], col_xs: List[float], density: float, rect: CoveredRectangle, frame: Optional[FrameInfo]) -> float` — L211 — Confidenza grezza, stesso spirito additivo di `frame._confidence` — da
- `_build_cells(rect: CoveredRectangle, row_ys: List[float], col_xs: List[float], doc) -> List[Cell]` — L231 — I divisori tagliano `rect` in celle; ogni cella raccoglie il testo delle
- `read_titleblock(layout) -> dict` — L293 — Legge le celle del cartiglio → dict dei campi
- `_split_labeled_text(text: str, cell_index: int) -> Dict[str, dict]` — L327 — Ogni etichetta trovata in `text` → valore = il testo fino alla prossima etichetta (o fine stringa).

#### `snapdraw/views.py` — 161 lines

_snapdraw/views.py_

- `sheet_islands(doc: forge.ForgeDocument) -> forge.ForgeResult` — L43 — Le isole di un foglio: `forge.island` con il `max_gap` scelto da
- `classify_view(cluster, angle_tolerance: float=AXIS_ANGLE_TOLERANCE) -> str` — L52 — "orthographic" se almeno metà della lunghezza dei LineSeg (contorno e
- `projection_mates(views: List[View], tolerance: float=MATE_TOLERANCE) -> Dict[int, Tuple[List[int], List[int]]]` — L65 — Per ogni vista ortogonale: (height_mates, width_mates). Stessa
- `principal_view(views: List[View]) -> Tuple[Optional[int], List[str]]` — L82 — La vista con compagni in tutte e due le direzioni (la più grande, se più
- `view_depth(views: List[View], principal: Optional[int], tolerance: float=MATE_TOLERANCE) -> Tuple[Optional[float], List[str]]` — L101 — La terza dimensione della vista principale: la larghezza dei compagni in
- `read_views(result, tolerance: float=MATE_TOLERANCE) -> ViewLayout` — L120 — Ricetta: classifica ogni cluster, trova i compagni di proiezione, la
- `_reference(views: List[View]) -> Optional[View]` — L152 — La vista che fa da metro per i simboli: la principale, o la più grande.
- `_area(view: View) -> float` — L160

## Internal dependencies

Which `snapdraw` modules each module imports — "what works with what". Modules with no internal import are omitted.

| module | imports |
|---|---|
| `snapdraw/__init__.py` | `snapdraw.features` · `snapdraw.frame` · `snapdraw.generate` · `snapdraw.model` · `snapdraw.recipe` · `snapdraw.render` · `snapdraw.roles` · `snapdraw.rules` · `snapdraw.tag` · `snapdraw.titleblock` · `snapdraw.views` |
| `snapdraw/features.py` | `snapdraw.model` · `snapdraw.roles` · `snapdraw.views` |
| `snapdraw/frame.py` | `snapdraw.geometry` · `snapdraw.model` |
| `snapdraw/generate.py` | `snapdraw.geometry` · `snapdraw.model` · `snapdraw.roles` |
| `snapdraw/recipe.py` | `snapdraw.frame` · `snapdraw.model` · `snapdraw.titleblock` |
| `snapdraw/render.py` | `snapdraw.model` · `snapdraw.roles` |
| `snapdraw/tag.py` | `snapdraw.model` · `snapdraw.roles` |
| `snapdraw/titleblock.py` | `snapdraw.geometry` · `snapdraw.model` |
| `snapdraw/views.py` | `snapdraw.model` |

