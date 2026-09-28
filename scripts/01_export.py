import _paths  # noqa: F401  — chdir alla radice del repo

import forge
import snapdraw as sd

# --- CONFIG ---------------------------------------------------------------
INPUT  = r"tests/examples/complete_drawings/bend_sheet/singoli_piegati/3d_1.dxf"
OUTPUT = r"pipeline_output/tavola_08_framed.dxf"
RULES  = "generic"   # rules/<nome>.json — uno studio: load_rules("studio_x") + load_rules("generic")
# -----------------------------------------------------------------------------

doc = forge.load_dxf(INPUT, role_rules=sd.load_rules(RULES))
print(f"edge: {len(doc.edges)}  annotazioni: {len(doc.annotations)}")

layout = sd.detect_frame(doc)
if layout.frame:
    f = layout.frame
    print(f"cornice: bbox={tuple(round(v, 1) for v in f.bbox)}  formato={f.iso_format}  "
          f"contenimento={f.containment:.0%}  conf={f.confidence:.2f}  ({len(f.edges)} edge)")
else:
    print("cornice: non trovata")
print("flag:", layout.flags or "nessuno")

n = sd.tag_layout(doc, layout)
m = sum(1 for e in doc.edges if e.role == sd.CONSTRUCTION)
print(f"{n} edge di cornice/cartiglio marcati, {m} linee di costruzione (regole al caricamento)")

# messa in tavola = viste su un foglio: si legge per isole, non con heal
result = forge.island(doc)
print(f"island: valid={result.is_valid}  isole={len(result.clusters)}  "
      f"trash={len(result.trash_entities)}")

# colore/layer di "frame" arrivano dalla registrazione di sd.roles
out = forge.to_dxf(result, doc)

import os
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
out.saveas(OUTPUT)
print(f"scritto {OUTPUT}")
