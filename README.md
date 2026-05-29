# Hotelling's Law Simulation

Python replication of the NetLogo Hotelling's Law model for SWEN90004 Assignment 2.

The project supports the NetLogo line and plane layouts. Stores choose price and
location changes using the same high-level structure as the original NetLogo model:
stores first plan their changes, then all selected changes are applied together for
the tick.

## Requirements

- Python 3.12 or later
- No runtime dependencies outside the Python standard library

## Quick Start

From the repo root:

```bash
python3 run_custom_experiment.py --layout line --rules normal --num-stores 3 --steps 100 --runs 30
```

Or from `hotelling-law/`:

```bash
cd hotelling-law
python3 run.py baseline
python3 run.py plane
python3 run.py test
```

Generated CSV files are written to `hotelling-law/outputs/` unless an output directory
is explicitly provided.

## Main Commands

Run these from `hotelling-law/`:

```bash
python3 run.py baseline   # NetLogo-aligned line baseline
python3 run.py plane      # NetLogo-aligned plane baseline
python3 run.py sweep      # sensitivity sweep
python3 run.py loyalty    # customer loyalty extension
python3 run.py all        # run baseline, plane, sweep, and loyalty
python3 run.py plots      # generate SVG plots from outputs/*.csv
python3 run.py test       # run unit tests
```

Run configurable one-off experiments from the repo root:

```bash
python3 run_custom_experiment.py --layout line --rules moving-only --num-stores 4 --steps 100 --runs 30
python3 run_custom_experiment.py --layout plane --rules pricing-only --num-stores 3 --steps 50 --runs 10
python3 run_custom_experiment.py --layout line --num-stores 3 --steps 100 --runs 30 --loyalty-strength 0.75 --loyalty-threshold 20 --output-prefix loyalty_example
```

The configurable runner accepts:

```text
--layout         line | plane
--rules          normal | moving-only | pricing-only
--num-stores     number of stores
--steps          ticks per run
--runs           independent replications
--market-size    default 40, matching NetLogo -20..20
--num-customers  optional override
--base-seed      first random seed
--loyalty-strength  customer loyalty weight, default 0.0
--loyalty-threshold switching margin for loyalty, default 10.0
--output-prefix  optional output file prefix
--output-dir     optional output folder
```

Use the loyalty flags when you want quick extension examples without editing `experiments/extension_loyalty.py`.

Run a loyalty sweep that writes one combined summary CSV and matching line plots:

```bash
python3 run_loyalty_examples.py --num-stores 3 --steps 100 --runs 30 --loyalty-threshold 20
```

If `--num-customers` is omitted, the script uses NetLogo-aligned defaults:

```text
line:  41 customers, one for each pycor patch from -20 to 20
plane: 1681 customers, one for each patch in the 41 x 41 grid
```

## Baseline Configurations

Use these as the primary NetLogo validation cases.

| Case | Layout | Stores | Rules | Steps | Runs | Customers |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| Baseline | `line` | 3 | `normal` | 100 | 30 | 41 |
| Plane validation | `plane` | 3 | `normal` | 100 | 30 | 1681 |

For sensitivity experiments, vary only:

```text
num_stores
rules
```

Keep these fixed for clean comparison:

```text
layout      line for main baseline/sensitivity, plane for plane validation
market_size 40
steps       100 unless intentionally testing runtime or convergence
runs        30
```

Recommended sensitivity combinations:

| Purpose | Layout | Stores | Rules |
| --- | --- | --- | --- |
| Baseline validation | `line` | 3 | `normal` |
| Store-count sensitivity | `line` | 2, 3, 4, 6 | `normal` |
| Rule sensitivity | `line` | 3 | `normal`, `moving-only`, `pricing-only` |
| Combined sensitivity | `line` | 2, 3, 4, 6 | `normal`, `moving-only`, `pricing-only` |
| Plane validation | `plane` | 3 | `normal` |

## Output Files

Standard experiment commands write:

```text
baseline_raw.csv
baseline_raw_2.csv
baseline_summary.csv
baseline_summary_netlogo.csv
plane_baseline_raw.csv
plane_baseline_raw_2.csv
plane_baseline_summary.csv
plane_baseline_summary_netlogo.csv
replication_sweep_raw.csv
replication_sweep_summary.csv
extension_loyalty_raw.csv
extension_loyalty_summary.csv
```

The configurable runner writes files using the selected prefix:

```text
<prefix>_raw.csv
<prefix>_raw_2.csv
<prefix>_summary.csv
<prefix>_summary_netlogo.csv
```

Plot generation writes SVG files to:

```text
hotelling-law/outputs/plots/
```

Output meanings:

| File type | Meaning |
| --- | --- |
| `*_raw.csv` | One row per store per tick per run |
| `*_raw_2.csv` | Final tick only, one row per store per run |
| `*_summary.csv` | Python summary statistics over final tick rows |
| `*_summary_netlogo.csv` | NetLogo BehaviorSpace-style table, one row per run |

## NetLogo BehaviorSpace Setup

Use the original NetLogo Hotelling's Law model and create BehaviorSpace experiments
that match the Python configurations.

For both line and plane validation:

```text
number-of-stores = 3
rules = "normal"
steps = 100
runs = 30
```

