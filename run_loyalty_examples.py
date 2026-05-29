"""Repo-root wrapper for hotelling-law/run_loyalty_examples.py."""

import runpy
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent / "hotelling-law" / "run_loyalty_examples.py"


if __name__ == "__main__":
    runpy.run_path(SCRIPT, run_name="__main__")
