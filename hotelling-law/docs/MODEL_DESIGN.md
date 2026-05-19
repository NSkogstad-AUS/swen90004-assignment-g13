# Model Design

## Overview

This document describes the design of the Python implementation of Hotelling's Law
and explains how it maps conceptually to the original NetLogo model.

---

## Baseline Model

Hotelling's Law (1929) describes how competing sellers on a one-dimensional market tend to
cluster toward the centre over time.  This is sometimes called the **principle of minimum
differentiation**.

The Python model implements a simplified, one-dimensional version:

- A market line spans from position `0` to `market_size`.
- Customers are distributed along this line with fixed positions.
- Stores compete by adjusting their positions each simulation tick.
- Customers choose the store that minimises their effective cost.

---

## Agents and Entities

### Customer

| Attribute           | Type          | Description                                        |
|---------------------|---------------|----------------------------------------------------|
| `id`                | `int`         | Unique identifier.                                 |
| `position`          | `float`       | Fixed location on the market line.                 |
| `previous_store_id` | `int` / None  | Store chosen last tick; used by loyalty extension. |

Customers do not move.  They select a store every tick based on effective cost.

### Store

| Attribute                | Type    | Description                                            |
|--------------------------|---------|--------------------------------------------------------|
| `id`                     | `int`   | Unique identifier; used for deterministic tie-breaking.|
| `position`               | `float` | Current location on the market line.                   |
| `price`                  | `float` | Fixed price charged to all customers.                  |
| `market_share`           | `int`   | Number of customers assigned this tick.                |
| `assigned_customer_count`| `int`   | Alias for `market_share`; recorded separately in CSV.  |
| `profit`                 | `float` | Earnings this tick: `market_share × price`.            |

---

## Parameters

| Parameter               | Default   | Description                                              |
|-------------------------|-----------|----------------------------------------------------------|
| `market_size`           | 100       | Length of the market line.                               |
| `num_customers`         | 100       | Number of customers.                                     |
| `num_stores`            | 2         | Number of competing stores.                              |
| `ticks`                 | 100       | Number of simulation steps.                              |
| `price`                 | 10.0      | Fixed price for all stores.                              |
| `distance_weight`       | 1.0       | Multiplier on travel distance in effective cost.         |
| `step_size`             | 1.0       | Maximum movement per store per tick.                     |
| `random_seed`           | None      | Seed for reproducibility.                                |
| `customer_distribution` | uniform   | Placement distribution: `uniform` or `clustered`.        |
| `loyalty_strength`      | 0.0       | Retention factor for loyalty extension (0.0–1.0).        |
| `loyalty_threshold`     | 10.0      | Absolute cost margin for loyalty check.                  |

---

## Update Rules

### Tick sequence

Each tick executes in this order:

1. **Reset store metrics** — `market_share`, `assigned_customer_count`, and `profit` are
   zeroed before any new assignments.
2. **Assign customers** — each customer computes effective costs for all stores and selects
   the cheapest option (ties broken by lowest store id).  The customer's `previous_store_id`
   is updated.
3. **Calculate profits** — `profit = market_share × price` for each store.
4. **Record output** — all per-store metrics are written to output rows.  Positions recorded
   here are where the store was when it earned its profit (before any movement this tick).
5. **Update positions** — each store performs a single-step local search and moves to the
   candidate position (left, stay, right) that gives the highest simulated profit.

### Effective cost formula

```
effective_cost = store.price + distance_weight × |customer.position − store.position|
```

### Customer choice rule

Choose the store with the minimum effective cost.  If two or more stores tie, choose the
one with the lowest `store.id`.  This is deterministic and seed-independent.

### Store movement

Each store tests three candidate positions:

- `position − step_size`  (clamped to `0`)
- `position`              (stay)
- `position + step_size`  (clamped to `market_size`)

For each candidate, the store simulates how many customers it would attract (using current
positions of all other stores), then moves to the candidate with the highest simulated
profit.  Ties prefer the current position, then the numerically smallest position.

Stores update sequentially in id order, so a store with id 0 moves before id 1 sees any
change.  This is a sequential (not simultaneous) update.

### Profit formula

```
profit = market_share × price
```

---

## Assumptions

1. Customer positions are fixed throughout a run; they do not move.
2. All stores share the same fixed price (prices do not change).
3. The position lookahead evaluates only a single step; multi-step lookahead is not used.
4. During lookahead, loyalty effects are not applied; stores optimise on raw effective costs.
5. Store positions update sequentially (lower ids first), not simultaneously.
6. Loyalty effects apply only from the second tick onward (no `previous_store_id` on tick 0).
7. The `random_seed` controls both customer placement and all stochastic behaviour; with a
   fixed seed, the simulation is fully deterministic.

---

## Customer Distributions

### Uniform

Customer positions are drawn independently from a uniform distribution over
`[0, market_size]`.  This matches the default NetLogo distribution.

### Clustered

Three cluster centres are placed at `market_size × k/(num_clusters+1)` for k = 1, 2, 3
(i.e. 25%, 50%, 75% of the market).  Each customer is assigned to a random cluster and
positioned using a Gaussian draw with sigma = `market_size / 12`, clamped to bounds.

---

## Mapping to the NetLogo Model

| Concept                  | NetLogo                              | Python implementation              |
|--------------------------|--------------------------------------|------------------------------------|
| Market space             | Patch grid (1D strip)                | Continuous float line [0, 100]     |
| Customer placement       | Random patch selection               | `random.uniform` or Gaussian       |
| Customer choice          | Minimum travel + price               | Same formula, lowest-id tie-break  |
| Store movement           | Move toward higher profit            | Single-step local search (±step)   |
| Profit                   | Customers served × price             | Same formula                       |
| Randomness               | NetLogo PRNG                         | Python `random.Random`             |
| Update order             | Simultaneous (ask turtles)           | Sequential by store id             |

**Note on numerical comparison:** Because the two implementations use different random
number generators and potentially different update ordering, exact tick-by-tick numerical
agreement is not expected.  Comparison should focus on aggregate and final-state statistics
such as mean final store position, average inter-store distance, and convergence speed.
