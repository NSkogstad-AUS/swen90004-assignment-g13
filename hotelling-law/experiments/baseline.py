"""Baseline experiment: two-store model over multiple independent runs."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hotelling.experiment import Experiment
from hotelling.csv_writer import write_csv

OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "baseline.csv"
)


def run_baseline() -> None:
    """Run the default two-store baseline experiment and write results to CSV."""
    experiment = Experiment(
        experiment_name="baseline",
        num_runs=10,
        base_seed=42,
        market_size=100,
        num_customers=100,
        num_stores=2,
        ticks=50,
        price=1.0,
        distance_weight=1.0,
        step_size=1.0,
        customer_distribution="uniform",
        loyalty_strength=0.0,
    )
    rows = experiment.run()
    write_csv(OUTPUT_PATH, rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    run_baseline()
