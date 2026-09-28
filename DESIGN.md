# framer — design

Origine: `FRAMER.md` nel repo di forge (la specifica dalla quale nasce questo
modulo). Qui la versione operativa, allineata al codice.

## Dove gira nella pipeline

framer lavora sulla geometria **grezza** di `doc` — le primitive che forge ha
già parsato e normalizzato (`forge.load_dxf`), ma **prima** di qualunque
lettura di forge (`heal` o `island`). framer interpreta, forge trasforma la
topologia: la lettura a valle è una scelta del chiamante, non un passo di
framer (MAP D13).

```
file CAD
   │
   ▼
forge.load_dxf(path, role_rules=framer.load_rules("generic"))
                            → ForgeDocument; le regole di rules/ assegnano già
                              i ruoli al caricamento (assi = construction, MAP D17)
   │
   ▼
framer.detect_frame(doc)    → FrameLayout: cornice + cartiglio (la ricetta)
   │
   ├──► framer.read_titleblock(l) → celle del cartiglio → metadati di disegno
   │
   ▼  (solo se servono i pezzi)
framer.tag_layout(doc, l)   → setta edge.role su doc.edges (frame / title_block)
   │
   ▼
forge.heal(doc) | forge.island(doc)
                            → cluster puliti: frame e title_block fuori dal grafo,
                              in trash_entities col loro ruolo, non cluster
```

`detect_frame` è una **ricetta** sopra passi pubblici, stesso schema di
`forge.heal` (forge D62): `find_frame(doc)` → `find_titleblock(doc,
frame=...)` → flag di incertezza. Chi vuole un'altra composizione (solo la
cornice, il cartiglio con una cornice già nota) chiama i passi a mano.

## I due ruoli

| ruolo | cos'è | forge lo conosce? |
|---|---|---|
| `frame` | il riquadro di formato ISO | no — slug di consumatore (forge D31 ha rimosso `ContourRole.FRAME`) |
| `title_block` | il cartiglio | no — slug di consumatore, forge lo conserva (D27) |

Nessuno dei due è strutturale: geometria non di taglio. `heal` li tiene fuori
dal grafo, finiscono in `trash_entities` col ruolo intatto, e l'output DXF li
scrive sul layer/colore registrati in `framer/roles.py` (`Frame`, `TitleBlock`,
nero) — non su un layer grigio generico (MAP D7).

## Algoritmo cornice (`frame.py`, portato e funzionante)

1. tra gli `Edge` con `segment` di tipo `LineSeg`, trova i **rettangoli chiusi**
   via `shapely.ops.polygonize` dell'unione nodata (gestisce con lo stesso
   passaggio il rettangolo disegnato come polilinea chiusa e quello fatto di 4
   LINE); tiene i poligoni che coincidono col proprio envelope (axis-aligned);
2. filtra quelli con **rapporto dei lati ≈ √2** (formati ISO), tolleranza ±5%;
3. per ogni candidato calcola il **contenimento**: frazione degli `Edge`
   restanti i cui endpoint stanno dentro la bbox (con un margine);
4. tieni i candidati con contenimento ≥ **80%**; tra questi prendi il **più
   grande** — quella è la cornice;
5. **conservativo**: se nessun candidato supera la soglia, `find_frame`
   ritorna `None`, `detect_frame()` mette `frame: uncertain` nei flag e `tag_layout`
   non marca niente. Meglio un cluster sporco che buttare via la geometria di
   un pezzo.

Il formato ISO (`A4`, `A3`, ...) è dedotto dalle dimensioni della bbox
assumendo mm — best effort, non blocca.

## Algoritmo cartiglio (`titleblock.py`, portato e funzionante, MAP D11)

Il cartiglio **non è per forza dentro una cornice**: il rilevamento è
indipendente. Segnali combinati (nessuno sufficiente da solo):

