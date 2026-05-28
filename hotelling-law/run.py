"""
Command-line entry point for the Hotelling's Law simulation.

Usage:
    python run.py baseline   Run the NetLogo line baseline experiment.
    python run.py plane      Run the NetLogo plane baseline experiment.
    python run.py sweep      Run the replication parameter sweep.
    python run.py loyalty    Run the customer loyalty extension experiment.
    python run.py all        Run all experiments in sequence.
    python run.py test       Discover and run all unit tests in tests/.
"""

import argparse
import os
import subprocess
import sys

# Ensure the project root is on sys.path regardless of where the script is invoked.
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _PROJECT_ROOT)

COMMANDS = ("baseline", "plane", "sweep", "loyalty", "all", "test")


def main() -> None:
    """Parse the command-line argument and dispatch to the appropriate experiment(s)."""
    parser = argparse.ArgumentParser(
        description="Run Hotelling's Law simulation experiments.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "commands:\n"
            "  baseline  NetLogo line baseline, 30 runs (outputs/baseline_*.csv)\n"
            "  plane     NetLogo plane baseline, 30 runs (outputs/plane_baseline_*.csv)\n"
            "  sweep     Parameter sweep: num_stores, distance_weight, distribution\n"
            "            (outputs/replication_sweep_*.csv)\n"
            "  loyalty   Customer loyalty extension experiment\n"
            "            (outputs/extension_loyalty_*.csv)\n"
            "  all       Run all experiments\n"
            "  test      Discover and run all unit tests\n"
        ),
    )
    parser.add_argument("command", choices=COMMANDS, help="Command to run.")
    args = parser.parse_args()

    if args.command == "test":
        _run_tests()
        return

    if args.command in ("baseline", "all"):
        from experiments.baseline import run_baseline
        run_baseline()

    if args.command in ("plane", "all"):
        from experiments.plane_baseline import run_plane_baseline
        run_plane_baseline()

    if args.command in ("sweep", "all"):
        from experiments.replication_sweep import run_sweep
        run_sweep()

    if args.command in ("loyalty", "all"):
        from experiments.extension_loyalty import run_loyalty
        run_loyalty()


def _run_tests() -> None:
    """
    Discover and run all unit tests in the tests/ directory.

    Delegates to unittest's built-in discovery mechanism.  Exits with a non-zero
    status code if any tests fail so that CI pipelines can detect failures.
    """
    print("Discovering and running tests in tests/ ...")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=_PROJECT_ROOT,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
