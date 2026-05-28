"""Repo-root wrapper for hotelling-law/plot_results.py."""

import runpy
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent / "hotelling-law" / "plot_results.py"


if __name__ == "__main__":
    runpy.run_path(SCRIPT, run_name="__main__")
