# ENG-060 Runtime Proof

Case: Native CDX vs LMDB-Backed CDX

Status: behavioral proof captured (GREEN). Native CDX-V64 built and traversed entirely in RAM,
no LMDB, zero files on disk.

Behavioral proof (native CDX-V64 in RAM):

- fixture path: `dottalkpp/data/scripts/mem_proof.dts` (curated regression `MEM`)
- command sequence: `DO mem`, `DO mem_proof`  (or `REGRESSION RUN MEM`)
- executable: `D:\code\ccode\build\src\Release\dottalkpp.exe`
- working directory: `D:\code\ccode`
- build identifier: dottalk++ v0.6 (2026-07-21, e68ccf1a dirty), build Jul 22 2026 (post duplicate-basename shadow-guard / /INCREMENTAL:NO hardening)
- date: 2026-07-22
- reviewer: Derald (maintainer), Claude (steward)
- result: PASS

Expected output (self-asserting markers):

```
MEM_T1_top_ADAMS:.T.
MEM_T2_next_MILLER:.T.
MEM_T3_bottom_ZEBRA:.T.
```

Captured output (abridged):

```
. do mem
VDISK: note: RAM disk mounted (in-process VFS): D:\code\ccode\dottalkpp\data\ram
VDISK: note:   DBF     -> D:\code\ccode\dottalkpp\data\ram
VDISK: note:   INDEXES -> D:\code\ccode\dottalkpp\data\ram\indexes
VDISK: note:   LMDB    -> D:\code\ccode\dottalkpp\data\ram\lmdb
. do mem_proof
MEM-TABLE-PROOF-BEGIN
Created D:\code\ccode\dottalkpp\data\ram\MEMT.dbf [X64]
Opened D:\code\ccode\dottalkpp\data\ram\MEMT.dbf with 0 records.
VDISK: note: RAM bytes = 249
VDISK: note: RAM files = 1
VDISK: note:   d:\code\ccode\dottalkpp\data\ram\memt.dbf
CDX: created: "D:\code\ccode\dottalkpp\data\ram\indexes\MEMT.cdx"
CDX ADDTAG: added 'LNAME'.
REINDEX CDX -> BUILDLMDB
REINDEX: note: native CDX-V64 rebuilt in RAM: D:\code\ccode\dottalkpp\data\ram\indexes\MEMT.cdx
SET ORDER: CDX TAG 'LNAME' (ASC)
MEM_T1_top_ADAMS:.T.
MEM_T2_next_MILLER:.T.
MEM_T3_bottom_ZEBRA:.T.
VDISK: note: RAM bytes = 778
VDISK: note: RAM files = 2
VDISK: note:   d:\code\ccode\dottalkpp\data\ram\indexes\memt.cdx
VDISK: note:   d:\code\ccode\dottalkpp\data\ram\memt.dbf
MEM-TABLE-PROOF-END
```

Contrast fixture (LMDB-backed CDX on disk): `dottalkpp/data/scripts/index_v64_cdx_lmdb_smoke.dts`
builds the same logical order but materializes an LMDB environment sidecar (`<stem>.cdx.d`) next
to the container — the visible difference between the two backends.

Acceptance: demonstrate that the CDX order/tag contract is served by a native RUN8 index living
entirely in the RAM VFS (no `mmap`, no LMDB, no disk files), with ordered read-back matching the
sorted key order. MET.

Cross-reference: `src/AIPortal/sessions/2026-07-21_claude_recno64_indextxn_onboarding/AIF_043_M1_PROOF_GREEN_CLOSEOUT_V1_20260722.md`.
