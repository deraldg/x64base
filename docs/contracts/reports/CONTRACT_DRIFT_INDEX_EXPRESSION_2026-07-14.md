# Contract Drift Report — Index Key Is A Field, Not An Expression

Status: **repaired**.
Found: 2026-07-14.
Repaired: 2026-07-14.
Owning lifecycle: DotTalk++ SDLC.
SDLC lane: maintenance.
Risk class: documentation-only (no source or runtime behavior changed).

## The Drift

Eight documentation files advertised FoxPro expression indexes as if they were
DotTalk++ syntax:

```text
STUDENTS:  INDEX ON UPPER(LNAME+FNAME) TAG NAME
CLASSES:   INDEX ON TERM+CID+STR(SEC,2) TAG TCSEC
```

DotTalk++ `INDEX ON` takes a **field key**, not an expression. The composite
tags `NAME` and `TCSEC` cannot be built and have no DotTalk++ equivalent.

## Authority

Per `docs/governance/authority_order.md` — runtime proves, source defines, HELP
explains. All three agree, and the documentation was the outlier:

| Authority | Evidence |
| --- | --- |
| Runtime | `INDEX USAGE` readback, 2026-07-14: `INDEX ON <field> TAG <name>` |
| Source | `src/cli/cmd_index.cpp` usage contract — `<field>`, not `<expr>` |
| HELP / manual | `DOTTALKPP_COMMAND_REFERENCE_GUIDE_V1.md`: *"using a field key"* |
| Corpus | 40+ `INDEX ON` statements across `dottalkpp/data/**/*.dts`. **Every one a bare field. Zero expressions.** |

The offending line in each file read `Suggested indexes (create in FoxPro)`. It
was FoxPro advice about a FoxPro-origin dataset — historically accurate, and
never a DotTalk++ claim. It was simply read as one.

## Why It Persisted

The claim was plausible to anyone who knows xBase, and it sat in a *data*
directory rather than a *contract* directory, so no contract review covered it.
It survived because it looked right, not because anyone checked it.

An AI partner working this repo on 2026-07-14 drafted DotScript that would have
built two nonexistent tags, on the strength of this file. Caught before
execution, but only because the maintainer redirected it to read the `.dts`
corpus rather than trusting the schema notes.

## Files Repaired

Thirteen files carried a byte-identical block. The first pass found only eight;
a verification sweep across the whole tree found five more, including one under
`src/`. Recorded because the under-count is itself the lesson: a grep scoped to
the directory where you *expect* the drift will confirm your expectation.

Data and help lane:

- `dottalkpp/data/dbf/mcc_schema.txt`
- `dottalkpp/data/dbf/community_college_schema.txt`
- `dottalkpp/data/dbf/community_college_x64_schema.txt`
- `dottalkpp/data/dbf/x64/community_college_x64_schema.txt`
- `dottalkpp/data/dbf/x64/Original Vector Name Sizes/community_college_x64_schema.txt`
- `dottalkpp/data/dbf/x32/README.txt`
- `dottalkpp/data/help/DATA_INDEX_README.txt`
- `dottalkpp/data/help/V32_help/DATA_INDEX_README.txt`

Found only on the verification sweep:

- `src/data/DATA_INDEX_README.txt`  ← **under `src/`**
- `mcc/community_college_schema.txt`
- `mcc/README.txt`
- `dottalkpp/docs/My_Comminty_College_README.txt`
- `dottalkpp/docs/My_Comminty_College_Data_Schema_README.txt`

## Not Repaired — Generated Artifacts

Two files still contain the old text and were **deliberately left alone**:

- `dottalkpp/docs/generated/proposals/source_comment_metadata_create_review_v1/source_comment_metadata_create_syntax_evidence_v1.csv`
- `dottalkpp/docs/generated/proposals/source_comment_metadata_create_review_v1/source_comment_metadata_create_syntax_focused_v1.csv`

These are **generated** proposal artifacts. Hand-patching generated output would
falsify the provenance trail — the CSV is a faithful record of what the source
text said when the scan ran. They will carry the correction when regenerated.

Per `AI_ASSIMILATION_BOOK_V1.md` §13: *"Do not assume generated output is junk."*
The corollary holds too: do not hand-edit it into agreement with a later truth.

## Repair Shape

The FoxPro block is **retained**, relabelled `HISTORICAL — FoxPro 2.6a origin.
Retained as provenance. NOT DotTalk++ syntax.` This is a FoxPro-lineage project;
deleting the original would destroy real provenance. It is preserved and
correctly classified rather than erased.

A `DOTTALK++ — current, contract-backed` block now sits beside it, giving the
field-key tags and the correct build path per lane.

## Second Contract Registered

Repairing this surfaced a related rule that was also undocumented outside
source — the **index lane split**:

| | x32 / v32 (MS-DOS) | x64 / v64 / v128 |
| --- | --- | --- |
| Container | **CNX** — sorted index by tag | **CDX** |
| Runtime tag mutation | **NOT supported** | **Supported** |
| Rebuild | `REINDEX CNX` — batch only | `BUILDLMDB` |
| LMDB backing | none | `lmdb/<slot>/<stem>.cdx.d/` |

Runtime evidence, 2026-07-14: `USE USAGE` (*"x64/v128 tables prefer CDX. x32
tables prefer CNX, then INX"*), `REINDEX` (*"REINDEX ALL -> v32 table: INX +
CNX, v64 table: CDX"*), `CNX USAGE`, `CDX USAGE`, `BUILDLMDB USAGE`.

Also clarified, because it was being conflated:

- `INDEX ON` builds an **INX** file. It does **not** build CDX/CNX tags.
- `BUILDLMDB` **builds** the LMDB store from a CDX container.
- `SETLMDB` only **selects** an already-built LMDB ordering.

## Registry

Both rules added to `CONTRACT_REGISTRY_V1.md` as **Runtime-proven**:

- Index Key Is A Field, Not An Expression
- Index Lane Split (CNX x32 / CDX x64)

## Residual Risk

Low. No source or runtime behavior changed; only documentation was corrected.

Open: the eight repaired files are *data-directory* documentation and are not
covered by any automated drift check. `tools/contracts/contract_scan.py` scans
contract-like docs and source annotations; it does not scan `dottalkpp/data/**`
prose. A recurrence in that tree would not be caught. Extending the scanner to
flag `INDEX ON <expr>` patterns outside the corpus is a candidate follow-up, not
done here.
