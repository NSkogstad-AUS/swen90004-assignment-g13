"""CSV output writer for simulation results."""

import csv
import os
from statistics import mean, stdev
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

NETLOGO_TABLE_HEADERS: List[str] = [
    "[run number]",
    "layout",
    "number-of-stores",
    "rules",
    "[step]",
    "mean [pycor] of turtles",
    "standard-deviation [pycor] of turtles",
    "min [pycor] of turtles",
    "max [pycor] of turtles",
    "mean [abs pycor] of turtles",
    "standard-deviation [abs pycor] of turtles",
    "min [abs pycor] of turtles",
    "max [abs pycor] of turtles",
    "mean [mean [distance myself] of other turtles] of turtles",
    "standard-deviation [mean [distance myself] of other turtles] of turtles",
    "min [mean [distance myself] of other turtles] of turtles",
    "max [mean [distance myself] of other turtles] of turtles",
    "mean [price * area-count] of turtles",
    "standard-deviation [price * area-count] of turtles",
    "min [price * area-count] of turtles",
    "max [price * area-count] of turtles",
    "mean [area-count] of turtles",
    "standard-deviation [area-count] of turtles",
    "min [area-count] of turtles",
    "max [area-count] of turtles",
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


def _sample_stdev(values: List[float]) -> float:
    """Return NetLogo-style sample standard deviation for a list of values."""
    return stdev(values) if len(values) > 1 else 0.0


def _metric_stats(values: List[float]) -> List[float]:
    return [mean(values), _sample_stdev(values), min(values), max(values)]


def write_netlogo_table_csv(filepath: str, rows: List[Dict]) -> None:
    """Write final-tick per-run metrics using NetLogo BehaviorSpace-style columns."""
    parent = os.path.dirname(filepath)
    if parent:
        os.makedirs(parent, exist_ok=True)

    if not rows:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(NETLOGO_TABLE_HEADERS)
        return

    final_tick = max(int(row["tick"]) for row in rows)
    final_rows = [row for row in rows if int(row["tick"]) == final_tick]

    grouped: Dict[int, List[Dict]] = {}
    for row in final_rows:
        grouped.setdefault(int(row["run_id"]), []).append(row)

    table_rows: List[List] = []
    for run_id in sorted(grouped):
        run_rows = grouped[run_id]
        first = run_rows[0]
        positions = [float(row["store_position"]) for row in run_rows]
        distances_from_centre = [float(row["distance_from_centre"]) for row in run_rows]
        distances_to_others = [
            float(row["average_distance_to_other_stores"]) for row in run_rows
        ]
        profits = [float(row["store_profit"]) for row in run_rows]
        market_shares = [float(row["store_market_share"]) for row in run_rows]

        table_rows.append([
            run_id,
            first["layout"],
            int(first["num_stores"]),
            first["rules"],
            final_tick + 1,
            *_metric_stats(positions),
            *_metric_stats(distances_from_centre),
            *_metric_stats(distances_to_others),
            *_metric_stats(profits),
            *_metric_stats(market_shares),
        ])

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(NETLOGO_TABLE_HEADERS)
        writer.writerows(table_rows)


def write_summary_csv(filepath: str, rows: List[Dict]) -> None:
    """Write summary rows using SUMMARY_HEADERS column order."""
    write_csv(filepath, rows, SUMMARY_HEADERS)
