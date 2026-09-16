---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260916-COWORK-210
  recorded_at_utc: 2026-09-16T14:40:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260916-001
  project:
    id: project.x64base.gui
    root: D:/code/ccode/gui
  git:
    branch: development
    baseline_commit: 86acb7470
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-09-16 -- "R77-PROPERTY",
      then "split", then "didn't we agree property?" -- correcting the author's
      reading of "split" as a licence to grow the vocabulary.
    scope: >
      Rules the editable/fixed distinction a PROPERTY, adopted from the VFP
      corpus, and withdraws the `choice` KIND the first draft of this ruling
      proposed. States the corpus measurement the importer needs, which has now
      been taken.
  report:
    path: docs/maintenance/AIF120_FIXED_SET_PROPERTY_V1.md
    kind: ruling
---

# AIF-120 -- R145: a fixed set is not an editable one, and the distinction is a PROPERTY the corpus already carries

Status: **review-needed.** The author does not self-approve.
Owner: `member.derald`. Author: `member.ai.claude.cowork`. Date: 2026-09-16.
Baseline `86acb7470`. R-number from `tools/coordination/next_r.py`, allocated for
the withdrawn draft and **retained** -- one R-number, one question.

---

## 0. The one-paragraph version

`combo` renders an editable control unconditionally while the Workbench uses a
fixed-set one, so a generated frontend offers typed input where the document
permitted one of N values. **That difference is real and this ruling keeps it.**
What this ruling changes is where it lives: the first draft made it a
twenty-first KIND called `choice`, and **that was wrong twice over.** The owner
had already ruled the R77 candidates PROPERTY, and the argument the draft used to
justify a KIND had been outlawed one ruling earlier by R143(b). The corpus then
settled it: VFP records the distinction as a property, and section 7 adopts
properties rather than inventing kinds.

---

## 1. The measurements

### (a) The defect, unchanged

`gui/uidef/uidef_wx.py:277`:

```python
'combo':  'new wxComboBox(%s, wxID_ANY, wxEmptyString, %s, %s)',
```

Unconditional. `wxComboBox` carries a text field. `src/gui/wx/main_frame.cpp`
uses `wxChoice` **twice** -- a dropdown with no text field. R77 recorded this as
*"approximate -- `combo` means the editable one"* and left it. It is not
approximate.

### (b) The corpus, measured 2026-09-16, which the draft said had not been measured

195 corpus files (170 `.scx`, 25 `.vcx`), **4,013 records, 195/195 readable,
zero failures.** Reader: `gui/uidef/_vfp.Dbf(path).rows()`.

VFP records the distinction as a ComboBox property named `Style`, carried as an
ordinary `name = value` line in the `PROPERTIES` memo -- section 7's
mini-language exactly.

```
combobox records (BASECLASS = combobox) : 93
  Style present, explicit                : 51   every one of them value 2
  Style absent                           : 42
    plain combobox, no subclass          : 25
    subclassed                           : 17
```

`Style = 2` is the fixed set. `Style = 0` is the editable one and is the base
default, so VFP omits it.

**Absence is the default, not silence**, and that is established inside the
corpus rather than assumed. `Style` appears on six baseclasses, and `checkbox`
carries both `1` (18 records) and an explicit `0` (4 records) -- VFP writes the
line when the value differs from the **parent class**, not from the base class,
so an explicit `0` is what a reset-to-default looks like. **No combobox record
in 195 files carries an explicit `0`**, which is what 25 plain comboboxes
inheriting the base default looks like and nothing else.

| baseclass | records with `Style` | values |
| --- | --- | --- |
| combobox | 51 | `2` x51 |
| shape | 30 | `3` x29, `0` x1 |
| label | 30 | `3` x30 |
| checkbox | 22 | `1` x18, `0` x4 |
| container | 3 | `3` x3 |
| commandbutton | 2 | `1` x2 |

---

## 2. The ruling

**R145. The editable/fixed distinction is a PROPERTY, adopted from the corpus.
`combo` keeps its name and its single KIND. THE VOCABULARY STAYS AT TWENTY.
The `choice` KIND proposed in this ruling's first draft is WITHDRAWN.**

