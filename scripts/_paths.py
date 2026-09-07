# scripts/_paths.py   (underscore = non fa parte del package)
# Import all'inizio di ogni script numerato: fa chdir alla radice del repo, così
# i path relativi in CONFIG risolvono uguale da qualunque CWD.
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent   # scripts/ -> radice repo
os.chdir(ROOT)
