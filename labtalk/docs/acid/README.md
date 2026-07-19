# DotTalk++ ACID Education Contract

DotTalk++ treats ACID as an observable, evidence-backed engineering contract.
Transaction command names are not proof of transaction guarantees.

The glass-box educational design does not inherently weaken ACID. Visibility
and correctness are separate concerns: exposing buffers, dirty/stale state,
locks, commit boundaries, and recovery evidence helps users inspect a
guarantee, but neither proves nor disproves it.

Every finding must distinguish among:

- an intentional educational tradeoff;
- an implementation gap; and
- a verified or unverified transactional guarantee.

Every assessment must identify:

1. the property and storage/operation lane in scope;
2. the mechanism believed to support it;
3. repeatable evidence;
4. known failure cases; and
5. the work needed to improve the rating.

Allowed ratings are `Compliant`, `Partial`, `Not compliant`, `Unverified`, and
`Not applicable`. `Compliant` requires repeatable passing tests. Missing
evidence is `Unverified`, not an inferred success.

Assessments are versioned. Historical reports are retained so improvements and
regressions remain visible.

Proposed runtime surfaces are `HELP ACID`, `ACID STATUS`, `ACID EXPLAIN
<property>`, `ACID TEST`, `ACID REPORT`, and `LAB_ACID <property>`. They are a
design contract until implemented and proven in the engine repository.

See `acid_glass_box_analysis_v1.md` for the architectural analysis and
`acid_assessment_beta-1.md` for the current release-scoped evidence rating
(buffered-lane Atomicity and Durability re-rated to **Partial** after the
2026-07-19 table-buffer WAL). `acid_assessment_beta-0.md` is retained as the
historical baseline.
