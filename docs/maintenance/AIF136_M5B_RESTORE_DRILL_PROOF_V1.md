# AIF-136 M5-B Timestamped-Directory Restore Drill Proof V1

Status: PASS
Run: `CODEX-20260915-AIF136-M5B-RESTORE-001`
Measured: `2026-09-16T03:25:09Z`
Scope: isolated restore proof only; no existing storage reclaim

## 1. Result

The owner-approved restore drill passed.

The runner copied the retained `DATA_DICTIONARY_OBJECTS.dbf` and
`DATA_DICTIONARY_OBJECTS.cdx` into a new isolated workspace and used
`BUILDLMDB CLEAN YES` to create a standard LMDB environment. It then copied
only the generated `data.mdb` and `lock.mdb` into a new empty directory whose
name exactly matched the real timestamp-suffixed candidate directory.

`LMDBDUMP` opened that restored timestamp-suffixed directory directly and
read it without using the normal active-environment path resolver. It found all
three expected named tag databases, each with 10 entries. The
`CATALOG_OBJECT_ID` database returned all ten expected keys in order.

The real candidate directory, its two MDB files, the retained DBF and CDX, the
live 1 GiB LMDB environment, and every sibling archive in the protected M5-A
population had identical sizes and SHA-256 hashes before and after the drill.

Candidate files removed: 0.
Candidate directories removed: 0.
Physical reclaim authorized: no.

## 2. Measured restored environment

| File | Logical bytes | SHA-256 | Match |
| --- | ---: | --- | --- |
| `data.mdb` | 134217728 | `12d16e75e20e8bdbfecea99ab1097e87cab4e9fea974703bc008aa244473cf47` | standard rebuild equals timestamped restore |
| `lock.mdb` | 8192 | `ed3cb89ffd92b37e56896eb03cbe092c1740ce42997857a2592b84ad38addc77` | standard rebuild equals timestamped restore |

The restored directory leaf was exactly:

`DATA_DICTIONARY_OBJECTS.cdx.d_20260529_111604`

## 3. Readback

| Check | Result |
| --- | --- |
| Standard isolated BUILDLMDB | PASS; 3 tags rebuilt |
| Restored directory opened directly read-only | PASS |
| `CATALOG_OBJECT_ID` | 10 entries; 10 expected ordered keys read |
| `CATALOG_OBJECT_TYPE` | 10 entries; 10 records scanned |
| `CATALOG_OBJECT_NAME` | 10 entries; 10 records scanned |
| Rebuilt and restored MDB hashes | identical |
| Full protected population before versus after | identical |
| Runner-owned temporary workspace cleanup | PASS |

The measured executable was
`D:\code\ccode\build\src\Release\dottalkpp.exe`, size 9,100,800 bytes,
SHA-256 `0c3b4b61b0999bf1fe3f33066cc846c11216ecba2b327e6483f3c0dc853786a5`.

## 4. Proof artifacts

- Exact reclaim and restore manifest:
  `labtalk/registries/aif136_m5b_reclaim_manifest_v1.json`
- Restore runner: `labtalk/ai_portal/run_aif136_m5b_restore_drill.py`
- Runner tests: `labtalk/ai_portal/tests/test_run_aif136_m5b_restore_drill.py`
- Runtime transcript:
  `labtalk/proofs/runs/20260915_aif136_m5b_restore_drill.txt`
- Machine-readable proof:
  `labtalk/proofs/runs/20260915_aif136_m5b_restore_drill.json`

The transcript SHA-256 is
`ae768e9fa89c25ad4a6e73ba640240207c3fd361f900d97d6c6e28fa60b20970`.

## 5. Authorization boundary

This proof closes the restore-drill prerequisite only. It does not change
`m5b_action_authorized`, which remains false, and it does not approve physical
reclaim.

The next action, if the owner wants the 16 KiB pilot reclaim, requires the
separate exact ruling already printed in the ruling packet:

`Approve AIF136-M5B-001 exactly as measured: remove only its listed data.mdb and lock.mdb files, preserve the target directory, DBF, CDX/CNX metadata containers, and every other LMDB environment.`
