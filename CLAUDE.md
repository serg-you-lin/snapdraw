# snapdraw — note per chi ci lavora

snapdraw legge come un pezzo è documentato sul foglio: cornice, cartiglio,
viste, notazione, scala. Consuma forge, non lo modifica.

## Da leggere prima

- `MAP.md`: decisioni chiuse (D1–D18) e, in fondo, gli **Appunti** divisi per
  argomento: il confine con forge/snapbend/Pippo, notazione, scala, come
  "vedere", problemi aperti. Parti da lì.
- `TODO.md`: i prossimi passi. `DESIGN.md`: gli algoritmi.
- forge: `../forge/docs/LLM.md` (riferimento denso dell'API) e `../forge/MAP.md`.

| situazione | leggi |
|---|---|
| **stai per scrivere una funzione, un helper, una classe** | `docs/INDEX.md` — ogni nome del package con `file:riga`. Controlla che nome *e* lavoro non esistano già; un fatto geometrico va cercato anche in `../forge/docs/INDEX.md`, e se manca si aggiunge a forge |
| perché una cosa è fatta così | `MAP.md` (una decisione chiusa non si ridecide) |
| script da lanciare | `SCRIPTS.md` |

`docs/INDEX.md` è **generato**, non si tocca a mano:

```
python scripts/gen_index.py            # dopo aver aggiunto o spostato codice
python scripts/gen_index.py --check    # esce 1 se è vecchio o la regola di dipendenza è violata
```

`tests/test_index.py` lo controlla nella suite. La regola sta in
`pyproject.toml` (`[tool.gen_index.layers]`): snapdraw non importa `ezdxf`
né `snapbend`. Lo script è identico a quello di forge e snapbend (copia di
riferimento nella skill `code-guardrails`).

## Regole

- Le viste di un disegno si leggono con `forge.island()`, non con `heal()`.
- **Mai `snapbend.flat.detect_flat` sulle viste**: presuppone un pezzo piano visto
  dalla faccia. Su una vista i suoi numeri non hanno senso.
- Test e prove si costruiscono con le API di forge (`forge.load_dxf`,
  `forge.load_geometry`, `Edge`, `LineSeg`), mai con ezdxf direttamente. Si
  ragiona in termini di forge (edge, ruolo, segmento), non di entità o layer
  DXF.
- Una decisione va in `MAP.md` con il perché; le docstring restano corte.
- Un file grande si filtra, non si legge: per trovare qualcosa dentro un
  disegno, un log, un golden si usa Grep o un piccolo parser e si legge solo
  il suo output.
- Risultati geometrici da giudicare: dare a Federico dei DXF da aprire, non
  solo numeri o PNG.

## Ambiente

- Test: `.venv/Scripts/python.exe -m pytest -q` (forge installato in modo
  editabile da `../forge`).
- Campione di disegni con viste: `../forge/tests/examples/islands`.
