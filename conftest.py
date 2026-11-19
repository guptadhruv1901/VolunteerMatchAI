"""Make the backend package importable when pytest runs from repository root."""
import sys
from pathlib import Path

backend = Path(__file__).parent / "backend"
if str(backend) not in sys.path:
    sys.path.insert(0, str(backend))
