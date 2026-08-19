---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-064
  recorded_at_utc: 2026-08-20T02:00:00Z
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
    baseline_commit: 3456745b7
  authorization:
    requested_by: maintainer (member.derald), standing in-session -- gate 11's
      nearest fix, and the one piece of outstanding work with no prior art.
  report:
    path: docs/maintenance/AIF120_FONT_EMPHASIS_V1.md
    kind: ruling
---

# AIF-120 -- R56: a font is name, size, weight and slant, and the table was carrying two of them

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-20.

Gate 11's nearest fix, from R28: *"Name the `FONT` row's properties."* Naming them
turned out to require adding two.

**Prior art, checked first this time** (R54's house rule): there is no font code
anywhere in `include/` or `src/`, and no mention of fonts, typefaces, bold or italic
in `docs/ui/`. This is the one outstanding item in the lane with nothing to reuse.

## 1. What was being dropped

```
objects with a PROPERTIES memo : 3180
  declare FontName             : 1688
  declare FontBold             : 561   of which .T. : 158
  declare FontItalic           :   3   of which .T. :   3
```

**161 corpus objects state an emphasis the UIDEF table discarded entirely.** A bold
heading and the body text beneath it, at the same family and size, resolved to one
`FONT` row and rendered identically on every backend.

The contract's own section 14 had recorded the symptom -- *"`fontbold`/`fontitalic`
are in neither, so the `FONT` row is the incomplete one"* -- without a measurement
attached, and it sat there from R24 until now.

## 2. R56.1 -- a font's identity is all four components

`FONT` rows now carry `Name`, `Size`, **`Bold`**, **`Italic`**, `Metrics`, and two
objects share a `FONTREF` only when all four agree. Contract section 7b states them,
which is gate 11's fix 1 discharged.

## 3. R56.2 -- the object is the authority, and the cache must not be decoded

The source font-cache line looks like `Arial, 0, 9, 5, 15, 12, 32, 3, 0`. Field 1 is
the name, field 3 the size. **Field 2 looks exactly like a style bitmask**: across
every cache line in the corpus it takes the values 0 (390), 1 (35), 4 (2), 32, 3, 128
and 2 -- and `3` is precisely where `bold|italic` would fall if bit 0 were bold and
bit 1 italic.

I nearly ruled that. Then correlated it against the objects that actually declare
`FontBold = .T.`:

```
  cache line has bit 1 set   : 33
  cache line does NOT        : 85
  no matching cache line     :  8
```

**Agrees 33 times, disagrees 85.** Whatever field 2 is, a reader who decodes it as
bold will be wrong more than twice as often as right. `Metrics` therefore stays
carried and uninterpreted, section 7b says so explicitly, and the ruling is that the
**object's own `FontBold`/`FontItalic` is the authority** -- so a cache-derived row is
always `Bold = .F.`, and an object declaring emphasis gets a derived row of its own.

Three data points and a tidy pattern were nearly enough to put a wrong rule in the
contract. The corpus is what stopped it.

## 4. Runtime-proven on all three font-bearing backends

Four authored rows -- plain, bold, italic, bold+italic -- at one family and size:

```
Tk        L1  family=Liberation Sans size=12 weight=normal slant=roman
          L2  family=Liberation Sans size=12 weight=bold   slant=roman
          L3  family=Liberation Sans size=12 weight=normal slant=italic
          L4  family=Liberation Sans size=12 weight=bold   slant=italic

HTML      font-family:Arial;font-size:12pt
          font-family:Arial;font-size:12pt;font-weight:bold
          font-family:Arial;font-size:12pt;font-style:italic
          font-family:Arial;font-size:12pt;font-weight:bold;font-style:italic

wx C++    wxFont(12, wxFONTFAMILY_DEFAULT, wxFONTSTYLE_NORMAL, wxFONTWEIGHT_NORMAL, false, "Arial")
          wxFont(12, wxFONTFAMILY_DEFAULT, wxFONTSTYLE_NORMAL, wxFONTWEIGHT_BOLD,   false, "Arial")
          wxFont(12, wxFONTFAMILY_DEFAULT, wxFONTSTYLE_ITALIC, wxFONTWEIGHT_NORMAL, false, "Arial")
          wxFont(12, wxFONTFAMILY_DEFAULT, wxFONTSTYLE_ITALIC, wxFONTWEIGHT_BOLD,   false, "Arial")
```

The Tk row is read back from the toolkit's own `font actual`, not from the
generator's intent -- the distinction R40.2 made about compiling versus rendering.

The character-cell backend has no fonts and refuses them already (R35.3); nothing
changes there, and that refusal is now the contract's stated requirement for any
target that cannot render emphasis.

Corpus regression: 30 forms imported, 0 failures, 80 `FONT` rows of which 11 carry
emphasis. Evidence tier: **runtime-proven**.

## 5. Still open

- **Underline and strikeout are still dropped.** `FontUnderline` was not measured and
  is not carried. The same argument that justified `Bold` and `Italic` applies, and
  the same caution applies to guessing them out of `Metrics`.
- **`Metrics` remains undecoded.** Fields 2 and 4 through 9 have no stated meaning.
  Section 7b now says so rather than leaving a reader to assume.
- **No backend renders a font it cannot find.** `FONTREF` resolution falls back to the
  target default silently when the family is absent from the system; nothing reports
  the substitution, so `Liberation Sans` standing in for `Arial` above passed without
  comment.
- **R55.2 and R55.3 remain owner decisions**, and R53.4 still has no implementation.

## 6. Good Neighbor note

- **What changed.** `tools/uidef/import_scx.py`: `FONT` rows carry `Bold` and
  `Italic`; emphasis keys a derived row. `tools/uidef/uidef_tk.py`,
  `uidef_html.py`, `uidef_wx.py`: each applies them.
  `docs/maintenance/AIF120_DESIGN_TABLE_CONTRACT_V1.md`: new section 7b.
- **Whose area.** AIF-120's own, entirely. Nothing outside `tools/uidef/` and
  `docs/maintenance/` was touched, and nothing outside the lane was read except to
  confirm no font prior art exists.
- **What authorization.** Maintainer (member.derald), standing in-session.
- **How to verify or undo.** Verify: author a table with four `FONT` rows differing
  only in `Bold`/`Italic`, render on Tk and read back `font actual`, and inspect the
  HTML and wx output. Undo: removing `Bold`/`Italic` from the importer restores the
  collapse of emphasis onto one row, which no test outside this ruling detects.

## 7. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add tools/uidef/import_scx.py
git add tools/uidef/uidef_tk.py
git add tools/uidef/uidef_html.py
git add tools/uidef/uidef_wx.py
git add docs/maintenance/AIF120_DESIGN_TABLE_CONTRACT_V1.md
git add docs/maintenance/AIF120_FONT_EMPHASIS_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R56 -- the FONT row carries emphasis; 161 corpus objects had it dropped, and the cache field that looks like a style flag is not one"
```
