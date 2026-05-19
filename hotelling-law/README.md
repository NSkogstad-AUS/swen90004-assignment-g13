# Hotelling's Law Simulation

A plain Python 3.14 implementation of Hotelling's Law on a one-dimensional market line.

This repository is an initial implementation intended for later quantitative comparison
against the original NetLogo Hotelling's Law model. It produces CSV outputs that capture
per-tick store metrics across configurable experimental conditions.

---

## Model overview

Hotelling's Law describes how competing vendors on a one-dimensional market tend to converge
toward the centre over time. This implementation models that dynamic with the following rules.

### Market

The market is a continuous line from position `0` to `market_size`. Customers are placed
at fixed positions drawn from a configurable distribution. Stores compete by adjusting their
positions each tick to attract more customers.

### Customer assignment

Each tick, every customer chooses the store with the lowest effective cost:

```
effective_cost = store.price + distance_weight * |customer.position - store.position|
```

Ties (equal effective cost) are broken deterministically by the lowest store id.

### Store movement

After customer assignment, each store performs a one-step local search: it tests moving
left by `step_size`, staying, and moving right by `step_size`, then moves to whichever
candidate position yields the highest simulated profit. Positions are clamped to
`[0, market_size]`. Store positions are updated sequentially in id order.

### Profit

```
profit = market_share * price
```

### Customer distributions

| Value       | Description                                                                  |
|-------------|------------------------------------------------------------------------------|
| `uniform`   | Positions drawn uniformly at random from `[0, market_size]`.               |
| `clustered` | Positions drawn from Gaussian distributions centred at three evenly spaced  |
|             | points (`sigma = market_size / 12`). Each customer is assigned to a cluster |
|             | at random, then placed using `random.gauss`.                                 |

### Loyalty extension

When `loyalty_strength > 0.0`, a returning customer's previous store receives a cost
discount before comparison:

```
adjusted_cost = effective_cost * (1 - loyalty_strength)
```

- At `loyalty_strength = 0.0` the discount is zero and behaviour is identical to the
  baseline.
- At `loyalty_strength = 1.0` the previous store's adjusted cost is always 0, so the
  customer never switches.
- The discount applies only from the second tick onward (customers have no previous store
  on the first tick).

Loyalty is not applied during the store position lookahead; stores optimise based on
raw effective costs only.

---

## Parameters

| Parameter               | Default   | Description                                         |
|-------------------------|-----------|-----------------------------------------------------|
| `market_size`           | `100`     | Length of the market line.                          |
| `num_customers`         | `100`     | Number of customers.                                |
| `num_stores`            | `2`       | Number of competing stores.                         |
| `ticks`                 | `50`      | Number of simulation steps.                         |
| `price`                 | `1.0`     | Fixed price charged by all stores.                  |
| `distance_weight`       | `1.0`     | Weight applied to travel distance in effective cost.|
| `step_size`             | `1.0`     | Maximum distance a store can move per tick.         |
| `random_seed`           | `None`    | RNG seed for reproducibility (`None` = random).     |
| `customer_distribution` | `uniform` | Customer placement distribution.                    |
| `loyalty_strength`      | `0.0`     | Previous-store discount factor (0.0–1.0).           |

---

## Requirements

- Python 3.14 or later.
- No external dependencies — standard library only.

---

## Running experiments

All commands should be run from the `hotelling-law/` project root.

### Baseline — two-store model, 10 runs

```bash
python run.py baseline
```

Output: `outputs/baseline.csv`

### Parameter sweep — vary `num_stores` and `distance_weight`

```bash
python run.py sweep
```

Output: `outputs/parameter_sweep.csv`

Sweeps `num_stores` over `[2, 3, 4]` and `distance_weight` over `[0.5, 1.0, 2.0]`
(9 conditions × 5 runs each).

### Loyalty extension — compare loyalty strengths

```bash
python run.py loyalty
```

Output: `outputs/extension_loyalty.csv`

Compares `loyalty_strength` values `0.0`, `0.25`, `0.5`, and `0.75` (5 runs each).

### Run all experiments

```bash
python run.py all
```

Experiment scripts can also be run directly:

```bash
python experiments/baseline.py
python experiments/parameter_sweep.py
python experiments/extension_loyalty.py
```

---

## Running tests

From the project root:

```bash
python -m unittest discover tests
```

Or run a single file:

```bash
python tests/test_basic_model.py
python tests/test_csv_output.py
```

---

## CSV output format

All output files are written to `outputs/`. Each file contains one row per store per tick
per run.

| Column                             | Type    | Description                                          |
|------------------------------------|---------|------------------------------------------------------|
| `experiment_name`                  | string  | Label identifying the experiment.                    |
| `run_id`                           | int     | Replicate index (0-based).                           |
| `tick`                             | int     | Simulation step (0-based).                           |
| `store_id`                         | int     | Store index (0-based).                               |
| `store_position`                   | float   | Store position after movement this tick.             |
| `store_price`                      | float   | Store's fixed price.                                 |
| `store_profit`                     | float   | Profit earned this tick (market_share × price).      |
| `store_market_share`               | int     | Number of customers served this tick.                |
| `distance_from_centre`             | float   | Distance of the store from the market midpoint.      |
| `average_distance_to_other_stores` | float   | Mean distance to all other stores.                   |
| `parameters_summary`               | string  | Pipe-separated `key=value` pairs of model parameters.|

Note: `store_position` reflects the position the store moved to at the end of the tick;
`store_profit` reflects earnings computed at the start of that same tick before movement.

---

## Model assumptions

- Customer positions are fixed throughout the simulation.
- All stores share the same fixed price.
- Stores optimise position independently with no coordination or communication.
- The position lookahead uses a single step and does not account for other stores moving.
- Loyalty applies only to customers who have been assigned at least once (from tick 1).
- The simulation is fully deterministic when `random_seed` is set.

---

## NetLogo comparison notes

This implementation is intended as a Python baseline for comparison against the NetLogo
Hotelling's Law model. When comparing outputs, note:

- NetLogo uses a discrete patch grid; this implementation uses a continuous line.
- NetLogo's random number generator will differ from Python's `random` module.
- Movement rules, tie-breaking, and update ordering may differ between implementations.

For valid comparison, focus on aggregate statistics such as final store positions,
convergence speed, and market share distribution rather than exact per-tick values.
