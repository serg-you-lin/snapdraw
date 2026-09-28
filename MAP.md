# MAP — log delle decisioni di framer

Registro cronologico. Una decisione chiusa non si ri-decide: se cambia idea, è
una nuova voce che supera la precedente.

---

## DECISIONI CHIUSE

### D1 — framer è un repo a sé, consumatore di forge  ✅

Nasce come modulo scorporato dalla specifica `FRAMER.md` (repo forge). Repo
separato (non cartella dentro l'interprete, che ancora non esiste), sibling di
`forge`, package `framer`. Quando l'interprete esisterà lo importerà come
libreria. Precedente: `unfold`.

forge è dipendenza **locale non pubblicata**: `pip install -e ../forge`,
non elencata in `pyproject.toml` (solo `shapely`). Stesso schema di `unfold`.

### D2 — Aggancio a forge: opzione B  ✅

framer setta `edge.role` sugli `Edge` di `doc.edges` prima di `forge.heal`. La
scelta è stata chiusa in **forge D30**: nessuna API nuova su forge, solo
consolidamento —

- `forge.is_structural_role` / `STRUCTURAL_ROLES` unico punto di verità;
- `heal._split_labeled` estrae dal grafo ogni ruolo deciso e non strutturale
  (`frame`, `title_block`, slug custom), non più solo engrave/marking;
- `forge.detect` non trasforma un ruolo che non conosce in una feature: lo
  lascia in `trash_entities` (prima lo perdeva);
- `forge.normalize_role` / `forge.is_structural_role` pubbliche.

Scartate: **A** (framer rimuove gli edge e li riemette a valle — scarica su
framer il problema "chi ridisegna la cornice"); **C** (hook `role_resolver` in
`load_dxf`/`heal` — si valuta quando anche l'unfolder lo chiede; D30 lo rende
banale da aggiungere).

### D3 — `detect_frame` portato da forge `ccbb34f^`  ✅

L'algoritmo del vecchio `core/classification/frame_detector.py` di forge
(rimosso in forge D24 perché girava prima di `heal` — cioè roba del consumatore)
riscritto sugli `Edge` / `LineSeg` di forge invece che su `RawSegment` propri.
Niente `print("DEBUG")`. Rettangoli via `shapely.ops.polygonize` invece della
ricerca combinatoria a quadruple. Stesse soglie: ratio √2 ±5%, contenimento
≥ 80%, conservativo.

`detect_titleblock` e `read_titleblock` restano **stub** con firma definitiva.

### D4 — framer è importato dall'interprete; la lettura del cartiglio sta qui  ✅

Chiuse le due domande aperte di FRAMER.md:

- **framer è un progetto a sé che l'interprete importa** come libreria, come
  `unfold`. Non è una cartella dentro l'interprete. L'interprete è **solo un
  orchestratore**: non fa lavoro geometrico.
- **La lettura dei campi del cartiglio (`read_titleblock`) sta in framer**, non
  in uno step dell'interprete. framer delimita il cartiglio, ne legge le celle e
  ne estrae i valori (con `source` + `confidence`). L'interprete riceve il
  risultato e lo incrocia con callout e ERP, non legge geometria.

### D5 — Rilevamento rettangoli: dai lati, non da `polygonize`  ✅

Il primo `find_rectangles` usava `shapely.ops.polygonize`. Su un disegno reale
(`42D025Z00I`) non funziona: il bordo cornice è coperto di tacche di
graduazione zona, `polygonize` restituisce un poligono da 45 punti con 13 buchi
invece di un rettangolo, e prende solo il riquadro interno. Il riquadro esterno
sopravvive → `heal` lo classifica come `outer` e si mangia tutto.

Riscritto: si cercano i **lati** direttamente — linee axis-aligned lunghe
almeno il 30% della dimensione del disegno, che coprono ≥ 85% dei quattro lati
di un rettangolo. Una cornice a doppio bordo dà due rettangoli. `detect_frame`
marca gli `Edge` di **tutti** i rettangoli che passano ISO + contenimento, non
solo il più grande. `iso_format` confronta anche contro il foglio meno un
rientro tipico di squadratura (5/10/20/25 mm): un A2 squadrato a 10 mm misura
574 × 400.

Nota aperta: su `42D025Z00I` la cornice ora esce (`cluster 1 → 4`), ma i pezzi
veri non si chiudono in `heal` (tanti archi, linee di costruzione, 97 edge non
di contorno) — è roba di forge/heal, non di framer.

### D6 — `frame` è uscito da forge (forge D31)  ✅

Aprendo i DXF prodotti, la geometria di cornice usciva **sul layer `Trash`**
insieme alla spazzatura vera: `forge.io.dxf._write_trash` scriveva tutto su
`TRASH_LAYER` ignorando il ruolo. Federico: tutto ciò che è framer, ruolo
compreso e anche nell'adapter, deve uscire da forge.

Fatto in **forge D31**: `ContourRole.FRAME` rimosso, `frame` è uno slug di
consumatore come `title_block`. `_write_trash` instrada per ruolo — slug di
consumatore → un layer col nome dello slug, colore grigio; `unknown` → `Trash`.
`framer.tag_layout` non cambia: `forge.normalize_role("frame")` ora ritorna la
stringa `"frame"` invece della costante. Sul disegno reale: `frame` esce su un
layer `frame` (11 entità), la spazzatura su `Trash` (388).

### D7 — `frame`/`title_block` registrano il proprio stile in `framer/roles.py` (forge D47)  ✅

forge D47 ("roles out of core") ha spostato anche `hole`/`bending`/`engrave`
fuori dal motore: `tools/manufacturing_role.py` costruisce quel vocabolario e
registra colore/layer con `forge.register_role_style` allo stesso modo
pubblico con cui lo farebbe un consumatore esterno — nessuna via privilegiata.
Prima framer non aveva un equivalente: `FRAME_ROLE`/`TITLE_BLOCK_ROLE` erano
inline in `tag.py`, senza stile registrato, e chi voleva un colore diverso da
grigio lo passava a mano a `to_dxf(..., role_styles={...})` in ogni script
(`scripts/00_detection.py`, `scripts/01_export.py` lo facevano con due valori
diversi — incoerente, e da ripetere ovunque).

Fatto: nuovo modulo `framer/roles.py`, stesso schema di
`manufacturing_role.py` — costanti `FRAME`/`TITLE_BLOCK` via
`forge.normalize_role`, `register_defaults()` che chiama
`forge.register_role_style` per entrambe (nero, layer `Frame`/`TitleBlock`),
eseguita all'import del modulo. `tag.py` importa le costanti da qui invece di
definirle. Nessun `is_structural` qui: cornice/cartiglio sono decorazione, non
topologia di pezzo — il default di `heal()` (nessun predicato) già li tiene
fuori dal grafo, a differenza di `hole` in forge che invece È strutturale.
Gli script non passano più `role_styles` a mano: colore/layer arrivano gratis
da `import framer`.

### D8 — Generazione cartiglio+cornice: `framer/generate.py`, un template condiviso  ✅

Il verso "aggiungi" era solo una nota futura in `forge/FRAMER.md` e in
`TODO.md`. Nessun cartiglio reale è stato trovato tra i repo sibling
(`DxfTagCreator`, `dxf_archive`, `bendly` verificati — niente su disco): il
design qui sotto è "inventato da noi", deliberatamente semplice.

Decisioni prese con Federico:
- **solo vettoriale per questo giro** — rettangolo + griglia + testo, tutto
  forge-nativo (`forge.load_geometry` + `forge.Note`). Il logo/immagine resta
  fuori: forge non ha un concetto di immagine nel suo modello neutro, andrebbe
  aggiunto in un secondo giro direttamente sul `Drawing` ezdxf di `to_dxf()`;
- **un solo template di cartiglio**, condiviso da A3/A4 orizzontale/
  verticale — la sua geometria non cambia con formato/orientamento, solo
  *dove* viene ancorato sul foglio. Di conseguenza `add_title_block` non ha
  un parametro `fmt`/`orientation`: l'ancoraggio di default è l'angolo in
  basso a destra della bbox corrente di `doc`, che è già agnostico rispetto a
  quei 4 casi — verificati con 4 fixture di test (`tests/test_generate.py`),
  non con 4 rami di codice;
- **`add_frame(doc)` sceglie da solo il formato ISO** (A4..A0, in entrambi gli
  orientamenti) più piccolo che contiene la geometria esistente più un
  margine più lo spazio per il cartiglio — niente formato passato a mano, e
  `ValueError` se nemmeno A0 basta (conservativo, non si inventa una
  dimensione).

Bug preso e corretto durante l'implementazione: `add_title_block` calcolava
l'anchor di default con `_, _, max_x, min_y = doc_bbox` — uno spacchettamento
che, dato `_doc_bbox() -> (min_x, min_y, max_x, max_y)`, lega `min_y` al
valore vero di `max_y`. Il cartiglio finiva quindi sopra la geometria invece
che sotto, e il controllo di contenimento lo intercettava con un
`ValueError` invece di piazzarlo male in silenzio — il fail-fast conservativo
del modulo ha funzionato come doveva, l'ha solo reso visibile subito.

Provato su fixture reali: 10 disegni pezzo-nudo in
`tests/examples/to_add_frame/` (nome file
`{drawing_number}_{position}_{material}_SP{spessore}_Q{quantità}`, es.
`piastra_02.dxf`), da 20×10 mm a 628×528 mm — tutti e 10
passano (`scripts/02_batch_frame.py`, mai i file originali). Il parsing del
nome file **sta nello script**, non in `framer/`: è nomenclatura di questa
cartella/cliente (DESIGN.md, "Cosa NON ci va" — mai nel modulo pubblico).

Restano aperti: generazione della sola cornice quando basta quella (oggi
`add_frame` presuppone sempre spazio per un cartiglio); logo/immagine.

### D9 — Cornice e cartiglio ridisegnati su due riferimenti reali in `templates/`  ✅

Il primo taglio di D8 era troppo "inventato": celle larghe affiancate con
etichetta+valore su due righe della stessa altezza dentro una cella quadrata
— a schermo, testo enorme che sborda e si accavalla, niente doppio bordo.
Federico ha messo due file in `templates/` (mai committati — `*.dxf` resta
ignorato ovunque tranne `tests/examples/`, quindi anche il file scaricato da
una libreria online resta locale, nessun problema di licenza): uno fatto a
mano da lui partendo da un nostro output, uno scaricato (blocco
`TB_ISO_A3_L_STANDARD`, un cartiglio ISO professionale con circa 15 campi).

Presi a riferimento, non copiati 1:1 — i campi restano i 5 di D8, non si
reinventano:

- **doppio bordo + lineetta di centratura**: dal file fatto a mano di
  Federico — bordo esterno (il perimetro del foglio) e uno interno inset di
  5&nbsp;mm (`_BORDER_GAP`), collegati da una lineetta al centro di ogni
  lato. È il segno di centratura ISO 5457 per la riproduzione dei disegni,
  non solo estetica — `add_frame` ora disegna sempre questa coppia
  (`_frame_entities`), non un rettangolo solo;
- **etichetta piccola sopra, valore più grande sotto**: dal cartiglio
  scaricato — lì ogni campo ha una `TEXT` di etichetta ad altezza 1.8 mm
  seguita da un `ATTDEF` di valore ad altezza 3–6 mm, impilati, non
  affiancati sulla stessa riga. Adottato lo stesso schema (`_LABEL_HEIGHT`
  1.8, `_VALUE_HEIGHT` 3.0) invece della singola stringa
  "ETICHETTA: valore" di prima;
- righe passate da 5 celle larghe 36 mm/alte 30 mm a 5 righe piena larghezza
  (90 mm) alte 10 mm ciascuna — il cartiglio scaricato impacchetta ~15 campi
  in una griglia 2D (180×56 mm) perché ne ha bisogno; i nostri 5 campi non
  richiedono quella complessità, restano un'unica colonna di righe.

Non toccato: il logo (fuori scope, D8) e la griglia 2D del cartiglio
scaricato (i suoi campi extra — OWNER/APPROVED/PROJECTION/SHEET OF/... — non
sono nei 5 che usiamo, "non reinventiamoli" vale anche qui).

### D10 — Griglia di riferimento ISO 5457: più lineette sui formati più grandi  ✅

Federico, guardando l'A0 generato per `piastra_01` (627.8×527.8 mm — sceglie
A0, non un formato piccolo): un formato più grande deve avere **più**
lineette sul bordo, non lo stesso numero della cornice piccola — è la
griglia di riferimento ISO 5457 (le zone A/B/C.../1/2/3... usate per
localizzare un dettaglio), distinta dalla lineetta di centratura di D9 (che
resta unica, sempre al centro di ogni lato, per la riproduzione/microfilm —
non fa parte della griglia di zone).

