# Executed offline evidence

On **27 November 2026**, the committed evaluation scripts and all eight test entry files from local website commit **`423399849406d1c78d68a162aadc6fd684082547`** ran successfully in a private, exact-byte export. The original dirty checkout was preserved. Source, fixture, dependency and command receipts and per-case results remain private; only aggregates are reproduced here. The retained measurements received bounded review, including an independent restricted aggregate/challenge replay. This does not establish deployed operation or live-answer quality.

## Execution qualification

The selected package declares Node `>=20.x`, but its `.nvmrc` pins `20`; that runtime pin was not reproduced. Execution used **Node 25.4.0**, Zod **3.25.76** and OpenAI SDK **4.104.0** (imported by prompt tests, with no client call). Installed versions matched 484 selected lock entries; 97 optional entries were absent, 96 with platform selectors. There were no installed-lock extras. The selected Astro dependency declares Node `>=22.12.0`, which also conflicts with the committed Node 20 pin; Astro was not executed. This was existing local dependency reuse, not a fresh lockfile installation or integrity revalidation against package archives.

The additional macOS sandbox wrapper failed before execution with `sandbox_apply: Operation not permitted`. The successful route used Node’s permission system inside the existing workspace sandbox: network, child processes, workers and filesystem writes denied; reads limited to the export, installed dependencies and small private harness files. Denial probes passed. A minimal environment contained no provider/database credentials, and no `.env` was loaded. No server, installation, provider, database or email operation ran.

The committed commands select `tsx` 4.22.4. To avoid granting its subprocess requirements, the same unmodified TypeScript entry files ran through Node’s native type stripping and a small extensionless-import resolver. **This is a qualified reproduction of the actual code and fixtures, not an exact `npm test`/tsx reproduction.** The eight entries cover retrieval, phase-two contracts/rendering, phase-three grounding, golden and realistic-language retrieval quality, internal-source policy, combined source separation, and output quality/prompt assembly. Each exited 0. Golden, realistic-language, combined and mocked-output evaluation scripts also each exited 0. Script runtime is recorded privately as test execution time, not product latency.

## Existing retrieval fixtures

The committed fixtures contain 45 author-curated golden cases and 40 realistic-language cases. The latter are explicitly tagged **25 synthetic realistic examples and 15 manual paraphrases**; none is tagged as an anonymised note in this selected fixture set. They are not live traffic or an independent holdout. Combined evaluation reuses those same 85 cases.

| Measure | Golden (45 cases) | Realistic language (40) | Combined (85) |
| --- | ---: | ---: | ---: |
| Expected-source recall | 42/42 | 38/38 | 80/80 |
| Cases hitting an expected primary source | 42/42 | 38/38 | 80/80 |
| Cases returning a fixture-forbidden source | 0/45 | 0/40 | 0/85 |
| Retrieval fallback | 3/45 | 2/40 | 5/85 (5.9%) |
| Cases with internal context | 42/45 | 38/40 | 80/85 (94.1%) |

Expected-source recall counts retrieved expected primary sources divided by all expected primary sources. Case hit rate counts cases with at least one expected primary hit, among cases declaring a primary source. These denominators happen to coincide because each of the 80 non-fallback cases expects one primary source. Forbidden-source rate counts cases returning a specifically forbidden source, not all irrelevant-source precision. These are **not answer/model accuracy**.

All five observed fallbacks matched the fixture expectations. Empty retrieval was 0/85: fallback can still carry generic guidance while suppressing visible citations. All 85 repeated retrieval comparisons were deterministic. No unknown source/chunk or visibility violations were observed under the evaluator’s checks. Maximum formatted public-context length was 2,391 characters. These figures do not measure total prompt size or semantic grounding. The evaluator’s grouped coverage helper automatically credits expected-fallback cases; the separately computed zero fallback mismatches is the relevant check of their actual fallback behaviour.

## Mocked output contracts

The existing 25 mocked outputs comprise **12 positive cases and 13 deliberate negatives**. All expected outcomes matched; 13 cases were marked for review. Schema passed on 22/25, public/internal reference validation on 22/25, and the heuristic “discovery-call usefulness” check on 22/25. Those are separate, overlapping dimensions, not 22 wholly successful answers or 88% model quality.

The controls exercised unknown source/chunk references, internal-source disclosure, unsupported endorsement and return-on-investment language, missing assumptions/risks, malformed enums, unnecessary advanced AI recommendations, unsafe HTML-like text and generic prose. Aggregate flags included two leakage cases, two overclaim cases, two advanced-AI-overrecommendation cases, one unsafe-HTML case and one generic-output warning. Failures were intentional and successfully detected against fixture expectations.

“Usefulness” checks field presence, rationale length and fixed language patterns. It is not a human judgement of recommendation quality. Reference validity is not entailment. Prompt tests check assembled text; they do not establish that a model follows it. No real model output was generated or scored.

## New frozen retrieval challenge

A separate **ten-case, agent-authored synthetic challenge** was frozen and hashed before calling the actual retrieval API. It was written after API/category inspection, without adapting cases or code to outcomes. It is neither externally independent nor a statistically representative holdout. Details remain private because expectations refer to internal registry identifiers.

| Frozen expectation | Passed / cases | Observed limitation |
| --- | ---: | --- |
| Abstain on ambiguous, weak, no-match or out-of-domain input: fallback true and no visible sources | 1/6 | Five received visible sources, including an irrelevant request with overlapping domain words |
| Recover both required sources for competing needs, without fallback | 2/2 | Both required sources recovered in these two cases |
| Recover the requested source and exclude an explicitly negated category | 0/1 | The negated category was still retrieved |
| Recover the required source for a routine in-domain request | 1/1 | Required source recovered; this criterion did not require exclusive retrieval |
| **All frozen expectations** | **4/10** | **Six failures retained; no tuning or selection after execution** |

This challenges abstention and lexical ambiguity directly. It explains why perfect recall on the existing curated fixtures is insufficient evidence of generalisation. The next useful work is broader, independently authored retrieval assessment and separately authorised human-reviewed live generation; no claim about live usefulness, commercial conversion, cost, latency or deployed production follows from this run.

[Case](README.md) · [Architecture](architecture.md) · [Wholly invented illustration](illustrative-contract.md)
