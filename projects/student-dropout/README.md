# Student dropout risk and decision timing

I completed this Cambridge classification assignment in March 2026, comparing XGBoost and TensorFlow/Keras neural networks across three releases of student information. The report, dated 14 March, describes **25,059 observations**, approximately 85% course completion and 15% dropout. My contribution covered preprocessing, staged model comparisons, recall-oriented threshold analysis and SHAP interpretation.

The useful question was when student-support staff could identify learners who might need help. Later academic information may distinguish recorded outcomes while arriving too late for early support. The original stages made that trade-off explicit:

| Original stage | Observed feature definitions | Intended decision window and limitation |
| --- | --- | --- |
| Enrolment | Birth-year-derived age, first-intake flag, booking/lead source, course level/name, centre, progression university, gender and nationality | Applicant/enrolment information; exact observation and decision dates were not established |
| Engagement | Enrolment fields plus authorised and unauthorised absence counts | After attendance information accumulates; a timestamped availability contract is needed |
| Academic progress | Earlier fields plus assessed, passed and failed module counts | After assessment; these counts may follow disengagement and partially encode the outcome |

The workflow used numeric median imputation, scaling, log transforms for skewed counts, one-hot and ordinal encoding, a stratified split, ROC-AUC model selection and thresholds targeting at least 75% recall. XGBoost was compared with baseline and tuned neural networks. SHAP described associations in the fitted tree models using a training-data sample; it supplies model interpretation, not causes of dropout or evidence that a support intervention works.

## Original evidence and limitations

The canonical 207-cell submission and its working counterpart were verified byte-identical and preserved. Inspection confirms that preprocessing returns train/validation/test arrays but callers name them train/test/validation. That positional mismatch alone does **not** establish training/holdout overlap. The concrete evaluation defect is that threshold selection uses labels subsequently reused for reporting. Model settings are selected on the other named holdout; this does not restore independent operating-point evaluation.

Stages 2 and 3 also perform full-cohort imputation before splitting, despite the later train-fitted preprocessing pipeline. Age is calculated as 2026 minus birth year, without a learner-specific observation reference date or birthday adjustment. Cross-stage learner membership cannot be freshly verified without the source inputs. The original report explicitly recognises demographic/cohort proxies and possible temporal leakage from academic progress. Subgroup calibration and error analysis were proposed, not demonstrated. Original model-performance and intervention-effect numbers are therefore not promoted here.

## Corrected executable mechanics

The new [offline synthetic example](../../examples/student_dropout/README.md) independently implements a prevalence baseline and deterministic logistic comparator, a common cohort, named learner/group-disjoint chronological splits, stage-specific feature allowlists and availability checks, train-only transforms, bounded development selection and frozen final measurement. It excludes demographic predictors and includes a reference-date age utility outside the modelling path. Tests exercise missing/unseen values, score ties, infeasible threshold policies, missing/duplicate predictions and held-out perturbations.

The [retained comparison](../../examples/student_dropout/results/scores.csv) covers all three stages and both methods on the same **64 invented evaluation learners**. It includes confusion counts, precision, recall, specificity, false alerts, workload, ROC-AUC and explicitly defined average precision. No model reaches the 75% evaluation recall target; two logistic stages exceed the development workload cap on evaluation. Those results remain unchanged after scoring. They demonstrate the evaluation mechanics and limits of transferring a development policy, not the original advanced-model results.

**Status:** original assignment completed; corrected synthetic candidate implemented for independent review. No original XGBoost, neural-network or SHAP rerun is claimed. Continued local learner-data processing permission and an approved local input cache were not established. The example documents a separately permission-gated private input route; redistribution remains unapproved. Original artifacts and saved real-study evidence remain outside the public example. No student predictions were used for decisions, and no fairness, calibrated-probability, intervention-success or deployment-readiness claim is made.

[Provenance register](../../docs/provenance.csv) · [Project index](../../docs/project-index.md) · [Portfolio](../../README.md)
