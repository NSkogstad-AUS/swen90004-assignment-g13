"""CLI for generating SVG plots from experiment CSV outputs."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, os.fspath(PROJECT_ROOT))

from hotelling.plotting import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR, generate_plots  # noqa: E402


EXPERIMENTS = ("baseline", "plane", "sweep", "loyalty", "all")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate SVG plots from Hotelling experiment CSV outputs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--experiment",
        choices=EXPERIMENTS,
        default="all",
        help="Which experiment plots to generate.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Directory containing experiment CSV outputs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write generated SVG plots.",
    )
    args = parser.parse_args()

    generated = generate_plots(
        experiment=args.experiment,
        input_dir=args.input_dir,
        output_dir=args.output_dir,
    )

    if not generated:
        raise SystemExit(
            "No plots were generated. Run the experiments first or point --input-dir at "
            "a folder containing CSV outputs."
        )

    for path in generated:
        print(f"[plots] wrote: {path}")


if __name__ == "__main__":
    main()
