---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-094
  recorded_at_utc: 2026-08-21T00:40:00Z
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
    baseline_commit: fdacdbfe9
  authorization:
    requested_by: steward (member.derald), in-session -- "number 4", the smaller
      items left open by R85, of which the first was a property R85 itself
      invented and no backend reads.
    scope: >
      Close the design table's PROPERTY vocabulary per RECKIND and report an
      unknown key. Writes gui/uidef/ and docs/ only.
  report:
    path: docs/maintenance/AIF120_PROPERTY_VOCABULARY_V1.md
    kind: ruling
---

# AIF-120 -- R86: the vocabulary is three vocabularies, and it has one dead word

**Status: review-needed.** The author does not self-approve.

## 0. The one-paragraph version

R85 argued that a KIND beats a property because an unknown KIND is REFUSED and an
unknown property is silently ignored -- and then, in the same unit, put
`Multiline = true` into a fixture, where nothing read it and nothing said so. This
ruling closes the property vocabulary and reports an unknown key. Measured across
**29 documents and 297 rows: it fires exactly once**, on the word R85 invented.

## 1. The ruling

**R86. The design table's PROPERTY vocabulary is closed and keyed by RECKIND. A
key outside it, on a row this lane authored, is REPORTED.**

    DOC   sourcefile contract version title origin kind
    FONT  name size metrics bold italic
    OBJ   caption columns columnwidths fill filter mask minpane order
          readonly rowlimit shows weight

`multiline` is deliberately absent from OBJ. It goes in when the four backends can
each say what they do with it -- putting it in now on the strength of wanting it
is the same silence, performed by the check meant to break it.

**Rows whose PROVENANCE is `imported` are exempt.** They carry what the source
record carried, and that is preservation, not a claim.

## 2. Why REPORT and not REFUSE

R85 refused an unknown KIND. Symmetry would refuse an unknown property. The
asymmetry has a reason and it is not taste: **an unknown KIND cannot be drawn at
all, while an unknown property loses a modifier on an object that still renders.**
This lane already has a word for that outcome -- R80 and R81 report a DROPPED
Weight rather than refusing the document -- so an unknown property joins the
reports rather than inventing a third policy. Silently ignored becomes NAMED.

## 3. The measurement, and my first attempt at it was wrong

The first scan asked "which properties does no backend read" by matching
`pr.get('...')` across the four backends and the checker. It reported **128
distinct dead properties** and was wrong twice over:

- It could not see a property reached any other way. FONT rows are read through
  the font machinery (`fontobj`, `fontcss`), never through an object's PROPS, so
  `Name`, `Size` and `Metrics` looked dead and are not.
- It had no idea which RECKIND a key came from. A DOC row's `Version` is document
  metadata read by a person; it is not an object property that no target
  implements.

**A search shaped by the object you have cannot find an object with a different
schema.** The house doctrine, earned this time on my own evidence rather than on
someone else's code -- and the second time this lane has caught a whitelist-shaped
scanner narrowing the question (R81.2 was the first).

Grouped by RECKIND and by PROVENANCE, the real picture:

| PROVENANCE | unread occurrences | distinct keys | what they are |
|---|---|---|---|
| `imported` | 404 | 116 | VFP source records preserved verbatim -- `oldsetdelete`, `viewtype`, `cmdprev.enabled` |
| `authored` | 34 | 9 | all DOC or FONT metadata -- `contract`, `version`, `title`, `name`, `size` |
| `measured` | 4 | 2 | `sourcefile` (DOC), and **`multiline`** |

One dead word in the corpus, and it is mine.

## 4. Proof

- **Positive:** `P8_splitter_nested.DBF` reports
  `NOTE  OBJ LOG states Multiline`. It is the only hit in 29 documents.
- **Negative control:** an invented `GravityHint = 3` added to an authored row is
  reported by name, then removed; `author_cases.py` restored and verified by md5.
- **No false positives:** the 120 `imported` rows carrying 116 distinct source
  properties produce nothing, which is the exemption working rather than absent.

## 5. What this leaves open -- item 4, parked by the steward

Three things found by the same survey, none of them built here:

1. **`Multiline` and `ReadOnly` on a `text` control.** `ReadOnly` is real
   vocabulary but has only ever meant contract 4b(b) on a FRAME kind; on a `text`
   it is a different claim and no backend reads either word. P8 states both and
   claims `PROVENANCE: measured`, transcribing
   `wxTE_MULTILINE|wxTE_READONLY|wxTE_RICH2`.
2. **`ColumnWidths` is validated and rendered by NOTHING.** The checker counts it
   against BINDING -- `P5_widths_mismatch` is refused, `P6_widths_ok` passes --
   and no target emits a column width. A document is refused for getting wrong a
   number no screen uses. That is the sharpest instance of the pattern this
   ruling is about, and the checker is the one doing it.
3. **Tk's `pack` expand is a boolean and loses R79's ratio** (R80 section 4).
   `grid()` carries it. Open since R80.

## 6. Good Neighbor note

- **What changed:** `gui/uidef/manifest.py` only -- one constant, one collection
  loop, one report. No backend, no fixture, no gate.
- **Whose area:** AIF-120, lane `application-ui-dsl`.
- **What authorization:** steward, in-session, "number 4".
- **How to verify:** `python3 manifest.py P8_splitter_nested.DBF` -- expect the
  single `R86` NOTE; run it over the other 28 documents and expect none.
- **How to undo:** revert. The check is additive and advisory; it refuses nothing
  and changes no output any target produces.
