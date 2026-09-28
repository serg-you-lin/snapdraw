import _paths  # noqa: F401  — chdir alla radice del repo

import forge
import snapdraw as sd

# --- CONFIG ---------------------------------------------------------------
INPUT = r"42D025Z00I.DXF"   # relativo -> dalla radice del repo
# INPUT = r"C:\job\disegno_cliente.dxf"        # assoluto -> usato com'è
# -----------------------------------------------------------------------------

doc = forge.load_dxf(INPUT)
print(f"edge: {len(doc.edges)}  annotazioni: {len(doc.annotations)}")

layout = sd.detect_frame(doc)

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
    print("cartiglio: non trovato")

print("flag:", layout.flags or "nessuno")

# la ricetta si ferma qui: nessuna lettura di forge a valle. Per marcare gli
# Edge e scrivere un DXF (heal o island, scelta del chiamante) vedi 01_export.py.
if layout.title_block:
    fields = sd.read_titleblock(layout)
    for name, field in fields.items():
        if name != "unresolved" and field["value"]:
            print(f"  {name}: {field['value']}")
