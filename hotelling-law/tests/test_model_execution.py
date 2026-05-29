"""
Tests for overall model execution and store movement behaviour.

Verifies that the model runs without errors, produces the correct number of
output rows, and keeps stores within market bounds across all ticks.
"""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hotelling.model import HotellingModel


class TestModelRun(unittest.TestCase):
    """Tests that the model executes without crashing and returns correct output."""

    def test_default_netlogo_grid_has_one_customer_per_patch(self):
        """Default setup should place one customer on each -50..50 patch."""
        model = HotellingModel(ticks=0, random_seed=0)
        self.assertEqual(model.num_customers, 101)
        self.assertEqual([c.position for c in model.customers], list(range(-50, 51)))

    def test_default_starting_price_is_ten(self):
        """Stores should start at the NetLogo hardcoded price."""
        model = HotellingModel(ticks=0, random_seed=0)
        self.assertTrue(all(store.price == 10.0 for store in model.stores))

    def test_run_completes_without_exception(self):
        """Model.run() should complete all ticks without raising an exception."""
        model = HotellingModel(
            market_size=100, num_customers=50, num_stores=2,
            ticks=20, price=10.0, distance_weight=1.0, random_seed=7,
        )
        try:
            model.run()
        except Exception as exc:
            self.fail(f"model.run() raised an unexpected exception: {exc}")

    def test_output_row_count(self):
        """Total output rows should equal ticks * num_stores."""
        ticks = 15
        num_stores = 3
        model = HotellingModel(
            market_size=100, num_customers=40, num_stores=num_stores,
            ticks=ticks, price=10.0, distance_weight=1.0, random_seed=11,
        )
        rows = model.run()
        self.assertEqual(len(rows), ticks * num_stores)

    def test_output_rows_cover_all_ticks(self):
        """Output rows should include every tick from 0 to ticks-1."""
        ticks = 10
        model = HotellingModel(
            market_size=100, num_customers=20, num_stores=2,
            ticks=ticks, price=10.0, distance_weight=1.0, random_seed=99,
        )
        rows = model.run()
        recorded_ticks = {r["tick"] for r in rows}
        self.assertEqual(recorded_ticks, set(range(ticks)))

    def test_output_rows_cover_all_store_ids(self):
        """Output rows should include every store id at every tick."""
        model = HotellingModel(
            market_size=100, num_customers=20, num_stores=3,
            ticks=5, price=10.0, distance_weight=1.0, random_seed=3,
        )
        rows = model.run()
        for tick in range(5):
            tick_store_ids = {r["store_id"] for r in rows if r["tick"] == tick}
            self.assertEqual(tick_store_ids, {0, 1, 2})


class TestPricing(unittest.TestCase):
    """Tests store price update behaviour."""

    def test_price_can_drop_below_removed_floor(self):
        """Price updates should not be clamped to the former min_price floor."""
        model = HotellingModel(
            market_size=100, num_customers=0, num_stores=1,
            ticks=1, price=0.5, price_step=1.0, random_seed=0,
        )
        model.run()
        self.assertEqual(model.stores[0].price, -0.5)

    def test_price_plans_are_computed_before_movement_is_applied(self):
        """Price planning should see the same pre-update positions as movement planning."""
        model = HotellingModel(
            market_size=20, num_customers=10, num_stores=2,
            ticks=1, price=10.0, distance_weight=1.0, random_seed=0,
        )
        original_positions = [store.position for store in model.stores]
        seen_positions = []

        def fake_best_position(store):
            return (store.x_position, store.position + 1)

        def fake_best_price(store):
            seen_positions.append(tuple(s.position for s in model.stores))
            return store.price

        with patch.object(HotellingModel, "_best_position", side_effect=fake_best_position):
            with patch.object(HotellingModel, "_best_price", side_effect=fake_best_price):
                model.run()

        self.assertEqual(seen_positions, [tuple(original_positions), tuple(original_positions)])
        self.assertEqual(
            [store.position for store in model.stores],
            [position + 1 for position in original_positions],
        )

    def test_price_ties_prefer_lower_candidate_order(self):
        """Equal simulated revenues should keep the first NetLogo-style price candidate."""
        model = HotellingModel(
            market_size=20, num_customers=1, num_stores=1,
            ticks=0, price=10.0, price_step=1.0, random_seed=0,
        )
        store = model.stores[0]

        with patch.object(HotellingModel, "_simulated_revenue", return_value=5.0):
            self.assertEqual(model._best_price(store), 9.0)


