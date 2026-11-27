# Student dropout risk and intervention timing

**Status:** completed Cambridge classification assignment, report dated 14 March 2026. Public methods overview; corrected evaluation and data publication remain pending. **My role:** preprocessing, staged model comparisons, recall-oriented threshold analysis and SHAP interpretation.

The problem was when a student-support team could identify learners who might need help. Later academic information can improve a retrospective prediction while arriving too late for an early intervention. I therefore compared enrolment, engagement and academic-progress stages using a source population of **25,059 student observations**.

I built preprocessing pipelines and compared XGBoost with TensorFlow/Keras neural networks. Threshold selection emphasised recall, with the corresponding cost of false alerts and staff workload. SHAP helped describe the model’s associations with features; it does not identify causes of dropout or establish which intervention will work.

The completed report discusses demographic proxies and temporal leakage. Feature availability must be tied to the actual intervention date: an enrolment-stage model cannot legitimately use progress information observed later. A model’s discrimination also does not establish that acting on its output benefits students.

The submitted evaluation has a concrete limitation: validation/test variables are named inconsistently, and thresholds are selected on a partition subsequently used for performance reporting. The naming issue alone does not prove training/holdout overlap. Reusing labels for threshold selection does prevent treating the resulting operating-point metrics as independent final evidence. No recall, accuracy or model-superiority number is promoted here.

A public revision needs stable split identifiers, train-only learned transforms, development-only model and threshold selection, and a frozen final evaluation. Stage comparisons should use explicit cohorts and feature-time definitions. Precision, recall, confusion counts and alert workload should then be reported together, with fairness and temporal generalisation assessed separately.

The evidence route is this original methods account and the [provenance register](../../docs/provenance.csv). Submitted notebooks and report remain preserved outside the portfolio. Learner-level source access and redistribution scope are unresolved; there is no public raw-data bundle or freshly executed notebook here. The original assignment remains completed.

[Project index](../../docs/project-index.md) · [Portfolio](../../README.md)
