---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-017
  recorded_at_utc: 2026-08-19T01:30:24Z
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
    baseline_commit: d752a5e62
  authorization:
    requested_by: maintainer (member.derald), in-session, "good, continue" -- continuing
      discovery against the corpus after the RESERVED4 investigation closed negative.
  report:
    path: docs/maintenance/AIF120_METHOD_CODE_SCOPE_V1.md
    kind: ruling
---

# AIF-120 -- R14: real form code cannot enter v1, and the corpus says so numerically

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

Settles the lane's oldest open item. **R4** ruled that reading `.SCX` recovers
layout and binding and no logic, and flagged that this was true of *wizard* files
and might not be true of the format. The lane has wanted a hand-authored specimen
with real method code since the first day. It now has 169 of them.

## 1. The measurement

`VFPX/Samples` at `8827135c2c60`, 170 `.SCX`, of which **169 carry `METHODS`**.

| | |
| --- | --- |
| procedures | **1,583** |
| method code | **501,447 bytes** |
| distinct method names | 315 |
| code lines, comments and blanks excluded | 15,692 |

## 2. The decisive number

The charter's **stopping rule**, inherited from AIF-119: *"if a construct cannot
be expressed without exposing the target's object model to the script, it does
not belong in v1. The whole argument for FoxPro syntax is that it hides that
model."*

Measured against that rule:

| construct | procedures containing it | share |
| --- | --- | --- |
| `THIS.` | 810 | 51% |
| `THISFORM.` | 741 | 47% |
| `THIS.PARENT` / `PARENT.` | 120 | 8% |
| `DODEFAULT()` | 89 | 6% |
| `THISFORMSET.` | 87 | 5% |
| `CREATEOBJECT()` | 32 | 2% |
| `_SCREEN` | 26 | 2% |
| `ADDOBJECT()` | 12 | 1% |
| **any of the above** | **1,396** | **88%** |

**88% of real form procedures navigate the target's object model**, and 4,411 of
15,692 code lines (28%) touch it directly.

## 3. R14 -- the ruling

**R14. Method bodies do not enter v1. The design table carries a handler
REFERENCE -- a name and its dispatch -- and never handler source. R4's scope
boundary is not a limitation of the import path to be lifted later; it is what
the stopping rule requires, and the corpus shows it is required by a factor of
seven to one.**

This is a ruling the lane could have reached by argument and did not, because
until today "what must the DSL do about code" had no evidence attached. It now
has 1,583 procedures of it.

Three consequences.

**R14.1 -- R4 is promoted from a limitation to a boundary.** R4 currently reads
as an apology: `.SCX` import recovers no logic *because wizard forms keep theirs
in a `.VCX`*. That framing invites a future session to "fix" it by learning to
import `METHODS`. It must not be fixed. Importing method bodies would import
`THISFORM.grdOrders.Column2.Header1.Caption` into a language whose entire
argument is that the script never holds an object.

**R14.2 -- the table carries handler identity, and R11 already assumed this.**
R11 gave every handler a `DISPATCH` attribute and an `ON_COMPLETE` name. Those
are references. R14 states the general form: what crosses the interchange
boundary is *which* handler runs and *where*, never *what it does*. A generator
emits a stub with the right name, thread affinity and completion path; the body
is the target platform's business.

**R14.3 -- the event vocabulary is small even though the method vocabulary is
not.** 315 distinct method names, but the distribution is steep:

| method | implementations |
| --- | --- |
| `Click` | 428 |
| `Init` | 202 |
| `InteractiveChange` | 94 |
| `Activate` | 83 |
| `Deactivate` | 80 |
| `Destroy` | 52 |
| `Error` | 30 |
| `GotFocus` | 26 |
| `Load` | 21 |
| `RightClick` | 19 |

Ten names cover 1,035 of 1,583 procedures (65%). A v1 that names roughly ten
events and refuses the rest is not a crippled subset -- it is two thirds of real
usage, and every one of those ten exists on every platform in the charter's
table. This is the R8 pattern again: adopt the vocabulary that is already there
rather than invent one.

