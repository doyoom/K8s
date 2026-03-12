import sys
from pathlib import Path


# Make repo root importable for simple portfolio CI runs.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

