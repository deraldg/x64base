# Findings — Native CNX / CDX Format Relationship + Terminology

**Date:** 2026-07-21
**Author:** Claude (hosted AI), source-read only.
**Purpose:** Settle whether native CNX and native CDX share the same indexing mechanism, and lock terminology across lanes `XIDX-TXN-01` (LMDB) and `XIDX-TXN-02` (CNX).

---

## 1. Verdict

- **Native container FORMAT: same mechanism (twins).** `cnxfile::` (`include/cnx/cnx.hpp`) and `cdxfile::` (`include/cdx/cdx.hpp` + `src/cdx/cdx_file.cpp`) are structurally identical designs — same header, tag directory, table-bind, API, and raw RUN/page primitives — duplicated into two namespaces. They differ **only** in the 4-byte magic and namespace name.
- **Backend KEY-SERVING: not shared.** `CnxBackend` and `CdxBackend` are separate classes. CNX serves keys **from the `.cnx` file** (RUN1). Wired CDX serves keys **from LMDB**, using `.cdx` as tag-directory metadata only. A standalone native-CDX key path is **unrealized** (no `CdxDocument`).

## 2. Evidence — the formats are twins

| Element | `cnxfile::` (CNX) | `cdxfile::` (CDX) | Same? |
|---|---|---|---|
| Magic | `"CNX1"` 0x31584e43 | `"CDX1"` 0x31584443 | differs (only this + namespace) |
| Version / page size | 1 / 4096 | 1 / 4096 | ✔ |
| Dirty flag | `CNX_HDRF_DIRTY` 0x0001 | `CDX_HDRF_DIRTY` 0x0001 | ✔ |
| Header layout | magic,version,page_size,flags,tagdir_offset,tag_count,reserved0-3 | identical | ✔ |
| `TagDirEntry` | name[32],tag_id,flags,collation_id,expr_hash64,for_hash64,root_page_off,key_type,key_len,stats_rec,updated_ts | identical | ✔ |
| `TableBind`/`TableProbe`/`validate_table_bind` | present | identical | ✔ |
| API | open/close/read_header/set_dirty/flush_header, read/write_table_bind, read/write_tagdir, add/drop_tag, append_bytes/read_at/write_at | identical | ✔ |
| Design note | "does not build keys; REBUILD/COMPACT separate"; raw I/O "for RUN blocks, future B-tree pages" | identical wording | ✔ |

Conclusion: one container design, two magic numbers. (Duplicated code, not shared functions — a refactor could unify them behind a `magic` parameter.)

## 3. Evidence — the key-serving backends diverge

- **CNX (native, keys in file):** `CnxDocument::open` reads `RUN1` payloads (runs of **uint32** recnos) from the `.cnx` via `cnxfile::read_at(root_page_off,…)` into an in-memory `InxPayload`; `CnxBackend` serves seeks from it; `rebuild()` rewrites RUN1 with `cnxfile::append_bytes`. Keys live in the `.cnx` file.
- **CDX (wired = LMDB, keys in LMDB):** the only calls against the `.cdx` are `cdxfile::read_tagdir` — in `order_hooks` (tag validation/default pick) and `BUILDLMDB` (tag discovery). Keys are built into and served from the LMDB env (`data\lmdb\<stem>.cdx.d`) by `CdxBackend`/`BUILDLMDB` (composite key `field‖recno8`, uint64). **No `CdxDocument` / RUN reader for `.cdx` exists in any path read.**
- Therefore native-CDX-without-LMDB key serving is a **format-capable but code-absent** gap; LMDB currently fills that role.

## 4. Locked terminology

- **Native indexing** — the `cnxfile::`/`cdxfile::` self-contained file formats (twins). Keys stored in the container as RUN blocks (and, per the header, "future B-tree pages").
  - **Native CNX** (`.cnx`, V32/uint32): **working** native key path (`CnxDocument` RUN1).
  - **Native CDX** (`.cdx`, V64/uint64): **format present, key path absent** — currently used as tagdir metadata only.
- **LMDB indexing** — `CdxBackend` + `LmdbBackend` key store in an LMDB env; the **default** profile. `.cdx` here is the tagdir; keys are in LMDB. (Separate from the standalone `SET LMDB` `LmdbBackend`, which uses DUPSORT — a different env/scheme.)
- Profiles (`DOTTALK_INDEX_MODE`): `NONE` (no index), `LEGACY` (native CNX/CDX, no LMDB), `LMDB` (default; LMDB-backed CDX).

## 5. Implication for the lanes (design opportunity)

Because native CNX and native CDX are the **same container format**, the mutable-key work planned in **`XIDX-TXN-02`** (CNX transactional mutations — Option A in-place RUN rewrite, or Option B reserved B-tree pages) is written against primitives (`append_bytes`/`read_at`/`write_at`, `root_page_off`, `CNX_HDRF_DIRTY`) that are **identical** in `cdxfile::`. So a native mutable/transactional key path built for CNX can be **lifted to native CDX (V64) almost for free** — the delta is the magic number, uint32→uint64 recno width, and instantiating a `CdxDocument` twin of `CnxDocument`.

Recommended register updates:
- `XIDX-TXN-02` gains a note: its native write path should be authored format-neutrally so it serves both `.cnx` (V32) and a future `.cdx` (V64) native key store; consider unifying `cnxfile::`/`cdxfile::` behind a shared implementation parameterized by magic + recno width.
- New candidate follow-up lane **`XIDX-NATIVE-CDX-01`** (native CDX key path, V64, no LMDB) — deferred; unlocked by `XIDX-TXN-02` if authored format-neutrally.

## 6. Cross-reference

Ties to the Optional-Index Architecture Decision "remaining proof item 1" (attached-CNX mutation sync) and item 2 (CDX metadata→LMDB workflow). The native-CDX key gap explains why item 2 routes CDX through LMDB rather than a standalone `.cdx` key store today.
