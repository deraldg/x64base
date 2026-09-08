// @dottalk.file v1
// subsystem: xbase
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// ==============================
// File: src/xbase/dbarea.cpp
// Core DbArea implementation.
//
// Layer boundary restoration:
// - Keep DbArea as an engine-side storage object.
// - Preserve index manager and memo manager integration.
// - Preserve locking and direct write/index-update behavior.
// - Remove shell/CLI coupling from this file.
// - Do NOT depend here on table buffering globals, cursor hooks,
//   or shell_engine() lookup.
// - Buffering, stale-field tracking, and shell event notifications
//   belong in the CLI/service layer above DbArea.
// ==============================

#include "xbase.hpp"
#include "xbase/workspace_membership.hpp"
#include "xbase/index_hooks.hpp"
#include "xbase/trigger_hooks.hpp"
#include "memo/memo_manager.hpp"

#include "xbase_locks.hpp"

#include <functional>
#include <algorithm>
#include <cctype>
#include <filesystem>
#include <system_error>
#include <string>

namespace fs = std::filesystem;

namespace xbase {

// ---------- helpers ---------------------------------------------------------
static std::string to_upper_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}

// prefer path-based API to avoid char8_t/u8string issues
static bool file_exists(const fs::path& p) {
    std::error_code ec;
    return fs::exists(p, ec) && !ec;
}

// ---------- lifecycle --------------------------------------------------------
DbArea::DbArea() = default;
DbArea::~DbArea() { try { close(); } catch(...) {} }

void DbArea::close() {
    _fp.clear();

    // An indexed composition may have attached external state.  Detach it
    // while the DbArea is still valid; a table-only build installs no hook.
    index_hooks::detach(*this);

    if (_memo_mgr) {
        _memo_mgr->close();
    } else {
        _memo_ctx.clear();
    }

    if (_fp.is_open()) {
        _fp.close();
    }
    _fp.clear();

    // In-memory tables (AIF-043 V2): detach this area's ramfs byte store. The RAM
    // file itself persists in the ramfs registry (like a .dbf on disk survives a
    // close) until erased or the virtual disk is unmounted/cleared.
    _ram.reset();
    _in_memory = false;

    // Clear canonical runtime descriptors
    _clear_paths_and_names_();

    // Clear schema/buffers & cursor flags
    _hdr = {};
    _fields.clear();
    _rawFields.clear();
    _recbuf.clear();
    _fd.clear();
    _fd_snapshot.clear();
    _fd_null.clear();   // lockstep with _fd

    // Lockstep with _fields, for the same reason _fd_null is lockstep with _fd.
    // A closed area must not carry the previous table's varchar bit layout: see
    // clearFields(). close() and clearFields() are two hand-maintained teardown
    // lists over the same members, which is HOW this member came to be missed --
    // recorded here rather than unified, because collapsing them changes what a
    // closed area reports about _extras and _null_flags and that is a separate
    // change with its own arm to write.
    _null_layout = vfp::NullBitLayout{};

    _crn = 0;
    _crn64 = 0;
    _rec_count64 = 0;
    _data_start64 = 0;
    _record_length64 = 0;
    _del = NOT_DELETED;

    _memo_kind = MemoKind::NONE;
    _kind = AreaKind::Unknown;

    // Drop per-area managers
    _memo_mgr.reset();
    _memo_ctx.clear();

    // AIF-120 I1.0: the area is no longer owned by any workspace. The ENGINE
    // slot is NOT cleared -- it is stamped once at engine construction and is a
    // property of the array position, not of whatever table is open in it.
    //
    // AIF-078 stage 2: leave the workspace's child list before dropping the
    // handle, because the handle is what says which list to leave. The
    // WORKSPACE-LOCAL slot IS cleared, because unlike the engine slot it is a
    // property of the membership, and the membership is what just ended. The
    // vacated local slot is reused by the next join rather than shifting the
    // survivors down -- a local slot is an address, and re-addressing live
    // members silently would be worse than a gap.
    // R6: only a WORK AREA ever joined, so only a work area leaves. A scratch
    // handle (no engine slot) was never a member -- see dbf_file.cpp's open().
    if (_engine_slot >= 0) workspace::leave(_ws_handle, _engine_slot);
    _ws_handle = 0;
    _ws_local_slot = -1;
    // The area handle is CLEARED, never reassigned: the next open() mints a
    // fresh one. That is what makes a stale id resolve to "gone" instead of to
    // whatever opened into this slot next -- the engine slot IS reused, and
    // this is the field that does not.
    _area_handle = 0;

    // x64/VFP extras
    // NOTE the sentinel split: 0 here, but the on-disk floor is 1
    // (dbf_create.cpp). Harmless while the slot is unwired -- nothing reads
    // it -- and a trap for whoever wires it. See xbase_64.hpp.
    _dbf_version_byte = 0x03;
    _autoq_next64 = 0;
    _table_flags = 0;
}

// Legacy helper retained; should update canonical filename
void DbArea::setFilename(std::string path) {
    fs::path p(path);
    std::error_code ec;
    if (!p.is_absolute()) p = fs::absolute(p, ec);

    _compute_paths_and_names_(p.string());
}