Fatto: `_zone_count(length)` sceglie il numero di zone su un lato in modo che
la lunghezza di zona resti nell'intervallo ISO 5457 (25–75 mm, target
indicativo 50 mm — non ho una tabella ufficiale per formato memorizzata con
certezza, quindi il criterio è dedotto dalla lunghezza reale del lato, non
una tabella A0→N/A4→M copiata a memoria). `_frame_entities` aggiunge una
lineetta per ogni confine di zona su ogni lato (bordo esterno → bordo
interno, stessa lunghezza `_BORDER_GAP` della centratura), saltando il
confine che coincide col centro esatto del lato per non duplicare la
lineetta di centratura di D9. Risultato su fixture reali: A5 (1412DC326-1A)
→ 20 edge di cornice, A0 (piastra_01) → 88 — la densità segue la
dimensione, non è un numero fisso.

### D11 — `detect_titleblock`/`read_titleblock` portati da stub a funzionanti  ✅

Ripreso da `ROADMAP.md`: il cartiglio è il pezzo di framer già maturo per
essere costruito (a differenza del raggruppamento viste, ancora rimandato).
Bootstrap senza aspettare fixture DXF reali (non ancora raccolte, TODO.md):
round-trip su `generate.py` — genera un cartiglio con `add_title_block`,
verifica che `detect_titleblock` lo ritrovi. Le `forge.Note` che
`add_title_block` scrive sono lo stesso tipo di annotazione di un cartiglio
vero, quindi il round-trip esercita davvero la macchina dei segnali, non un
mock.

