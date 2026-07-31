# LANE -- Index Backend / Table Format Orthogonality

**Lane code:** `AIF-080`
**Lane name:** Separate container format from maintenance engine; replace the format-purity gate with the capacity gate that already exists
**Status:** `planned lane` *(not earned: no source landed beyond the wasStale wiring this lane was found from)*
**Owner:** `member.derald` - drafting partner: Claude (Cowork, local repo access)
**Run:** `INDEX-BACKEND-ORTHOGONALITY-20260731`
**Baseline:** `a6c0aa07f` on `development`
**Created:** 2026-07-31

> **Authority hierarchy.** Conventions suggest. Registration declares. Metadata records. Runtime proves. Validators enforce. This file *declares* the lane; status is earned per gate by proof artifacts.

---

## 1. One-line

`SET INDEX` refuses `.cnx` on a v64 table because "True x64/v128 tables require CDX (LMDB-backed)" -- a single sentence that welds together two independent axes: **which container format** a table uses, and **which engine maintains it**. Separate them, and enforce the constraint that is actually real (record-number capacity) instead of the one that is conventional (format purity).

## 2. Owner's framing

Recorded verbatim because it is the origin of the lane:

> "We have code baked in to exclude cnx from x64, to enforce LMDB usage. CNX index files were updated by batch mode, period, by a single stale mark at commit time. Now that CNX supports key field mutations, we need clear support of both and orthogonality."

**One correction, load-bearing for the design.** CNX does not yet support key field mutations. `CnxBackend::upsert`/`erase` remain `(void)key; (void)rec; stale_ = true;` (`cnx_backend.cpp:521-533`), and `CdxNativeBackend::upsert` is byte-identical (`cdx_native_backend.cpp:507-512`). What changed at `a6c0aa07f`+ is that `apply_replace_snapshot` now compares `wasStale()` across the apply and reports a false -> true transition, so the ABSENCE of maintenance is visible per mutation instead of silent. That is reporting granularity, not capability. The batch/rebuild model is intact and `XIDX-TXN-02` is still unbuilt.

The orthogonality argument survives the correction unchanged, and is arguably strengthened: the engine now *tells* you when a backend did not maintain, which is precisely the signal a per-workload backend choice needs.

## 3. The two axes, and where they are currently collapsed

| | native / batch (rebuild + stale mark) | LMDB / transactional |
|---|---|---|
| **`.cnx`** RUN1, uint32 recnos | v32 today | never existed |
| **`.cdx`** RUN8, uint64 recnos | **`CdxNativeBackend` -- exists, reachable ONLY in RAM** | v64 on disk today |

The empty-looking quadrant is already written. `CdxNativeBackend` is a complete LMDB-free v64 native index (AIF-043 V4). `IndexManager::openCdx` selects it on one condition and one only:

```cpp
if (xbase::ramfs::is_virtual(cdx_container_path)) {   // index_manager.cpp:114
    auto b = std::make_unique<CdxNativeBackend>(area_, cdx_container_path, tag_upper);
```

Disk `.cdx` falls through to the LMDB `CdxBackend` and hard-fails when the env is absent (`openCdx: LMDB env missing`). So "x64 requires LMDB" is true only for on-disk paths, and only because of that single `is_virtual()` branch.

## 4. Verified findings

### F1 -- The gate lives at TWO command surfaces and is not airtight

> **Corrected 2026-07-31 during M1.** This finding originally said "one command surface". It is two. `cmd_setorder.cpp:437` carries `validate_explicit_container_for_flavor` with the same refusal under `SetOrderV64RequiresCdxText` ("True x64/v128 tables require CDX for SET ORDER"), plus a mirror `SetOrderV32UsesCnxNotCdxText`. So the rule is duplicated across `SET INDEX` and `SET ORDER`, absent from `SET CNX` and the index layer, and the two copies can drift independently. That is the AIF-065/066/067 shape again -- two things that never compare themselves -- and it strengthens the argument for enforcing at the seam rather than per command.


`src/cli/cmd_setindex.cpp:276-282`:

```cpp
if (is_x64_cdx_area(A)) {                    // versionByte()==DBF_VERSION_64 || kind()==V128
    if (ext != ".cdx") { err = msg(MessageId::SetIndexV64RequiresCdxText); return false; }
    return true;
}
```

Mirror gate at `:268-274` refuses `.cdx` on v32 ("Classic xBase/VFP tables accept INX or CNX, not CDX").

Where the gate is NOT:

