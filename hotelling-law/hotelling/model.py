"""Core simulation model for Hotelling's Law."""

import random
from math import hypot
from typing import Dict, List, Optional, Tuple

from hotelling.customer import Customer
from hotelling.store import Store


class HotellingModel:
    """
    Simulates Hotelling's Law on a one-dimensional line or two-dimensional plane.

    Replicates the behaviour of the NetLogo Hotelling's Law model (Ottino, Stonedahl &
    Wilensky, 2009) using the 'line' and 'plane' layouts.  Each tick, stores
    independently optimise their position and price (down/stay/up) to maximise
    revenue.  Customers choose the store with the lowest sum of price and distance.

    Assumptions:
    - Customer positions are integer-valued patch coordinates.
    - Customer positions are fixed throughout a run.
    - Position and price updates are simultaneous: all stores compute their new
      position/price before any store moves, matching the NetLogo task-based approach.
    - Tie-breaking in customer assignment is random, matching NetLogo's min-one-of.
    - The position and price lookaheads are both computed before either change is
      applied, matching NetLogo's task-based go procedure.
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
        num_customers: int = 101,
        num_stores: int = 2,
        ticks: int = 100,
        price: float = 10.0,
        price_step: float = 1.0,
        distance_weight: float = 1.0,
        step_size: float = 1.0,
        random_seed: Optional[int] = None,
        customer_distribution: str = "uniform",
        layout: str = "line",
        rules: str = "normal",
        loyalty_strength: float = 0.0,
        loyalty_threshold: float = 10.0,
    ):
        """
        Initialise the model with the given parameters.

        Args:
            market_size: Length of the market line; default integer positions span [-50, 50].
            num_customers: Number of customers placed on the market line.
            num_stores: Number of competing stores.
            ticks: Number of simulation steps to execute.
            price: Initial price for every store.  Prices evolve dynamically each tick.
            price_step: Amount by which a store can raise or lower its price each tick.
                        Matches the NetLogo model's ±1 price unit per tick.
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
        self.market_min: int = -int(market_size / 2)
        self.market_max: int = int(market_size / 2)
        self.num_customers: int = num_customers
        self.num_stores: int = num_stores
        self.ticks: int = ticks
        self.price: float = price             # initial price; stores diverge over time
        self.price_step: float = price_step
        self.distance_weight: float = distance_weight
        self.step_size: float = step_size
        if layout not in ("line", "plane"):
            raise ValueError(f"Unknown layout: '{layout}'")
        # Model layout: 'line' uses pxcor=0 and varies pycor; 'plane' uses all patches.
        self.layout: str = layout
        # Rules control whether stores may move and/or change prices:
        # 'normal' -> both; 'moving-only' -> only move; 'pricing-only' -> only price.
        self.rules: str = rules
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

        Positions are integer-valued, matching NetLogo's discrete
        patches.  Raises ValueError for unknown distribution names.
        """
        if self.customer_distribution == "uniform":
            consumer_patches = self._consumer_patches()
            if self.num_customers == len(consumer_patches):
                return [
                    self._customer_from_patch(i, patch)
                    for i, patch in enumerate(consumer_patches)
                ]
            return [
                self._customer_from_patch(i, self._rng.choice(consumer_patches))
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
        the market bounds.  Integer positions match NetLogo's patch model.
        """
        num_clusters = 3
        sigma = self.market_size / 12.0
        centres = [
            self.market_min + self.market_size * (k + 1) / (num_clusters + 1)
            for k in range(num_clusters)
        ]
        customers = []
        for i in range(self.num_customers):
            y_centre = self._rng.choice(centres)
            y_pos = round(self._rng.gauss(y_centre, sigma))
            y_pos = max(self.market_min, min(self.market_max, y_pos))
            if self.layout == "plane":
                x_centre = self._rng.choice(centres)
                x_pos = round(self._rng.gauss(x_centre, sigma))
                x_pos = max(self.market_min, min(self.market_max, x_pos))
            else:
                x_pos = 0
            customers.append(Customer(id=i, position=y_pos, x_position=x_pos))
        return customers

    def _create_stores(self) -> List[Store]:
        """
        Return stores at random integer positions, matching the NetLogo setup procedure.

        Each store is placed on a randomly chosen consumer patch (integer position in
        the market bounds).  Multiple stores may share an initial position.  All stores
        start with the same initial price; prices diverge dynamically each tick.
        """
        if self.layout == "plane":
            return [
                self._store_from_patch(i, self._rng.choice(self._consumer_patches()))
                for i in range(self.num_stores)
            ]

        return [
            Store(
                id=i,
                position=self._rng.randint(self.market_min, self.market_max),
                price=self.price,
            )
            for i in range(self.num_stores)
        ]

    def _patch_positions(self) -> List[int]:
        """Return all integer patch coordinates in the market."""
        return list(range(self.market_min, self.market_max + 1))

    def _consumer_patches(self) -> List[Tuple[int, int]]:
        """Return NetLogo-equivalent consumer patch coordinates for the layout."""
        if self.layout == "line":
            return [(0, y) for y in self._patch_positions()]
        return [
            (x, y)
            for x in self._patch_positions()
            for y in self._patch_positions()
        ]

    def _customer_from_patch(self, id: int, patch: Tuple[int, int]) -> Customer:
        x, y = patch
        return Customer(id=id, position=y, x_position=x)

    def _store_from_patch(self, id: int, patch: Tuple[int, int]) -> Store:
        x, y = patch
        return Store(id=id, position=y, x_position=x, price=self.price)

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
        5. Compute location and price changes from the same pre-update state.
        6. Apply all location changes and then all price changes.
        """
        for store in self.stores:
            store.reset_metrics()
        self._assign_customers()
        self._calculate_profits()
        self._record_output(tick)
        new_positions = self._planned_positions()
        new_prices = self._planned_prices()
        for store, pos in zip(self.stores, new_positions):
            self._set_store_coords(store, pos)
        for store, price in zip(self.stores, new_prices):
            store.price = price

    # ------------------------------------------------------------------
    # Customer assignment

    def _customer_coords(self, customer: Customer) -> Tuple[float, float]:
        return (customer.x_position, customer.position)

    def _store_coords(self, store: Store) -> Tuple[float, float]:
        return (store.x_position, store.position)

    def _set_store_coords(self, store: Store, coords: Tuple[float, float]) -> None:
        store.x_position, store.position = coords

    def _distance_between(
        self,
        first: Tuple[float, float],
        second: Tuple[float, float],
    ) -> float:
        return hypot(first[0] - second[0], first[1] - second[1])
    # ------------------------------------------------------------------

    def _effective_cost(self, customer: Customer, store: Store) -> float:
        """
        Return the effective cost for a customer visiting a store.

        Formula: store.price + distance_weight * distance(customer, store)
        With distance_weight = 1.0 (default) this matches the NetLogo formula:
        effective_cost = price + distance.
        """
        return (
            store.price
            + self.distance_weight
            * self._distance_between(self._customer_coords(customer), self._store_coords(store))
        )

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
        store with the lowest effective cost.  Ties are broken randomly, matching
        NetLogo's min-one-of behaviour.

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

    def _planned_positions(self) -> List[Tuple[float, float]]:
        """
        Return each store's planned next position.

        Matches NetLogo's task-based simultaneous update: every store computes its new
        position using the pre-update state of all stores and prices. The caller later
        applies all computed moves at once.
        """
        # If the rules prohibit moving, skip position updates.
        if self.rules == "pricing-only":
            return [self._store_coords(store) for store in self.stores]
        return [self._best_position(store) for store in self.stores]

    def _best_position(self, store: Store) -> Tuple[float, float]:
        """
        Return the coordinates with the highest simulated revenue, price held fixed.

        Matches the NetLogo new-location-task logic:
        - If the store had customers this tick (market_share > 0), the current position
          is included and preferred on ties (NetLogo: fput patch-here possible-moves).
        - If the store had zero customers, the current position is excluded; the store
          must move (NetLogo: "only consider status quo if area-count > 0").  Direction
          is chosen randomly on ties.
        Candidates are clamped to the market bounds.
        """
        stay = self._store_coords(store)
        neighbours = self._neighbour_positions(stay)
        self._rng.shuffle(neighbours)

        if store.market_share > 0:
            # Status quo included; it wins ties (placed first, stable sort equivalent).
            candidates = [stay] + neighbours
        else:
            # Must move; shuffled neighbours avoid favouring one direction on ties.
            candidates = neighbours if neighbours else [stay]

        best_pos = stay
        best_rev = float("-inf")
        for pos in candidates:
            rev = self._simulated_revenue(store, pos, store.price)
            if rev > best_rev:
                best_rev = rev
                best_pos = pos
        return best_pos

    def _neighbour_positions(self, coords: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Return legal NetLogo neighbors4 candidate patches for the current layout."""
        x, y = coords
        step = self.step_size
        if self.layout == "line":
            raw = [(0, y - step), (0, y + step)]
        else:
            raw = [
                (x - step, y),
                (x + step, y),
                (x, y - step),
                (x, y + step),
            ]

        neighbours: List[Tuple[float, float]] = []
        for raw_x, raw_y in raw:
            candidate = (
                max(self.market_min, min(self.market_max, round(raw_x))),
                max(self.market_min, min(self.market_max, round(raw_y))),
            )
            if candidate != coords and candidate not in neighbours:
                neighbours.append(candidate)
        return neighbours

    # ------------------------------------------------------------------
    # Store price optimisation
    # ------------------------------------------------------------------

    def _planned_prices(self) -> List[float]:
        """
        Return each store's planned next price.

        Matches NetLogo's task-based simultaneous update: every store computes its new
        price using the same pre-update state used for location planning. The caller
        later applies all computed price changes at once.
        """
        # If the rules prohibit pricing changes, skip price updates.
        if self.rules == "moving-only":
            return [store.price for store in self.stores]
        return [self._best_price(store) for store in self.stores]

    def _best_price(self, store: Store) -> float:
        """
        Return the price (down, stay, or up by price_step) with the highest simulated
        revenue, holding the store's current position fixed.

        Matches the NetLogo new-price-task logic:
        - Candidate order is lower, current, higher price, so equal simulated
          revenues keep the first candidate in that order.
        - Emergency procedure: if all candidate prices yield zero revenue and the
          current price lowers by price_step.  This prevents stores from being
          permanently stuck with zero market share.
        """
        candidates = [
            store.price - self.price_step,
            store.price,
            store.price + self.price_step,
        ]
        revenues = [
            self._simulated_revenue(store, self._store_coords(store), p) for p in candidates
        ]

        # Emergency: all revenues zero, so drop price to attract customers.
        if all(r == 0.0 for r in revenues):
            return store.price - self.price_step

        best_price = candidates[0]
        best_rev = float("-inf")
        for price, rev in zip(candidates, revenues):
            if rev > best_rev:
                best_rev = rev
                best_price = price
        return best_price

    # ------------------------------------------------------------------
    # Shared simulation helper
    # ------------------------------------------------------------------

    def _simulated_revenue(
        self,
        moving_store: Store,
        candidate_pos: Tuple[float, float],
        candidate_price: float,
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
                + self.distance_weight
                * self._distance_between(self._customer_coords(customer), candidate_pos)
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
        centre = 0.0
        num_stores = len(self.stores)

        for store in self.stores:
            distance_from_centre = self._distance_between(self._store_coords(store), (centre, centre))

            if num_stores > 1:
                avg_distance_to_others = sum(
                    self._distance_between(self._store_coords(store), self._store_coords(other))
                    for other in self.stores
                    if other.id != store.id
                ) / (num_stores - 1)
            else:
                avg_distance_to_others = 0.0

            self.output_rows.append({
                "tick": tick,
                "store_id": store.id,
                "store_x_position": store.x_position,
                "store_y_position": store.position,
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
                "customer_distribution": self.customer_distribution,
                "layout": self.layout,
                "rules": self.rules,
                "loyalty_strength": self.loyalty_strength,
                "loyalty_threshold": self.loyalty_threshold,
                "random_seed": self.random_seed,
            })
