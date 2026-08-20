---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-084
  recorded_at_utc: 2026-08-20T06:00:00Z
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
    id: project.x64base.gui
    root: D:/code/ccode/gui
  git:
    branch: development
    baseline_commit: 99653aaa9
  authorization:
    requested_by: maintainer (member.derald) -- "do i get to try my form?", which
      exposed that the fixture corpus every refusal count is measured on does not
      exist outside the session container. Closing the author's own leftover under
      the standing housekeeping rule.
    scope: >
      Add an author script for the sixteen negative and property fixtures so the
      corpus is reproducible from a clone. Writes gui/uidef/ and docs/ only.
  report:
    path: docs/maintenance/AIF120_FIXTURE_CORPUS_V1.md
    kind: ruling
---

# AIF-120 -- R75: the corpus the refusals are measured on existed in one container, and the citation gate could not see that

**Status: review-needed.** The author does not self-approve.

## 0. The one-paragraph version

Asked whether he could try his form, the maintainer could not -- and the reason was
worse than a missing build target. The eighteen UIDEF documents every measurement
in R66, R70, R73 and R74 is quoted against **were not in the repository**. Four of
them regenerate from tracked author scripts. **The other sixteen -- the negative
and property cases, the ones that prove the gates actually refuse things -- were
built ad hoc during R66 and R70 and existed only in the session container that made
them.** `author_cases.py` reproduces all sixteen. Verified behaviourally, not by
byte.

## 1. What was actually missing

| fixture | source | state before this ruling |
|---|---|---|
| `FRAMEDEMO` | `author_frame.py` | reproducible, script tracked |
| `FLOWDEMO`, `FONTDEMO`, `AUTHORED`/`DOC1` | `author_flow.py`, `author_fonts.py`, `author_uidef.py` | reproducible, scripts tracked |
| **the sixteen `N*` / `P*` cases** | **nothing** | **container only** |

Those sixteen carry every refusal claim the lane has made: R66's eight bad
documents refusing with distinct reasons, R70's "six of eighteen refused" table,
R73's `P1_order_bad` and `P2_order_ok`. A reader with a clone could read the counts
and reproduce none of them.

## 2. Why nine rulings went by without noticing

The `cited-paths` gate reads a document, extracts anything shaped like a repository
path, and reports those that are untracked. It has caught real widows in this lane
repeatedly, including one of mine three commits ago.

It could not catch this one. **The rulings cite these fixtures by BARE NAME** --
`N1_editable_grid`, `P4_rowlimit_big`, `FRAMEDEMO` -- and `PATH_RE` matches paths.
Evidence named rather than pathed is outside what that gate can reach.

That is the finding worth keeping, because it is not a bug in the gate:

> **A gate sees the shape it was built to see.** `cited-paths` makes untracked
> *pointers* visible and leaves untracked *evidence* invisible whenever the
> evidence is referred to the way a person refers to it. The lane's own white paper
> argues that a gate's value is telling another lane where to look; this is the
> same argument from the other side -- a gate silent about a class of thing is not
> evidence that the class is clean.

Nothing here changes the gate. Naming the blind spot is the deliverable.

## 3. What R75 adds, and what it deliberately does not

**Adds:** `gui/uidef/author_cases.py`, holding the sixteen documents' rows and
writing them through `uidef.write()` -- the same path every other author script
uses. `python author_cases.py` makes all sixteen; `python author_cases.py N5_ordinal_spec`
makes one.

**Does not add:** the `.DBF`/`.FPT` binaries. They are derived artifacts, they
would land as `data/fixtures` in every gate run, and one byte of each churns daily
(section 4). The house already treats generated documents this way -- that is why
`FRAMEDEMO.DBF` was never tracked either, and that part was right.

## 4. Verified behaviourally, because byte-identity is the wrong test

Regenerating and comparing against the originals, `N1_editable_grid.DBF`, 1316
bytes, differs in **three**:

| offset | before | after | what |
|---|---|---|---|
| 3 | `0x13` | `0x14` | the DBF header's day-of-month stamp |
| 969 | `0x1c` | `0x1a` | memo block pointer |
| 1295 | `0x90` | `0x8e` | memo block pointer |

A memo block number is a position in the `.FPT`, not content, and a date stamp is a
date. So byte-equality would fail every regeneration for reasons that mean nothing.
The test that means something is whether the document still *says* the same thing:

```
behaviourally identical: 16 of 16
```

Each fixture regenerated, then compared on both surfaces that consume it --
`manifest.stream_refusals()` and the full `uidef_wx.generate(..., stream=True)`
output. Same refusals, same C++, all sixteen. `FRAMEDEMO` regenerates with exactly
one byte differing, the same date stamp.

## 5. Open

- **The four flavor probes and the workspace scripts** used in R73 (`flavors.dts`) are tracked; the MCC tables they read are shipped data and were already present.
- **`author_cases.py` carries the rows literally.** It is a snapshot, not a derivation -- if a fixture is edited by hand the script goes stale silently. A regeneration check in the lane's own gate would close that, and is not built here.
- **R73.3a stands unchanged:** `x64.dts` and 95 other `.dts` in `dottalkpp/data/scripts` remain untracked. That is another lane's area and another lane's call.

## 6. Good Neighbor

| | |
|---|---|
| What changed | new `gui/uidef/author_cases.py`; this ruling; ledger rows; the session closeout, in this same commit |
| Whose area | AIF-120's own fixtures and docs. No source, no other lane |
| Authorization | maintainer, in-session: "do i get to try my form?" -- and the standing rule that a session sweeps its own leftovers before finishing |
| How to verify | `cd gui/uidef && python author_cases.py`, then `python manifest.py` on any `N*`/`P*` and check the refusal matches the ruling that cites it |
| How to undo | delete the script. Nothing depends on it at build time |
| Risk | none at build time. The script writes only into its own directory |

## 7. Handoff -- PowerShell, run in `D:\code\ccode`

The closeout is staged **with** this ruling, not after it. That is the rule R74's
closeout recorded after this document's own predecessor went stale twice.

```powershell
git status -uall

git add gui/uidef/author_cases.py
git add docs/maintenance/AIF120_FIXTURE_CORPUS_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git add docs/maintenance/SESSION_CLOSEOUT_APPLICATION_UI_DSL_LANE_2026-08-20.md
git add docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md

git status -uall

git commit -m "AIF-120: R75 -- the sixteen refusal fixtures every measurement is quoted against existed only in the session container, and the citation gate could not see it because they are cited by name"
```
