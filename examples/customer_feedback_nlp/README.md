# Invented customer-feedback evaluation

This small offline example evaluates authored mock issue extractions and runs an optional actual LDA topic comparison. All review text, IDs, reference issues and mock outputs were independently invented by a Codex agent for this example. No original reviews, hidden prompts, saved model outputs or original-data distributions were used to construct it. The same agent authored the semantic annotations; there is no independent human adjudication, held-out language-model benchmark or business-performance claim.

From the repository root, choose fresh output directories. No installations, downloads, providers or pretrained model loads are used.

```sh
python3 -B -S -m examples.customer_feedback_nlp --output "$RUN_DIR/feedback-smoke"
python3 -B -S -m unittest examples.customer_feedback_nlp.test_evaluation -v
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python3 -B -m examples.customer_feedback_nlp --scientific --output "$RUN_DIR/feedback-lda"
python3 -B -m unittest examples.customer_feedback_nlp.test_evaluation -v
python3 -B scripts/check_portfolio_links.py
```

Set `RUN_DIR` and `TMPDIR` to private writable directories. The smoke commands need only Python 3.10+; `-S` excludes site packages and skips the LDA test. The science commands require an already installed NumPy/SciPy/scikit-learn runtime and fail if absent. Retained executions used CPython 3.11.14, arm64, NumPy 2.3.5, SciPy 1.17.1 and scikit-learn 1.7.2. Both modes replayed exactly twice in that runtime; cross-platform floating-point identity is not promised. The CLI sets a one-thread budget and installs a Python audit hook denying socket connection, bind and DNS. The fixture-only runner has no external-input adapter.

[Reviews](fixtures/reviews.json), [mock predictions and annotations](fixtures/mock.json), and the [reference rubric](rubric.json) are bound by the [pre-measurement identity lock](predeclared.json). The lock was saved before implementing or running the evaluator. It is not an independently timestamped preregistration and cannot prevent replacement of the entire evidence bundle. No fixture, annotation or rubric was tuned to measured scores.

## Cohort and measures

The 14 input rows contain 13 distinct IDs. One exact repeated ID collapses. One empty review, one non-English review and one positive-rating review are excluded, leaving all ten eligible negatives. Equal text with distinct IDs remains separate. Eligibility uses authored language metadata and ratings one/two, not a language detector. The four source/location groups each retain their own input, unique and eligible counts; the eligible counts are 3, 3, 2 and 2 in sorted group order. There is no random sampling or claim of population coverage.

| Authored mock measure | Observed numerator / denominator |
| --- | --- |
| Supported claims / all predictions | 7 / 11 |
| Unsupported claims / all predictions | 3 / 11 |
| Ambiguous claims / all predictions | 1 / 11 |
| Duplicate issues / supported claims | 1 / 7 |
| Matched definite issues / definite references | 6 / 9 |
| Omitted definite issues / definite references | 3 / 9 |
| Correct category / unique matches | 5 / 6 |
| Useful specificity / unique matches | 5 / 6 |
| No-issue reviews without claims / no-issue reviews | 0 / 1 |

These are arithmetic over the explicit authored judgments, not semantic accuracy estimated by code. Exact spans and text hashes verify attribution only. A maximum-cardinality one-to-one matcher uses authored supported edges within each review; repetition gets no second credit. Category and specificity are separate from support. Ambiguous references are outside the definite-recall denominator and remain visible. Empty denominators are null, never zero accuracy. All intended review IDs must be represented, even when no issue was extracted.

The [retained evaluation](results/scientific/evaluation.json) includes every review, match, omission, duplicate and authored rationale. For example, mock claim P04 turns an access failure into payment theft; P05 invents a refused refund in a no-issue review; P10 contradicts an on-time replacement. P06 makes a definite attribution despite uncertainty. P01/P02 repeat one delay; a damaged item and a missing return label are omitted. P03 describes a billing problem under the delivery category. P07 loses useful detail. These failures remain part of the result.

## Actual topic comparison

The [scientific topic result](results/scientific/topics.json) contains actual scikit-learn `LatentDirichletAllocation` fits on a common count vocabulary, with fixed seed 19, two/three topics, at most eight batch iterations, up to 120 features and one thread. Both candidates are retained; no winner or refit is selected.

| Topics | In-sample perplexity |
| --- | --- |
| 2 | 60.307083 |
| 3 | 70.143948 |

All ten eligible reviews, including the no-issue and ambiguous cases, enter both fits. Vocabulary, component weights, top words and document-topic weights are saved. These fit diagnostics neither measure semantic correctness nor generalisation. No BERTopic/BERT/Phi-4 substitute is used. Those original methods remain unexecuted here, and mock issue outputs are not model inference. The [smoke topic artifact](results/smoke/topics.json) explicitly marks LDA pending.

The [scientific manifest](results/scientific/manifest.json) and [smoke manifest](results/smoke/manifest.json) bind exact input, rubric, lock, Python source, runtime and result bytes. Run identity includes the runtime and mode. The [verifier](verify.py) checks exact file sets, identities, retained inputs and a fresh standard-library accounting replay. It does not rerun scientific fits in the documentation checker; two separate fresh scientific runs establish replay in the recorded environment.

[Tests](test_evaluation.py) cover wrong IDs/spans/hashes, unsupported claims with valid spans, maximum matching, duplicates, omissions, category mistakes, uncertainty/conflict, group coverage, zero/empty denominators, exact artifacts and actual LDA dimensions. The [case](../../projects/customer-feedback-nlp/README.md), [methods](../../projects/customer-feedback-nlp/methods.md) and [evidence boundary](../../projects/customer-feedback-nlp/evidence.md) distinguish this new example from completed coursework and unresolved original-data permission/lineage.
