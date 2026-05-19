"""
Baseline experiment: two-store Hotelling's Law model over 30 independent runs.

Purpose:
    Demonstrate basic store convergence and competition under default parameters.
    Provides raw per-tick data and final-tick summary statistics for comparison
    against the NetLogo reference model.

Outputs:
    outputs/baseline_raw.csv     - one row per store per tick per run
    outputs/baseline_summary.csv - final-tick summary statistics across runs
"""

import os
import sys

# Allow running directly from the experiments/ directory or from the project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hotelling.experiment import Experiment
from hotelling.statistics import generate_summary_rows
from hotelling.csv_writer import write_raw_csv, write_summary_csv

# --- Output paths (absolute, relative to project root) ---
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_OUTPUT = os.path.join(_PROJECT_ROOT, "outputs", "baseline_raw.csv")
SUMMARY_OUTPUT = os.path.join(_PROJECT_ROOT, "outputs", "baseline_summary.csv")

# --- Experiment configuration ---
EXPERIMENT_NAME = "baseline"
NUM_RUNS = 30
BASE_SEED = 100

# --- Default model parameters matching the NetLogo baseline ---
MARKET_SIZE = 100
NUM_CUSTOMERS = 100
NUM_STORES = 2
TICKS = 100
PRICE = 10.0
DISTANCE_WEIGHT = 1.0
STEP_SIZE = 1.0
CUSTOMER_DISTRIBUTION = "uniform"
LOYALTY_STRENGTH = 0.0
LOYALTY_THRESHOLD = 10.0


def run_baseline() -> None:
    """
    Run the baseline two-store experiment and write raw and summary CSV files.

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
        distance_weight=DISTANCE_WEIGHT,
        step_size=STEP_SIZE,
        customer_distribution=CUSTOMER_DISTRIBUTION,
        loyalty_strength=LOYALTY_STRENGTH,
        loyalty_threshold=LOYALTY_THRESHOLD,
    )
    raw_rows = experiment.run()

    # Write raw CSV.
    write_raw_csv(RAW_OUTPUT, raw_rows)
    print(f"[baseline] Raw output:     {RAW_OUTPUT}  ({len(raw_rows)} rows)")

    # Generate and write summary CSV.
    summary_rows = generate_summary_rows(
        rows=raw_rows,
        experiment_name=EXPERIMENT_NAME,
        scenario_name="baseline_default",
        parameter_name="configuration",
        parameter_value="default",
    )
    write_summary_csv(SUMMARY_OUTPUT, summary_rows)
    print(f"[baseline] Summary output: {SUMMARY_OUTPUT}  ({len(summary_rows)} rows)")


if __name__ == "__main__":
    run_baseline()
