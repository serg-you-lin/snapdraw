import _paths  # noqa: F401  — chdir alla radice del repo

import glob
import os
from collections import Counter

import forge

# --- CONFIG ---------------------------------------------------------------
FOLDER = r"tests/examples/regression"
# -----------------------------------------------------------------------------

# Quello che resta di testuale in un disegno ripulito, così come lo legge
# forge: testi e quote, layer delle annotazioni, provenienza, tipi di linea.
# forge non conserva i layer degli edge, i nomi dei blocchi né l'header oltre
# alle unità: quelli si puliscono nel CAD (purge, rinomina layer).

for path in sorted(glob.glob(os.path.join(FOLDER, "*.dxf"))):
    doc = forge.load_dxf(path)
    print(f"\n=== {os.path.basename(path)}")
    texts = Counter(a.display_text.strip() for a in doc.annotations if a.display_text.strip())
    print(f"  testi ({len(texts)} diversi):")
    for text, n in sorted(texts.items()):
        print(f"    {n:3d} × {text}")
    print("  layer delle annotazioni:", sorted({a.layer for a in doc.annotations}))
    print("  provenienza:", sorted({str(a.origin) for a in doc.annotations if a.origin})[:20])
    print("  tipi di linea:", sorted({(e.style.linetype, e.style.linetype_desc) for e in doc.edges if e.style}))
    print("  header:", doc.source_meta)
