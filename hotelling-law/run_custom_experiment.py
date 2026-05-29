"""
Configurable CLI runner for one-off Hotelling's Law experiments.

Examples:
    python3 run_custom_experiment.py --layout line --rules normal --num-stores 3 --steps 100 --runs 30
    python3 run_custom_experiment.py --layout plane --rules pricing-only --num-stores 4 --steps 50 --runs 10
    python3 run_custom_experiment.py --layout line --num-stores 3 --loyalty-strength 0.75 --loyalty-threshold 20 --output-prefix loyalty_example
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Optional

# Ensure imports work when the script is run from either repo root or hotelling-law/.
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from hotelling.csv_writer import (  # noqa: E402
    write_final_tick_raw_csv,
    write_netlogo_table_csv,
    write_raw_csv,
    write_summary_csv,
)
from hotelling.experiment import Experiment  # noqa: E402
from hotelling.statistics import generate_summary_rows  # noqa: E402


DEFAULT_MARKET_SIZE = 40
DEFAULT_NUM_STORES = 3
DEFAULT_STEPS = 100
DEFAULT_RUNS = 30
DEFAULT_PRICE = 10.0
DEFAULT_STEP_SIZE = 1.0
DEFAULT_PRICE_STEP = 1.0
DEFAULT_BASE_SEED = 500
DEFAULT_LOYALTY_STRENGTH = 0.0
DEFAULT_LOYALTY_THRESHOLD = 10.0


def _default_num_customers(layout: str, market_size: int) -> int:
    """Return the NetLogo-equivalent customer count for the selected layout."""
    patches_per_axis = market_size + 1
    if layout == "plane":
        return patches_per_axis * patches_per_axis
    return patches_per_axis


def _safe_filename(value: str) -> str:
    """Make a readable filename component from CLI values."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")


