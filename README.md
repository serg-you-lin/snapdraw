# framer

Automatic detection **and generation** of the **drawing frame** and **title
block** in laid-out technical drawings.

*(Versione italiana: [README_IT.md](README_IT.md))*

## What it is

`framer` is a **consumer of [forge](../forge)**. It recognises two things in
a drawing's geometry:

- the **frame** (`frame`) — the ISO-format border around the sheet;
- the **title block** (`title_block`) — the information box, usually split into
  cells and full of text.

It is not part of forge: forge stays neutral and deterministic and does not
decide what a title block is. framer uses forge's primitives to do the
recognition, assigns the roles (`frame`, `title_block`) and feeds them back down
to forge as input — the same pattern as `label_map` and `detect`.

In the bigger picture framer is a **module of the drawing interpreter** (a
project not built yet), a sibling of the unfolder. It is its own repo because the
problem is large and worth solving on its own.

## Why it is needed

On a drawing with a frame, forge today produces **a single cluster** containing
all the sheet's geometry: the frame is the outermost loop and swallows
everything. framer detects frame and title block **before** `forge.heal`, marks
them, and `heal` excludes them from cluster detection. The real part outlines
emerge; the title block is not a cluster; its texts stay without a `cluster_ref`.

## Usage

```python
import forge, framer

doc = forge.load_dxf("drawing.dxf", role_rules=framer.load_rules("generic"))

layout = framer.detect_frame(doc)    # frame + title block on the raw geometry
fields = framer.read_titleblock(layout)

# only when you need the parts: mark, then pick forge's reading
framer.tag_layout(doc, layout)       # mark the Edges → role="frame" / "title_block"
result = forge.island(doc)           # a sheet of views is read by islands
```

Roles are assigned at load time by rule files in `rules/`, turned into
`forge.RoleRule`s by `framer.load_rules`. `rules/generic.json` holds the
technical-drawing rules for everyone: chain lines (dash-dot: `CENTER`,
`PHANTOM`, ...) are axes and construction lines in ISO 128 and become
`construction`, so they stop gluing views to dimensions. Plain dashed lines
(`HIDDEN`) are hidden edges — real geometry — and are left alone. A studio
or client writes its own rules (layer names included) in
`rules/studio_<name>.json`, kept out of git, and puts them first:

```python
role_rules = framer.load_rules("studio_x") + framer.load_rules("generic")
```

`framer.detect_frame(doc)` is a **recipe**, the same way `forge.heal` is one
(forge D62): it composes public steps — `find_frame(doc)` and
`find_titleblock(doc, frame=...)` — and presumes no forge reading after it.
Compose the steps yourself for a different reading. It returns a
`FrameLayout`:

- `frame` — the frame's bbox, edges and ISO format, or `None`
- `title_block` — the title block's bbox, edges and cells, or `None`
- `flags` — `frame: uncertain`, `title_block: uncertain`, ...

## Generating a frame and title block

The opposite direction: given a drawing that has no frame yet, `add_frame`
adds a standard ISO one around the existing geometry, and `add_title_block`
adds a title block filled with the caller's own data — never stored in this
repo, same principle as forge's `data_injector`.

```python
doc = forge.load_dxf("bare_part.dxf")

framer.add_frame(doc)                                        # ISO frame around the existing geometry
framer.add_title_block(doc, fields={"material": "S235JR", "quantity": "2"})

result = forge.heal(doc)
forge.to_dxf(result, doc).saveas("bare_part_framed.dxf")
```

`add_frame` picks the smallest ISO format and orientation (A4..A0, landscape
or portrait) that fits the existing geometry plus a margin plus room for the
title block — there is no `fmt`/`orientation` parameter to pass. Both
functions are purely forge-native (`forge.load_geometry` + `forge.Note`, no
ezdxf) and tag their own geometry with `role="frame"`/`"title_block"`, so
`heal`/`detect`/`to_dxf` treat it exactly like a detected one. A logo/image
is out of scope for now — forge's neutral model has no concept of an image.

## Hook into forge

framer hooks in with **option B** (forge D30): it sets `edge.role` on the `Edge`
objects of `doc.edges` before `heal`. forge took no new API —
`forge.heal._split_labeled` pulls every decided, non-structural role out of the
graph, and `forge.detect` leaves roles it does not know alone. The frame and
title-block geometry is not lost: it ends up in `trash_entities` with its role
intact and the output DXF re-emits it natively.

Requires forge installed separately:

```
pip install -e ../forge
pip install -e .
```

## Status

Pre-alpha.

- `detect_frame` — the recipe over `find_frame` + `find_titleblock`
- `find_frame` — **ported and working** (it was forge's `frame_detector`,
  removed in forge D24 because it runs before `heal`)
- `find_titleblock` / `read_titleblock` — **working** (thresholds still raw)
- `add_frame` / `add_title_block` — **working**, vector-only (no logo/image yet)

See [TODO.md](TODO.md) and [DESIGN.md](DESIGN.md).
