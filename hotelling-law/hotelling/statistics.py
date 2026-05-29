"""
Summary statistics helpers for Hotelling's Law experiment output.

Uses only the Python standard library (statistics module).
Provides functions to compute per-run averages and cross-run summary rows
suitable for writing to the summary CSV files.
"""

from statistics import mean, stdev
from typing import Any, Dict, List


# Metrics computed from final-tick store rows.
SUMMARY_METRICS: List[str] = [
    "store_position",
    "store_profit",
    "store_market_share",
    "market_share_variation",
    "distance_from_centre",
    "average_distance_to_other_stores",
]


def final_tick_from_rows(rows: List[Dict]) -> int:
    """
    Return the maximum tick value present in rows.

    This identifies the last tick recorded, which represents the steady-state
    (or near-steady-state) behaviour of the simulation.
    """
    if not rows:
        raise ValueError("rows list is empty; cannot determine final tick.")
    return max(int(r["tick"]) for r in rows)


def per_run_averages(rows: List[Dict], final_tick: int) -> Dict[int, Dict[str, float]]:
    """
    Compute the average of each SUMMARY_METRICS field across stores for each run,
    restricted to the given final_tick.

    Returns a dict mapping run_id -> {metric_name -> average_value}.

    Averaging across stores gives one representative value per run per metric,
    which is then aggregated across runs in generate_summary_rows().
    """
    # Filter to final tick rows only.
    final_rows = [r for r in rows if int(r["tick"]) == final_tick]

    # Group final-tick rows by run_id.
    grouped: Dict[int, List[Dict]] = {}
    for row in final_rows:
        run_id = int(row["run_id"])
        grouped.setdefault(run_id, []).append(row)

    averages: Dict[int, Dict[str, float]] = {}
    for run_id, run_rows in grouped.items():
        run_avg: Dict[str, float] = {}
        for metric in SUMMARY_METRICS:
            if metric == "market_share_variation":
                market_shares = [float(r["store_market_share"]) for r in run_rows]
                run_avg[metric] = stdev(market_shares) if len(market_shares) > 1 else 0.0
                continue

            values = [float(r[metric]) for r in run_rows]
            run_avg[metric] = mean(values) if values else 0.0
        averages[run_id] = run_avg

    return averages


def generate_summary_rows(
    rows: List[Dict],
    experiment_name: str,
    scenario_name: str,
    parameter_name: str,
    parameter_value: Any,
) -> List[Dict]:
    """
    Produce one summary row per metric for a single experimental scenario.

    The summary aggregates per-run averages across the final simulation tick.
    Returns a list of dicts matching the summary CSV header format.

    Args:
        rows: Raw output rows from one scenario (may include multiple runs).
        experiment_name: Label identifying the experiment (e.g. 'baseline').
        scenario_name: Label identifying this specific scenario within the experiment.
        parameter_name: Name of the key parameter varied in this scenario
                        (e.g. 'num_stores').  Use 'configuration' for baseline.
        parameter_value: Value of that parameter for this scenario.
    """
    if not rows:
        return []

    final_tick = final_tick_from_rows(rows)
    run_avgs = per_run_averages(rows, final_tick)

    if not run_avgs:
        return []

    summary_rows: List[Dict] = []

    for metric in SUMMARY_METRICS:
        values = [avg[metric] for avg in run_avgs.values()]
        run_count = len(values)

        # Standard deviation requires at least two data points.
        sd = stdev(values) if run_count > 1 else 0.0

        summary_rows.append({
            "experiment_name": experiment_name,
            "scenario_name": scenario_name,
            "parameter_name": str(parameter_name),
            "parameter_value": str(parameter_value),
            "metric_name": metric,
            "mean": round(mean(values), 6),
            "standard_deviation": round(sd, 6),
            "minimum": round(min(values), 6),
            "maximum": round(max(values), 6),
            "run_count": run_count,
        })

    return summary_rows
