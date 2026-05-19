"""Parameter sweep experiment over num_stores and distance_weight."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hotelling.experiment import Experiment
from hotelling.csv_writer import write_csv

OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "outputs",
    "parameter_sweep.csv",
)

NUM_STORES_VALUES = [2, 3, 4]
DISTANCE_WEIGHT_VALUES = [0.5, 1.0, 2.0]


def run_sweep() -> None:
    """Sweep num_stores and distance_weight, writing all results to a single CSV."""
    all_rows = []

    for num_stores in NUM_STORES_VALUES:
        for distance_weight in DISTANCE_WEIGHT_VALUES:
            name = f"sweep_stores{num_stores}_dw{distance_weight}"
            experiment = Experiment(
                experiment_name=name,
                num_runs=5,
                base_seed=42,
                market_size=100,
                num_customers=100,
                num_stores=num_stores,
                ticks=50,
                price=1.0,
                distance_weight=distance_weight,
                step_size=1.0,
                customer_distribution="uniform",
                loyalty_strength=0.0,
            )
            rows = experiment.run()
            all_rows.extend(rows)
            print(f"  {name}: {len(rows)} rows")

    write_csv(OUTPUT_PATH, all_rows)
    print(f"Wrote {len(all_rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    run_sweep()
