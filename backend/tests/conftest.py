import sys
import os

# Ensure the project root (parent of backend/) is on the path so that
# both `backend.app.*` (used by COMET modules) resolve correctly.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
