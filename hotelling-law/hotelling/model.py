"""Core simulation model for Hotelling's Law."""

import random
from typing import Dict, List, Optional

from hotelling.customer import Customer
from hotelling.store import Store


class HotellingModel:
    """
    Simulates Hotelling's Law on a one-dimensional market line.

    Stores compete for customers by adjusting their positions each tick.
    Customers choose stores based on effective cost (price + weighted distance).
    Store positions evolve via single-step local search toward higher profit.
    """

    def __init__(
        self,
        market_size: int = 100,
        num_customers: int = 100,
        num_stores: int = 2,
        ticks: int = 50,
        price: float = 1.0,
        distance_weight: float = 1.0,
        step_size: float = 1.0,
        random_seed: Optional[int] = None,
        customer_distribution: str = "uniform",
        loyalty_strength: float = 0.0,
    ):
        """
        Initialise the model with the given parameters.

        Args:
            market_size: Length of the market line (positions run from 0 to market_size).
            num_customers: Number of customers placed on the market line.
            num_stores: Number of competing stores.
            ticks: Number of simulation steps to run.
            price: Fixed price applied to all stores.
            distance_weight: Multiplier for travel distance in effective cost.
            step_size: Maximum distance a store can move per tick.
            random_seed: Seed for the random number generator; None for non-deterministic.
            customer_distribution: 'uniform' or 'clustered'.
            loyalty_strength: Discount applied to a customer's previous store (0.0–1.0).
        """
        self.market_size = market_size
        self.num_customers = num_customers
        self.num_stores = num_stores
        self.ticks = ticks
        self.price = price
        self.distance_weight = distance_weight
        self.step_size = step_size
        self.random_seed = random_seed
        self.customer_distribution = customer_distribution
        self.loyalty_strength = loyalty_strength

        self._rng = random.Random(random_seed)
        self.customers: List[Customer] = []
        self.stores: List[Store] = []
        self.output_rows: List[Dict] = []

        self._initialise()

    def _initialise(self) -> None:
        """Create customers and stores and clear any prior output."""
        self.customers = self._create_customers()
        self.stores = self._create_stores()
        self.output_rows = []

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _create_customers(self) -> List[Customer]:
        """Return a list of customers placed according to customer_distribution."""
        if self.customer_distribution == "uniform":
            return [
                Customer(id=i, position=self._rng.uniform(0.0, float(self.market_size)))
                for i in range(self.num_customers)
            ]
        if self.customer_distribution == "clustered":
            return self._create_clustered_customers()
        raise ValueError(f"Unknown customer_distribution: '{self.customer_distribution}'")

    def _create_clustered_customers(self) -> List[Customer]:
        """
        Return customers distributed around three evenly spaced cluster centres.

        Each customer is assigned to a random cluster, then placed using a Gaussian
        draw (sigma = market_size / 12) clamped to [0, market_size].
        """
        num_clusters = 3
        sigma = self.market_size / 12.0
        centres = [
            self.market_size * (k + 1) / (num_clusters + 1)
            for k in range(num_clusters)
        ]
        customers = []
        for i in range(self.num_customers):
            centre = self._rng.choice(centres)
            pos = self._rng.gauss(centre, sigma)
            pos = max(0.0, min(float(self.market_size), pos))
            customers.append(Customer(id=i, position=pos))
        return customers

    def _create_stores(self) -> List[Store]:
        """Return stores placed at evenly spaced intervals across the market."""
        return [
            Store(
                id=i,
                position=self.market_size * (i + 1) / (self.num_stores + 1),
                price=self.price,
            )
            for i in range(self.num_stores)
        ]

    # ------------------------------------------------------------------
    # Simulation loop
    # ------------------------------------------------------------------

    def run(self) -> List[Dict]:
        """
        Run the simulation for the configured number of ticks.

        Returns the list of output rows (one per store per tick).
        """
        for tick in range(self.ticks):
            self._tick(tick)
        return self.output_rows

    def _tick(self, tick: int) -> None:
        """
        Execute one simulation step in the order:

        1. Reset store metrics.
        2. Assign customers to stores.
        3. Calculate profits.
        4. Update store positions.
        5. Record output rows.
        """
        for store in self.stores:
            store.reset_metrics()
        self._assign_customers()
        self._calculate_profits()
        self._update_store_positions()
        self._record_output(tick)

    # ------------------------------------------------------------------
    # Customer assignment
    # ------------------------------------------------------------------

    def _effective_cost(self, customer: Customer, store: Store) -> float:
        """Return the raw effective cost for a customer visiting a store."""
        return store.price + self.distance_weight * abs(customer.position - store.position)

    def _assign_customers(self) -> None:
        """
        Assign every customer to their chosen store and increment that store's market_share.

        Updates customer.previous_store_id for use in the next tick's loyalty calculation.
        """
        for customer in self.customers:
            chosen = self._choose_store(customer)
            chosen.market_share += 1
            customer.previous_store_id = chosen.id

    def _choose_store(self, customer: Customer) -> Store:
        """
        Return the store a customer will choose.

        Computes effective cost for each store. If loyalty_strength > 0 and the customer
        has a previous store, that store's effective cost is discounted by
        (1 - loyalty_strength), making the customer less likely to switch.
        Ties are broken deterministically by the lowest store id.
        """
        best_store: Optional[Store] = None
        best_cost = float("inf")

        for store in self.stores:
            cost = self._effective_cost(customer, store)

            if (
                self.loyalty_strength > 0.0
                and customer.previous_store_id is not None
                and store.id == customer.previous_store_id
            ):
                cost *= (1.0 - self.loyalty_strength)

            if best_store is None or cost < best_cost or (
                cost == best_cost and store.id < best_store.id
            ):
                best_cost = cost
                best_store = store

        return best_store  # type: ignore[return-value]  # stores list is never empty

    # ------------------------------------------------------------------
    # Profit calculation
    # ------------------------------------------------------------------

    def _calculate_profits(self) -> None:
        """Set each store's profit to market_share * price."""
        for store in self.stores:
            store.profit = store.market_share * store.price

    # ------------------------------------------------------------------
    # Store movement
    # ------------------------------------------------------------------

    def _update_store_positions(self) -> None:
        """Move each store to the neighbouring position that maximises simulated profit."""
        for store in self.stores:
            store.position = self._best_position(store)

    def _best_position(self, store: Store) -> float:
        """
        Return the position (left, stay, or right by step_size) with the highest
        simulated profit for store.

        Candidate positions are clamped to [0, market_size]. Loyalty is not applied
        during this lookahead; it uses raw effective costs only.
        """
        candidates = [
            max(0.0, min(float(self.market_size), store.position - self.step_size)),
            store.position,
            max(0.0, min(float(self.market_size), store.position + self.step_size)),
        ]

        best_pos = store.position
        best_profit = float("-inf")

        for pos in candidates:
            profit = self._simulated_profit(store, pos)
            if profit > best_profit:
                best_profit = profit
                best_pos = pos

        return best_pos

    def _simulated_profit(self, moving_store: Store, candidate_pos: float) -> float:
        """
        Estimate the profit moving_store would earn if positioned at candidate_pos.

        All other stores remain at their current positions. Does not modify any state.
        Tie-breaking follows the same lowest-id rule as regular assignment.
        """
        count = 0
        for customer in self.customers:
            candidate_cost = (
                moving_store.price
                + self.distance_weight * abs(customer.position - candidate_pos)
            )

            chosen_id = moving_store.id
            winning_cost = candidate_cost

            for store in self.stores:
                if store.id == moving_store.id:
                    continue
                cost = self._effective_cost(customer, store)
                if cost < winning_cost or (cost == winning_cost and store.id < chosen_id):
                    winning_cost = cost
                    chosen_id = store.id

            if chosen_id == moving_store.id:
                count += 1

        return count * moving_store.price

    # ------------------------------------------------------------------
    # Output recording
    # ------------------------------------------------------------------

    def _record_output(self, tick: int) -> None:
        """Append one output row per store to output_rows for the given tick."""
        centre = self.market_size / 2.0
        num_stores = len(self.stores)

        for store in self.stores:
            distance_from_centre = abs(store.position - centre)

            if num_stores > 1:
                avg_distance_to_others = sum(
                    abs(store.position - other.position)
                    for other in self.stores
                    if other.id != store.id
                ) / (num_stores - 1)
            else:
                avg_distance_to_others = 0.0

            self.output_rows.append({
                "tick": tick,
                "store_id": store.id,
                "store_position": store.position,
                "store_price": store.price,
                "store_profit": store.profit,
                "store_market_share": store.market_share,
                "distance_from_centre": distance_from_centre,
                "average_distance_to_other_stores": avg_distance_to_others,
            })
