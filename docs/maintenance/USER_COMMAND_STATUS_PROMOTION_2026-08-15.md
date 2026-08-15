---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260815-COWORK-003
  recorded_at_utc: 2026-08-15T00:00:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  authorization:
    requested_by: >
      member.derald, owner, in-session and explicit: "flip user to supported",
      reaffirmed as "I am the owner" after the scribe raised the declared gaps
      below. Owner ruling recorded; the scribe's reservation is recorded with it.
    scope: >
      One-line metadata change to the @dottalk.usage status field in
      src/cli/cmd_user.cpp. No logic change. No other file touched.
  report:
    path: docs/maintenance/USER_COMMAND_STATUS_PROMOTION_2026-08-15.md
    kind: audited_closeout
  primary_topics:
    - "USER command"
    - "status promotion"
    - "AIF-045 identity"
    - "declared gaps"
---

# USER command -- status promotion to `supported`

**Date:** 2026-08-15
**Owner / authority:** member.derald
**Executed by:** member.ai.claude.cowork (local access, owner-authorized)
**Risk class:** low mechanically, medium in claim surface (see section 3)

## 1. The change

`src/cli/cmd_user.cpp`, `@dottalk.usage` block:

```
- // status: experimental
+ // status: supported
```

One line. No logic touched. No other file modified in this change.

## 2. Why it was straightforward

The file contradicted itself. The `@dottalk.file` block at line 8 already read
`status: supported`; the `@dottalk.usage` block at line 14 read `experimental`.
The published command catalog harvests the usage block, so
`command-catalog.mdx:247` renders `USER | diagnostics | experimental` while the
file header claims otherwise. The promotion resolves that inconsistency in the
direction the owner chose.

`USER VERIFY` provides the APH-5 round-trip proof (save -> reload -> compare
counts/keys/decisions), and the identity catalog itself (AIF-045, nine tables) is
recorded as runtime-proven in `SYSTEM_SCHEMA_MAP_AND_NORMALIZATION_V1.md`.

## 3. What the scribe raised before executing

Recorded because the owner ruled over it knowingly, not because it was missed.

`labtalk/registries/proofs.yaml`, `proof.agency.model`, `state: source_defined`:

> Declared gaps: no per-session identity, no token expiry, git agency serialized
> by convention not mechanism (AIF-059), no durable Decision audit trail.

The same entry splits proof carefully: "Underlying leg-level behavior IS
runtime_observed (`proof.bbs.m2_net_egress` = boundary refusal; `proof.bbs.guest`
= designed minimal agency); the MODEL itself is source_defined."

The house rule is "Prove before you claim. Status is PLANNED -> PARTIAL ->
SUPPORTED only on runtime proof." Two of the four gaps -- no per-session identity,
no token expiry -- bear directly on a command whose own header declares
`mutates: identity-catalog session-auth authorization-store`.

The owner's position is that co-development authority covers this. The gaps are
declared rather than hidden, which is the material difference from an overclaim.

## 4. Consequences to expect

- **The public site has not changed yet.** `command-catalog.mdx:247` still reads
  `experimental`. It flips on the next documentation flush that reharvests source
  comment metadata. If that flush is not run, source and site disagree until it is.
- **No test breaks.** `tools/comments/tests/test_reharvest_source_comment_catalog.py`
  asserts `status == "experimental"` against `src/cli/cmd_maint.cpp`, not
  `cmd_user.cpp`. Verified before the edit.
- **AIF-112 is unblocked on this point.** COWORK-002 section 7 flagged that the
  lane would bind attribution and permission gating to an experimental surface.
  That objection is now closed by owner ruling.

## 5. Follow-on -- registry amended (done, owner-approved)

The four declared gaps in `proof.agency.model` are now carried by a `supported`
command. Three options were offered; the owner chose to amend the registry.

**Done in this changeset:** `labtalk/registries/proofs.yaml`, `proof.agency.model`,
`notes` field appended:

> 2026-08-15 owner ruling: the USER command (`src/cli/cmd_user.cpp`) was promoted
> experimental -> supported with these four gaps outstanding and declared, not
> closed. The status field and this registry entry are therefore deliberately in
> tension: USER is supported, the agency model it administers remains
> source_defined with named gaps. Recorded so the promotion is discoverable from
> the proof side rather than only from the source header.

`state:` was **not** changed and remains `source_defined`. The promotion is a
status claim about the command surface, not new proof about the model. Conflating
them would have been the actual overclaim.

YAML validated after the edit: 63 proofs parse, `proof.agency.model` intact.

**Still open, if wanted:** an identity-hardening lane to close the gaps rather than
declare them -- per-session identity, token expiry, durable Decision audit trail.
AIF-059 already covers the git-agency leg. Not opened here.

---

Owner: `member.derald`. Author: `member.ai.claude.cowork`.
Evidence class: `source-defined` (file:line verified pre- and post-edit).
Mutation: 1 file, 1 line, metadata only.
