import csv
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "run_custom_experiment.py"


class TestCustomExperimentCli(unittest.TestCase):
    def test_custom_cli_writes_expected_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    os.fspath(SCRIPT),
                    "--layout",
                    "line",
                    "--rules",
                    "moving-only",
                    "--num-stores",
                    "2",
                    "--steps",
                    "2",
                    "--runs",
                    "1",
                    "--output-dir",
                    tmp,
                    "--output-prefix",
                    "smoke",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("[custom] raw output:", result.stdout)

            raw_path = Path(tmp) / "smoke_raw.csv"
            final_path = Path(tmp) / "smoke_raw_2.csv"
            summary_path = Path(tmp) / "smoke_summary.csv"
            netlogo_path = Path(tmp) / "smoke_summary_netlogo.csv"

            for path in (raw_path, final_path, summary_path, netlogo_path):
                self.assertTrue(path.exists(), path)

            with raw_path.open(newline="", encoding="utf-8") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 4)

            with final_path.open(newline="", encoding="utf-8") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 2)

            with netlogo_path.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["layout"], "line")
            self.assertEqual(rows[0]["rules"], "moving-only")
            self.assertEqual(rows[0]["number-of-stores"], "2")
            self.assertEqual(rows[0]["[step]"], "2")


if __name__ == "__main__":
    unittest.main()
