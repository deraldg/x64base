# AIF-136 M5-B Reclaim Pilot Ruling Packet V1

Date: 2026-09-15
Lane: AIF-136
Phase: M5-B
State: COMPLETE; RESTORE DRILL PASS; PHYSICAL RECLAIM PASS

## 1. Decision requested

Decide whether to run one tightly bounded reclaim pilot after its remaining
restore drill passes. This packet does not authorize or perform deletion.

The machine-readable authority is:

`labtalk/registries/aif136_m5b_reclaim_manifest_v1.json`

It deliberately records `m5b_action_authorized: false` and an owner decision
of `pending` for physical reclaim. The owner approved only the isolated restore
drill on 2026-09-15.

## 2. Exact proposed change

Preserve this directory:

`docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0/lmdb/backups/DATA_DICTIONARY_OBJECTS.cdx.d_20260529_111604`

Remove only these reconstructable LMDB payload files from inside it:

| File | Logical bytes | SHA-256 |
| --- | ---: | --- |
| `data.mdb` | 8192 | `b74af879d304cf0bb5be2b8deebb75ab63183062a39db9836af59cca908cbe6c` |
| `lock.mdb` | 8192 | `bc30335232fdf9613ca3c1de50c36fd109f63dd25bd25f5b961b8efa3b80c312` |

Expected logical reclaim: 16,384 bytes.

The directory must continue to exist after the files are removed. No other
LMDB environment is in scope.

## 3. Files that must remain

These are the reconstruction inputs and are outside the deletion scope:

| Role | File | Logical bytes | SHA-256 |
| --- | --- | ---: | --- |
| Authoritative table | `docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0/dbf/DATA_DICTIONARY_OBJECTS.dbf` <!-- cite-check:ignore -- local development data retained outside Git --> | 5761 | `63412569a6ca8d5e8d1e498bee1060f95214d14c5cf3b38b2e7d5c1681ad6adf` |
| CDX metadata/index generator | `docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0/indexes/DATA_DICTIONARY_OBJECTS.cdx` | 1064 | `76b94efde9268493a31d0fd3d61f3e89c8db23a18feb79cc641f101ba2f30503` |

The same retention rule applies to CNX containers in any future pilot: CDX and
CNX containers are metadata/index generators and are not reclaim payloads.
The two inputs above are intentionally local development data, not Git payloads;
the manifest and proofs preserve their exact identities and recovery contract.

## 4. What M5-A proved

M5-A proved, in isolation, that the retained DBF and CDX can rebuild a standard
LMDB environment twice. Both runs produced three tags and the expected ten
records, and the protected inputs remained unchanged.

Evidence:

- `docs/maintenance/AIF136_M5A_RECONSTRUCTION_PROOF_V1.md`
- `labtalk/proofs/runs/20260915_aif136_m5a_protected_hashes.json`
- commit `0ada5f52d` (`docs(ai-portal): verify AIF-136 M5-A reconstruction`)

## 5. Remaining gap before deletion

M5-A rebuilt a standard environment in an isolated workspace. It did not prove
that the two generated MDB files can be restored into an already preserved,
timestamp-suffixed directory.

Before any M5-B deletion, run a non-destructive restore drill that:

1. creates an empty timestamp-suffixed test directory in an isolated workspace;
2. rebuilds the standard environment from copies of the retained DBF and CDX;
3. copies only the generated `data.mdb` and `lock.mdb` into the test directory;
4. validates the same ten records and three tags from that restored location;
5. proves the retained DBF and CDX hashes did not change; and
6. records the commands, hashes, and result as durable proof.

The drill passed on 2026-09-15 and is recorded in
`AIF136_M5B_RESTORE_DRILL_PROOF_V1.md`. Physical reclaim remains blocked until
the owner issues the separate exact ruling in section 8.

## 6. Tool ruling

Do not use `tools/fullstack_docs/prune_lmdb_archives.ps1 -Execute` for this
pilot. That tool removes whole archive directories. This pilot requires the
directory to survive and permits removal of exactly two named files only.

Any eventual executor must fail closed unless all of these are true:

- the owner decision in the manifest is `approved`;
- both candidate files still match the recorded sizes and hashes;
- the target directory contains exactly the two expected entries;
- the retained DBF and CDX still match their recorded sizes and hashes;
- the simulated timestamped-directory restore drill has passed; and
- the executor can remove only the two manifest-listed files without removing
  the directory.

## 7. Proportionality

This pilot recovers only 16 KiB. Its value is procedural: proving that the
portal can age reconstructable generated payloads into long-term memory without
damaging their reconstructable structure. Deferring or rejecting the pilot is
reasonable if that proof is not worth the operational ceremony.

## 8. Owner ruling

Restore-drill ruling: APPROVED by `member.derald` in the active session on
2026-09-15. Physical-reclaim ruling: APPROVED by `member.derald` in the active
session on 2026-09-15 by responding `go` directly to the exact ruling below.

The bounded approval received was:

`Approve AIF-136 M5-B restore drill only. Do not delete the candidate MDB files.`

The drill has passed. Physical reclaim still requires a second, explicit
ruling naming manifest `AIF136-M5B-001`. A suitable ruling is:

`Approve AIF136-M5B-001 exactly as measured: remove only its listed data.mdb and lock.mdb files, preserve the target directory, DBF, CDX/CNX metadata containers, and every other LMDB environment.`

## 9. Action taken by this preparation step

- Remeasured both candidate MDB files and both retained inputs.
- Confirmed their sizes and hashes match the M5-A evidence.
- Recorded the exact deletion and retention boundaries.
- Excluded the whole-directory archive pruner.
- Performed no deletion, move, rename, cleanup, rebuild, commit, or push during
  packet preparation.

## 10. Restore-drill result

Run `CODEX-20260915-AIF136-M5B-RESTORE-001` passed:

- rebuilt a standard LMDB environment from isolated copies of the retained DBF
  and CDX;
- copied the generated `data.mdb` and `lock.mdb` into the exact
  timestamp-suffixed candidate-directory shape in an isolated workspace;
- opened that restored directory directly with read-only `LMDBDUMP`;
- found all three named tag databases with 10 entries each;
- read the ten expected `CATALOG_OBJECT_ID` keys in order;
- proved the restored MDB files matched the standard rebuilt files by size and
  SHA-256;
- proved the full protected M5-A population was unchanged before versus after;
- removed only the runner-owned temporary workspace after success; and
- removed zero candidate files and zero candidate directories.

Proof: `docs/maintenance/AIF136_M5B_RESTORE_DRILL_PROOF_V1.md`.

## 11. Physical-reclaim result

Run `CODEX-20260915-AIF136-M5B-RECLAIM-001` passed on 2026-09-15:

- removed exactly the manifest-listed `data.mdb` and `lock.mdb` files;
- reclaimed 16,384 logical bytes;
- preserved the target directory empty;
- preserved the retained DBF and CDX with identical sizes and SHA-256 hashes;
- changed zero other LMDB environments in the protected population;
- verified both approved payload hashes again in an owned quarantine before
  final unlink; and
- removed the owned quarantine workspace after success.

Proof: `docs/maintenance/AIF136_M5B_RECLAIM_EXECUTION_PROOF_V1.md`.

This is one exact pilot result. It does not authorize another directory or a
bulk pruning operation.
