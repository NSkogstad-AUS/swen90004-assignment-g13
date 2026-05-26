# Hotelling's Law Simulation

Python replication of the NetLogo Hotelling's Law model for SWEN90004 Assignment 2.

The model places stores and customers on a market line. Customers choose the store
with the lowest `price + distance`; stores update their position and price to improve
revenue.

## Requirements

- Python 3.12 or later
- No runtime dependencies outside the standard library

## Quick Start

Run commands from `hotelling-law/`:

```bash
cd hotelling-law
python3 run.py all
python3 run.py test
```

## Commands

```bash
python3 run.py baseline   # baseline two-store experiment
python3 run.py sweep      # NetLogo-aligned parameter sweep
python3 run.py loyalty    # customer loyalty extension
python3 run.py all        # run all experiments
python3 run.py test       # run unittest test suite
```

Generated CSVs are written to `hotelling-law/outputs/`.

## Experiments

| Command | Output files | Notes |
| --- | --- | --- |
| `baseline` | `baseline_raw.csv`, `baseline_summary.csv` | 2 stores, 101 customers, 30 runs |
| `sweep` | `replication_sweep_raw.csv`, `replication_sweep_summary.csv` | Sweeps `num_stores`, `layout`, and `rules` |
| `loyalty` | `extension_loyalty_raw.csv`, `extension_loyalty_summary.csv` | Sweeps `loyalty_strength` |

The sweep covers:

- `num_stores`: `2`, `4`, `6`
- `layout`: `plane`, `line`
- `rules`: `normal`, `moving-only`, `pricing-only`

`layout="plane"` is accepted for NetLogo compatibility, but the Python model currently
uses 1D behaviour for both layouts.

## Model Defaults

- Market positions: integer patches from `-50` to `50`
- Customers: `101`, one per patch by default
- Stores: `2`
- Initial price: `10.0`
- Price step: `1.0`
- Movement step: `1.0`
- Ticks per run: `100`

Profit is calculated as:

```text
profit = market_share * price
```

## Project Layout

```text
hotelling-law/
  run.py
  hotelling/
    model.py
    customer.py
    store.py
    experiment.py
    statistics.py
    csv_writer.py
  experiments/
    baseline.py
    replication_sweep.py
    extension_loyalty.py
    generate_all_results.py
  tests/
  docs/
  outputs/
```

## NetLogo Comparison

This is intended as a qualitative replication of the NetLogo Hotelling's Law model,
especially the 1D line case. Exact tick-by-tick equality is not expected because Python
and NetLogo use different random number generators.

Use `docs/NETLOGO_COMPARISON_TEMPLATE.md` to record side-by-side results.
