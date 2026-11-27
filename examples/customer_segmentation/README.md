# Corrected customer segmentation mechanics

This revision repairs currency signs, distinct-order frequency and cluster evaluation in a portable, offline pipeline. **The results below use invented purchases only.** The completed Cambridge assignment and its original notebook/PDF remain historical evidence; no corrected real-customer profiles have been produced. Original-input availability and express continuing local-processing permission remain unresolved, separately from redistribution permission.

From the repository root, with Python 3.10+ and no packages or network:

```bash
python3 -B -m examples.customer_segmentation --output /private/tmp/segmentation-demo
python3 -B -m unittest examples.customer_segmentation.test_pipeline -v
python3 -B scripts/check_portfolio_links.py
```

Choose a fresh output directory; existing results are never overwritten. The [fixture generator](fixture.py) independently invents 30 eligible customers, one deliberately ineligible customer and one repeated line. The [fixed protocol](protocol.json) declares 18 fit and 12 evaluation customers, k=2/3, five restarts, 60 iterations and seeds before evaluation. IDs determine cohorts, not outcomes. This is a mechanics demonstration, not a representative sample or a temporal validation study.

## Measured synthetic results

The [retained evaluation](results/evaluation.json), [fitted states and centres](results/frozen.json), [customer features](results/customers.json) and [ingestion ledger](results/ledger.json) belong to the same [hashed run](results/manifest.json). Profiles are arithmetic means in original feature units; centres are in transformed standardized coordinates. Both k candidates remain available; no winner is automatically deployed or refitted on holdout.

| Diagnostic | k=2 | k=3 |
| --- | --- | --- |
| Fit silhouette (18 customers) | 0.395231 | 0.362782 |
| Held-out silhouette (12 customers) | 0.367806 | 0.244114 |
| Fit cluster sizes, label order | 9 / 9 | 3 / 6 / 9 |
| Held-out cluster sizes, label order | 7 / 5 | 1 / 4 / 7 |
| Held-out seed ARI range | 1.000000–1.000000 | 0.811966–1.000000 |
| Held-out resample ARI range | 1.000000–1.000000 | 0.811966–0.873199 |
| Held-out ARI after dropping cost mix | 1.000000 | 0.811966 |

Two clusters have stronger geometric separation here. Three clusters include a singleton evaluation cluster and show weaker agreement under perturbation. A perfect ARI on this tiny invented cohort does not establish population stability, useful personas or business value. These outcomes were retained without changing the fixed fixture/configuration after evaluation.

The ledger counts 136 input lines, 135 unique keyed lines and 30 eligible customers after excluding the customer with missing profit. The eligible 134 lines reconcile exactly: invented revenue 5,473.80 minus purchased-item cost 4,820.40 equals observed profit 653.40. The deliberately missing profit remains missing, even though revenue and cost are zero.

## Feature and ingestion contract

The canonical CSV fields, in order, are `customer_id,order_id,line_id,order_date,quantity,revenue,unit_cost,profit,currency`. Customer identities must be stable; a globally unique order belongs to one customer, date and currency. `(order_id,line_id)` identifies a line. Identical parsed records at that key are replay duplicates and counted once; conflicting records fail. Separate line IDs preserve legitimate identical purchases. A missing or invented ad hoc line identity cannot resolve duplicate ambiguity in original data.

Only positive integer purchase quantities and a single USD-style currency are supported. Revenue and unit cost must be nonnegative; observed profit may be signed. Returns, cancellations, mixed currencies and taxes/discount adjustments require an explicitly reviewed schema adaptation. Money uses `Decimal`: `($0.40)`, `-$0.40`, `$-0.40` and `-0.40` all mean −0.40. Well-grouped thousands separators and at most two decimal places are accepted. Empty text, `.`, `NA` and `N/A` are missing; zero is a value. Malformed grouping, percentages, scientific notation, nonfinite values, ambiguous signs and other currencies fail.

Each complete line checks `residual = observed_profit − (revenue − quantity × unit_cost)`. The default absolute tolerance is 0.01 per line, with a hard failure outside tolerance. The alternate `flag_exclude_customer` policy records the exception and excludes the entire customer. Missing required monetary values also exclude the whole customer, preserving a reason in the ledger; partial totals and zero imputation are prohibited. The aggregate bound is number of retained customer lines × per-line tolerance, not a second permissive test. No discount is subtracted twice: the identity assumes supplied revenue is the realized line total; its applicability must be established for any private mapping.

