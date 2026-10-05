"""
tests/generate_islands.py
-------------------------
Scrive il golden delle isole di ogni foglio in `tests/examples/islands/`:
`json/<nome>.json` con la lettura di `islands_reading.read_islands`.

Si lancia solo sui fogli con le isole giuste, guardate da Federico sulla
pagina o sul DXF. Mai per far passare un test.

    python tests/generate_islands.py            # solo i fogli senza golden (non `anonymus/`)
    python tests/generate_islands.py --force    # riscrive tutti
    python tests/generate_islands.py --only anch_02,drw_0003
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from islands_reading import GOLDEN, read_islands, sheets  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="riscrive anche i golden esistenti")
    parser.add_argument("--only", help="solo i fogli con questi nomi, separati da virgola (senza .dxf)")
    args = parser.parse_args()

    GOLDEN.mkdir(parents=True, exist_ok=True)
    only = set(args.only.split(",")) if args.only else None
    for path in sheets():
        if only and path.stem not in only:
            continue
        if not only and path.parent.name == "anonymus":
            continue   # fogli non ancora tutti giudicati: solo per nome, con --only
        target = GOLDEN / f"{path.stem}.json"
        if target.exists() and not args.force:
            print(f"salto {path.name}: golden già presente (--force per riscriverlo)")
            continue
        reading = read_islands(path)
        target.write_text(json.dumps(reading, indent=2), encoding="utf-8")
        print(f"scritto {target.name}: {len(reading['islands'])} isole, "
              f"{reading['open_outside']} linee aperte fuori")


if __name__ == "__main__":
    main()
