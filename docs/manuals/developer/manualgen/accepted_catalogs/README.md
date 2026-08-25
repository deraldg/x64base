# accepted_catalogs -- what this is, and what is tracked

Owner: member.derald. Author: member.ai.claude.cowork. Date: 2026-08-18. Lane: OI-011.

Not a backup. This is the **accepted output of a green promotion gate**:
`man_catalog_v1_manifest.json` records `MDO-251`, status
`X64BASE_MAN_CATALOG_BASELINE_PROMOTION_GREEN`, promoting eight MAN* tables out
of the MDO-248 execution workspace into a baseline.

Until 2026-08-18 nothing here was tracked, and the directory also held 5.00 G of
LMDB `.mdb` preallocations. The `.mdb` are gone (regenerable from the DBFs beside
them); the baseline stayed.

## Verified before tracking, using the promotion's own manifests

| check | source of truth | result |
| --- | --- | --- |
| every promoted file still byte-identical | `mdo_251_promotion_file_manifest_v1.csv`, 21 rows | **21 intact, 0 missing, 0 mismatched** |
| each table still equals what MDO-251 promoted | `mdo_251_promoted_dbf_manifest_v1.csv`, 8 tables | **8 of 8 identical** |
| promoted equals the source it came from | `source_sha256` vs `promoted_sha256` | **8 of 8 equal** |

So the tracked bytes are provably the bytes MDO-251 accepted, which are provably
the bytes MDO-248 produced. That chain is worth having recorded, because the
execution workspace it came from -- `manualgen/generated/x64base_man_catalog_execution_v1/`
-- **no longer exists on disk** and is gitignored at `.gitignore:82`.

## What is tracked: 23 files

- `man_catalog_v1/dbf/` -- 8 promoted MAN* tables (MANRUN, MANSECTION, MANMEDIA,
  MANANCHOR, MANHASH, MANREVIEW, MANPUB, MANAPPX)
- `man_catalog_v1/man_catalog_v1_manifest.json` -- the promotion record
- `man_catalog_v1/evidence/reports/*.md` -- 4 run summaries, MDO-248 to MDO-251
- `manstar_native_reference_v1/dbf/` -- 5 MANREF* tables
- `manstar_native_reference_v1/indexes/` -- 5 `.cdx`

## What is NOT tracked: the 15 evidence `.csv`

`.gitignore:341` (`docs/manuals/developer/manualgen/**/*.csv`) excludes them.
That rule was written for regenerable catalog output, so the question was
whether these are that. Answer, after reading all fifteen: **fourteen are
recoverable, one is not.**

**Recomputable from the tracked DBFs** -- `mdo_248_field_mapping_v1` (table,
field, type, length: readable from the DBF headers), `mdo_249_dbf_observation_v1`
and `mdo_250_dbf_header_readback_v1` (sizes, hashes, header fields),
`mdo_251_promotion_file_manifest_v1` and `mdo_251_promoted_dbf_manifest_v1`
(paths, sizes, hashes of files that are now in git).

**Restated in full by the four tracked `.md`** -- the four boundary ledgers, the
four status summaries and the gate matrix. Every `.md` opens with its `Status:`
and carries a `## Boundary` section listing the same zeros (HELP, META,
CMDHELPCHK, source, publication, media, protected-system), and the MDO-251
summary carries the precondition and decision that the gate matrix tabulates.
The CSVs are the machine-readable form of assertions the prose already makes.

**The one exception: `mdo_248_generated_dts_manifest_v1.csv`.** It holds the
byte length and sha256 of three DotScript files under
`generated/x64base_man_catalog_execution_v1/dts/`. Those scripts are gone from
disk and were never tracked, so the hashes cannot be recomputed and cannot be
checked against anything. The MDO-248 `.md` names all three script paths but not
their hashes.

Left ignored, deliberately. It is a dangling assertion: it identifies artifacts
that no longer exist by a fingerprint nothing can now be compared against. If the
`.dts` are ever recovered, this file becomes the thing that proves which ones
they were -- so it survives in `D:\code\ccode.sidecar\manualgen\accepted_catalogs\`
rather than being deleted. Promote it into git only if the scripts come back.

## Five empty directories

`manstar_native_reference_v1/lmdb`, `man_catalog_v1/csv/execution`,
`man_catalog_v1/csv/staging`, `man_catalog_v1/dts`, `_backups` are left over from
the `.mdb` removal. Git does not track empty directories, so they cost nothing.
