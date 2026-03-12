# tests/conftest.py
import os
import sys

# Add the project root (parent of tests) to sys.path so `import bank` works
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)