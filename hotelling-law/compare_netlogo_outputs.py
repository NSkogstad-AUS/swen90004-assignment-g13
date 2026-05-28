"""
Compare NetLogo BehaviorSpace exports against Python Hotelling outputs.

Usage:
    python3 compare_netlogo_outputs.py

By default this reads NetLogo CSV exports from:
    netlogo tests input here/

and writes comparison CSV files to:
    outputs/
"""

import argparse
import csv
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT_DIR = PROJECT_ROOT / "netlogo tests input here"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"

BASE_COLUMNS = {"[run number]", "layout", "number-of-stores", "rules", "[step]"}

PYTHON_OUTPUTS = {
    "line": DEFAULT_OUTPUT_DIR / "baseline_summary_netlogo.csv",
    "plane": DEFAULT_OUTPUT_DIR / "plane_baseline_summary_netlogo.csv",
}

COMPARISON_OUTPUTS = {
    "line": DEFAULT_OUTPUT_DIR / "netlogo_python_line_comparison.csv",
    "plane": DEFAULT_OUTPUT_DIR / "netlogo_python_plane_comparison.csv",
}

MEANING = {
    "mean [pycor] of turtles": "average vertical position",
    "standard-deviation [pycor] of turtles": "vertical spread across stores",
    "min [pycor] of turtles": "lowest vertical store position",
    "max [pycor] of turtles": "highest vertical store position",
    "mean [abs pycor] of turtles": "average vertical distance from centre",
    "standard-deviation [abs pycor] of turtles": "uneven vertical distance from centre",
    "min [abs pycor] of turtles": "closest vertical distance to centre",
    "max [abs pycor] of turtles": "furthest vertical distance from centre",
    "mean [mean [distance myself] of other turtles] of turtles": "average inter-store distance",
    "standard-deviation [mean [distance myself] of other turtles] of turtles": "uneven inter-store isolation",
    "min [mean [distance myself] of other turtles] of turtles": "least isolated store distance",
    "max [mean [distance myself] of other turtles] of turtles": "most isolated store distance",
    "mean [price * area-count] of turtles": "average store profit",
    "standard-deviation [price * area-count] of turtles": "profit inequality across stores",
    "min [price * area-count] of turtles": "lowest store profit",
    "max [price * area-count] of turtles": "highest store profit",
    "mean [area-count] of turtles": "average market share",
    "standard-deviation [area-count] of turtles": "market-share inequality",
    "min [area-count] of turtles": "lowest store market share",
    "max [area-count] of turtles": "highest store market share",
    "mean [pxcor] of turtles": "average horizontal position",
    "standard-deviation [pxcor] of turtles": "horizontal spread across stores",
    "min [pxcor] of turtles": "leftmost store position",
    "max [pxcor] of turtles": "rightmost store position",
    "mean [abs pxcor] of turtles": "average horizontal distance from centre",
    "standard-deviation [abs pxcor] of turtles": "uneven horizontal distance from centre",
    "min [abs pxcor] of turtles": "closest horizontal distance to centre",
    "max [abs pxcor] of turtles": "furthest horizontal distance from centre",
    "mean [distancexy 0 0] of turtles": "average radial distance from centre",
    "standard-deviation [distancexy 0 0] of turtles": "uneven radial distance from centre",
    "min [distancexy 0 0] of turtles": "closest total distance to centre",
    "max [distancexy 0 0] of turtles": "furthest total distance from centre",
}


def read_netlogo_table(path: Path) -> List[Dict[str, str]]:
    """Read a NetLogo BehaviorSpace table export with metadata rows."""
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    header_i = next(
        i for i, row in enumerate(rows)
        if row and row[0] == "[run number]"
    )
    header = rows[header_i]
    return [dict(zip(header, row)) for row in rows[header_i + 1:] if row]


def read_plain_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def numeric_mean(rows: Iterable[Dict[str, str]], column: str) -> float:
    return mean(float(row[column]) for row in rows)


def find_netlogo_rows(input_dir: Path, layout: str) -> Optional[List[Dict[str, str]]]:
    """Return final-step NetLogo rows for the requested layout from any matching CSV."""
    for path in sorted(input_dir.glob("*.csv")):
        try:
            rows = read_netlogo_table(path)
        except (StopIteration, UnicodeDecodeError, csv.Error):
            continue

        selected = [
            row for row in rows
            if row.get("layout") == layout
            and row.get("number-of-stores") == "3"
            and row.get("rules") == "normal"
            and row.get("[step]") == "100"
        ]
        if selected:
            print(f"[{layout}] NetLogo input: {path}")
            return selected
    return None


