import _paths  # noqa: F401  — chdir alla radice del repo

import os

import forge
import snapdraw as sd

# --- CONFIG ---------------------------------------------------------------
FOLDER = r"../forge/tests/examples/islands"
NAMES  = ["leva_01", "tavola_02", "tavola_04", "tavola_07", "tavola_05", "tavola_10"]
OUTPUT = r"pipeline_output/holes"
RULES  = "generic"
# -----------------------------------------------------------------------------

os.makedirs(OUTPUT, exist_ok=True)
for name in NAMES:
    doc = forge.load_dxf(os.path.join(FOLDER, name + ".dxf"), role_rules=sd.load_rules(RULES))
    sd.tag_layout(doc, sd.detect_frame(doc))
    result = forge.island(doc)
    views = sd.read_views(result)
    holes = sd.read_holes(doc, result, views)

    print(f"\n{name}: vista principale {views.principal}, profondità {views.depth}, "
          f"scala quote {holes.scale}  {views.flags + holes.flags}")
    for h in holes.holes:
        written = h.callout.text if h.callout else "—"
        traces = [(t.view, t.through, round(t.length, 2)) for t in h.traces]
        print(f"  {h.path}: Ø disegnato {h.drawn_diameter:.3f}  quota {written}  passante={h.through} "
              f"({h.source})  profondità {h.drawn_depth} → {h.depth}  tracce={traces}  {h.flags}")
    print(" ", sd.describe_holes(holes))

    # la lettura scritta accanto a ogni cerchio, per giudicarla nel CAD
    for h in holes.holes:
        kind = {True: "passante", False: "cieco"}.get(h.through, "?")
        depth = h.depth if h.depth is not None else h.drawn_depth
        depth = f"{depth:.2f}" if depth is not None else "?"
        size = h.callout.text if h.callout else f"Ø? ({h.drawn_diameter:.2f} dis.)"
        x, y = h.center
        result.annotations.append(forge.Note(position=(x + h.drawn_diameter / 2, y + h.drawn_diameter / 2),
                                             source_kind="TEXT", height=1.5,
                                             text=f"{size} {kind} ({h.source}) prof. {depth}"))
    path = os.path.join(OUTPUT, name + "_holes.dxf")
    forge.to_dxf(result, doc).saveas(path)
    print(f"  scritto {path}")
