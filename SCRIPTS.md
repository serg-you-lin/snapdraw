# Scripts

La "palestra" per imparare e collaudare l'API di snapdraw. Ogni script:

- ha un blocco `# --- CONFIG ---` in cima (input, path);
- gira **senza argomenti** (`python scripts/00_detection.py`);
- prima riga `import _paths` — fa `chdir` alla radice del repo, così i path
  relativi in CONFIG risolvono uguale da qualunque CWD;
- input di default che puntano a `tests/examples/`.

| script | copre |
|---|---|
| `00_detection.py` | `sd.detect_frame`, `sd.read_titleblock` — solo la ricetta: rileva cornice e cartiglio e legge i campi, nessuna lettura di forge a valle |
| `01_export.py` | `sd.detect_frame`, `sd.tag_layout` + `sd.sheet_islands` — marca cornice e cartiglio, legge le viste per isole e scrive il DXF |
| `02_batch_frame.py` | `sd.add_frame`, `sd.add_title_block` — genera cornice+cartiglio in batch su `tests/examples/to_add_frame/` (metadati dal nome file), scrive `pipeline_output/framed/*_framed.dxf`, non tocca gli originali |
| `05_read_features.py` | `sd.read_features` + `sd.tag_features` — le feature di tutte le viste ortogonali (fori e tipi, asole, aperture; passante/cieco, quota, scala per vista) sulle fixture e su alcuni fogli di `islands`, scrive `pipeline_output/features/*_features.dxf` con le feature sui layer del loro ruolo e la lettura accanto |
| `06_render_views.py` | `sd.render_views` — un PNG per vista (ritagliato, indice sopra, niente quote né testi) su alcuni disegni del campione `islands`, scrive `pipeline_output/views/<disegno>/view_N.png` |
| `07_check_client_info.py` | `forge.load_dxf` — elenca il testo che forge legge nei fogli di `tests/examples/regression/` (testi, quote, layer delle annotazioni, tipi di linea, header), per controllare che non resti niente del cliente |
