# Scripts

La "palestra" per imparare e collaudare l'API di framer. Ogni script:

- ha un blocco `# --- CONFIG ---` in cima (input, path);
- gira **senza argomenti** (`python scripts/00_detect.py`);
- prima riga `import _paths` — fa `chdir` alla radice del repo, così i path
  relativi in CONFIG risolvono uguale da qualunque CWD;
- input di default che puntano a `tests/examples/`.

| script | copre |
|---|---|
| `00_detect.py` | `framer.detect`, `framer.tag_layout` — rileva cornice e cartiglio, marca gli Edge, passa a `forge.heal` e mostra i cluster |
