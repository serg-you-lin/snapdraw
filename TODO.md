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

- [ ] **test "lettura per un agente AI" sui disegni veri** (deciso con
      Federico il 3 ottobre; contesto e prima prova in `forge/MAP.md`, nota
      aperta "forge as the step before an AI reads a drawing"). Si fa
      **qui**, non in forge, e **dopo** due cose: `detect_feature` sulle
      isole e `detect_combined` (feature lette mettendo insieme viste e
      sezioni). Il motivo: su `anch_01` la lettura fatta con il solo
      `island()` ha perso le svasature (cerchi concentrici che diventano
      mezzi archi o spariscono) e non separava le viste (la cornice
      diventava l'outer di tutto). Non è un difetto di `island()`: manca la
      detection, che è di snapdraw.
      Come si fa: tre agenti nuovi con le stesse domande a risposta nota,
      (a) solo PNG, (b) PNG + lettura, (c) solo DXF grezzo; si contano le
      risposte giuste e i token consumati. Prima prova (6 domande, un
      disegno): (a) 2/6 con ~45k token, (b) 6/6 con ~50k, (c) 6/6 con ~178k.
      Solo su disegni **anonimizzati** (il lotto `anonimizzati/`), perché il
      risultato è fatto per essere mostrato. Il DXF grezzo solo su 1–2
      disegni medi: quelli grandi non entrano nel contesto di un agente.

- [ ] **cartiglio sulle fixture** (MAP D22): falso positivo su `regr_03`
      (la fascia della griglia di riferimento), campi letti male su
      `regr_05`/`regr_02`/`regr_04` — ritarare `detect_titleblock` e la
      lettura dei campi, poi rimettere i campi nel golden.

- [ ] **risultati serializzabili** (Appunti, "Pippo come portale"):
      `to_dict()` su `ViewLayout`, `HoleLayout`, `FrameLayout`, con
      riferimenti stabili (`clusters[i].inners[j]`, `view_<i>.png`) — senza,
      un portale di strumenti non può esporre niente.

- [ ] **feature (MAP D23)**: giudicare i DXF di `pipeline_output/features/`,
      poi rigenerare i golden; sezioni fuori dalle compagne; tracce per
      coincidenza in compagne complesse; rettangoli raccordati.
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
