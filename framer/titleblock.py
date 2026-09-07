"""
framer/titleblock.py
--------------------
Rilevamento del cartiglio e lettura delle sue celle.

STUB — la delimitazione del cartiglio e la lettura dei campi non sono ancora
implementate. Le firme e i tipi di ritorno sono quelli definitivi (vedi
FRAMER.md e DESIGN.md); il corpo è conservativo: ritorna None / dict vuoto,
così `detect()` mette "title_block: uncertain" nei flag e non marca niente.
"""

from __future__ import annotations

from typing import Optional

from .model import FrameInfo, TitleBlock


def detect_titleblock(doc, frame: Optional[FrameInfo] = None) -> Optional[TitleBlock]:
    """
    Delimita il cartiglio nella geometria grezza di `doc`.

    Il cartiglio **non è per forza dentro una cornice**: se `frame` è dato la
    sua posizione è un segnale in più (di solito il cartiglio sta in un angolo
    della cornice, in basso a destra), non un prerequisito.

    Segnali da combinare (nessuno sufficiente da solo — vedi DESIGN.md):
      - rettangolo chiuso suddiviso da linee interne in una griglia di celle;
      - racchiude un gruppo denso di annotazioni (incrocio con `doc.annotations`);
      - dimensioni tipiche da cartiglio, piccolo rispetto all'estensione totale;
      - se la cornice c'è: dentro la sua bbox, di solito in un angolo;
      - opzionale: nome di blocco noto se l'adapter lo espone.

    Conservativo: nel dubbio ritorna None.

    STUB — ritorna sempre None.
    """
    return None


def read_titleblock(layout) -> dict:
    """
    Legge le celle del cartiglio → dict dei campi
    (`{material, drawing_number, revision, scale, ...}`), ognuno con `source` e
    `confidence`; `None` + voce in `unresolved` dove non legge.

    Sta **in framer** (MAP D4): framer delimita il cartiglio e ne legge i
    valori; l'interprete è solo un orchestratore e non fa lavoro geometrico.

    STUB — ritorna un dict vuoto.
    """
    return {}
