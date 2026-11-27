# Scoped offline evidence

Builder checks performed on 27 November 2026. Counts below describe different evidence sets and must not be added into a claim of full private-system coverage.

| Evidence set | Result | What it establishes |
| --- | --- | --- |
| Exact private committed source | Selected Git blob identities and SHA-256 file hashes verified; private export retained | Version-bound source inspection, separate from current installation |
| Existing parser tests | 16 passed | Valid envelopes and rejection of malformed or injected metadata |
| Existing isolated review-contract tests | 111 passed; two deselected | Synthetic authority/source/reviewer checks, transactional contention, durable intent and reconciliation with a recording transport |
| Independently invented public example | 21 passed | Local SQLite invariants, reopen/rollback, duplicates, competing writers, immutable evidence, review and publication bindings |
| New example replay | Two fresh runs; all four exported files identical | Deterministic invented scenario summary and manifest on the tested runtime |
| Prior portfolio regression suite | 164 passed in the scientific runtime | Retained examples’ existing assertions still pass; no original-data study was rerun |

The private tests ran unchanged from the selected commit. The review component explicitly uses a separate schema and recording transport. Two tests were omitted: one scans broader production entrypoint files, and one imports a native client solely to reject it. The production state/admission tests have a transitive runtime/controller dependency chain; native publication tests also build broad scheduler, worker and Git fixtures. They were inspected but not executed. No substitute test was counted as a pass for those paths.

Execution used existing interpreters and dependencies read-only, disabled bytecode and automatic pytest plugins, isolated HOME/TMPDIR/XDG directories, denied socket operations, confined writes to private scratch and set CPU, file, descriptor and wall-time bounds. No installation or provider call was needed. An initial pytest setup attempt was stopped by the write guard at its default logging destination; the successful invocation disabled that unused plugin. This is scoped execution evidence, not a security audit of the sandbox.

The private-source runtime was CPython 3.11.5 with pytest 8.4.2. The public example ran on CPython 3.14.0 using only the standard library. Prior scientific tests used CPython 3.11.14 with NumPy 2.3.5, SciPy 1.17.1 and scikit-learn 1.7.2. Exact executable, imported dependency hashes, command arguments, exclusions and exit records remain private. The new manifest deliberately records a portable runtime contract rather than volatile host details; the private receipt records the concrete runtime.

The [scenario summary](../../examples/engineering_workflow/results/summary.json) and [manifest](../../examples/engineering_workflow/results/manifest.json) contain only invented inputs and aggregate local outcomes. Hashes detect changes relative to the retained manifest; they do not authenticate the publisher or establish review quality. All source and tests of this example are public. Private source code, repository identity, task content, operational topology and real logs are withheld.

Historical acceptance recorded in the method is dated source evidence. This assessment makes no new source-acceptance, installation, daemon, canary, actual model-work or accepted-delivery claim. Bounded review checked the retained private test receipts and independently replayed the public example; it did not rerun the private-source tests or validate installed operation.

[Case](README.md) · [Architecture](architecture.md) · [Run the example](../../examples/engineering_workflow/README.md)
