"""Store entity for the Hotelling's Law simulation."""


class Store:
    """
    A store competing for customers on the one-dimensional market line.

    Each tick a store earns profit based on how many customers choose it, then
    considers moving left or right to improve its position for the next tick.
    """

    def __init__(self, id: int, position: float, price: float):
        """
        Initialise a store with a fixed id, starting position, and price.

        Args:
            id: Unique non-negative integer identifier.  Used for tie-breaking.
            position: Initial location on the market line.
            price: Starting price charged to customers; changes during a run.
        """
        # Identity and fixed attributes.
        self.id: int = id
        self.position: float = position
        self.price: float = price

        # Per-tick metrics; reset at the start of each tick by reset_metrics().
        self.market_share: int = 0           # Number of customers assigned this tick.
        self.assigned_customer_count: int = 0  # Alias for market_share; kept for output clarity.
        self.profit: float = 0.0             # Earnings this tick: market_share * price.

    def reset_metrics(self) -> None:
        """
        Reset all per-tick metrics to zero.

        Must be called at the start of every tick before customers are re-assigned.
        """
        self.market_share = 0
        self.assigned_customer_count = 0
        self.profit = 0.0