class TestStoreBounds(unittest.TestCase):
    """Tests that store positions stay within centered market bounds after movement."""

    def test_positions_within_bounds_after_run(self):
        """No store position should fall outside the centered market bounds."""
        model = HotellingModel(
            market_size=50, num_customers=30, num_stores=2,
            ticks=50, price=10.0, distance_weight=1.0, random_seed=5, step_size=5.0,
        )
        model.run()
        for store in model.stores:
            self.assertGreaterEqual(store.position, model.market_min)
            self.assertLessEqual(store.position, model.market_max)

    def test_positions_within_bounds_large_step(self):
        """Even with a step_size larger than market_size, positions remain bounded."""
        model = HotellingModel(
            market_size=20, num_customers=10, num_stores=2,
            ticks=30, price=10.0, distance_weight=1.0, random_seed=2, step_size=50.0,
        )
        model.run()
        for store in model.stores:
            self.assertGreaterEqual(store.position, model.market_min)
            self.assertLessEqual(store.position, model.market_max)

    def test_positions_in_recorded_rows_within_bounds(self):
        """Recorded store_position values in output rows must all be within bounds."""
        market_size = 100
        model = HotellingModel(
            market_size=market_size, num_customers=50, num_stores=3,
            ticks=20, price=10.0, distance_weight=1.0, random_seed=8,
        )
        rows = model.run()
        for row in rows:
            pos = float(row["store_position"])
            self.assertGreaterEqual(pos, -market_size / 2.0)
            self.assertLessEqual(pos, market_size / 2.0)

    def test_plane_neighbours_include_four_cardinal_directions(self):
        """Plane layout should use NetLogo neighbors4 movement candidates."""
        model = HotellingModel(
            market_size=4, num_customers=1, num_stores=1,
            ticks=0, price=10.0, random_seed=0, layout="plane",
        )
        self.assertEqual(
            set(model._neighbour_positions((0, 0))),
            {(-1, 0), (1, 0), (0, -1), (0, 1)},
        )

    def test_plane_output_uses_euclidean_distances(self):
        """Plane output distances should match NetLogo distance semantics."""
        model = HotellingModel(
            market_size=10, num_customers=0, num_stores=2,
            ticks=0, price=10.0, random_seed=0, layout="plane",
        )
        model.stores[0].x_position = 3.0
        model.stores[0].position = 4.0
        model.stores[1].x_position = 0.0
        model.stores[1].position = 0.0
        model._record_output(0)

        row = next(r for r in model.output_rows if r["store_id"] == 0)
        self.assertEqual(row["store_x_position"], 3.0)
        self.assertEqual(row["store_y_position"], 4.0)
        self.assertEqual(row["store_position"], 4.0)
        self.assertAlmostEqual(row["distance_from_centre"], 5.0)
        self.assertAlmostEqual(row["average_distance_to_other_stores"], 5.0)


class TestDeterminism(unittest.TestCase):
    """Tests that identical seeds produce identical results."""

    def test_same_seed_gives_identical_output(self):
        """Two runs with the same seed must produce exactly the same output rows."""
        params = dict(
            market_size=100, num_customers=30, num_stores=2,
            ticks=10, price=10.0, distance_weight=1.0, random_seed=42,
        )
        rows_a = HotellingModel(**params).run()
        rows_b = HotellingModel(**params).run()
        self.assertEqual(len(rows_a), len(rows_b))
        for ra, rb in zip(rows_a, rows_b):
            self.assertEqual(ra["store_position"], rb["store_position"])
            self.assertEqual(ra["store_profit"], rb["store_profit"])

    def test_different_seeds_give_different_output(self):
        """Two runs with different seeds should not produce identical positions."""
        params = dict(
            market_size=100, num_customers=30, num_stores=2,
            ticks=5, price=10.0, distance_weight=1.0,
        )
        rows_a = HotellingModel(random_seed=1, **params).run()
        rows_b = HotellingModel(random_seed=999, **params).run()
        positions_a = [r["store_position"] for r in rows_a]
        positions_b = [r["store_position"] for r in rows_b]
        self.assertNotEqual(positions_a, positions_b)


if __name__ == "__main__":
    unittest.main()
