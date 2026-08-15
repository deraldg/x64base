---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260815-COWORK-005
  recorded_at_utc: 2026-08-15T00:00:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local
  git:
    branch: development
    baseline_commit: 5e4c86b84
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  authorization:
    requested_by: maintainer (member.derald), in-session, "do it"
    scope: >
      Lane charter only. Measured against src/cli/cmd_set*.cpp and the live
      runtime on 2026-08-15. No source mutation, no website mutation. AIF-114
      claimed host-side by the owner via session_coordinator.py claim-aif; not
      self-assigned.
  lane: AIF-114
  report:
    path: docs/maintenance/SET_FAMILY_PUBLISHED_WITHOUT_IMPLEMENTATION_LANE_V1.md
    kind: lane_charter
  primary_topics:
    - "SET family"
    - "documentation drift"
    - "public site accuracy"
    - "prove before you claim"
---

# Seven Published SET Options With No Implementation (Lane V1)

**Status:** not started -- charter only. **Lane:** AIF-114
(claimed 2026-08-15, run COWORK-20260815-001, lane `set-family-doc-drift`).
**Owning project:** PDLC (website) with a DotTalk++ SDLC dependency.
**Evidence class:** `runtime-observed` + `source-defined` (both legs measured 2026-08-15).
**Found during:** AIF-112 Phase-1 Step 0, incidentally. Not part of that lane.

## The problem, measured

`x64base-site/content/docs/dottalk/set-family.mdx` publishes a code block under
the heading **"Data and editing behavior -- Current documented surfaces
include:"**. It lists eleven settings, with no status qualifier of any kind.

Measured against `src/cli/cmd_set*.cpp`:

| Setting | In source |
|---|---|
| `SET TABLE BUFFER` | present |
| `SET DELETED` | present |
| `SET CASE` | present |
| `SET NEAR` | present |
| `SET SAFETY` | **ABSENT** |
| `SET EXACT` | **ABSENT** |
| `SET ESCAPE` | **ABSENT** |
| `SET CARRY` | **ABSENT** |
| `SET CONFIRM` | **ABSENT** |
| `SET EXCLUSIVE` | **ABSENT** |
| `SET MULTILOCKS` | **ABSENT** |

Seven of eleven. Confirmed on the runtime independently: `SET EXCLUSIVE` and
`SET MULTILOCKS` both fall through to the generic `SET` usage listing, and
neither appears in its public options or its developer/transitional options.

This is live on x64base.com.

## Why it matters more than a typo

The house rule is stated in the working agreement and repeated in the seed:
**"Prove before you claim. Status is PLANNED -> PARTIAL -> SUPPORTED only on
runtime proof. Runtime proves, source defines, HELP explains."** A page that
lists seven non-existent settings as "current documented surfaces" is the
cleanest possible violation of it, on the public surface, in a doc a reader has
no reason to distrust.

It is also the pattern `BBS_SESSION_EXCHANGE_GUARD_LANE_V1.md` already names as
cautionary precedent -- **VDISK CEIL**, "a runaway RAM cap whose config surface
exists but whose enforcement is ABSENT ... do NOT ship the cap as config without
the enforcement path proven." This case is one rung thinner: there is not even a
config surface, only a published claim.

Two of the seven were found while trying to use them. `SET EXCLUSIVE` and
`SET MULTILOCKS` were in a discovery step for AIF-112 precisely because the
published page said they existed. That is the cost: the doc sent a reader
looking for something that was never there.

## Scope question to settle first

Are the seven **aspirational** (classic xBase settings intended but not built),
or **stale** (once implemented, since removed)? The answer changes the fix:

- Aspirational -> they belong in a roadmap or a clearly-labelled "not yet
  implemented" block, not in "current documented surfaces."
- Stale -> they should be deleted from the page and, if anything depended on
  them, that dependency is already broken and unrecorded.

`git log` on `cmd_set*.cpp` and on the mdx will answer this in one pass. Do it
before choosing a remedy.

## Design (options)

1. **Delete the seven from the page.** Cheapest, immediately honest, loses the
   record of intent.
2. **Split the block.** Keep implemented settings under "current documented
   surfaces"; move the seven under an explicitly labelled heading such as
   "Classic xBase settings not implemented." Preserves intent, ends the false
   claim.
3. **Implement them.** Only if any are actually wanted. `SET EXACT` and
   `SET SAFETY` have real semantics in the xBase tradition; `SET CARRY` and
   `SET CONFIRM` are screen-editing behaviours that may not fit this runtime at
   all. This is a per-setting decision, not one decision.

Option 2 is recommended: it costs one edit, tells the truth, and does not throw
away the fact that somebody meant these.

## Check the neighbours before closing

This lane should not fix seven lines and declare victory. The same page carries
other unqualified lists, and other pages may too:

- [ ] The rest of `set-family.mdx` -- the paragraph naming `SET STATUS`,
      `SET TIME`, `SET TIMER`, `SET CLOCK`, `SET BELL`, `SET TYPEAHEAD`,
      `SET REPROCESS` as being "in the settings registry" is unverified here.
- [ ] `command-catalog.mdx` -- generated from source headers, so likely sound,
      but its `status` column is only as good as the headers.
- [ ] Any other `content/docs/**` page with a bare code block of command names.

The website documentation matrix classifies each page as `static`, `maintained`,
or generated. `set-family.mdx` should be checked against that classification --
if it is generated, the generator is the defect, not the page.

## What this does NOT solve

- It does not address `USER`'s recent promotion to `supported`
  (`USER_COMMAND_STATUS_PROMOTION_2026-08-15.md`), which is an owner ruling with
  its gaps declared, not a documentation defect.
- It does not audit HELP or CMDHELP for the same class of drift. Runtime `HELP`
  is generated from source metadata and is likely sound, but that is an
  assumption stated here rather than a measurement.

## Acceptance

- [ ] Aspirational-vs-stale settled from git history, recorded in this doc.
- [ ] The seven no longer appear as "current documented surfaces" on the live
      site.
- [ ] The neighbour checks above completed, findings recorded even where clean.
- [ ] If a guard is cheap: something that compares published command/setting
      names against the source registries, so this class of drift fails a gate
      rather than waiting for a reader. `refcheck_v1.py` and the normalization
      gate already do this for `dotref`/`foxref` entries -- the SET family
      appears not to be covered by either.

The last item is the one worth arguing about. `prepush_gate.py` already runs a
cross-authority normalization gate that would have caught this if the SET family
were in scope. Extending that is likely cheaper than any manual audit, and per
the gate-compliance figure quoted in `PREPUSH_GATE_REFERENCE_V1.md` --
"obligations carrying a gate held 83-94 percent compliance; the one without a
gate held 33" -- it is the only version of this fix that stays fixed.

## Ties

- `BBS_SESSION_EXCHANGE_GUARD_LANE_V1.md` -- the VDISK CEIL precedent.
- `PREPUSH_GATE_REFERENCE_V1.md` -- the gate-vs-no-gate compliance figures.
- `content/docs/dev/website-documentation-matrix.mdx` -- page classification.
- AIF-112 -- where this was found, but not where it belongs.
