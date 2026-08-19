---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-018
  recorded_at_utc: 2026-08-19T01:35:24Z
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
    requested_by: maintainer (member.derald), in-session, "keep going" -- continuing
      corpus discovery after R14.
  report:
    path: docs/maintenance/AIF120_SHARED_PROPERTY_LANGUAGE_V1.md
    kind: ruling
---

# AIF-120 -- R15: the formats share TWO layers, not one

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

Every measurement in this lane so far has found **divergence**. R10 concluded
that across the designer formats "only the DBF layer is shared", and the `.FRX`
measurement made that more true, not less: `.SCX` positions with `Top`/`Left`,
`.MNX` has no geometry at all, `.FRX` uses `VPOS`/`HPOS`; fonts live in a
reserved record, a reserved column, or three dedicated columns depending on which
file you open.

This is the first measurement that found convergence, and it is load-bearing for
gate 10.

## 1. The measurement

Every column of every record in the corpus, tested for whether its value parses
as two or more `name = value` lines. 195 `.SCX`/`.VCX`, 14 `.FRX`, 9 `.MNX`.

| format | column carrying property text | records |
| --- | --- | --- |
| `.SCX` | **`PROPERTIES`** | 2,967 |
| `.VCX` | **`PROPERTIES`** | 495 |
| `.FRX` | **`EXPR`** | 55 |
| `.MNX` | -- | 3, incidental |

Three of the four formats carry a `name = value` property mini-language. They put
it in **different columns**, which is why it was invisible until every column was
tested rather than the expected one.

## 2. And the VOCABULARY is shared too, for the sub-objects the formats share

A `.FRX` carries a DataEnvironment (`OBJTYPE 25`, once per file) and its cursors
(`OBJTYPE 26`), exactly as an `.SCX` does. Their property keys:

| | keys |
| --- | --- |
| shared by both | `alias`, `cursorsource`, `database`, `name`, `top`, `left`, `height`, `width`, `order` |
| `.SCX` only | `buffermodeoverride`, `exclusive`, `readonly` |
| `.FRX` only | `childalias`, `parentalias`, `childorder`, `relationalexpr`, `onetomany` |

**Nine keys shared, and the divergences are semantically explicable rather than
arbitrary:** a form edits rows, so it needs buffering and locking; a report walks
master-detail, so it needs relation keys. Neither format invented a different
spelling for the concepts they have in common.

A `.FRX` cursor record, verbatim from the `EXPR` column:

```text
Top = 10
Left = 20
Height = 293
Width = 118
Alias = "employee"
Database = ..\..\data\testdata.dbc
CursorSource = "employee"
```

That is indistinguishable in form from an `.SCX` cursor's `PROPERTIES` memo.
Note also `Database = ..\..\data\testdata.dbc` -- **relative-to-document
addressing**, the same convention the save round-trip proved for `.SCX`
`CursorSource`, appearing independently in a second format.

## 3. R15 -- the ruling

**R15. The designer formats share two layers, not one: the DBF container, and a
`name = value` property mini-language with a shared key vocabulary for shared
sub-objects. Gate 10 adopts that mini-language as the design table's property
encoding rather than inventing one, and adopts its key names where a concept
already has one.**

R10 is amended, not contradicted. R10 is about **structure** -- parenting,
geometry vocabulary, band-versus-container -- and remains correct and now
better-evidenced. R15 is about **payload**, and says the payload layer converges
where the structural layer diverges.

Three consequences.

**R15.1 -- gate 10 has less to invent than it looked.** The charter's plan was a
documented table schema. Half of that schema is a property encoding, and there is
a shipped one with three format's worth of precedent and a shared vocabulary. The
R8 pattern a third time: adopt what exists.

**R15.2 -- per-format mapping is a COLUMN mapping, not a language mapping.**
Importing `.SCX`, `.VCX` and `.FRX` properties needs one parser and three
pointers -- `PROPERTIES`, `PROPERTIES`, `EXPR`. That is a much smaller import
surface than R10's structural divergence implies, and it is the practical reason
this project's own `read_vfp_binary.py` generalised to 195 unseen files without a
failure.

**R15.3 -- `.MNX` is the genuine outlier and should be stated as one.** It carries
no property text at all: it is purely columnar, with `PROMPT`, `KEYNAME`,
`SKIPFOR` and the rest as real DBF fields. R8 already ruled the lane adopts the
menu vocabulary as-is; R15 explains why that ruling cannot be generalised to the
other formats -- menus are the one designer format with no property sub-language
to share.

## 4. How this was nearly missed, and the method that found it

The property language was found by testing **every column of every record**
rather than the column the lane expected. Had the scan looked only where `.SCX`
keeps properties, `.FRX` would have reported "no property text" and the
convergence would have been recorded as more divergence.

That is the third time in this session the same method has paid: the font metrics
table (M5) was in a record the parser stepped over, `RESERVED4` was in a column
the sweep did not list, and the property language was in a column that differs
per format. **The lane's own trap -- a search shaped by the object you have
cannot find an object with a different schema -- has a cheap general remedy on a
DBF: enumerate the columns instead of naming them.**

## 5. What R15 does not settle

- **`.MNX`'s exclusion is measured, not explained.** Whether menus lack a property
  language because they predate it or because they never needed one is unknown.
- **The `.FRX` `OBJTYPE` enum is partly decoded.** Settled by column evidence:
  `1` page-setup header (14 of 14 files), `5` literal text, `8` a data
  expression, `25`/`26` the DataEnvironment and its cursors, `18` report
  variables, `17` a picture field. Narrowed since: **`9` is a band** -- 67
  records, `HEIGHT` set with no `VPOS`/`HPOS`, `OBJCODE` populated in 64 of 67,
  and 67 bands across 14 files is a plausible per-report count; **`6` is a rule or
  line** -- `PENSIZE` and `PENPAT` on all 32, one sample 6.77in wide by 0.02in
  tall; **`7` is a filled box** -- `PENSIZE`, `PENPAT`, `FILLPAT` and `FILLRED`
  together, 15 records. Still **not** decoded: `23` (74 records, pen colour and
  font on every one) and `10` (2 records, `VPOS`/`HPOS` and nothing else).
- **No `.PJX`, `.LBX` or `.DBC` measured.** The interchange table in the charter
  names more formats than this lane has opened.

## 6. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git add docs/maintenance/AIF120_SHARED_PROPERTY_LANGUAGE_V1.md
git add docs/maintenance/AIF120_METHOD_CODE_SCOPE_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git status --short -uall
git commit -m "AIF-120: R15 -- three of four designer formats share a name=value property language with a shared key vocabulary; R14 confirmed on .VCX"
```
