# Staged student dropout classification with invented data

This independently authored, standard-library example implements a corrected evaluation protocol alongside the [completed Cambridge case](../../projects/student-dropout/README.md). It trains a prevalence baseline and logistic comparator at three decision stages, selects settings and thresholds on development data, and measures the frozen choices on identical evaluation rows. All **192 learners are invented**. No original student data, notebook, trained model or SHAP output is included.

## Run offline

Python 3.10+; builder verified on Python 3.14.0. No installs, downloads or model services. From the repository root:

```sh
python3 -B -m unittest examples.student_dropout.test_protocol -v
# Choose fresh output directory names; on macOS use /private/tmp, not its symlink /tmp.
python3 -B -m examples.student_dropout --output /private/tmp/dropout-demo-a
python3 -B -m examples.student_dropout --output /private/tmp/dropout-demo-b
diff -r /private/tmp/dropout-demo-a /private/tmp/dropout-demo-b
python3 -B scripts/check_portfolio_links.py
```

On systems without `/private/tmp`, use a real temporary directory path. Existing output directories and symlink paths are refused. [Fixture generator](fixture.py), [exact input](fixtures/cohort.json), [configuration](protocol.json), [tests](test_protocol.py) and [retained manifest](results/manifest.json) are inspectable. SHA-256 binds the exact input/config bytes consumed, Python source including tests, frozen state and every output payload. The manifest excludes itself; it records runtime version. Replays on the same runtime produce identical bytes. Hashes establish identity, not authenticity.

## Cohort and feature availability

One record per learner is required. Duplicate learner/record IDs, groups spanning splits, unassigned cohorts and unavailable features fail validation. All rows must have the full schema; a missing measurement is `null`, while a missing field is rejected. No method can drop a difficult row. The common eligible cohort consists of learners represented through all three decision points with later outcome ascertainment. That retrospective eligibility definition would need scrutiny for selection bias with real early dropouts.

| Decision stage | Decision time | Cumulative predictor allowlist and definition |
| --- | --- | --- |
| Enrolment | Enrolment day | `orientation_tasks`: 0–8 completed preparatory tasks; `enrolment_check`: administrative checklist status |
| Engagement | Day 30 | Above, plus `absence_count`: 0–20 missed scheduled sessions; `practice_completed`: 0–10 practice tasks completed by day 30 |
| Academic progress | Day 90 | Above, plus `assessed_modules`, `passed_modules`, `failed_modules`: 0–6 modules assessed by day 90; observed counts satisfy assessed = passed + failed |

The [contract](contract.py) enforces each observation's availability between enrolment and its stage deadline, even when used at a later stage. Missing values still require a timestamp documenting the observation window. The generator uses one latent readiness draw plus separate deterministic SHA-256 draws for process observations and the terminal binary outcome at day 180. It includes missing measurements and an evaluation-only checklist category. This is an invented process, not a fit to the original study or a realistic dropout simulation.

Predictors contain no age, sex, nationality, location, course or institution proxies. IDs, group/cohort labels and dates never enter the model. `age_at(birth_date, reference_date)` demonstrates completed-birthday derivation using an explicit reference date, with boundary tests; age is excluded from this example. The original study used a fixed-year approximation, discussed in the case. Excluding demographic predictors does not demonstrate fairness; even process measures can have unequal meanings in real settings.

[Named split IDs](results/splits.json) contain 64 learners each from 2021 (train), 2022 (development) and 2023 (evaluation), sorted by stable ID. Groups are administrative sets of four learners confined to one phase. Every earlier phase's labels must be available strictly before the next phase's earliest enrolment, so all stage comparisons share valid chronology. These artificial dates exercise a **fixed retrospective evaluation**, not forward prospective validation, a real temporal generalisation finding or an intervention trial.

## Fit and selection

[Preprocessing and models](models.py) learn numeric medians, filled-column means/population standard deviations and sorted categorical vocabularies on training rows only. An entirely missing numeric training column uses zero; zero variance uses scale one. Missing and unseen categories have distinct fixed buckets. No learned transform is refitted on development or evaluation.

The prevalence model emits the training positive fraction. Logistic regression uses zero initial coefficients, 160 full-batch gradient steps at learning rate 0.1 and three L2 strengths (0, 0.05, 0.2). Development log loss selects the strength; an exact tie chooses smaller L2. The intercept is unpenalised. There is no calibration fit, evaluation-driven early stopping or refit on development. These scores are not established calibrated probabilities.

[Protocol code](protocol.py) exposes `fit_stage(stage, train, development, config)` with no evaluation argument. Immutable model, transform and threshold objects are created for every stage/method before scoring. [Frozen choices](results/frozen.json) retain development search losses, selected settings and threshold status. The runner serializes the choices before generating evaluation scores and checks that state remains unchanged. [Predictions](results/predictions.csv) retain exactly the expected evaluation ID order independently of model outputs; missing, duplicate or extra predictions fail rather than shrinking the denominator.

## Threshold and metric definitions

The declared rule seeks **recall ≥ 0.75 with at most 50% of development rows alerted**. Among feasible score thresholds it chooses the fewest alerts, then the highest threshold. If infeasible, it maximizes recall within capacity, then minimizes alerts, then chooses the highest threshold. Status remains explicitly infeasible. With no development positives, recall is undefined and alert-none is chosen.

