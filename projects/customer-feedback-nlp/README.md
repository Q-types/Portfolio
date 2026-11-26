# Customer-feedback NLP

**Status:** completed Cambridge coursework; generic methods overview. **My role:** review preparation, comparative topic modelling, pretrained emotion inference and a local language-model extraction experiment. The public route is deliberately limited to an original explanation of methods.

The analytical problem was to turn unstructured customer feedback into themes that could guide further investigation, while preserving the distinction between what customers wrote and what a model inferred. Reviews are self-selected observations: location and source comparisons can reflect who posts and what gets retained, as well as differences in service.

I compared **BERTopic and LDA** for topic analysis. BERTopic groups semantically related text using embeddings and clustering; LDA provides a different topic representation based on word distributions. Topic coherence and qualitative interpretability helped assess whether the resulting groups were useful descriptions. Neither provides a direct measure of customer satisfaction or a classification-accuracy score.

I used a **pretrained BERT emotion classifier** for emotion inference, separately from the topic models. This was inference, not BERT fine-tuning. A separate **local Phi-4-mini** experiment compared prompts for extracting issues from a bounded review sample. Its findings should not be generalised to full-corpus extraction.

The evaluation considered coherence, interpretability and unsupported generated claims. The practical lesson is to assess whether an extracted issue is supported, whether relevant issues were omitted, and whether a suggested action adds information absent from the input. A fluent recommendation is not evidence that the underlying customer statement supports it. No full-corpus accuracy, location ranking or business uplift is claimed here.

Before a reproducible public revision, the original and intermediate input versions need reconciliation, stable review IDs, exact model/prompt identities and a fixed review rubric. Original review text, quotations, derived tables, report images and named case materials are not included. Publication scope for naming and narrative is distinct from permission to redistribute data; this generic account is the available route while those details remain unresolved.

No model was run for this overview. The [provenance register](../../docs/provenance.csv) identifies this as a methods narrative without public source data or results artifacts.

[Project index](../../docs/project-index.md) · [Portfolio](../../README.md)