### (a) Why the KIND argument fails, which is the part worth reading

The draft's case was section 2(a): that the other three R77 candidates fail by
LOSING a capability and this one fails by GAINING one, and that an unauthorised
gain cannot be left to *"a property a backend can quietly not honour."*

**A backend cannot quietly not honour it.** R143(b), one ruling earlier, in this
lane, on this owner's instruction:

> Section 7's *"an unknown property is dropped silently, never rejected"* (R3)
> governs UNKNOWN properties -- third-party names a reader never heard of. A
> KNOWN property a target cannot honour is R22.4's case instead: *"an item whose
> capability is absent must not render as an ordinary live item."*

A registered property that a target cannot honour **refuses and names**. The
silent-drop the draft argued against had already been ruled out for exactly this
class of property, by the ruling immediately before it. The gain-versus-loss
distinction in section 1(a) of the draft is a true observation about the failure
mode; it is not a reason to grow the vocabulary, because R143(b) already
supplies the machinery that makes an unhonourable property visible.

This is the third prior-art miss on this lane, whose seed reads *"Twice this
lane has written a procedure for a mechanism that already existed."* It is now
three times, and the mechanism was one ruling old.

### (b) Why the owner's reading of "split" is the correct one

The instruction that opened the R77 candidates was literally **"R77-PROPERTY"**
(register row R143). R144 landed as a property. The register entry for R144
reads *"and splits it, because MEASURING the call sites showed it was not one
question"* -- so in this lane, one turn earlier, **"split" names the splitting of
a QUESTION, not of the vocabulary.** The author read the next instruction,
"split", against R85's kind-vs-property test instead of against the standing
ruling and the immediately preceding usage. The record does not support that
reading.

### (c) Provenance, which the property route wins on outright

Section 7: `PROPS` are **adopted, not invented.** This property is adopted --
name, place and mini-language all come from the corpus. It needs no rescue.

Contrast R143's `Scroll`, which measured **zero** corpus hits and had to borrow
R66's runtime-provenance route to enter at all. **This is the best-provenanced
property in the lane**, and the draft proposed to discard that in favour of a
kind name argued from wxWidgets' spelling -- which the draft itself conceded was
*"a weak argument."*

### (d) THE REVIEWABLE PART: the name, which has a problem the draft's name did not

Section 7 says adopt. The adopted name is `Style`. **`Style` is overloaded in
VFP** -- section 1(b)'s own table shows it on six baseclasses with six unrelated
value spaces. That is precisely the objection the draft used to reject `select`:
*"a word that means two things in one tree is the defect this house keeps
finding."*

Two readings, and this is the owner's call:

- **Adopt `Style` verbatim.** The overload is not a real ambiguity here, because
  in VFP `Style` is *already* kind-scoped -- it is only ever read against its
  baseclass -- and the design table carries `KIND` on the same row, so a reader
  never has to guess which `Style` it is holding. Cost: a reader scanning `PROPS`
  out of context sees a word that means six things.
- **Adopt the semantics, spell the name scoped.** Cost: section 7 says adopted,
  not invented, and a re-spelling is an invention wearing an adoption's clothes.

**Recommended: adopt `Style` verbatim**, on the ground that the overload is
resolved by a column the table already carries. Recorded as a recommendation,
not a decision.

**Values** are the same question in miniature. VFP's are numeric (`0`, `2`).
R143 chose words (`none | row | column | both`) over numbers. Adopting numerals
imports a two-valued sparse integer whose `1` does not exist; choosing words
invents. **Recommended: adopt `0 | 2` verbatim and let the contract's prose carry
the meaning**, because a reader who meets `Style = 2` in a `PROPS` memo and a
reader who meets it in a `.scx` should not have to learn two spellings. Also a
recommendation.

---

## 3. What this obliges

1. **The vocabulary does not change.** Section 4 stays at twenty. `choice` does
   not enter. `prove_r88.py` is unaffected either way -- a combo is not a
   container.
2. **Section 7 gains the property**, with its corpus provenance and its value
   space, subject to 2(d).
