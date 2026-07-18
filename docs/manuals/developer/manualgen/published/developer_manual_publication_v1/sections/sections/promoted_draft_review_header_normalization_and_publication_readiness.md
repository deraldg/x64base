# Promoted Draft Review, Header Normalization, and Publication Readiness




Pippets used:
- PIP-001 Target Selection
- MDO-196 Target Selection
- MDO-197 Draft Fill

Evidence boundary:
- Runtime proves behavior.
- Source defines implementation and subsystem ownership.
- HELP explains.
- Metadata organizes.
- CMDHELPCHK validates.
- SelfDoc preserves provenance.
- Manualgen assembles.

Slow-lane warning:
- This section touches promoted draft review, review packet practice, candidate note cleanup, reviewed candidate status cleanup, header normalization, path repair, canonical path verification, table of contents checks, section order checks, final publication boundaries, generated command page no deletion, and no mutation safety.
- Do not send this directly to generic PIP-003.
- Run a slow-lane promoted-draft readiness review first.

Evidence tokens under review:
- promoted draft
- review packet
- inspection packet
- human review
- candidate note
- reviewed candidate status
- header normalization
- publication readiness
- final publication
- table of contents
- section order
- section count
- path repair
- canonical path
- slug
- generated command pages
- no deletion
- HELP
- CMDHELPCHK
- metadata
- SelfDoc
- manualgen
- PIP
- report-only
- no mutation

Draft notes:
- This is conservative manual prose for slow-lane evidence review.
- Promoted draft workspace assembly is not final publication.
- Candidate note headers in promoted draft sections must not be normalized casually one section at a time.
- Reviewed candidate status blocks in promoted draft sections must be handled by a systematic promoted-draft header normalization pass.
- Header normalization must not rewrite substantive prose without explicit review.
- Path and slug verification must use canonical section ids and inspectable files.
- Table of contents and section order must be verified against actual section files.
- Review packets should remain the preferred human-inspection surface before authorization.
- Generated command pages and evidence artifacts must not be deleted during publication-readiness work.
- Publication readiness may recommend repairs, but it should not silently publish or normalize.

## Purpose of this section

This section explains how the Developer Manual should review a promoted draft workspace, prepare for header normalization, and separate publication readiness from final publication.

It follows the Command Reference Assembly section because that section exposed a concrete promoted-section path problem. MDO-194 reported a successful promotion, but MDO-194A was needed to repair and verify the canonical promoted section path. That experience proves that status reports are not enough. A promoted draft must be inspectable, path-checked, section-counted, and reviewed as a workspace.

The goal is not to publish the manual. The goal is to define a safe review lane between promoted draft assembly and any later final publication step.

## Promoted draft workspace

A promoted draft workspace is an assembled manual draft.

It may contain:
- reviewed candidate prose copied into section files;
- candidate note headers;
- reviewed candidate status blocks;
- promoted section paths;
- generated section ordering;
- table of contents material or future table of contents inputs;
- evidence of promotion history;
- known draft-workspace debt.

Safe wording:
- A promoted draft is not final publication.
- A promoted draft is a reviewable workspace.
- A promoted draft can contain review artifacts that are useful during assembly but inappropriate for final publication.
- Final publication should require a later explicit gate.

## Inspectable files

The user should be able to inspect the actual prose.

Inspectable files matter because status reports can be green while path or filename issues remain. MDO-194A showed why the canonical path must be checked directly.

Safe wording:
- Review must include actual section files, not only status CSVs.
- Canonical paths should be opened or tested directly.
- A readable section file is stronger evidence than a report that only says a section exists.
- Review packets should make prose easy to inspect before authorization.

## Review packets and inspection packets

Review packets are human-inspection surfaces.

They should provide:
- the prose to read;
- a checklist;
- known canaries;
- a summary;
- a hold, repair, or accept decision point.

Safe wording:
- Review packets should remain the preferred human-inspection surface before authorization.
- Review packets should not create human decisions by themselves.
- Review packets should not promote.
- Review packets should help the reviewer decide HOLD, REPAIR, or ACCEPT_FOR_PROMOTION.

## Candidate note headers

Candidate note headers are useful during review.

They preserve:
- origin of the candidate;
- promotion-gate provenance;
- review warning;
- draft status.

