# TODO — framer

## Fatto

- [x] scheletro repo (pyproject, moduli, docs, test, `pip install -e .`)
- [x] aggancio a forge chiuso (opzione B, forge D30) — `tag_layout`
- [x] `detect_frame` portato da forge `ccbb34f^` e riscritto sulle primitive
      di forge — funzionante, test sintetici verdi

## Prossimi passi

- [ ] **fixture reali** in `tests/examples/`: un `6200013103` con la cornice
      (chiedere al cliente una versione completa), più un paio di A3/A4
      standard. Test di regressione su quelli, non solo sui sintetici.
- [ ] **`detect_titleblock`** — i segnali combinati (griglia di celle,
      densità di annotazioni via `doc.annotations`, dimensioni, angolo della
      cornice, nome blocco). Conservativo. Vedi DESIGN.md.
- [ ] **`read_titleblock`** — lettura delle celle → campi con `source` +
      `confidence`. Decidere se sta qui o nello step dell'interprete.
- [ ] confidenza del frame: la formula in `frame._confidence` è grezza,
      tararla sulle fixture reali.
- [ ] formato ISO: `iso_format` assume mm. Se il disegno è in altre unità
      (`doc.source_meta["$INSUNITS"]`) va convertito prima del confronto.
- [ ] il verso "aggiungi una cornice" (generazione), quando serve per i draft.

## Domande aperte

- Repo GitHub remoto: crearlo o tenerlo locale?
- framer modulo dell'interprete o progetto importato? (per ora: importato)