3. **Section 7 must also transcribe R143(b), and currently does not.** As
   printed today section 7 carries only the R3 silent-drop bullet. This ruling
   DEPENDS on R143(b), and a reader routed to the contract for *"what happens to
   a property my target cannot honour"* is still told the wrong half. **This is
   the fourth stale authority found in this lane in three days** and it is named
   here rather than left.
4. **The importer can now perform the split**, which the draft said it could not.
   `import_scx.py:22` maps `'combobox':'combo'`; it must read `Style` and resolve
   inheritance. Resolution of the 17 subclassed records against the corpus's
   class definitions:

   | parent class | defined in | `Style` | resolves to |
   | --- | --- | --- | --- |
   | `cbofontname`, `cbofontsize` | `samples.vcx` | 2 | fixed |
   | `basecombobox` | `BaseControls.vcx` | 2 | fixed |
   | `cboarray`, `cbooperators` | `bldquery.vcx` | 2 | fixed |
   | `cbofields` | `bldquery.vcx` -> `cboarray` | inherited | fixed, **two hops** |
   | `cbochoices` | `LibMember.vcx` | 2 (3 of 4 defs) | fixed |
   | `combodist` | `isapi.vcx` | absent | editable |
   | `_cbolookup`, `_urlcombobox`, `_cbodistinctvalues` | **not in corpus** | -- | **UNRESOLVABLE** |

   **88 of 93 resolve. 5 do not**, and those five are VFP's own FFC library
   classes, shipped with the product and absent from this corpus. Those five are
   **refused and named**, per R66's standard -- 33 grid objects measured, 16
   refused by name, before `grid` was mapped. The importer must not guess them.
5. **Four backends gain a reading**, and the two that cannot honour it refuse and
   name per 2(a). `uidef_tk.py:406` builds `ttk.Combobox(parent)`, which takes
   `state='readonly'`; `uidef_wx.py:277` can take `wxCB_READONLY` or `wxChoice`.
   `uidef_text.py:139` renders `[________ v]` on a character grid. **Whether a
   character-cell target can show the difference at all is NOT MEASURED here**,
   and neither is `uidef_html.py`. Both are owed before this is implemented.

---

## 4. What this does NOT do

- **Nothing is implemented.** No backend reads the property, no fixture uses it,
  the importer is unchanged, nothing was built or run. R85's standard is *built
  AND run, all four backends, one document*.
- **It does not patch the contract.** Sections 7 and 4 are untouched by this
  document; obligations 2 and 3 are what a patch would have to satisfy.
- **It does not revisit `list`.** A `list` and a fixed-set dropdown are different
  controls and this ruling assumes so without measuring whether the corpus
  agrees.
- **It does not reconcile the record counts.** Contract section 4 cites *"3,010
  measured object records"*; this scan counts **4,013** (3,350 `.scx`, 663
  `.vcx`). The 3,010 figure's filter is recorded nowhere, and it is the scan that
  reported no such property while reading this same corpus.

---

## 5. How to disprove this

- Show a target where a registered, known property genuinely *can* be dropped
  without refusing -- that would reopen 2(a) and put the KIND back on the table.
  It requires overturning R143(b) first.
- Show that `Style` on a combobox and `Style` on a checkbox must be read by one
  code path in this engine. That would make 2(d)'s overload a real ambiguity and
  force a scoped spelling.
- Show `list` already covers a fixed set with one visible row in a way all four
  backends honour. That would make even the property redundant.
- Measure the 5 unresolvable FFC classes from a VFP installation and find they
  are editable. That would not change the ruling, but it would shrink the
  refusal list to zero and is worth someone's ten minutes.

---

## 6. The withdrawn draft, recorded so a reader who saw it is not confused

An earlier draft of R145, dated the same day and **never committed**, ruled the
distinction a twenty-first KIND named `choice`, and stated in its section 2(c)
that *"nothing in this lane has measured whether the corpus carries that
distinction."* Section 1(b) above is that measurement. It was prompted by the
owner asserting this ruling's own first disproof condition, and it falsified the
draft's premise. The draft's file, `AIF120_CHOICE_KIND_V1.md`,
is deleted rather than superseded, because it never entered history and this
house has enough stale authorities already.
