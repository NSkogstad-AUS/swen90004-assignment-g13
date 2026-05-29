"""Generate SVG plots from Hotelling experiment CSV outputs."""

from __future__ import annotations

import csv
from html import escape
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Sequence, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = PROJECT_ROOT / "outputs"
DEFAULT_OUTPUT_DIR = DEFAULT_INPUT_DIR / "plots"

LINE_COLORS = (
    "#1f77b4",
    "#d62728",
    "#2ca02c",
    "#ff7f0e",
    "#9467bd",
    "#8c564b",
)
BAR_COLOR = "#4c78a8"
GRID_COLOR = "#d9d9d9"
AXIS_COLOR = "#222222"
BACKGROUND_COLOR = "#ffffff"

RAW_POSITION_PLOT = "mean_store_position_by_tick.svg"
RAW_PROFIT_PLOT = "mean_store_profit_by_tick.svg"
RAW_DISTANCE_PLOT = "mean_distance_from_centre_by_tick.svg"

SWEEP_METRICS = (
    "store_profit",
    "distance_from_centre",
    "average_distance_to_other_stores",
)
LOYALTY_METRICS = (
    "store_profit",
    "distance_from_centre",
    "average_distance_to_other_stores",
    "market_share_variation",
)
METRIC_LABELS = {
    "store_position": "Mean store position",
    "store_profit": "Mean store profit",
    "store_market_share": "Mean store market share",
    "market_share_variation": "Market share variation",
    "distance_from_centre": "Mean distance from centre",
    "average_distance_to_other_stores": "Mean distance to other stores",
}


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    """Return all rows from a plain CSV file."""
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _ordered_unique(values: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _format_value(value: float) -> str:
    if abs(value) >= 1000:
        return f"{value:.0f}"
    if abs(value) >= 100:
        return f"{value:.1f}"
    if abs(value) >= 10:
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _value_range(values: Sequence[float]) -> Tuple[float, float]:
    minimum = min(values)
    maximum = max(values)
    if minimum == maximum:
        padding = 1.0 if minimum == 0 else abs(minimum) * 0.1
        return minimum - padding, maximum + padding
    padding = (maximum - minimum) * 0.08
    return minimum - padding, maximum + padding


def _svg_shell(width: int, height: int, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" fill="{BACKGROUND_COLOR}"/>'
        f"{body}</svg>"
    )


def _write_svg(path: Path, body: str, width: int = 960, height: int = 540) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_svg_shell(width, height, body), encoding="utf-8")


