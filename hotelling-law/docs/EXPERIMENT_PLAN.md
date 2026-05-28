# Experiment Plan

## Overview

This document describes the experimental design for the SWEN90004 Assignment 2 replication
and extension experiments.  All experiments use the Python Hotelling's Law model and output
CSV files to `outputs/`.

---

## Why Multiple Runs Are Required

Stochastic simulations produce different outcomes when customer positions are drawn from a
random distribution.  A single run may not represent the typical behaviour of the model.
Running the same parameter configuration 30 times and computing summary statistics
(mean, standard deviation, min, max) gives a reliable estimate of the model's expected
behaviour and its variability.

30 runs is a common choice in agent-based modelling literature; it provides enough
replicates for simple descriptive statistics without prohibitive compute time.

---

## Experiment 1 — Baseline

**File:** `experiments/baseline.py`

**Purpose:**
Establish a reference behaviour for the NetLogo line configuration.  This is the primary
basis for comparison against the NetLogo model.

**Configuration:**

| Parameter               | Value    |
|-------------------------|----------|
| `num_stores`            | 3        |
| `num_customers`         | 41       |
| `market_size`           | 40       |
| `ticks`                 | 100      |
| `price`                 | 10.0     |
| `step_size`             | 1.0      |
| `layout`                | line     |
| `rules`                 | normal   |
| `num_runs`              | 30       |

**Expected behaviour:**
Stores should converge toward the centre of the market (position 0) over time,
consistent with Hotelling's principle of minimum differentiation.

**Outputs:**
- `outputs/baseline_raw.csv` — one row per store per tick per run
- `outputs/baseline_raw_2.csv` — one final-tick row per store per run
- `outputs/baseline_summary.csv` — final-tick statistics across 30 runs
- `outputs/baseline_summary_netlogo.csv` — NetLogo BehaviorSpace-style table

---

## Experiment 2 — Replication Parameter Sweep

**File:** `experiments/replication_sweep.py`

**Purpose:**
Test model sensitivity to key parameter changes.  Supports behavioural comparison against
the NetLogo model across a range of conditions.

**Swept parameters:**

| Parameter               | Values                      |
|-------------------------|-----------------------------|
| `num_stores`            | 2, 4, 6                     |
| `distance_weight`       | 0.5, 1.0, 2.0               |
| `customer_distribution` | uniform, clustered           |

All other parameters are held at baseline values.  Total combinations: 3 × 3 × 2 = 18.

**Runs per scenario:** 30

**Behavioural measures collected:**
- Final store positions (mean across stores and runs)
- Average distance between stores at final tick
- Average distance from centre at final tick
- Average profit per store
- Market share distribution

**Expected effects of parameter changes:**
- More stores should increase competition and reduce individual profit.
- Higher `distance_weight` makes travel more costly, potentially reducing willingness to
  switch stores and affecting equilibrium positions.
- Clustered distribution creates uneven market pressure; stores may not converge to centre.

**Outputs:**
- `outputs/replication_sweep_raw.csv` — all 18 scenarios × 30 runs
- `outputs/replication_sweep_summary.csv` — final-tick summary per scenario

---

## Experiment 3 — Loyalty Extension

**File:** `experiments/extension_loyalty.py`

**Research question:**
"How does customer loyalty affect store clustering, market share, and profit in a
Hotelling's Law market?"

**Swept parameter:**

| `loyalty_strength` | Description                         |
|--------------------|-------------------------------------|
| 0.0                | Baseline (no loyalty)               |
| 0.25               | Weak loyalty                        |
| 0.5                | Moderate loyalty                    |
| 0.75               | Strong loyalty                      |

All other parameters held at baseline values.  `loyalty_threshold = 10.0`.

**Loyalty rule:**
A customer stays with their previous store if:
```
prev_store_cost <= best_store_cost + loyalty_strength × loyalty_threshold
```

**Runs per scenario:** 30

**Expected effects:**
- Higher loyalty should reduce store clustering (stores need not compete as aggressively).
- Market shares may become more stable and less responsive to position changes.
- Profit may become more stable under high loyalty, but individual stores may earn less if
  they lose the incentive to optimise position.

**Outputs:**
- `outputs/extension_loyalty_raw.csv`
- `outputs/extension_loyalty_summary.csv`

---

## Statistical Summaries

All summary CSVs are computed from **final-tick values** (tick = ticks − 1).

For each run, metrics are averaged across stores at the final tick, giving one value per
run.  Cross-run statistics (mean, standard deviation, min, max) are then computed from
these per-run values.

**Summary metrics:**
- `store_position` — final store position (mean across stores)
- `store_profit` — final profit (mean across stores)
- `store_market_share` — final market share (mean across stores)
- `distance_from_centre` — final distance from market midpoint
- `average_distance_to_other_stores` — final mean pairwise distance between stores

---

## Comparing Python Results with NetLogo

1. Run the NetLogo model with matching parameter settings.
2. Record final-tick output for the same metrics listed above.
3. Fill in the `docs/NETLOGO_COMPARISON_TEMPLATE.md` table with NetLogo and Python means.
4. Assess whether the Python model replicates the NetLogo model's qualitative behaviour
   (e.g., do stores converge to the centre? Does more competition reduce profit?).
5. Quantitative agreement is not expected due to different RNGs and update order; focus on
   directional agreement (e.g., higher distance_weight → more spread vs. more clustering).
