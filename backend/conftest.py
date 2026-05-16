"""Pytest bootstrap for the backend package.

Mirrors the runtime sys.path setup that `scripts/refresh_cache.py` and
`reflection/__main__.py` perform: agents/synthesizer/runner modules import
their siblings without a `backend.` prefix (e.g. `from reflection.lesson_store
import ...`), so pytest needs `backend/` on sys.path before those modules
load.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
