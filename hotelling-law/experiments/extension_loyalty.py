"""
Loyalty extension experiment.

Research question:
    "How does customer loyalty affect store clustering, market share, and profit
    in a Hotelling's Law market?"

Extension:
    Customers remember their previous store.  When loyalty_strength > 0, a customer
    will stay with their previous store unless a competitor's effective cost is better
    by more than loyalty_strength * loyalty_threshold.

    Formally, a customer stays with their previous store when:
        prev_store_cost <= best_store_cost + loyalty_strength * loyalty_threshold

    loyalty_strength = 0.0 is behaviourally identical to the baseline model.

Swept values:
    loyalty_strength: 0.0, 0.25, 0.5, 0.75

Outputs:
    outputs/extension_loyalty_raw.csv     - one row per store per tick per run
    outputs/extension_loyalty_summary.csv - final-tick summary statistics per scenario
"""

import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hotelling.experiment import Experiment
from hotelling.statistics import generate_summary_rows
from hotelling.csv_writer import write_raw_csv, write_summary_csv

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_OUTPUT = os.path.join(_PROJECT_ROOT, "outputs", "extension_loyalty_raw.csv")
SUMMARY_OUTPUT = os.path.join(_PROJECT_ROOT, "outputs", "extension_loyalty_summary.csv")

EXPERIMENT_NAME = "extension_loyalty"
NUM_RUNS = 30
BASE_SEED = 300
TICKS = 100

# --- Fixed model parameters ---
MARKET_SIZE = 100
NUM_CUSTOMERS = 500
NUM_STORES = 2
PRICE = 10.0
DISTANCE_WEIGHT = 1.0
STEP_SIZE = 1.0
PRICE_STEP = 1.0
MIN_PRICE = 1.0
CUSTOMER_DISTRIBUTION = "uniform"
# loyalty_threshold sets the absolute cost margin for the loyalty check.
# A value of 10.0 (equal to the price) means a competitor must be meaningfully
# cheaper before a loyal customer will switch.
LOYALTY_THRESHOLD = 10.0

# --- Swept loyalty_strength values ---
# 0.0 acts as the baseline control; higher values increase retention.
LOYALTY_STRENGTH_VALUES = [0.0, 0.25, 0.5, 0.75]


def run_loyalty() -> None:
    """
    Compare model behaviour across four loyalty_strength values.

    loyalty_strength = 0.0 serves as the control (identical to baseline assignment).
    Higher values progressively increase customer retention, which is expected to
    reduce store clustering and alter the distribution of market shares.
    """
    all_raw: List[Dict] = []
    all_summary: List[Dict] = []

    total = len(LOYALTY_STRENGTH_VALUES)
    for idx, loyalty_strength in enumerate(LOYALTY_STRENGTH_VALUES, start=1):
        scenario_name = f"loyalty_{loyalty_strength}"
        print(f"[loyalty] Scenario {idx}/{total}: {scenario_name} ...")

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
            price_step=PRICE_STEP,
            min_price=MIN_PRICE,
            customer_distribution=CUSTOMER_DISTRIBUTION,
            loyalty_strength=loyalty_strength,
            loyalty_threshold=LOYALTY_THRESHOLD,
        )
        raw_rows = experiment.run()
        all_raw.extend(raw_rows)

        summary_rows = generate_summary_rows(
            rows=raw_rows,
            experiment_name=EXPERIMENT_NAME,
            scenario_name=scenario_name,
            parameter_name="loyalty_strength",
            parameter_value=loyalty_strength,
        )
        all_summary.extend(summary_rows)

    write_raw_csv(RAW_OUTPUT, all_raw)
    print(f"[loyalty] Raw output:     {RAW_OUTPUT}  ({len(all_raw)} rows)")

    write_summary_csv(SUMMARY_OUTPUT, all_summary)
    print(f"[loyalty] Summary output: {SUMMARY_OUTPUT}  ({len(all_summary)} rows)")


if __name__ == "__main__":
    run_loyalty()
