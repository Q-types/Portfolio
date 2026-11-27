# Wholly invented contract illustration

This is a hand-authored explanation, **not an original QSol fixture, actual retrieval result, executed test or generated model answer**. The chunk text and labels below were created solely for this page. It illustrates the separation of retrieval, a structured brief and reference validation.

**Invented problem:** “Our volunteer repair café keeps appointment counts in three files. We want one weekly view, but each volunteer spells service names differently.”

**Illustrative selected chunks:**

| Invented label | Invented text | Citation eligibility |
| --- | --- | --- |
| `DEMO-A / counts` | Agree a shared service-name list before combining appointment totals. | Visible |
| `DEMO-B / checks` | Compare each imported total with its source file before publishing the weekly view. | Visible |
| `DEMO-M / caution` | Ask who owns corrections and how missing records will be reviewed. | Internal guidance only |

**Mock brief:** “Start with a small reporting workflow. First agree service names and reconcile one week’s counts. Assume the files contain one row per appointment; check for duplicates and missing sessions. A language model is not needed for adding the counts. Discuss who approves corrections. Proposed citations: `DEMO-A / counts`, `DEMO-B / checks`.”

**Illustrative reference check:** both proposed references belong to the selected visible set, so they satisfy the membership rule. Adding `DEMO-Z / promises` would fail because it was never retrieved. Adding `DEMO-M / caution` would fail the visibility rule. A structured-output check would separately require the brief’s expected fields and valid enums.

Passing those checks would not prove that the advice is correct, complete or supported sentence by sentence. In the real production path, even guidance excluded from visible citations is sent to the provider. The [actual offline measurements](evidence.md) use the frozen QSol implementation and existing evaluators, separate from this illustration.

[Case](README.md) · [Architecture](architecture.md)
