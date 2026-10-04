import _paths  # noqa: F401  — chdir alla radice del repo

import os

import forge
import snapdraw as sd

# --- CONFIG ---------------------------------------------------------------
FOLDER = r"tests/examples/regression"
NAMES  = ["regr_05", "regr_01", "regr_03"]
OUTPUT = r"pipeline_output/views"
RULES  = "generic"
# -----------------------------------------------------------------------------

for name in NAMES:
    doc = forge.load_dxf(os.path.join(FOLDER, name + ".dxf"), role_rules=sd.load_rules(RULES))
    sd.tag_layout(doc, sd.detect_frame(doc))
    views = sd.read_views(forge.island(doc))
    paths = sd.render_views(doc, views, os.path.join(OUTPUT, name))
    print(f"{name}: principale {views.principal}  {views.flags or ''}")
    for view, path in zip(views.views, paths):
        print(f"  {view.index}  {view.kind:12s} {view.width:7.1f} x {view.height:7.1f}  → {path}")
