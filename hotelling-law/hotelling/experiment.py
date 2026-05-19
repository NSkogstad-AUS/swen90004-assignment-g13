"""Experiment runner that executes multiple model replications."""

from typing import Any, Dict, List, Optional

from hotelling.model import HotellingModel


class Experiment:
    """
    Runs multiple independent replications of a HotellingModel and collects output rows.

    Each replication uses a deterministic seed derived from base_seed + run_id so that
    results are reproducible while each run still has different customer/store positions.
    """

    def __init__(
        self,
        experiment_name: str,
        num_runs: int = 5,
        base_seed: Optional[int] = 42,
        **model_params: Any,
    ):
        """
        Initialise the experiment.

        Args:
            experiment_name: Label written into every output row.
            num_runs: Number of independent replications to run.
            base_seed: Starting seed; each run uses base_seed + run_id.
                       Pass None for non-deterministic seeds.
            **model_params: Keyword arguments forwarded to HotellingModel.
                            Do not include random_seed; the experiment manages seeds.
        """
        self.experiment_name = experiment_name
        self.num_runs = num_runs
        self.base_seed = base_seed
        self.model_params = model_params

    def run(self) -> List[Dict]:
        """
        Execute all replications and return combined output rows with experiment metadata.

        Adds 'experiment_name', 'run_id', and 'parameters_summary' to each row.
        """
        all_rows: List[Dict] = []
        params_summary = self._params_summary()

        for run_id in range(self.num_runs):
            seed = (self.base_seed + run_id) if self.base_seed is not None else None
            model = HotellingModel(random_seed=seed, **self.model_params)
            rows = model.run()

            for row in rows:
                row["experiment_name"] = self.experiment_name
                row["run_id"] = run_id
                row["parameters_summary"] = params_summary

            all_rows.extend(rows)

        return all_rows

    def _params_summary(self) -> str:
        """Return a compact key=value string of all model parameters, sorted by key."""
        return "|".join(f"{k}={v}" for k, v in sorted(self.model_params.items()))