int DbArea::recordLength() const noexcept {
    return recLength();
}

// ---------- runtime capability model ----------------------------------------
bool DbArea::supports(AreaCapability cap) const noexcept
{
    switch (_kind) {
        case AreaKind::V32:
            switch (cap) {
                case AreaCapability::TupleOps:
                    return false;
                default:
                    return true;
            }

        case AreaKind::V64:
            return true;

        case AreaKind::V128:
            return true;

        case AreaKind::Tup:
            switch (cap) {
                case AreaCapability::ReadRows:
                case AreaCapability::TupleOps:
                    return true;
                default:
                    return false;
            }

        case AreaKind::Unknown:
        default:
            return false;
    }
}

// ---------- canonical descriptor computation --------------------------------
void DbArea::_compute_paths_and_names_(const std::string& abs_dbf_path) {
    std::error_code ec;

    // 1) Canonicalize path (prefer weakly_canonical to avoid throws on odd segments)
    fs::path p(abs_dbf_path);
    if (!p.is_absolute()) {
        p = fs::absolute(p, ec); // best effort
    } else {
        fs::path wc = fs::weakly_canonical(p, ec);
        if (!ec && !wc.empty()) p = std::move(wc);
    }

    // 2) Stamp canonical DBF descriptors
    _dbf_abs_path = p.string();
    _dbf_dir      = p.parent_path().string();
    _dbf_ext      = p.has_extension() ? p.extension().string() : std::string{};
    _dbf_basename = p.stem().string();
    _logical_name = to_upper_copy(_dbf_basename);

    // 3) Memo detection (co-located only): prefer .fpt, else .dbt
    const fs::path fpt = p.parent_path() / (_dbf_basename + ".fpt");
    const fs::path dbt = p.parent_path() / (_dbf_basename + ".dbt");

    _memo_abs_path.clear();
    _memo_kind = MemoKind::NONE;

    if (file_exists(fpt)) {
        _memo_abs_path = fpt.string();
        _memo_kind = MemoKind::FPT;
    } else if (file_exists(dbt)) {
        _memo_abs_path = dbt.string();
        _memo_kind = MemoKind::DBT;
    }
}

void DbArea::_clear_paths_and_names_() noexcept {
    _dbf_abs_path.clear();
    _dbf_dir.clear();
    _dbf_basename.clear();
    _dbf_ext.clear();
    _logical_name.clear();
    _memo_abs_path.clear();
    _memo_kind = MemoKind::NONE;
}

// ---------- memo manager access ---------------------------------------------
dottalk::memo::MemoManager& DbArea::memoManager() {
    if (!_memo_mgr) {
        _memo_mgr = std::make_unique<dottalk::memo::MemoManager>(*this, _memo_ctx);
    }
    return *_memo_mgr;
}

// ---------- replace funnel ---------------------------------------------------
// Engine-only direct-write replace path.
// Notes:
// - No table-buffer orchestration here.
// - No cursor_hook notifications here.
// - No shell area lookup here.
// - Higher layers may wrap this function with buffering/events as needed.
// ONE ENVELOPE, TWO STAGERS.
//
// replaceFieldStored() and replaceFieldNull() differ by a single line -- WHAT they
// stage before the write -- and agree on everything that makes a write safe: the
// record lock, the index snapshot taken BEFORE the change, the write itself, the
// unlock, index maintenance, and the trigger fire. Duplicating that for the null
// path would have produced two 90-line functions obliged to stay in step, which is
// the defect shape this project keeps finding one layer up. The body below is the
// original replaceFieldStored() moved verbatim; only the staging call is a
// parameter now.
bool DbArea::replaceFieldEnveloped_(int field1,
                                    const std::function<bool()>& stage,
                                    std::string* err)
{
    if (err) err->clear();

    if (!isOpen()) {
        if (err) *err = "no file open";
        return false;
    }

    if (field1 < 1 || field1 > fieldCount()) {
        if (err) *err = "invalid field index";
        return false;
    }

    const std::uint64_t rn = recno64();
    if (rn == 0) {
        if (err) *err = "no current record";
        return false;
    }

    std::string lock_err;
    if (!xbase::locks::try_lock_record(*this, rn, &lock_err)) {
        if (err) {
            *err = lock_err.empty()
                ? std::string("record is locked")
                : std::string("record is locked (") + lock_err + ")";
        }
        return false;
    }

    bool ok = false;
    index_hooks::Snapshot before_snap;

    try {
        before_snap = index_hooks::capture(*this);

        ok = stage() && writeCurrent();
    }
    catch (...) {
        ok = false;
    }

    xbase::locks::unlock_record(*this, rn);

    if (!ok) {
        if (err) *err = "write failed";
        return false;
    }

    // Index maintenance runs after the physical write succeeded. A failure here
    // does NOT undo the record write, so this still returns true: the caller's
    // "did the write land" question is answered yes.
    //
    // What it must not do is swallow the failure. The apply_replace() result was
    // previously discarded, so an index that silently stopped tracking this
    // record produced no message, no stale mark, and no return-code difference --
    // the failure was invisible to every caller. Report it through `err` and let
    // the caller decide what to do (warn, mark the field stale, both).
    //
    // Contract for callers: a `true` return with a NON-EMPTY `err` means
    // "record written, index not maintained" -- treat the index as stale for the
    // affected field. Stale-index reporting itself belongs above DbArea.
    bool index_ok = true;
    try {
        const auto after_snap = index_hooks::capture(*this);
        if (!index_hooks::apply_replace(*this, before_snap, after_snap, rn)) {
            index_ok = false;
            if (err && err->empty()) *err = "index update failed";
        }
    }
    catch (const std::exception& ex) {
        index_ok = false;
        if (err && err->empty()) *err = std::string("index update failed (") + ex.what() + ")";
    }
    catch (...) {
        index_ok = false;
        if (err && err->empty()) *err = "index update failed";
    }

    // AIF-087 Phase-1 (B1): data-trigger fire after successful index apply_replace.
    // Not cursor_hook. No fire when index maintenance failed. Buffered path never
    // reaches this function.
    if (index_ok) {
        trigger_hooks::fire_field_replace(*this, field1, rn);
    }

    return true;
}

