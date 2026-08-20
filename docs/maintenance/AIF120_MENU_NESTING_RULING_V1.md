---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-024
  recorded_at_utc: 2026-08-19T09:04:09Z
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
    baseline_commit: 799c6499f
  authorization:
    requested_by: maintainer (member.derald), in-session, standing "keep going" -- the
      .MNX -> UIDEF importer named as the next target, contract section 11 being the
      only part with no producer and no consumer.
  report:
    path: docs/maintenance/AIF120_MENU_NESTING_RULING_V1.md
    kind: ruling
---

# AIF-120 -- R18: the menu hierarchy is in the table, but not in a column

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

**Evidence tier: `runtime-proven`.** Both menus imported to UIDEF and one rendered
as a live Tk menubar under `xvfb`.
Evidence: `docs/maintenance/evidence/AIF120_uidef_menu_tk.png`.

Contract section 11 was the only part of gate 10 with neither a producer nor a
consumer. Both now exist: `gui/uidef/import_mnx.py` and
`gui/uidef/uidef_tk_menu.py`.

## 1. The `.MNX` structure, measured

| `OBJTYPE` | meaning |
| --- | --- |
| `1` | menu header, one per file |
| `2` | a **container** -- its name in `LEVELNAME`, its child count in `NUMITEMS` |
| `3` | an **item**, parented by its `LEVELNAME`, ordered by `ITEMNUM` |

## 2. The defect the first render exposed

The first importer treated every container as a top-level menu. Rendered, that
put `msysmenu` and `mGo` **side by side on the menubar**, when the real structure
is: `_msysmenu` holds one item, `Go`, and that item *opens* `_mGo`.

**The item-opens-submenu link is not a column.** Every non-empty field on the
opening item was inspected -- `OBJTYPE`, `OBJCODE`, `NAME`, `PROMPT`, `MESSAGE`,
`MARK`, `KEYNAME`, `KEYLABEL`, `LEVELNAME`, `ITEMNUM`, `LOCATION` -- and **none
names `_mGo`**. The relationship appears only in GENMENU's output:

```text
DEFINE PAD _msm_Go OF _MSYSMENU PROMPT "\<Go" COLOR SCHEME 3
ON PAD  _msm_Go OF _MSYSMENU ACTIVATE POPUP _mgo
DEFINE POPUP _mgo MARGIN RELATIVE SHADOW COLOR SCHEME 4
```

## 3. R18 -- the ruling

**R18. In `.MNX`, `OBJCODE = 77` marks an item that opens a submenu, and the
container that follows it in DOCUMENT ORDER is the submenu it opens. The link must
be resolved by order, never by name.**

Measured:

| file | items with `OBJCODE = 77` | containers besides `_msysmenu` | linked by order |
| --- | --- | --- | --- |
| `test_go.mnx` | 1 | 1 | **1 of 1** |
| `test_main.mnx` | **9** | **9** | **9 of 9** |

`OBJCODE = 67` is an ordinary command item (10 and 37 respectively); `78` appears
21 times in `test_main` and is **not decoded**.

**Why order and not name -- this is the load-bearing half.** Seven of the nine
openers in `test_main.mnx` carry a name like `_msm_file`, and pairing those with
`_mfile` by convention works. **Two carry no name at all**: the items prompting
`M\<acros...` and `\<Error Logs` have `NAME` empty, and their containers are
`_mMacros` and `_mErrorLog`. A name-keyed importer drops both silently.

That is **R5's lesson arriving in a second format**. R5 ruled that `.SCX` identity
is the dotted path and never `OBJNAME`, because `OBJNAME` repeats. Here the failure
is the sibling case: **the field is allowed to be empty.** Generalised: a
structural link must never be inferred from a field the format permits to be
blank, whether it repeats or vanishes.

## 4. What rendering confirmed

`test_main.mnx` -> UIDEF -> Tk: **1 root container, 9 cascades, 46 items, 12
separators**, and the menubar reads `File Edit Tools Program Favorites Window
Help` -- seven at top level, the two unnamed cascades correctly nested inside
others rather than promoted to the bar.

**R8 is confirmed at the pixel.** The `\<` mnemonic escape is positional, and it
rendered positionally: `F`ile, `E`dit, `T`ools, `P`rogram, `W`indow, `H`elp
underline the first letter, while **`F\<avorites` underlines the `a`**. The
importer carried the index; Tk honoured it. `\-` produced all 12 separators.

**R12.4 is confirmed by construction.** Zero UIDEF rows carry `ORIGIN`, in both
documents. The menu half of the design table has no geometry and needs none.

**And `NUMITEMS` is a declared count that checks.** Every container's `NUMITEMS`
matched its observed child count, in both files. That is the third place this
lane has found a self-checking count -- `RESERVED2` in `.SCX` and `.VCX`, now
`NUMITEMS` in `.MNX` -- which is a small argument that the format family expects
consumers to verify rather than trust.

## 5. What R18 does not settle

- **`OBJCODE = 78` is undecoded**, 21 records in `test_main.mnx`.
- **Two specimens, one author.** Both menus are from the same maintainer's VFP 9
  session. The corpus has nine more `.MNX` that were not run through this.
- **No `ON SELECTION` semantics.** Handlers were carried as references per R14 and
  wired to no-ops; nothing was invoked.
- **R9's imperative half untouched** -- `SET SKIP OF BAR`, `RELEASE POPUP` and the
  rest remain out of scope by ruling.
- **`SKIPFOR` is carried as opaque text** and not evaluated, per contract s13.

## 6. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
$env:X64BASE_ALLOW_DATA = "1"
git add gui/uidef/import_mnx.py gui/uidef/uidef_tk_menu.py
git add docs/maintenance/AIF120_MENU_NESTING_RULING_V1.md
git add docs/maintenance/evidence/AIF120_uidef_menu_tk.png
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git status --short -uall
git commit -m "AIF-120: R18 -- .MNX submenu links resolve by OBJCODE 77 plus document order, never by name; section 11 exercised end to end"
Remove-Item Env:\X64BASE_ALLOW_DATA
```
