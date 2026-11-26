# QSol business solution finder

**My role:** taxonomy, curated methods, application implementation and project-fit scoring. **Status, 26 November 2026:** published classifier source plus later unpublished retrieval work. Deployment of the later work is unverified.

The application translates a business-problem description into candidate technical approaches and an implementation roadmap. It combines language-model interpretation with an explicit business-problem taxonomy and deterministic aggregation of model-supplied project-fit components. The stack includes TypeScript/Astro, the OpenAI API and Supabase.

| Version | Implemented behaviour | Evidence boundary |
| --- | --- | --- |
| Public snapshot `2a9c9dd` | Curated static prompt context, a model call, JSON parsing and weighted fit scoring | Public source inspection; no runtime document retrieval in this path |
| Later local implementation | Retrieves bounded public-playbook and internal-method context, then generates and validates structured output/citation references | Unpublished implementation and historical offline checks; not evidence that the live site uses it |

The [published classifier](https://github.com/Q-types/qsol-analytics-website/blob/2a9c9ddacb63dfe91f91f97f01c40729c224765d/src/lib/classifier.ts) is a concrete, inspectable application component. Its weighted project-fit score is a heuristic, not a calibrated probability of success or an estimate of commercial return.

The later retrieval implementation uses deterministic token, phrase, category and source scoring rather than embedding/vector search. It separates material eligible for visible citations from internal method guidance. Internal guidance is still supplied to the model provider; excluding it from client-facing citations is not a guarantee that it never leaves the server.

Existing offline evaluation covers author-curated retrieval fixtures and mocked output contracts, including deliberate negative controls. These test source selection and validation under their defined conditions. They do not establish live-model accuracy, independent holdout performance, client adoption or answer usefulness in production. No historical percentage is promoted as an end-to-end accuracy result, and those checks were not rerun for this page.

A stronger next evaluation would freeze independently authored problems, assess retrieval separately from generated answers, and review unsupported recommendations and abstention behaviour. Live latency and cost need an actual bounded measurement. The public evidence route remains the pinned classifier source and this version-specific explanation; internal notes, local fixtures and unpublished code are not copied here.

[Project index](../../docs/project-index.md) · [Provenance](../../docs/provenance.csv) · [Portfolio](../../README.md)