def _line_chart(
    path: Path,
    title: str,
    x_label: str,
    y_label: str,
    series: Sequence[Tuple[str, Sequence[Tuple[float, float]]]],
) -> None:
    if not series:
        raise ValueError("series must not be empty")

    width = 960
    height = 540
    left = 90
    right = 220
    top = 70
    bottom = 80
    chart_width = width - left - right
    chart_height = height - top - bottom

    xs = [point[0] for _, points in series for point in points]
    ys = [point[1] for _, points in series for point in points]
    x_min, x_max = _value_range(xs)
    y_min, y_max = _value_range(ys)

    def x_pos(value: float) -> float:
        return left + (value - x_min) / (x_max - x_min) * chart_width

    def y_pos(value: float) -> float:
        return top + chart_height - (value - y_min) / (y_max - y_min) * chart_height

    parts = [
        f'<text x="{width / 2:.1f}" y="32" text-anchor="middle" '
        f'font-size="22" font-family="Arial, sans-serif">{escape(title)}</text>',
        f'<line x1="{left}" y1="{top + chart_height}" x2="{left + chart_width}" '
        f'y2="{top + chart_height}" stroke="{AXIS_COLOR}" stroke-width="2"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_height}" '
        f'stroke="{AXIS_COLOR}" stroke-width="2"/>',
        f'<text x="{left + chart_width / 2:.1f}" y="{height - 20}" text-anchor="middle" '
        f'font-size="14" font-family="Arial, sans-serif">{escape(x_label)}</text>',
        f'<text x="26" y="{top + chart_height / 2:.1f}" text-anchor="middle" '
        f'font-size="14" font-family="Arial, sans-serif" transform="rotate(-90 26 {top + chart_height / 2:.1f})">'
        f"{escape(y_label)}</text>",
    ]

    for index in range(6):
        fraction = index / 5
        y_value = y_min + (y_max - y_min) * fraction
        y = y_pos(y_value)
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_width}" y2="{y:.1f}" '
            f'stroke="{GRID_COLOR}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{left - 10}" y="{y + 5:.1f}" text-anchor="end" '
            f'font-size="12" font-family="Arial, sans-serif">{escape(_format_value(y_value))}</text>'
        )

    x_tick_values = sorted(set(xs))
    if len(x_tick_values) > 8:
        step = max(1, len(x_tick_values) // 7)
        x_tick_values = x_tick_values[::step]
        if x_tick_values[-1] != max(xs):
            x_tick_values.append(max(xs))

    for x_value in x_tick_values:
        x = x_pos(x_value)
        parts.append(
            f'<line x1="{x:.1f}" y1="{top + chart_height}" x2="{x:.1f}" y2="{top + chart_height + 6}" '
            f'stroke="{AXIS_COLOR}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{x:.1f}" y="{top + chart_height + 24}" text-anchor="middle" '
            f'font-size="12" font-family="Arial, sans-serif">{escape(_format_value(x_value))}</text>'
        )

    legend_x = left + chart_width + 20
    legend_y = top + 10
    for index, (label, points) in enumerate(series):
        color = LINE_COLORS[index % len(LINE_COLORS)]
        point_string = " ".join(f"{x_pos(x):.1f},{y_pos(y):.1f}" for x, y in points)
        parts.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{point_string}"/>'
        )
        for x, y in points:
            parts.append(
                f'<circle cx="{x_pos(x):.1f}" cy="{y_pos(y):.1f}" r="3.5" fill="{color}"/>'
            )
        y_offset = legend_y + index * 24
        parts.append(
            f'<line x1="{legend_x}" y1="{y_offset}" x2="{legend_x + 18}" y2="{y_offset}" '
            f'stroke="{color}" stroke-width="3"/>'
        )
        parts.append(
            f'<text x="{legend_x + 28}" y="{y_offset + 4}" font-size="12" '
            f'font-family="Arial, sans-serif">{escape(label)}</text>'
        )

    _write_svg(path, "".join(parts), width=width, height=height)


def _bar_chart(path: Path, title: str, y_label: str, items: Sequence[Tuple[str, float]]) -> None:
    if not items:
        raise ValueError("items must not be empty")

    width = 1100
    height = 620
    left = 90
    right = 50
    top = 70
    bottom = 220
    chart_width = width - left - right
    chart_height = height - top - bottom

    values = [value for _, value in items]
    y_min = min(0.0, min(values))
    y_max = max(0.0, max(values))
    y_min, y_max = _value_range([y_min, y_max])

    def y_pos(value: float) -> float:
        return top + chart_height - (value - y_min) / (y_max - y_min) * chart_height

    zero_y = y_pos(0.0)
    slot_width = chart_width / max(1, len(items))
    bar_width = slot_width * 0.7

    parts = [
        f'<text x="{width / 2:.1f}" y="32" text-anchor="middle" '
        f'font-size="22" font-family="Arial, sans-serif">{escape(title)}</text>',
        f'<line x1="{left}" y1="{top + chart_height}" x2="{left + chart_width}" '
        f'y2="{top + chart_height}" stroke="{AXIS_COLOR}" stroke-width="2"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_height}" '
        f'stroke="{AXIS_COLOR}" stroke-width="2"/>',
        f'<text x="26" y="{top + chart_height / 2:.1f}" text-anchor="middle" '
        f'font-size="14" font-family="Arial, sans-serif" transform="rotate(-90 26 {top + chart_height / 2:.1f})">'
        f"{escape(y_label)}</text>",
    ]

    for index in range(6):
        fraction = index / 5
        y_value = y_min + (y_max - y_min) * fraction
        y = y_pos(y_value)
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_width}" y2="{y:.1f}" '
            f'stroke="{GRID_COLOR}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{left - 10}" y="{y + 5:.1f}" text-anchor="end" '
            f'font-size="12" font-family="Arial, sans-serif">{escape(_format_value(y_value))}</text>'
        )

    parts.append(
        f'<line x1="{left}" y1="{zero_y:.1f}" x2="{left + chart_width}" y2="{zero_y:.1f}" '
        f'stroke="{AXIS_COLOR}" stroke-width="1.5"/>'
    )

    for index, (label, value) in enumerate(items):
        center_x = left + slot_width * index + slot_width / 2
        x = center_x - bar_width / 2
        top_y = min(y_pos(value), zero_y)
        height_value = abs(zero_y - y_pos(value))
        parts.append(
            f'<rect x="{x:.1f}" y="{top_y:.1f}" width="{bar_width:.1f}" '
            f'height="{height_value:.1f}" fill="{BAR_COLOR}"/>'
        )
        parts.append(
            f'<text x="{center_x:.1f}" y="{top_y - 8:.1f}" text-anchor="middle" '
            f'font-size="11" font-family="Arial, sans-serif">{escape(_format_value(value))}</text>'
        )
        label_x = center_x
        label_y = top + chart_height + 20
        parts.append(
            f'<text x="{label_x:.1f}" y="{label_y:.1f}" text-anchor="end" '
            f'font-size="12" font-family="Arial, sans-serif" transform="rotate(-40 {label_x:.1f} {label_y:.1f})">'
            f"{escape(label)}</text>"
        )

    _write_svg(path, "".join(parts), width=width, height=height)


