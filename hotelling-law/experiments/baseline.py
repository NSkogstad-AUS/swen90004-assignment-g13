"""
Baseline experiment aligned to the NetLogo line variant where supported.

Purpose:
    Demonstrate basic store convergence and competition under default parameters.
    Provides raw per-tick data and final-tick summary statistics for comparison
    against the NetLogo reference model.

Outputs:
    outputs/baseline_raw.csv     - one row per store per tick per run
    outputs/baseline_raw_2.csv   - one final-tick row per store per run
    outputs/baseline_summary.csv - final-tick summary statistics across runs
"""

import os
import sys

# Allow running directly from the experiments/ directory or from the project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hotelling.experiment import Experiment
from hotelling.statistics import generate_summary_rows
from hotelling.csv_writer import write_final_tick_raw_csv, write_raw_csv, write_summary_csv

# --- Output paths (absolute, relative to project root) ---
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_OUTPUT = os.path.join(_PROJECT_ROOT, "outputs", "baseline_raw.csv")
FINAL_TICK_RAW_OUTPUT = os.path.join(_PROJECT_ROOT, "outputs", "baseline_raw_2.csv")
SUMMARY_OUTPUT = os.path.join(_PROJECT_ROOT, "outputs", "baseline_summary.csv")

# --- Experiment configuration ---
EXPERIMENT_NAME = "baseline"
NUM_RUNS = 30
BASE_SEED = 100

# --- Default model parameters matching the NetLogo line configuration.
# We mirror the NetLogo world height/width of -20..20 with a 1D market of
# 41 integer positions and one customer per position.
# Extension-specific parameters such as distance_weight, customer_distribution,
# and loyalty controls are intentionally omitted here so the baseline only sets
# parameters that correspond to the original NetLogo controls.
MARKET_SIZE = 40
NUM_CUSTOMERS = 41
NUM_STORES = 3
TICKS = 100
PRICE = 10.0
STEP_SIZE = 1.0
PRICE_STEP = 1.0
LAYOUT = "line"
RULES = "normal"


def run_baseline() -> None:
    """
    Run the baseline experiment and write raw and summary CSV files.

    Uses 30 runs for statistical reliability.  Seeds are deterministic and recorded
    in the raw CSV so results are reproducible.
    """
    print(f"[baseline] Running {NUM_RUNS} replications ...")

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

    # Write raw CSV.
    write_raw_csv(RAW_OUTPUT, raw_rows)
    print(f"[baseline] Raw output:     {RAW_OUTPUT}  ({len(raw_rows)} rows)")

    write_final_tick_raw_csv(FINAL_TICK_RAW_OUTPUT, raw_rows)
    final_tick_row_count = NUM_RUNS * NUM_STORES
    print(
        f"[baseline] Raw output 2:   {FINAL_TICK_RAW_OUTPUT}  "
        f"({final_tick_row_count} rows)"
    )

    # Generate and write summary CSV.
    summary_rows = generate_summary_rows(
        rows=raw_rows,
        experiment_name=EXPERIMENT_NAME,
        scenario_name="baseline_netlogo_line",
        parameter_name="configuration",
        parameter_value="default",
    )
    write_summary_csv(SUMMARY_OUTPUT, summary_rows)
    print(f"[baseline] Summary output: {SUMMARY_OUTPUT}  ({len(summary_rows)} rows)")


if __name__ == "__main__":
    run_baseline()
