---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-021
  recorded_at_utc: 2026-08-19T08:40:58Z
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
    baseline_commit: cba7bb618
  authorization:
    requested_by: maintainer (member.derald), in-session, "yes" -- to writing up the
      gate 11 spike and adding uidef_tk.py to tools/uidef/.
  report:
    path: docs/maintenance/AIF120_GATE11_TK_SPIKE_V1.md
    kind: measurement
---

# AIF-120 -- gate 11 spike: a Tk frontend built from the table alone, and what it made visible

Status: **measurement, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

**Evidence tier: `runtime-proven`.** Executed by the agent in its own container
under `xvfb`; the rendered window was captured and inspected. Not run on the
maintainer's machine.

## 1. Gate 11's test, and what it required

The charter's gate 11: *"A second backend spiked from the TABLE, not the parser --
enough of wx or Tk to prove a generator needs nothing but the documented schema.
Without it, gate 3 passing says nothing about portability."*

`tools/uidef/uidef_tk.py` is that spike. Its **entire input** is a DBF with a memo
sidecar plus the gate 10 contract. It imports a DBF reader and `tkinter`. It
contains no reference to VFP, `.SCX`, `foxref`, the FoxTalk layer, or any other
part of this project -- checked by reading it, and it is 150 lines, so the check
is cheap to repeat.

Tk was chosen deliberately as the **least flattering** backend: the charter's own
threading table calls it *"not thread-safe at all"*, and its geometry model is
`pack`/`grid`/`place` rather than anything resembling character cells.

## 2. It works

`UIDEF_STUDENTS.DBF` -- imported from `STUDENTS.SCX`, 1 `DOC` row, 3 `FONT` rows,
20 `OBJ` rows -- rendered as a Tk window with nine label/entry pairs in the right
order, at the right positions, with the right relative widths (`Gender` narrow,
`Email` wide).

Evidence image: `docs/maintenance/evidence/AIF120_uidef_tk_render.png`.

**Gate 11 is satisfied in miniature.** A frontend was generated from the design
table by code that knows nothing else, which is the claim the charter's amendment
(b) rests on: *"a new frontend never needs the DSL, the parser, or any of this
C++ -- it needs to read one documented table."*

Reproduction:

```sh
cd tools/uidef
python3 import_scx.py ../vfp/fixtures/STUDENTS.SCX generated/UIDEF_STUDENTS
xvfb-run -s "-screen 0 620x420x24" python3.12 uidef_tk.py \
    generated/UIDEF_STUDENTS.DBF --shot render.png
```

Two environment notes, recorded because they cost time: `tkinter` is present only
under Python **3.12** in that container (3.11 and 3.10 have none), and the capture
uses ImageMagick's `import`, because `xwd` is absent.

## 3. What it made VISIBLE, which is worth more than the pass

**Every label is truncated.** `Lnam`, `Fnam`, `Gend`, `Enroll` -- clipped short.

That is not a generator defect. `ORIGIN_WIDTH = 41` was honoured exactly as
contract section 8 requires, and **Tk's default font is wider than the font VFP
measured those widths against.** The positions travel; the sizes do not, because
the numbers were never about the content -- they were about one font on one
platform.

**This is R12's argument, rendered.** R12 chose layout intent as primary and
quarantined absolute geometry as advisory, and it was decided on a *sequencing*
argument: intent-first can add absolute later as an annotation, absolute-first
cannot add intent without rewriting every consumer. That argument is sound and it
was not evidence. There is now a picture of the alternative failing: honour
absolute geometry faithfully on a second toolkit and the content stops being
legible.

**R12.3 is vindicated in the same image.** Its rule -- *an absent dimension is
derived by the target, never defaulted to a number* -- is what would have avoided
this. A label with no stated width would have been sized by Tk from its own text
and font, and would have read correctly. **The labels that carry a width are the
ones that break.**

**And R6's exclusion is visible as a hole.** `STUDENTS.SCX`'s `BUTTONSET1`
imported as an empty `panel`: the buttons inside it are count-generated implicit
children, which R6 excludes from v1. The render shows precisely what that costs --
a container arriving with nothing in it. Nobody reading R6 would picture that; the
image supplies it.

## 4. What this does NOT establish

- **One document, one backend, one platform.** Nothing about wx, Qt, the browser,
  or the TUI.
- **`FLOW` is still unexercised.** Every object in the test document is
  `FLOW = free` with an `ORIGIN` group, per section 5b. The `row`/`column`/`grid`
  paths in the generator exist and have never run against real data.
- **No handlers were invoked.** `HANDLERS` was parsed and printed, never wired.
  R11's `DISPATCH` and R14's reference model are untested at runtime.
- **No menus.** Section 11 remains unexercised.
- **Not run on the maintainer's machine**, so the Windows path is unverified.

## 5. The obvious next test, and it is cheap

Render the SAME document twice: once honouring `ORIGIN` and once ignoring it and
letting Tk size everything from content. Section 8 says a generator that ignores
`ORIGIN` entirely remains conformant, so both are legal. **If the ignore-`ORIGIN`
render is more legible than the honour-`ORIGIN` one, that is a measured argument
for changing which of the two the contract calls advisory.**

## 6. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git add tools/uidef/uidef_tk.py
git add docs/maintenance/AIF120_GATE11_TK_SPIKE_V1.md
git add docs/maintenance/evidence/AIF120_uidef_tk_render.png
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git status --short -uall
git commit -m "AIF-120: gate 11 spike -- Tk frontend from the UIDEF table alone; truncated labels are R12's argument rendered"
```

The PNG is a data file; expect `prepush-gate` to want `X64BASE_ALLOW_DATA=1`.
