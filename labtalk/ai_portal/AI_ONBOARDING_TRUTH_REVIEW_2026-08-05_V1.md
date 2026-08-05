# AI onboarding truth review (2026-08-05)

Owner: `member.derald`
Author: `member.ai.claude.cowork`
Trigger: environment mistakes during the flush v4 / Phase 8 session -- wrong on
x32-vs-x64 and memo extensions, on treating DBF/CDX/CNX data, and fumbling the
authority roots the owner assumed were baked in.
Class: onboarding/assimilation review (report-only; no onboarding surface changed
here, recommendations only).

## What went wrong this session

- Fumbled the authority roots and promotion model: confused `D:\code\ccode`
  (development, sole authoring) with the site tree, and the sandbox mount path with
  the Windows path when editing the website.
- Used a v32-era DBF reader (`dbfread`) on x64 tables and hit unresolved memos,
  not knowing x64 memo text is a MemoManager/x64-sidecar concern, not classic `.dbt`.
- Undercounted the reference authorities as "four" (dotref/foxref/edref/SYSFUNC);
  the guards later showed pshell_ref, sql_ref, and devref too.
- Hand-edited generated website pages before reading the website page-class matrix.

## Two failure modes (the important distinction)

### 1. Baked in, but unread (assimilation was skipped)

These truths ARE in the onboarding surface. The failure was not reading it.

- `AI_TIER1_SEED_V1.md` Section 1 "Where you are (invariant)" is an explicit table:
  `D:\code\ccode` = `development`, sole development/authoring; `C:\x64base` = `main`,
  sterilized publication staging; `D:\dev\x64base-site` = website source tree.
  Binding: `docs/contracts/REPOSITORY_ROLE_AND_PROMOTION_CONTRACT_V1.md`.
- Section 2 names "DBF/CDX/CNX/LMDB data, HELP tables, metadata and generated
  catalogs, manuals" as report-only unless the task says otherwise.
- `CLAUDE.md` line 3 mandates it: "Start with `labtalk/ai_portal/AI_TIER1_SEED_V1.md`."
- `AI_README.md` records that enumerating/building against `main` is "a hard
  onboarding failure (observed)" -- the exact trap.

Root cause: the session did not perform the mandated Tier 1 assimilation (read the
seed / `MAINT AI ASSIMILATE`) before acting. The authority roots were also present
in the auto-injected system context, so this is an assimilation failure, not an
absence of truth.

### 2. Genuinely missing from fast-start (a real content gap)

These truths are NOT in the Tier 1 seed or the portal onboarding at all.

- x32 vs x64 DBF formats; the memo extension distinction (`.dbt` v32 vs the x64
  MemoManager sidecar); CDX/CNX/LMDB index specifics.
- They live in the developer manual: `docs/manuals/developer/dev/dev-08-dbf-x32-x64-formats.md`
  (x64 geometry, first byte `0x64`, "memo fields require MemoManager-aware
  documentation"), dev-09 (indexing), dev-10 (memo system). The authoritative
  behavior is in source (`src/cli/cmd_use.cpp`, the MemoManager path).
- Aggravating: `dev-08` is currently UNTRACKED/candidate, so even the manual page
  is not a stable committed reference, and it self-labels the memo area as
  under-documented.

Root cause: no fast-start surface points a working session at the format/memo
truth, so an agent doing DBF I/O (the harvest exporter) proceeds blind and reaches
for a v32 reader.

## Why the owner "thought it was baked in"

Both readings are partly right. The **roots** are baked in (Tier 1 Section 1 plus
the auto-injected context) -- the failure was skipped assimilation. The
**format/memo** truths are not baked into any fast-start surface -- a genuine gap.

## Recommendations (fixes, not yet applied)

1. **Enforce session-start assimilation.** Read `AI_TIER1_SEED_V1.md` (per CLAUDE.md)
   or run `MAINT AI ASSIMILATE` before acting. Highest-leverage fix: it prevents the
   authority-root/promotion fumbles by construction.
2. **Add an "engine format invariants" pointer to the Tier 1 seed** (invariant +
   pointer, no perishable detail): x32 vs x64; x64 memo text is a MemoManager /
   x64-sidecar concern, NOT classic `.dbt`; CDX/CNX/LMDB are the index/memo family;
   when reading or writing DBF programmatically, use the native x64 path
   (`cmd_use.cpp`), never a v32 reader. Pointer to dev-08/09/10 and the MemoManager.
3. **Track dev-08 (and 09/10)** so the format truth is a stable committed reference,
   and resolve its "memo requires MemoManager-aware documentation" gap from source.
4. **Add the reference-authority family as a fast-start pointer:** dotref, foxref,
   edref, pshell_ref, sql_ref, devref, plus SYSFUNC for functions -- each owning its
   namespace; verify with `refcheck_v1.py` / `normcheck_v1.py`.
5. **Website page-class rule** (already added to the flush cookbook as rule 11):
   consult `x64base-site` `website-documentation-matrix.mdx` before editing; never
   hand-edit `generated`/`derived`/`maintained_current` regions.

## Teaching note

This is the same lesson as the flush lane's north star, one level up: a truth that
exists in one place (the Tier 1 seed, the developer manual, the source) is worthless
to a session that does not cross the bridge to it. Baked-in is not the same as
reached. The fix is both -- put the missing truths on the fast-start bank, and
actually assimilate before acting.
