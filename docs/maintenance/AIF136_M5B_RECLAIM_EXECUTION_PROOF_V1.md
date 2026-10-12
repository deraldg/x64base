# AIF-136 M5-B Exact Reclaim Execution Proof V1

Status: PASS
Run: `CODEX-20260915-AIF136-M5B-RECLAIM-001`
Measured: `2026-09-16T03:38:26Z`
Manifest: `AIF136-M5B-001`

## 1. Owner ruling

The owner responded `go` directly to this exact ruling:

`Approve AIF136-M5B-001 exactly as measured: remove only its listed data.mdb and lock.mdb files, preserve the target directory, DBF, CDX/CNX metadata containers, and every other LMDB environment.`

The manifest recorded that ruling before execution.

## 2. Result

The exact reclaim passed.

The executor remeasured the manifest-listed files, retained inputs, restore
proof, transcript hash, target-directory contents, and full protected M5-A
population before changing storage. It then moved exactly the two approved MDB
files into an owned quarantine. After proving the target directory survived
empty and every retained protected hash was unchanged, it unlinked those two
quarantined files and removed the empty owned quarantine.

| Measure | Result |
| --- | --- |
| Files removed | 2 |
| Logical bytes reclaimed | 16,384 |
| Target directory present after reclaim | PASS |
| Target directory entries after reclaim | 0 |
| Retained DBF unchanged | PASS |
| Retained CDX unchanged | PASS |
| Other protected LMDB environments changed | 0 |
| Quarantine removed after success | PASS |

## 3. Removed files

| File | Logical bytes | SHA-256 verified before unlink |
| --- | ---: | --- |
| `data.mdb` | 8192 | `b74af879d304cf0bb5be2b8deebb75ab63183062a39db9836af59cca908cbe6c` |
| `lock.mdb` | 8192 | `bc30335232fdf9613ca3c1de50c36fd109f63dd25bd25f5b961b8efa3b80c312` |

The preserved empty directory is:

`docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0/lmdb/backups/DATA_DICTIONARY_OBJECTS.cdx.d_20260529_111604`

## 4. Retained reconstruction inputs

| File | Logical bytes | SHA-256 after reclaim |
| --- | ---: | --- |
| `DATA_DICTIONARY_OBJECTS.dbf` | 5761 | `63412569a6ca8d5e8d1e498bee1060f95214d14c5cf3b38b2e7d5c1681ad6adf` |
| `DATA_DICTIONARY_OBJECTS.cdx` | 1064 | `76b94efde9268493a31d0fd3d61f3e89c8db23a18feb79cc641f101ba2f30503` |

The CDX remains the metadata/index generator. CNX containers remain protected
under the same rule for future populations.

## 5. Rollback

The runtime-proven rollback is recorded by
`docs/maintenance/AIF136_M5B_RESTORE_DRILL_PROOF_V1.md`:

1. copy the retained DBF and CDX into an isolated workspace;
2. rebuild the standard LMDB environment with `BUILDLMDB CLEAN YES`;
3. copy the generated `data.mdb` and `lock.mdb` into the preserved target
   directory;
4. open that timestamp-suffixed directory directly with read-only `LMDBDUMP`;
5. validate three tag databases with 10 entries each and the ten expected
   ordered ID keys; and
6. recheck the retained and protected hashes.

## 6. Proof artifacts

- Exact manifest: `labtalk/registries/aif136_m5b_reclaim_manifest_v1.json`
- Fail-closed executor: `labtalk/ai_portal/run_aif136_m5b_reclaim.py`
- Executor tests: `labtalk/ai_portal/tests/test_run_aif136_m5b_reclaim.py`
- Machine-readable execution proof:
  `labtalk/proofs/runs/20260915_aif136_m5b_reclaim.json`

## 7. Boundary

This proof covers only manifest `AIF136-M5B-001`. It does not authorize
another LMDB directory, another `*.mdb` file, or the bulk archive-pruning tool.
