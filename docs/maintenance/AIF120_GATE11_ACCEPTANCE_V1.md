---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-036
  recorded_at_utc: 2026-08-19T11:30:00Z
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
    baseline_commit: ecbb9a6dc
  authorization:
    requested_by: maintainer (member.derald), in-session -- "let me the gate 11 acceptance
      test". Section 14 item 4 of the contract names this as its own acceptance test.
  report:
    path: docs/maintenance/AIF120_GATE11_ACCEPTANCE_V1.md
    kind: ruling
---

# AIF-120 -- R28: gate 11 run for real. The contract passed, and it is not finished

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

The contract names its own acceptance test:

> **Gate 11 is the acceptance test for this document** -- a frontend generated
> from this table alone, by someone holding nothing else.

I could not run it, because I wrote both ends. It has now been run by an
implementer that had never seen my consumers.

## 1. Method -- isolation by construction, not by instruction

A clean directory containing **only**: the contract, a generic DBF/FPT reader
(given so the exercise tests the UI language rather than DBF parsing), and five
design tables -- `FLOWDEMO`, `TABDEMO`, `FONTDEMO`, `UIDEF_STUDENTS`,
`UIDEF_MENU`, plus `STUDENTS.dbf` to bind against.

Nothing else was reachable. Not `uidef_tk.py`, not the rulings, not the lane. The
implementer was told that wanting to look at another implementation was itself a
finding to write down rather than act on, and reports the impulse was strongest
at exactly the two places this ruling calls worst.

Its output is preserved verbatim:
`docs/maintenance/evidence/AIF120_gate11_render.py` (718 lines) and
`docs/maintenance/evidence/AIF120_gate11_FINDINGS.md`.

## 2. Result

**Four of the five tables rendered.** A menubar with 7 popups, 67 items,
mnemonics, accelerators and separators. A `ttk.Notebook` from `pageset`/`page`.
Three distinct fonts resolved through `FONTREF`, with a dangling reference
diagnosed. An imported data-entry form. The fifth was **refused**, correctly, for
a `grid` with no `Columns`.

**Gate 11 is met as a test and the contract is not finished.** An independent
implementer built a working consumer from the document. It also logged **4
contradictions, 19 gaps and 7 ambiguities**, and its verdict is the finding:

> The contract answers *"how is a UIDEF document structured?"* completely and
> *"what is in one?"* barely. A second implementer can build the tree, validate
> requiredness and refuse correctly; they cannot render a font, size a bound
> control, or draw a menu without reverse-engineering the fixtures -- which is the
> exact activity section 1 promises is unnecessary.

Section 1 promises *"a consumer needs only this document and a DBF reader."*
**That promise is not met.**

## 3. R28.1 -- the worst defect is mine, not the contract's

`UIDEF_STUDENTS`'s panel `O020` has **no child records**. Its ten buttons exist
only as dotted property names inside its own `PROPS`:

```
cmdadd.caption   = "\<Add"
cmdadd.enabled   = .T.
cmddelete.name   = "cmdDelete"
...
```

**22 dotted properties naming 10 implied children** -- `cmdAdd`, `cmdDelete`,
`cmdEdit`, `cmdEnd`, `cmdExit`, `cmdFind`, `cmdNext`, `cmdPrev`, `cmdPrint`,
`cmdTop`. Section 13 and R6 put implicit children out of v1 deliberately, so a
conformant reader renders an empty panel -- and the panel carries no
`ORIGIN_WIDTH`, so it renders as nothing at all.

**Every UIDEF import of a wizard form silently loses its entire navigation bar.**
The screenshot is a clean data-entry form with no indication that ten buttons are
missing. That is section 4's own stated failure mode, produced by a rule section
13 states on purpose.

I walked past this. Measuring the property passthrough for R25 I saw
`label1.name` (x77), `behindscenes1.name` (x72), `c_solutions1.name` (x72) in the
key list, noted them as "the parent's aggregated child properties -- another
finding, but let me not chase it", and moved on. They are not noise. They are ten
missing buttons. **An implementer with no stake in the design chased what the
author set aside.**

> **R28.1.** An object whose children exist only as dotted property names is
> **not** a complete object. A reader that drops them must say how many it
> dropped and name them. Silently rendering an empty container is R7's empty box
> at container scale.

## 4. R28.2 -- two sound rules that jointly erase the menus

Section 7: *"an unknown property is dropped silently, never rejected"* (R3 --
import is an allow-list).
Section 11 names six menu properties: `Caption`, `Key`, `Message`, `Checked`,
`Enabled`, `Separator`.

Measured on `UIDEF_MENU.DBF`, 77 rows carry **thirteen** distinct keys:

