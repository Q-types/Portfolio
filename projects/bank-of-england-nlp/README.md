# Bank of England: financial-text NLP

**I built the corpus and topic-attention analysis for the completed Cambridge / Bank of England employer project (2026).** The work connects source provenance and structural parsing to comparable bank-quarter measurements, then tests how their interpretation changes across specifications. Inspect the saved research through the pinned notebooks, or run the [independently authored synthetic measurement example](../../examples/financial_text_nlp/README.md).

## Research problem

Earnings calls contain both management’s prepared disclosures and analysts’ questions. I investigated how their thematic attention differs across banks and quarters, whether one series tends to precede another, and how the text measures relate retrospectively to financial variables. The aim was to construct auditable measurements and examine associations, rather than assume that recurring language is a validated risk signal.

## Corpus and personal contribution

I built a corpus of **60 calls from three banks across 2021Q1–2025Q4**, covering **20 quarters**, with deterministic extraction and parsing, **61 source revisions** and **34 linked tables**. The canonical corpus contains **5,342 turns, 1,900 question units and 39,738 sentence rows**. Source revisions link to calls, speakers, sections, turns, questions and exchanges; canonical IDs and text hashes distinguish a missing match from a changed text version.

The [public preprocessing notebook](https://github.com/saad-muddasser/CamDS2026_EmpProj_Team7_Submission/blob/6513a0d3047066af4d076648e2172af040dd4808/notebooks/Team7_Cam_EP_Data_Collection_Preprocessing.ipynb) records this work in sections 5, 6, 11, 12 and 14 (zero-based cells 8, 10, 20, 22 and 24). Analyst questions are structural turn proxies; a multipart question can remain one unit. Section and speaker-role rules distinguish prepared management, analyst questions, management answers and unresolved speech. Structural integrity checks establish source identity and record relationships; independent call-level semantic verification remained **0/60**, and BAC source status remained provisional.

## Measurement and method choices

I used Sentence Transformer embeddings with UMAP, HDBSCAN and BERTopic’s c-TF-IDF representations to explore analyst-question topics. Clustering supports discovery of recurring language, but naming a cluster and transferring it to prepared remarks require additional judgement. The retained themes are operational proxies with partial coverage.

| Population | Count | Meaning |
| --- | ---: | --- |
| Eligible questions fitted by the primary L25 model | 1,533 | The inherited fitting cohort; 367 other questions remain outside this fit |
| Questions in topic-share denominators | 1,900 | Includes questions outside the retained proxies |
| Questions covered by seven retained proxies | 330 | 17.37% of all 1,900 questions; partial coverage, not exhaustive topics |

The remaining denominator mass includes mixed/unresolved, conversational, noise and not-fitted questions. Fit eligibility, cluster membership and retained-theme coverage are distinct.

Question-frequency shares divide theme-question counts by **all questions in the call**. For analyst/prepared comparisons, I used non-overlapping **128-wordpiece windows**, retaining the shorter final window, in the same frozen topic space for both channels. Theme-token shares divide by **all content tokens in that channel**. Management Q&A and operator speech are excluded from prepared remarks. Comparisons match bank, call, quarter and theme; bank-quarter summaries preserve the two denominators. Quarterly trends and bank comparisons expose heterogeneity that a pooled average can hide. Same-bank lead–lag comparisons describe timing; controlled regressions, block-bootstrap intervals and sensitivity checks assess how much conclusions depend on specification and the short panel.

I also joined saved FinBERT sentiment features using identifiers and text hashes. An absent theme in a bank-quarter has no defined conditional mean sentiment; it should not silently become neutral sentiment. The label-review provenance is **human-confirmed AI-assisted review**, including my confirmation of all **40 development items** after two blinded AI reviews. It should not be described as two independent human reviewers.

## Measurement architecture

| Stage | Output and control |
| --- | --- |
| Register → extract | Versioned sources, canonical text hashes and source coordinates |
| Parse → link | Call, speaker, section, channel and question identities; unresolved cases stay auditable |
| Fit → map | Eligible analyst-question fit; retained proxies plus explicit non-retained accounting |
| Measure → align | Full question denominators; comparable token windows; same-bank/call/quarter/theme rows |
| Join → evaluate | Version-checked saved sentiment; conditional means with explicit availability; retrospective timing and financial sensitivity families |

The [synthetic example](../../examples/financial_text_nlp/README.md) makes the population, join, window and missingness controls runnable with hand-calculated tables. It does not reproduce the fitted model or original research results.

## Saved findings and evaluation

The completed topic-attention analysis shows changing thematic attention and differences between banks. Its 2025-versus-2021 annual contrasts for deposits and lending were positive across the three banks, while capital and cards were negative; those contrasts do not imply that every full-period slope was precisely estimated. Mean analyst-minus-prepared lending token gaps were **−0.56 percentage points at BAC, −1.05 at Citi and +1.33 at JPM**. This bank-level heterogeneity is lost in a single pooled description.

The timing evidence was sensitive to representation and specification. A positive lending relationship in level-based models did not remain conclusive in differenced and bank-relative interval estimates. Both investigated financial association families had intervals spanning zero. These are useful negative and qualified findings: the saved analysis does not establish a stable predictive relationship simply because one specification has a directional coefficient.

Evaluation combines source and join checks, reconstruction of saved analytical quantities, matched cohorts, uncertainty intervals and specification sensitivity. These are saved findings from the [combined topic-attention notebook](https://github.com/saad-muddasser/CamDS2026_EmpProj_Team7_Submission/blob/6513a0d3047066af4d076648e2172af040dd4808/notebooks/Team7_Cam_EP_BERTopic_Analysis_And_Topic_Attention.ipynb), not a new model fit or full analytical rerun. The runnable synthetic results establish measurement mechanics only. A three-bank, twenty-quarter panel, partial theme coverage, source/role uncertainty and transfer of the analyst topic space to prepared remarks limit generalisation. Full-period representation and incomplete historical publication-vintage information also make this a retrospective study, not a prospective financial-risk test.

## Team attribution

| Component | Contribution and boundary |
| --- | --- |
| Corpus preparation and topic-attention analysis | David McCann; the personal work described above |
| Sentiment analysis | Separate team work; my contribution here includes validated joins to saved features, not sole authorship of every sentiment component |
| Cross-bank Q&A / RAG prototype | **Dr Gulnaz Aksenova**; a separate **46-call** corpus, distinct from my 60-call corpus |

See the [team submission](https://github.com/saad-muddasser/CamDS2026_EmpProj_Team7_Submission/tree/6513a0d3047066af4d076648e2172af040dd4808), [combined topic-attention notebook](https://github.com/saad-muddasser/CamDS2026_EmpProj_Team7_Submission/blob/6513a0d3047066af4d076648e2172af040dd4808/notebooks/Team7_Cam_EP_BERTopic_Analysis_And_Topic_Attention.ipynb) and [Gulnaz’s RAG notebook](https://github.com/saad-muddasser/CamDS2026_EmpProj_Team7_Submission/blob/6513a0d3047066af4d076648e2172af040dd4808/notebooks/Team7_Cam_EP_Cross_Bank_Q%26A_Analysis_RAG.ipynb). Upload ownership does not determine component authorship.

## Inspection and reuse

All team links are pinned to submission snapshot `6513a0d`. The public topic notebook combines edited personal analysis and reuse sections; it is not byte-identical to either local final notebook. Saved outputs can be inspected, but the notebook expects separate handoff/reuse packages absent from the public tree. It is not offered here as a turnkey run.

For an offline public run, use the [synthetic fixture, tests and hashed result tables](../../examples/financial_text_nlp/README.md). It retains unmatched rows and demonstrates failure on conflicting versions, text hashes, duplicate keys and invalid cohorts.

This portfolio links to the existing team evidence without importing team code, original result assets or transcript data. Public visibility does not grant blanket redistribution rights. A personal retrieval-and-answering extension would need its own corpus version, permissions, retrieval evaluation and citation-support assessment.

[Project index](../../docs/project-index.md) · [Provenance](../../docs/provenance.csv) · [Portfolio](../../README.md)
