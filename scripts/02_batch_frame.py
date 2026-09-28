import _paths  # noqa: F401  — chdir alla radice del repo

import re

import forge
import snapdraw as sd

# --- CONFIG ---------------------------------------------------------------
INPUT_DIR  = "tests/examples/to_add_frame"
OUTPUT_DIR = "pipeline_output/framed"
# nome file: {drawing_number}_{position}_{material}_SP{thickness}_Q{quantity}[_X]
# convenzione di QUESTO cliente/cartella — non è un formato generico, per
# questo il parsing sta nello script e non in snapdraw/ (DESIGN.md, "cosa NON
# ci va": nomenclatura di un singolo cliente mai nel modulo pubblico).
FILENAME_PATTERN = re.compile(
    r"^(?P<drawing_number>.+?)_(?P<position>P\d+)_(?P<material>[A-Za-z0-9]+)"
    r"_SP(?P<thickness>[\d.]+)_Q(?P<quantity>\d+)(?:_X)?$"
)
# ---------------------------------------------------------------------------

import os
os.makedirs(OUTPUT_DIR, exist_ok=True)

paths = sorted(p for p in os.listdir(INPUT_DIR) if p.lower().endswith(".dxf"))
print(f"{len(paths)} disegni in {INPUT_DIR}")

ok, skipped = 0, 0
for name in paths:
    stem = os.path.splitext(name)[0]
    match = FILENAME_PATTERN.match(stem)
    if not match:
        print(f"  [SALTATO] {name}: nome file non riconosciuto dal pattern")
        skipped += 1
        continue
    parsed = match.groupdict()
    fields = {
        "drawing_number": parsed["drawing_number"],
        "position":       parsed["position"],
        "material":       parsed["material"],
        "thickness":      f"{parsed['thickness']} mm",
        "quantity":       f"{parsed['quantity']} pz",
    }

    path = os.path.join(INPUT_DIR, name)
    try:
        doc = forge.load_dxf(path)
        sd.add_frame(doc)
        sd.add_title_block(doc, fields=fields)
        result = forge.heal(doc)
        if not result.is_valid:
            print(f"  [SALTATO] {name}: heal non valido — {result.errors}")
            skipped += 1
            continue
        out = forge.to_dxf(result, doc)
        out_path = os.path.join(OUTPUT_DIR, f"{stem}_framed.dxf")
        out.saveas(out_path)
        print(f"  [OK] {name} -> {out_path}  ({fields['material']}, SP {parsed['thickness']}, Q{parsed['quantity']})")
        ok += 1
    except ValueError as e:
        print(f"  [SALTATO] {name}: {e}")
        skipped += 1

print(f"\nfatti {ok}/{len(paths)} — saltati {skipped}")
