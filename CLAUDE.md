# framer — note per chi ci lavora

framer legge come un pezzo è documentato sul foglio: cornice, cartiglio,
viste, notazione, scala. Consuma forge, non lo modifica.

## Da leggere prima

- `MAP.md`: decisioni chiuse (D1–D18) e, in fondo, gli **Appunti** divisi per
  argomento: il confine con forge/snapbend/Pippo, notazione, scala, come
  "vedere", problemi aperti. Parti da lì.
- `TODO.md`: i prossimi passi. `DESIGN.md`: gli algoritmi.
- forge: `../forge/docs/LLM.md` (riferimento denso dell'API) e `../forge/MAP.md`.

## Regole

- Le viste di un disegno si leggono con `forge.island()`, non con `heal()`.
- **Mai `forge.detect_flat` sulle viste**: presuppone un pezzo piano visto
  dalla faccia. Su una vista i suoi numeri non hanno senso.
- Test e prove si costruiscono con le API di forge (`forge.load_dxf`,
  `forge.load_geometry`, `Edge`, `LineSeg`), mai con ezdxf direttamente. Si
  ragiona in termini di forge (edge, ruolo, segmento), non di entità o layer
  DXF.
- Una decisione va in `MAP.md` con il perché; le docstring restano corte.
- Risultati geometrici da giudicare: dare a Federico dei DXF da aprire, non
  solo numeri o PNG.

## Ambiente

- Test: `.venv/Scripts/python.exe -m pytest -q` (forge installato in modo
  editabile da `../forge`).
- Campione di disegni con viste: `../forge/tests/examples/islands`.
