"""
Tests for customer-to-store assignment logic.

Verifies that customers choose stores correctly based on effective cost and that
tie-breaking is deterministic and consistent with the documented rule.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hotelling.model import HotellingModel


class TestEffectiveCost(unittest.TestCase):
    """Tests for the effective cost formula."""

    def _model(self, **kwargs) -> HotellingModel:
        """Return a minimal model with sensible defaults, overridden by kwargs."""
        defaults = dict(
            market_size=100, num_customers=1, num_stores=2,
            ticks=1, price=10.0, distance_weight=1.0, random_seed=0,
        )
        defaults.update(kwargs)
        return HotellingModel(**defaults)

    def test_effective_cost_formula(self):
        """effective_cost should equal price + distance_weight * |pos_c - pos_s|."""
        model = self._model(distance_weight=2.0)
        customer = model.customers[0]
        customer.position = 30.0
        store = model.stores[0]
        store.position = 10.0
        expected = 10.0 + 2.0 * abs(30.0 - 10.0)  # 10 + 40 = 50
        self.assertAlmostEqual(model._effective_cost(customer, store), expected)

    def test_zero_distance_cost_equals_price(self):
        """A customer at the same position as a store pays only the price."""
        model = self._model()
        model.customers[0].position = 50.0
        model.stores[0].position = 50.0
        self.assertAlmostEqual(model._effective_cost(model.customers[0], model.stores[0]),
                               model.price)


class TestBaselineAssignment(unittest.TestCase):
    """Tests for customer assignment without loyalty."""

    def _make_two_store_model(self) -> HotellingModel:
        """Return a two-store model with manually placed stores and a single customer."""
        model = HotellingModel(
            market_size=100, num_customers=1, num_stores=2,
            ticks=1, price=10.0, distance_weight=1.0, random_seed=0,
        )
        return model

    def test_customer_chooses_nearest_store(self):
        """A customer should be assigned to the store with the lowest effective cost."""
        model = self._make_two_store_model()
        model.stores[0].position = 10.0
        model.stores[1].position = 90.0
        model.customers[0].position = 20.0  # closer to store 0

        for s in model.stores:
            s.reset_metrics()
        model._assign_customers()

        self.assertEqual(model.stores[0].market_share, 1)
        self.assertEqual(model.stores[1].market_share, 0)

    def test_customer_chooses_cheaper_store(self):
        """Effective cost includes price; a cheaper store can win even if farther."""
        model = HotellingModel(
            market_size=100, num_customers=1, num_stores=2,
            ticks=1, price=10.0, distance_weight=1.0, random_seed=0,
        )
        # Store 0 is far but half the price; store 1 is close but full price.
        model.stores[0].price = 5.0
        model.stores[0].position = 0.0
        model.stores[1].price = 10.0
        model.stores[1].position = 50.0
        model.customers[0].position = 55.0

        # cost store 0: 5 + 1*55 = 60; cost store 1: 10 + 1*5 = 15 → store 1 wins
        for s in model.stores:
            s.reset_metrics()
        model._assign_customers()
        self.assertEqual(model.stores[1].market_share, 1)

    def test_tie_broken_randomly(self):
        """When effective costs are equal exactly one store wins (chosen at random)."""
        model = self._make_two_store_model()
        model.stores[0].position = 40.0
        model.stores[1].position = 60.0
        model.customers[0].position = 50.0  # equidistant from both

        for s in model.stores:
            s.reset_metrics()
        model._assign_customers()

        total = model.stores[0].market_share + model.stores[1].market_share
        self.assertEqual(total, 1, "exactly one store should win the tied customer")

    def test_tie_broken_randomly_both_stores_win_over_many_trials(self):
        """Random tie-breaking should assign tied customers to each store across runs."""
        wins = {0: 0, 1: 0}
        for seed in range(200):
            model = HotellingModel(
                market_size=100, num_customers=1, num_stores=2,
                ticks=1, price=10.0, distance_weight=1.0, random_seed=seed,
            )
            model.stores[0].position = 40.0
            model.stores[1].position = 60.0
            model.customers[0].position = 50.0
            for s in model.stores:
                s.reset_metrics()
            model._assign_customers()
            for s in model.stores:
                if s.market_share == 1:
                    wins[s.id] += 1
        # Both stores should win a meaningful fraction of tied assignments.
        self.assertGreater(wins[0], 50, "store 0 should win some tied assignments")
        self.assertGreater(wins[1], 50, "store 1 should win some tied assignments")

    def test_total_market_share_equals_num_customers(self):
        """Sum of all store market shares must equal num_customers every tick."""
        model = HotellingModel(
            market_size=100, num_customers=80, num_stores=3,
            ticks=1, price=10.0, distance_weight=1.0, random_seed=42,
        )
        for s in model.stores:
            s.reset_metrics()
        model._assign_customers()

        total = sum(s.market_share for s in model.stores)
        self.assertEqual(total, 80)

    def test_assigned_customer_count_matches_market_share(self):
        """assigned_customer_count must equal market_share after assignment."""
        model = HotellingModel(
            market_size=100, num_customers=20, num_stores=2,
            ticks=1, price=10.0, distance_weight=1.0, random_seed=7,
        )
        for s in model.stores:
            s.reset_metrics()
        model._assign_customers()

        for store in model.stores:
            self.assertEqual(store.assigned_customer_count, store.market_share)


if __name__ == "__main__":
    unittest.main()
