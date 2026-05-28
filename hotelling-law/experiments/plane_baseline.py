"""
Plane baseline experiment aligned to the NetLogo plane configuration.

Outputs:
    outputs/plane_baseline_raw.csv     - one row per store per tick per run
    outputs/plane_baseline_raw_2.csv   - one final-tick row per store per run
    outputs/plane_baseline_summary.csv - final-tick summary statistics across runs
    outputs/plane_baseline_summary_netlogo.csv - BehaviorSpace-style rows per run
"""

import os
import sys

# Allow running directly from the experiments/ directory or from the project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hotelling.experiment import Experiment
from hotelling.statistics import generate_summary_rows
from hotelling.csv_writer import (
    write_final_tick_raw_csv,
    write_netlogo_table_csv,
    write_raw_csv,
    write_summary_csv,
)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_OUTPUT = os.path.join(_PROJECT_ROOT, "outputs", "plane_baseline_raw.csv")
FINAL_TICK_RAW_OUTPUT = os.path.join(_PROJECT_ROOT, "outputs", "plane_baseline_raw_2.csv")
SUMMARY_OUTPUT = os.path.join(_PROJECT_ROOT, "outputs", "plane_baseline_summary.csv")
NETLOGO_TABLE_OUTPUT = os.path.join(
    _PROJECT_ROOT, "outputs", "plane_baseline_summary_netlogo.csv"
)

EXPERIMENT_NAME = "plane_baseline"
NUM_RUNS = 30
BASE_SEED = 400

# NetLogo default view is -20..20 in both x and y.
MARKET_SIZE = 40
CONSUMERS_PER_AXIS = MARKET_SIZE + 1
NUM_CUSTOMERS = CONSUMERS_PER_AXIS * CONSUMERS_PER_AXIS
NUM_STORES = 3
TICKS = 100
PRICE = 10.0
STEP_SIZE = 1.0
PRICE_STEP = 1.0
LAYOUT = "plane"
RULES = "normal"


def run_plane_baseline() -> None:
    """Run the NetLogo-style plane baseline and write comparison CSV files."""
    print(f"[plane] Running {NUM_RUNS} replications ...")

    experiment = Experiment(
        experiment_name=EXPERIMENT_NAME,
        num_runs=NUM_RUNS,
        base_seed=BASE_SEED,
        market_size=MARKET_SIZE,
        num_customers=NUM_CUSTOMERS,
        num_stores=NUM_STORES,
        ticks=TICKS,
        price=PRICE,
        step_size=STEP_SIZE,
        price_step=PRICE_STEP,
        layout=LAYOUT,
        rules=RULES,
    )
    raw_rows = experiment.run()

    write_raw_csv(RAW_OUTPUT, raw_rows)
    print(f"[plane] Raw output:     {RAW_OUTPUT}  ({len(raw_rows)} rows)")

    write_final_tick_raw_csv(FINAL_TICK_RAW_OUTPUT, raw_rows)
    final_tick_row_count = NUM_RUNS * NUM_STORES
    print(
        f"[plane] Raw output 2:   {FINAL_TICK_RAW_OUTPUT}  "
        f"({final_tick_row_count} rows)"
    )

    summary_rows = generate_summary_rows(
        rows=raw_rows,
        experiment_name=EXPERIMENT_NAME,
        scenario_name="baseline_netlogo_plane",
        parameter_name="configuration",
        parameter_value="default",
    )
    write_summary_csv(SUMMARY_OUTPUT, summary_rows)
    print(f"[plane] Summary output: {SUMMARY_OUTPUT}  ({len(summary_rows)} rows)")

    write_netlogo_table_csv(NETLOGO_TABLE_OUTPUT, raw_rows, include_plane_metrics=True)
    print(
        f"[plane] NetLogo table:   {NETLOGO_TABLE_OUTPUT}  "
        f"({NUM_RUNS} rows)"
    )


if __name__ == "__main__":
    run_plane_baseline()
