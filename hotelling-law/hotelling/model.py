"""Core simulation model for Hotelling's Law."""

import random
from typing import Dict, List, Optional

from hotelling.customer import Customer
from hotelling.store import Store


class HotellingModel:
    """
    Simulates Hotelling's Law on a one-dimensional market line.

    Replicates the behaviour of the NetLogo Hotelling's Law model (Ottino, Stonedahl &
    Wilensky, 2009) using the 'line' layout.  Each tick, stores independently optimise
    their position (left/stay/right) and then their price (down/stay/up) to maximise
    revenue.  Customers choose the store with the lowest sum of price and distance.

    Assumptions:
    - Customer positions are integer-valued, matching NetLogo's discrete patches.
    - Customer positions are fixed throughout a run.
    - Position and price updates are simultaneous: all stores compute their new
      position/price before any store moves, matching the NetLogo task-based approach.
    - Tie-breaking in customer assignment is random, matching NetLogo's min-one-of.
    - The position lookahead uses current prices; the price lookahead uses the updated
      positions, matching the NetLogo tick order.
    - A store with zero market share must move (status quo excluded from candidates),
      matching NetLogo's "only consider status quo if area-count > 0" rule.
    - Loyalty applies only from the second tick onward (no previous_store_id on tick 0).
    - Loyalty is not applied during the store-optimisation lookahead.
    - distance_weight = 1.0 by default, matching the NetLogo formula:
      effective_cost = price + distance.
    """

    def __init__(
        self,
        market_size: int = 100,
        num_customers: int = 500,
        num_stores: int = 2,
        ticks: int = 100,
        price: float = 10.0,
        price_step: float = 1.0,
        min_price: float = 1.0,
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
            market_size: Length of the market line; integer positions span [0, market_size].
            num_customers: Number of customers placed on the market line.
            num_stores: Number of competing stores.
            ticks: Number of simulation steps to execute.
            price: Initial price for every store.  Prices evolve dynamically each tick.
            price_step: Amount by which a store can raise or lower its price each tick.
                        Matches the NetLogo model's ±1 price unit per tick.
            min_price: Floor on store prices.  Prices cannot fall below this value.
                       The NetLogo model has an implicit floor of 1 via its emergency
                       price-drop procedure.
            distance_weight: Multiplier applied to travel distance in effective cost.
                             Set to 1.0 to match the NetLogo model (no weighting).
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
        self.price: float = price             # initial price; stores diverge over time
        self.price_step: float = price_step
        self.min_price: float = min_price
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
        Return customers placed according to customer_distribution.

        Positions are integer-valued (0 to market_size), matching NetLogo's discrete
        patches.  Raises ValueError for unknown distribution names.
        """
        if self.customer_distribution == "uniform":
            return [
                Customer(id=i, position=self._rng.randint(0, self.market_size))
                for i in range(self.num_customers)
            ]
        if self.customer_distribution == "clustered":
            return self._create_clustered_customers()
        raise ValueError(f"Unknown customer_distribution: '{self.customer_distribution}'")

    def _create_clustered_customers(self) -> List[Customer]:
        """
        Return customers distributed around three evenly spaced cluster centres.

        Each customer is assigned to a random cluster, then positioned using a Gaussian
        draw (sigma = market_size / 12) rounded to the nearest integer and clamped to
        [0, market_size].  Integer positions match NetLogo's patch model.
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
            pos = round(self._rng.gauss(centre, sigma))
            pos = max(0, min(self.market_size, pos))
            customers.append(Customer(id=i, position=pos))
        return customers

    def _create_stores(self) -> List[Store]:
        """
        Return stores at random integer positions, matching the NetLogo setup procedure.

        Each store is placed on a randomly chosen consumer patch (integer position in
        [0, market_size]).  Multiple stores may share an initial position.  All stores
        start with the same initial price; prices diverge dynamically each tick.
        """
        return [
            Store(
                id=i,
                position=self._rng.randint(0, self.market_size),
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
        Execute one simulation step, matching the NetLogo tick order:

        1. Reset per-tick store metrics.
        2. Assign customers to stores (based on current positions and prices).
        3. Calculate revenue for each store.
        4. Record output metrics (state before this tick's optimisation moves).
        5. Update store positions via local search (fixes prices, varies position).
        6. Update store prices via local search (uses new positions, varies price).
        """
        for store in self.stores:
            store.reset_metrics()
        self._assign_customers()
        self._calculate_profits()
        self._record_output(tick)
        self._update_store_positions()
        self._update_store_prices()

    # ------------------------------------------------------------------
    # Customer assignment
    # ------------------------------------------------------------------

    def _effective_cost(self, customer: Customer, store: Store) -> float:
        """
        Return the effective cost for a customer visiting a store.

        Formula: store.price + distance_weight * |customer.position - store.position|
        With distance_weight = 1.0 (default) this matches the NetLogo formula:
        effective_cost = price + distance.
        """
        return store.price + self.distance_weight * abs(customer.position - store.position)

    def _assign_customers(self) -> None:
        """
        Assign every customer to their chosen store, increment market_share and
        assigned_customer_count, then update previous_store_id for the loyalty extension.
        """
        for customer in self.customers:
            chosen = self._choose_store(customer)
            chosen.market_share += 1
            chosen.assigned_customer_count += 1
            customer.previous_store_id = chosen.id

    def _choose_store(self, customer: Customer) -> Store:
        """
        Return the store a customer will choose this tick.

        When loyalty_strength = 0 or the customer has no previous store, selects the
        store with the lowest effective cost.  Ties are broken by the lowest store id
        (NetLogo uses random tie-breaking — a documented difference).

        When loyalty_strength > 0 and the customer has a previous store:
          1. Find the best store by raw effective cost.
          2. If prev_cost <= best_cost + loyalty_strength * loyalty_threshold, stay.
          3. Otherwise switch to the best store.

        This ensures loyalty_strength = 0 is behaviourally identical to the baseline.
        """
        if self.loyalty_strength <= 0.0 or customer.previous_store_id is None:
            return self._choose_store_baseline(customer)

        best_store = self._choose_store_baseline(customer)
        previous_store = self._store_by_id(customer.previous_store_id)
        if previous_store is None:
            return best_store

        prev_cost = self._effective_cost(customer, previous_store)
        best_cost = self._effective_cost(customer, best_store)
        if prev_cost <= best_cost + self.loyalty_strength * self.loyalty_threshold:
            return previous_store
        return best_store

    def _choose_store_baseline(self, customer: Customer) -> Store:
        """
        Return the store with the lowest effective cost for a customer.

        Matches NetLogo's min-one-of: when two or more stores tie on effective cost,
        one of the tied stores is chosen at random using the seeded RNG.
        No loyalty adjustment is applied.
        """
        min_cost = min(self._effective_cost(customer, s) for s in self.stores)
        tied = [s for s in self.stores if self._effective_cost(customer, s) == min_cost]
        return self._rng.choice(tied)

    def _store_by_id(self, store_id: int) -> Optional[Store]:
        """Return the Store with the given id, or None if not found."""
        for store in self.stores:
            if store.id == store_id:
                return store
        return None

    # ------------------------------------------------------------------
    # Revenue / profit calculation
    # ------------------------------------------------------------------

    def _calculate_profits(self) -> None:
        """
        Set each store's profit (revenue) to market_share * price.

        With zero production cost, revenue equals profit.  This formula matches
        the NetLogo model: revenue = area-count * price.
        """
        for store in self.stores:
            store.profit = store.market_share * store.price

    # ------------------------------------------------------------------
    # Store position optimisation
    # ------------------------------------------------------------------

    def _update_store_positions(self) -> None:
        """
        Move all stores simultaneously to their best neighbouring position.

        Matches NetLogo's task-based simultaneous update: every store computes its new
        position using the pre-move state of all stores, then all moves are applied at
        once.  Prices are held fixed during this step.
        """
        new_positions = [self._best_position(store) for store in self.stores]
        for store, pos in zip(self.stores, new_positions):
            store.position = pos

    def _best_position(self, store: Store) -> float:
        """
        Return the position with the highest simulated revenue, price held fixed.

        Matches the NetLogo new-location-task logic:
        - If the store had customers this tick (market_share > 0), the current position
          is included and preferred on ties (NetLogo: fput patch-here possible-moves).
        - If the store had zero customers, the current position is excluded; the store
          must move (NetLogo: "only consider status quo if area-count > 0").  Direction
          is chosen randomly on ties.
        Candidates are clamped to [0, market_size].
        """
        stay = round(store.position)
        left = max(0, min(self.market_size, round(store.position - self.step_size)))
        right = max(0, min(self.market_size, round(store.position + self.step_size)))

        if store.market_share > 0:
            # Status quo included; it wins ties (placed first, stable sort equivalent).
            candidates = list(dict.fromkeys([stay, left, right]))  # deduplicate, keep order
        else:
            # Must move; shuffle so neither direction is favoured when they tie.
            move_candidates = list({left, right} - {stay})
            if not move_candidates:
                move_candidates = [stay]  # at boundary with no room to move
            self._rng.shuffle(move_candidates)
            candidates = move_candidates

        best_pos = stay
        best_rev = float("-inf")
        for pos in candidates:
            rev = self._simulated_revenue(store, pos, store.price)
            if rev > best_rev or (rev == best_rev and store.market_share > 0 and pos == stay):
                best_rev = rev
                best_pos = pos
        return best_pos

    # ------------------------------------------------------------------
    # Store price optimisation
    # ------------------------------------------------------------------

    def _update_store_prices(self) -> None:
        """
        Adjust all stores' prices simultaneously to maximise simulated revenue.

        Matches NetLogo's task-based simultaneous update: every store computes its new
        price using the current prices of all competitors, then all changes are applied
        at once.  Positions are fixed at the values set by _update_store_positions.
        """
        new_prices = [self._best_price(store) for store in self.stores]
        for store, price in zip(self.stores, new_prices):
            store.price = price

    def _best_price(self, store: Store) -> float:
        """
        Return the price (down, stay, or up by price_step) with the highest simulated
        revenue, holding the store's current position fixed.

        Matches the NetLogo new-price-task logic:
        - Status quo wins ties (equivalent to NetLogo's sort-by stability).
        - Emergency procedure: if all candidate prices yield zero revenue and the
          current price is above min_price, lower the price by price_step.  This
          prevents stores from being permanently stuck with zero market share.
        - Prices are floored at min_price.
        """
        candidates = [
            max(self.min_price, store.price - self.price_step),
            store.price,
            store.price + self.price_step,
        ]
        revenues = [
            self._simulated_revenue(store, store.position, p) for p in candidates
        ]

        # Emergency: all revenues zero and price above floor — drop price to attract customers.
        if all(r == 0.0 for r in revenues) and store.price > self.min_price:
            return max(self.min_price, store.price - self.price_step)

        best_price = store.price
        best_rev = float("-inf")
        for price, rev in zip(candidates, revenues):
            if rev > best_rev or (rev == best_rev and price == store.price):
                best_rev = rev
                best_price = price
        return best_price

    # ------------------------------------------------------------------
    # Shared simulation helper
    # ------------------------------------------------------------------

    def _simulated_revenue(
        self, moving_store: Store, candidate_pos: float, candidate_price: float
    ) -> float:
        """
        Estimate the revenue moving_store would earn if at candidate_pos with candidate_price.

        All other stores remain at their current positions and prices.  Does not modify
        any model state.  Loyalty is not applied.

        Tie-breaking is random (matching NetLogo's min-one-of behaviour), using the
        seeded RNG.  This makes the lookahead stochastic but deterministic for a given
        seed, correctly replicating the NetLogo potential-market-share procedure.
        """
        count = 0
        for customer in self.customers:
            candidate_cost = (
                candidate_price
                + self.distance_weight * abs(customer.position - candidate_pos)
            )
            # Collect (cost, store_id) for all stores, with moving_store at its candidate.
            store_costs = [(candidate_cost, moving_store.id)]
            for store in self.stores:
                if store.id != moving_store.id:
                    store_costs.append((self._effective_cost(customer, store), store.id))

            min_cost = min(c for c, _ in store_costs)
            tied_ids = [sid for c, sid in store_costs if c == min_cost]
            # Random choice among tied stores matches NetLogo's min-one-of.
            chosen_id = self._rng.choice(tied_ids)

            if chosen_id == moving_store.id:
                count += 1
        return count * candidate_price

    # ------------------------------------------------------------------
    # Output recording
    # ------------------------------------------------------------------

    def _record_output(self, tick: int) -> None:
        """
        Append one output row per store to output_rows for the given tick.

        Called after revenue calculation and before position/price updates, so
        store_position and store_price reflect the state when revenue was earned.
        All model parameters are embedded in every row for self-contained CSV output.
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
                "tick": tick,
                "store_id": store.id,
                "store_position": store.position,
                "store_price": round(store.price, 6),
                "store_profit": round(store.profit, 6),
                "store_market_share": store.market_share,
                "assigned_customer_count": store.assigned_customer_count,
                "distance_from_centre": round(distance_from_centre, 6),
                "average_distance_to_other_stores": round(avg_distance_to_others, 6),
                # Model parameters embedded for self-contained CSV rows.
                "num_stores": self.num_stores,
                "num_customers": self.num_customers,
                "market_size": self.market_size,
                "distance_weight": self.distance_weight,
                "step_size": self.step_size,
                "price_step": self.price_step,
                "min_price": self.min_price,
                "customer_distribution": self.customer_distribution,
                "loyalty_strength": self.loyalty_strength,
                "loyalty_threshold": self.loyalty_threshold,
                "random_seed": self.random_seed,
            })
