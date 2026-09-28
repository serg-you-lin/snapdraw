"""
snapdraw/rules.py
-----------------
Le regole di ruolo di snapdraw: file JSON in `rules/` → `forge.RoleRule`, da
passare a `forge.load_dxf(role_rules=...)` (forge D63/D64: forge dà il
meccanismo, il vocabolario è del chiamante).

Stesso schema delle calibrazioni di bendly: un file per insieme di regole,
nel repo solo `rules/generic.json` (il disegno tecnico, per tutti), i file
di studio/cliente (`studio_*.json`, `cliente_*.json`) fuori da git. Ogni
file è completo, nessuna ereditarietà (bendly D5): uno studio **compone**
le sue regole con quelle generiche nello script, in chiaro, e le sue vanno
prima perché vince la prima che corrisponde (MAP D17):

    role_rules = sd.load_rules("studio_x") + sd.load_rules("generic")
    doc = forge.load_dxf("disegno.dxf", role_rules=role_rules)

Formato:

    {
      "name": "generic",
      "description": "...",
      "rules": [
        {"role": "construction", "dash": "chain"},
        {"role": "construction", "name_contains": ["axis", "assi"]}
      ]
    }

Ogni regola ha i campi di `forge.RoleRule` (`role`, `name`,
`name_contains`, `dashed`, `dash`, `color`). `name` e `name_contains`
accettano anche una lista: diventa una regola per voce, nell'ordine dato.
Un campo sconosciuto alza `ValueError` — un refuso nel JSON non deve
diventare una regola che non matcha mai in silenzio.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Union

import forge

RULES_FOLDER = Path(__file__).resolve().parent.parent / "rules"

_RULE_FIELDS = {"role", "name", "name_contains", "dashed", "dash", "color"}
_LIST_FIELDS = ("name", "name_contains")


def load_rules(name: str, folder: Optional[Union[str, Path]] = None) -> List[forge.RoleRule]:
    """
    Legge `<folder>/<name>.json` (default `rules/` del repo) e ritorna le
    sue regole come `forge.RoleRule`, nell'ordine del file.
    """
    folder = Path(folder) if folder is not None else RULES_FOLDER
    path = folder / f"{name}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return rules_from_dict(data, source=str(path))


def rules_from_dict(data: dict, source: str = "<dict>") -> List[forge.RoleRule]:
    """Come `load_rules`, da un dict già letto."""
    rules: List[forge.RoleRule] = []
    for i, entry in enumerate(data.get("rules", [])):
        unknown = set(entry) - _RULE_FIELDS
        if unknown:
            raise ValueError(f"{source}, regola {i}: campi sconosciuti {sorted(unknown)} "
                             f"— validi: {sorted(_RULE_FIELDS)}")
        rules.extend(_expand(entry))
    return rules


def _expand(entry: dict) -> List[forge.RoleRule]:
    """Una voce del JSON → una o più RoleRule (una per elemento di una lista)."""
    for key in _LIST_FIELDS:
        value = entry.get(key)
        if isinstance(value, list):
            return [r for v in value for r in _expand({**entry, key: v})]
    return [forge.RoleRule(**entry)]
