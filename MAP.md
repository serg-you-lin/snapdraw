# MAP — log delle decisioni di framer

Registro cronologico. Una decisione chiusa non si ri-decide: se cambia idea, è
una nuova voce che supera la precedente.

---

## DECISIONI CHIUSE

### D1 — framer è un repo a sé, consumatore di forge  ✅

Nasce come modulo scorporato dalla specifica `FRAMER.md` (repo forge). Repo
separato (non cartella dentro l'interprete, che ancora non esiste), sibling di
`dxf-forge`, package `framer`. Quando l'interprete esisterà lo importerà come
libreria. Precedente: `unfold`.

forge è dipendenza **locale non pubblicata**: `pip install -e ../dxf-forge`,
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

---

## Appunti (aperti — non decisioni)

- Repo GitHub remoto: non ancora creato. framer resta locale finché non serve.
- Fixture reali (un A3/A4 con cornice e cartiglio veri) da mettere in
  `tests/examples/` — vedi TODO.md.
