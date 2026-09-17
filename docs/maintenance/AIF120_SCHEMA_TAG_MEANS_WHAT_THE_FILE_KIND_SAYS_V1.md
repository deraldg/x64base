---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260917-COWORK-005
  recorded_at_utc: 2026-09-17T16:24:54Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260917-001
  project:
    id: project.x64base.gui
    root: D:/code/ccode/gui
  git:
    branch: development
    baseline_commit: 1f7c559fe
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-09-17 -- "r824",
      then "c" on being offered three readings of what `tag=` means.
    scope: >
      Settles R82.4 by correcting its framing. Reads the save writer, the
      DTSHEMA contract, both shipped workspace files and the index containers
      behind them. NO CODE WAS WRITTEN.
  report:
    path: docs/maintenance/AIF120_SCHEMA_TAG_MEANS_WHAT_THE_FILE_KIND_SAYS_V1.md
    kind: ruling
---

# R148 -- `tag=` means what the file's own KIND says it means, and one writer has been ignoring that

Lane: AIF-120 (application-ui-dsl). Ruled by: `member.derald`.
Author: `member.ai.claude.cowork`.
Status: **review-needed** -- the author does not self-approve.
Settles **R82.4** by correcting its framing.

---

## 1. The ruling

Owner ruled **(c) -- carry both**: a workspace needs to say *how it should open*
AND *where it stood*.

**AND THE SPLIT ALREADY EXISTS, ONE LEVEL UP FROM WHERE IT WAS BEING LOOKED
FOR.** The author offered (c) as TWO FIELDS in one line. That was the worse
version of what was ruled. `cmd_workspace.cpp:110-113` already declares two file
KINDS, and the owner chartered them on 2026-08-24 (AIF-124):

>     DTSHEMA 2 -- AREA, RELATION, KEY. The DEFINITION. Relative paths, NO
>                  CURSOR, portable, and the one to commit.
>     DTSHEMA 3 -- adds FLAVOR / DBFROOT / IDXROOT / LMDBROOT (where it
>                  resolved from) and CURSOR / CURRENT (where it stood).

**So `tag=` needs no sibling field and no new vocabulary. Its MEANING FOLLOWS
THE DECLARED KIND OF THE FILE IT SITS IN:**

| file kind | what it is | what `tag=` means |
|---|---|---|
| `DTSHEMA 2` | **the DEFINITION**, the one to commit | the **INTENDED** order -- how this workspace opens |
| `DTSHEMA 3` | **the SESSION**, machine-specific by nature | the **ACTIVE** order -- where it stood |

Adopt, do not invent. Same rule R145 followed three days ago.

---

## 2. The defect, and it is one missing branch

`cmd_workspace.cpp:2371`, inside the AREA loop:

    std::string tag = getActiveTagSafe(A);

**The AREA loop never mentions `version`.** Line 2348 writes
`DTSHEMA 2` or `DTSHEMA 3` from the parameter, the v3 block below it adds
FLAVOR and the three roots -- and then the same loop writes the same
session-derived `tag=` into both.

**So every DTSHEMA 2 file carries one field of CURSOR STATE, in a format whose
own contract says NO CURSOR.** And v2 is *"the one to commit"*, so that session
artifact is in git.

### 2a. This explains both shipped files without either being a mistake

Measured at `1f7c559fe`:

- `dottalkpp/data/workspaces/mcc_x64.dtschema` -- `DTSHEMA 2`,
  `WSID F20260812T121051Z`, thirteen areas, **`tag=none` on every one**.
- `dottalkpp/data/workspaces/mcc_x32.dtschema` -- `DTSHEMA 2`, **no WSID line**,
  twelve areas, real tags (`BLDG`, `CLS_ID`, `CID`, `DEPT_ID`, `SID`, `MAJOR`,
  `ROOM`, `LNAME`, `TID`, `TERM`).

Both are honest about the SITTING they were saved from. Neither is honest as a
DEFINITION, because the writer never asked which it was producing. **R82.4 called
this "an asymmetry between two files, not a design decision." It is neither: it
is one writer ignoring the version it was handed.**

