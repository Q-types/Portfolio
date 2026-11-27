# Agent-assisted engineering workflow

**My role:** design and implementation of reusable components for task coordination, verification, review and recovery. **Status, 26 November 2026:** private source implementation described through a sanitised architecture overview. Source acceptance, installed operation, model execution and accepted project outcomes are separate milestones.

Data-science delivery involves more than a model fit: implementation changes need source isolation, evidence of what ran, review and a recoverable response to failure. I developed components using isolated Git worktrees, durable SQLite state, configured verification steps and explicit review/correction boundaries.

The workflow records authorised task scope and source identity, controls competing writers, and retains evidence of implementation and checks. Publication checks bind a proposed output to its intended branch and commit. Independent review remains a distinct decision; an implementation completion message cannot approve its own result.

An **illustrative scenario, not an executed test**: an implementation finishes and its bounded checks pass, but the process disconnects before the next action is known to have completed. Recovery should inspect durable evidence and retain the highest proven result. It should not blindly rerun a possibly completed external action or relabel the candidate independently accepted. This explains why source validation, publication and review need separate records.

The inspected source includes tests for state/admission and source-publication behaviour. The broader workflow can coordinate unit, integration and browser checks where appropriate. Test definitions and historical receipts demonstrate specific engineering mechanisms; they do not prove that every new project has passed them or that an installed service is currently running. No daemon, live state database or provider session was used to prepare this case.

The useful contribution is explicit source ownership and recoverable evidence around agent-assisted work. Autonomous reliability, delivery-speed gains and production adoption remain unmeasured here. Private task text, operational topology, provider transcripts and repository identities are excluded. This narrative and the [provenance register](../../docs/provenance.csv) are the public evidence route; an independently synthetic offline demonstration would be a separate extension.

[Project index](../../docs/project-index.md) · [Portfolio](../../README.md)
