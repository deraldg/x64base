---
id: ENG-060
title: Native CDX vs LMDB-Backed CDX
type: engine_case
era: 2025-present
level: developer
lab: LAB_CASE_NATIVE_CDX_VS_LMDB
domains: [xbase, indexes, cdx, lmdb, ramfs, run8, backend, in-memory]
status: runtime_lab_candidate
review_status: runtime_proof_available
evidence_class: runtime_proven_plus_source
runtime_visibility: hidden_until_reviewed
manual_visibility: draft_outline
source_docs: [AIF_043_M1_PROOF_GREEN_CLOSEOUT_V1_20260722.md, AIF_043_RAM_DBF_POSITIONING_AND_LIMITATIONS_V1_20260722.md]
media_assets: []
runtime_proof: [dottalkpp/data/scripts/mem_proof.dts (REGRESSION MEM)]
---

## SUMMARY

`CDX` is the user-facing logical index container; it can be served by two different
*backends*. The **LMDB-backed CDX** stores the sorted key→recno entries in a memory-mapped
B+tree on disk. The **native CDX-V64** stores the same ordered information as its own RUN blocks
inside the CDX container and answers queries from an in-memory sorted payload — no LMDB, no
`mmap`. This case teaches that the order concept (CDX/tags/SET ORDER) is stable while the backend
underneath is an implementation choice, and that the choice has real consequences for where the
index can live (disk vs RAM) and how it is maintained (static rebuild vs live tree).

## PROBLEM

Extends ENG-010 ("logical order ≠ physical order"). Once students accept that an index is a
navigation structure, the next question is: *what actually holds the sorted order, and can it
live somewhere other than a disk file?* The engine needed an index path that works inside the
in-process RAM VFS (`xbase::ramfs`, AIF-043), where an on-disk memory-mapped store is impossible.

## WORKFLOW

Runtime proof: `REGRESSION MEM` (`mem_proof.dts`). Under a mounted RAM disk (`DO mem`), build an
x64 table and index it with `CDX CREATE` / `CDX ADDTAG LNAME` / `REINDEX CDX`, then
`SET ORDER TAG LNAME` and traverse `TOP` / `SKIP` / `BOTTOM`. The ordered read-back is
ADAMS/MILLER/ZEBRA with **zero files on disk** — the whole index lives in RAM. Compare to the
disk path (`index_v64_cdx_lmdb_smoke.dts`), where the same commands build an LMDB environment
sidecar (`<stem>.cdx.d`) next to the container.

## MODEL

Two phases, two backends, one container abstraction.

Native CDX-V64 build (`REINDEX` → `CdxNativeBackend::rebuild`): scan the table
(`recCount64`/`recno64`), extract each record's key for the tag, type it (Character trimmed+upper;
Numeric parsed; Date kept as `YYYYMMDD`, whose lexical order is chronological), `stable_sort` by
key with recno as tiebreak, and serialize the resulting ordered recnos as little-endian RUN
blocks (RUN8 = 8-byte/uint64; RUN1 = 4-byte/uint32) into the CDX container. Query
(`SET ORDER`/SEEK/TOP-SKIP-BOTTOM): `CdxDocument` loads the tag's RUN payload into an in-RAM
`InxPayload`, and a `CdxCursor` walks it (`first/next/prev/last`) or binary-searches (`lower_bound`)
for a SEEK. All container I/O flows through the engine's `io()` seam, so on a mounted VDISK it is
`ramfs` bytes and on disk it is a file — the index never needs a file descriptor, page cache, or
`mmap`.

| Aspect | Native CDX-V64 | LMDB-backed CDX |
|---|---|---|
| Sorted store | Ordered RUN blocks in the CDX container + in-RAM payload | Memory-mapped B+tree (`.cdx.d` env) |
| Persistence substrate | Any `iostream` — disk **or** `ramfs` (in-RAM) | Real `mmap`'d OS file (disk only) |
| Lives in RAM VFS? | Yes (AIF-043 M1 path) | No — needs a real file; deferred symlink/RAM-disk add-on |
| Recno width | RUN1 uint32 / RUN8 uint64 ("build for big, fall back for small") | Backend key encoding |
| Maintenance | Static: `REINDEX` rebuilds the RUN blocks | Live B+tree; supports in-COMMIT maintenance (SET INDEXTXN lane) |
| Best for | Ephemeral in-memory tables; build-query-discard; fast reads | Long-lived on-disk tables with incremental index upkeep |

The key insight: the LMDB backend does two jobs — sorted structure *and* its persistence — and
both by `mmap`-ing a file. The native backend does the sort once at build time and persists it as
plain container bytes, so it inherits `ramfs`-routability that `mmap` can never have.

## TAKEAWAY

CDX is the contract; the backend is a choice. Reach for the **native CDX-V64** when the index
must live in RAM or when the workload is build-query-discard (ephemeral tables, index-build
acceleration, deterministic test fixtures) — it is `ramfs`-routable and fast to read, at the cost
of being a *static* index that `REINDEX` rebuilds rather than updates in place. Reach for the
**LMDB-backed CDX** for long-lived on-disk tables that need a live B+tree with incremental,
in-transaction maintenance. Teaching prose should keep saying "CDX / order / tag" and expose the
backend distinction only when the lesson is specifically about *where the index lives and how it
is maintained* — which is exactly this case.
