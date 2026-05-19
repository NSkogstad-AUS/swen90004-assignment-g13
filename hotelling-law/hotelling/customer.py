"""Customer entity for the Hotelling's Law simulation."""

from typing import Optional


class Customer:
    """
    A customer at a fixed position on the market line.

    Customers do not move.  Each tick they choose a store based on effective cost.
    Their previous choice is remembered to support the loyalty extension.
    """

    def __init__(self, id: int, position: float, previous_store_id: Optional[int] = None):
        """
        Initialise a customer.

        Args:
            id: Unique non-negative integer identifier.
            position: Fixed location on the market line [0, market_size].
            previous_store_id: The id of the store chosen in the previous tick.
                               None on the first tick (no prior choice exists).
        """
        self.id: int = id
        self.position: float = position
        # Tracks which store this customer used last tick; updated after each assignment.
        self.previous_store_id: Optional[int] = previous_store_id
