# Hotelling's Law Simulation — SWEN90004 Assignment 2

A Python 3.14 replication of the NetLogo Hotelling's Law model, implemented using only the
Python standard library.  Produces CSV outputs for quantitative comparison against the
original NetLogo model.

---

## Assignment Context

This project is submitted for SWEN90004: Modelling Complex Software Systems, Assignment 2.

The assignment requires:
1. Replicating an existing NetLogo agent-based model in Python.
2. Running experiments to compare the Python replication against the original NetLogo model.
3. Implementing and evaluating a novel model extension.

The NetLogo Hotelling's Law model is the reference.

---

## What Is Hotelling's Law?

Hotelling's Law (1929) describes how competing vendors on a one-dimensional market tend to
cluster toward the centre over time.  This is called the **principle of minimum
differentiation**: rather than spreading out to cover the market, rational competitors move
toward the middle to maximise their customer base at the expense of competitors.

This simulation places stores and customers on a line.  Customers choose the cheapest
store (price + travel cost).  Stores move each tick to attract more customers.

---

## Requirements

- Python 3.14 or later
- No external packages required (standard library only)

---

## Repository Structure

```
hotelling-law/
├── run.py                          Main CLI entry point
├── hotelling/
│   ├── customer.py                 Customer agent
│   ├── store.py                    Store agent
│   ├── model.py                    Simulation model
│   ├── experiment.py               Multi-run experiment runner
│   ├── statistics.py               Summary statistics helpers
│   └── csv_writer.py               CSV output utilities
├── experiments/
│   ├── baseline.py                 Baseline experiment
│   ├── replication_sweep.py        Parameter sweep for replication
│   ├── extension_loyalty.py        Loyalty extension experiment
│   └── generate_all_results.py     Run all experiments
├── outputs/                        Generated CSV files (not committed)
├── tests/
│   ├── test_customer_assignment.py
│   ├── test_store_metrics.py
│   ├── test_model_execution.py
│   ├── test_csv_output.py
│   └── test_loyalty_extension.py
└── docs/
    ├── MODEL_DESIGN.md             Model description and design decisions
    ├── EXPERIMENT_PLAN.md          Experiment designs and expected behaviour
    ├── EXTENSION_DESIGN.md         Loyalty extension rationale and design
    ├── NETLOGO_COMPARISON_TEMPLATE.md  Template for comparing Python vs NetLogo
    └── AI_USE_APPENDIX_DRAFT.md    Draft AI use statement
```

---

## Running Experiments

**All commands must be run from the `hotelling-law/` project root.**

### Run the baseline experiment

```bash
python run.py baseline
```

Runs the default two-store model for 30 replications.

Outputs:
- `outputs/baseline_raw.csv`
- `outputs/baseline_summary.csv`

### Run the parameter sweep

```bash
python run.py sweep
```

Sweeps `num_stores` (2, 4, 6), `distance_weight` (0.5, 1.0, 2.0), and
`customer_distribution` (uniform, clustered) — 18 scenarios × 30 runs.

Outputs:
- `outputs/replication_sweep_raw.csv`
- `outputs/replication_sweep_summary.csv`

### Run the loyalty extension experiment

```bash
python run.py loyalty
```

Compares `loyalty_strength` values 0.0, 0.25, 0.5, 0.75 across 30 runs each.

Outputs:
- `outputs/extension_loyalty_raw.csv`
- `outputs/extension_loyalty_summary.csv`

### Run all experiments

```bash
python run.py all
```

Runs baseline, sweep, and loyalty in sequence.  Produces all six CSV files.

### Run experiments directly

Individual experiment scripts can also be run from the project root:

```bash
python experiments/baseline.py
python experiments/replication_sweep.py
python experiments/extension_loyalty.py
```

---

## Running Tests

```bash
python run.py test
```

Or directly with unittest discovery:

```bash
python -m unittest discover tests -v
```

All tests use Python's built-in `unittest` module; no test runner installation is needed.

---

## Model Overview

### Market

A continuous line from `0` to `market_size` (default 100).

### Customers

Fixed positions drawn from a uniform or clustered distribution.  Each tick, a customer
chooses the store with the lowest effective cost.