`geometry.py`: due meccanismi nuovi, entrambi generici (non sanno cosa sia un
cartiglio, solo geometria) —
- `find_rectangles` accetta ora `min_side_length` (mm, assoluto) oltre a
  `min_side_fraction`: un cartiglio non scala con l'estensione del disegno
  come fa la cornice, la frazione userebbe una soglia assurda su un disegno
  grande;
- `grid_dividers(rect, doc)`: linee interne che attraversano il rettangolo
  per intero — il segnale forte del cartiglio;
- `annotation_density_ratio(rect, doc)`: quante volte più annotazioni per
  area rispetto alla densità media del disegno.

`titleblock.py`: il primo giro (naive) prendeva "ha una griglia interna, punteggio
più alto" e falliva subito sul round-trip — un secondo bordo inset (la
cornice a doppia squadratura di D9) supera il filtro perché produce anch'esso
2 "divisori" per lato. Corretto con due filtri, non uno:
- `_is_genuine_grid`: i segmenti fra i divisori devono essere **comparabili**
  (nessuno domina, soglia `MAX_DOMINANT_SEGMENT_FRACTION` 0.6) — un secondo
  bordo inset ha un segmento centrale enorme fra due gap minuscoli, non passa;
- `MIN_FILLED_CELL_FRACTION` (0.8): scarta candidati "gonfiati" da linee
  vicine (la griglia di riferimento della cornice, D10, tocca esattamente
  l'angolo dove il cartiglio di default si ancora) che aggiungono righe di
  griglia vuote — un cartiglio vero ha (quasi) tutte le celle piene, anche
  solo di un placeholder.

Fra i candidati che passano entrambi i filtri e superano `CONFIDENCE_THRESHOLD`
(0.6, punteggio additivo come `frame._confidence`), tiene **il più grande** —
stesso criterio di `detect_frame`: `find_rectangles` su una griglia restituisce
anche ogni sotto-rettangolo nidificato (una riga sola, due righe, ...), il più
grande è quello che racchiude l'intero cartiglio.

`read_titleblock`: deciso con Federico — **vocabolario ISO 7200 generico per
regex**, non posizionale (un template noto avrebbe funzionato solo sui
cartigli generati da noi stessi) e non nomenclatura di cliente (quella resta
nei `profiles/` privati, DESIGN.md "Cosa NON ci va" — i termini ISO 7200 sono
standard, non privati). Per ogni campo, cerca il suo pattern nel testo di ogni
cella; il resto del testo, ripulito dall'etichetta, è il valore. Nessun match
→ `None` + il nome in `unresolved`.

Soglie non tarate su un disegno reale (non ancora raccolto, TODO.md) — sono le
prime che fanno passare il round-trip e i casi conservativi sintetici
(`tests/test_titleblock.py`), da rivedere quando arriva una fixture vera.

### D12 — Il cartiglio si prende tutto quello che gli sta dentro, non solo il bordo  ✅

Federico, guardando il report visivo sui 22 disegni reali: `TitleBlock.edges`
portava solo il bordo trovato da `find_rectangles` — i divisori di griglia,
i simboli e i loghi che stanno geometricamente dentro il cartiglio restavano
senza ruolo, e `heal` li smistava a caso: in `trash_entities` come
`unknown`, o peggio in un cluster spurio a sé (il logo di
`B1250136`, D11 appunti). Non è un difetto della griglia o della soglia, è
che nessuno li marcava affatto.

Fatto: nuova `_edges_inside(bbox, doc)` in `titleblock.py` — dopo aver
scelto il cartiglio vincente, prende **tutti** gli `Edge` di `doc.edges`
(qualunque tipo di segmento, non solo `LineSeg`) i cui endpoint stanno dentro
la sua bbox, non solo quelli allineati al bordo. `detect_titleblock` ritorna
questo insieme invece di `rect.edges`; `tag_layout` (invariato) li marca
tutti `role="title_block"`. Verificato su `B1250136`: i cluster scendono da
63 a 59 (il logo e pezzi di griglia ora vanno sul layer cartiglio, non più
dispersi). Test aggiunti: un simbolo isolato piazzato dentro un cartiglio
generato viene marcato e, dopo `heal`, finisce in trash con
`role="title_block"` invece di formare un cluster a sé
(`TestTitleblockAssorbeInteriore`).

Nota operativa per il futuro: rilanciare il rilevamento dopo un cambio come
questo può **spostare gli indici dei cluster** su disegni dove il cartiglio
già esisteva (meno cluster restituiti da `heal` = indici diversi a valle) —
successo davvero su `tavola_09.dxf` mentre un'etichettatura reale (framer
`lab/`) era in corso, richiesta una migrazione manuale dei documenti nel
database dell'artifact per bbox invece che per indice. Prima di rilanciare
`survey.py` su un cambio che tocca `detect`/`heal`, avvisare.

