import _paths  # noqa: F401  — chdir alla radice del repo

import forge
import framer

# --- CONFIG ---------------------------------------------------------------
INPUT = r"tests/examples/framed_drawing.dxf"   # relativo -> dalla radice del repo
# INPUT = r"C:\job\disegno_cliente.dxf"        # assoluto -> usato com'è
# -----------------------------------------------------------------------------

doc = forge.load_dxf(INPUT)
print(f"edge: {len(doc.edges)}  annotazioni: {len(doc.annotations)}")

layout = framer.detect(doc)

if layout.frame:
    f = layout.frame
    print(f"cornice: bbox={tuple(round(v, 1) for v in f.bbox)}  "
          f"formato={f.iso_format}  contenimento={f.containment:.0%}  "
          f"confidenza={f.confidence:.2f}  ({len(f.edges)} edge)")
else:
    print("cornice: non trovata")

if layout.title_block:
    print(f"cartiglio: bbox={tuple(round(v, 1) for v in layout.title_block.bbox)}")
else:
    print("cartiglio: non trovato (stub)")

print("flag:", layout.flags or "nessuno")

# marca gli Edge e passa a heal: la cornice viene esclusa dai cluster
n = framer.tag_layout(doc, layout)
print(f"\n{n} edge marcati")

result = forge.heal(doc)
print(f"cluster dopo heal: {len(result.clusters)}")
for i, c in enumerate(result.clusters):
    b = tuple(round(v) for v in c.outer.polygon.bounds)
    print(f"  cluster {i}: area={c.outer.polygon.area:.0f}  bbox={b}  inner={len(c.inners)}")
