# DotTalk++ Portal Feed Contract V1

Status: accepted for implementation under AIF-132.

Owner: `member.derald`

Steward: `member.ai.codex`

Schema: `dottalk.portal.feed.v1`

## Purpose

The AI Portal is a router and evidence index. It does not become a second HELP
store, metadata catalog, manual database, or publication authority.

This contract defines the typed seam between DotTalk++ documentation/data
producers and Portal consumers. A feed record says where authority lives, how a
projection is produced, what artifacts it emits, how it is retained, who reads
it, and what evidence supports its present state.

## Process vocabulary

The canonical process states are names, not phase numbers:

| Canonical name | Meaning | Legacy aliases |
| --- | --- | --- |
| `development_closeout` | The development-tree run is closed and reviewed against its entry gate. | `Gate 7`, `Phase 7` in the full-stack recipe book |
| `publication_ascent` | A separately authorized promotion and publication process. | `Phase 8` in the recipe book; `Phase 7 web ascent` in an older runbook |

Historical documents keep their original numbering. New records use the
canonical name and may carry the historical label in `legacy_labels`. Gate 7
completion never implies promotion, deployment, or public availability.

## Registry authority

The registry is `labtalk/registries/portal_feeds.yaml`. Its root `schema` value
must be exactly `dottalk.portal.feed.v1`. Feed identifiers are durable and must
not be recycled.

Two companion registries keep perishable state and truth claims out of prose:

- `labtalk/registries/current_fullstack_doc_push.yaml` is the maintained pointer
  to the current documentation run and its publication boundary.
- `labtalk/registries/portal_assertions.yaml` carries typed claims with explicit
  validity, platform, evidence, expiry, and a structured check.

The assertion validator evaluates YAML values and collections. It does not use
phrase matching to decide whether prose is true. Evidence anchors must exist
exactly once, preventing a missing heading from silently widening a check to a
whole file.

Every feed contains:

- `feed_id` -- unique durable identifier.
- `subject_class` -- the kind of truth being routed.
- `status` -- `active`, `degraded`, `planned`, or `retired`.
- `phase.canonical` -- a stable process name.
- `source_authorities` -- paths the producer reads or the record treats as
  authoritative.
- `producer` -- the tool, runtime, or governed manual action that emits the
  feed.
- `outputs` -- materialized artifacts. Outputs remain owned by their source
  lane; registration does not transfer ownership to the Portal.
- `evidence` -- `planned`, `source-evidenced`, or `runtime-proven`, plus proof
  artifacts where required.
- `sensitivity` -- `public`, `internal`, or `restricted`.
- `derived_from` -- feed-to-feed lineage edges.
- `consumers` -- named readers and their visibility.
- `freshness` -- the event that makes the record require revalidation.

`source_commit`, `generated_at_utc`, and `sha256` are permitted measurements.
They must be generated or re-measured; they are not hand-kept status prose.

## Artifact retention

Each source, output, proof, producer, and consumer path declares one retention
class:

| Retention | Contract |
| --- | --- |
| `tracked` | The path exists inside the repository and is tracked by Git. |
| `transient` | The path may be ignored or untracked. An output must carry a SHA-256 value and a tracked proof must bind that value. |
| `external` | The artifact is outside this repository. The record must use a URI and must not claim repository-path validation. |

A tracked document that cites an untracked output without a bound hash is a
widow. Marking it `transient` without the hash and proof is not a waiver.

## Evidence states

- `planned` means the seam is designed but its producer/output relationship has
  not been observed.
- `source-evidenced` means the named source and producer paths exist and their
  relationship is inspectable from source or a governed record.
- `runtime-proven` means the producer ran and at least one retained proof binds
  the result. Runtime proof is platform-qualified.

The Portal reports evidence state; it does not promote a state. A validator may
find that a claimed state is unsupported and report it as advisory drift.

## Visibility rule

Sensitivity flows toward equal or more restricted consumers only:

`public -> internal -> restricted`

An internal or restricted feed cannot name a public consumer unless a separate
public projection feed performs the redaction and declares the private feed in
`derived_from`.

## Freshness policies

- `validate_on_change` -- revalidate when an authority, producer, or output
  changes.
- `run_scoped` -- revalidate when the named run closes or is superseded.
- `manual_review` -- a human ruling determines currency.
- `immutable` -- content-addressed evidence that is never rewritten.

Freshness failure is `ATTESTATION_STALE`, not proof that the underlying source
is defective. The owner lane decides whether to re-pin, regenerate, supersede,
or investigate.

## Validation and hardening

`labtalk/ai_portal/validate_portal_feeds.py` starts report-only. Exit code `0`
means no findings, `3` means advisory findings, and `1` means the registry could
not be parsed or evaluated. It checks schema shape, identifier uniqueness,
paths, retention, hashes, lineage, evidence support, and visibility.

The validator may become a hard gate only after:

1. known-bad fixtures prove each hardening arm goes red;
2. a real advisory cycle demonstrates acceptable noise;
3. the gate registry names its scope, severity, and owner; and
4. the owner explicitly promotes it.

## Ownership boundary

- Full-stack documentation owns content harvesting, comparison, manual
  generation, rehearsal, and run closeout.
- AI Portal owns feed registration, routing, lineage, freshness, evidence state,
  and visibility reporting.
- Publication owns promotion, public projection, deployment, and public
  verification.

The Portal consumes documentation proofs. It does not reimplement the
documentation lane's comparison or rehearsal machinery.