## 4. The 12% that does NOT touch the object model, and why it matters

187 procedures reference nothing object-oriented. They are not empty -- median
body is 3 lines -- and their leading verbs are:

`IF`/`ENDIF` (94), `RETURN` (55), `LOCAL` (53), `LPARAMETERS` (43), `CASE` (43),
**`USE` (41)**, `DO` (35), `MESSAGEBOX` (34), **`SELECT` (34)**, **`INSERT` (33)**,
`FOR` (26), **`MODIFY` (22)**, `SET` (20).

**That residue is data and control flow, and it is vocabulary DotTalk++ already
has.** `USE`, `SELECT`, `INSERT`, `MODIFY`, `SET`, `DO`, `IF`/`CASE` are commands
in `SYSCMD` today. So the split is not "code we can port and code we cannot" --
it is:

- **object-model navigation (88%)** -- belongs to the target, never crosses
- **data and control flow (12%)** -- already expressible, and needs no new
  language surface to express it

Which is a much better position than it looks. The lane does not need a
general-purpose scripting story to be useful; it needs handler references plus
the command language it already ships.

## 4b. Confirmed on `.VCX`, where the coupling changes SHAPE

23 of the 25 corpus class libraries carry code: **821 procedures, 300,288 bytes,
8,881 lines.** This is the file type wizard forms delegate their behaviour to, so
it is where R4's missing logic actually lives.

| | `.SCX` | `.VCX` |
| --- | --- | --- |
| procedures | 1,583 | 821 |
| object-model-referencing | **88%** | **83%** |
| lines touching it | 28% | 24% |

R14 holds. Across both formats: **2,404 procedures, 801 KB, 86% navigating the
object model.**

**But the composition inverts, and the inversion is the finding:**

| construct | `.SCX` | `.VCX` |
| --- | --- | --- |
| `THIS.` | 51% | **74%** |
| `THIS.PARENT` / `PARENT.` | 8% | **33%** |
| `THISFORM.` | **47%** | 14% |

**Class-library code navigates RELATIVELY; form code navigates ABSOLUTELY.** A
reusable class cannot know which form it will be dropped onto, so it walks the
ownership chain -- `THIS`, `THIS.PARENT`. A form's own handler knows exactly where
it is and says `THISFORM`.

That distinction is worth more than the 83% figure. **Relative navigation is the
portable half.** Every platform in the charter's table has a parent chain --
Turbo Vision owners, wx parents, Qt parents, Tk masters, DOM parents. None of
them has an equivalent of `THISFORM`, an absolute reference to a specific
top-level object from anywhere inside it. So if any code-adjacent construct ever
enters this DSL, the `THIS`/`PARENT` idiom is the one with a portable mapping and
`THISFORM` is the one that does not.

R14 is unchanged: neither enters v1. But this records WHICH door to try first if
a later version reopens the question, and it says so with a measurement rather
than a preference.

**One vocabulary note:** `Error` is the second-most-implemented method in `.VCX`
(130) against ninth in `.SCX` (30). Error handling is a class-library
responsibility in practice. If the DSL ever names ten events, the `.SCX` ranking
is the wrong one to take them from on its own.

## 5. What R14 does not settle

- ~~**`.VCX` method bodies are unmeasured.**~~ **Measured the same session -- see
  section 4b.** R14 holds on the second format and the coupling changes shape.
- **`SKIP FOR` expressions (R9) are unaffected and still open.** They are
  expressions in menu definitions, not method bodies, and the 88% figure says
  nothing about them.
- **It does not say what a generator emits for a named handler with no body** --
  a stub, an error, or nothing. That is gate 10 schema work.
- **One corpus, one vendor.** These are Microsoft sample forms. Application code
  written by ordinary VFP shops may navigate the object model more, not less.

## 6. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git add docs/maintenance/AIF120_METHOD_CODE_SCOPE_V1.md
git add docs/maintenance/AIF120_CORPUS_SCAN_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git status --short -uall
git commit -m "AIF-120: R14 -- method bodies stay out of v1; 88% of 1,583 real procedures navigate the object model"
```
