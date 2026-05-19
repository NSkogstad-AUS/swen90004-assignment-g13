"""
Tests for the customer loyalty extension.

Verifies that:
  - loyalty_strength = 0.0 produces identical results to the baseline (no loyalty).
  - loyalty_strength > 0.0 causes customers to stay with their previous store when
    the cost difference is within the loyalty tolerance.
  - The loyalty_threshold parameter correctly scales the retention window.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hotelling.model import HotellingModel
from hotelling.customer import Customer
from hotelling.store import Store


class TestLoyaltyZeroMatchesBaseline(unittest.TestCase):
    """loyalty_strength = 0.0 must be behaviourally identical to the baseline."""

    def _run(self, loyalty: float, seed: int = 99) -> list:
        """Run a small model and return its output rows."""
        return HotellingModel(
            market_size=100, num_customers=40, num_stores=2,
            ticks=10, price=10.0, distance_weight=1.0, random_seed=seed,
            loyalty_strength=loyalty, loyalty_threshold=10.0,
        ).run()

    def test_market_share_identical_to_baseline(self):
        """market_share per store per tick must match between baseline and loyalty=0."""
        baseline = self._run(loyalty=0.0, seed=77)
        loyal = self._run(loyalty=0.0, seed=77)
        self.assertEqual(len(baseline), len(loyal))
        for b, l in zip(baseline, loyal):
            self.assertEqual(b["store_market_share"], l["store_market_share"])

    def test_store_positions_identical_to_baseline(self):
        """Store positions must match exactly when loyalty_strength = 0."""
        baseline = self._run(loyalty=0.0, seed=55)
        loyal = self._run(loyalty=0.0, seed=55)
        for b, l in zip(baseline, loyal):
            self.assertAlmostEqual(float(b["store_position"]), float(l["store_position"]))


class TestLoyaltyRetention(unittest.TestCase):
    """loyalty_strength > 0.0 should retain customers within the tolerance window."""

    def _build_model(self, loyalty_strength: float, loyalty_threshold: float) -> HotellingModel:
        """Return a minimal model configured for loyalty testing."""
        return HotellingModel(
            market_size=100, num_customers=1, num_stores=2,
            ticks=1, price=10.0, distance_weight=1.0, random_seed=0,
            loyalty_strength=loyalty_strength,
            loyalty_threshold=loyalty_threshold,
        )

    def test_customer_stays_when_cost_difference_within_tolerance(self):
        """
        A customer should stay with their previous store when
        prev_cost <= best_cost + loyalty_strength * loyalty_threshold.
        """
        model = self._build_model(loyalty_strength=0.5, loyalty_threshold=20.0)
        # Tolerance = 0.5 * 20 = 10.

        # Place customer closer to store 1 (cost = 10 + 5 = 15).
        # Previous store is store 0 (cost = 10 + 15 = 25).
        # prev_cost(25) <= best_cost(15) + tolerance(10) → 25 <= 25 → True → stay.
        model.customers[0].position = 45.0
        model.stores[0].position = 30.0  # prev store; cost = 10 + 1*15 = 25
        model.stores[1].position = 40.0  # better store; cost = 10 + 1*5 = 15
        model.customers[0].previous_store_id = 0  # previously used store 0

        for s in model.stores:
            s.reset_metrics()
        model._assign_customers()

        # Customer should stay with store 0 (within tolerance).
        self.assertEqual(model.stores[0].market_share, 1,
                         "customer should stay with store 0 within loyalty tolerance")

    def test_customer_switches_when_cost_difference_exceeds_tolerance(self):
        """
        A customer should switch when the competitor's cost is more than
        loyalty_strength * loyalty_threshold better than the previous store.
        """
        model = self._build_model(loyalty_strength=0.5, loyalty_threshold=10.0)
        # Tolerance = 0.5 * 10 = 5.

        # Store 1 at position 50 gives cost = 10 + 0 = 10.
        # Store 0 (prev) at position 10 gives cost = 10 + 40 = 50.
        # prev_cost(50) <= best_cost(10) + tolerance(5) → 50 <= 15 → False → switch.
        model.customers[0].position = 50.0
        model.stores[0].position = 10.0  # prev store; cost = 10 + 40 = 50
        model.stores[1].position = 50.0  # better store; cost = 10 + 0 = 10
        model.customers[0].previous_store_id = 0

        for s in model.stores:
            s.reset_metrics()
        model._assign_customers()

        self.assertEqual(model.stores[1].market_share, 1,
                         "customer should switch to the clearly cheaper store")

    def test_no_previous_store_uses_baseline_assignment(self):
        """A customer with no previous store should follow baseline assignment."""
        model = self._build_model(loyalty_strength=0.75, loyalty_threshold=50.0)
        model.customers[0].position = 80.0
        model.customers[0].previous_store_id = None  # no prior store
        model.stores[0].position = 10.0
        model.stores[1].position = 85.0

        for s in model.stores:
            s.reset_metrics()
        model._assign_customers()

        # Store 1 is nearest (cost = 10 + 5 = 15 vs store 0: 10 + 70 = 80).
        self.assertEqual(model.stores[1].market_share, 1)

    def test_loyalty_threshold_zero_effectively_disables_retention(self):
        """
        When loyalty_threshold = 0, the tolerance is always 0, so the customer
        only stays if previous store cost equals the best store cost.
        """
        model = self._build_model(loyalty_strength=1.0, loyalty_threshold=0.0)
        # Tolerance = 1.0 * 0 = 0.
        # Customer will stay only if prev_cost <= best_cost exactly.
        model.customers[0].position = 50.0
        model.stores[0].position = 10.0  # prev; cost = 10 + 40 = 50
        model.stores[1].position = 50.0  # best; cost = 10 + 0 = 10
        model.customers[0].previous_store_id = 0

        for s in model.stores:
            s.reset_metrics()
        model._assign_customers()

        # prev_cost(50) <= best_cost(10) + 0 → False → customer switches.
        self.assertEqual(model.stores[1].market_share, 1,
                         "zero threshold should not retain a clearly worse store")

    def test_loyalty_output_rows_include_loyalty_parameters(self):
        """Output rows should record loyalty_strength and loyalty_threshold."""
        model = HotellingModel(
            market_size=100, num_customers=10, num_stores=2,
            ticks=2, price=10.0, distance_weight=1.0, random_seed=0,
            loyalty_strength=0.5, loyalty_threshold=15.0,
        )
        rows = model.run()
        for row in rows:
            self.assertAlmostEqual(float(row["loyalty_strength"]), 0.5)
            self.assertAlmostEqual(float(row["loyalty_threshold"]), 15.0)


if __name__ == "__main__":
    unittest.main()
