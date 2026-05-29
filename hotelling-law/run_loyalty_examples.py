"""
Run a configurable loyalty-strength sweep and generate matching plots.

Example:
    python3 run_loyalty_examples.py --num-stores 3 --steps 100 --runs 30 --loyalty-threshold 20
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, os.fspath(PROJECT_ROOT))

from hotelling.csv_writer import write_raw_csv, write_summary_csv  # noqa: E402
from hotelling.experiment import Experiment  # noqa: E402
from hotelling.plotting import generate_summary_line_plots  # noqa: E402
from hotelling.statistics import generate_summary_rows  # noqa: E402


DEFAULT_STRENGTHS = "0.0,0.25,0.5,0.75"
DEFAULT_THRESHOLD = 20.0
DEFAULT_LAYOUT = "line"
DEFAULT_RULES = "normal"
DEFAULT_MARKET_SIZE = 100
DEFAULT_NUM_CUSTOMERS = 101
DEFAULT_NUM_STORES = 3
DEFAULT_STEPS = 100
DEFAULT_RUNS = 30
DEFAULT_PRICE = 10.0
DEFAULT_DISTANCE_WEIGHT = 1.0
DEFAULT_STEP_SIZE = 1.0
DEFAULT_PRICE_STEP = 1.0
DEFAULT_BASE_SEED = 700
DEFAULT_OUTPUT_PREFIX = "loyalty_examples"


def _parse_strengths(value: str) -> List[float]:
    strengths = [float(part.strip()) for part in value.split(",") if part.strip()]
    if not strengths:
        raise ValueError("at least one loyalty strength is required")
    if any(strength < 0 for strength in strengths):
        raise ValueError("loyalty strengths must be non-negative")
    return strengths


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a loyalty-strength sweep and generate summary plots.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--strengths", default=DEFAULT_STRENGTHS)
    parser.add_argument("--loyalty-threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--layout", choices=("line", "plane"), default=DEFAULT_LAYOUT)
    parser.add_argument(
        "--rules",
        choices=("normal", "moving-only", "pricing-only"),
        default=DEFAULT_RULES,
    )
    parser.add_argument("--market-size", type=int, default=DEFAULT_MARKET_SIZE)
    parser.add_argument("--num-customers", type=int, default=DEFAULT_NUM_CUSTOMERS)
    parser.add_argument("--num-stores", type=int, default=DEFAULT_NUM_STORES)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--price", type=float, default=DEFAULT_PRICE)
    parser.add_argument("--distance-weight", type=float, default=DEFAULT_DISTANCE_WEIGHT)
    parser.add_argument("--step-size", type=float, default=DEFAULT_STEP_SIZE)
    parser.add_argument("--price-step", type=float, default=DEFAULT_PRICE_STEP)
    parser.add_argument("--base-seed", type=int, default=DEFAULT_BASE_SEED)
    parser.add_argument("--output-prefix", default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "outputs",
    )
    parser.add_argument(
        "--plot-dir",
        type=Path,
        default=None,
        help="Directory for generated SVG files. Defaults to <output-dir>/plots.",
    )
    return parser


def _positive_int(value: int, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be greater than 0")


def _positive_float(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be greater than 0")


def main() -> None:
    args = _build_parser().parse_args()

    strengths = _parse_strengths(args.strengths)
    _positive_float(args.loyalty_threshold, "loyalty-threshold")
    _positive_int(args.market_size, "market-size")
    _positive_int(args.num_customers, "num-customers")
    _positive_int(args.num_stores, "num-stores")
    _positive_int(args.steps, "steps")
    _positive_int(args.runs, "runs")

    output_dir = args.output_dir
    plot_dir = args.plot_dir or (output_dir / "plots")
    raw_output = output_dir / f"{args.output_prefix}_raw.csv"
    summary_output = output_dir / f"{args.output_prefix}_summary.csv"

    all_raw: List[Dict] = []
    all_summary: List[Dict] = []
    total = len(strengths)

    for index, loyalty_strength in enumerate(strengths, start=1):
        scenario_name = f"loyalty_{loyalty_strength}"
        print(f"[loyalty-examples] Scenario {index}/{total}: {scenario_name} ...")
        experiment = Experiment(
            experiment_name=args.output_prefix,
            num_runs=args.runs,
            base_seed=args.base_seed,
            market_size=args.market_size,
            num_customers=args.num_customers,
            num_stores=args.num_stores,
            ticks=args.steps,
            price=args.price,
            distance_weight=args.distance_weight,
            step_size=args.step_size,
            price_step=args.price_step,
            layout=args.layout,
            rules=args.rules,
            loyalty_strength=loyalty_strength,
            loyalty_threshold=args.loyalty_threshold,
        )
        raw_rows = experiment.run()
        all_raw.extend(raw_rows)
        all_summary.extend(
            generate_summary_rows(
                rows=raw_rows,
                experiment_name=args.output_prefix,
                scenario_name=scenario_name,
                parameter_name="loyalty_strength",
                parameter_value=loyalty_strength,
            )
        )

    write_raw_csv(os.fspath(raw_output), all_raw)
    write_summary_csv(os.fspath(summary_output), all_summary)

    plot_paths = generate_summary_line_plots(
        summary_output,
        plot_dir,
        args.output_prefix,
        "Loyalty Example",
        "Loyalty strength",
        (
            "distance_from_centre",
            "average_distance_to_other_stores",
            "store_profit",
            "market_share_variation",
        ),
    )

    print(f"[loyalty-examples] Raw output:     {raw_output} ({len(all_raw)} rows)")
    print(f"[loyalty-examples] Summary output: {summary_output} ({len(all_summary)} rows)")
    for path in plot_paths:
        print(f"[loyalty-examples] Plot:          {path}")


if __name__ == "__main__":
    main()