1. tra i rettangoli di bordo (`geometry.find_rectangles`, con un lato minimo
   **assoluto** in mm invece che una frazione del disegno — un cartiglio non
   scala con l'estensione totale come fa la cornice), tieni quelli con una
   **griglia interna genuina** (`geometry.grid_dividers` + `_is_genuine_grid`):
   linee che attraversano il rettangolo per intero, suddividendolo in segmenti
   comparabili — non un secondo bordo inset (quello produce anch'esso 2
   "divisori" per lato, ma il segmento centrale è quasi tutto il lato, non una
   cella: è la cornice a doppia squadratura di MAP D9, va escluso);
2. scarta le griglie con troppe **celle vuote** (`MIN_FILLED_CELL_FRACTION`):
   `find_rectangles` su un disegno con più linee parallele restituisce anche
   ogni sotto-rettangolo nidificato e ogni combinazione che arriva a toccare
   geometria vicina (la cornice, se il cartiglio le sta appena dentro) — un
   cartiglio vero ha (quasi) tutte le celle con del testo, anche solo un
   placeholder;
3. punteggio: densità di annotazioni per area rispetto alla media del disegno
   (`geometry.annotation_density_ratio`), bonus se dentro la bbox della
   cornice, bonus ulteriore se vicino al suo angolo in basso a destra;
4. fra i candidati sopra `CONFIDENCE_THRESHOLD`, tieni il **più grande** —
   stesso criterio di `find_frame`: è quello che racchiude l'intero
   cartiglio, non una sua riga o una sua colonna;
5. `extend_titleblock` (MAP D15): il rettangolo scelto è di rado tutto il
   cartiglio. Si estende a catena alle linee orizzontali e verticali che lo
   toccano (tabella revisioni sopra, blocchi di celle a fianco), solo dentro
   il cartiglio allargato del suo lato maggiore e mai sulle linee della
   cornice; poi si prende tutto quello che sta nell'area estesa (D12).

Un testo sul bordo di una cella conta come dentro (`TEXT_BORDER_TOL`,
0.5 mm): un MTEXT agganciato a sinistra ha il punto d'inserimento
esattamente sul bordo.

Se la cornice non è accettata ma un riquadro di bordo racchiude il cartiglio
(`frame.rejected_border`, un modello aziendale non ISO), `detect_frame` lo
dice nei flag: quel riquadro resta nel disegno e `island()` lo prenderebbe
come contorno esterno di tutte le viste.

Le celle risultanti raccolgono il testo delle annotazioni (`doc.annotations`)
che contengono, dall'alto in basso. `read_titleblock` cerca in ognuna un
piccolo vocabolario ISO 7200 generico per regex (`N. DISEGNO`/`DWG NO`,
`MATERIALE`/`MATERIAL`, `SCALA`/`SCALE`, ...) — mai nomenclatura di cliente,
quella resta nei `profiles/` privati (vedi "Cosa NON ci va"). Nessun match →
`None` + il nome del campo in `unresolved`, mai una supposizione.

Conservativo: nel dubbio non marca, `title_block: uncertain` nei flag. Soglie
(`CONFIDENCE_THRESHOLD`, `MIN_FILLED_CELL_FRACTION`, ...) grezze — non ancora
tarate su un disegno reale, vedi TODO.md.

## L'aggancio a forge (opzione B, chiusa in forge D30 + D31)

framer setta `edge.role` sugli `Edge` di `doc.edges` prima di `heal`. forge non
ha preso API nuove: ha consolidato il concetto "ruolo strutturale" in
`forge.is_structural_role` e reso l'aggancio un contratto.

- `heal._split_labeled` estrae dal grafo **ogni** edge con ruolo deciso e non
  strutturale (quindi `frame`, `title_block`, slug custom): non ci passano né
  per gap solving né per la ricerca loop;
- `detect()` non trasforma un ruolo che non conosce in una feature: lo lascia
  in `trash_entities`;
- l'output DXF scrive quella geometria nativa sul layer/colore che `framer`
  stesso registra in `roles.py` via `forge.register_role_style` — non su
  `Trash` insieme alla spazzatura vera (D31: `ContourRole.FRAME` rimosso da
  forge, i ruoli di consumatore vanno su un layer loro) e non lasciato al
  grigio generico di default (D47 di forge, "roles out of core": lo stesso
  meccanismo pubblico con cui forge registra il proprio vocabolario di
  `detect()` — vedi MAP D7).

Invariante: **framer non ragiona dentro forge.** Chiama `forge.load_dxf`, fa il
suo lavoro geometrico, restituisce dei ruoli. Se serve un cambiamento in forge è
solo per **accettare** i ruoli, mai per **decidere** cosa sia un cartiglio.

## Il verso "aggiungi" (`framer/generate.py`, MAP D8/D9)

Oltre a *rilevare* cornice e cartiglio, framer può *generarli* e aggiungerli a
un disegno che non li ha:

```python
doc = forge.load_dxf("pezzo_nudo.dxf")
framer.add_frame(doc)                                   # cornice ISO attorno alla geometria esistente
framer.add_title_block(doc, fields={"material": "S235JR"})  # cartiglio nel suo angolo
result = forge.heal(doc)
forge.to_dxf(result, doc).saveas("pezzo_framed.dxf")
```

`add_frame(doc)` non prende un formato in ingresso: calcola da solo il
formato ISO (A4..A0) e l'orientamento più piccoli che contengono la geometria
esistente con un margine, più lo spazio per il cartiglio — A3/A4 orizzontale/
verticale non sono 4 rami di codice, sono 4 casi dello stesso calcolo bbox
+ formato. `add_title_block(doc, fields=...)` ancora di default all'angolo
in basso a destra della bbox corrente di `doc` — se `add_frame` è già stato
chiamato, quella bbox è la cornice appena creata, e il cartiglio finisce nel
suo angolo senza altro codice di raccordo.

`fields` sono dati del chiamante (numero disegno, materiale, spessore, ...) —
**mai** salvati nel repo, stesso principio di `data_injector`/`profiles/`
sotto "Cosa NON ci va". Entrambe le funzioni sono puramente forge-native
(`forge.load_geometry` + `forge.Note`, zero ezdxf): `heal`/`detect`/`to_dxf`
trattano questa geometria esattamente come quella rilevata da
`find_frame`/`find_titleblock`.

L'aspetto è preso da due riferimenti reali in `templates/` (locali, mai
committati — MAP D9), non inventato a occhio come nel primo taglio:

