# Manualgen Canonical Acceptance -- Context Decision (2026-09-02)

Decision: approved for canonical acceptance preflight.

- Owner: member.derald
- Run: DOCFLUSH-20260901-002 (v8)
- Selective merge: `MANRUN-20260902T122254Z-3CCD4585`.

## How this decision was given, stated plainly

**Authorized by member.derald in-session on 2026-09-02**, in reply to a direct
question naming this run id and asking who should write this line. The owner
chose "I write it, citing you", so this document was drafted by
`member.ai.claude.cowork` and the approval it records is the owner's verbal
instruction, not the steward's judgement.

That distinction matters because `controlled_acceptance.py` reads this file to
decide whether a plan may be built, and the string it requires PINS THE RUN ID.
The gate exists so that approval cannot be reused from a previous run or granted
in advance. Recording the provenance here keeps that property true even though
the typing was delegated.

This follows the house convention already used by every gate record in this
lane: `authorization.requested_by: maintainer (member.derald), in-session`.

**Supersedes nothing.** `MANUALGEN_CANONICAL_ACCEPTANCE_CONTEXT_DECISION_2026-07-28.md`
is left untouched. It is the authorization record for a different run
(`MANRUN-20260728T015004Z-E1204923`, DOCFLUSH-20260722-001) and overwriting it
would have destroyed a historical approval to satisfy a current check.

## Scope of this decision

This decision authorizes building the report-only controlled-acceptance plan
from the passing selective-merge candidate above, for contextual review of the
exact mutation set before any application. It is the non-mutating preflight only.

- Canonical mutation authorized: no.
- Publication authorized: no.

## Not authorized by this decision

Applying the acceptance plan, editing canonical section sources, accepting the
Partial HELP appendix, rebuilding or replacing the accepted reader, changing a
reader pointer, staging to `C:\x64base`, committing, pushing, or publishing
externally. Each of those requires a separate, explicit, durable authorization
record naming this run and the exact plan-manifest and mutation-ledger hashes.

## Basis -- measured, at this run

- The selective-merge candidate `MANRUN-20260902T122254Z-3CCD4585` passed with
  `reviewed_topics=8`, `sections=2`, `appendices=1`, `readers=1`, `diffs=3`,
  and `hash_failures=0`, `anchor_failures=0`, `extraction_failures=0`,
  `section_deletions=0`, `canonical_hash_changes=0`.
- Those counts equal the `expected_counts` table in
  `manualgen_lib/controlled_acceptance.py` exactly.
- Pointer audit `pointer_audit_v2`: `pass=21 review=1 fail=0`, the single REVIEW
  being `CONTROLLED_PUBLICATION_MATCHES_PRIMARY_READER` -- both conditions
  `validate_pointer_audit` requires.
- `base_reader_sha256` on the candidate matches the reader file on disk AND the
  pointer audit's `active_reader.sha256`
  (`EA2E12A9D3E1AD3799BFA40DBE27F1E2CB1107E34CA05684599E429D7F9A5A8F`).
- The chain is green against harvest run `HELPMETA-20260902T112853Z`, which was
  produced by the sanctioned engine-backed exporter and promoted to canonical as
  M-1 on owner GO. Canonical reads `E5 PASS 14/14, manifest_findings=0`, with
  memo TEXT resolved (`HELP_COMMANDS` USAGE and VERBOSE both 462/462).
- `manualgen validate` on the host under `.venv312`:
  `validation_fail_rows=0 validation_review_rows=0 boundary_fail_rows=0`.

## Known state NOT asserted as approved

Recorded so this document does not imply more review than actually happened:

- **No 2026-09-02 prose review decision exists.** The July chain cited
  `MANUALGEN_PROSE_REVIEW_DECISION_2026-07-28.md`. This run did not execute
  `build-prose-review-batch`, and no equivalent decision is claimed here. The
  selective merge passed on its own hash and anchor checks; that is a different
  and narrower thing than an approved prose review, and the reviewer of the
  resulting plan should read the dry-run diff rather than assume prose was
  separately signed off.
- **`build-disposition-candidate` is FAIL** at this run (`missing_policy=1`,
  `extra_policy=13`). It is not an input to this preflight -- it feeds the
  command-reference branch -- but it is open, and the single unresolvable topic
  is `DOT|TRANSACTION`, a contract-declared command with no dotref entry.
