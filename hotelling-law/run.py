"""Command-line entry point for running Hotelling's Law experiments."""

import argparse
import os
import sys

# Ensure the project root is on sys.path regardless of working directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

COMMANDS = ("baseline", "sweep", "loyalty", "all")


def main() -> None:
    """Parse the command-line argument and dispatch to the appropriate experiment(s)."""
    parser = argparse.ArgumentParser(
        description="Run Hotelling's Law simulation experiments.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "commands:\n"
            "  baseline  Two-store model, 10 runs (outputs/baseline.csv)\n"
            "  sweep     Sweep over num_stores and distance_weight (outputs/parameter_sweep.csv)\n"
            "  loyalty   Compare loyalty_strength values (outputs/extension_loyalty.csv)\n"
            "  all       Run all three experiments\n"
        ),
    )
    parser.add_argument("command", choices=COMMANDS, help="Experiment to run.")
    args = parser.parse_args()

    if args.command in ("baseline", "all"):
        from experiments.baseline import run_baseline
        print("Running baseline experiment...")
        run_baseline()

    if args.command in ("sweep", "all"):
        from experiments.parameter_sweep import run_sweep
        print("Running parameter sweep...")
        run_sweep()

    if args.command in ("loyalty", "all"):
        from experiments.extension_loyalty import run_loyalty
        print("Running loyalty extension experiment...")
        run_loyalty()


if __name__ == "__main__":
    main()
