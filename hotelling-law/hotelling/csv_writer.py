"""CSV output writer for simulation results."""

import csv
import os
from typing import Dict, List

# Column order for the raw (per-tick, per-store) output CSV.
RAW_HEADERS: List[str] = [
    "experiment_name",
    "run_id",
    "tick",
    "store_id",
    "store_position",
    "store_price",
    "store_profit",
    "store_market_share",
    "assigned_customer_count",
    "distance_from_centre",
    "average_distance_to_other_stores",
    "num_stores",
    "num_customers",
    "market_size",
    "distance_weight",
    "step_size",
    "price_step",
    "customer_distribution",
    "layout",
    "rules",
    "loyalty_strength",
    "loyalty_threshold",
    "random_seed",
]

# Column order for the summary (aggregated across runs) CSV.
SUMMARY_HEADERS: List[str] = [
    "experiment_name",
    "scenario_name",
    "parameter_name",
    "parameter_value",
    "metric_name",
    "mean",
    "standard_deviation",
    "minimum",
    "maximum",
    "run_count",
]

# Convenience alias so callers that only need raw headers can import HEADERS.
HEADERS = RAW_HEADERS


def write_csv(filepath: str, rows: List[Dict], headers: List[str] = RAW_HEADERS) -> None:
    """
    Write a list of row dicts to a CSV file at filepath.

    Creates parent directories automatically.  Columns are written in the order
    defined by headers; extra keys in rows are silently ignored.

    Args:
        filepath: Destination path for the CSV file.
        rows: List of row dicts to write.
        headers: Column order.  Defaults to RAW_HEADERS.
    """
    parent = os.path.dirname(filepath)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_raw_csv(filepath: str, rows: List[Dict]) -> None:
    """Write raw simulation rows using RAW_HEADERS column order."""
    write_csv(filepath, rows, RAW_HEADERS)


def write_final_tick_raw_csv(filepath: str, rows: List[Dict]) -> None:
    """Write only rows from the final recorded tick using RAW_HEADERS column order."""
    if not rows:
        write_csv(filepath, rows, RAW_HEADERS)
        return

    final_tick = max(int(row["tick"]) for row in rows)
    final_rows = [row for row in rows if int(row["tick"]) == final_tick]
    write_csv(filepath, final_rows, RAW_HEADERS)


def write_summary_csv(filepath: str, rows: List[Dict]) -> None:
    """Write summary rows using SUMMARY_HEADERS column order."""
    write_csv(filepath, rows, SUMMARY_HEADERS)
