"""Tests for SVG plot generation from experiment CSV outputs."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from hotelling.csv_writer import write_raw_csv, write_summary_csv
from hotelling.experiment import Experiment
from hotelling.plotting import generate_plots


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLOT_SCRIPT = PROJECT_ROOT / "plot_results.py"


def _write_small_raw_csv(path: Path) -> None:
    experiment = Experiment(
        experiment_name="baseline",
        num_runs=2,
        base_seed=10,
        market_size=20,
        num_customers=10,
        num_stores=2,
        ticks=3,
        price=10.0,
        layout="line",
        rules="normal",
    )
    write_raw_csv(os.fspath(path), experiment.run())


def _write_sweep_summary_csv(path: Path) -> None:
    rows = [
        {
            "experiment_name": "replication_sweep",
            "scenario_name": "layoutline_stores2_rulesnormal",
            "parameter_name": "num_stores",
            "parameter_value": "2",
            "metric_name": "store_profit",
            "mean": "20.0",
            "standard_deviation": "1.0",
            "minimum": "19.0",
            "maximum": "21.0",
            "run_count": "30",
        },
        {
            "experiment_name": "replication_sweep",
            "scenario_name": "layoutline_stores3_rulesmoving-only",
            "parameter_name": "num_stores",
            "parameter_value": "3",
            "metric_name": "store_profit",
            "mean": "15.0",
            "standard_deviation": "1.5",
            "minimum": "13.0",
            "maximum": "17.0",
            "run_count": "30",
        },
        {
            "experiment_name": "replication_sweep",
            "scenario_name": "layoutline_stores2_rulesnormal",
            "parameter_name": "num_stores",
            "parameter_value": "2",
            "metric_name": "distance_from_centre",
            "mean": "5.0",
            "standard_deviation": "0.5",
            "minimum": "4.0",
            "maximum": "6.0",
            "run_count": "30",
        },
        {
            "experiment_name": "replication_sweep",
            "scenario_name": "layoutline_stores3_rulesmoving-only",
            "parameter_name": "num_stores",
            "parameter_value": "3",
            "metric_name": "distance_from_centre",
            "mean": "4.0",
            "standard_deviation": "0.5",
            "minimum": "3.0",
            "maximum": "5.0",
            "run_count": "30",
        },
        {
            "experiment_name": "replication_sweep",
            "scenario_name": "layoutline_stores2_rulesnormal",
            "parameter_name": "num_stores",
            "parameter_value": "2",
            "metric_name": "average_distance_to_other_stores",
            "mean": "7.0",
            "standard_deviation": "0.2",
            "minimum": "6.8",
            "maximum": "7.2",
            "run_count": "30",
        },
        {
            "experiment_name": "replication_sweep",
            "scenario_name": "layoutline_stores3_rulesmoving-only",
            "parameter_name": "num_stores",
            "parameter_value": "3",
            "metric_name": "average_distance_to_other_stores",
            "mean": "6.0",
            "standard_deviation": "0.3",
            "minimum": "5.7",
            "maximum": "6.3",
            "run_count": "30",
        },
    ]
    write_summary_csv(os.fspath(path), rows)


def _write_loyalty_summary_csv(path: Path) -> None:
    rows = []
    for loyalty_strength, profit, distance, spacing, share, share_variation in (
        (0.0, 20.0, 4.0, 8.0, 50.0, 6.0),
        (0.5, 18.0, 5.0, 9.0, 50.0, 4.0),
        (0.75, 17.0, 5.5, 9.5, 50.0, 2.0),
    ):
        rows.extend(
            [
                {
                    "experiment_name": "extension_loyalty",
                    "scenario_name": f"loyalty_{loyalty_strength}",
                    "parameter_name": "loyalty_strength",
                    "parameter_value": str(loyalty_strength),
                    "metric_name": "store_profit",
                    "mean": str(profit),
                    "standard_deviation": "1.0",
                    "minimum": str(profit - 1),
                    "maximum": str(profit + 1),
                    "run_count": "30",
                },
                {
                    "experiment_name": "extension_loyalty",
                    "scenario_name": f"loyalty_{loyalty_strength}",
                    "parameter_name": "loyalty_strength",
                    "parameter_value": str(loyalty_strength),
                    "metric_name": "distance_from_centre",
                    "mean": str(distance),
                    "standard_deviation": "0.5",
                    "minimum": str(distance - 0.5),
                    "maximum": str(distance + 0.5),
                    "run_count": "30",
                },
                {
                    "experiment_name": "extension_loyalty",
                    "scenario_name": f"loyalty_{loyalty_strength}",
                    "parameter_name": "loyalty_strength",
                    "parameter_value": str(loyalty_strength),
                    "metric_name": "average_distance_to_other_stores",
                    "mean": str(spacing),
                    "standard_deviation": "0.5",
                    "minimum": str(spacing - 0.5),
                    "maximum": str(spacing + 0.5),
                    "run_count": "30",
                },
                {
                    "experiment_name": "extension_loyalty",
                    "scenario_name": f"loyalty_{loyalty_strength}",
                    "parameter_name": "loyalty_strength",
                    "parameter_value": str(loyalty_strength),
                    "metric_name": "store_market_share",
                    "mean": str(share),
                    "standard_deviation": "0.0",
                    "minimum": str(share),
                    "maximum": str(share),
                    "run_count": "30",
                },
                {
                    "experiment_name": "extension_loyalty",
                    "scenario_name": f"loyalty_{loyalty_strength}",
                    "parameter_name": "loyalty_strength",
                    "parameter_value": str(loyalty_strength),
                    "metric_name": "market_share_variation",
                    "mean": str(share_variation),
                    "standard_deviation": "0.5",
                    "minimum": str(share_variation - 0.5),
                    "maximum": str(share_variation + 0.5),
                    "run_count": "30",
                },
            ]
        )
    write_summary_csv(os.fspath(path), rows)


class TestPlotGeneration(unittest.TestCase):
    def test_generate_plots_from_available_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_dir = Path(tmp) / "inputs"
            output_dir = Path(tmp) / "plots"
            input_dir.mkdir()

            _write_small_raw_csv(input_dir / "baseline_raw.csv")
            _write_sweep_summary_csv(input_dir / "replication_sweep_summary.csv")
            _write_loyalty_summary_csv(input_dir / "extension_loyalty_summary.csv")

            generated = generate_plots(
                experiment="all",
                input_dir=input_dir,
                output_dir=output_dir,
            )

            self.assertEqual(len(generated), 10)
            self.assertTrue((output_dir / "baseline_mean_store_position_by_tick.svg").exists())
            self.assertTrue((output_dir / "replication_sweep_store_profit.svg").exists())
            self.assertTrue((output_dir / "extension_loyalty_store_profit.svg").exists())
            self.assertTrue((output_dir / "extension_loyalty_market_share_variation.svg").exists())

            sample_svg = (output_dir / "baseline_mean_store_position_by_tick.svg").read_text(
                encoding="utf-8"
            )
            self.assertIn("<svg", sample_svg)
            self.assertIn("Baseline Mean Store Position By Tick", sample_svg)

    def test_plot_cli_writes_expected_svg_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_dir = Path(tmp) / "inputs"
            output_dir = Path(tmp) / "plots"
            input_dir.mkdir()

            _write_small_raw_csv(input_dir / "baseline_raw.csv")

            result = subprocess.run(
                [
                    sys.executable,
                    os.fspath(PLOT_SCRIPT),
                    "--experiment",
                    "baseline",
                    "--input-dir",
                    os.fspath(input_dir),
                    "--output-dir",
                    os.fspath(output_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("[plots] wrote:", result.stdout)
            self.assertTrue((output_dir / "baseline_mean_store_profit_by_tick.svg").exists())


if __name__ == "__main__":
    unittest.main()
