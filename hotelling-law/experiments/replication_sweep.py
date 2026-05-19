"""
Replication parameter sweep experiment.

Purpose:
    Support behavioural comparison against the NetLogo Hotelling's Law model by
    running the Python model across key parameter variations.  Shows how store
    clustering, market share, and profit change as parameters change.

Swept parameters:
    num_stores:            2, 4, 6
    distance_weight:       0.5, 1.0, 2.0
    customer_distribution: uniform, clustered

For each combination: 30 independent runs, 100 ticks each.

Outputs:
    outputs/replication_sweep_raw.csv     - one row per store per tick per run
    outputs/replication_sweep_summary.csv - final-tick summary statistics per scenario
"""

import os
import sys
from itertools import product
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hotelling.experiment import Experiment
from hotelling.statistics import generate_summary_rows
from hotelling.csv_writer import write_raw_csv, write_summary_csv

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_OUTPUT = os.path.join(_PROJECT_ROOT, "outputs", "replication_sweep_raw.csv")
SUMMARY_OUTPUT = os.path.join(_PROJECT_ROOT, "outputs", "replication_sweep_summary.csv")

EXPERIMENT_NAME = "replication_sweep"
NUM_RUNS = 30
BASE_SEED = 200
TICKS = 100

# --- Fixed parameters (held constant while others are swept) ---
MARKET_SIZE = 100
NUM_CUSTOMERS = 100
PRICE = 10.0
STEP_SIZE = 2.0
LOYALTY_STRENGTH = 0.0
LOYALTY_THRESHOLD = 10.0

# --- Swept parameter values ---
NUM_STORES_VALUES = [2, 4, 6]
DISTANCE_WEIGHT_VALUES = [0.5, 1.0, 2.0]
DISTRIBUTION_VALUES = ["uniform", "clustered"]


def _make_scenario_name(num_stores: int, distance_weight: float, distribution: str) -> str:
    """Return a compact scenario label encoding all three swept parameters."""
    return f"stores{num_stores}_dw{distance_weight}_dist{distribution}"


def run_sweep() -> None:
    """
    Run all parameter sweep scenarios and write raw and summary CSV files.

    Iterates over the full factorial combination of num_stores, distance_weight,
    and customer_distribution.  All results are concatenated into a single raw CSV
    and a single summary CSV, distinguished by experiment_name and scenario_name.
    """
    all_raw: List[Dict] = []
    all_summary: List[Dict] = []

    # Full factorial sweep: 3 * 3 * 2 = 18 scenarios.
    scenarios = list(product(NUM_STORES_VALUES, DISTANCE_WEIGHT_VALUES, DISTRIBUTION_VALUES))
    total = len(scenarios)

    for idx, (num_stores, distance_weight, distribution) in enumerate(scenarios, start=1):
        scenario_name = _make_scenario_name(num_stores, distance_weight, distribution)
        print(f"[sweep] Scenario {idx}/{total}: {scenario_name} ...")

        experiment = Experiment(
            experiment_name=EXPERIMENT_NAME,
            num_runs=NUM_RUNS,
            base_seed=BASE_SEED,
            market_size=MARKET_SIZE,
            num_customers=NUM_CUSTOMERS,
            num_stores=num_stores,
            ticks=TICKS,
            price=PRICE,
            distance_weight=distance_weight,
            step_size=STEP_SIZE,
            customer_distribution=distribution,
            loyalty_strength=LOYALTY_STRENGTH,
            loyalty_threshold=LOYALTY_THRESHOLD,
        )
        raw_rows = experiment.run()
        all_raw.extend(raw_rows)

        # Summary rows for this scenario — use num_stores as the primary parameter
        # label; distance_weight and distribution are encoded in scenario_name.
        summary_rows = generate_summary_rows(
            rows=raw_rows,
            experiment_name=EXPERIMENT_NAME,
            scenario_name=scenario_name,
            parameter_name="num_stores",
            parameter_value=num_stores,
        )
        all_summary.extend(summary_rows)

    write_raw_csv(RAW_OUTPUT, all_raw)
    print(f"[sweep] Raw output:     {RAW_OUTPUT}  ({len(all_raw)} rows)")

    write_summary_csv(SUMMARY_OUTPUT, all_summary)
    print(f"[sweep] Summary output: {SUMMARY_OUTPUT}  ({len(all_summary)} rows)")


if __name__ == "__main__":
    run_sweep()
