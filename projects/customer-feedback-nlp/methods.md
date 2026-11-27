# Methods and evaluation boundaries

| Component | Original coursework role, verified in final code | New executable evidence |
| --- | --- | --- |
| BERTopic | Document topic representation using UMAP and HDBSCAN; embedding backend left to library defaults | Pending; no pretrained load or substitute |
| LDA | Gensim topic distributions and coherence diagnostics | Actual scikit-learn LDA on invented text; a separate implementation and experiment |
| BERT emotion classifier | Pretrained sequence-classification inference, not training | Pending; no inferred emotion labels invented |
| Phi-4-mini | Local causal-language-model generation with two extraction prompt structures and a separate suggestion step | Independently authored mock extractions only; no new LLM inference |

The main notebook applies a language detector with a minimum text length to one source and a supplied English-language field to the other. It selects low ratings, constructs source/location subsets and exports derived files. These are different eligibility mechanisms. No explicit duplicate-removal call or immutable upstream review-ID contract was found in the final notebook code. The extraction notebook lowercases text, removes nonletters and takes ordered prefixes; this is not a random or representative sample. Its IDs are assigned within the extraction run, and its resume logic uses review text. The report's bounded sample description therefore cannot prove which exact input rows generated every saved file.

The new [rubric](../../examples/customer_feedback_nlp/rubric.json) defines a separate experiment. Reviews have invented stable IDs and explicit source, location, language and rating fields. Language labels are authored fixture metadata, not a language-detection model. English reviews rated one or two with nonempty text are eligible. Identical repeated rows at one ID collapse; conflicting rows at an ID fail. Equal text at different IDs survives. All eligible negatives enter the issue evaluation and topic comparison. The [ledger](../../examples/customer_feedback_nlp/results/scientific/evaluation.json) retains exclusions, duplicate IDs and raw/unique/eligible denominators for every source/location group.

Semantic support, permissible reference edges, ambiguity and useful specificity are authored annotations. Exact evidence spans, review hashes and prediction hashes bind those judgments to the intended records; they cannot establish semantic support. A maximum-cardinality one-to-one matcher counts supported claims against definite reference issues, within each review. Repeated claims receive no second recall credit. A wrong category does not erase a supported issue; category correctness is measured separately. Ambiguous references and claims remain visible without definite-match credit. No-issue cases remain in the cohort even when the mock output is empty.

Every measure includes its numerator and denominator. Support, unsupported and ambiguous fractions divide by all predictions. Duplicate rate divides by supported predictions. Recall and omission rate divide by definite reference issues. Category and specificity rates divide by unique matches. The no-issue control divides clean no-issue reviews by all no-issue reviews. Empty denominators return null. Neither reference membership nor word overlap is treated as automatic semantic accuracy.

The actual LDA route fits a common count vocabulary to all eligible invented reviews, using fixed two/three-topic candidates, eight batch iterations, one thread and a fixed seed. It retains vocabulary, components, top words, document weights and in-sample perplexity for both candidates. There is no holdout, tuning, automatic winner, emotion classifier or model-generated extraction. The comparison is descriptive evidence that the bounded topic method executed, not validation of the original coursework or of semantic quality.

[Case](README.md) · [Runnable example](../../examples/customer_feedback_nlp/README.md)
