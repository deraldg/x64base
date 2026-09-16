# AIF-136 M5-A Reconstruction Pilot Ruling V1

Status: APPROVED FOR ISOLATED PROOF ONLY

Owner: `member.derald`

Steward: `member.ai.codex`

Run: `CODEX-20260915-AIF136-M5A-001`

Manifest: `labtalk/registries/aif136_m5a_reconstruction_manifest_v1.json`

## Owner ruling

The owner approved M5-A in the active Codex task at
`2026-09-16T01:16:50Z`, after receiving this exact boundary:

> Approve AIF-136 M5-A for the isolated DATA_DICTIONARY_OBJECTS
> reconstruction proof only. No existing archive, live LMDB environment,
> source DBF/CDX, or other database may be moved, modified, or deleted.
> Return with hashes, record and index readback, and the exact M5-B reclaim
> proposal.

The owner's follow-up clarifies the physical contract: the LMDB environment
directory must continue to exist. Files inside it are reconstructible with
BUILDLMDB. Therefore M5-A must test an existing empty directory, reconstruct
its files, empty only the isolated temporary directory, preserve that
directory, and reconstruct the files again.

## Exact pilot

The retained-input and derivation chain is:

```text
copied DBF data + copied CDX metadata index container
-> BUILDLMDB data.mdb and lock.mdb files
```

The `.cdx` and `.cnx` containers must be retained. They are metadata index
generators for their LMDB environments; M5 targets only the reconstructible
`*.mdb` files, never the containers. `CNX` is not used by this one-table CDX
pilot, but the same preservation rule applies to it. M5-A copies the existing
CDX and verifies its hash before using BUILDLMDB.

The possible M5-B candidate is exactly:

`docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0/lmdb/backups/DATA_DICTIONARY_OBJECTS.cdx.d_20260529_111604`

That directory contains 16,384 logical bytes across `data.mdb` and `lock.mdb`.
M5-A does not modify either file or the directory.

## M5-A acceptance

1. Every protected file matches the manifest before execution.
2. A new isolated workspace is created under `tmp/aif136_m5a/`.
3. The source DBF and its CDX metadata container are copied into it and both
   copies match their approved hashes.
4. The target LMDB environment directory is created before BUILDLMDB and is
   verified empty.
5. The copied CDX reports its existing `CATALOG_OBJECT_ID` tag.
6. BUILDLMDB creates the environment files from the copied CDX and ordered readback reports all
   ten records.
7. Only the isolated `data.mdb` and `lock.mdb` are removed. The environment
   directory must still exist and be empty.
8. BUILDLMDB reconstructs the files again from the copied DBF and preserved
   CDX, and ordered readback again reports all ten records.
9. Every protected file matches its before hash after execution.
10. No existing archive, live environment, source DBF/CDX, CNX, or other
    database is changed.

## Not authorized

- No M5-B reclaim action.
- No removal of an existing `data.mdb` or `lock.mdb`.
- No removal of an LMDB environment directory.
- No removal or regeneration of an existing `.cdx` or `.cnx` container.
- No broad archive-prune command.
- No mutation of DBF, CDX, CNX, live LMDB, HELP, metadata, website, or
  publication state.

M5-B requires a second owner ruling after the M5-A proof is reviewed.
