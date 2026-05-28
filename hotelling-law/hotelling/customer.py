"""Customer entity for the Hotelling's Law simulation."""

from typing import Optional


class Customer:
    """
    A customer at a fixed patch position.

    Customers do not move.  Each tick they choose a store based on effective cost.
    Their previous choice is remembered to support the loyalty extension.
    """

    def __init__(
        self,
        id: int,
        position: float,
        previous_store_id: Optional[int] = None,
        x_position: float = 0.0,
    ):
        """
        Initialise a customer.

        Args:
            id: Unique non-negative integer identifier.
            position: Fixed y-coordinate on the market line or plane.
            previous_store_id: The id of the store chosen in the previous tick.
                               None on the first tick (no prior choice exists).
            x_position: Fixed x-coordinate.  Always 0.0 for line layout.
        """
        self.id: int = id
        self.x_position: float = x_position
        self.position: float = position
        # Tracks which store this customer used last tick; updated after each assignment.
        self.previous_store_id: Optional[int] = previous_store_id