// A VALUE ASSIGNMENT ENDS A NULL, AND UNTIL 2026-09-05 IT DID NOT.
//
// set() writes `_fd[idx]` and has never touched `_fd_null[idx]` -- correctly, it
// is a bare stager. storeFieldsToBuffer() then RECOMPUTES every null bit FROM
// `_fd_null`. So a value written over a null cell put the new value on disk and
// RE-COMMITTED THE STALE NULL BIT in the same record write. The cell then
// answered two different things depending on who asked:
//
//     LIST     ->  .NULL.
//     ? VNAME  ->  restored
//     ? ISNULL(VNAME) -> .T.
//
// Measured 2026-09-05 on rec 3 of NULLSPEC, and it survived a close and reopen
// because it reached the disk. Found by vfp_null_assertions.dts on its first run
// (NL_T11/T12/T14/T16), which is the only instrument that ever asked -- every
// earlier proof in this lane ran one direction, set-then-read, including the VFP
// acceptance scripts. A feature proven in one direction is not proven.
//
// AND THERE WAS NO WAY BACK. replaceFieldNull(field, false) has been correct and
// callable since f641fb38a and its ONLY caller in the tree was a unit test
// (test_vfp_set_null.cpp arm C). No command path passed false, so once a cell was
// null the shell could not un-null it. Sixth AIF-079 instance in this lane and
// the first that was costing something rather than merely sitting there.
//
// WHY THE CLEAR IS HERE AND NOT IN set(). set() has callers in cmd_calcwrite,
// cmd_commit, cmd_replace_multi, cmd_validate_unique, hierarchy_service,
// edu_text, trigger_hooks and index_manager. Giving it an opinion about nulls
// would hand that opinion to all of them at once, including paths that stage a
// value they did not author. This funnel is where a cell is REPLACED, which is
// the act that ends a null, so this is where the two halves are kept in step.
//
// WHY THE fieldIsNullable() GUARD IS LOAD-BEARING. setFieldNull() returns false
// for a field whose descriptor carries no null flag -- which is EVERY field of
// every non-VFP table in the product. Staged as `setFieldNull(f,false) &&
// set(f,v)` it would short-circuit and make every REPLACE everywhere fail. The
// guard asks the table first and the return is deliberately ignored: past the
// guard the only remaining failure is an out-of-range index, and the envelope
// has already rejected those.
//
// Every caller of this funnel writes a real value, so clearing is right for all
// of them -- including cmd_commit, whose buffered path cannot carry a NULL at
// all (the buffer stores one value string per field and refuses NULL for exactly
// that reason), so a committed value is always a value.
bool DbArea::replaceFieldStored(int field1, const std::string& stored_value,
                                std::string* err)
{
    return replaceFieldEnveloped_(
        field1,
        [&] {
            if (fieldIsNullable(field1)) setFieldNull(field1, false);
            return set(field1, stored_value);
        },
        err);
}

// Set (or clear) this field's NULL state and write the record, through the SAME
// envelope a value write uses.
//
// THE INDEX SNAPSHOT IS WHY THIS GOES THROUGH THE ENVELOPE AT ALL. Nulling an
// indexed field changes what that record sorts as, exactly as replacing its value
// does. A null written outside the envelope would leave the index pointing at the
// old key with nothing marked stale -- the IDXSTALE shape, and the same one
// VALIDATE UNIQUE ... REPAIR was caught in when it used set()+writeCurrent()
// directly (VUREPAIR). What the index backends make of a null key is NOT settled
// here and is not claimed: this guarantees the maintenance hook RUNS, not that
// every backend orders nulls the way anyone expects.
//
// Refuses via setFieldNull() when the field is not nullable or the table has no
// `_NullFlags` column; the record is not written in that case.
bool DbArea::replaceFieldNull(int field1, bool make_null, std::string* err)
{
    return replaceFieldEnveloped_(
        field1, [&] { return setFieldNull(field1, make_null); }, err);
}

} // namespace xbase
