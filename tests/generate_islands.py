"""
tests/generate_islands.py
-------------------------
Scrive il golden delle isole di ogni foglio in `tests/examples/islands/`:
`json/<nome>.json` con la lettura di `islands_reading.read_islands`.

Si lancia solo quando le isole sono giuste, guardate da Federico sulla
pagina o sul DXF. Mai per far passare un test.

    python tests/generate_islands.py            # solo i fogli senza golden
    python tests/generate_islands.py --force    # riscrive tutti
    python tests/generate_islands.py --only anch_02
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from islands_reading import GOLDEN, ISLANDS, read_islands  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="riscrive anche i golden esistenti")
    parser.add_argument("--only", help="solo il foglio con questo nome (senza .dxf)")
    args = parser.parse_args()

    GOLDEN.mkdir(parents=True, exist_ok=True)
    for path in sorted(ISLANDS.glob("*.dxf")):
        if args.only and path.stem != args.only:
            continue
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