### Effective cost formula

```
effective_cost = store.price + distance_weight × |customer.position − store.position|
```

Ties are broken by the lowest store id.

### Stores

Stores move each tick by testing three candidate positions (left, stay, right by
`step_size`) and moving to whichever yields the highest simulated profit.

### Profit formula

```
profit = market_share × price
```

### Tick order

1. Reset store metrics.
2. Assign customers.
3. Calculate profits.
4. Record output (position before movement is recorded).
5. Update store positions.

---

## Loyalty Extension

When `loyalty_strength > 0.0`, customers remember their previous store.  A customer stays
with their previous store if:

```
prev_store_cost <= best_store_cost + loyalty_strength × loyalty_threshold
```

At `loyalty_strength = 0.0`, behaviour is identical to the baseline model.

The extension tests whether customer inertia reduces store clustering and alters profit
and market share dynamics.  See `docs/EXTENSION_DESIGN.md` for the full rationale.

---

## CSV Output Files

### Raw CSV (`*_raw.csv`)

One row per store per tick per run.

| Column                             | Description                                          |
|------------------------------------|------------------------------------------------------|
| `experiment_name`                  | Experiment label.                                    |
| `run_id`                           | Replication index (0-based).                         |
| `tick`                             | Simulation step (0-based).                           |
| `store_id`                         | Store index (0-based).                               |
| `store_position`                   | Store position before movement this tick.            |
| `store_price`                      | Fixed store price.                                   |
| `store_profit`                     | Profit earned this tick (market_share × price).      |
| `store_market_share`               | Customers served this tick.                          |
| `assigned_customer_count`          | Same as market_share; included for completeness.     |
| `distance_from_centre`             | Distance from the market midpoint.                   |
| `average_distance_to_other_stores` | Mean distance to all other stores.                   |
| `num_stores`                       | Parameter: number of stores.                         |
| `num_customers`                    | Parameter: number of customers.                      |
| `market_size`                      | Parameter: market line length.                       |
| `distance_weight`                  | Parameter: travel cost multiplier.                   |
| `step_size`                        | Parameter: maximum store movement per tick.          |
| `customer_distribution`            | Parameter: customer placement distribution.          |
| `loyalty_strength`                 | Parameter: loyalty retention factor.                 |
| `loyalty_threshold`                | Parameter: loyalty cost margin.                      |
| `random_seed`                      | RNG seed for this run.                               |

### Summary CSV (`*_summary.csv`)

One row per metric per scenario, aggregated over final-tick values across all runs.

| Column               | Description                                                |
|----------------------|------------------------------------------------------------|
| `experiment_name`    | Experiment label.                                          |
| `scenario_name`      | Scenario label (encodes parameter values).                 |
| `parameter_name`     | Name of the key parameter varied in this scenario.         |
| `parameter_value`    | Value of that parameter.                                   |
| `metric_name`        | Metric being summarised.                                   |
| `mean`               | Mean across runs.                                          |
| `standard_deviation` | Standard deviation across runs.                            |
| `minimum`            | Minimum observed across runs.                              |
| `maximum`            | Maximum observed across runs.                              |
| `run_count`          | Number of runs included.                                   |

---

## Comparing Against NetLogo

1. Run the NetLogo Hotelling's Law model with matching parameter settings.
2. Record final-tick metrics for the same number of runs (30).
3. Fill in the `docs/NETLOGO_COMPARISON_TEMPLATE.md` table.
4. Compare directional behaviour (clustering, profit trends) rather than exact values.

Exact numerical agreement is not expected due to different random number generators and
store update ordering.  See `docs/MODEL_DESIGN.md` for a full mapping.

---

## No External Dependencies

This project uses only the Python standard library:

- `random` — random number generation
- `statistics` — mean and standard deviation
- `csv` — CSV file reading and writing
- `argparse` — command-line interface
- `pathlib`, `os` — file path handling
- `itertools` — parameter sweep iteration
- `unittest` — testing framework
- `subprocess` — test runner dispatch from run.py

No installation step is required.  No `requirements.txt`, `pyproject.toml`, or virtual
environment is needed.
