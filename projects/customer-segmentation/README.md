# Customer segmentation

**Status:** completed Cambridge assignment with existing public notebook/report; feature corrections and public revalidation pending. **My role:** data cleaning, customer aggregation, clustering, visualisation and business interpretation.

The study explored purchasing behaviour across **68,300 customers and more than 951,000 transaction lines**. I used engineered purchasing features, K-means, illustrative Ward linkage, elbow/silhouette diagnostics and PCA, t-SNE and UMAP views. The purpose was to describe customer groups and propose targeting hypotheses, not to claim a measured campaign effect.

Feature definitions determine what those groups mean. Observed-period summed profit is historical profit, not predicted future customer lifetime value. Mean purchased-item unit cost describes product cost mix, not measured price sensitivity. The current notebook’s frequency feature counts transaction lines; distinct purchase frequency would require counting unique order identifiers.

The [existing notebook](../../MachineLearning_AI/Customer_Segmentation_Clustering/McCann_David_CAM_C101_Week_6_Mini_project.ipynb) also removes accounting parentheses without restoring negative signs. Correcting this changes monetary inputs and may require a different transformation for negative totals. The public notebook and final report differ by one raw row; the rounded scale above avoids silently choosing one exact count.

The saved analysis chose three clusters for interpretability although two had the stronger silhouette. Ward linkage used only a ten-customer illustration, which cannot validate population structure. Embedding separation and in-sample silhouette do not establish stability or business value. Existing cluster profiles must therefore be read as results of the original, uncorrected workflow; they have not been repaired or rerun by adding this page.

A corrected public revision needs monetary reconciliation, explicit line/order definitions, valid signed transformations and seed/resample stability checks before new profiles are promoted. Campaign actions remain proposals until tested.

The [historical project folder](../../MachineLearning_AI/Customer_Segmentation_Clustering/README.md) retains the original public report and notebook. Use them as inspectable historical evidence at Portfolio snapshot `f4255f9`; this overview qualifies their feature and evaluation claims. Source-data redistribution rights are not inferred from public hosting, and no dataset is added here.

[Project index](../../docs/project-index.md) · [Provenance](../../docs/provenance.csv) · [Portfolio](../../README.md)
