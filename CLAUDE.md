# snapdraw — note per chi ci lavora

snapdraw legge come un pezzo è documentato sul foglio: cornice, cartiglio,
viste, notazione, scala. Consuma topo, non lo modifica.

## Da leggere prima

- `MAP.md`: decisioni chiuse (D1–D18) e, in fondo, gli **Appunti** divisi per
  argomento: il confine con topo/snapbend/Pippo, notazione, scala, come
  "vedere", problemi aperti. Parti da lì.
- `TODO.md`: i prossimi passi. `DESIGN.md`: gli algoritmi.
- topo: `../topo/docs/LLM.md` (riferimento denso dell'API) e `../topo/MAP.md`.

| situazione | leggi |
|---|---|
| **devi capire cosa c'è o cosa fa una funzione** (di snapdraw o di topo) | prima `docs/INDEX.md` e `../topo/docs/LLM.md`, poi solo le righe che indicano. Mai leggere un modulo intero per capirlo: l'indice c'è per risparmiare token |
| **stai per scrivere una funzione, un helper, una classe** | `docs/INDEX.md` — ogni nome del package con `file:riga`. Controlla che nome *e* lavoro non esistano già; un fatto geometrico va cercato anche in `../topo/docs/INDEX.md`, e se manca si aggiunge a topo |
| perché una cosa è fatta così | `MAP.md` (una decisione chiusa non si ridecide) |
| script da lanciare | `SCRIPTS.md` |

`docs/INDEX.md` è **generato**, non si tocca a mano:

```
python scripts/gen_index.py            # dopo aver aggiunto o spostato codice
python scripts/gen_index.py --check    # esce 1 se è vecchio o la regola di dipendenza è violata
```

`tests/test_index.py` lo controlla nella suite. La regola sta in
`pyproject.toml` (`[tool.gen_index.layers]`): snapdraw non importa `ezdxf`
né `snapbend`. Lo script è identico a quello di topo e snapbend (copia di
riferimento nella skill `code-guardrails`).

## Regole

- Le viste di un disegno si leggono per isole con `sd.sheet_islands(doc)` — `topo.island()` con la distanza scelta da snapdraw, l'unico posto dove la si sceglie (MAP D29) — non con `heal()`.
- **Mai `snapbend.flat.detect_flat` sulle viste**: presuppone un pezzo piano visto
  dalla faccia. Su una vista i suoi numeri non hanno senso.
- Test e prove si costruiscono con le API di topo (`topo_dxf.load_dxf`,
  `topo.load_geometry`, `Edge`, `LineSeg`), mai con ezdxf direttamente. Si
  ragiona in termini di topo (edge, ruolo, segmento), non di entità o layer
  DXF.
- Una decisione va in `MAP.md` con il perché; le docstring restano corte.
- Un file grande si filtra, non si legge: per trovare qualcosa dentro un
  disegno, un log, un golden si usa Grep o un piccolo parser e si legge solo
  il suo output.
- Risultati geometrici da giudicare: dare a Federico dei DXF da aprire, non
  solo numeri o PNG.

## Ambiente

- Test: `.venv/Scripts/python.exe -m pytest -q` (topo installato in modo
  editabile da `../topo`).
- Campione di disegni con viste: `../topo/tests/examples/islands`.
