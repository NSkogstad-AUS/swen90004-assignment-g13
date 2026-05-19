"""Customer entity for the Hotelling's Law simulation."""

from typing import Optional


class Customer:
    """A customer at a fixed position on the market line."""

    def __init__(self, id: int, position: float, previous_store_id: Optional[int] = None):
        """
        Initialise a customer.

        Args:
            id: Unique customer identifier.
            position: Fixed location on the market line.
            previous_store_id: Store chosen in the previous tick, or None on first tick.
        """
        self.id = id
        self.position = position
        self.previous_store_id = previous_store_id