### 2b. The tags are on disk and unnamed -- so this is under-declaration, not absence

Read from the containers directly:

    x64/STUDENTS.cdx   2216 B   tags: DOB FNAME GPA LNAME MAJOR SID
    x64/BUILDING.cdx    296 B   tags: BLDG
    x32/STUDENTS.cnx   9664 B   tags: DOB FNAME GPA LNAME MAJOR SID RUN1

**`BLDG` is in the x64 BUILDING container -- the exact tag its x32 twin names.**
STUDENTS carries the same six on both sides. So `tag=none` is not "x64 has no
orders"; it is a definition declining to name orders that exist. That is why the
maintainer's transcript read `Order: ASCEND` with `Active tag : (none)`.

---

## 3. THE CLOSEOUT'S WARNING POINTS AT THE WRONG SAVE

`SESSION_CLOSEOUT_APPLICATION_UI_DSL_LANE_2026-09-16.md` puts R82.4 first and
says decide *"BEFORE the v3 save bakes it in"*, noting the v3 save has not
happened.

**V3 IS THE SAFE ONE.** A DTSHEMA 3 is chartered to record where the session
stood; `tag=` holding the active order is exactly right there, and a v3 save
bakes in nothing that does not belong to it.

**IT IS V2 THAT HAS BEEN BAKING A SITTING INTO A COMMITTED DEFINITION, on every
save, since the writer was written.** The deadline was real and pointed one file
kind away from the thing doing the damage.

---

## 4. What is owed

1. **Branch the writer on version.** v3 keeps `getActiveTagSafe`. v2 writes the
   INTENDED tag.
2. **Where v2's intended tag comes from, and this is the substantive question.**
   The cheapest defensible answer is **PRESERVE**: a v2 save should carry
   forward the tag the existing v2 file already declares rather than overwrite
   it from the session. **Had it preserved, x32's tags would have survived and
   x64's would never have become `none`** -- the defect is an overwrite, so the
   remedy is to stop overwriting. Alternatives: a human names them (twelve for
   MCC), or the structural tag in the container is adopted as a default. Not
   ruled here.
3. **What LOAD does with each kind** -- a v2 load SETS the declared order; a v3
   load RESTORES the cursor. Today neither is specified in the ruling record.
4. **Whether an existing v2 in the tree is repaired or re-saved.** Once (1) and
   (2) land, `mcc_x64.dtschema` still says `tag=none` thirteen times and nothing
   will change that but a decision about twelve tags.

## 5. Three things the "13 vs 12" summary flattened

- **It is 12 comparable areas plus one x64-only `TEST64`**, carrying
  `index=none | indextype=NONE`. The comparable set is 12-to-12.
- **x64 is CDX, x32 is CNX** -- different index backends, not only different
  tags. Any reconciliation that assumes one file is the other's twin is wrong
  about the backend before it is wrong about the tag.
- **x32 has no `WSID` line at all**, so the two files were not produced by the
  same code path, and the missing stamp is evidence rather than an oversight.

## 6. Not measured

- Whether the other six `mcc_x*.dtschema` copies under `dottalkpp/user/{default,
  derald,public}/workspaces/` have the same shape. They are dated 2026-05-04 and
  are a different size (1584 / 1613 bytes against 1058 / 1157), so they may
  predate this format entirely.
- Whether any OTHER v2 field is session-derived. `tag=` was found by reading the
  writer; the same loop also calls `getOrderNameSafe`, and whether an index FILE
  name is definition or session has not been asked.
- What a structural/primary tag means in this engine's CDX, which option (2c)
  would depend on.

## 7. How to verify

    sed -n '108,116p' src/cli/cmd_workspace.cpp      # the two kinds, chartered
    sed -n '2364,2372p' src/cli/cmd_workspace.cpp    # getActiveTagSafe, no version branch
    cat dottalkpp/data/workspaces/mcc_x64.dtschema   # DTSHEMA 2, thirteen tag=none
    strings -n 3 dottalkpp/data/indexes/x64/BUILDING.cdx | grep -E '^[A-Z]{3,}$'
