"""Unit tests for CSV output generation."""

import csv
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hotelling.csv_writer import HEADERS, write_csv
from hotelling.experiment import Experiment


def _small_experiment(experiment_name: str = "test") -> Experiment:
    """Return a minimal Experiment suitable for fast tests."""
    return Experiment(
        experiment_name=experiment_name,
        num_runs=1,
        base_seed=0,
        market_size=20,
        num_customers=10,
        num_stores=2,
        ticks=3,
        price=1.0,
        distance_weight=1.0,
        loyalty_strength=0.0,
    )


class TestCsvFileCreation(unittest.TestCase):
    """Tests that write_csv creates a valid file."""

    def test_file_is_created(self):
        """write_csv should create the output file at the specified path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "output.csv")
            rows = _small_experiment().run()
            write_csv(path, rows)
            self.assertTrue(os.path.exists(path))

    def test_creates_parent_directories(self):
        """write_csv should create intermediate directories if they do not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "nested", "dir", "output.csv")
            rows = _small_experiment().run()
            write_csv(path, rows)
            self.assertTrue(os.path.exists(path))


class TestCsvHeaders(unittest.TestCase):
    """Tests that the CSV file contains the expected column headers."""

    def test_headers_match_expected(self):
        """CSV file should contain exactly the columns defined in HEADERS, in order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "output.csv")
            rows = _small_experiment().run()
            write_csv(path, rows)
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, HEADERS)


class TestCsvRowCount(unittest.TestCase):
    """Tests that the CSV contains the correct number of rows."""

    def test_row_count_matches_ticks_times_stores(self):
        """Row count should be num_runs * ticks * num_stores (1 * 3 * 2 = 6)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "output.csv")
            rows = _small_experiment().run()
            write_csv(path, rows)
            with open(path, newline="", encoding="utf-8") as f:
                data = list(csv.DictReader(f))
            self.assertEqual(len(data), 6)


class TestCsvValues(unittest.TestCase):
    """Tests that CSV values are correctly typed and within expected ranges."""

    def _read_rows(self) -> list:
        """Write a small experiment and return the parsed CSV rows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "output.csv")
            rows = _small_experiment().run()
            write_csv(path, rows)
            with open(path, newline="", encoding="utf-8") as f:
                return list(csv.DictReader(f))

    def test_numeric_fields_are_parseable(self):
        """Numeric columns should parse as float or int without raising ValueError."""
        for row in self._read_rows():
            float(row["store_position"])
            float(row["store_price"])
            float(row["store_profit"])
            int(row["store_market_share"])
            float(row["distance_from_centre"])
            float(row["average_distance_to_other_stores"])
            int(row["tick"])
            int(row["store_id"])
            int(row["run_id"])

    def test_experiment_name_is_populated(self):
        """experiment_name column should not be empty."""
        for row in self._read_rows():
            self.assertTrue(len(row["experiment_name"]) > 0)

    def test_parameters_summary_is_populated(self):
        """parameters_summary column should contain at least one key=value pair."""
        for row in self._read_rows():
            self.assertIn("=", row["parameters_summary"])


if __name__ == "__main__":
    unittest.main()
