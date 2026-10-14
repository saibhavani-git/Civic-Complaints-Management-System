"""Legacy entry point — use seed_demo_data.py for full demo accounts and complaints."""

import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import importlib.util

_spec = importlib.util.spec_from_file_location(
    "seed_demo_data", Path(__file__).resolve().parent / "seed_demo_data.py"
)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader
_spec.loader.exec_module(_mod)

if __name__ == "__main__":
    asyncio.run(_mod.seed_all())