| Site | Flavor check | Currency |
|---|---|---|
| `src/cli/cmd_setcnx.cpp` | **none** -- zero flavor references in the file | **legacy surface** |
| `src/cli/cmd_setcdx.cpp` | (paired with the above) | **legacy surface** |
| `IndexManager::openCnx` (`index_manager.cpp:241`) | none | seam |
| `IndexManager::load_for_table` (`:906`) | none -- dispatches purely on file extension, preferring `.cdx` candidates | seam (auto-attach) |

> **Severity corrected 2026-07-31 by the owner.** An earlier draft of this row called `SET CNX` "a back door" and concluded "a prohibition enforced at one of four entry points is a convention with a warning attached, not an invariant." That overstates it. The CURRENT workflow is:
>
> ```
> SELECT n
> USE <table>
> SET INDEX TO <indexname>      && defaults to the table name; extension defaults to .cdx
> SET ORDER TO TAG <tag>
> SEEK <value>
> ```
>
> Both `SET INDEX` and `SET ORDER` carry the format gate. So on the path in actual use the rule IS enforced, at both surfaces that matter. `SET CNX` / `SET CDX` are older, still-registered surfaces that predate this workflow.
>
> The finding does not vanish, it changes shape. What remains true: the rule is stated twice and can drift; the seam has no opinion; and two legacy commands can still reach `openCnx` without it. What is NOT true is that the live path is unguarded. Closing the legacy gap is hygiene, not a correctness fire, and it should be sequenced accordingly.
>
> A separate question this surfaced: `cmd_setcnx.cpp` carries `status: supported` in its usage contract while not being the current workflow. Supported-but-superseded is a real state, but it is not the same as supported, and the contract does not distinguish them. That is a documentation-currency question for the messaging/usage lane, not for this one -- noted here so it is not lost.

### F2 -- The gate that SHOULD enforce this exists and has zero call sites

```cpp
// include/xindex/index_manager.hpp:85-90
// ... recordNumberFitsBackend() and reject with a clear error rather than truncate.
std::uint64_t backendMaxRecordNumber() const noexcept { return backend_ ? backend_->maxRecordNumber() : UINT64_MAX; }
bool recordNumberFitsBackend(RecNo rec) const noexcept { return rec <= backendMaxRecordNumber(); }
```

with `CnxBackend::maxRecordNumber() = UINT32_MAX` and `CdxNativeBackend::maxRecordNumber() = UINT64_MAX`. **No caller anywhere in `src/` or `include/`.**

This is the real constraint. CNX cannot index a record above 4 G because its RUN1 payload addresses recnos in 32 bits -- not because the table's header byte says v64. A v64 table with fewer than 2^32 records can use CNX correctly. The header comment already states the intended behavior ("reject ... rather than truncate"); nothing calls it.

Feeds `AIF-079` as a further D1 instance (declared public capability, zero call sites), and is the mechanism this lane needs.

### F3 -- The refusal message conflates the axes in user-facing text

> "True x64/v128 tables require CDX (LMDB-backed).\nUse .cdx for this table."

Two claims in one sentence, one of which is a format statement and one an engine statement. Whatever the code ends up doing, this message needs splitting, because it teaches the conflation to every operator who hits it.

## 5. Scope

**In:** wire `recordNumberFitsBackend` at the binding site; replace the F1 format gate with the capacity gate; close the `SET CNX` back door by moving enforcement to `IndexManager::openCnx`/`openCdx` where all four entry points converge; split the F3 message; make `CdxNativeBackend` selectable for on-disk `.cdx` rather than only `is_virtual()`.

**Out:** implementing incremental mutation for either native backend -- that is `XIDX-TXN-02`, and this lane must not absorb it (section 7). Also out: INX/2INX, which is a third format with its own lane.

## 6. Milestone gates

### M0 -- Decide the selection surface -> readiness `source-evidenced`
**Exit:** decide HOW an operator or the engine picks native-vs-LMDB for a disk `.cdx`. Candidates: a `SET` flag mirroring `SET INDEXTXN`; a per-container sidecar declaration; build-vector default with per-area override. Decide whether v32 + native `.cdx` is permitted (capacity says yes, tradition says no).
**Proof:** M0 findings note appended here.

### M1 -- Defects only, no new capability -> PARTIAL, `source-evidenced` 2026-07-31
**Exit:** capacity gate called and refusing a >UINT32_MAX bind to CNX with a clear error; `SET CNX` no longer bypasses; message split. No change to which backend is chosen for existing tables.
**Note:** M1 is independently valuable and has NO dependency on M2 or on XIDX-TXN-02. If the lane stalls, M1 alone leaves the tree better.

**LANDED (source-evidenced, needs `REGRESSION ALL` for runtime):** the capacity gate, in `IndexManager::openCnx` (`index_manager.cpp:296`). This is the FIRST call site `recordNumberFitsBackend()` has ever had; the 2026-07-21 lane docs asked for it twice ("enforce at call sites", "wherever appends bind a recno to the backend") and it was never wired.

