---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-022
  recorded_at_utc: 2026-08-19T08:44:49Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: f88765b97
  authorization:
    requested_by: maintainer (member.derald), in-session, "yes" then implicit continuation --
      the A/B test proposed in section 5 of the gate 11 spike.
  report:
    path: docs/maintenance/AIF120_ORIGIN_AB_RULING_V1.md
    kind: ruling
---

# AIF-120 -- R16: a stated dimension is advisory when content determines it

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

**Evidence tier: `runtime-proven`.** Both renders executed under `xvfb` in the
agent's container and inspected. Evidence:
`docs/maintenance/evidence/AIF120_origin_ab.png`.

## 1. The test

Contract section 8 makes two behaviours legal: a generator may honour `ORIGIN`, or
may ignore it entirely and remain conformant. The gate 11 spike proposed rendering
the same document both ways to see which the contract should prefer.

Done. One document -- `UIDEF_STUDENTS.DBF` -- two conformant generators.

## 2. The result: neither wins, and that is the finding

| | A: `ORIGIN` honoured | B: `ORIGIN` ignored |
| --- | --- | --- |
| labels | **truncated** -- `Lnam`, `Fnam`, `Gend`, `Enroll` | **all legible** |
| field widths | **preserved** -- `Gender` one character, `Email` wide, `Dob` date-sized | **all identical** -- information lost |
| positions | as authored | derived from `ORDINAL` |

**A destroys the labels. B destroys the fields.** The expected result was that B
would simply be better; it is not. Each render loses something the other keeps,
and what each loses is different in kind.

## 3. Why, and the rule that falls out

A label's width is a **consequence of its content**. `ORIGIN_WIDTH = 41` on a
label records how wide that text happened to be *in VFP's font*. On any other
toolkit that number is not information about the design -- it is a stale
measurement of a different font, and honouring it truncates.

A text field's width is **not** a consequence of its content. It is a design
decision about how much data must fit: `Gender` is one character, `Email` is
forty. **The document knows this and the target cannot infer it.** Discarding it
loses real information, which is exactly what B does.

**R16. A dimension stated in `ORIGIN` is ADVISORY for controls whose size is
determined by their content, and AUTHORITATIVE for controls whose size is
determined by the data they must accommodate. A conformant generator derives the
former from content and honours the latter.**

The v1 `KIND` vocabulary already draws the line, so R16 needs no new field:

| | kinds | `ORIGIN` size |
| --- | --- | --- |
| content-sized | `label`, `button`, `check`, `radio`, `group`, `page` | advisory -- derive from content |
| data-sized | `text`, `list`, `combo`, `image` | authoritative -- honour |
| container | `form`, `panel`, `pageset` | authoritative -- honour |

Position (`ORIGIN_TOP`, `ORIGIN_LEFT`) is untouched by R16 and remains advisory
throughout, per R12.

## 4. What R16 changes

**It refines R12.3 rather than contradicting it.** R12.3 says an *absent*
dimension is derived by the target and never defaulted to a number. R16 extends
that: for content-sized controls, a *present* dimension should also be derived,
because presence does not make it meaningful. The measured form of the rule is
sharper than the ruled form was -- **the labels that carry a width are the ones
that break.**

**It makes section 8's "may ignore `ORIGIN` entirely" wrong in both directions.**
A generator that ignores it wholly loses field sizing; one that honours it wholly
truncates text. Neither of the two behaviours the contract currently permits is
the right one, and R16 names a third that is.

**It leaves section 5b's finding intact.** Imports are still `FLOW = free` with an
`ORIGIN` group carrying the layout, and `ORIGIN` is still load-bearing for
imports. R16 changes how a generator *reads* that group, not whether it is needed.

## 5. What this does not establish

- **One toolkit.** Tk's font is wider than VFP's; on a toolkit with a narrower
  font, A's labels might not truncate and the asymmetry would be less visible.
  The rule is argued from *why* the numbers differ in kind, not from Tk.
- **`image` is classified by assumption.** It is grouped as data-sized because an
  image has intrinsic pixel dimensions, but no specimen exercised it here.
- **No wrapping or ellipsis was tried.** A generator could honour a stated width
  and ellipsise instead of clipping. That is a third behaviour and it was not
  tested.
- **Still one document, one platform, no handlers wired.**

## 6. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
$env:X64BASE_ALLOW_DATA = "1"
git add docs/maintenance/AIF120_ORIGIN_AB_RULING_V1.md
git add docs/maintenance/evidence/AIF120_origin_ab.png
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git status --short -uall
git commit -m "AIF-120: R16 -- a stated dimension is advisory when content determines it; A/B render evidence"
Remove-Item Env:\X64BASE_ALLOW_DATA
```
