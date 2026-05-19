"""Store entity for the Hotelling's Law simulation."""


class Store:
    """A store competing for customers on the market line."""

    def __init__(self, id: int, position: float, price: float):
        """
        Initialise a store.

        Args:
            id: Unique store identifier.
            position: Initial location on the market line.
            price: Fixed price charged to customers.
        """
        self.id = id
        self.position = position
        self.price = price
        self.profit: float = 0.0
        self.market_share: int = 0

    def reset_metrics(self) -> None:
        """Reset profit and market_share to zero before each tick."""
        self.profit = 0.0
        self.market_share = 0
