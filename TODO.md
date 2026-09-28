# TODO — snapdraw

## Fatto

- [x] scheletro repo (pyproject, moduli, docs, test, `pip install -e .`)
- [x] aggancio a forge chiuso (opzione B, forge D30) — `tag_layout`
- [x] `detect_frame` portato da forge `ccbb34f^` e riscritto sulle primitive
      di forge — funzionante, test sintetici verdi
- [x] `snapdraw/roles.py`: cornice/cartiglio registrano colore+layer con
      `forge.register_role_style`, allineato a forge D47 (MAP D7)
- [x] `snapdraw/generate.py`: `add_frame`/`add_title_block`, il verso
      "aggiungi" — vettoriale, un template condiviso per A3/A4 orizzontale/
      verticale, provato su 10 fixture reali in `tests/examples/to_add_frame/`
      via `scripts/02_batch_frame.py` (MAP D8)
- [x] cornice a doppio bordo + lineetta di centratura, cartiglio con
      etichetta/valore impilati — ridisegnati su due riferimenti reali in
      `templates/` (locali, mai committati) invece che a occhio (MAP D9)
- [x] griglia di riferimento ISO 5457 sulla cornice: più lineette sui lati
      dei formati più grandi, non un numero fisso (MAP D10)
- [x] **`detect_titleblock`** — griglia interna genuina + filtro celle vuote
      + densità di annotazioni + bonus posizione rispetto alla cornice.
      Provato in round-trip su `generate.py` (`tests/test_titleblock.py`),
      non ancora su un disegno reale (MAP D11)
- [x] **`read_titleblock`** — vocabolario ISO 7200 generico per regex contro
      il testo di ogni cella, non posizionale (MAP D11)
- [x] **22 disegni reali** raccolti in `tests/examples/complete_drawings/`
      (non ancora fixture di test formali — vedi sotto) — sopperisce a quello
      che questa voce chiedeva prima. `lab/survey.py` + `lab/generate_report.py`
      (locali, mai in git) girano `detect`/`heal` su tutti e producono un
      report visivo pubblicato come Artifact, cliccabile per etichettare i
      cluster (`Vista`/`3D`/`Simbolo`/`Decor.`/`Cartiglio`/`Boh`) — dataset in
      corso di costruzione per un futuro classificatore (albero), vedi sotto.
- [x] **il cartiglio assorbe tutto quello che ha dentro** (griglia, simboli,
      loghi), non solo il proprio bordo — altrimenti finiva in
      `trash_entities` senza ruolo o in un cluster spurio (MAP D12)

## Prossimi passi

- [ ] **risultati serializzabili** (Appunti, "Pippo come portale"):
      `to_dict()` su `ViewLayout`, `HoleLayout`, `FrameLayout`, con
      riferimenti stabili (`clusters[i].inners[j]`, `view_<i>.png`) — senza,
      un portale di strumenti non può esporre niente.

- [ ] **fori (MAP D19)**: giudicare i DXF di `pipeline_output/holes/`;
      poi lamature/svasature (cerchi concentrici → un foro solo), callout
      con conteggio ("3xØ5") e profondità scritta (↧), profondità vera
      dove sta il foro su un pezzo piegato.

- [ ] **fixture di regressione formali**: promuovere 2-3 dei 22 disegni reali
      di `lab/` (con permesso cliente) a `tests/examples/` vero e proprio,
      con test che fissano frame/cartiglio/n_cluster attesi — oggi sono solo
      materiale di esplorazione in una cartella locale, non nella suite.
- [ ] **ritarare le soglie di `titleblock.py`** (`CONFIDENCE_THRESHOLD`,
      `MIN_FILLED_CELL_FRACTION`, `MAX_DOMINANT_SEGMENT_FRACTION`) sui 22
      disegni reali — oggi sono le prime che fanno passare il round-trip
      sintetico, non un cartiglio vero. Notato anche: `detect_titleblock`
      trova meno affidabilmente il cartiglio quando manca la cornice o non è
      in basso a destra (perde solo il bonus di posizionamento, ma basta a
      scendere sotto soglia su alcuni disegni) — capire se vale ritarare i
      pesi o aggiungere un segnale indipendente dalla cornice.
- [ ] **classificatore cluster (assorbi/scarta/tieni)** — la parte grossa:
      dopo l'etichettatura in `lab/` (Vista/3D/Simbolo/Decor./Cartiglio),
      allenare un albero (non regressione logistica — la logica ricorrente è
      "piccolo E vicino", un AND di soglie che un albero cattura nativamente)
      su feature geometriche (area relativa, distanza dal cluster più
      grande, distribuzione angoli — utile anche a distinguere viste
      assonometriche, angoli non 0°/90°). Non ancora iniziato: serve prima
      un numero decente di disegni etichettati.
- [ ] confidenza del frame: la formula in `frame._confidence` è grezza,
      tararla sulle fixture reali.
- [ ] formato ISO: `iso_format` assume mm. Se il disegno è in altre unità
      (`doc.source_meta["$INSUNITS"]`) va convertito prima del confronto —
      osservato anche un caso dove il riquadro è a scala reale ma non
      standard (2970×2100mm, ~2.5× A0) pur essendo già in mm: `iso_format`
      giustamente torna `None`, non è un bug di unità.
- [ ] **bug in forge, non qui, ma blocca "vista utile" su alcuni disegni**:
      un outer che non chiude in `heal` su una vista vera (non decorativa) —
      tre casi reali indipendenti ormai (`42D025Z00I`, `U07010Z21`,
      `TRG19E_A.BLANK050` — quest'ultimo con causa trovata: lato spezzato in
      segmenti che non si saldano). Vedi `forge/TODO.md`, sezione "Limiti
      geometrici noti" — decisione se aprire un'indagine dedicata non ancora
      presa.
- [ ] logo/immagine nel cartiglio generato: forge non ha un concetto di
      immagine nel suo modello neutro — andrebbe inserito in un secondo giro
      direttamente sul `Drawing` ezdxf restituito da `to_dxf()`, fuori da
      `snapdraw/generate.py`. Non ancora progettato.
- [ ] griglia di riferimento (D10): il target di 50 mm/zona è dedotto dal
      range ISO 5457 (25–75 mm), non da una tabella ufficiale per formato —
      se Federico ha/trova la tabella vera (conteggio zone per A0..A4),
      ritararla su quella invece che sulla formula.


## Domande aperte

- Repo GitHub remoto: crearlo o tenerlo locale?
- snapdraw modulo dell'interprete o progetto importato? (per ora: importato)
