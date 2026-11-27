# QSol business solution finder

**My contribution:** problem taxonomy, curated method selection, TypeScript application integration, deterministic retrieval, structured output and reference validation, and project-fit scoring. I built the application to turn an SME’s loosely stated problem into a practical technical approach and a discovery brief: what data is needed, what to try first, and what remains uncertain.

**Evidence updated 27 November 2026:** the later local implementation’s actual offline retrieval and output-contract checks were rerun. [Measured results and failures](evidence.md) distinguish the existing curated cases from a new synthetic challenge. No live model or deployment was tested.

| Version | Behaviour | Evidence boundary |
| --- | --- | --- |
| Published `2a9c9ddacb63dfe91f91f97f01c40729c224765d` | Static prompt context, model-generated classification and weighted project-fit scoring | [Pinned public classifier](https://github.com/Q-types/qsol-analytics-website/blob/2a9c9ddacb63dfe91f91f97f01c40729c224765d/src/lib/classifier.ts); public-main identity supplied by a separate 27 November check |
| Locally committed `423399849406d1c78d68a162aadc6fd684082547` | Bounded playbook and internal-method retrieval, prompt assembly, structured generation, output and citation validation | Actual committed offline checks rerun in an isolated export; ten commits after the public snapshot; implementation remains unpublished |
| Separate uncommitted Phase 5 | Later hardening work | Preserved and excluded from this evaluation |
| Deployed website | Runtime version unverified | Neither source inspection nor offline tests establish what is deployed |

The [architecture](architecture.md) uses deterministic lexical, phrase and category scoring, rather than dense vector search. It separates citation-eligible context from internal methodological guidance. Both are sent to the model in the production code path: “internal” is a client-visibility rule, not a guarantee of secrecy or compliance. The stack is TypeScript/Astro with an OpenAI generation boundary and Supabase persistence boundary.

The existing 85 curated retrieval cases recovered all 80 expected sources. A newly authored ten-case challenge met only **4/10 frozen expectations**, exposing weak-input, out-of-domain and negation failures. The 25 mocked outputs produced the expected validation outcomes, including intentional failures. These are measurements of source selection and deterministic checks, not model accuracy or useful answers in production.

The weighted project-fit score combines model-supplied components using fixed rules. It is a heuristic, not a calibrated success probability or commercial-return estimate. [A wholly invented walkthrough](illustrative-contract.md) explains the problem → chunks → mock brief → reference-check flow without exposing original fixtures or internal notes.

[Evidence](evidence.md) · [Architecture](architecture.md) · [Project index](../../docs/project-index.md) · [Provenance](../../docs/provenance.csv) · [Portfolio](../../README.md)