def build_comparison(
    layout: str,
    netlogo_rows: List[Dict[str, str]],
    python_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    metric_cols = [
        col for col in python_rows[0]
        if col in netlogo_rows[0] and col not in BASE_COLUMNS
    ]

    comparison = []
    for col in metric_cols:
        netlogo_value = numeric_mean(netlogo_rows, col)
        python_value = numeric_mean(python_rows, col)
        diff = python_value - netlogo_value
        pct = "" if netlogo_value == 0 else f"{diff / abs(netlogo_value) * 100:.2f}%"
        comparison.append({
            "layout": layout,
            "metric": col,
            "meaning": MEANING.get(col, ""),
            "netlogo_mean_across_runs": f"{netlogo_value:.6f}",
            "python_mean_across_runs": f"{python_value:.6f}",
            "difference": f"{diff:.6f}",
            "percentage_difference": pct,
            "netlogo_runs": str(len(netlogo_rows)),
            "python_runs": str(len(python_rows)),
            "stores_per_run": "3",
        })
    return comparison


def write_comparison(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "layout",
        "metric",
        "meaning",
        "netlogo_mean_across_runs",
        "python_mean_across_runs",
        "difference",
        "percentage_difference",
        "netlogo_runs",
        "python_runs",
        "stores_per_run",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def print_table(layout: str, rows: List[Dict[str, str]]) -> None:
    title = f"{layout.upper()} BASELINE COMPARISON"
    print()
    print(title)
    print("=" * len(title))
    print(f"NetLogo final rows / runs: {rows[0]['netlogo_runs']}")
    print(f"Python rows / runs:        {rows[0]['python_runs']}")
    print(f"Stores per run:            {rows[0]['stores_per_run']}")
    if layout == "line":
        print("World/line:                pycor -20..20, pxcor = 0")
    else:
        print("World/plane:               pxcor -20..20, pycor -20..20")
        print("Consumers:                 1681 patches")
    print()
    print("Each metric below is averaged across runs.")
    print("For standard-deviation reporters, stddev is first computed across stores inside each run.")
    print()
    print(
        f"{'metric':65} {'meaning':42} "
        f"{'netlogo':>12} {'python':>12} {'diff':>12} {'pct':>10}"
    )
    print("-" * 160)
    for row in rows:
        print(
            f"{row['metric'][:65]:65} "
            f"{row['meaning'][:42]:42} "
            f"{float(row['netlogo_mean_across_runs']):12.6f} "
            f"{float(row['python_mean_across_runs']):12.6f} "
            f"{float(row['difference']):12.6f} "
            f"{row['percentage_difference']:>10}"
        )


def compare_layout(layout: str, input_dir: Path, output_dir: Path) -> bool:
    netlogo_rows = find_netlogo_rows(input_dir, layout)
    if not netlogo_rows:
        print(f"[{layout}] No matching NetLogo CSV found in: {input_dir}")
        return False

    python_path = PYTHON_OUTPUTS[layout]
    if not python_path.exists():
        print(f"[{layout}] Missing Python output: {python_path}")
        return False

    python_rows = read_plain_csv(python_path)
    comparison = build_comparison(layout, netlogo_rows, python_rows)
    output_path = output_dir / COMPARISON_OUTPUTS[layout].name
    write_comparison(output_path, comparison)
    print_table(layout, comparison)
    print(f"\n[{layout}] Wrote comparison CSV: {output_path}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare NetLogo BehaviorSpace CSVs with Python Hotelling outputs.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Folder containing NetLogo BehaviorSpace table CSV exports.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Folder to write comparison CSV outputs.",
    )
    parser.add_argument(
        "--layout",
        choices=("line", "plane", "both"),
        default="both",
        help="Which layout comparison to run.",
    )
    args = parser.parse_args()

    layouts = ("line", "plane") if args.layout == "both" else (args.layout,)
    any_compared = False
    for layout in layouts:
        any_compared = compare_layout(layout, args.input_dir, args.output_dir) or any_compared

    if not any_compared:
        raise SystemExit(
            "No comparisons were run. Add NetLogo table CSV exports to "
            f"'{args.input_dir}' and try again."
        )


if __name__ == "__main__":
    main()
