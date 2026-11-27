# Durable workflow example

An independently authored, standard-library illustration with entirely invented identities. It does not reproduce the private implementation. It performs no Git, provider, network or external publication action.

From the repository root, with an existing Python 3.10+ interpreter:

```sh
python3 -B -m unittest examples.engineering_workflow.test_workflow -v
python3 -B -m examples.engineering_workflow --output /tmp/invented-workflow-run-a
python3 -B -m examples.engineering_workflow --output /tmp/invented-workflow-run-b
python3 -B scripts/check_portfolio_links.py
```

Use fresh output directory names. Set `TMPDIR` to a private scratch directory if required. The runner creates a temporary SQLite database, reopens it at interruption boundaries and exports deterministic JSON. It does not export database pages, paths, timestamps or random IDs. Retained results came from two fresh byte-identical runs on CPython 3.14.0; 21 tests passed.

The [fixture](fixture.json) supplies four invented requests, including an authorized conflicting variant. The [policy](policy.json) declares exact request hashes, writer scopes, role labels and a logical approval epoch. The [implementation](workflow.py) reserves one writer per scope and binds immutable candidate, check, review, approval and intent records by hash. An exact repeat returns the existing admission; a changed request under the same key fails. Checks must bind the current candidate. A rejected or replaced candidate requires fresh verification and review; the highest proven historical effect remains recorded.

| Scenario group | Expected result |
| --- | --- |
| Unauthorized request or same key with conflicting content | Reject with no state change |
| Same request twice, including after reopening | One admission; duplicate result |
| Same declared scope held by another writer | Reject; unrelated scope can proceed |
| Pre-publication interruption | Retain writer ownership; exact owner/source recovery resumes the stage |
| Self review or candidate/evidence mismatch | Reject; no review acceptance |
| Review rejection or candidate replacement | New checks and review required; prior evidence retained |
| Missing publication permission, stale epoch or mismatched approval | Reject before intent |
| Wrong publication branch or binding | Roll back the whole attempted intent transaction |
| Restart after intent with no readback | Hold indefinitely; no repeat invocation or writer release |
| Simulated effect followed by lost acknowledgement | Reconcile the exact durable readback; one simulated effect; then release writer |

The [retained summary](results/summary.json) records 16 scenarios. It ends with one confirmed simulated publication, a newly admitted rival, and another task held with an unknown outcome. The tests add concurrent callers, malformed evidence/readback, policy drift, immutable-record checks and manifest tampering. These are illustrative local results, separate from the [actual private-source checks](../../projects/engineering-workflow/evidence.md).

Transactions use `BEGIN IMMEDIATE` on one local SQLite file, with a two-second busy timeout. A unique scope row serializes admission; each public state mutation commits or rolls back as a unit. Initialization occurs before concurrent admission tests. Scope overlap is **declared**, not inferred from filesystem paths; two aliases for overlapping work would need a shared scope. The database, Python process, policy and simulated readback store are trusted. This model is not hardened against a caller editing tables, replacing Python objects or forging every record and manifest together.

`building → candidate → verified → reviewed → unknown → published` is the successful path. Review rejection returns to building. A pre-publication hold can resume its saved stage. Highest proven effect is separately ordered as `0: admitted`, `1: verified`, `2: simulated publication confirmed`; a higher historical value does not validate a later candidate. Publication approval includes the exact review, evidence, candidate, base, branch and logical epoch. Epoch staleness is a binding check, not a wall-clock expiry or revocation service.

The invocation permit exists only in the original process after intent commits and is consumed once. A restart cannot recreate it. The simulator records readback in a separate transaction, leaving a deliberate crash gap before acknowledgement. Missing readback stays unknown even when this particular simulator did nothing. This conservative rule illustrates the real uncertainty boundary; the local stand-in is not a distributed external service and offers no production distributed exactly-once guarantee. No automatic takeover, lease timer, job runner or general orchestration product is provided.

Role strings illustrate policy comparison; they do not authenticate identities or prove reviewer independence. Likewise a passing check payload is a fixture assertion, not execution of a real project’s tests. Hashes bind exact bytes but establish neither permission nor correctness.

The [manifest](results/manifest.json) covers the exact fixture/config bytes, all six Python source files including tests, and every output payload, excluding itself. The verifier checks the file sets, hashes, retained inputs and a fresh scenario replay. Concrete runtime and test receipts are recorded separately in the private review handoff.

[Engineering case](../../projects/engineering-workflow/README.md) · [Portfolio](../../README.md)
