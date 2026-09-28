# Scripts

La "palestra" per imparare e collaudare l'API di framer. Ogni script:

- ha un blocco `# --- CONFIG ---` in cima (input, path);
- gira **senza argomenti** (`python scripts/00_detection.py`);
- prima riga `import _paths` — fa `chdir` alla radice del repo, così i path
  relativi in CONFIG risolvono uguale da qualunque CWD;
- input di default che puntano a `tests/examples/`.

| script | copre |
|---|---|
| `00_detection.py` | `framer.detect_frame`, `framer.read_titleblock` — solo la ricetta: rileva cornice e cartiglio e legge i campi, nessuna lettura di forge a valle |
| `01_export.py` | `framer.detect_frame`, `framer.tag_layout` + `forge.island` — marca cornice e cartiglio, legge le viste per isole e scrive il DXF |
| `02_batch_frame.py` | `framer.add_frame`, `framer.add_title_block` — genera cornice+cartiglio in batch su `tests/examples/to_add_frame/` (metadati dal nome file), scrive `pipeline_output/framed/*_framed.dxf`, non tocca gli originali |
