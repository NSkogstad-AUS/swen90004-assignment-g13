import csv
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "run_loyalty_examples.py"


class TestLoyaltyExamplesCli(unittest.TestCase):
    def test_loyalty_examples_cli_writes_combined_outputs_and_plots(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            result = subprocess.run(
                [
                    sys.executable,
                    os.fspath(SCRIPT),
                    "--strengths",
                    "0.0,0.75",
                    "--num-stores",
                    "3",
                    "--steps",
                    "2",
                    "--runs",
                    "1",
                    "--output-dir",
                    tmp,
                    "--plot-dir",
                    os.fspath(tmp_path / "plots"),
                    "--output-prefix",
                    "loyalty_examples_smoke",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("[loyalty-examples] Summary output:", result.stdout)

            summary_path = tmp_path / "loyalty_examples_smoke_summary.csv"
            self.assertTrue(summary_path.exists(), summary_path)

            with summary_path.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))

            self.assertEqual(len(rows), 12)
            self.assertEqual(
                sorted({row["parameter_value"] for row in rows}),
                ["0.0", "0.75"],
            )
            self.assertIn("market_share_variation", {row["metric_name"] for row in rows})

            plot_dir = tmp_path / "plots"
            for filename in (
                "loyalty_examples_smoke_distance_from_centre.svg",
                "loyalty_examples_smoke_average_distance_to_other_stores.svg",
                "loyalty_examples_smoke_store_profit.svg",
                "loyalty_examples_smoke_market_share_variation.svg",
            ):
                self.assertTrue((plot_dir / filename).exists(), filename)


if __name__ == "__main__":
    unittest.main()
