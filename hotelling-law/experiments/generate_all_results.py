"""
Generate all experiment results in a single pass.

Runs the baseline, replication sweep, and loyalty extension experiments in sequence,
producing all six output CSV files.  This script is invoked by 'python run.py all'.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments.baseline import run_baseline
from experiments.replication_sweep import run_sweep
from experiments.extension_loyalty import run_loyalty


def run_all() -> None:
    """Run all experiments and print a final summary of outputs produced."""
    print("=" * 60)
    print("Hotelling's Law — generating all experiment results")
    print("=" * 60)

    run_baseline()
    print()

    run_sweep()
    print()

    run_loyalty()
    print()

    print("=" * 60)
    print("All experiments complete.  Output files:")
    _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outputs_dir = os.path.join(_project_root, "outputs")
    for fname in sorted(os.listdir(outputs_dir)):
        if fname.endswith(".csv"):
            fpath = os.path.join(outputs_dir, fname)
            print(f"  {fpath}")
    print("=" * 60)


if __name__ == "__main__":
    run_all()
