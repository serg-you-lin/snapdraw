import _paths  # noqa: F401  — chdir alla radice del repo

import forge
import framer

# --- CONFIG ---------------------------------------------------------------
INPUT  = r"42D025Z00I.DXF"
OUTPUT = r"pipeline_output/42D025Z00I_framed.dxf"
# -----------------------------------------------------------------------------

doc = forge.load_dxf(INPUT)
print(f"edge: {len(doc.edges)}  annotazioni: {len(doc.annotations)}")

layout = framer.detect(doc)
if layout.frame:
    f = layout.frame
    print(f"cornice: bbox={tuple(round(v, 1) for v in f.bbox)}  formato={f.iso_format}  "
          f"contenimento={f.containment:.0%}  conf={f.confidence:.2f}  ({len(f.edges)} edge)")
else:
    print("cornice: non trovata")
print("flag:", layout.flags or "nessuno")

n = framer.tag_layout(doc, layout)
print(f"{n} edge marcati")

result = forge.heal(doc)
print(f"heal: valid={result.is_valid}  cluster={len(result.clusters)}  "
      f"trash={len(result.trash_entities)}")

out = forge.to_dxf(result, doc)

import os
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
out.saveas(OUTPUT)
print(f"scritto {OUTPUT}")
