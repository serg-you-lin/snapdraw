import _paths  # noqa: F401  — chdir alla radice del repo

import os

import forge
import snapdraw as sd

# --- CONFIG ---------------------------------------------------------------
SHEETS = [r"tests/examples/regression/regr_0{}.dxf".format(i) for i in range(1, 6)] + [
    r"tests/examples/rules/vista_pianta_assi.dxf",
]
OUTPUT = r"pipeline_output/features"
RULES  = "generic"
# -----------------------------------------------------------------------------

os.makedirs(OUTPUT, exist_ok=True)
for path in SHEETS:
    name = os.path.splitext(os.path.basename(path))[0]
    doc = forge.load_dxf(path, role_rules=sd.load_rules(RULES))
    sd.tag_layout(doc, sd.detect_frame(doc))
    result = forge.island(doc)
    views = sd.read_views(result)
    features = sd.read_features(doc, result, views)

    print(f"\n{name}: vista principale {views.principal}, scale {features.scales}  {views.flags + features.flags}")
    for f in features.features:
        written = f.callout.text if f.callout else "—"
        traces = [(t.view, t.through, round(t.length, 2)) for t in f.traces]
        print(f"  v{f.view} {f.kind:8s} {f.hole_type or '':12s} {f.shape.length:7.2f}×{f.shape.width:<6.2f} quota {written:14s} "
              f"passante={f.through} ({f.source}) prof. {f.drawn_depth} → {f.depth}  tracce={traces}  {f.flags}")
    print(" ", sd.describe_features(features))

    # la lettura scritta accanto a ogni feature, per giudicarla nel CAD; le feature sui layer del loro ruolo
    for f in features.features:
        kind = {True: "passante", False: "cieco"}.get(f.through, "?")
        depth = f.depth if f.depth is not None else f.drawn_depth
        what = f.callout.text if f.callout else f"{f.shape.length:.2f}×{f.shape.width:.2f}"
        label = f"{f.role} {what} {kind} ({f.source})" + (f" prof. {depth:.2f}" if depth is not None else "")
        x, y = f.center
        result.annotations.append(forge.Note(position=(x + f.shape.length / 2, y + f.shape.width / 2),
                                             source_kind="TEXT", height=1.5, text=label))
    sd.tag_features(result, features)
    out = os.path.join(OUTPUT, name + "_features.dxf")
    forge.to_dxf(result, doc).saveas(out)
    print(f"  scritto {out}")