But candidate note headers can become clutter in a final manual.

Safe wording:
- Candidate note headers in promoted draft sections must not be normalized casually one section at a time.
- Candidate note headers should be handled by a systematic promoted-draft header normalization pass.
- Candidate note headers should not be removed until the manual has a defined normalization rule.
- Header normalization should preserve provenance in reports even if public-facing prose is cleaned later.

## Reviewed candidate status blocks

Reviewed candidate status blocks are also useful during review.

They say that a section passed a reviewed-candidate lane, but they are not necessarily final publication text.

Safe wording:
- Reviewed status blocks should not be removed casually one section at a time.
- Reviewed status blocks should be recorded in normalization reports if removed from public-facing prose.
- A section can be accepted for promoted draft assembly without being final-publication-ready.

## Header normalization

Header normalization is the process of turning review-oriented section headers into final-manual section headers.

Header normalization may include:
- removing Candidate note blocks from public-facing copies;
- preserving provenance in reports;
- standardizing title and section metadata;
- checking section order and table of contents alignment.

Safe wording:
- Header normalization must not rewrite substantive prose without explicit review.
- Header normalization must be systematic.
- Header normalization should report every section changed.
- Header normalization should preserve originals or backups.
- Header normalization is not final publication by itself.

## Substantive prose boundary

Header normalization should not become stealth editing.

Substantive prose includes:
- conceptual explanations;
- evidence doctrine;
- command behavior claims;
- canary language;
- examples;
- scope boundaries;
- future metadata feeder descriptions.

Safe wording:
- Header normalization may clean review headers.
- Header normalization should not change substantive prose without explicit authorization.
- Substantive repairs should go through a repair/review path, not a normalization pass.
- If a header-normalization script changes body prose, that is a failure unless explicitly authorized.

## Path repair and canonical path verification

Promoted drafts should verify canonical paths.

Path repair and canonical path verification should check:
- section id;
- expected filename;
- actual file existence;
- readable content;
- hash match with source candidate where expected;
- legacy or non-canonical path leftovers;
- duplicate section files.

Safe wording:
- Path and slug verification must use canonical section ids and inspectable files.
- A status report is not enough if the file cannot be opened.
- Path repair should preserve evidence and avoid deletion unless separately authorized.
- Canonical path verification should be part of publication-readiness review.

## Slugs and section ids

A slug or filename is not just formatting. It controls whether humans and scripts can find the section.

Safe wording:
- Slugs should be derived from reviewed section ids.
- Slug changes should be reported.
- Non-canonical slugs should be flagged before publication.
- Slug repair should preserve old evidence until cleanup is explicitly authorized.

## Section count

Section count is a basic workspace integrity check.

A promoted draft review should report:
- total section files;
- expected required sections;
- missing required sections;
- extra or duplicate sections;
- sections with candidate headers;
- sections with reviewed-status blocks;
- sections needing header normalization.

Safe wording:
- Section count is a workspace health check.
- Section count does not prove prose quality.
- Section count should be combined with inspectable file checks.

## Section order

Section order matters because the manual should read coherently.

A section-order review should check:
- onboarding and orientation before deep internals;
- data model before navigation;
- navigation before indexing;
- indexing before expressions where appropriate;
- command surface before command reference;
- evidence doctrine before publication readiness;
- appendices or reference sections after concepts.

Safe wording:
- Section order should be explicit.
- Section order should be reviewable.
- Section order should not be inferred only from directory listing order.
- A future table of contents or manifest should own final order.

## Table of contents

A table of contents is the public navigation surface for the manual.

Publication readiness should eventually verify:
- every TOC entry has a section file;
- every required section file appears in the TOC or is intentionally excluded;
- titles match;
- order is intentional;
- section ids and slugs are stable;
- no draft-only sections appear accidentally;
- no evidence-only reports appear as public manual chapters.

Safe wording:
- Table of contents checks belong to publication readiness.
- TOC readiness is not the same as final publication.
- TOC generation should not delete source sections.
- TOC generation should preserve auditability.

## Final publication boundary

Final publication is separate from promoted draft workspace assembly.

Safe wording:
- Final publication requires explicit authorization.
- Promotion into a draft workspace is not final publication.
- Header normalization is not final publication.
- TOC readiness is not final publication.
- Publication readiness may recommend repairs, but it should not silently publish or normalize.

