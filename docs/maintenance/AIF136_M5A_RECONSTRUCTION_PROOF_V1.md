# AIF-136 M5-A Isolated Reconstruction Proof V1

Status: PASS
Run: `CODEX-20260915-AIF136-M5A-001`
Measured: `2026-09-16T01:28:03Z`
Scope: reconstruction proof only; no existing storage reclaim

## 1. Result

The approved M5-A pilot passed.

An isolated copy of `DATA_DICTIONARY_OBJECTS.dbf` and its retained
`DATA_DICTIONARY_OBJECTS.cdx` metadata container rebuilt a new LMDB
environment twice. Between the two builds, the runner removed only the
isolated `data.mdb` and `lock.mdb` files that it had just created. It kept the
LMDB environment directory and the CDX container in place.

The second build restored both MDB files, exposed all three retained CDX tags,
selected `CATALOG_OBJECT_ID`, and returned all 10 records in the expected key
order.

No existing DBF, CDX, CNX, live LMDB file, archive LMDB file, or existing
directory was removed or changed.

## 2. Durable storage rule proved

For this exact v64 population:

```text
retained DBF data
  + retained CDX metadata index container
  + retained LMDB environment directory
  -> BUILDLMDB CLEAN YES
  -> reconstructed data.mdb and lock.mdb
```

CDX and CNX files are not reclaim candidates. They are durable metadata index
containers. The environment directory is not a reclaim candidate. Only the
reconstructable `*.mdb` payload files inside an approved environment may be a
future reclaim candidate.

This proof applies to the exact manifest population only. It is not a blanket
ruling for every LMDB environment in the tree.

## 3. Measured evidence

| Check | Result |
| --- | --- |
| Source DBF copy matched source SHA-256 | PASS |
| Retained CDX copy matched source SHA-256 before and after both builds | PASS |
| CDX tags reported | 3: `CATALOG_OBJECT_ID`, `CATALOG_OBJECT_TYPE`, `CATALOG_OBJECT_NAME` |
| Table records opened | 10 |
| Stage 1 build | `BUILDLMDB: done OK=3 tags rebuilt.` |
| Isolated generated files after stage 1 | `data.mdb`, `lock.mdb` |
| Isolated generated files removed between stages | `data.mdb`, `lock.mdb` only |
| Environment directory survived empty | PASS |
| Stage 2 reconstruction | `BUILDLMDB: done OK=3 tags rebuilt.` |
| Indexed read after reconstruction | 10 records in expected `CATALOG_OBJECT_ID` order |
| Protected files before versus after | byte size and SHA-256 identical |
| Existing files removed | 0 |
| Existing directories removed | 0 |

The executable measured by this run was
`D:\code\ccode\build\src\Release\dottalkpp.exe`, SHA-256
`66f52cc75a4a57f095c79e1a4eb3a8b26c52c12677947f1235a8b211f9b10d8f`.

## 4. Proof artifacts

- Ruling: `docs/maintenance/AIF136_M5A_RECONSTRUCTION_PILOT_RULING_V1.md`
- Exact manifest: `labtalk/registries/aif136_m5a_reconstruction_manifest_v1.json`
- Proof runner: `labtalk/ai_portal/run_aif136_m5a_reconstruction.py`
- Runner tests: `labtalk/ai_portal/tests/test_run_aif136_m5a_reconstruction.py`
- Stage 1 transcript: `labtalk/proofs/runs/20260915_aif136_m5a_reconstruction_stage1.txt`
- Stage 2 transcript: `labtalk/proofs/runs/20260915_aif136_m5a_reconstruction_stage2.txt`
- Protected-file hashes and measured file states:
  `labtalk/proofs/runs/20260915_aif136_m5a_protected_hashes.json`

## 5. Authorization boundary

M5-A is complete. M5-B is not authorized.

No existing `*.mdb` file may be removed on the strength of this report alone.
Any M5-B action requires a second owner approval naming the exact directory,
the exact `data.mdb` and `lock.mdb` files, their measured hashes and sizes, the
retained DBF and CDX or CNX inputs, and rollback or reconstruction instructions.

The current manifest names one possible M5-B directory only for review:

`docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0/lmdb/backups/DATA_DICTIONARY_OBJECTS.cdx.d_20260529_111604`

Its directory and its related DBF and CDX container must remain. Its two MDB
files total 16,384 logical bytes. That small reclaim yield should be considered
before authorizing any physical action.