All dates must lie in the explicit inclusive observation window, 2024-01-01 through reference date 2025-01-01 in this fixture. Invalid/out-of-window lines fail. Declared fit and evaluation IDs must be disjoint and cover exactly all eligible customers; eligibility changes require a new protocol, not silent cohort deletion.

| Feature | Definition and interpretation |
| --- | --- |
| `recency_days` | Reference date minus latest eligible purchase date; never system time or the observed maximum date. |
| `distinct_orders` | Number of distinct order IDs per customer; separate from retained `line_count`. |
| `observed_profit` | Sum of signed observed line profit within the window; not predictive lifetime value. |
| `unit_weighted_cost` | Sum(quantity × unit cost) / sum(quantity); purchased-item cost mix, not price response. |
| Audit/profile fields | Revenue, purchased cost, purchased units, retained lines, unweighted line mean unit cost and reconciliation residual. These are not additional clustering features. |

The primary cost feature deliberately weights purchased units. The historical notebook used an unweighted line mean; both meanings are named separately. Age is omitted to avoid silently carrying forward the original approximate birthdate/age treatment. No predictive CLV, price elasticity, measured campaign lift or retention effect is estimated.

## Model and evaluation

For each feature, `t = asinh(x / s)` uses fixed scales `[30, 1, 20, 10]` in feature order. This signed monotone transform is defined for losses and zero. `z = (t − mean_fit) / sd_fit` uses population standard deviation learned only on the declared fit cohort. A fit standard deviation ≤ 1e−12 makes that dimension zero for all subsequent rows. Fixed scales are domain choices, not estimates from holdout.

K-means minimizes squared Euclidean distance with seeded K-means++ initialization, five deterministic restarts and a 60-iteration cap. Ties prefer the lower cluster label and then earlier restart. Degenerate empty-cluster restarts are discarded and counted; all-degenerate fits fail. The retained state reports convergence, iterations, valid restarts, seeds and fit IDs. No full-population hierarchical clustering or embeddings are used.

Silhouette is `(b − a) / max(a,b)`, where a is mean within-cluster distance and b the smallest mean distance to another cluster; singleton clusters score zero. It is exact on each small fixture cohort. Larger approved cohorts use at most 100 customers chosen by fixed-seed uniform sampling, with the sampled IDs retained. That measures separation within the sample, not a full-population silhouette. Unrepresented/degenerate cluster coverage returns an explicit null result.

Seed fits use seeds 41, 73 and 109. Each resample retains floor(0.8 × fit size) customers without replacement and learns its own preprocessing. All candidate fits, including the predeclared cost-feature omission, freeze **before** evaluation. Each predicts the same untouched evaluation customers. Adjusted Rand index (ARI) compares pair agreements adjusted for chance; it is invariant to label numbering, can be negative and equals 1 for identical partitions. Profiles and sizes for every variation are retained; label numbers across runs are not personas. This evaluates assignment sensitivity, not business usefulness or future-time stability.

The adapter caps input/config/receipt files at 4 MB, 5,000 raw lines, 300 customers, four stability seeds, ten restarts and 100 iterations. These deliberately small limits make standard-library execution portable. The original approximately 68k-customer study needs a separately scoped, efficient implementation and authorized data access; this route does not promise a population rerun.

## Evidence and private input route

[Source differences](source_notes.md) records cell-level defects, original schema differences and the unresolved saved-state/count discrepancy without publishing original records. [Private adapter instructions](private_input.md) explain the canonical mapping and established permission receipt. The gate binds exact consumed input/config bytes and private locations; it does not grant rights or authenticate a claimed permission. Public hosting and historic coursework access are insufficient grounds for continuing processing or redistribution.

The manifest hashes the exact read-once input/config buffers, Python source, frozen fits and every output payload. `run_id` hashes the input/config/source identity map; the manifest excludes itself. Two fresh runs are byte-identical on the recorded Python runtime. Floating-point last bits across Python/platform implementations are not promised. Hashes detect changes against retained evidence, not forgery of an entire evidence bundle. Tests verify arithmetic, fit boundaries, label permutation, invalid cohorts, perturbation controls and permission/content tampering. Builder checks are not independent acceptance.

[Customer-segmentation case](../../projects/customer-segmentation/README.md) · [Portfolio](../../README.md)
