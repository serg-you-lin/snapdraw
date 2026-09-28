"""
tests/generate_regression.py
----------------------------
Scrive il golden di ogni foglio in `tests/examples/regression/`:
`json/<nome>.json` con la lettura di `regression_reading.read_sheet`.

Si lancia una volta, quando la lettura è giusta (controllata a occhio sul
DXF). Mai per far passare un test: prima si dimostra che il codice è
giusto, poi si rigenera, un foglio alla volta, guardando il diff. Le
chiavi in `known_wrong` (verità scritta a mano) restano come sono, e resta
l'elenco `unchecked` (letture non ancora controllate).

    python tests/generate_regression.py            # solo i fogli senza golden
    python tests/generate_regression.py --force    # riscrive tutti
    python tests/generate_regression.py --only "leva_01"
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from regression_reading import GOLDEN, REGRESSION, read_sheet  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="riscrive anche i golden esistenti")
    parser.add_argument("--only", help="solo il foglio con questo nome (senza .dxf)")
    args = parser.parse_args()

    GOLDEN.mkdir(parents=True, exist_ok=True)
    for path in sorted(REGRESSION.glob("*.dxf")):
        if args.only and path.stem != args.only:
            continue
        target = GOLDEN / f"{path.stem}.json"
        if target.exists() and not args.force:
            print(f"salto {path.name}: golden già presente (--force per riscriverlo)")
            continue
        reading = read_sheet(path)
        if target.exists():
            # le letture sbagliate note portano la verità scritta a mano: non si riscrivono
            old = json.loads(target.read_text(encoding="utf-8"))
            known_wrong = old.get("known_wrong", {})
            for key in known_wrong:
                reading[key] = old[key]
            if known_wrong:
                reading["known_wrong"] = known_wrong
            if old.get("unchecked"):
                reading["unchecked"] = old["unchecked"]
        target.write_text(json.dumps(reading, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"scritto {target.name}: {reading['clusters']} isole, principale {reading['principal']}, "
              f"feature: {reading['features']['summary'] or '—'}")


if __name__ == "__main__":
    main()
