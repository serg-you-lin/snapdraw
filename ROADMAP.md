# ROADMAP — la strada verso Pippo, in breve

Non è un doppione di `INTERPRETER.md` (quello resta il "come e perché" di
ogni pezzo). Questo è il foglio corto: chi fa cosa, cosa c'è già, cosa manca
davvero, in che ordine. Se ti perdi tra i dettagli, riparti da qui.


## Il traguardo, con le tue parole

**Pippo**: un agente addestrato/tarato su uno **stock di disegni di un
cliente specifico** (non "un agente generico per qualsiasi disegno del
pianeta" — un agente che impara le convenzioni di UN cliente alla volta,
esattamente il `ShopProfile` già previsto).



## Chi fa cosa — quattro pezzi, non settanta moduli

| pezzo | di cosa si occupa | dove vive |
|---|---|---|
| **forge** | il pezzo fabbricato: geometria, topologia, feature (fori/pieghe/incisioni), conteggi (`cluster.summary`) | `forge`, maturo |
| **framer** | come il disegno è documentato: cornice, cartiglio, callout, raggruppamento viste | `framer`, pre-alpha, un pezzo su cinque fatto |
| **l'interprete** | nomenclatura privata del cliente, profili, riempimento buchi da ERP | non esiste ancora un repo — e forse non gli serve nemmeno, vedi `INTERPRETER.md` |
| **bendly** | sviluppo lamiere — direzione opposta (da specifica a DXF), oracolo di verifica in futuro | `unfold_generator`, alpha, già in uso |

> **Nota (Federico): "forse non gli serve nemmeno [un repo]" — non ho capito
> cosa intendi.**
> **Risposta:** non "l'interprete non ti serve" (quello ti serve di sicuro:
> nomenclatura, profili, ERP restano privati per forza). Intendevo: forse non
> ti serve un **repo/progetto vero e proprio con un orchestratore** —
> `pipeline.py` che chiama forge poi framer poi traduzione in sequenza
> fissa. Perché una volta tolto tutto quello che è finito in framer, quello
> che resta dell'interprete è poca roba: un paio di file Python privati
> (`nomenclature.py`, `profiles/`) con dentro le tue tabelle e i tuoi
> pattern. È abbastanza sottile che potrebbe bastarti chiamare quelle
> funzioni direttamente da dove oggi chiami forge, senza costruire un
> pacchetto a parte che le orchestra. Il dettaglio è nella "Domanda aperta"
> di `INTERPRETER.md`, sezione "L'interprete": non è deciso, resta
> intenzionalmente aperto finché non vedi quanto pesa in pratica la parte di
> traduzione privata.

Tutto il resto (Determinismo/Interpretazione/Correzione, il confine
manifattura/documentazione/privato) è spiegazione del *perché* questa tabella
è fatta così — sta in `INTERPRETER.md`, non serve ripeterlo qui.