Placed at the SEAM rather than a command surface, so all four entry points -- `SET INDEX`, `SET CNX`, `SET ORDER`, and `load_for_table` auto-attach -- are covered by one check. That partially closes the `SET CNX` back door as a side effect, for capacity though not yet for format.

Uses `recCount64()`, not `recCount()`. `recCount()` returns `int32_t` (`xbase.hpp:274`, whose own comment defers to `recCount64()` as "the authoritative value"), so checking a 32-bit overflow through it would truncate the quantity under test and the gate would never fire. Worth recording because the wrong accessor produces a gate that compiles, reads correctly, and silently never triggers.

Pure addition: refuses only above 2^32 records, no fixture is near that, and the format gates are untouched.

**DEFERRED, with reason:** the message split. `SetIndexV64RequiresCdxText` does not live only in `helpdata_messages.cpp` -- it is also carried in `dottalkpp/data/scripts/messaging/SYSTEM_MESSAGE_TEXT_IMPORT_v1.csv` across five locales WITH CONTENT HASHES (`c36cbcc0...`). Editing the compiled text alone would desync source from the catalog fixture; doing it properly is a messaging-lane change with a regeneration step, and the `LANGUAGE` regression validates that catalog. That is real scope, not a one-line edit, and guessing at it would have been the third time today something looked cheap because only half of it was visible.

**REMAINING for M1:** message split (above); collapsing the duplicated FORMAT gate in `cmd_setindex` / `cmd_setorder` to one seam-level check, which also picks up the legacy `SET CNX` / `SET CDX` surfaces for free.

Sequencing note after the currency correction in F1: this is now **hygiene, not urgency**. The live workflow (`SET INDEX TO` -> `SET ORDER TO TAG`) is gated at both surfaces, so nothing reachable by normal use is unguarded. The value of moving it to the seam is that one rule stops being written twice -- worth doing when M2 opens `openCdx` for native-vs-LMDB selection anyway, since that is the same function and the same decision. Doing it standalone now would touch the default suite for no correctness gain.

Behavior-visible constraint whenever it IS done: the non-destructive smoke calls bare `SETCNX` at line 271 and prints `file not found`. A seam-level format gate must run AFTER the existence check or that output changes.

### M2 -- Native `.cdx` reachable on disk -> `runtime-evidenced`
**Exit:** a v64 table can attach a native `.cdx` with no LMDB env present, SEEK/SCAN correctly, and report staleness after mutation via the wasStale path landed at this baseline.
**Proof:** regression on a disk-resident native `.cdx`, mirroring `mem_proof.dts` but without the RAM mount.

### M3 -- Orthogonal selection documented and defaulted
**Exit:** format and engine independently selectable within capacity; defaults preserve today's behavior so nothing silently changes under existing users.

## 7. Relationship to XIDX-TXN-02

They meet, and the order matters.

`XIDX-TXN-02` implements incremental mutation for the native path. Its blocker N1 is that `InxPayload` is immutable by construction, and **both** `CnxBackend` and `CdxNativeBackend` read through it -- so a mutable payload serves `.cnx` and native `.cdx` at once. That is the strongest argument for doing this lane's M2 first: it makes the second consumer real and on-disk, so XIDX-TXN-02 is authored against two live callers instead of one live and one RAM-only.

The reverse order also works but wastes the wasStale signal: without M2, native-on-disk stays unreachable and the only way to exercise the batch path is the v32 lane.

**Recommended sequencing:** M1 now (pure defect repair, independent), M0 decision alongside, then M2 before XIDX-TXN-02 M1.

## 8. False-positive risks to check at M0

- Does any existing fixture or workspace rely on `SET INDEX TO <x>.cnx` being REFUSED on a v64 table (i.e. is the error load-bearing somewhere)?
- `.cdx` is used as the container extension by BOTH the LMDB and native backends. If both become reachable on disk, a `.cdx` file alone no longer tells a reader which engine owns it. Decide whether the sidecar/metadata already written by `openCdx` is sufficient to disambiguate, or whether the container needs a marker.
- `REINDEX`/`BUILDLMDB` routing assumes v64 -> BUILDLMDB. If native disk `.cdx` becomes legal, `REINDEX CDX` must dispatch on the bound backend, not the table flavor.

## 9. Provenance

Found while wiring `wasStale()` into the replace seam to earn runtime evidence for item E of the 2026-07-30 index-seam slice. The wiring is what made the batch backends' silence audible; the owner's orthogonality question is what identified the silence as a design boundary rather than a defect.

Owner `member.derald`; steward `member.ai.claude.cowork`.
