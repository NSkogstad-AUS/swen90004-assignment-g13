"""
Tests for store metric calculation (market share, profit, reset).

Verifies that profits are computed correctly and that reset_metrics clears
per-tick state so that values do not carry over between ticks.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hotelling.model import HotellingModel
from hotelling.store import Store


class TestProfitCalculation(unittest.TestCase):
    """Tests for the profit = market_share * price formula."""

    def test_profit_formula(self):
        """Profit must equal market_share * price after _calculate_profits."""
        model = HotellingModel(
            market_size=100, num_customers=40, num_stores=2,
            ticks=1, price=5.0, distance_weight=1.0, random_seed=1,
        )
        for s in model.stores:
            s.reset_metrics()
        model._assign_customers()
        model._calculate_profits()

        for store in model.stores:
            self.assertAlmostEqual(store.profit, store.market_share * store.price)

    def test_total_profit_equals_total_customers_times_price(self):
        """Total profit across all stores equals num_customers * price."""
        model = HotellingModel(
            market_size=100, num_customers=60, num_stores=3,
            ticks=1, price=8.0, distance_weight=1.0, random_seed=2,
        )
        for s in model.stores:
            s.reset_metrics()
        model._assign_customers()
        model._calculate_profits()

        total_profit = sum(s.profit for s in model.stores)
        expected = 60 * 8.0
        self.assertAlmostEqual(total_profit, expected)

    def test_zero_market_share_gives_zero_profit(self):
        """A store with no customers earns zero profit."""
        store = Store(id=0, position=50.0, price=10.0)
        store.market_share = 0
        store.profit = store.market_share * store.price
        self.assertAlmostEqual(store.profit, 0.0)


class TestResetMetrics(unittest.TestCase):
    """Tests that reset_metrics clears per-tick state correctly."""

    def test_reset_clears_market_share(self):
        """market_share must be 0 after reset_metrics."""
        store = Store(id=0, position=50.0, price=10.0)
        store.market_share = 42
        store.reset_metrics()
        self.assertEqual(store.market_share, 0)

    def test_reset_clears_assigned_customer_count(self):
        """assigned_customer_count must be 0 after reset_metrics."""
        store = Store(id=0, position=50.0, price=10.0)
        store.assigned_customer_count = 17
        store.reset_metrics()
        self.assertEqual(store.assigned_customer_count, 0)

    def test_reset_clears_profit(self):
        """profit must be 0.0 after reset_metrics."""
        store = Store(id=0, position=50.0, price=10.0)
        store.profit = 999.9
        store.reset_metrics()
        self.assertAlmostEqual(store.profit, 0.0)

    def test_reset_does_not_affect_position_or_price(self):
        """reset_metrics must not modify position or price."""
        store = Store(id=1, position=25.0, price=15.0)
        store.reset_metrics()
        self.assertAlmostEqual(store.position, 25.0)
        self.assertAlmostEqual(store.price, 15.0)

    def test_market_share_does_not_accumulate_across_ticks(self):
        """Values from a previous tick must not be present after reset."""
        model = HotellingModel(
            market_size=100, num_customers=30, num_stores=2,
            ticks=1, price=10.0, distance_weight=1.0, random_seed=5,
        )
        # Simulate tick 0 manually.
        for s in model.stores:
            s.reset_metrics()
        model._assign_customers()
        model._calculate_profits()

        shares_tick0 = [s.market_share for s in model.stores]
        self.assertEqual(sum(shares_tick0), 30)

        # Reset and verify everything clears.
        for s in model.stores:
            s.reset_metrics()
        self.assertTrue(all(s.market_share == 0 for s in model.stores))
        self.assertTrue(all(s.profit == 0.0 for s in model.stores))


if __name__ == "__main__":
    unittest.main()