Alert means `score >= threshold`; tied scores enter together. Candidates include every distinct development score, zero (alert-all for valid scores) and explicit `null` (alert-none, even at score 1). No arbitrary ordering splits ties to fill capacity. A constant prevalence score cannot alert a subset: under this cap its selected action is none. The capacity is a **development selection constraint**, not a guarantee of future workload. Evaluation cannot change the threshold or enforce a new quota.

[Metrics](metrics.py) report TP, FP, TN, FN; precision = TP/(TP+FP), recall = TP/(TP+FN), specificity = TN/(TN+FP), false alerts = FP, alert count and workload = alerts/N. ROC-AUC uses positive/negative rank pairs with half credit for ties. **Average precision** is the sum of recall increments times cumulative precision at complete tied-score blocks; it is not trapezoidal PR-AUC. Zero denominators yield JSON `null` / empty CSV fields. ROC-AUC is undefined with one class, AP is undefined with no positives and equals one with only positives. Empty metric inputs yield zero counts and undefined rates; the runner requires nonempty phases.

## Actual synthetic evaluation

Each row below measures the same 64 evaluation learners, including 27 positives. Values are rounded here; [scores.csv](results/scores.csv) retains full precision and all counts.

| Stage | Method | TP / FP / TN / FN | Precision | Recall | Specificity | Alerts / workload | ROC-AUC | AP |
| --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| Enrolment | Prevalence | 0 / 0 / 37 / 27 | undefined | 0.000 | 1.000 | 0 / 0.000 | 0.500 | 0.422 |
| Enrolment | Logistic | 17 / 20 / 17 / 10 | 0.459 | 0.630 | 0.459 | 37 / 0.578 | 0.602 | 0.504 |
| Engagement | Prevalence | 0 / 0 / 37 / 27 | undefined | 0.000 | 1.000 | 0 / 0.000 | 0.500 | 0.422 |
| Engagement | Logistic | 16 / 18 / 19 / 11 | 0.471 | 0.593 | 0.514 | 34 / 0.531 | 0.630 | 0.574 |
| Academic progress | Prevalence | 0 / 0 / 37 / 27 | undefined | 0.000 | 1.000 | 0 / 0.000 | 0.500 | 0.422 |
| Academic progress | Logistic | 13 / 17 / 20 / 14 | 0.433 | 0.481 | 0.541 | 30 / 0.469 | 0.618 | 0.635 |

Development logistic recall was 0.75, 0.70 and 0.60 at 30, 32 and 32 alerts respectively; only enrolment met the target under capacity. All prevalence choices were infeasible. No model meets 75% recall on evaluation. Enrolment and engagement evaluation workloads exceed 50%; the thresholds remain frozen. Later features do not uniformly improve every metric. These results establish mechanics only: no original-study superiority, earlier decision efficacy, calibrated probabilities, subgroup fairness, intervention benefit or deployment readiness.

## Authorized private input route

The original learner-level input route and continued local processing permission remain unresolved. **No real-data rerun was performed.** Local processing rights and redistribution rights are separate. Do not use actual predictions for student decisions.

An authorized custodian can prepare an extract with this schema outside the checkout, using pseudonymous IDs, explicit observation/label dates and the common eligible cohort. Retain the source byte identities, schema mapping, exclusions, processing basis and original-to-pseudonym mapping privately. The runner is capped at 10,000 rows and fixed illustrative count ranges; this is a bounded adapter route, not a drop-in importer for the original study. Changing those constraints requires a reviewed schema/protocol revision, not silently clipping or sampling records.

Before reading record content, the runner requires a private permission receipt containing `authorized_local_processing: true`, `redistribution_authorized: false`, `scope: "private_retrospective_methodology"`, a nonempty `authority_reference`, and `input_sha256` / `config_sha256` for the exact files. This records the caller's established authority; the receipt cannot itself grant permission. Keep input, config, receipt and fresh output directory outside the checkout:

```sh
python3 -B -m examples.student_dropout \
  --input "$PRIVATE_INPUT_JSON" --config "$PRIVATE_CONFIG_JSON" \
  --permission-receipt "$PRIVATE_PERMISSION_JSON" --output "$PRIVATE_NEW_OUTPUT_DIR"
```

Outputs include an exact adapted input snapshot, IDs, labels, predictions and fitted parameters. They remain private, with scope and receipt hash in the manifest. Neither those outputs nor original source artifacts belong in the public results directory.

## Original advanced-model rerun requirements

[adapters.py](adapters.py) offers a bounded, dependency-injected backend interface, tested with constant-score doubles. It fits transforms on train, allows at most four candidate settings, selects by development AP and freezes the threshold. It receives no evaluation labels. A fresh XGBoost factory can return `predict_proba(X)[:, 1]`; a Keras factory can return flattened `predict(X)` scores. Factories must not capture held-out data; this interface cannot police arbitrary closures or make a mutable third-party backend immutable. No advanced library is imported, installed or rerun here, and doubles supply no model-performance evidence.

A correct original XGBoost/NN/SHAP comparison still needs authorized local inputs and exact hashes; verified learner joins and eligibility across staged releases; genuine decision/observation/outcome dates; reference-date age handling; all imputation and feature selection moved inside train; compatible recorded installed dependencies; explicit seeds, threads, bounded search and early-stopping policy; one frozen retrospective row contract; and development-only model/threshold choices. Backend-specific integration tests and reproducible model-state snapshots are required. SHAP should use a documented training/background sample and explain the frozen model, without causal interpretation. Reused historical holdouts remain retrospective. Prospective validation, subgroup error/calibration work, consent/governance and an evaluated support intervention are separate future tasks.

[Portfolio](../../README.md) · [Project index](../../docs/project-index.md)
