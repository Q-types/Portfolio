# Customer segmentation

**Status:** completed Cambridge assignment; corrected pipeline implemented and tested on invented data. Original-data revalidation remains blocked by input availability and continuing local-processing permission. **My role:** data cleaning, customer features, clustering, evaluation, visualisation and interpretation.

This case shows why feature definitions matter as much as clustering algorithms. The original study explored approximately 68,300 customers and more than 951,000 transaction lines. Reviewing the saved workflow exposed two consequential errors: accounting losses lost their minus signs, and transaction-line counts were described as purchase frequency. Historical summed profit was also labelled lifetime value, while purchased-item cost mix was interpreted as price sensitivity.

The [corrected runnable revision](../../examples/customer_segmentation/README.md) implements strict Decimal parsing, distinct-order counts, explicit customer/order/line identities, duplicate conflict checks and revenue–cost–profit reconciliation. Signed transforms and standardization learn only from declared fit customers. Fixed k=2/3 comparisons, cluster profiles and seed/resample sensitivity share one retained run, evaluated on common held-out customer IDs. It runs offline with the Python standard library.

On the invented fixture, k=2 has held-out silhouette **0.368**, compared with **0.244** for k=3. Three clusters produce a singleton held-out group and weaker resample agreement (ARI **0.812–0.873**). These are small synthetic mechanics results, not findings about the original customers. Neither stability nor separation establishes business usefulness, campaign lift or price response.

The [source evidence note](../../examples/customer_segmentation/source_notes.md) records exact notebook/report hashes and cell references. The original row-count discrepancy remains unresolved, with inconsistent saved shape/column evidence also retained. The original schema lacks a separate line identity, so its full-row duplicate removal cannot be silently reused as an authoritative transaction rule.

No original-data rerun was performed. Bounded local inspection found no matching original input or express permission for continuing local processing. Redistribution permission is separate and also unestablished. The [private input route](../../examples/customer_segmentation/private_input.md) requires established permission bound to exact consumed bytes, reviewed schema/identity mapping and private locations.

The [historical folder](../../MachineLearning_AI/Customer_Segmentation_Clustering/README.md) preserves the original notebook and report unchanged. Its profiles belong to the uncorrected workflow. The original choice of three clusters was interpretive despite stronger silhouette for two; a ten-customer Ward illustration cannot validate population structure. The completed assignment remains completed, and a corrected real-data analysis remains outstanding.

[Project index](../../docs/project-index.md) · [Provenance](../../docs/provenance.csv) · [Portfolio](../../README.md)
