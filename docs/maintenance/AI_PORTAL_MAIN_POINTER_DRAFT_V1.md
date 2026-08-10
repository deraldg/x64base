# DRAFT: replacement for AI_PORTAL.md on the `main` branch (pointer-only)

**Status:** APPROVED -- owner ruled "Promote" 2026-08-10, and ratified the companion rule
**no widows and orphans** (glossary: `labtalk/ai_portal/AI_GLOSSARY_V1.md`): no published
document without a refresh path, no pointer without a resolvable target on its own surface.
The rule also settles this draft's open sub-ruling below: `AI_PORTAL.md` IS added to
`PROMOTE.manifest`, because manifest exclusion is exactly the mechanism that orphaned it.
Owner: member.derald. Steward: member.ai.claude.cowork.
Date 2026-08-09 (ruled 2026-08-10). **Not a file for this branch** -- this is the approved
CONTENT of `AI_PORTAL.md` as it should exist on `main`, delivered once through the sanctioned
staging channel (`C:\x64base` -> commit -> push), never by editing `main` directly.

Rationale: `main`'s current `AI_PORTAL.md` is an ORPHAN -- published under an older regime,
later trimmed from `PROMOTE.manifest` ("metalevel docs, portal seeds ... deliberately
trimmed"), so nothing refreshes it and it now serves a stale pre-recall-graph portal that
actively misleads (measured 2026-08-09: `main` = 507 commits behind, intake frontier
AIF-025 vs real AIF-098; a hosted agent baselined on it and collided on AIF-044). Per the
no-perishable-literals rule (AIF-082), the fix is a PURE POINTER: nothing below can go
stale, because nothing below asserts perishable state.

Open owner ruling: whether to also add the single line `AI_PORTAL.md` to `PROMOTE.manifest`
so future pointer edits flow automatically (safe precisely because the pointer is
non-perishable), or leave it manifest-excluded and touch it manually on the rare branch
rename. Either is coherent; the trim was a deliberate scope choice, so the reversal is the
owner's call.

---

## Proposed content of `main:AI_PORTAL.md` (everything between the rules)

```markdown
# x64base AI Portal -- you are on the wrong branch

You are reading the `main` branch. `main` is a lagging, frozen public snapshot.
It is NOT the onboarding source, and nothing on this branch may be used to
derive current state (lane numbers, current targets, work status, doctrine
versions).

## Where to go

The canonical AI Portal, the onboarding corpus, and the current integration
baseline live on the `development` branch of this same repository:

    https://github.com/deraldg/x64base/tree/development

Read `AI_PORTAL.md` at the root of THAT branch and follow its Mandatory Start.

## The rule (binding for every AI partner)

Before reading source or writing any proposal or change package:

1. Enumerate the published branches -- do not trust the default:

       git ls-remote --heads https://github.com/deraldg/x64base.git

2. Baseline on `development` and record its exact commit in your package.
   Use `main` only if the maintainer names it for the task.
3. If you cannot reach `development`, say so explicitly and mark your work
   provisional. Do not present a `main`-baselined package as current.

Building against `main` without enumerating branches is a hard onboarding
failure. It has happened; it produced colliding lane numbers and proposals
against retired structure. This page exists so it does not happen again.

## Why this page is nearly empty

Anything written here would freeze the moment `main` was promoted and then
mislead every reader until the next promotion. So this page asserts nothing
perishable: it only points. The pointer stays true regardless of how far
`main` lags.

Maintainer: Derald Grimwood (member.derald). This pointer supersedes any older
full-portal text previously published on `main`.
```

---

## Delivery runsheet (host-side, owner)

1. Review both drafts (this file + the banner added atop dev `AI_PORTAL.md`).
2. Optional but recommended: exercise the new peer-review concept -- this is
   AI-facing authority text, one of its six mandatory triggers; a
   different-provider agent reviews before promotion.
3. In `C:\x64base` (staging, on `main`): replace `AI_PORTAL.md` content with the
   block above (byte-diff against this draft to prove mirror == source).
4. Commit in staging with a message citing this draft's path + dev commit; push
   `main`.
5. If ruled yes: add `AI_PORTAL.md` to `PROMOTE.manifest` (single line) so the
   pointer rides `rebuild-staging.ps1` thereafter.
