# framer

Rilevamento automatico di **cornice** e **cartiglio** nei disegni tecnici
impaginati.

*(English version: [README.md](README.md))*

## Cos'è

`framer` è un **consumatore di [forge](../dxf-forge)**. Riconosce nella
geometria di un disegno due cose:

- la **cornice** (`frame`) — il riquadro di formato ISO che borda il foglio;
- il **cartiglio** (`title_block`) — il riquadro delle informazioni, di solito
  suddiviso in celle e pieno di testo.

Non fa parte di forge: forge resta neutro e deterministico e non decide cosa sia
un cartiglio. framer usa le primitive di forge per fare il riconoscimento,
assegna i ruoli (`frame`, `title_block`) e li riporta giù a forge come input —
lo stesso pattern di `label_map` e di `detect`.

Nel disegno d'insieme framer è un **modulo dell'interprete di disegno** (progetto
ancora da fare), sorella dell'unfolder. È un repo suo perché il problema è grosso
e vale come capacità a prescindere dall'interprete.

## Perché serve

Su un disegno con la cornice, forge oggi produce **un unico cluster** con dentro
tutta la geometria del foglio: la cornice è il loop più esterno e si mangia
tutto. framer rileva cornice e cartiglio **prima** di `forge.heal`, li marca, e
`heal` li esclude dal calcolo dei cluster. L'outer vero dei pezzi emerge; il
cartiglio non è un cluster; i suoi testi restano senza `cluster_ref`.

## Uso

```python
import forge, framer

doc = forge.load_dxf("disegno.dxf")

layout = framer.detect(doc)          # cornice + cartiglio sulla geometria grezza
framer.tag_layout(doc, layout)       # marca gli Edge → role="frame" / "title_block"

result = forge.heal(doc)             # heal esclude cornice e cartiglio dai cluster
```

`framer.detect(doc)` ritorna un `FrameLayout`:

- `frame` — bbox, edge e formato ISO della cornice, o `None`
- `title_block` — bbox, edge e celle del cartiglio, o `None`
- `flags` — `frame: uncertain`, `title_block: uncertain`, ...

## Aggancio a forge

framer si aggancia con l'**opzione B** (forge D30): setta `edge.role` sugli
`Edge` di `doc.edges` prima di `heal`. forge non ha preso nessuna API nuova —
`forge.heal._split_labeled` estrae dal grafo ogni ruolo deciso e non
strutturale, e `forge.detect` non tocca i ruoli che non conosce. La geometria di
cornice e cartiglio non si perde: finisce in `trash_entities` col ruolo intatto
e l'output DXF la riscrive nativa.

Serve forge installato a parte:

```
pip install -e ../dxf-forge
pip install -e .
```

## Stato

Pre-alpha.

- `detect_frame` — **portato e funzionante** (era il `frame_detector` di forge,
  rimosso in forge D24 perché gira prima di `heal`)
- `detect_titleblock` — **stub**
- `read_titleblock` — **stub**

Vedi [TODO.md](TODO.md) e [DESIGN.md](DESIGN.md).
