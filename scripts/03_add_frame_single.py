import _paths  # noqa: F401  — chdir alla radice del repo

import os

import forge
import framer

# --- CONFIG ---------------------------------------------------------------
INPUT_PATH = r"tests/examples/to_add_frame/2_parti_saldate.dxf"
OUTPUT_DIR = "pipeline_output"
# ---------------------------------------------------------------------------

doc = forge.load_dxf(INPUT_PATH)
framer.add_frame(doc)
result = forge.heal(doc)
if not result.is_valid:
    raise SystemExit(f"heal non valido: {result.errors}")

out = forge.to_dxf(result, doc)
os.makedirs(OUTPUT_DIR, exist_ok=True)
stem = os.path.splitext(os.path.basename(INPUT_PATH))[0]
out_path = os.path.join(OUTPUT_DIR, f"{stem}_framed.dxf")
out.saveas(out_path)
print(f"[OK] {INPUT_PATH} -> {out_path}")
