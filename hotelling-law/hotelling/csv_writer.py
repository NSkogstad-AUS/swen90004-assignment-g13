"""CSV output writer for simulation results."""

import csv
import os
from typing import Dict, List

HEADERS: List[str] = [
    "experiment_name",
    "run_id",
    "tick",
    "store_id",
    "store_position",
    "store_price",
    "store_profit",
    "store_market_share",
    "distance_from_centre",
    "average_distance_to_other_stores",
    "parameters_summary",
]


def write_csv(filepath: str, rows: List[Dict]) -> None:
    """
    Write simulation output rows to a CSV file.

    Creates parent directories if they do not exist. Columns are written in the
    fixed order defined by HEADERS; any extra keys in rows are silently ignored.

    Args:
        filepath: Destination path for the CSV file.
        rows: List of row dicts, each produced by Experiment.run().
    """
    parent = os.path.dirname(filepath)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