def _mean_series_by_tick_and_store(
    rows: Sequence[Dict[str, str]],
    metric_name: str,
) -> List[Tuple[str, List[Tuple[float, float]]]]:
    store_ids = sorted({int(row["store_id"]) for row in rows})
    series: List[Tuple[str, List[Tuple[float, float]]]] = []
    for store_id in store_ids:
        grouped: Dict[int, List[float]] = {}
        for row in rows:
            if int(row["store_id"]) != store_id:
                continue
            grouped.setdefault(int(row["tick"]), []).append(float(row[metric_name]))
        points = [(float(tick), mean(values)) for tick, values in sorted(grouped.items())]
        series.append((f"Store {store_id}", points))
    return series


def _mean_series_by_tick(rows: Sequence[Dict[str, str]], metric_name: str) -> List[Tuple[str, List[Tuple[float, float]]]]:
    grouped: Dict[int, List[float]] = {}
    for row in rows:
        grouped.setdefault(int(row["tick"]), []).append(float(row[metric_name]))
    points = [(float(tick), mean(values)) for tick, values in sorted(grouped.items())]
    return [(METRIC_LABELS.get(metric_name, metric_name), points)]


def _metric_rows(rows: Sequence[Dict[str, str]], metric_name: str) -> List[Dict[str, str]]:
    return [row for row in rows if row["metric_name"] == metric_name]


def _summary_metric_by_scenario(rows: Sequence[Dict[str, str]], metric_name: str) -> List[Tuple[str, float]]:
    metric_rows = _metric_rows(rows, metric_name)
    scenario_order = _ordered_unique(row["scenario_name"] for row in rows)
    values = {
        row["scenario_name"]: float(row["mean"])
        for row in metric_rows
    }
    return [(scenario, values[scenario]) for scenario in scenario_order if scenario in values]


def _summary_metric_by_parameter(rows: Sequence[Dict[str, str]], metric_name: str) -> List[Tuple[str, List[Tuple[float, float]]]]:
    metric_rows = _metric_rows(rows, metric_name)
    sorted_rows = sorted(metric_rows, key=lambda row: float(row["parameter_value"]))
    points = [
        (float(row["parameter_value"]), float(row["mean"]))
        for row in sorted_rows
    ]
    return [(METRIC_LABELS.get(metric_name, metric_name), points)]


