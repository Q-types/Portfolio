# Financial-text measurement, with invented data

This standard-library example makes the joins and denominators behind a financial-text case inspectable. Two invented banks, three calls, seven questions and two manually assigned theme proxies demonstrate measurement mechanics. The [completed Bank of England case](../../projects/bank-of-england-nlp/README.md) reports separate saved research findings. These fixtures contain no original transcript excerpts, assignments, sentiment outputs or teammate code.

## Run offline

From the repository root, with Python 3.11 or later:

```sh
python3 -B -m unittest -v examples.financial_text_nlp.test_measurement
python3 -B -m examples.financial_text_nlp --output /tmp/financial-text-demo-1
python3 -B -m examples.financial_text_nlp --output /tmp/financial-text-demo-2
diff -r /tmp/financial-text-demo-1 /tmp/financial-text-demo-2
python3 -B scripts/check_portfolio_links.py
```

Choose new output directory names: existing directories are rejected. No install, model, download, network request or environment mutation is needed. [Fixture](fixtures/synthetic.json), [measurement implementation](measurement.py), [tests](test_measurement.py) and [result manifest](results/manifest.json) are inspectable. The manifest records Python version, source hashes, exact input bytes and result payload hashes; it excludes its own hash. Two replays on the same runtime produce identical bytes. Different Python versions change runtime metadata. Hash consistency establishes identity, not authenticity or scientific accuracy.

## Measurement contract

| Layer | Identity and checks |
| --- | --- |
| Sources | Selected and history-only revision IDs; one selected revision per call; immutable release ID; canonical text and SHA-256 |
| Structure | Bank → call/quarter → ordered segment → speaker; explicit section and channel; questions cover all analyst-question segments |
| Population | A separate question-ID roster per call defines the total denominator; fit eligibility is explicit; missing assignments remain rows |
| Assignments | One row per question or window; matching call, revision, release, canonical-text hash and assignment version; duplicates and foreign keys fail |
| Windows | Non-overlapping four-whitespace-token windows, including short tails, for both analyst and prepared channels; all tokens stay in each channel's denominator |
| Aggregation | Complete declared bank-quarter × theme grid; same-call, same-bank, same-quarter comparisons; missing calls and unmatched channels retained |
| Sentiment | Signed invented scores in [−1, 1]; missing row, missing value, absent theme and observed zero distinguished |

Canonical text is Unicode NFC with whitespace collapsed to single spaces and ends stripped; hashes cover its UTF-8 bytes. Keys must already be lowercase ASCII identifiers: normalization is never silently applied during a join. Source-revision text is the ordered concatenation of its segments. Changing text requires new identities and matching assignments. Source hashes and canonical-question hashes have defined, separate scopes.

The example's **fit rule is at least four whitespace tokens in an analyst question**. This is an illustrative policy, not the historical project's eligibility rule. It yields six eligible questions out of seven total; only three questions receive a retained proxy. One short question is excluded, one is noise, one unresolved, and one has a missing assignment. These categories stay in the denominator. The expected coverage receipt is checked against actual joins, not trusted as a substitute for validation.

Question shares count questions. Token shares sum the tokens in assigned windows, divided by **all channel tokens**, including tokens with no assignment. No question-frequency share is compared with a prepared-token share. The historical project used 128-wordpiece windows; this tiny example uses a transparent whitespace tokenizer and performs no BERTopic fit or projection.

## Hand-computable results

In Alder 2024Q1, question `q1` has eight funding tokens, `q2` has four noise tokens, and `q3` has two excluded tokens. Prepared remarks have four funding and four lending tokens.

| Alder 2024Q1 funding measure | Numerator | Denominator | Result |
| --- | ---: | ---: | ---: |
| Question-frequency share | 1 question | 3 questions | 1/3 |
| Analyst token share | 8 tokens | 14 tokens | 4/7 |
| Prepared token share | 4 tokens | 8 tokens | 1/2 |
| Analyst minus prepared gap | 100 × (4/7 − 1/2) | percentage points | 50/7 ≈ 7.142857 |
| Conditional sentiment | +0.5 | 1 observed funding question | +0.5 |

Across the fixture: seven denominator questions, six fit-eligible, three retained-proxy questions (**3/7 coverage**), eleven windows, one missing question assignment and one missing window assignment. Three sentiment rows include one missing value; four questions have no sentiment row.

| Bank-quarter | What the output preserves |
| --- | --- |
| Alder 2024Q1 | Complete matched token comparison; absent lending-question sentiment is undefined |
| Alder 2024Q2 | Three questions / twelve analyst tokens, including an unassigned four-token question; the gap and conditional sentiment are withheld because assignment coverage is incomplete |
| Birch 2024Q1 | Funding question present but sentiment absent; prepared channel missing; no gap |
| Birch 2024Q2 | Declared cohort with no call; null shares and no gap, rather than invented zero observations |

`question_share` and channel token shares retain observed assigned mass over the full denominator. Where assignments are missing, these are **lower bounds on proxy coverage**, labelled incomplete; they are not complete thematic estimates. A conditional sentiment mean requires complete question assignments and a score for every question in the theme. An absent theme has no conditional sentiment. The test that completes Alder Q2 question assignments demonstrates a genuine neutral lending mean of **0.0**, while a missing theme remains null. No missing row is silently dropped or converted to zero.

Inspect [bank-quarter rows](results/bank_quarter.csv), [joined questions](results/questions.csv), [window ledger](results/windows.csv) and [coverage audit](results/audit.json). CSV empty fields represent unavailable values; the status columns explain why. The cohort is explicitly declared, not expanded into a guessed balanced panel. No lead–lag model or significance test is fitted to this tiny invented sample.

## Adapting an authorized precomputed table privately

An adapter can be written outside this checkout to translate an authorized, frozen assignment table to this JSON contract. Keep its exact source-byte digest, schema, release, model/mapping version, selected revisions and processing permission in a private receipt. A private input may use the same `synthetic_measurement_v1` schema identifier: this identifies the demonstration contract, not the origin of its data.

Map the complete canonical question roster first, including non-retained and non-fitted rows. Join precomputed question assignments on the question ID **and** call/revision/release/text hash; never recover identity by row position or fuzzy text matching. Translate an explicitly approved fixed theme mapping; do not infer fit eligibility from retained status. Preserve the original eligibility field in a richer adapter, and replace this example's four-token policy only through a separately reviewed implementation.

Question-level assignments cannot supply token-window assignments. The adapter also needs independently authorized canonical segments, speaker/channel metadata and matching precomputed windows made under this exact tokenizer/window contract. If only question assignments are available, the token comparison is unsupported: do not repeat a question label across invented windows. A source using another tokenizer requires a separately versioned implementation and tests. Source text must remain private; hashes alone cannot reconstruct or validate unavailable canonical text.

Only run after confirming local processing permission separately from redistribution permission:

```sh
python3 -B -m examples.financial_text_nlp \
  --input "$PRIVATE_INPUT_JSON" --authorized-local-use \
  --output "$PRIVATE_NEW_OUTPUT_DIR"
```

Non-fixture inputs and outputs must be outside the checkout. The flag records the caller's authorization assertion; it cannot establish rights. Outputs include the exact input snapshot, canonical text, IDs and derived rows and therefore remain private. Publish neither those outputs nor original-source identifiers. The bundled fixture and results are independently invented; they establish auditable mechanics, not original-project accuracy or prospective financial-risk performance.

[Portfolio](../../README.md) · [Project index](../../docs/project-index.md)
