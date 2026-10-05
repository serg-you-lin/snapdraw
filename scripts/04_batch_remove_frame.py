"""
scripts/04_batch_remove_frame.py
--------------------------------
Il verso "togli": su ogni DXF di una cartella rileva la cornice e, se la trova,
la elimina dal disegno. Il risultato finisce nella STESSA cartella come
`<nome>_noframe.dxf`.

Nota sul come: `sd.tag_layout` + `forge.island` NON basta a rimuovere — quel
percorso marca gli Edge e li fa finire in `trash_entities`, che `forge.to_dxf`
riscrive sul layer `Frame` (forge D31): la cornice resta nel file, solo su un
altro layer. Per togliere davvero la geometria va staccata da `doc.edges` prima
di `heal`, per identità di oggetto (gli Edge in `layout.frame.edges` sono gli
stessi oggetti di `doc.edges`, snapdraw non ne fa copie). La lettura è
`island()`, non `heal()`: una messa in tavola è fatta di viste (MAP D14).
"""

import _paths  # noqa: F401  — chdir alla radice del repo

import os

import forge
import snapdraw as sd

# --- CONFIG ---------------------------------------------------------------
FOLDER_PATH = r"C:\Users\FEDERICO\Documents\Python_Scripts\Projects\GitHub\forge\tests\examples\islands"
# suffisso del file prodotto, e insieme marcatore per non rimasticare gli
# output di un giro precedente
SUFFIX = "_noframe"
# togliere anche il cartiglio, quando rilevato (la cornice è il riquadro di
# formato, il cartiglio è un riquadro a sé: senza questo resta nel disegno)
REMOVE_TITLE_BLOCK = True
# regole di ruolo al caricamento (rules/<nome>.json, MAP D17)
RULES = "generic"
# ---------------------------------------------------------------------------


def frame_free_edges(doc, layout: sd.FrameLayout) -> list:
    """
    Gli Edge di `doc` che non appartengono a cornice (e cartiglio, se
    `REMOVE_TITLE_BLOCK`). Confronto per identità: `id(edge)`, non per valore —
    due lati distinti possono avere la stessa geometria.
    """
    drop = {id(edge) for edge in layout.frame.edges}
    if REMOVE_TITLE_BLOCK and layout.title_block is not None:
        drop |= {id(edge) for edge in layout.title_block.edges}
    return [edge for edge in doc.edges if id(edge) not in drop]


names = sorted(
    name for name in os.listdir(FOLDER_PATH)
    if name.lower().endswith(".dxf")
    and not os.path.splitext(name)[0].endswith(SUFFIX)
)
print(f"{len(names)} disegni in {FOLDER_PATH}")

done, skipped = 0, 0
for name in names:
    stem = os.path.splitext(name)[0]
    path = os.path.join(FOLDER_PATH, name)
    try:
        doc = forge.load_dxf(path, role_rules=sd.load_rules(RULES))
        layout = sd.detect_frame(doc)

        if layout.frame is None:
            print(f"  [SALTATO] {name}: cornice non rilevata ({', '.join(layout.flags)})")
            skipped += 1
            continue

        f = layout.frame
        kept = frame_free_edges(doc, layout)
        removed = len(doc.edges) - len(kept)
        doc.edges = kept
        result = sd.sheet_islands(doc)
        if not result.is_valid:
            print(f"  [SALTATO] {name}: island non valido dopo la rimozione — {result.errors}")
            skipped += 1
            continue

        out_path = os.path.join(FOLDER_PATH, f"{stem}{SUFFIX}.dxf")
        forge.to_dxf(result, doc).saveas(out_path)
        print(f"  [OK] {name}: -{removed} edge  (formato={f.iso_format}, "
              f"conf={f.confidence:.2f}, cartiglio={'sì' if layout.title_block else 'no'}) "
              f"-> {os.path.basename(out_path)}")
        done += 1
    except (ValueError, OSError) as e:
        print(f"  [SALTATO] {name}: {type(e).__name__} — {e}")
        skipped += 1

print(f"\nfatti {done}/{len(names)} — saltati {skipped}")