### D13 — `detect_frame` è una ricetta, e non presuppone `heal`  ✅

Segue forge D62 (`heal()` è una ricetta sopra passi pubblici, `HealStep` non
c'è più) e D58 (`heal` e `island` sono due letture, nessuna sta "sopra"
l'altra). Federico: non va che il rilevamento di framer si porti dietro
sempre un `heal` a valle, e il punto d'ingresso deve chiamarsi
`detect_frame`, non `detect`.

- **`framer.detect` → `framer.detect_frame`**, in `framer/recipe.py`
  (`detect.py` rimosso, clean break): solo la composizione di default,
  stesso schema di `forge/core/heal.py`.
- **I passi sono pubblici** e rinominati per non collidere con la ricetta:
  `frame.detect_frame` → `find_frame`, `titleblock.detect_titleblock` →
  `find_titleblock`, entrambi in `framer.__all__`. `tag_layout` resta un
  passo a sé. Chi vuole un'altra composizione li chiama a mano.
- **Nessuna lettura di forge presupposta**: `detect_frame` non muta `doc`;
  marcare (`tag_layout`) e poi leggere con `heal` o `island` è scelta del
  chiamante — il recipe consumer delle note di forge per i disegni di viste
  usa proprio `island()`. `scripts/00_detection.py` si ferma alla ricetta +
  `read_titleblock`; la scrittura del DXF (che richiede un `ForgeResult`,
  quindi una lettura) resta in `01_export.py`.
- Nessun passo di forge nella ricetta per ora: i passi di normalizzazione
  di `heal` (`merge_collinear_overlaps`, `weld_degenerate_linesegs`)
  restituiscono Edge **nuovi** dove fondono, e `tag_layout` marca per
  identità gli Edge di `doc.edges` — usarli romperebbe l'aggancio. Né
  `split_labeled`: un cartiglio generato da `add_title_block` è già
  `role="title_block"` e deve restare visibile a `find_titleblock` (il test
  `TestTitleblockAssorbeInteriore` ci conta).

Comportamento invariato: solo nomi e composizione, la suite passa identica.

### D14 — Dopo la cornice si legge per isole: `island()`, non `heal()`  ✅

Federico: nelle messe in tavola si cercano le isole (una per vista), quindi
dopo `detect_frame` + `tag_layout` la lettura di forge è `forge.island()`.
`heal()` resta la lettura dei file di taglio piatti (e del verso "aggiungi",
`add_frame` su un pezzo nudo, non toccato qui). `01_export.py` e
`04_batch_remove_frame.py` passano a `island()`.

Conseguenza: le cose che rompono le isole su un foglio di viste sono lavoro
di framer, da marcare per ruolo **prima** di `island()` — i cerchi di
ingrandimento (un cerchio che taglia una vista la fonde con quello che ha
intorno) e le linee di interruzione delle viste interrotte. Rilevatori non
ancora scritti: prima si verificano a occhio sui `complete_drawings`.

### D15 — Il cartiglio si estende alle tabelle attaccate; riquadro rifiutato segnalato  ✅

Dall'etichettatura dei 34 `complete_drawings` (pagina `lab/export_circles.py`):
in 16 disegni su 19 con cornice un pezzo di cartiglio restava un'isola per
`forge.island()`. `find_titleblock` sceglie un rettangolo coi quattro lati
coperti; la tabella revisioni sopra (più stretta) o un blocco di celle a
fianco (più alto) ne restava fuori, e la sua riga chiusa diventava un'isola.

- **`extend_titleblock(title_block, doc, frame)`**, passo pubblico chiamato
  dalla ricetta: a catena, ogni linea orizzontale/verticale che tocca il
  cartiglio entro 1 mm entra, poi tutto quello che sta nell'area estesa
  (stesso principio di D12). `cells` resta quello del rettangolo di
  partenza, `bbox` diventa l'area estesa.
- **Limite**: una linea entra solo se sta tutta nel cartiglio allargato del
  suo lato maggiore, e mai una linea di cornice. Senza limite, su
  `B1250136` la catena risaliva i lati del riquadro che condivide il bordo
  col cartiglio.
- **Risultato**: in tutti e 16 i disegni sparisce esattamente l'isola
  segnata da Federico come pezzo di cartiglio, nessuna vista persa. Restano
  due simbolini (7 e 47 mm², `tavola_10`, `tavola_02`) appena fuori dall'area
  estesa: stesso caso del simbolo di disegno di `tavola_13`, aperto.
- **`sviluppo_01`**: cartiglio perso perché i testi, MTEXT agganciati
  a sinistra, hanno il punto d'inserimento esattamente sul bordo e un
  arrotondamento li buttava fuori dalle celle (e dalla densità). Ora
  `TEXT_BORDER_TOL` = 0.5 mm in `_build_cells` e `annotation_density_ratio`.
  Isole da 3 a 2 (i due pezzi).
- **Riquadro rifiutato** (`frame.rejected_border`): su `B1250136` il riquadro
  non ISO (900×1453, rapporto 1.61, contenimento 54%) è giustamente scartato
  come cornice, ma non diventava un'isola solo perché la marcatura del
  cartiglio ne apriva il lato inferiore — risultato giusto per caso. Senza
  marcatura è un'isola unica con 288 interni. Ora `detect_frame` lo dice nei
  flag ("frame: rejected border (...) encloses the title block, left in the
  drawing"); lo controlla sul cartiglio *prima* dell'estensione. Non si
  segnala senza cartiglio dentro: il rettangolo di un pezzo nudo non è un
  riquadro di impaginazione.

Suite: 35 passed (6 test nuovi).

### D16 — Tratto e punto = linea di costruzione, fuori dalle isole  ✅

Segue forge D63 (`role_rules`: forge dà il meccanismo, il vocabolario è del
chiamante). Federico: "regole di massima" plausibili per il disegno tecnico,
non regole tarate perché tutti i disegni di prova passino.

- **Regola** (ISO 128), sul pattern del tipo di linea, non sul nome:
  tratto e punto (più lunghezze di tratto: `CENTER`, `CENTERX2`, `PHANTOM`,
  `ASSI1/2`, `GEN7A`, `AM_ISO08W050`) → `construction`; solo tratteggio
  (`HIDDEN`, `DOT`) → non si tocca, sono spigoli nascosti o pieghe.
- **Passi**: `is_dash_dot(style)`, `find_construction_lines(doc)` (puro,
  solo Edge `unknown`), `tag_construction(edges)`; ruolo `construction`
  registrato in `roles.py` (layer `Construction`). Da chiamare dopo
  `tag_layout`, prima di `forge.island()`. Non è una `RoleRule` di forge:
  `RoleRule(dashed=True)` non distingue tratto e punto da tratteggio.
- **Scartato**: `dashed=True` → costruzione. Toglie anche gli `HIDDEN`, e le
  viste laterali di lamiera piegata (`tavola_04`, `tavola_04_1`) perdono metà
  contorno: la piega vista di fianco è disegnata nascosta.
- **Scartato**: una protezione "un tratto e punto che passa per due estremi
  liberi chiude un contorno, resta geometria", cucita su `tavola_11`. Era
  overfitting, e leggeva male il disegno: quella linea non è un lato del
  pezzo, delimita un ingrandimento parziale ("la vista continua").
- **Effetti** sui 34 `complete_drawings`: `tavola_03` ritrova la vista in
  pianta che mancava (non era forge: gli assi la collegavano alle quote);
  `assieme_020` non chiude più la vista frontale sulle linee dell'angolo dei
  fori; le circonferenze di foratura di `tavola_06` escono. `tavola_11` si
  spezza (4 → 10 isole) per via dell'ingrandimento parziale: caso aperto,
  va con viste interrotte/parziali. Compaiono isoline di 1–6 mm² (simboli
  che gli assi tenevano attaccati alle viste): stesso caso aperto dei
  simboli di disegno.
- Cerchi candidati ingrandimento (`lab/export_circles.py`): da ~72 a 17, i
  fori non risultano più "tagliati" dai propri assi. I 3 ingrandimenti veri
  restano candidati.

Suite: 42 passed (7 in `test_construction.py`).

### D17 — Regole di ruolo in file JSON: generiche nel repo, di studio fuori; D16 diventa una regola  ✅

Segue forge D64 (`EdgeStyle.dash_kind`, `RoleRule(dash=...)`): il tratto e
punto è ora un fatto del modello di forge, e la regola di D16 si scrive come
qualunque `RoleRule`. Federico: regole generiche estendibili da uno studio o
un cliente, sul modello delle calibrazioni di bendly.

- **`rules/<nome>.json`** → `framer.load_rules(name, folder=None)` →
  `list[forge.RoleRule]`, da passare a `forge.load_dxf(role_rules=...)`.
  Ogni voce ha i campi di `RoleRule`; `name`/`name_contains` accettano una
  lista (una regola per voce, in ordine); un campo sconosciuto alza.
- **Nel repo solo `rules/generic.json`**; `rules/studio_*.json` e
  `rules/cliente_*.json` in `.gitignore` (come bendly `calibrations/`).
- **Estendere = comporre nello script, non ereditare** (bendly D5, "flatten
  it"): `load_rules("studio_x") + load_rules("generic")`. Ogni file si legge
  da solo; lo studio va prima perché vince la prima regola che corrisponde;
  una correzione al generico arriva a tutti. Scartato: file di studio che
  copiano il generico (le correzioni non si propagano) e un campo
  `"extends"` (ereditarietà nascosta, quella che bendly D5 ha tolto).
- **Clean break**: `construction.py` (`is_dash_dot`,
  `find_construction_lines`, `tag_construction`) rimosso; il ruolo
  `construction` si assegna al caricamento con `{"role": "construction",
  "dash": "chain"}`. Stesse isole e stessi cerchi candidati di D16 su tutti i
  34 `complete_drawings`: `dash_kind == "chain"` di forge coincide con il
  vecchio `is_dash_dot`.
- **Nomi di layer fuori dal generico.** Provato `name_contains` su
  axis/axes/assi/center/centre/centro: su `tavola_01` il layer
  `ASSI` contiene il pezzo intero (874 linee: fori, spline,
  spigoli nascosti), non gli assi — probabilmente un nome di layer di
  default del CAD d'origine. Il nome del layer è convenzione di chi disegna:
  va nel file di uno studio che la conosce (es. `Centro (ISO)` di `Leva
  INOX`), non nelle regole per tutti. Stem/matching più furbo sui nomi:
  rimandato finché un file di studio non ne ha bisogno.

Suite: 40 passed (`test_rules.py` sostituisce `test_construction.py`).

### D18 — Le viste del foglio: `read_views`, conti sulle primitive, niente immagini  ✅

Dopo `island()` ogni isola è un cluster, ma nessuno dice quale sia la vista
del pezzo: un'assonometria, un logo e una vista vera sono tutti cluster
uguali. Una persona lo capisce guardando; qui lo si misura. Proiezione ortogonale = convenzione di
disegno, stesso dominio di cornice e cartiglio: sta in framer, non in forge.

- **`framer/views.py`**, ricetta `read_views(result) -> ViewLayout` sopra
  passi pubblici (`classify_view`, `projection_mates`, `principal_view`,
  `view_depth`), stesso schema di `detect_frame` (D13).
- **Ortogonale / assonometria**: quota di lunghezza dei LineSeg orizzontali
  o verticali (±2°) ≥ 0,5. Sul campione `islands` di forge le ortogonali
  stanno fra 68% e 100%, le assonometrie fra 0% e 32%: niente in mezzo, e il
  motivo è geometrico (un pezzo prismatico proiettato ortogonalmente è fatto
  di orizzontali e verticali). Le assonometrie di `assieme` non sono
  isometriche vere (25–53% a ±30°): la regola è "poche orizzontali e
  verticali", non "tante a 30°".
- **Compagni di proiezione**: stessa estensione verticale (frontale ↔
  laterale) o orizzontale (frontale ↔ pianta) entro 1 mm.
- **Vista principale**: compagni in tutte e due le direzioni (la più
  grande); altrimenti l'unica ortogonale; altrimenti la più grande con
  compagni in una direzione sola, flag `principal: single projection`;
  altrimenti `None` + `principal: uncertain`.
- **Profondità, non spessore**: la terza dimensione dai compagni della
  principale (3 su `tavola_05`, 5 su `leva_01`, 80 su `assieme_016`). Che sia
  lo spessore di una lamiera o l'ingombro di un assieme è interpretazione e
  sta sopra (DESIGN: niente supposizioni non etichettate). Compagni
  discordi → `None` + `depth: inconsistent`.
- **Simbolo**: isola senza compagni, dimensione maggiore sotto 1/10 della
  dimensione minore della vista di riferimento (la principale, o la più
  grande). Questa soglia è scelta, non geometrica: sul campione separa
  logo/segni (1–10 mm) dalle viste vere più piccole (`tavola_12` 54×3,
  `tavola_01` 16×115).
- Sul campione (21 fogli): principale trovata su 18; i 3 senza sono le due
  assonometrie pure (`3d_1`, `3d_painted`) e `tavola_01` (viste non
  allineate).
- **Mai `detect` sulle viste** (Federico, poi forge D67: rinominata
  `detect_flat`). Presuppone un pezzo piano visto dalla faccia; su una vista
  trova "pieghe" negli spigoli e "fori" nelle lettere. Una prima stesura di
  questa voce contava le pieghe di `detect` sulle viste: tolte, non hanno
  senso per costruzione. La lettura delle feature sulle viste non esiste
  ancora (vedi Appunti).
- **Non risolto qui**: se la vista principale sia uno sviluppo (lamiera
  piana) o un pezzo già formato. Fuori anche: sezioni (servono tratteggio o
  etichetta), dettagli in altra scala, primo/terzo diedro.

Suite: 47 passed (7 nuovi in `test_views.py`).

### D19 — I fori della vista principale: `read_holes`, passante per convenzione  ✅

Primo caso di lettura delle feature sulle viste (Appunti, "Chi fa cosa"):
per ogni cerchio della principale (`forge.contour_shape`), la traccia nelle
viste compagne e la quota di diametro agganciata. forge dice "cerchio";
che sia un foro passante o cieco si legge qui, incrociando viste e
notazione. Trapano o laser no: è processo, snapbend.

- **`framer/holes.py`**, ricetta `read_holes(doc, result, views) ->
  HoleLayout` sopra passi pubblici (`principal_circles`, `hole_trace`,
  `diameter_callouts`, `parse_callout`, `callout_scale`, `group_holes`);
  `describe_holes` scrive i gruppi ("2 fori passanti Ø5,3 +0,05/0,
  profondità 4"). Serve `doc` oltre a `result`: le linee nascoste restano
  fuori dalle isole.
- **Passante per convenzione** (Federico): senza indicazioni un foro è
  passante; su una lamiera tagliata al laser un foro cieco non esiste. Le
  nascoste si omettono spesso: la loro assenza non fa un cieco. `source =
  "convention"`, non una confidenza bassa. Profondità = quella delle viste
  (D18).
- **Traccia**: nelle compagne, due pareti rettilinee (qualunque tipo di
  linea) alla quota del cerchio ± r. Come finisce ogni parete: su una
  **faccia** (una linea che la attraversa, un edge che va verso l'esterno —
  anche obliquo, uno smusso — o il bordo della vista) o su un **fondo** (edge
  solo verso l'altra parete, piatto o a punta). Faccia–faccia → passante,
  profondità = lunghezza delle pareti; faccia–fondo → cieco. Pareti senza
  né l'una né l'altro non sono una traccia.
- **Scartato**: passante solo se le pareti coprono tutta la vista compagna,
  cieco altrimenti. Sulle laterali di lamiera piegata (`tavola_04`,
  `tavola_02`, `tavola_07`) il foro passa un'ala spessa 1–3 mm e usciva
  "cieco profondità 1": la faccia interna dell'ala scambiata per fondo.
- **Quota**: la `Dimension` di diametro con `references` sul cerchio
  (`forge.dimension_references`, forge D69); dal `display_text` si leggono
  "Ø"/"M", valore e tolleranza (`+0,05^-0` impilata, `±`). Il resto non letto
  finisce in un flag.
- **Scala** (appunto "Scala", ristretto ai fori): scritto / misurato sulle
  quote Ø, non sui filetti M (cadono sul nocciolo). Quote discordi → `None`
  + `scale: inconsistent`. `leva_01`: 0,8, profondità 5 disegnata → 4.
- **Non fatto**: cerchi concentrici (lamatura, svasatura: `tavola_02` Ø30
  cieco 1,5 sopra Ø8 passante 13,5; `tavola_05`) restano fori separati con
  il flag `concentric:`. Callout con conteggio ("3xØ5"), profondità scritta
  (↧), fori visti di fianco nella principale: dopo.
- **Limite noto**: la profondità per convenzione è quella delle viste; su un
  pezzo piegato (`tavola_04`, 50) non è lo spessore dove sta il foro.

Suite: 56 passed (8 nuovi in `test_holes.py`). DXF da giudicare:
`scripts/05_read_holes.py` → `pipeline_output/holes/`.

---

## Appunti (aperti — non decisioni)

Raccolti per argomento. Molti vengono da una sessione di lavoro su forge
(28/09/2026, forge D65–D67): lì si è deciso *che* certe cose vanno in
framer, qui c'è *cosa* sono.

### Chi fa cosa (il confine, detto da Federico)

- **Tre domini, non tre livelli di certezza.** forge = la geometria del
  pezzo. framer = come il pezzo è documentato sul foglio: cornice,
  cartiglio, viste, notazione, scala. Pippo = capire: processo, profilo del
  cliente, incrocio fra numeri e immagine. "È deterministico" **non** è il
  criterio per mettere una cosa in forge: anche la lettura delle viste è
  deterministica e sta qui.
- **La detection di processo non è di forge.** Fori con la soglia da
  trapano, pieghe, incisioni sono sapere di lamiera: andranno in snapbend
  (ex bendly); forge terrà i predicati geometrici (`circular_geometry`,
  `NonContourEdgeDetector`) e l'overlay `cluster.detected`. Direzione
  segnata nel MAP di forge, non ancora fatta.
- **Feature sulle viste: i fori della principale ci sono (D19).** `detect_flat` no (D18).
  Per Federico la lettura va fatta per processo — lamiera, profili,
  asportazione (la stampa 3D probabilmente non ne ha bisogno) — e non è
  deciso dove. Punto di partenza: `forge.contour_shape` (forge D68) dà la
  forma di ogni `inner` — cerchio, stadio, rettangolo, poligono, altro — con
  misure e orientamento, uguale su `heal` e `island`. forge dice "cerchio",
  mai "foro": che quel cerchio sia un foro passante, cieco o un perno lo dice
  snapdraw incrociando le viste (linee nascoste, profondità) e la notazione
  (la quota agganciata); trapano o laser lo dice snapbend.

### Notazione: frecce, quote, callout

- **forge D66 dà già l'aggancio**: `anchor_annotations` riempie
  `Leader.target` con il percorso dell'elemento su cui cade la punta
  (`"clusters[0].inners[3]"`); `forge.resolve_target` lo risolve. Leggere il
  testo ("M8" → quel foro è M8) è di framer, non di forge.
- **Sul campione `islands` i callout dei fori stanno nelle quote di
  diametro, non nelle frecce** (`text_override` `M<>`, `%%c<>`): 18 frecce,
  nessuna con testo. **forge D69** ora dà `Dimension.references` (quale
  elemento misura la quota, da `anchor_annotations`) e un `display_text`
  intero (`"Ø6.5"`, `"M5"`, non più `"n"`/`"M"`). Sul campione: 54 quote
  di diametro su 76 agganciate, 30 a un cerchio dello stesso Ø; un `M5` col
  filetto disegnato come arco aperto cade sul cerchio di nocciolo (Ø4,13) —
  vicino, non esatto: decide snapdraw.
- Da leggere in framer: "M6", "n°23 fori lamati", ∅, R, con `source` +
  `confidence` come il cartiglio (D4).

### Scala

- **Controllo della scala (Federico: è di framer).** Confrontare il valore
  scritto in una quota con la geometria che misura. Caso reale: `leva_01`
  (campione `islands` di forge) ha `∅5,3` su cerchi da 6,625, `∅4,3` su
  5,375, `R8,5` su 10,625 — rapporto 0,8 su tutte: la geometria è a 1,25:1,
  la profondità di `read_views` (5) è in realtà 4 mm. L'aggancio quota →
  cerchio c'è (forge D69): `measured_value` è in unità del disegno (6,625),
  il numero scritto sta in `display_text` (`∅5,3`).

### Come "vedere" un disegno (immagini, Pippo, fingerprint)

- **Come ha "visto" Claude nell'esperimento di forge**: nessun OpenCV,
  nessuna visione artificiale propria. Gli edge di forge disegnati in PNG
  con matplotlib, poi l'immagine letta da un modello multimodale. Nient'altro.
- **Un'immagine porta meno informazione del file vettoriale**: le misure
  esatte, i centri, i raggi si perdono nei pixel. Guardare non sostituisce la
  geometria di forge; la cosa utile è l'incrocio — l'immagine dice "questa è
  un'assonometria / un logo", i numeri dicono quanto misura. Su un caso
  l'occhio ha sbagliato (8 asole chiamate "fori" su `tavola_06`) e forge
  aveva ragione.
- **framer misura, non guarda** (D18): le regole delle viste sono conti
  sulle primitive. Le immagini sono di Pippo: ritagli delle viste passati al
  modello, controllati contro i numeri di forge + framer.
- **Fingerprint (idea di Federico, aperta)**: un descrittore compatto e
  versionato di una vista, calcolato da framer, che risparmi la creazione
  dell'immagine e un domani serva anche ad addestrare qualcosa. Non
  progettato.
- Materiale dell'esperimento (braccio A: agente con solo ezdxf; braccio B:
  forge + framer; immagini, DXF, script): `forge/output/esperimento_agente/`,
  fuori da git.

### Problemi visti sul campione `islands`

- Nell'esperimento a 5 disegni `detect_frame` ha mancato la cornice in 3
  casi su 4.
- La mappatura dei campi del cartiglio non è affidabile.
- `tavola_05`: la "O" del logo esce come isola a sé; la regola del simbolo
  (D18) la scarta come vista, ma resta un cluster.

### Repo

- **Nome: `snapdraw`** (`import snapdraw as sd`), deciso da Federico;
  `snapsheet` scartato perché richiama la lamiera. Stessa famiglia di
  `snapbend` (`sb`). Rinomina del repo e del package non ancora fatta.
- Repo GitHub remoto: non ancora creato. framer resta locale finché non serve.
- Fixture reali (un A3/A4 con cornice e cartiglio veri, rilevamento non
  generazione) da mettere in `tests/examples/` — vedi TODO.md.

### Primo disegno reale

- **Primo giro su un disegno reale** (`tavola_08.dwg`, locale, non
  committato — un complessivo "Group", non un pezzo singolo): `detect_frame`
  e `detect_titleblock` funzionano — cornice trovata (rapporto ISO,
  confidence 1.0) e cartiglio individuato esattamente nell'angolo giusto
  (confidence 0.96). Due cose emerse, non ancora risolte:
  - `iso_format` torna `None` — non è un bug di unità (`$INSUNITS`=4, mm),
    il riquadro di questo disegno (2970×2100) è ~2.5× un A0 nominale: il
    loro template non è un formato ISO standard, o è disegnato a una scala
    non 1:1. Esattamente il caso che ROADMAP.md segnalava ("è già a scala
    reale" è un'assunzione, non una garanzia) — `iso_format` giustamente non
    indovina, torna `None`;
  - i divisori di colonna di un cartiglio reale spesso coprono una riga sola,
    non l'intero cartiglio (`grid_dividers` li scarta, non sono "genuini" a
    livello dell'intero rettangolo) — una cella geometrica finisce quindi con
    più campi dentro. Corretto **nella lettura, non nella geometria**:
    `read_titleblock` ora cerca ogni etichetta del vocabolario nel testo di
    una cella (non solo la prima) e segmenta il valore fino all'etichetta
    successiva, invece di richiedere una cella per campo. Regge bene finché
    tutte le etichette di una riga sono nel vocabolario; se una riga mescola
    etichette note e sconosciute (qui: "DISEGN./CONTR./DATA/PEZZA/FOGLIO",
    non ancora nel vocabolario) quelle sconosciute finiscono dentro il valore
    del campo noto precedente;
  - questo cartiglio incorpora anche una legenda tolleranze/note legali
    dentro lo stesso riquadro — la parola "MATERIALE" ci compare come
    intestazione di colonna della tabella tolleranze ISO 2768, non come
    campo del pezzo: falso positivo del vocabolario su un template
    particolarmente ricco, non un problema di nomenclatura cliente.
  Non ancora deciso come proseguire: allargare il vocabolario ISO generico
  (DISEGN./CONTR./DATA/PEZZA/FOGLIO sono termini standard, non privati) o
  aspettare un disegno di **pezzo singolo** (non un complessivo) più
  rappresentativo del caso d'uso preventivo.
