# Extension Design — Customer Loyalty

## Research Question

> "How does customer loyalty affect store clustering, market share, and profit in a
> Hotelling's Law market?"

---

## Motivation

The standard Hotelling model assumes customers switch costlessly between stores.  In
practice, customers often exhibit inertia — they return to familiar stores even when a
slightly better option exists.  This inertia may arise from habit, trust, switching costs,
or loyalty programmes.

Adding a loyalty mechanism to the Hotelling model allows us to investigate:
- Whether stores still cluster toward the centre when customers are less likely to switch.
- Whether loyalty stabilises or destabilises profit and market share.
- Whether stores have reduced incentive to reposition when loyal customers are retained
  regardless of position.

---

## Extension Description

### New Parameters

| Parameter           | Default | Description                                                  |
|---------------------|---------|--------------------------------------------------------------|
| `loyalty_strength`  | 0.0     | Controls how strongly previous-store preference influences  |
|                     |         | customer choice.  Range: 0.0 (no loyalty) to 1.0 (maximum). |
| `loyalty_threshold` | 10.0    | Absolute cost margin for the loyalty retention check.        |

### Loyalty Rule

After the first tick, every customer has a `previous_store_id` recording their last choice.

When `loyalty_strength > 0.0`, before assigning a customer:

1. Find the **best store** by raw effective cost (same as baseline; ties by lowest id).
2. Retrieve the **previous store** for this customer.
3. Compute the **loyalty tolerance**: `loyalty_strength × loyalty_threshold`.
4. If `prev_store_cost <= best_store_cost + loyalty_tolerance`, the customer **stays**
   with their previous store.
5. Otherwise, the customer **switches** to the best store.

**Formula:**
```
stay_with_previous = (prev_cost <= best_cost + loyalty_strength * loyalty_threshold)
```

### Boundary behaviour

- `loyalty_strength = 0.0`: loyalty path is never entered; behaviour is exactly the same
  as the baseline model.  This is verified by unit tests.
- `loyalty_threshold = 0.0`: tolerance is always zero regardless of `loyalty_strength`;
  customers only stay if their previous store is already the cheapest option.
- First tick: all customers have `previous_store_id = None`, so loyalty does not apply
  on tick 0.  This is unavoidable and consistent with the model's initialisation.

### Why Not Apply Loyalty During Position Lookahead?

Store position updates use a simulated profit estimate (`_simulated_profit`).  Loyalty
effects depend on customers' `previous_store_id` values, which represent assignments from
the previous tick.  Applying loyalty in the lookahead would require predicting future
loyalty states, introducing complexity with limited benefit for a first-order model.  The
simplification is documented clearly in the code.

---

## Relevance to Hotelling's Law

In the standard Hotelling model, the incentive to cluster arises because moving toward a
competitor steals customers from their side.  With customer loyalty:

- Customers near a competitor may not switch even if the competitor moves closer.
- This weakens the incentive for aggressive repositioning.
- Stores may find stable equilibria farther apart than the classic centrist solution.

This is related to real-world phenomena like brand loyalty reducing price competition and
geographic market segmentation persisting even when stores could profitably converge.

---

## Experiment Design

**File:** `experiments/extension_loyalty.py`

| Scenario          | `loyalty_strength` | Interpretation             |
|-------------------|--------------------|----------------------------|
| `loyalty_0.0`     | 0.0                | Baseline control           |
| `loyalty_0.25`    | 0.25               | Weak loyalty               |
| `loyalty_0.5`     | 0.5                | Moderate loyalty           |
| `loyalty_0.75`    | 0.75               | Strong loyalty             |

**Fixed parameters:** baseline values (2 stores, 100 customers, market_size 100, 100 ticks,
`loyalty_threshold = 10.0`).

**Runs per scenario:** 30.

**Output metrics compared across scenarios:**
- Mean final store position — does clustering decrease with higher loyalty?
- Mean average distance between stores — are stores more spread out?
- Mean profit — does loyalty raise or lower per-store earnings?
- Mean market share — does loyal retention create more stable distributions?

---

## Expected Behavioural Effects

| Effect                      | Expectation                                              |
|-----------------------------|----------------------------------------------------------|
| Store clustering            | Weaker with higher loyalty (less incentive to converge). |
| Inter-store distance        | Increases with loyalty_strength.                         |
| Profit                      | May decrease if loyalty reduces competition pressure.    |
| Market share stability      | Increases with loyalty (fewer customers switching).      |
| Position equilibrium        | May emerge farther from centre than baseline.            |

---

## Answering the Research Question

The experiment compares the four scenarios across the listed metrics.  The research
question is answered by observing:

1. Whether final-tick store positions diverge more under high loyalty (reduced clustering).
2. Whether profit and market share variances are lower (more stable markets).
3. Whether the relationship is monotonic (more loyalty → more divergence).

Results are summarised in `outputs/extension_loyalty_summary.csv` and can be interpreted
qualitatively against the theoretical expectations described above.
