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

- [ ] **detection sulle isole e combinata sulle viste** (Federico, 5
      ottobre): come `detect_flat` per un pezzo piano, ma su un'isola, più
      una lettura che mette insieme le viste. `read_features` (D23) ne fa
      già una parte (feature per vista, tracce nelle compagne). In più deve
      dire **se il pezzo disegnato è un assemblato** (multipezzo), per
      esempio un saldato: più parti unite che il disegno mostra come un
      oggetto solo. Federico: non basarsi sui simboli di saldatura, che
      nei disegni veri spessissimo non ci sono — va letto dalla geometria
      delle viste. Come, non ancora studiato.
      Viene dopo le isole: se le isole sono sbagliate, si leggono male
      anche i pezzi.

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
- [ ] **isole: quello che resta dopo forge D99-D100** (Federico, 5 ottobre,
      "questo è un buon set di golden"; golden delle isole su anch_01-08):
      - ✅ **anch_07: il cartiglio diventava un'isola** (nessun testo nelle
        celle): MAP D32, griglia in basso a destra anche senza testo.
      - **senza cornice il cartiglio si prende tutto il disegno**
        (`examples/anonymus`, drw_0001, 0007, 0009): nessuna cornice
        trovata, un riquadro passa per cartiglio e assorbe tutti gli edge
        (D12), così non resta nessuna isola. Senza cornice D31-D32 non
        valgono: serve un altro vincolo. drw_0002 ha solo `3DFACE`, niente
        da leggere.
      - **cartiglio di un disegno reale non trovato** (`complete_drawings`,
        Federico l'ha segnato: la fascia bassa in basso a destra): non è fra
        i candidati che toccano il bordo interno della cornice. Da capire se
        `find_rectangles` non lo vede o se non tocca il bordo.
      - **anch_08, vista frontale: un leader esploso** (freccia e linea
        disegnate come geometria, non come annotazione) si attacca alla
        vista. Federico: "almeno il leader non ha senso che sia rosso".
        Riconoscerlo come leader è lettura della notazione, cioè del framer.
      - **anch_08, l'angolo**: specifico di quel disegno, non si tocca nel
        codice generale — sarebbe una regola sul cliente (lavorando sullo
        spessore), roba da ottimizzazione per cliente.

- [ ] **isole di un foglio, giudizi del 5 ottobre** (dalla prova sulla
      scala, forge TODO punto 13, chiuso; pagina "Scala delle isole", `lab/island_scale.py`; giudizi nel
      database della pagina, collezione `picks`). Su 13 disegni: 9 con una
      distanza giusta, tutte fra 17 e 78 mm; la proposta automatica coincide
      con 6 delle 9. Quello che resta per framer:
      - **una vista non si riconosce dalla grandezza.** In `anch_07` e
        `regr_05` la vista laterale (25×32 mm) resta "piccola" perché è sotto
        un quarto della diagonale della vista principale: verificato. Vale
        anche per il classificatore qui sopra ("piccolo E vicino"): una vista
        di lato di un pezzo sottile è piccola e vicina come un simbolo;
      - **i simboli finiscono già nell'isola giusta** (nota di Federico su
        `anch_06`): manca solo riconoscerli come simboli, non attaccarli;
        Anche `anch_02`: la vista di 1525×140 mm è il pezzo stesso, lungo e
        piatto, e fa sembrare piccolo tutto il resto;
      - ✅ **avanzi di cornice** (MAP D28): la cornice si prende la sua
        fascia. Resta aperto: **le note del disegno** (testo fuori dalle
        viste, fuori dalla fascia) vanno tenute come annotazioni generali del
        foglio, trattate come le informazioni del cartiglio — non ancora
        fatto. In `anch_08` restano due tratti di 136×4 mm nel disegno, da
        capire cosa sono.
      - ❌ **scartato: scegliere la distanza dalla scala** (delle isole o del
        disegno letta dal cartiglio). Federico, 5 ottobre: la scala non
        c'entra e non c'entrerà mai con la detection delle isole (forge D98).
        La distanza resta in `sheet_islands(doc)` (MAP D29).
      Positivo: in `regr_01` l'isola di sotto ora si legge intera (prima a
      metà) — non per la cornice tolta, ha detto Federico.
      **Misura del 5 ottobre (dopo D28)**: per ogni disegno giudicato,
      l'intervallo di distanze che dà esattamente le isole scelte (sulla
      scala della pagina, cioè vicinanza fra pezzi, non `forge.island`
      stesso): anch_01 e regr_03 6,7–26,6; anch_04 9,5–70; anch_05 15–77;
      anch_06 19–45; anch_08 20,5–51,6; regr_02 16,9–61,7; regr_04 15–96,7;
      anch_03 61,7–88,9. **Fra 20,5 e 26,6 vanno bene 8 su 9**; anch_03 da
      solo vuole oltre 61,7, e i 4 senza distanza giusta restano.
      Federico: la distanza non è una costante — è flottante, cambia da
      disegno a disegno, e la distanza come criterio potrebbe essere
      sbagliata del tutto. Da provare il **ray casting** per decidere a
      quale isola appartiene un pezzo (proposta sua). Non è il ray casting
      scartato in forge D59/D65: quello cercava il contorno esterno di una
      vista; qui servirebbe a dire chi "vede" chi fra i pezzi del foglio.
      Si giudica sulla pagina "Scala delle isole", non su DXF.
      Federico, su `anch_02`: la regola della pagina ("grande" = diagonale
      ≥ 1/4 della più grande, il gradino scelto fra unioni di isole
      grandi) è sbagliata. Le viste di lato restano grigie perché sono
      molto più piccole della vista dall'alto, lunghissima — e non è un
      caso speciale, succede spesso. La grandezza non entra nel criterio.
      Nota sulla pagina: "a 132,6 ha senso per la vista da sopra e il 3D,
      ma la vista laterale e la vista ingrandita restano grigie".
      Il ray casting c'è già in forge e nessuno lo usa:
      `forge/core/healing/outer_scan.py` (raggi orizzontali e verticali a
      ogni quota-evento; oggi restituisce solo il primo e l'ultimo punto di
      ogni raggio, non tutti i pezzi incontrati in ordine).
      **Prototipo** `lab/island_rays.py` (locale): isole a contatto
      (`forge.island` a 0,5 mm, i fori stanno dentro per contenimento),
      raggi solo sui contorni esterni, per ogni coppia di isole che si
      vedono: raggi, larghezza in comune, vuoto minimo. Primo giro: pochi
      contorni esterni (3–11 per disegno) ma **molti edge aperti restano
      fuori** (68–1504 per disegno): parti di vista che a contatto non
      chiudono un contorno. I raggi devono vedere anche quelli.
      Federico sul metodo (5 ottobre): **non cercare la soglia che separa
      i giudizi** — si finisce con un codice perfettamente deterministico
      su un campione irrilevante. La regola si dice prima, dal motivo
      geometrico; i disegni servono a vedere dove sbaglia, e dove sbaglia
      si dichiara incerto (Pippo), non si ritocca. E l'allineamento in
      proiezione non è una legge: una trave lunghissima ha la vista
      laterale messa sotto, non allineata, a volte in un'altra scala con
      le quote di riferimento. Allineate → indizio di viste separate; non
      allineate → non dice niente.
      **Proposta di Federico: uno scan invece della distanza.** "Le isole a
      occhio sono palesemente separate, c'è spazio fra loro." Tradotto: si
      scorre il foglio con una linea orizzontale e una verticale; dove la
      linea non attraversa nessuna geometria c'è un corridoio vuoto, e un
      corridoio vuoto che attraversa tutta la zona separa due parti. Si
      ripete dentro ogni parte (taglio ricorsivo orizzontale/verticale).
      Nessuna distanza da scegliere. Limiti da vedere sui disegni: viste
      incastrate (un'assonometria nell'angolo a L di un'altra vista) non
      si separano con un taglio dritto → "non so"; simboli disegnati come
      geometria fuori dalla vista vengono staccati (quote e testi no: sono
      annotazioni, non entrano). I mattoni dello scan sono già in
      `outer_scan.py`.
      **Trovato il 5 ottobre, prima dello scan:** `forge.island` raggruppa
      per distanza e poi in ogni gruppo tiene **un solo** contorno esterno,
      il più grande (`outer_face`); gli altri contorni chiusi del gruppo
      finiscono in `outside_loops` e, se il gruppo non è annidato, nel
      cestino. A 10 mm capita in 9 disegni su 13. Regola di Federico:
      **più contorni esterni = isole diverse**. Contato con la regola: il
      numero di isole quasi non cambia fra 5 e 200 mm (anch_01 5, regr_01
      3, anch_05 3 a ogni distanza; oggi anch_01 passa da 5 a 1 a 50 mm).
      Prototipo `lab/island_outers.py`: pezzi a contatto, un'isola per
      contorno esterno non contenuto in un altro, la distanza attacca solo
      i pezzi staccati (pochi: 0–5 per disegno). Pagina "Scala delle
      isole" ripubblicata con questa regola, senza la regola "grande /
      grigio"; giudizi nuovi in `outer_picks`, i vecchi restano in `picks`.
      Da giudicare: viste fatte di più contorni che non si toccano
      (diventano più isole) e simboli chiusi fuori dalle viste (diventano
      isole loro).
      **Proposta di Federico (5 ottobre): togliere la distanza del tutto.**
      Si trovano i contorni esterni (pezzi a contatto, `max_gap`), poi una
      passata di gerarchia assegna alla stessa vista tutto quello che le
      sta dentro, chiuso o aperto. Riapre forge D59/D98 (`island_gap`
      sparisce). Da decidere prima: dove vanno nel modello le linee aperte
      dentro una vista (oggi in `trash_entities` anche se stanno dentro;
      `ForgeCluster` ha posto solo per i giri chiusi) e dove vanno i pezzi
      fuori da ogni contorno (note e segni del foglio, senza distanza non
      si attaccano a niente).
      **Fatto in forge (D99, non committato), ma prima di chiudere:** su
      alcune viste il contorno esterno di forge è sbagliato e dentro non si
      annida niente (c'era già col codice di prima: stesso risultato).
      Verificato su anch_07, vista 104×68: il giro lungo la faccia esterna
      fa tutta la sagoma (206 edge, si chiude), ma passa due volte per due
      nodi dove si incontrano 4 linee; l'anello che ne esce si incrocia,
      le due metà hanno verso opposto e l'area si annulla (347 mm², il 5%
      del rettangolo). Verificato dopo: la direzione di uscita NON è il
      problema (angoli di forge entro 1° da quelli veri). Nei due nodi si
      incrociano un arco e una linea quasi paralleli (2–6°), tratti di
      0,13 mm; il giro va da un capo all'altro della vista lungo due
      percorsi che stanno dallo stesso lato e si incrociano lì: l'area
      racchiusa è quella fra i due (347 = 1001,7 − 654,6). I fori 5×5 e
      3×4 della vista stanno nel suo rettangolo ma fuori da quell'anello.
      Da capire sul disegno (pagina "Contorni delle isole", anch_07, cerchi
      rossi) com'è fatta la sagoma vera di quella vista 3D: se le sue linee
      non chiudono una faccia, il contorno esterno non può contenere i fori.
      Federico (5 ottobre, pagina "Il contorno a otto"): il giro non deve
      tornare indietro ("il sorriso"), deve proseguire la curva e chiudere
      la parte sotto; le linee in mezzo non sono contorno. Indizio suo: la
      vista 3D di anch_02, tutta a spigoli, si chiude bene e prende tutte
      le feature; quella di anch_07, con gli archi, no. Misurato: andata e
      ritorno del giro a ~3 mm per tutta la lunghezza (banda da 347 mm²,
      anche unendo le due parti). Pista: dove una linea è tangente a un arco,
      si incrociano quasi parallele (2–6°) in due punti a 0,13 mm, e lì il
      giro sceglie il ramo sbagliato. Pagina "Contorni delle isole" (anch_02,
      anch_07) con i contorni in verde.
      Fori, controllati il 5 ottobre: anch_02, isola 0 (contorno giusto per
      Federico): 49 cerchi dentro, 49 ritrovati come interni — se sulla
      pagina sembravano persi era la pagina. anch_03, isola 0: 10 cerchi,
      8 ritrovati. I due persi (r 4,25 in 171,9/270 e 171,9/363) sono
      attraversati da linee nascoste: forge li spezza in archi e nessun
      giro chiuso viene trovato, finiscono fra le linee aperte (con
      `cluster_ref` 0, quindi non persi dall'isola, ma non sono un foro).
      Persi anche col codice di prima. Da capire perché il giro del
      cerchio non si chiude.
      **Cartiglio (MAP D31):** i fori "persi" di anch_02 erano mangiati da un
      falso cartiglio; ora 95 su 95. anch_03 dopo D31: 13 cerchi dentro la
      vista, 9 interni — i due delle linee nascoste più due da guardare.
      Aperto: su un foglio generato `find_frame` dà un `inner_bbox` misto
      (lati alto/basso del bordo esterno) e il cartiglio rilevato si
      allarga fino al bordo esterno; sui disegni reali non visto.
- [x] ✅ **chiuso il 5 ottobre**: dopo forge D99-D100 la vista in pianta si trova anche
      senza regole; il test ora lo dice (`test_senza_regole_la_vista_c_e_lo_stesso`).
      Storia: **`test_rules` falliva dal 4 ottobre** (verificato il 5 ottobre: falliva
      già al commit che l'ha spostato sulla copia anonimizzata
      `tests/examples/rules/vista_pianta_assi.dxf`, con forge di quel giorno).
      Fallisce la prima metà: sulla copia la vista in pianta
      (36, 218, 136, 268) si trova anche **senza** regole, mentre il test
      vuole che manchi (gli assi la legavano alle quote, MAP D17). Con le
      regole generiche c'è, come deve. Causa non ancora cercata: o la copia
      non riproduce più il caso del disegno originale, o qualcosa a monte
      (cornice, annotazioni) ha tolto il legame. Da capire prima di toccare
      il test.
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
