# framer

Automatic detection of the **drawing frame** and **title block** in laid-out
technical drawings.

*(Versione italiana: [README_IT.md](README_IT.md))*

## What it is

`framer` is a **consumer of [forge](../dxf-forge)**. It recognises two things in
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

doc = forge.load_dxf("drawing.dxf")

layout = framer.detect(doc)          # frame + title block on the raw geometry
framer.tag_layout(doc, layout)       # mark the Edges → role="frame" / "title_block"

result = forge.heal(doc)             # heal excludes frame and title block from clusters
```

`framer.detect(doc)` returns a `FrameLayout`:

- `frame` — the frame's bbox, edges and ISO format, or `None`
- `title_block` — the title block's bbox, edges and cells, or `None`
- `flags` — `frame: uncertain`, `title_block: uncertain`, ...

## Hook into forge

framer hooks in with **option B** (forge D30): it sets `edge.role` on the `Edge`
objects of `doc.edges` before `heal`. forge took no new API —
`forge.heal._split_labeled` pulls every decided, non-structural role out of the
graph, and `forge.detect` leaves roles it does not know alone. The frame and
title-block geometry is not lost: it ends up in `trash_entities` with its role
intact and the output DXF re-emits it natively.

Requires forge installed separately:

```
pip install -e ../dxf-forge
pip install -e .
```

## Status

Pre-alpha.

- `detect_frame` — **ported and working** (it was forge's `frame_detector`,
  removed in forge D24 because it runs before `heal`)
- `detect_titleblock` — **stub**
- `read_titleblock` — **stub**

See [TODO.md](TODO.md) and [DESIGN.md](DESIGN.md).
