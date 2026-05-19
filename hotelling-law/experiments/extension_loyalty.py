"""Loyalty extension experiment comparing loyalty_strength values."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hotelling.experiment import Experiment
from hotelling.csv_writer import write_csv

OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "outputs",
    "extension_loyalty.csv",
)

LOYALTY_VALUES = [0.0, 0.25, 0.5, 0.75]


def run_loyalty() -> None:
    """
    Compare model behaviour across loyalty_strength values 0.0, 0.25, 0.5, and 0.75.

    loyalty_strength=0.0 is the unmodified baseline; higher values make customers
    increasingly reluctant to switch stores.
    """
    all_rows = []

    for loyalty_strength in LOYALTY_VALUES:
        name = f"loyalty_{loyalty_strength}"
        experiment = Experiment(
            experiment_name=name,
            num_runs=5,
            base_seed=42,
            market_size=100,
            num_customers=100,
            num_stores=2,
            ticks=50,
            price=1.0,
            distance_weight=1.0,
            step_size=1.0,
            customer_distribution="uniform",
            loyalty_strength=loyalty_strength,
        )
        rows = experiment.run()
        all_rows.extend(rows)
        print(f"  {name}: {len(rows)} rows")

    write_csv(OUTPUT_PATH, all_rows)
    print(f"Wrote {len(all_rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    run_loyalty()