- la cornice ha un **doppio bordo**: quello esterno (il perimetro del
  foglio) e uno interno inset di 5 mm, collegati da una **lineetta di
  centratura** al centro di ogni lato — il segno ISO 5457 per la
  riproduzione dei disegni, non solo estetica;
- in più, la **griglia di riferimento** ISO 5457 (MAP D10): ogni lato è
  diviso in zone (25–75 mm ciascuna, target 50 mm) con una lineetta per
  confine — un formato più grande ha più zone, quindi più lineette, non lo
  stesso numero fisso di un formato piccolo;
- il cartiglio ha, per ogni campo, un'**etichetta piccola sopra** (1.8 mm) e
  un **valore più grande sotto** (3 mm), impilati in una sola colonna di
  righe alte 10 mm — non più due righe di testo grosso affiancate dentro una
  cella larga, che sbordava e si accavallava.

Il logo/immagine resta fuori: forge non ha un concetto di immagine nel suo
modello neutro (niente entità `IMAGE`), andrebbe inserito in un secondo giro
direttamente sul `Drawing` ezdxf restituito da `to_dxf()` — domanda aperta,
non implementato.

## Cosa NON ci va

- decisioni dentro forge — forge non sa cosa sia un cartiglio, e resta così;
- nomenclatura di reparto o logica di un singolo cliente — sta nei `profiles/`
  dell'interprete, mai qui e mai su GitHub;
- guessing non etichettato: ogni campo letto dal cartiglio porta `source` +
  `confidence`, "non lo so" è `None` + `unresolved`, mai una supposizione;
- discretizzazione: la geometria di cornice è marcata, non ridisegnata — forge
  la riscrive con le primitive native.

## Decisioni (erano domande aperte, chiuse in MAP D4)

- **framer è un progetto a sé che l'interprete importa** come libreria, come
  `unfold` — non una cartella dentro l'interprete. L'interprete è solo un
  orchestratore, non fa lavoro geometrico.
- **La lettura dei campi del cartiglio (`read_titleblock`) sta in framer.**
  framer delimita il cartiglio, ne legge le celle e ne estrae i valori con
  `source` + `confidence`. L'interprete riceve il risultato e lo incrocia con
  callout ed ERP.
