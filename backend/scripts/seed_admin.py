"""Seed all role demo accounts (delegates to seed_roles)."""

import asyncio
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "seed_roles", Path(__file__).resolve().parent / "seed_roles.py"
)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader
_spec.loader.exec_module(_mod)

if __name__ == "__main__":
    asyncio.run(_mod.main())