def _default_prefix(
    layout: str,
    rules: str,
    num_stores: int,
    steps: int,
    runs: int,
    loyalty_strength: float,
    loyalty_threshold: float,
) -> str:
    rules_name = _safe_filename(rules.replace("-", "_"))
    loyalty_suffix = ""
    if (
        loyalty_strength != DEFAULT_LOYALTY_STRENGTH
        or loyalty_threshold != DEFAULT_LOYALTY_THRESHOLD
    ):
        loyalty_suffix = (
            f"_loyalty{loyalty_strength:g}_threshold{loyalty_threshold:g}"
        )
    return (
        f"custom_{layout}_stores{num_stores}_{rules_name}_steps{steps}_runs{runs}"
        f"{loyalty_suffix}"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a configurable Hotelling's Law experiment.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--layout", choices=("line", "plane"), default="line")
    parser.add_argument(
        "--rules",
        choices=("normal", "moving-only", "pricing-only"),
        default="normal",
    )
    parser.add_argument("--num-stores", type=int, default=DEFAULT_NUM_STORES)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--market-size", type=int, default=DEFAULT_MARKET_SIZE)
    parser.add_argument(
        "--num-customers",
        type=int,
        default=None,
        help="Override customer count. If omitted, NetLogo layout defaults are used.",
    )
    parser.add_argument("--base-seed", type=int, default=DEFAULT_BASE_SEED)
    parser.add_argument("--price", type=float, default=DEFAULT_PRICE)
    parser.add_argument("--step-size", type=float, default=DEFAULT_STEP_SIZE)
    parser.add_argument("--price-step", type=float, default=DEFAULT_PRICE_STEP)
    parser.add_argument(
        "--loyalty-strength",
        type=float,
        default=DEFAULT_LOYALTY_STRENGTH,
        help="Customer loyalty weight. Use 0.0 for baseline behaviour.",
    )
    parser.add_argument(
        "--loyalty-threshold",
        type=float,
        default=DEFAULT_LOYALTY_THRESHOLD,
        help="Switching margin used by the loyalty rule.",
    )
    parser.add_argument(
        "--output-prefix",
        default=None,
        help="Output filename prefix. If omitted, a prefix is generated from the config.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "outputs",
        help="Directory for generated CSV files.",
    )
    return parser


def _positive_int(value: int, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be greater than 0")


def _non_negative_float(value: float, name: str) -> None:
    if value < 0:
        raise ValueError(f"{name} must be greater than or equal to 0")


def _positive_float(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be greater than 0")


def run_custom_experiment(argv: Optional[list[str]] = None) -> None:
    args = _build_parser().parse_args(argv)

    _positive_int(args.market_size, "market-size")
    _positive_int(args.num_stores, "num-stores")
    _positive_int(args.steps, "steps")
    _positive_int(args.runs, "runs")
    if args.num_customers is not None:
        _positive_int(args.num_customers, "num-customers")
    _non_negative_float(args.loyalty_strength, "loyalty-strength")
    _positive_float(args.loyalty_threshold, "loyalty-threshold")

    num_customers = args.num_customers or _default_num_customers(
        args.layout,
        args.market_size,
    )
    output_prefix = args.output_prefix or _default_prefix(
        args.layout,
        args.rules,
        args.num_stores,
        args.steps,
        args.runs,
        args.loyalty_strength,
        args.loyalty_threshold,
    )
    output_prefix = _safe_filename(output_prefix)
    output_dir = args.output_dir

    raw_output = output_dir / f"{output_prefix}_raw.csv"
    final_tick_output = output_dir / f"{output_prefix}_raw_2.csv"
    summary_output = output_dir / f"{output_prefix}_summary.csv"
    netlogo_output = output_dir / f"{output_prefix}_summary_netlogo.csv"

    experiment_name = output_prefix
    scenario_name = (
        f"{args.layout}_stores{args.num_stores}_{args.rules}_steps{args.steps}"
    )
    parameter_value = (
        f"layout={args.layout};rules={args.rules};num_stores={args.num_stores};"
        f"steps={args.steps};runs={args.runs};market_size={args.market_size};"
        f"num_customers={num_customers};loyalty_strength={args.loyalty_strength};"
        f"loyalty_threshold={args.loyalty_threshold}"
    )

    print(f"[custom] layout:        {args.layout}")
    print(f"[custom] rules:         {args.rules}")
    print(f"[custom] stores:        {args.num_stores}")
    print(f"[custom] steps:         {args.steps}")
    print(f"[custom] runs:          {args.runs}")
    print(f"[custom] market size:   {args.market_size}")
    print(f"[custom] customers:     {num_customers}")
    print(f"[custom] loyalty str:   {args.loyalty_strength}")
    print(f"[custom] loyalty thr:   {args.loyalty_threshold}")
    print(f"[custom] base seed:     {args.base_seed}")
    print("[custom] running experiment ...")

    experiment = Experiment(
        experiment_name=experiment_name,
        num_runs=args.runs,
        base_seed=args.base_seed,
        market_size=args.market_size,
        num_customers=num_customers,
        num_stores=args.num_stores,
        ticks=args.steps,
        price=args.price,
        step_size=args.step_size,
        price_step=args.price_step,
        layout=args.layout,
        rules=args.rules,
        loyalty_strength=args.loyalty_strength,
        loyalty_threshold=args.loyalty_threshold,
    )

    raw_rows = experiment.run()
    summary_rows = generate_summary_rows(
        rows=raw_rows,
        experiment_name=experiment_name,
        scenario_name=scenario_name,
        parameter_name="configuration",
        parameter_value=parameter_value,
    )

    write_raw_csv(os.fspath(raw_output), raw_rows)
    write_final_tick_raw_csv(os.fspath(final_tick_output), raw_rows)
    write_summary_csv(os.fspath(summary_output), summary_rows)
    write_netlogo_table_csv(
        os.fspath(netlogo_output),
        raw_rows,
        include_plane_metrics=args.layout == "plane",
    )

    print(f"[custom] raw output:     {raw_output} ({len(raw_rows)} rows)")
    print(
        f"[custom] raw output 2:   {final_tick_output} "
        f"({args.runs * args.num_stores} rows)"
    )
    print(f"[custom] summary output: {summary_output} ({len(summary_rows)} rows)")
    print(f"[custom] NetLogo table:  {netlogo_output} ({args.runs} rows)")


if __name__ == "__main__":
    run_custom_experiment()