```
Name  Container  OpenedBy  OpenerPrompt  DeclaredItems  Caption  Mnemonic
Key   Message    Mark      SkipFor       Separator      KeyLabel
```

Seven are undocumented. Two of them are load-bearing: **`Container` is the only
thing distinguishing a popup from an item**, and **`OpenerPrompt` is the only
caption a popup row has** -- the 10 container rows carry no `Caption` at all.
Meanwhile two keys section 11 *does* name, `Checked` and `Enabled`, appear
**zero** times; the real one is `Mark`, on 67 rows.

So a reader following both rules exactly produces **a blank menubar**. Neither
rule is wrong. Together they delete the menu.

> **R28.2.** Structure must not travel in a channel the spec permits a reader to
> discard. Any property a consumer must understand is named in the contract, and
> the silent-drop rule applies only to what is left.

This is R25.5 arriving from the other direction. There it was `inputmask` carrying
a width under VFP's spelling; here it is `Container` carrying the menu tree under
no spelling at all.

## 5. R28.3 -- `SOURCE.Table` has no case rule, and the failure is invisible

`UIDEF_STUDENTS` says `Table = students.dbf`. The file is `STUDENTS.dbf`.

On Windows this works by luck. The implementer, on a case-sensitive filesystem,
implemented section 10 **literally**, resolution failed, R17 had no schema, and
the code fell through to the unbound branch. In their words:

> The form rendered and looked entirely plausible with nine wrong field widths. I
> only caught it because I happened to be logging the resolution.

> **R28.3.** `SOURCE.Table` resolution is case-insensitive, and a document whose
> table does not resolve is **refused**, not rendered unbound. A width silently
> derived from a schema that was never opened is worse than no width.

## 6. R28.4 -- section 11's `\<` claim is false of the table

Section 11 says the source vocabulary *"uses them consistently in both captions
and prompts (R8)."* Measured: **0 of 55 captions** in `UIDEF_MENU.DBF` contain
`\<`. The importer resolves the escape into a `Mnemonic` index -- which section 11
does not name. The claim is true of `.MNX` and false of UIDEF, and the contract
does not distinguish the two.

## 7. R28.5 -- R16 makes imported forms collide

The implementer expected R16/R17 to make imported forms *more* correct and found
the opposite. Honouring `ORIGIN` positions while re-deriving sizes puts a
content-sized label into the space the designer measured for a shorter one. Their
render of `UIDEF_STUDENTS` shows `Enroll_d:` running into its own entry box, and a
40-character `email` overrunning its authored 290 px slot.

R17's `r=0.9982` measured **correlation**, not **collision**. Neither R16 nor R17
says what happens when a re-derived size crosses a neighbour that kept its
authored position. Open, and mine to have missed.

## 8. What was clear -- a test that only reports faults is not a measurement

The implementer built the record model, the `PARENT` tree, per-direction
requiredness validation and the refusal policy **right on the first try**, from
the document alone. `RECKIND`, `OBJID`, `PARENT`, `ORDINAL`, the three-value
requiredness of section 6, `ORIGIN`'s quarantine, and the refuse-unknown-`KIND`
rule all did their job. Nine sections are listed as clear.

The split is sharp and worth stating plainly: **the shape of a document is
specified; the contents of one are not.**

## 9. The nearest fixes, in the implementer's order of value

1. Name the `FONT` row's properties.
2. Define `BINDING`'s syntax, and require refusal when `SOURCE.Table` does not
   resolve.
3. State the grid wrap rule in prose, not only in a ruling.
4. Promote the menu structure keys out of the silent-drop allow-list.
5. Either give `ORIGIN_SCALE` conversions or cut the enumeration down to `px`.

Plus R28.1, which is ahead of all of them and is a defect in the importer rather
than the document.

## 10. Still open

- **One implementer, one toolkit.** Tk again. A second reading is a data point,
  not a proof.
- **The 19 gaps are not all ruled here.** This document rules the five with
  measured consequences. The rest are in
  `docs/maintenance/evidence/AIF120_gate11_FINDINGS.md` and are the owner's to
  triage.
- **The DBF reader was given.** Whether a third party could parse the container
  from the contract alone was not tested.

## 11. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_GATE11_ACCEPTANCE_V1.md
git add docs/maintenance/evidence/AIF120_gate11_FINDINGS.md
git add docs/maintenance/evidence/AIF120_gate11_render.py
git add docs/maintenance/evidence/AIF120_gate11_students.png
git add docs/maintenance/evidence/AIF120_gate11_menu.png
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R28 -- gate 11 run by an independent implementer; 4 of 5 tables render, 4 contradictions and 19 gaps found"
```
