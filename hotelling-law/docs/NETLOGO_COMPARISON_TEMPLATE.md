# NetLogo vs Python Comparison Template

This template is for recording side-by-side comparison of the NetLogo reference model and
the Python replication.  Fill in the NetLogo columns manually after running the NetLogo
model with matching parameter settings.

Python values can be read from `outputs/baseline_summary.csv` and
`outputs/replication_sweep_summary.csv`.

**Note:** Exact numerical agreement is not expected.  The two implementations use different
random number generators and (potentially) different update ordering.  Focus on whether the
models agree qualitatively (same direction of effect, similar magnitude of convergence).

---

## Baseline Comparison (2 stores, uniform distribution, default parameters)

| Metric                              | NetLogo Mean | Python Mean | Difference | Interpretation |
|-------------------------------------|:------------:|:-----------:|:----------:|----------------|
| Mean final store position (store 0) | _fill in_    | _see CSV_   |            |                |
| Mean final store position (store 1) | _fill in_    | _see CSV_   |            |                |
| Mean distance from centre           | _fill in_    | _see CSV_   |            |                |
| Mean avg distance between stores    | _fill in_    | _see CSV_   |            |                |
| Mean final profit per store         | _fill in_    | _see CSV_   |            |                |
| Mean final market share per store   | _fill in_    | _see CSV_   |            |                |

**NetLogo parameter settings used:**
```
num-stores: 2
num-consumers: 100
market-size: 100
price: 10
distance-weight: 1.0
step-size: 1
num-runs: 30
```

---

## Parameter Sweep Comparison — num_stores

| num_stores | Metric                       | NetLogo Mean | Python Mean | Difference | Interpretation |
|:----------:|------------------------------|:------------:|:-----------:|:----------:|----------------|
| 2          | Mean final profit per store  | _fill in_    | _see CSV_   |            |                |
| 2          | Mean avg dist. between stores| _fill in_    | _see CSV_   |            |                |
| 4          | Mean final profit per store  | _fill in_    | _see CSV_   |            |                |
| 4          | Mean avg dist. between stores| _fill in_    | _see CSV_   |            |                |
| 6          | Mean final profit per store  | _fill in_    | _see CSV_   |            |                |
| 6          | Mean avg dist. between stores| _fill in_    | _see CSV_   |            |                |

---

## Parameter Sweep Comparison — distance_weight

| distance_weight | Metric                       | NetLogo Mean | Python Mean | Difference | Interpretation |
|:---------------:|------------------------------|:------------:|:-----------:|:----------:|----------------|
| 0.5             | Mean dist. from centre       | _fill in_    | _see CSV_   |            |                |
| 0.5             | Mean avg dist. between stores| _fill in_    | _see CSV_   |            |                |
| 1.0             | Mean dist. from centre       | _fill in_    | _see CSV_   |            |                |
| 1.0             | Mean avg dist. between stores| _fill in_    | _see CSV_   |            |                |
| 2.0             | Mean dist. from centre       | _fill in_    | _see CSV_   |            |                |
| 2.0             | Mean avg dist. between stores| _fill in_    | _see CSV_   |            |                |

---

## Parameter Sweep Comparison — customer_distribution

| distribution | Metric                       | NetLogo Mean | Python Mean | Difference | Interpretation |
|:------------:|------------------------------|:------------:|:-----------:|:----------:|----------------|
| uniform      | Mean dist. from centre       | _fill in_    | _see CSV_   |            |                |
| uniform      | Mean final profit per store  | _fill in_    | _see CSV_   |            |                |
| clustered    | Mean dist. from centre       | _fill in_    | _see CSV_   |            |                |
| clustered    | Mean final profit per store  | _fill in_    | _see CSV_   |            |                |

---

## Notes on Comparison Methodology

- Python mean values come from `scenario_name` rows in the summary CSVs.  Filter by
  `metric_name` to find the relevant row.
- NetLogo values should be computed as the mean across the same number of runs (30) using
  the same final-tick measurement approach.
- "Difference" = Python Mean − NetLogo Mean (positive = Python is higher).
- Interpretation should note whether the models agree on direction (e.g., both show
  clustering), even if exact magnitudes differ.
- Discrepancies in update order (sequential vs. simultaneous) may cause systematic
  differences in convergence speed; this is expected and should be noted.