## Generated command pages and evidence artifacts

Generated command pages and evidence artifacts remain protected.

Publication-readiness work must not delete:
- generated command pages;
- HELP evidence;
- metadata reports;
- CMDHELPCHK reports;
- review packets;
- PIP reports;
- source evidence reports;
- canary reports;
- promoted draft history.

Safe wording:
- Generated command pages and evidence artifacts must not be deleted during publication-readiness work.
- Cleanup recommendations may be reported.
- Deletion or mutation requires a separate explicit authorization path.

## HELP, CMDHELPCHK, and metadata boundaries

Publication-readiness review may read HELP, CMDHELPCHK, and metadata evidence.

It must not mutate:
- HELP;
- META;
- CMDHELPCHK;
- catalogs;
- source;
- runtime data;
- production SelfDoc metadata.

Safe wording:
- HELP explains.
- CMDHELPCHK validates.
- Metadata organizes.
- Manualgen publication-readiness review remains report-only.
- No mutation occurs without explicit authorization.

## Report-only publication readiness

Publication readiness should start as report-only.

Report-only readiness can produce:
- section inventory;
- candidate header inventory;
- reviewed status inventory;
- canonical path check;
- slug check;
- table of contents check;
- section order check;
- review packet inventory;
- unresolved canary inventory;
- publication blocker list;
- recommended repairs.

Safe wording:
- Report-only readiness is safe by default.
- Report-only readiness can recommend repair.
- Report-only readiness must not silently normalize, publish, or delete evidence.

## Human review

Human review remains the decision point.

Human review should decide:
- HOLD;
- REPAIR;
- ACCEPT_FOR_PROMOTION;
- READY_FOR_HEADER_NORMALIZATION;
- READY_FOR_PUBLICATION_REVIEW;
- NOT_READY_FOR_PUBLICATION.

Safe wording:
- Human review should inspect prose, not only reports.
- Human review should be recorded.
- Authorization should follow inspection.
- Publication should not be implied by prior section acceptance.

## Slow-lane canary tracking names

The slow-lane review tracks these canaries by exact name. These names are review anchors, not final user-facing prose.

- candidate note headers not normalized one section at a time
- reviewed candidate status blocks systematic normalization
- header normalization no substantive prose rewrite
- final publication separate from promoted draft assembly
- canonical path slug verification inspectable files
- table of contents section order actual files
- review packets preferred human inspection before authorization
- generated command pages evidence artifacts no deletion
- help meta cmdhelpchk source runtime selfdoc no mutation
- publication readiness recommends not silently publishes

These anchors preserve the canaries that the prose discusses in ordinary language. They should remain until the section is promoted through evidence review.

## Review notes before PIP-003

This is a slow-lane section. Before generic PIP-003 is allowed to create a reviewed-candidate path, an MDO slow-lane evidence review should check:

- all required tokens are represented or intentionally excluded;
- promoted draft workspace review is distinct from final publication;
- candidate note headers are not normalized casually one section at a time;
- reviewed candidate status blocks are handled systematically;
- header normalization does not rewrite substantive prose;
- canonical path and slug verification use inspectable files;
- section count, section order, and table of contents checks are represented;
- review packets are preserved as human-inspection surfaces;
- generated command pages and evidence artifacts are protected from deletion;
- HELP, META, CMDHELPCHK, source, runtime data, and production SelfDoc metadata are not mutated;
- publication readiness may recommend repairs but does not silently publish or normalize.

Recommended required tokens for later PIP-003:
- promoted draft
- review packet
- inspection packet
- human review
- candidate note
- reviewed candidate status
- header normalization
- publication readiness
- final publication
- table of contents
- section order
- section count
- path repair
- canonical path
- slug
- generated command pages
- no deletion
- HELP
- CMDHELPCHK
- metadata
- SelfDoc
- manualgen
- PIP
- report-only
- no mutation

## Boundary

- prose draft fill only
- slow-lane review still required
- no reviewed candidate generated
- no final prose promotion
- no final publication
- no header normalization
- no generated command page deletion
- no HELP mutation
- no META mutation
- no CMDHELPCHK mutation
- no catalog apply
- no source edits
- no production SelfDoc metadata promotion

