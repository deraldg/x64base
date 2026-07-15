#include "tuple/tuple_graph_cursor.hpp"

#include <algorithm>
#include <cctype>
#include <exception>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "cli/expr/api.hpp"
#include "cli/expr/ast.hpp"
#include "cli/workarea_cursor_restore.hpp"
#include "expr_tuple_glue.hpp"
#include "set_relations.hpp"
#include "tuple/root_recno_source.hpp"
#include "tuple_builder.hpp"

namespace dottalk::tupleaugment {

namespace {

static std::string trim(std::string s) {
    auto issp = [](unsigned char c) { return std::isspace(c) != 0; };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), [&](unsigned char c) { return !issp(c); }));
    s.erase(std::find_if(s.rbegin(), s.rend(), [&](unsigned char c) { return !issp(c); }).base(), s.end());
    return s;
}

static bool safe_open(const xbase::DbArea& area) {
    try { return area.isOpen(); } catch (...) { return false; }
}

static int safe_reccount(const xbase::DbArea& area) {
    try { return static_cast<int>(area.recCount()); } catch (...) { return 0; }
}

static bool goto_read(xbase::DbArea& area, int rn) {
    try {
        if (rn < 1 || rn > safe_reccount(area)) return false;
        if (!area.gotoRec(rn)) return false;
        return area.readCurrent();
    } catch (...) {
        return false;
    }
}

} // namespace

struct TupleGraphCursor::Impl {
    xbase::DbArea& root;
    TupleGraphCursorOptions opt;
    TupleGraphCursorStats stats;

    WorkAreaCursorRestore restore;
    std::vector<int> root_recnos;
    std::size_t pos{0};

    std::unique_ptr<dottalk::expr::Expr> filter_prog;

    bool opened{false};
    bool closed{false};

    Impl(xbase::DbArea& r, TupleGraphCursorOptions o)
        : root(r), opt(std::move(o)) {}

    ~Impl() { close(); }

    bool compile_filter(std::string& error) {
        error.clear();
        opt.for_expr = trim(std::move(opt.for_expr));
        stats.for_expr = opt.for_expr;
        if (opt.for_expr.empty()) return true;

        auto cr = dottalk::expr::compile_where(opt.for_expr);
        if (!(cr && cr.program)) {
            error = cr.error.empty() ? "invalid FOR expression" : cr.error;
            return false;
        }

        filter_prog = std::move(cr.program);
        return true;
    }

    bool build_tuple(dottalk::TupleRow& out, std::string& error) {
        dottalk::TupleBuildOptions build_opt;
        build_opt.strict_fields = opt.strict_fields;
        build_opt.refresh_relations = true;
        build_opt.header_area_prefix = opt.header_area_prefix;

        auto result = dottalk::build_tuple_from_spec(opt.tuple_spec.empty() ? "*" : opt.tuple_spec, build_opt);
        if (!result.ok) {
            error = result.error.empty() ? "tuple build failed" : result.error;
            return false;
        }

        out = std::move(result.row);
        return true;
    }

    bool passes_tuple_filter(const dottalk::TupleRow& row) const {
        if (!filter_prog) return true;
        try {
            auto rv = dottalk::exprglue::make_record_view(row);
            return filter_prog->eval(rv);
        } catch (...) {
            return false;
        }
    }

    void close() noexcept {
        if (closed) return;
        closed = true;
        std::string ignored;
        (void)restore.restore(ignored);
        stats.cursors_restored = restore.was_restored();
    }
};

TupleGraphCursor::TupleGraphCursor(xbase::DbArea& root, TupleGraphCursorOptions options)
    : impl_(std::make_unique<Impl>(root, std::move(options))) {}

TupleGraphCursor::~TupleGraphCursor() = default;

bool TupleGraphCursor::open(std::string& error) {
    if (!impl_) {
        error = "tuple graph cursor not initialized";
        return false;
    }

    error.clear();
    if (!safe_open(impl_->root)) {
        error = "no file open";
        return false;
    }

    impl_->stats = TupleGraphCursorStats{};
    impl_->root_recnos.clear();
    impl_->pos = 0;

    // WorkAreaCursorRestore snapshots in its constructor.  Refreshing here makes
    // the relation graph current before root recno collection begins.
    try { relations_api::refresh_if_enabled(); } catch (...) {}

    RootRecnoSourceOptions ropt;
    ropt.use_active_order = impl_->opt.use_active_order;
    ropt.include_deleted = impl_->opt.include_deleted;
    ropt.only_deleted = impl_->opt.only_deleted;

    RootRecnoSource source(impl_->root, ropt);
    if (!source.collect(impl_->root_recnos, error)) return false;

    const auto& rs = source.stats();
    impl_->stats.order_status = rs.order_status;
    impl_->stats.ordered = rs.ordered;
    impl_->stats.order_fallback = rs.order_fallback;
    impl_->stats.first_root_recno = rs.first_recno;
    impl_->stats.last_root_recno = rs.last_recno;

    impl_->stats.root_table_rec_count = rs.table_rec_count;
    impl_->stats.root_candidate_recnos = rs.candidate_recnos;
    impl_->stats.root_recnos_collected = rs.recnos_collected;
    impl_->stats.root_skipped_read = rs.skipped_read;
    impl_->stats.root_skipped_deleted = rs.skipped_deleted;
    impl_->stats.root_skipped_out_of_range = rs.skipped_out_of_range;
    impl_->stats.root_skipped_read_recnos = rs.skipped_read_recnos;
    impl_->stats.root_skipped_deleted_recnos = rs.skipped_deleted_recnos;
    impl_->stats.root_skipped_out_of_range_recnos = rs.skipped_out_of_range_recnos;

    if (!impl_->compile_filter(error)) return false;

    impl_->opened = true;
    return true;
}

bool TupleGraphCursor::next(dottalk::TupleRow& out, std::string& error) {
    error.clear();
    if (!impl_ || !impl_->opened) {
        error = "tuple graph cursor not open";
        return false;
    }

    while (impl_->pos < impl_->root_recnos.size()) {
        const int rn = impl_->root_recnos[impl_->pos++];
        ++impl_->stats.root_visited;

        if (!goto_read(impl_->root, rn)) continue;

        // Relationship synchronization must occur after root positioning and
        // before tuple projection.  tuple_builder also refreshes by option, but
        // this explicit refresh documents and preserves the cursor contract.
        try { relations_api::refresh_if_enabled(); } catch (...) {}

        dottalk::TupleRow row;
        if (!impl_->build_tuple(row, error)) return false;
        if (row.empty()) continue;

        if (!impl_->passes_tuple_filter(row)) continue;

        out = std::move(row);
        ++impl_->stats.tuples_emitted;
        return true;
    }

    return false; // EOF, error remains empty
}

void TupleGraphCursor::close() noexcept {
    if (impl_) impl_->close();
}

const TupleGraphCursorStats& TupleGraphCursor::stats() const {
    return impl_->stats;
}

} // namespace dottalk::tupleaugment
