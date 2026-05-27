"""
Tests for CSV output generation.

Verifies that CSV files are created at the expected path, contain correct headers,
have the right number of rows, and that numeric fields are parseable.
"""

import csv
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hotelling.csv_writer import (
    NETLOGO_TABLE_HEADERS,
    RAW_HEADERS,
    SUMMARY_HEADERS,
    write_final_tick_raw_csv,
    write_netlogo_table_csv,
    write_raw_csv,
    write_summary_csv,
)
from hotelling.experiment import Experiment
from hotelling.statistics import generate_summary_rows


def _small_experiment(experiment_name: str = "test") -> Experiment:
    """Return a minimal Experiment for fast test runs (1 run, 3 ticks, 2 stores)."""
    return Experiment(
        experiment_name=experiment_name,
        num_runs=1,
        base_seed=0,
        market_size=20,
        num_customers=10,
        num_stores=2,
        ticks=3,
        price=10.0,
        distance_weight=1.0,
        loyalty_strength=0.0,
        loyalty_threshold=10.0,
    )


class TestRawCsvCreation(unittest.TestCase):
    """Tests that write_raw_csv creates a properly structured file."""

    def test_file_is_created(self):
        """write_raw_csv should create the file at the given path."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "raw.csv")
            write_raw_csv(path, _small_experiment().run())
            self.assertTrue(os.path.exists(path))

    def test_creates_nested_directories(self):
        """write_raw_csv should create any missing parent directories."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "a", "b", "raw.csv")
            write_raw_csv(path, _small_experiment().run())
            self.assertTrue(os.path.exists(path))

    def test_raw_headers_match_expected(self):
        """CSV header row must match RAW_HEADERS exactly."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "raw.csv")
            write_raw_csv(path, _small_experiment().run())
            with open(path, newline="", encoding="utf-8") as f:
                self.assertEqual(csv.DictReader(f).fieldnames, RAW_HEADERS)

    def test_raw_row_count(self):
        """Row count should be num_runs * ticks * num_stores (1 * 3 * 2 = 6)."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "raw.csv")
            write_raw_csv(path, _small_experiment().run())
            with open(path, newline="", encoding="utf-8") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 6)

    def test_numeric_fields_parseable(self):
        """All numeric columns should parse as float or int without error."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "raw.csv")
            write_raw_csv(path, _small_experiment().run())
            with open(path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    int(row["tick"])
                    int(row["store_id"])
                    int(row["run_id"])
                    float(row["store_position"])
                    float(row["store_price"])
                    float(row["store_profit"])
                    int(row["store_market_share"])
                    int(row["assigned_customer_count"])
                    float(row["distance_from_centre"])
                    float(row["average_distance_to_other_stores"])

    def test_experiment_name_populated(self):
        """experiment_name column must not be empty."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "raw.csv")
            write_raw_csv(path, _small_experiment(experiment_name="myexp").run())
            with open(path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    self.assertEqual(row["experiment_name"], "myexp")

    def test_final_tick_raw_csv_only_writes_final_tick_rows(self):
        """Final-tick raw CSV should keep one row per store for each run."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "raw_final_tick.csv")
            write_final_tick_raw_csv(path, _small_experiment().run())
            with open(path, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(len(rows), 2)
        self.assertEqual({int(row["tick"]) for row in rows}, {2})
        self.assertEqual({int(row["store_id"]) for row in rows}, {0, 1})

    def test_netlogo_table_csv_matches_behavior_space_shape(self):
        """NetLogo table CSV should have one final-step reporter row per run."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "netlogo_table.csv")
            write_netlogo_table_csv(path, _small_experiment().run())
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

        self.assertEqual(reader.fieldnames, NETLOGO_TABLE_HEADERS)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["[run number]"], "0")
        self.assertEqual(rows[0]["[step]"], "3")
        float(rows[0]["mean [pycor] of turtles"])
        float(rows[0]["standard-deviation [area-count] of turtles"])


class TestSummaryCsvCreation(unittest.TestCase):
    """Tests that write_summary_csv creates a properly structured summary file."""

    def _get_summary_rows(self) -> list:
        """Run a small experiment and generate summary rows."""
        rows = _small_experiment().run()
        return generate_summary_rows(
            rows=rows,
            experiment_name="test",
            scenario_name="test_scenario",
            parameter_name="configuration",
            parameter_value="default",
        )

    def test_summary_file_is_created(self):
        """write_summary_csv should create the file at the given path."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "summary.csv")
            write_summary_csv(path, self._get_summary_rows())
            self.assertTrue(os.path.exists(path))

    def test_summary_headers_match_expected(self):
        """Summary CSV header row must match SUMMARY_HEADERS exactly."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "summary.csv")
            write_summary_csv(path, self._get_summary_rows())
            with open(path, newline="", encoding="utf-8") as f:
                self.assertEqual(csv.DictReader(f).fieldnames, SUMMARY_HEADERS)

    def test_summary_has_one_row_per_metric(self):
        """Summary should have exactly one row for each metric in SUMMARY_METRICS."""
        from hotelling.statistics import SUMMARY_METRICS
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "summary.csv")
            write_summary_csv(path, self._get_summary_rows())
            with open(path, newline="", encoding="utf-8") as f:
                data = list(csv.DictReader(f))
            self.assertEqual(len(data), len(SUMMARY_METRICS))

    def test_summary_mean_is_parseable_float(self):
        """The mean column in summary rows must parse as a float."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "summary.csv")
            write_summary_csv(path, self._get_summary_rows())
            with open(path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    float(row["mean"])
                    float(row["standard_deviation"])
                    float(row["minimum"])
                    float(row["maximum"])
                    int(row["run_count"])


if __name__ == "__main__":
    unittest.main()
