"""Experiment runner that executes multiple model replications."""

from typing import Any, Dict, List, Optional

from hotelling.model import HotellingModel


class Experiment:
    """
    Runs multiple independent replications of a HotellingModel and collects output rows.

    Each replication is given a deterministic seed derived from base_seed + run_id so
    that results are reproducible and each run still has different customer positions.

    The experiment adds 'experiment_name' and 'run_id' to every output row.
    All model parameters are embedded by the model itself in each row.
    """

    def __init__(
        self,
        experiment_name: str,
        num_runs: int = 30,
        base_seed: Optional[int] = 100,
        **model_params: Any,
    ):
        """
        Initialise the experiment.

        Args:
            experiment_name: Label written into every output row.
            num_runs: Number of independent replications to run.
            base_seed: Seed for the first replication.  Run i uses base_seed + i.
                       Pass None for non-deterministic behaviour.
            **model_params: Keyword arguments forwarded directly to HotellingModel.
                            Do not include 'random_seed'; the experiment manages seeds.
        """
        self.experiment_name: str = experiment_name
        self.num_runs: int = num_runs
        self.base_seed: Optional[int] = base_seed
        self.model_params: Dict[str, Any] = model_params

    def run(self) -> List[Dict]:
        """
        Execute all replications and return the combined list of output rows.

        Adds 'experiment_name' and 'run_id' to every row returned by HotellingModel.
        Model parameters are already embedded by HotellingModel._record_output().
        """
        all_rows: List[Dict] = []

        for run_id in range(self.num_runs):
            seed = (self.base_seed + run_id) if self.base_seed is not None else None
            model = HotellingModel(random_seed=seed, **self.model_params)
            rows = model.run()

            for row in rows:
                row["experiment_name"] = self.experiment_name
                row["run_id"] = run_id

            all_rows.extend(rows)

        return all_rows