Set `layout = "line"` for the line baseline and `layout = "plane"` for the plane
validation.

For plane, NetLogo should report:

```text
mean [pycor] of turtles
standard-deviation [pycor] of turtles
min [pycor] of turtles
max [pycor] of turtles
mean [abs pycor] of turtles
standard-deviation [abs pycor] of turtles
min [abs pycor] of turtles
max [abs pycor] of turtles
mean [mean [distance myself] of other turtles] of turtles
standard-deviation [mean [distance myself] of other turtles] of turtles
min [mean [distance myself] of other turtles] of turtles
max [mean [distance myself] of other turtles] of turtles
mean [price * area-count] of turtles
standard-deviation [price * area-count] of turtles
min [price * area-count] of turtles
max [price * area-count] of turtles
mean [area-count] of turtles
standard-deviation [area-count] of turtles
min [area-count] of turtles
max [area-count] of turtles
mean [pxcor] of turtles
standard-deviation [pxcor] of turtles
min [pxcor] of turtles
max [pxcor] of turtles
mean [abs pxcor] of turtles
standard-deviation [abs pxcor] of turtles
min [abs pxcor] of turtles
max [abs pxcor] of turtles
mean [distancexy 0 0] of turtles
standard-deviation [distancexy 0 0] of turtles
min [distancexy 0 0] of turtles
max [distancexy 0 0] of turtles
```

For line, NetLogo should report:

```text
mean [pycor] of turtles
standard-deviation [pycor] of turtles
min [pycor] of turtles
max [pycor] of turtles
mean [abs pycor] of turtles
standard-deviation [abs pycor] of turtles
min [abs pycor] of turtles
max [abs pycor] of turtles
mean [mean [distance myself] of other turtles] of turtles
standard-deviation [mean [distance myself] of other turtles] of turtles
min [mean [distance myself] of other turtles] of turtles
max [mean [distance myself] of other turtles] of turtles
mean [price * area-count] of turtles
standard-deviation [price * area-count] of turtles
min [price * area-count] of turtles
max [price * area-count] of turtles
mean [area-count] of turtles
standard-deviation [area-count] of turtles
min [area-count] of turtles
max [area-count] of turtles
```

The standard-deviation reporters are not repeated measures of the same thing. Each
one is the spread across stores within a run for that specific quantity, then the
comparison script averages those per-run values across all runs.

## Comparing Python Against NetLogo

Put NetLogo BehaviorSpace table CSV exports in:

```text
hotelling-law/netlogo tests input here/
```

Then generate Python outputs:

```bash
cd hotelling-law
python3 run.py baseline
python3 run.py plane
```

Compare both layouts:

```bash
python3 compare_netlogo_outputs.py
```

Compare only one layout:

```bash
python3 compare_netlogo_outputs.py --layout line
python3 compare_netlogo_outputs.py --layout plane
```

Comparison CSVs are written to:

```text
hotelling-law/outputs/netlogo_python_line_comparison.csv
hotelling-law/outputs/netlogo_python_plane_comparison.csv
```

The comparison script keeps line and plane separate by filtering on:

```text
layout
number-of-stores
rules
[step]
```

Small differences between Python and NetLogo are expected because their random number
generators and random tie-breaking are not identical. The goal is close distributional
agreement across runs, not exact tick-by-tick equality.

## Model Alignment With NetLogo

Current NetLogo-aligned behaviour:

```text
line layout uses pycor -20..20 with pxcor fixed at 0
plane layout uses pxcor -20..20 and pycor -20..20
plane consumers use all 1681 patches by default
customer choice is based on price + distance
stores start at price 10
movement step is 1 patch
price step is 1
rules supports normal, moving-only, and pricing-only
location and price decisions are planned before being applied
```

Python-specific extension parameters still exist for extension experiments:

```text
distance_weight
customer_distribution
loyalty_strength
loyalty_threshold
```

For NetLogo baseline comparison, these are omitted or kept at neutral values. Do not
vary them in the NetLogo-aligned validation unless the report explicitly discusses
them as Python extensions.

## Project Layout

```text
hotelling-law/
  run.py
  run_custom_experiment.py
  compare_netlogo_outputs.py
  hotelling/
    model.py
    customer.py
    store.py
    experiment.py
    statistics.py
    csv_writer.py
  experiments/
    baseline.py
    plane_baseline.py
    replication_sweep.py
    extension_loyalty.py
  netlogo tests input here/
  outputs/
  tests/
run_custom_experiment.py
```

## Testing

Run the full test suite:

```bash
cd hotelling-law
python3 run.py test
```

Or:

```bash
cd hotelling-law
python3 -m unittest discover -s tests -v
```

## Plot Generation

Generate plots from the standard experiment outputs:

```bash
cd hotelling-law
python3 run.py plots
```

Or from the repo root:

```bash
python3 plot_results.py --experiment all
```

The plotting CLI accepts:

```text
--experiment    baseline | plane | sweep | loyalty | all
--input-dir     folder containing CSV outputs
--output-dir    folder for generated SVG files
```

Current plot types:

```text
baseline / plane: mean store position, profit, and distance-from-centre by tick
sweep:            bar charts of final summary metrics by scenario
loyalty:          line charts of final summary metrics by loyalty_strength
```
