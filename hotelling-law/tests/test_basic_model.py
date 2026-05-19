"""Unit tests for core model behaviour."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hotelling.model import HotellingModel


class TestCustomerAssignment(unittest.TestCase):
    """Tests for customer-to-store assignment logic."""

    def _make_model(self, **overrides):
        """Return a small deterministic model, optionally overriding defaults."""
        defaults = dict(
            market_size=100,
            num_customers=1,
            num_stores=2,
            ticks=1,
            price=1.0,
            distance_weight=1.0,
            random_seed=0,
        )
        defaults.update(overrides)
        return HotellingModel(**defaults)

    def test_customer_chooses_lowest_effective_cost(self):
        """Customer should be assigned to the store with the lowest effective cost."""
        model = self._make_model()
        model.stores[0].position = 10.0
        model.stores[1].position = 90.0
        model.customers[0].position = 20.0  # closer to store 0

        for store in model.stores:
            store.reset_metrics()
        model._assign_customers()

        self.assertEqual(model.stores[0].market_share, 1)
        self.assertEqual(model.stores[1].market_share, 0)

    def test_tie_broken_by_lowest_store_id(self):
        """When effective costs are equal the store with the lower id should win."""
        model = self._make_model()
        model.stores[0].position = 40.0
        model.stores[1].position = 60.0
        model.customers[0].position = 50.0  # equidistant from both stores

        for store in model.stores:
            store.reset_metrics()
        model._assign_customers()

        self.assertEqual(model.stores[0].market_share, 1)
        self.assertEqual(model.stores[1].market_share, 0)

    def test_total_market_share_equals_num_customers(self):
        """The sum of market shares across all stores must equal num_customers."""
        model = HotellingModel(
            market_size=100, num_customers=50, num_stores=3,
            ticks=1, price=1.0, distance_weight=1.0, random_seed=42,
        )
        for store in model.stores:
            store.reset_metrics()
        model._assign_customers()

        total = sum(s.market_share for s in model.stores)
        self.assertEqual(total, 50)

    def test_model_runs_without_error(self):
        """Model should complete all ticks and return the correct number of output rows."""
        model = HotellingModel(
            market_size=100, num_customers=50, num_stores=2,
            ticks=20, price=1.0, distance_weight=1.0, random_seed=7,
        )
        rows = model.run()
        # Expect one row per store per tick.
        self.assertEqual(len(rows), 20 * 2)

    def test_loyalty_zero_matches_baseline_assignment(self):
        """loyalty_strength=0.0 should produce identical market shares to the baseline."""
        params = dict(
            market_size=100, num_customers=30, num_stores=2,
            ticks=5, price=1.0, distance_weight=1.0, random_seed=99,
        )
        baseline_model = HotellingModel(**params)
        loyal_model = HotellingModel(**params, loyalty_strength=0.0)

        baseline_rows = baseline_model.run()
        loyal_rows = loyal_model.run()

        for base_row, loyal_row in zip(baseline_rows, loyal_rows):
            self.assertEqual(
                base_row["store_market_share"],
                loyal_row["store_market_share"],
            )


class TestProfitCalculation(unittest.TestCase):
    """Tests for profit and market share calculation."""

    def test_profit_equals_market_share_times_price(self):
        """Each store's profit must equal its market_share multiplied by its price."""
        model = HotellingModel(
            market_size=100, num_customers=20, num_stores=2,
            ticks=1, price=2.0, distance_weight=1.0, random_seed=1,
        )
        for store in model.stores:
            store.reset_metrics()
        model._assign_customers()
        model._calculate_profits()

        for store in model.stores:
            self.assertAlmostEqual(store.profit, store.market_share * store.price)

    def test_market_share_is_reset_between_ticks(self):
        """Market share from a previous tick must not carry over after reset_metrics."""
        model = HotellingModel(
            market_size=100, num_customers=10, num_stores=2,
            ticks=1, price=1.0, distance_weight=1.0, random_seed=3,
        )
        # Simulate two ticks manually and check that reset works.
        for store in model.stores:
            store.reset_metrics()
        model._assign_customers()

        first_shares = [s.market_share for s in model.stores]
        self.assertEqual(sum(first_shares), 10)

        for store in model.stores:
            store.reset_metrics()
        self.assertTrue(all(s.market_share == 0 for s in model.stores))


class TestStoreMovement(unittest.TestCase):
    """Tests for the store position update (local search) logic."""

    def test_stores_stay_within_market_bounds(self):
        """Store positions should never fall outside [0, market_size] after movement."""
        model = HotellingModel(
            market_size=10, num_customers=20, num_stores=2,
            ticks=30, price=1.0, distance_weight=1.0, random_seed=5, step_size=3.0,
        )
        model.run()
        for store in model.stores:
            self.assertGreaterEqual(store.position, 0.0)
            self.assertLessEqual(store.position, 10.0)


if __name__ == "__main__":
    unittest.main()
