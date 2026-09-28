# snapdraw

Rilevamento **e generazione** automatica di **cornice** e **cartiglio** nei
disegni tecnici impaginati.

*(English version: [README.md](README.md))*

## Cos'è

`snapdraw` è un **consumatore di [forge](../forge)**. Riconosce nella
geometria di un disegno due cose:

- la **cornice** (`frame`) — il riquadro di formato ISO che borda il foglio;
- il **cartiglio** (`title_block`) — il riquadro delle informazioni, di solito
  suddiviso in celle e pieno di testo.

Non fa parte di forge: forge resta neutro e deterministico e non decide cosa sia
un cartiglio. snapdraw usa le primitive di forge per fare il riconoscimento,
assegna i ruoli (`frame`, `title_block`) e li riporta giù a forge come input —
lo stesso pattern di `label_map` e di `detect`.

Nel disegno d'insieme snapdraw è un **modulo dell'interprete di disegno** (progetto
ancora da fare), sorella dell'unfolder. È un repo suo perché il problema è grosso
e vale come capacità a prescindere dall'interprete.

## Perché serve

Su un disegno con la cornice, forge oggi produce **un unico cluster** con dentro
tutta la geometria del foglio: la cornice è il loop più esterno e si mangia
tutto. snapdraw rileva cornice e cartiglio **prima** di `forge.heal`, li marca, e
`heal` li esclude dal calcolo dei cluster. L'outer vero dei pezzi emerge; il
cartiglio non è un cluster; i suoi testi restano senza `cluster_ref`.

## Uso

```python
import forge
import snapdraw as sd

doc = forge.load_dxf("disegno.dxf", role_rules=sd.load_rules("generic"))

layout = sd.detect_frame(doc)    # cornice + cartiglio sulla geometria grezza
fields = sd.read_titleblock(layout)

# solo se servono i pezzi: marca, poi scegli la lettura di forge
sd.tag_layout(doc, layout)       # marca gli Edge → role="frame" / "title_block"
result = forge.island(doc)           # una messa in tavola si legge per isole
```

I ruoli si assegnano al caricamento con i file di regole in `rules/`, che
`sd.load_rules` trasforma in `forge.RoleRule`. `rules/generic.json` ha
le regole del disegno tecnico, per tutti: il tratto e punto (`CENTER`,
`PHANTOM`, ...) è asse o linea di costruzione per ISO 128 e diventa
`construction`, così non lega più le viste alle quote. Il tratteggio
semplice (`HIDDEN`) è uno spigolo nascosto, geometria vera, e non si tocca.
Uno studio o un cliente scrive le sue regole (nomi di layer compresi) in
`rules/studio_<nome>.json`, fuori da git, e le mette prima:

```python
role_rules = sd.load_rules("studio_x") + sd.load_rules("generic")
```

`sd.detect_frame(doc)` è una **ricetta**, come lo è `forge.heal` (forge
D62): compone passi pubblici — `find_frame(doc)` e
`find_titleblock(doc, frame=...)` — e non presuppone nessuna lettura di forge
a valle. Per una lettura diversa componi i passi a mano. Ritorna un
`FrameLayout`:

- `frame` — bbox, edge e formato ISO della cornice, o `None`
- `title_block` — bbox, edge e celle del cartiglio, o `None`
- `flags` — `frame: uncertain`, `title_block: uncertain`, ...

## Generare cornice e cartiglio

Il verso opposto: dato un disegno senza cornice, `add_frame` ne aggiunge una
ISO standard attorno alla geometria esistente, e `add_title_block` aggiunge
un cartiglio compilato con i dati del chiamante — mai salvati in questo
repo, stesso principio del `data_injector` di forge.

```python
doc = forge.load_dxf("pezzo_nudo.dxf")

sd.add_frame(doc)                                          # cornice ISO attorno alla geometria esistente
sd.add_title_block(doc, fields={"material": "S235JR", "quantity": "2"})

result = forge.heal(doc)
forge.to_dxf(result, doc).saveas("pezzo_framed.dxf")
```

`add_frame` sceglie da solo il formato e l'orientamento ISO più piccoli
(A4..A0, orizzontale o verticale) che contengono la geometria esistente più
un margine più lo spazio per il cartiglio — non c'è un parametro
`fmt`/`orientation` da passare. Entrambe le funzioni sono puramente
forge-native (`forge.load_geometry` + `forge.Note`, niente ezdxf) e taggano
la propria geometria con `role="frame"`/`"title_block"`, quindi
`heal`/`detect`/`to_dxf` la trattano esattamente come una rilevata. Il
logo/immagine resta fuori per ora — il modello neutro di forge non ha un
concetto di immagine.

## Aggancio a forge

snapdraw si aggancia con l'**opzione B** (forge D30): setta `edge.role` sugli
`Edge` di `doc.edges` prima di `heal`. forge non ha preso nessuna API nuova —
`forge.heal._split_labeled` estrae dal grafo ogni ruolo deciso e non
strutturale, e `forge.detect` non tocca i ruoli che non conosce. La geometria di
cornice e cartiglio non si perde: finisce in `trash_entities` col ruolo intatto
e l'output DXF la riscrive nativa.

Serve forge installato a parte:

```
pip install -e ../forge
pip install -e .
```

## Stato

Pre-alpha.

- `detect_frame` — la ricetta sopra `find_frame` + `find_titleblock`
- `find_frame` — **portato e funzionante** (era il `frame_detector` di forge,
  rimosso in forge D24 perché gira prima di `heal`)
- `find_titleblock` / `read_titleblock` — **funzionanti** (soglie ancora grezze)
- `add_frame` / `add_title_block` — **funzionanti**, solo vettoriale (niente
  logo/immagine ancora)

Vedi [TODO.md](TODO.md) e [DESIGN.md](DESIGN.md).
