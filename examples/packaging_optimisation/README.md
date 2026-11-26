# Synthetic packaging layout and quote provenance

A small runnable example of a business decision: which available sheet and layout has the lowest material **plus cutting cost** for a fixed quantity, and can an issued quote still be explained after prices change?

This is independently authored portfolio code with wholly invented specifications, identifiers and prices. It illustrates bounded optimisation and provenance principles related to the [KSP case](../../projects/ksp-mis/README.md). It is not an export, reproduction or validation of the private MIS, a production guillotine implementation, a commercial benchmark or an original Cambridge assignment result. Its tests establish behaviour only for this example.

## Run and inspect

Use Python **3.10 or later**, standard library only; builder execution used Python 3.14.0. From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m examples.packaging_optimisation
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest examples.packaging_optimisation.test_model -v
```

The first command writes or verifies the nine small deterministic files in `results/`. It refuses to overwrite an existing file with different bytes. To reproduce independently, supply `--output /tmp/packaging-demo-a` and then `--output /tmp/packaging-demo-b` using fresh directories, and compare the files. Output files contain no time, machine path or random values. If you edit source or fixtures, use a fresh output directory; the source manifest will correctly differ.

- [Initial fixture](fixtures/initial.json) and [repriced fixture](fixtures/repriced.json): full validated jobs.
- [Initial candidate table](results/initial_candidates.csv) and [repriced table](results/repriced_candidates.csv): every feasible and rejected stock/orientation.
- [Summary](results/summary.json), [initial estimate](results/initial_estimate.json) and [repriced estimate](results/repriced_estimate.json): actual synthetic results and scope.
- [Issued snapshot](results/issued.json): retained inputs, version identities and result.
- [Manifest](results/manifest.json): source, fixture and output hashes, units, measured quantities and limits.
- [Calculation and provenance API](model.py) and [tests](test_model.py).

Public API: construct frozen `Spec`, `Stock`, `PriceBook` and `CutRule` records, then `Job`; call `evaluate(job)` for a detached result, `issue(job, "SYN-quote-01")` for immutable bytes, and `recover(snapshot.payload)` to verify and replay a saved record. `Job.from_dict` loads the fixture schema. Invalid fields or wholly infeasible jobs raise `ValueError`; a mixed feasible/infeasible stock set retains rejected candidates with reasons.

## Candidate family and geometry

Each stock contributes **one maximal uniform grid per allowed orientation**: normal, and optionally a 90-degree rotation. Both are retained even for square blanks. Grids begin at the top-left margin; all blanks in a grid have the same orientation. There are no mixed orientations, partial grids, combinations of stock types or alternative cutting directions. The selected result is best **among the enumerated candidates under the declared model**, not a global unrestricted packing optimum. Even a smaller grid might win under a different candidate family or cost rule.

Lengths are positive integer **millimetres**. Quantity and sheet prices are positive integers; uniform margin, gap and cut rate are nonnegative integers. Booleans are not accepted as integers. The margin applies independently at all four stock edges. The gap is empty material **between** blanks, never an extra gap at an outside boundary. Grain direction is represented only by allowing or prohibiting rotation; thickness, kerf and machine tolerances are not modelled.

For stock width `W`, blank width `w`, margin `m` and gap `g`:

```text
usable_width = W - 2m
columns = floor((usable_width + g) / (w + g))
span_width = columns*w + (columns - 1)*g
```

Height gives the row count in the same way. In words, fit full blanks and their intervening gaps inside the usable rectangle, with no trailing gap. All arithmetic is integer arithmetic. If even one blank does not fit, reject that stock/orientation. The two counts multiply to blanks per sheet `B`; `sheets = ceil(quantity / B)`. Every purchased sheet is cut as the same full grid, including the last sheet. Excess blanks are recorded as unused capacity, with no resale or salvage credit.

Utilisation is the **exact fraction** `B * blank_area / gross_sheet_area`, emitted as integer numerator/denominator. Waste area per sheet is gross area minus all grid blanks, so it includes margins, gaps and unused strips. Surplus cut blanks on the last sheet are reported separately as unused blank capacity; they are not counted as geometric offcut waste.

## Deliberately simplified cutting and cost

The declared cutting model is `trim-envelope-rows-then-blanks-v1`:

1. Trim the stock to the grid envelope. Each of the four envelope sides that is inset from the corresponding stock edge costs one cut; a side already at a stock edge costs none.
2. Separate rows across the envelope width. Each row boundary costs one cut when gap is zero; a positive gap strip needs two cuts to remove it.
3. Cut each row separately into blanks, again one cut per zero-gap boundary or two per positive-gap strip. Rows and sheets are **never stacked**.

These are idealised operations on individual rectangles, with zero kerf and no setup, repositioning, handling, tool wear or maximum cutting length. No final blank edge finishing is added. Gap-removal and envelope trims are already counted, so no further generic trim charge is added. With `R` rows, `C` columns, `T` exterior trims and `k = 1` for zero gap or `2` otherwise:

```text
cuts_per_sheet = T + k*(R - 1) + R*k*(C - 1)
material_minor = sheets * sheet_price_minor
cutting_minor = sheets * cuts_per_sheet * cost_per_cut_minor
total_minor = material_minor + cutting_minor
```

In words, pay for every whole sheet and every operation on that sheet. Prices are integer **SYN minor units**, where 100 minor units make one invented major unit. No real currency, tax, shipping, markup, stock availability or minimum order is represented. Final rounding is the identity operation: all arithmetic is exact integer minor units, and fractional prices are rejected. Displaying 590 as 5.90 does not change the objective.

Ties use total cost, then stock identifier in ascending ASCII order, then normal before rotated. Stock-list order does not affect canonical inputs, results or selection. Version strings identify records; the full contents are also hashed, so changing data without changing a version still changes its input digest. The program cannot enforce external version governance.

## Worked result from the actual demo

The initial job asks for 12 blanks of 40 × 30 mm, with 5 mm margins and 5 mm gaps. Cutting costs 10 minor units per operation.

| Stock / orientation | Grid | Sheets | Cuts per sheet | Material | Cutting | Total minor units |
| --- | --- | --- | --- | --- | --- | --- |
| SYN-small / normal (100 × 80 mm) | 2 × 2 | 3 | 10 | 300 | 300 | 600 |
| SYN-small / rotated | 2 × 1 | 6 | 6 | 600 | 360 | 960 |
| SYN-large / normal (145 × 80 mm) | 3 × 2 | 2 | 14 | 310 | 280 | **590** |
| SYN-large / rotated | 4 × 1 | 3 | 10 | 465 | 300 | 765 |

SYN-narrow (25 × 80 mm) fails in both orientations. Among feasible stocks, the small sheet has the lowest nominal price (100 versus 155), but its best layout costs 600 for the job. The combined objective selects the large normal grid at 590: 10 more in material, 20 less in cutting, and 10 less overall. This is synthetic arithmetic, not a measured commercial saving.

For the large normal grid, the envelope is 130 × 65 mm: four exterior trims, two row-separation cuts, and eight blank-separation cuts give 14 cuts per sheet. Two sheets produce exactly 12 blanks. Its utilisation is `7200/11600` (18/29), versus `4800/8000` (3/5) for the small normal grid.

The second fixture changes only the price version and large-sheet price, from 155 to 175. That plan then costs 350 material + 280 cutting = 630; a **new estimate** selects the small normal grid at 600. The issued original remains 590, with its original specification, complete price book, cutting rule, input digest and candidate table intact.

## Provenance and validation scope

The input identity hashes canonical UTF-8 JSON: sorted object keys, ASCII escapes, compact separators, no NaN and no final newline. Stocks are sorted by identifier. The representation includes the specification, complete stock dimensions/prices, price and cutting-rule versions, currency/units, model version, cutting-model identity, tie rule and money rule. [Canonical initial inputs](results/initial_inputs.json) and [repriced inputs](results/repriced_inputs.json) can be hashed directly. Results never enter their own input hash.

An issued snapshot is a frozen record holding immutable canonical bytes. Loading returns a detached dictionary and checks input identity plus a complete replayed result. Repricing builds a new job rather than mutating the issued record. Keep the versioned source alongside snapshots for replay. This is an offline illustration, with no transaction service, signatures, access controls or durable write-once storage. Hashes and replay detect inconsistencies; they cannot prove authenticity or prevent someone replacing an entire file and its hashes.

The manifest hashes each package-root Python file (including tests) and a canonical path-to-hash map as the source identity. It separately hashes fixture bytes and all eight result payloads; it excludes itself to avoid self-reference. No uncommitted candidate is presented as a final Git commit. The coordinator can bind accepted bytes to a later commit.

Tests cover hand-calculated totals, exact-fit and one-millimetre gap/margin boundaries, rotation, rejected layouts, invalid input, full-sheet rounding, deterministic ties, exact money, input changes and issued-record preservation/tamper detection. An independently written tiny oracle places rectangles by coordinates, counts distinct cut edges and accumulates sheets without the production counting formulas. It exhausts **1,152 small jobs**, with two stocks and both orientations per job; it checks the selected candidate only within the same maximal-grid family. It is narrower than manufacturing validation and does not establish unrestricted packing optimality. Artifact tests also check repeated generation and output digests.

Builder execution is not independent acceptance. No runtime speedup, factory performance, commercial outcome or historical private-system test result is established by this package.

[Portfolio](../../README.md) · [Project index](../../docs/project-index.md)
