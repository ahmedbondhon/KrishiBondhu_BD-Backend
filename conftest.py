import os
import sys
from pathlib import Path

# Add backend directory to sys.path so 'app' can be imported anywhere
backend_path = Path(__file__).resolve().parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))
