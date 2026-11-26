# Bank of England: financial-text NLP

**Context:** completed Cambridge / Bank of England live employer project, 2026. **My contribution:** corpus engineering, preprocessing and topic-attention analysis. This page presents the completed analysis and its limits; a fully packaged public reproduction and my own complete RAG implementation remain separate future work.

## Research problem

Earnings calls contain both management’s prepared disclosures and analysts’ questions. I investigated how their thematic attention differs across banks and quarters, whether one series tends to precede another, and how the text measures relate retrospectively to financial variables. The aim was to construct auditable measurements and examine associations, rather than assume that recurring language is a validated risk signal.

## Corpus and personal contribution

I built a corpus of **60 calls from three banks across 2021Q1–2025Q4**, with deterministic extraction and parsing, source provenance and **34 linked tables** for speakers, turns, sentences and exchanges. Stable identifiers and text hashes support downstream joins and help distinguish a missing match from a changed text version.

The [public preprocessing notebook](https://github.com/saad-muddasser/CamDS2026_EmpProj_Team7_Submission/blob/6513a0d3047066af4d076648e2172af040dd4808/notebooks/Team7_Cam_EP_Data_Collection_Preprocessing.ipynb) records this work. Structural integrity checks establish relationships between records; they do not establish independent semantic verification of every call. Source-status and speaker/section proxies remain limitations.

## Measurement and method choices

I used Sentence Transformer embeddings with UMAP, HDBSCAN and BERTopic’s c-TF-IDF representations to explore analyst-question topics. Clustering supports discovery of recurring language, but naming a cluster and transferring it to prepared remarks require additional judgement. The retained themes are operational proxies with partial coverage.

| Population | Count | Meaning |
| --- | ---: | --- |
| Eligible questions fitted by the topic model | 1,533 | The model-fitting population |
| Questions in topic-share denominators | 1,900 | Includes questions outside the retained proxies |
| Questions covered by seven retained proxies | 330 | A subset, not exhaustive topic coverage |

Question-frequency shares and token-window shares answer different questions. I retained their denominators, compared matched token windows, and aligned analyst and prepared-remark observations by bank and calendar quarter. Quarterly trends and bank comparisons expose heterogeneity that a pooled average can hide. Same-bank lead–lag comparisons describe timing; controlled regressions, block-bootstrap intervals and sensitivity checks assess how much conclusions depend on specification and the short panel.

I also joined saved FinBERT sentiment features using identifiers and text hashes. An absent theme in a bank-quarter has no defined conditional mean sentiment; it should not silently become neutral sentiment. The label-review provenance is **human-confirmed AI-assisted review**, including my confirmation of development items. It should not be described as two independent human reviewers.

## Saved findings and evaluation

The completed topic-attention analysis shows changing thematic attention and differences between banks. Its annual contrasts for deposits and lending were positive across the three banks, while capital and cards were negative; those contrasts do not imply that every full-period slope was precisely estimated. Analyst/prepared lending gaps also differed by bank.

The timing evidence was sensitive to representation and specification. A positive lending relationship in level-based models did not remain conclusive in differenced and bank-relative interval estimates. The investigated financial association families had intervals spanning zero. These are useful negative and qualified findings: the saved analysis does not establish a stable predictive relationship simply because one specification has a directional coefficient.

Evaluation combines source and join checks, reconstruction of saved analytical quantities, matched cohorts, uncertainty intervals and specification sensitivity. This page reports existing evidence; no notebook was freshly executed for it. A three-bank, twenty-quarter panel, partial theme coverage, source/role uncertainty and transfer of the analyst topic space to prepared remarks limit generalisation. Full-period representation and incomplete historical publication-vintage information also make this a retrospective study, not a prospective financial-risk test.

## Team attribution

| Component | Contribution and boundary |
| --- | --- |
| Corpus preparation and topic-attention analysis | David McCann; the personal work described above |
| Sentiment analysis | Separate team work; my contribution here includes validated joins to saved features, not sole authorship of every sentiment component |
| Cross-bank Q&A / RAG prototype | **Dr Gulnaz Aksenova**; a separate **46-call** corpus, distinct from my 60-call corpus |

See the [team submission](https://github.com/saad-muddasser/CamDS2026_EmpProj_Team7_Submission/tree/6513a0d3047066af4d076648e2172af040dd4808), [combined topic-attention notebook](https://github.com/saad-muddasser/CamDS2026_EmpProj_Team7_Submission/blob/6513a0d3047066af4d076648e2172af040dd4808/notebooks/Team7_Cam_EP_BERTopic_Analysis_And_Topic_Attention.ipynb) and [Gulnaz’s RAG notebook](https://github.com/saad-muddasser/CamDS2026_EmpProj_Team7_Submission/blob/6513a0d3047066af4d076648e2172af040dd4808/notebooks/Team7_Cam_EP_Cross_Bank_Q%26A_Analysis_RAG.ipynb). Upload ownership does not determine component authorship.

## Inspection and reuse

All team links are pinned to submission snapshot `6513a0d`. The public topic notebook is an edited combination of the personal final analysis and reuse companion, not a byte-identical copy of either. Saved outputs can be inspected, but the notebook expects separate handoff/reuse packages absent from the public tree. It is not offered here as a turnkey run.

This portfolio links to the existing team evidence without importing team code or transcript data. Public visibility does not grant blanket redistribution rights. A personal retrieval-and-answering extension would need its own corpus version, permissions, retrieval evaluation and citation-support assessment.

[Project index](../../docs/project-index.md) · [Provenance](../../docs/provenance.csv) · [Portfolio](../../README.md)
