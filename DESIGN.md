# framer — design

Origine: `FRAMER.md` nel repo di forge (la specifica dalla quale nasce questo
modulo). Qui la versione operativa, allineata al codice.

## Dove gira nella pipeline

framer lavora sulla geometria **grezza** di `doc` — le primitive che forge ha
già parsato e normalizzato (`forge.load_dxf`), ma **prima** che `heal` costruisca
il grafo.

```
file CAD
   │
   ▼
forge.load_dxf(path)      → ForgeDocument (edges puri + annotations)
   │
   ▼
framer.detect(doc)        → FrameLayout: cornice + cartiglio
   │
   ▼
framer.tag_layout(doc, l) → setta edge.role su doc.edges (frame / title_block)
   │
   ▼
forge.heal(doc)           → cluster puliti: frame e title_block fuori dal grafo,
   │                         in trash_entities, non cluster
   ▼
forge.detect(result)      → feature dentro i cluster (forge, non li tocca)
   │
   ▼
framer.read_titleblock(l) → (stub) celle del cartiglio → metadati di disegno
```

## I due ruoli

| ruolo | cos'è | forge lo conosce? |
|---|---|---|
| `frame` | il riquadro di formato ISO | no — slug di consumatore (forge D31 ha rimosso `ContourRole.FRAME`) |
| `title_block` | il cartiglio | no — slug di consumatore, forge lo conserva (D27) |

Nessuno dei due è strutturale: geometria non di taglio. `heal` li tiene fuori
dal grafo, finiscono in `trash_entities` col ruolo intatto, e l'output DXF li
scrive su un layer col nome dello slug (`frame`, `title_block`), colore grigio.

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
5. **conservativo**: se nessun candidato supera la soglia, `detect_frame`
   ritorna `None`, `detect()` mette `frame: uncertain` nei flag e `tag_layout`
   non marca niente. Meglio un cluster sporco che buttare via la geometria di
   un pezzo.

Il formato ISO (`A4`, `A3`, ...) è dedotto dalle dimensioni della bbox
assumendo mm — best effort, non blocca.

## Algoritmo cartiglio (`titleblock.py`, stub)

Il cartiglio **non è per forza dentro una cornice**: il rilevamento è
indipendente. Segnali da combinare (nessuno sufficiente da solo):

- rettangolo chiuso **suddiviso da linee interne** in una griglia di celle — il
  più forte, non dipende dalla cornice;
- **racchiude un gruppo denso di annotazioni** — incrocio con `doc.annotations`;
- dimensioni tipiche da cartiglio, piccolo rispetto all'estensione totale;
- se la cornice c'è: **dentro** la sua bbox, di solito in un **angolo** in basso
  a destra — segnale aggiuntivo, non necessario;
- opzionale: **nome di blocco noto** se l'adapter lo espone.

Conservativo: nel dubbio non marca, `title_block: uncertain` nei flag.

## L'aggancio a forge (opzione B, chiusa in forge D30 + D31)

framer setta `edge.role` sugli `Edge` di `doc.edges` prima di `heal`. forge non
ha preso API nuove: ha consolidato il concetto "ruolo strutturale" in
`forge.is_structural_role` e reso l'aggancio un contratto.

- `heal._split_labeled` estrae dal grafo **ogni** edge con ruolo deciso e non
  strutturale (quindi `frame`, `title_block`, slug custom): non ci passano né
  per gap solving né per la ricerca loop;
- `detect()` non trasforma un ruolo che non conosce in una feature: lo lascia
  in `trash_entities`;
- l'output DXF scrive quella geometria nativa su un **layer col nome dello
  slug** (`frame`, `title_block`), colore grigio — non su `Trash` insieme alla
  spazzatura vera (D31: `ContourRole.FRAME` rimosso da forge, i ruoli di
  consumatore vanno su un layer loro).

Invariante: **framer non ragiona dentro forge.** Chiama `forge.load_dxf`, fa il
suo lavoro geometrico, restituisce dei ruoli. Se serve un cambiamento in forge è
solo per **accettare** i ruoli, mai per **decidere** cosa sia un cartiglio.

## Il verso "aggiungi" (più avanti)

Oltre a *rilevare* una cornice, framer può *generarne* una standard e metterla
attorno a un disegno che non ce l'ha: dato un `ForgeResult` e un formato ISO,
produce gli edge di cornice + un cartiglio vuoto. Fuori dal primo giro.

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