def generate_raw_experiment_plots(
    raw_csv_path: Path,
    output_dir: Path,
    stem: str,
    title_prefix: str,
) -> List[Path]:
    rows = read_csv_rows(raw_csv_path)
    if not rows:
        return []

    output_paths = [
        output_dir / f"{stem}_{RAW_POSITION_PLOT}",
        output_dir / f"{stem}_{RAW_PROFIT_PLOT}",
        output_dir / f"{stem}_{RAW_DISTANCE_PLOT}",
    ]
    _line_chart(
        output_paths[0],
        f"{title_prefix} Mean Store Position By Tick",
        "Tick",
        METRIC_LABELS["store_position"],
        _mean_series_by_tick_and_store(rows, "store_position"),
    )
    _line_chart(
        output_paths[1],
        f"{title_prefix} Mean Store Profit By Tick",
        "Tick",
        METRIC_LABELS["store_profit"],
        _mean_series_by_tick_and_store(rows, "store_profit"),
    )
    _line_chart(
        output_paths[2],
        f"{title_prefix} Mean Distance From Centre By Tick",
        "Tick",
        METRIC_LABELS["distance_from_centre"],
        _mean_series_by_tick(rows, "distance_from_centre"),
    )
    return output_paths


def generate_summary_bar_plots(
    summary_csv_path: Path,
    output_dir: Path,
    stem: str,
    title_prefix: str,
    metrics: Sequence[str],
) -> List[Path]:
    rows = read_csv_rows(summary_csv_path)
    if not rows:
        return []

    output_paths: List[Path] = []
    for metric_name in metrics:
        items = _summary_metric_by_scenario(rows, metric_name)
        if not items:
            continue
        output_path = output_dir / f"{stem}_{metric_name}.svg"
        _bar_chart(
            output_path,
            f"{title_prefix} {METRIC_LABELS.get(metric_name, metric_name)}",
            METRIC_LABELS.get(metric_name, metric_name),
            items,
        )
        output_paths.append(output_path)
    return output_paths


def generate_summary_line_plots(
    summary_csv_path: Path,
    output_dir: Path,
    stem: str,
    title_prefix: str,
    parameter_label: str,
    metrics: Sequence[str],
) -> List[Path]:
    rows = read_csv_rows(summary_csv_path)
    if not rows:
        return []

    output_paths: List[Path] = []
    for metric_name in metrics:
        series = _summary_metric_by_parameter(rows, metric_name)
        if not series or not series[0][1]:
            continue
        output_path = output_dir / f"{stem}_{metric_name}.svg"
        _line_chart(
            output_path,
            f"{title_prefix} {METRIC_LABELS.get(metric_name, metric_name)}",
            parameter_label,
            METRIC_LABELS.get(metric_name, metric_name),
            series,
        )
        output_paths.append(output_path)
    return output_paths


def generate_baseline_plots(
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> List[Path]:
    raw_path = input_dir / "baseline_raw.csv"
    if not raw_path.exists():
        return []
    return generate_raw_experiment_plots(raw_path, output_dir, "baseline", "Baseline")


def generate_plane_plots(
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> List[Path]:
    raw_path = input_dir / "plane_baseline_raw.csv"
    if not raw_path.exists():
        return []
    return generate_raw_experiment_plots(raw_path, output_dir, "plane_baseline", "Plane Baseline")


def generate_sweep_plots(
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> List[Path]:
    summary_path = input_dir / "replication_sweep_summary.csv"
    if not summary_path.exists():
        return []
    return generate_summary_bar_plots(
        summary_path,
        output_dir,
        "replication_sweep",
        "Replication Sweep",
        SWEEP_METRICS,
    )


def generate_loyalty_plots(
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> List[Path]:
    summary_path = input_dir / "extension_loyalty_summary.csv"
    if not summary_path.exists():
        return []
    return generate_summary_line_plots(
        summary_path,
        output_dir,
        "extension_loyalty",
        "Loyalty Extension",
        "Loyalty strength",
        LOYALTY_METRICS,
    )


def generate_plots(
    experiment: str = "all",
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> List[Path]:
    """Generate SVG plots for the selected experiment set."""
    generators = {
        "baseline": generate_baseline_plots,
        "plane": generate_plane_plots,
        "sweep": generate_sweep_plots,
        "loyalty": generate_loyalty_plots,
    }

    if experiment == "all":
        generated: List[Path] = []
        for generator in generators.values():
            generated.extend(generator(input_dir=input_dir, output_dir=output_dir))
        return generated

    return generators[experiment](input_dir=input_dir, output_dir=output_dir)
