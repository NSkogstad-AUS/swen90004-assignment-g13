"""Core simulation model for Hotelling's Law."""

import random
from typing import Dict, List, Optional

from hotelling.customer import Customer
from hotelling.store import Store


class HotellingModel:
    """
    Simulates Hotelling's Law on a one-dimensional market line.

    Stores compete for customers by adjusting their positions each tick.
    Customers choose stores based on effective cost (price + weighted travel distance).
    Store positions evolve via a single-step local search aimed at maximising profit.

    Assumptions:
    - Customer positions are fixed throughout the run.
    - All stores share the same fixed price.
    - Stores update positions sequentially in id order (lower ids move first).
    - The position lookahead does not account for simultaneous store movement.
    - Loyalty applies only from the second tick onward (no previous store on tick 0).
    - Loyalty is NOT applied during the store-position lookahead; stores optimise on
      raw effective costs only.
    """

    def __init__(
        self,
        market_size: int = 100,
        num_customers: int = 100,
        num_stores: int = 2,
        ticks: int = 100,
        price: float = 10.0,
        distance_weight: float = 1.0,
        step_size: float = 1.0,
        random_seed: Optional[int] = None,
        customer_distribution: str = "uniform",
        loyalty_strength: float = 0.0,
        loyalty_threshold: float = 10.0,
    ):
        """
        Initialise the model with the given parameters.

        Args:
            market_size: Length of the market line; positions span [0, market_size].
            num_customers: Number of customers placed on the market line.
            num_stores: Number of competing stores.
            ticks: Number of simulation steps to execute.
            price: Fixed price charged by every store.
            distance_weight: Multiplier applied to travel distance in effective cost.
            step_size: Maximum distance a store can move per tick.
            random_seed: Seed for the RNG; None yields non-deterministic behaviour.
            customer_distribution: 'uniform' or 'clustered'.
            loyalty_strength: Controls how much previous-store preference influences
                              customer choice (0.0 = no loyalty, see _choose_store).
            loyalty_threshold: Absolute cost margin used in the loyalty check.
                               A customer stays with their previous store if
                               prev_cost <= best_cost + loyalty_strength * loyalty_threshold.
        """
        # --- Simulation parameters ---
        self.market_size: int = market_size
        self.num_customers: int = num_customers
        self.num_stores: int = num_stores
        self.ticks: int = ticks
        self.price: float = price
        self.distance_weight: float = distance_weight
        self.step_size: float = step_size
        self.random_seed: Optional[int] = random_seed
        self.customer_distribution: str = customer_distribution
        self.loyalty_strength: float = loyalty_strength
        self.loyalty_threshold: float = loyalty_threshold

        # --- Runtime state ---
        self._rng = random.Random(random_seed)
        self.customers: List[Customer] = []
        self.stores: List[Store] = []
        self.output_rows: List[Dict] = []

        self._initialise()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _initialise(self) -> None:
        """Create customers and stores, and clear any prior output rows."""
        self.customers = self._create_customers()
        self.stores = self._create_stores()
        self.output_rows = []

    def _create_customers(self) -> List[Customer]:
        """
        Return a list of customers placed according to customer_distribution.

        Raises ValueError for unknown distribution names.
        """
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

        Each customer is assigned to a randomly chosen cluster, then placed using
        a Gaussian draw with sigma = market_size / 12, clamped to [0, market_size].
        Three clusters and this sigma produce noticeable but overlapping groups.
        """
        num_clusters = 3
        sigma = self.market_size / 12.0
        # Cluster centres at 25%, 50%, 75% of market_size.
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
        """
        Return stores placed at evenly spaced intervals across the market.

        Store i starts at market_size * (i+1) / (num_stores+1), ensuring no store
        begins at the boundary and all stores are symmetrically distributed.
        """
        return [
            Store(
                id=i,
                position=float(self.market_size) * (i + 1) / (self.num_stores + 1),
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

        Returns the accumulated output_rows list (one dict per store per tick).
        """
        for tick in range(self.ticks):
            self._tick(tick)
        return self.output_rows

    def _tick(self, tick: int) -> None:
        """
        Execute one simulation step in the following order:

        1. Reset per-tick store metrics.
        2. Assign customers to stores (updates customer.previous_store_id).
        3. Calculate profit for each store.
        4. Record output metrics (position and profit before any movement).
        5. Update store positions via local search.
        """
        # Step 1: reset metrics.
        for store in self.stores:
            store.reset_metrics()

        # Step 2: assign customers; previous_store_id updated inside.
        self._assign_customers()

        # Step 3: compute profits.
        self._calculate_profits()

        # Step 4: record state before stores move.
        self._record_output(tick)

        # Step 5: move stores toward higher-profit positions.
        self._update_store_positions()

    # ------------------------------------------------------------------
    # Customer assignment
    # ------------------------------------------------------------------

    def _effective_cost(self, customer: Customer, store: Store) -> float:
        """
        Return the raw effective cost for a customer considering a specific store.

        Formula: price + distance_weight * |customer.position - store.position|
        """
        return store.price + self.distance_weight * abs(customer.position - store.position)

    def _assign_customers(self) -> None:
        """
        Assign every customer to their chosen store and update per-tick counts.

        After assignment, each customer's previous_store_id is updated so that
        loyalty effects are available in the following tick.
        """
        for customer in self.customers:
            chosen = self._choose_store(customer)
            chosen.market_share += 1
            chosen.assigned_customer_count += 1
            customer.previous_store_id = chosen.id

    def _choose_store(self, customer: Customer) -> Store:
        """
        Return the store a customer will choose this tick.

        When loyalty_strength is 0.0 (or the customer has no previous store), the
        customer simply chooses the store with the lowest effective cost, with ties
        broken by the lowest store id.

        When loyalty_strength > 0.0 and the customer has a previous store:
          1. Identify the best store by raw effective cost (ties: lowest id).
          2. Compute the effective cost of the previous store.
          3. If prev_cost <= best_cost + loyalty_strength * loyalty_threshold,
             the customer stays with their previous store.
          4. Otherwise, the customer switches to the best store.

        This ensures loyalty_strength = 0.0 is behaviourally identical to the
        baseline (no loyalty) model.
        """
        # With no loyalty active, use the fast baseline path.
        if self.loyalty_strength <= 0.0 or customer.previous_store_id is None:
            return self._choose_store_baseline(customer)

        # Loyalty path: find best store, then check if previous store is close enough.
        best_store = self._choose_store_baseline(customer)
        previous_store = self._store_by_id(customer.previous_store_id)

        # If the previous store no longer exists (edge case), fall back to baseline.
        if previous_store is None:
            return best_store

        prev_cost = self._effective_cost(customer, previous_store)
        best_cost = self._effective_cost(customer, best_store)

        # Stay with previous store if its cost is within the loyalty tolerance.
        loyalty_tolerance = self.loyalty_strength * self.loyalty_threshold
        if prev_cost <= best_cost + loyalty_tolerance:
            return previous_store

        return best_store

    def _choose_store_baseline(self, customer: Customer) -> Store:
        """
        Return the store with the lowest effective cost for a customer.

        Ties are broken deterministically by the lowest store id.  This method
        never applies any loyalty adjustment.
        """
        best_store: Optional[Store] = None
        best_cost = float("inf")

        for store in self.stores:
            cost = self._effective_cost(customer, store)
            if best_store is None or cost < best_cost or (
                cost == best_cost and store.id < best_store.id
            ):
                best_cost = cost
                best_store = store

        return best_store  # type: ignore[return-value]  # stores list is never empty

    def _store_by_id(self, store_id: int) -> Optional[Store]:
        """Return the Store with the given id, or None if not found."""
        for store in self.stores:
            if store.id == store_id:
                return store
        return None

    # ------------------------------------------------------------------
    # Profit calculation
    # ------------------------------------------------------------------

    def _calculate_profits(self) -> None:
        """
        Set each store's profit to market_share * price.

        Profit is computed after customer assignment so that market_share is final.
        """
        for store in self.stores:
            store.profit = store.market_share * store.price

    # ------------------------------------------------------------------
    # Store movement
    # ------------------------------------------------------------------

    def _update_store_positions(self) -> None:
        """
        Move each store to the neighbouring position that maximises simulated profit.

        Stores are updated in id order.  Because positions are updated sequentially,
        a store that moves first may alter the market for stores with higher ids.
        This is a deterministic sequential update strategy.
        """
        for store in self.stores:
            store.position = self._best_position(store)

    def _best_position(self, store: Store) -> float:
        """
        Return the candidate position (left, stay, or right) with the highest
        simulated profit for the given store.

        Three candidates are evaluated:
          - store.position - step_size  (clamped to 0)
          - store.position              (current position)
          - store.position + step_size  (clamped to market_size)

        Ties are broken by preferring the current position, then the numerically
        lowest position (i.e. left over right when both tie with stay).
        Loyalty is not applied in this lookahead.
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
            # Prefer higher profit; break ties by keeping current position (evaluated
            # second), then favouring numerically smaller position.
            if profit > best_profit or (
                profit == best_profit and pos == store.position
            ):
                best_profit = profit
                best_pos = pos

        return best_pos

    def _simulated_profit(self, moving_store: Store, candidate_pos: float) -> float:
        """
        Estimate the profit moving_store would earn if placed at candidate_pos.

        All other stores remain at their current positions.  Does not modify any
        model state.  Uses the same tie-breaking rule (lowest store id) as regular
        assignment.  Loyalty is not applied.
        """
        count = 0
        for customer in self.customers:
            # Cost for moving_store at the candidate position.
            candidate_cost = (
                moving_store.price
                + self.distance_weight * abs(customer.position - candidate_pos)
            )

            # Start assuming moving_store wins this customer.
            chosen_id = moving_store.id
            winning_cost = candidate_cost

            # Check each competitor at its current position.
            for store in self.stores:
                if store.id == moving_store.id:
                    continue
                cost = self._effective_cost(customer, store)
                if cost < winning_cost or (
                    cost == winning_cost and store.id < chosen_id
                ):
                    winning_cost = cost
                    chosen_id = store.id

            if chosen_id == moving_store.id:
                count += 1

        return count * moving_store.price

    # ------------------------------------------------------------------
    # Output recording
    # ------------------------------------------------------------------

    def _record_output(self, tick: int) -> None:
        """
        Append one output row per store to output_rows.

        Called after profit calculation and before store movement, so
        store_position reflects where the store was when it earned its profit.
        Parameter fields are embedded in every row to make the CSV self-contained.
        """
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
                # Tick and store identity.
                "tick": tick,
                "store_id": store.id,
                # Store state this tick.
                "store_position": round(store.position, 6),
                "store_price": store.price,
                "store_profit": round(store.profit, 6),
                "store_market_share": store.market_share,
                "assigned_customer_count": store.assigned_customer_count,
                # Derived spatial metrics.
                "distance_from_centre": round(distance_from_centre, 6),
                "average_distance_to_other_stores": round(avg_distance_to_others, 6),
                # Model parameters embedded for self-contained CSV rows.
                "num_stores": self.num_stores,
                "num_customers": self.num_customers,
                "market_size": self.market_size,
                "distance_weight": self.distance_weight,
                "step_size": self.step_size,
                "customer_distribution": self.customer_distribution,
                "loyalty_strength": self.loyalty_strength,
                "loyalty_threshold": self.loyalty_threshold,
                "random_seed": self.random_seed,
                # experiment_name and run_id are added by the Experiment runner.
            })
