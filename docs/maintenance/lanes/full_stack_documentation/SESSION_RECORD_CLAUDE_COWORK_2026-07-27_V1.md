# Session record -- Cowork, 2026-07-27

- **Run**: DOCFLUSH-20260722-001 · **Member**: member.ai.claude.cowork
- **Lanes**: AIF-065 (closed), AIF-067 (in progress)
- **Branch**: development · **Purpose**: resume without re-deriving anything

---

## Read these first, in this order

1. `docs/ai-friendly/ENTITY_LIFECYCLE_AND_THE_BRIDGE_V1.md` -- the model everything
   else now hangs off. Sections 0, 2b, 2c, 2d are new today.
2. `docs/maintenance/SUBCOMMAND_IDENTITY_CONTRACT_LANE_V1.md` -- AIF-067 lane,
   including sections 9a-9e (fixture, dead registrations, shim, DDICT turnover).
3. `docs/maintenance/LMDB_MAPSIZE_OVERRIDE_LANE_V1.md` -- AIF-065, closed, kept
   because the method notes are the transferable part.
4. `labtalk/lessons/career/discovery_by_documentation_v0.md` -- thesis evidence.

## State

**AIF-065 CLOSED.** `BUILDLMDB`'s size ladder was parsed, echoed, written, then
overridden to 1 GiB on index attach. Fixed with `mdb_env_set_mapsize(env_, 0)` at
`cdx_backend.cpp` and `lmdb_backend.cpp`. Verified controlled: SYSARGS
33,554,432 -> 1,073,741,824 pre-fix, 33,554,432 -> 33,554,432 post-fix.
`BUILDLMDB CLEAN` now discards the superseded environment (`ARCHIVE` opts in).

**AIF-067 IN PROGRESS.** 31 `@dottalk.subusage` contracts on the SET ladder;
`SYSSUBCMD` generated and seeded (31 rows); `SET USAGE` generated in both copies;
`SYSCMD` generator built and NOT yet seeded.

```
stack_audit   WARN 18-20 range, FAIL 0, 1 expected (cmd_area51 fixture)
SYSCMD        live 203  ->  generated 213
entity_stages 1036 entities: idea 813, source_defined 223, catalogued 199
LMDB tree     73 GB, 63 containers still at 1 GiB (reclaim not started)
```

## Next actions, in order

1. **Seed `SYSCMD`.** `python tools\fullstack_docs\generate_syscmd.py --root . --write`
   then run the emitted `SYSCMD_SEED_v1.dts`. Expect 213 rows. Ten rows LEAVE the
   table by design -- `DDICT` (turned over) and nine `SET` subcommands whose home
   is `SYSSUBCMD`. Verify `USER` and `AREA51` are present afterwards.
2. **Triage the 9 identity errors** -- contracts naming something unregistered.
   `CATALOGCANARY` names its handler, not its command (`CANARY`). `POLLING` is a
   SET subcommand. The rest need individual checks. Do NOT batch-fix.
3. **Reclaim the LMDB tree.** 63 containers at 1 GiB; rebuild at proper rungs,
   delete the 25 archives. Single pass now that `CLEAN` discards. ~55 GiB.
4. **`dotref`** -- regenerate from the completed catalog; fix `SIMPLEBROWSER` /
   `SMARTBROWSER` (should be `SIMPLEBROWSE` / `SMARTBROWSE`).
5. Then HELP coverage, then the manual's `greenfield` binding decision.

## Owed decisions (maintainer)

- `@dottalk.pdlc` marker: proposed, not ratified. Applies to ~6 zero-byte entities.
- `cmd_ -> app_` rename: ten implemented apps, contracts already exist. `cmd_cobol
  -> app_cobol` nominated first (runtime-proofed).
- `mapsize_explicit` rebuild rule: flag exists at `cmd_buildlmdb.cpp`, still
  `(void)`'d.
- Whether `BUILDLMDB CLEAN` should discard before or after a successful rebuild.

## Traps that cost time today -- do not re-learn these

- **`datarun.ps1` runs with cwd = `dottalkpp\data`.** Relative output paths
  retarget silently and a failing `Tee-Object` aborts the pipeline before the
  shell runs. Use absolute paths.
- **A null probe and a negative result look identical.** State what success looks
  like IN THE TRANSCRIPT, not just what to measure. `tools/proofs/run_proof.ps1`
  enforces this and refuses a verdict when markers are absent.
- **Check the binary is newer than the source under test.** One run reported
  CONTRADICTED against a binary that predated the fix. `-SourceUnderTest` guards it.
- **Three harvester bugs today were all "a match that does not stop where it
  should"**: a greedy comment run swallowing sibling blocks, a pre-filter narrower
  than the regex it guarded, a first-token capture reading `SET CASE` as `SET`.
  Every one made the CATALOG look stale when the READER was blind. Suspect the
  instrument when a count surprises you.
- **`git commit -m` with long messages breaks PowerShell parsing.** Write the
  message to `.git\MSG.txt` and use `git commit -F`.
- **`cmd_area51.cpp` is deliberately absent from the SRC* catalog** (lane doc sec
  9a). Do not "fix" it; it is a planted fixture with a pass/fail predicate.

## Method notes worth keeping

- Contracts are authority; catalogs and surfaces are DERIVED. Never hand-type a
  row a generator can emit.
- Assert generated CSV column order against the live DBF header before writing.
- `dbfread.py` is the only sanctioned DBF reader -- it refuses layouts it cannot
  reconcile, understands the X64M extended header (32-bit widths, logical names)
  and never presents a memo pointer as text.
- Declare only what cannot be derived. Stage is derived; `status:` is intent.
- A voluntary block (`@dottalk.usage.voluntary`) is NOT under contract: it
  promises nothing and no guard may report it non-compliant.
