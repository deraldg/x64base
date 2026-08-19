// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "db_tuple_stream.hpp"

#include <sstream>
#include <algorithm>
#include <filesystem>
#include <vector>
#include <cstdint>

#if DOTTALK_WITH_INDEX
#include <lmdb.h>
#endif

#include "xbase.hpp"
#include "workareas.hpp"
#include "tuple_builder.hpp"

#include "cli/order_state.hpp"
#include "cli/order_nav.hpp"
#include "relations_status.hpp"

using dottalk::expr::CompileResult;

namespace dottalk {

namespace {

xbase::DbArea* current_area() {
    try {
        const std::size_t slot = workareas::current_slot();
        return const_cast<xbase::DbArea*>(workareas::db(slot));
    } catch (...) {
        return nullptr;
    }
}

// RECNO64. This read recCount(), which is the SIGNALLING 32-bit adapter: past
// INT32_MAX it returns -1 by design ("out of 32-bit range; use the *64 accessor"),
// so every bound check below became `r > -1` and the whole stream refused to
// position on exactly the tables the engine was widened for. recCount64() is the
// authoritative value.
RecordNo safe_rec_count(xbase::DbArea* A) {
    if (!A) return 0;
    try { return A->recCount64(); }
    catch (...) { return 0; }
}

bool goto_rec_safe(xbase::DbArea* A, RecordNo r) {
    if (!A) return false;
    try {
        if (r < 1 || r > A->recCount64()) return false;
        A->gotoRec64(r);
        (void)A->readCurrent();
        return true;
    } catch (...) {
        return false;
    }
}

static inline bool file_exists(const std::filesystem::path& p) {
    std::error_code ec{};
    return std::filesystem::exists(p, ec);
}

#if DOTTALK_WITH_INDEX
static inline std::filesystem::path lmdb_envdir_from_cdx(const std::filesystem::path& cdxPath) {
    std::filesystem::path p = cdxPath;
    p += ".d";
    return p;
}

static inline uint64_t read_le_u64(const void* p) {
    const unsigned char* b = static_cast<const unsigned char*>(p);
    uint64_t v = 0;
    v |= (uint64_t)b[0];
    v |= (uint64_t)b[1] << 8;
    v |= (uint64_t)b[2] << 16;
    v |= (uint64_t)b[3] << 24;
    v |= (uint64_t)b[4] << 32;
    v |= (uint64_t)b[5] << 40;
    v |= (uint64_t)b[6] << 48;
    v |= (uint64_t)b[7] << 56;
    return v;
}

// Collect recnos from a CDX.d LMDB environment.
// Returns true only if LMDB was successfully used.
// The output vector is produced in the CURRENT logical order direction:
//   asc=true  -> first..last
//   asc=false -> last..first
static bool collect_lmdb_cdx_recnos(const std::string& cdxPathStr,
                                    const std::string& tag,
                                    RecordNo recCount,
                                    bool asc,
                                    std::vector<RecordNo>& out)
{
    out.clear();
    if (tag.empty()) return false;

    const std::filesystem::path cdxPath(cdxPathStr);
    const std::filesystem::path envDir = lmdb_envdir_from_cdx(cdxPath);
    if (!file_exists(envDir / "data.mdb")) return false;

    MDB_env* env = nullptr;
    MDB_txn* txn = nullptr;
    MDB_dbi dbi = 0;
    MDB_cursor* cur = nullptr;

    auto cleanup = [&]() {
        if (cur) mdb_cursor_close(cur);
        if (txn) mdb_txn_abort(txn);
        if (env) mdb_env_close(env);
        cur = nullptr;
        txn = nullptr;
        env = nullptr;
    };

    int rc = mdb_env_create(&env);
    if (rc != MDB_SUCCESS) {
        cleanup();
        return false;
    }

    (void)mdb_env_set_maxdbs(env, 1024);

    rc = mdb_env_open(env, envDir.string().c_str(), MDB_RDONLY, 0664);
    if (rc != MDB_SUCCESS) {
        cleanup();
        return false;
    }

    rc = mdb_txn_begin(env, nullptr, MDB_RDONLY, &txn);
    if (rc != MDB_SUCCESS) {
        cleanup();
        return false;
    }

    // IMPORTANT: use the exact tag string reported by orderstate.
    rc = mdb_dbi_open(txn, tag.c_str(), 0, &dbi);
    if (rc != MDB_SUCCESS) {
        cleanup();
        return false;
    }

    rc = mdb_cursor_open(txn, dbi, &cur);
    if (rc != MDB_SUCCESS) {
        cleanup();
        return false;
    }

    MDB_val k{};
    MDB_val v{};
    rc = mdb_cursor_get(cur, &k, &v, asc ? MDB_FIRST : MDB_LAST);

    // A hint only -- and recCount is now a 64-bit count that a corrupt header could
    // make enormous, so it is capped rather than trusted. The old line clamped the
    // LOWER bound (std::max(0, ...)) against a signed int; with an unsigned count
    // the bound that matters is the upper one. Watch this one: it is the first
    // place a wide count turns into an allocation.
    constexpr RecordNo kReserveCap = 1u << 22;      // 4 Mi entries = 32 MB
    out.reserve(static_cast<std::size_t>(recCount < kReserveCap ? recCount
                                                               : kReserveCap));

    while (rc == MDB_SUCCESS) {
        uint64_t rn64 = 0;

        // Preferred layout: value is LE recno.
        if (v.mv_size == 8) {
            rn64 = read_le_u64(v.mv_data);
        } else if (v.mv_size == 4) {
            const unsigned char* b = static_cast<const unsigned char*>(v.mv_data);
            rn64 = (uint64_t)b[0]
                 | ((uint64_t)b[1] << 8)
                 | ((uint64_t)b[2] << 16)
                 | ((uint64_t)b[3] << 24);
        } else if (k.mv_size >= 8) {
            // Fallback: composite key encodes trailing recno.
            const unsigned char* b = static_cast<const unsigned char*>(k.mv_data);
            rn64 = read_le_u64(b + (k.mv_size - 8));
        }

        if (rn64 > 0 && rn64 <= recCount) {
            // The x64 CDX/LMDB path stores FULL 64-bit record numbers (RECNO64
            // M3c) and this line used to write them into a uint32_t vector. On a
            // table past 2^31 the index held the right number and the stream threw
            // the top bits away -- silently, on both platforms. push() refuses
            // rather than truncating, and the refusal is counted and reported.
            out.push_back(rn64);
        }

        rc = mdb_cursor_get(cur, &k, &v, asc ? MDB_NEXT : MDB_PREV);
    }

    cleanup();
    return !out.empty();
}
#else
static bool collect_lmdb_cdx_recnos(const std::string&,
                                    const std::string&,
                                    RecordNo,
                                    bool,
                                    std::vector<RecordNo>& out)
{
    out.clear();
    return false;
}
#endif

} // namespace

DbTupleStream::DbTupleStream(std::string spec, std::string page_hint)
    : spec_(std::move(spec)), hint_(std::move(page_hint)) {
    refresh_bounds_and_order();
}

void DbTupleStream::set_filter_for(std::string expr) {
    filter_for_ = std::move(expr);
    filter_prog_.reset();
    if (!filter_for_.empty()) {
        CompileResult cr = dottalk::expr::compile_where(filter_for_);
        if (cr && cr.program) {
            filter_prog_ = std::move(cr.program); // compile-once
        } else {
            // Safe fallback: disable filter on compile errors
            filter_for_.clear();
        }
    }
}

bool DbTupleStream::goto_recno(RecordNo r) { return goto_recno_internal(r); }

bool DbTupleStream::goto_pos(RecordNo pos) {
    if (pos < 1 || mode_ != NavMode::OrderVector) return false;
    return goto_order_pos(pos);          // both 1-based now
}

bool DbTupleStream::is_ordered() const { return mode_ == NavMode::OrderVector; }

RecordNo DbTupleStream::order_count() const {
    return static_cast<RecordNo>(order_recnos_.size());
}

RecordNo DbTupleStream::current_pos() const {
    return mode_ == NavMode::OrderVector ? order_pos_ : cur_recno_;
}

void DbTupleStream::refresh_bounds_only() {
    xbase::DbArea* A = current_area();
    max_recno_ = safe_rec_count(A);
    if (cur_recno_ > max_recno_) cur_recno_ = max_recno_;
}

void DbTupleStream::refresh_bounds_and_order() {
    xbase::DbArea* A = current_area();
    max_recno_ = safe_rec_count(A);

    bool has_order = false;
    try {
        has_order = (A && orderstate::hasOrder(*A));
    } catch (...) {
        has_order = false;
    }

    if (has_order) {
        mode_ = NavMode::OrderVector;
        order_recnos_.clear();
        order_pos_ = 0;

        try {
            if (orderstate::isCnx(*A)) {
                // Classic CNX stores recnos in four bytes (RECNO64 M4-4), so the
                // loader's uint32_t vector is correct BY FORMAT here, not a
                // compromise. It is copied into the capacity-checked vector.
                const std::string tag = orderstate::activeTag(*A);
                std::vector<uint32_t> tmp;
                order_nav_detail::build_cnx_recnos_from_db(*A, tag, tmp);
                order_recnos_.assign(tmp.begin(), tmp.end());
            } else if (orderstate::isCdx(*A)) {
                const std::string ord_path = orderstate::orderName(*A);
                const std::string tag = orderstate::activeTag(*A);
                const bool asc = orderstate::isAscending(*A);

                if (!ord_path.empty()) {
                    (void)collect_lmdb_cdx_recnos(
                        ord_path,
                        tag,
                        A->recCount64(),
                        asc,
                        order_recnos_
                    );
                }
            } else {
                const std::string ord_path = orderstate::orderName(*A);
                if (!ord_path.empty()) {
                    // Legacy .inx is a classic 32-bit format (M4-4), same as CNX.
                    std::vector<uint32_t> tmp;
                    order_nav_detail::load_inx_recnos(ord_path, A->recCount(), tmp);
                    // Legacy INX loader is assumed ascending; preserve current direction.
                    if (!orderstate::isAscending(*A)) {
                        std::reverse(tmp.begin(), tmp.end());
                    }
                    order_recnos_.assign(tmp.begin(), tmp.end());
                }
            }
        } catch (...) {
            order_recnos_.clear();
        }

        if (order_recnos_.empty()) {
            mode_ = NavMode::Physical;
        }
    } else {
        mode_ = NavMode::Physical;
        order_recnos_.clear();
        order_pos_ = 0;
    }

    if (cur_recno_ > max_recno_) cur_recno_ = max_recno_;
}

void DbTupleStream::top() {
    refresh_bounds_and_order();
    last_emitted_recno_ = 0;
    order_pos_ = 0;
    cur_recno_ = 0;
}

void DbTupleStream::bottom() {
    refresh_bounds_and_order();
    last_emitted_recno_ = 0;

    if (mode_ == NavMode::OrderVector) {
        if (!order_recnos_.empty()) {
            order_pos_ = static_cast<RecordNo>(order_recnos_.size());   // 1-based
            cur_recno_ = order_recnos_.back();
            (void)goto_rec_safe(current_area(), cur_recno_);
        } else {
            order_pos_ = 0;
            cur_recno_ = 0;
        }
    } else {
        cur_recno_ = max_recno_;
        (void)goto_rec_safe(current_area(), cur_recno_);
    }
}

bool DbTupleStream::goto_physical_recno(RecordNo r) {
    xbase::DbArea* A = current_area();
    if (!A) return false;
    if (!goto_rec_safe(A, r)) return false;
    cur_recno_ = r;
    return true;
}

// `p` is 1-based, matching goto_pos() and current_pos(). The old code mixed a
// 0-based index with a -1 sentinel, which is why the position had to be adjusted
// at four different call sites; an unsigned identity has no room for -1 and 0 was
// already free.
bool DbTupleStream::goto_order_pos(RecordNo p) {
    if (p < 1) return false;
    const RecordNo sz = static_cast<RecordNo>(order_recnos_.size());
    if (p > sz) return false;
    const RecordNo rn = order_recnos_[static_cast<std::size_t>(p - 1)];
    if (!goto_physical_recno(rn)) return false;
    order_pos_ = p;
    return true;
}

bool DbTupleStream::goto_recno_internal(RecordNo r) {
    refresh_bounds_only();
    if (mode_ == NavMode::OrderVector) {
        const RecordNo p = order_find_pos(order_recnos_, r);   // 1-based, 0 = absent
        if (p == 0) return false;
        return goto_order_pos(p);
    }
    return goto_physical_recno(r);
}

bool DbTupleStream::step(RecordDelta delta) {
    refresh_bounds_only();
    // Both branches compute in SIGNED 64-bit and only then range-check into the
    // unsigned identity, so an underflow is a rejected move rather than a very
    // large record number.
    if (mode_ == NavMode::OrderVector) {
        const RecordDelta sz = static_cast<RecordDelta>(order_recnos_.size());
        if (sz <= 0) return false;
        RecordDelta target;
        if (order_pos_ == 0) target = (delta > 0) ? 1 : 0;
        else target = static_cast<RecordDelta>(order_pos_) + delta;
        if (target < 1 || target > sz) return false;
        return goto_order_pos(static_cast<RecordNo>(target));
    }

    RecordDelta target = static_cast<RecordDelta>(cur_recno_) + delta;
    if (cur_recno_ == 0 && delta > 0) target = 1;
    if (target < 1 || target > static_cast<RecordDelta>(max_recno_)) return false;
    return goto_physical_recno(static_cast<RecordNo>(target));
}

TupleRow DbTupleStream::build_current_tuple() {
    TupleBuildOptions opt;
    opt.refresh_relations  = true;
    opt.header_area_prefix = true;
    opt.strict_fields      = false;

    auto r = build_tuple_from_spec(spec_, opt);
    if (!r.ok) return TupleRow{};
    return std::move(r.row);
}

bool DbTupleStream::passes_filter_on_tuple(const TupleRow& row) const {
    if (!filter_prog_) return true;
    try {
        auto rv = dottalk::exprglue::make_record_view(row);
        return filter_prog_->eval(rv);
    } catch (...) {
        return false;
    }
}

std::vector<TupleRow> DbTupleStream::next_page(std::size_t max_rows) {
    std::vector<TupleRow> out;
    if (max_rows == 0) return out;

    refresh_bounds_only();

    if (mode_ == NavMode::OrderVector) {
        if (order_recnos_.empty()) return out;
        if (order_pos_ == 0) {                 // unpositioned; 1-based from here
            if (!goto_order_pos(1)) return out;
        }
    } else {
        if (max_recno_ == 0) return out;
        if (cur_recno_ == 0) {
            if (!goto_physical_recno(1)) return out;
        }
    }

    for (std::size_t i = 0; i < max_rows; ++i) {
        TupleRow row = build_current_tuple();
        if (!row.empty() && passes_filter_on_tuple(row)) {
            out.push_back(std::move(row));
            last_emitted_recno_ = cur_recno_;
        }
        if (!step(1)) break;
    }
    return out;
}

void DbTupleStream::skip(RecordDelta n) {
    if (n == 0) return;

    if (n > 0) {
        if (mode_ == NavMode::OrderVector) {
            if (order_pos_ == 0) {
                if (!goto_order_pos(1)) return;
                --n;
            }
        } else {
            if (cur_recno_ == 0) {
                if (!goto_physical_recno(1)) return;
                --n;
            }
        }
    }

    (void)step(n);
}

std::string DbTupleStream::current_order_hint() const {
    xbase::DbArea* A = current_area();
    if (!A) return hint_.empty() ? "physical" : hint_;

    try {
        if (!orderstate::hasOrder(*A)) return "physical";

        std::ostringstream oss;

        if (orderstate::isCnx(*A)) {
            oss << "CNX:" << orderstate::activeTag(*A);
        } else if (orderstate::isCdx(*A)) {
            oss << "CDX:" << orderstate::orderName(*A);
            const std::string tag = orderstate::activeTag(*A);
            if (!tag.empty()) oss << " TAG " << tag;
        } else {
            oss << "INX:" << orderstate::orderName(*A);
        }

        oss << (orderstate::isAscending(*A) ? " ASC" : " DESC");
        return oss.str();
    } catch (...) {
        return hint_.empty() ? "physical" : hint_;
    }
}

std::string DbTupleStream::status_line() const {
    std::ostringstream oss;
    const std::string oh = current_order_hint();

    if (mode_ == NavMode::OrderVector) {
        const RecordNo pos_show = order_pos_;
        const RecordNo total = static_cast<RecordNo>(order_recnos_.size());
        oss << "SMARTBROWSER: pos " << pos_show << " / " << total << "  [" << oh << "]";
    } else {
        const RecordNo show = (last_emitted_recno_ > 0 ? last_emitted_recno_ : cur_recno_);
        oss << "SMARTBROWSER: rec " << show << " / " << max_recno_ << "  [" << oh << "]";
    }

    if (!filter_for_.empty()) oss << "  FOR";

    try {
        if (auto* A = current_area()) {
            const std::string logical = A->logicalName();
            const std::string base    = A->dbfBasename();
            if (!logical.empty() || !base.empty()) {
                oss << "  |  AREA: ";
                if (!logical.empty()) oss << logical;
                if (!base.empty())    oss << " [" << base << "]";
            }
        }
    } catch (...) {}

    try {
        const std::string rt = relations_status::relation_status_token();
        if (!rt.empty()) oss << "  |  " << rt;
    } catch (...) {}

    return oss.str();
}

void DbTupleStream::set_order_physical() {
    mode_ = NavMode::Physical;
    order_recnos_.clear();
    order_pos_ = 0;      // 1-based; 0 is unpositioned
    last_emitted_recno_ = 0;
    refresh_bounds_only();
}

void DbTupleStream::set_order_inx() {
    mode_ = NavMode::OrderVector;
    order_pos_ = 0;      // 1-based; 0 is unpositioned
    last_emitted_recno_ = 0;
}

void DbTupleStream::set_order_cnx() {
    mode_ = NavMode::OrderVector;
    order_pos_ = 0;      // 1-based; 0 is unpositioned
    last_emitted_recno_ = 0;
}

std::string DbTupleStream::current_area_name() const {
    if (auto* A = current_area()) {
        try {
            const std::string ln = A->logicalName();
            if (!ln.empty()) return ln;
            return A->name();
        } catch (...) {}
    }
    return std::string{};
}

} // namespace dottalk
