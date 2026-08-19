// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
#include <string>
#include <vector>
#include <cstdint>
#include <limits>
#include <memory>
#include "tuple_stream.hpp"
#include "tuple_types.hpp"
#include "cli/expr/api.hpp"
#include "cli/expr/ast.hpp"
#include "expr_tuple_glue.hpp"
namespace dottalk {

// 1-based position of `rn` in `v`, or 0 if absent. Unsigned identity, so 0 is the
// "not found" value and there is no -1 to smuggle through an unsigned type.
inline RecordNo order_find_pos(const std::vector<RecordNo>& v, RecordNo rn) {
    for (std::size_t i = 0; i < v.size(); ++i)
        if (v[i] == rn) return static_cast<RecordNo>(i) + 1;
    return 0;
}

class DbTupleStream final : public TupleStream {
public:
    explicit DbTupleStream(std::string spec, std::string page_hint = "");
    void top() override;
    void bottom() override;
    void skip(RecordDelta n) override;
    bool goto_record(RecordNo recno) override { return goto_recno(recno); }
    std::vector<TupleRow> next_page(std::size_t max_rows) override;
    std::string status_line() const override;
    void set_filter_for(std::string expr);
    void set_spec(std::string spec) { spec_ = std::move(spec); top(); }
    std::string current_filter() const { return filter_for_; }
    const std::string& current_spec() const { return spec_; }
    bool goto_pos(RecordNo pos);
    bool goto_recno(RecordNo r);
    bool is_ordered() const;
    RecordNo order_count() const;
    // 1-based position in the order vector, or 0 when unpositioned/unordered.
    RecordNo current_pos() const;
    void set_order_physical();
    void set_order_inx();
    void set_order_cnx();
    std::string current_area_name() const;
private:
    enum class NavMode : uint8_t { Physical = 0, OrderVector = 1 };
    std::string spec_;
    std::string hint_;
    std::string filter_for_;
    std::unique_ptr<dottalk::expr::Expr> filter_prog_;
    NavMode     mode_              = NavMode::Physical;
    RecordNo    cur_recno_         = 0;
    RecordNo    max_recno_         = 0;
    // RECNO64 / AIF-120 R68. The order vector is the ONE place where widening has
    // a cost worth thinking about: at pinocchio scale (5,501,358 rows) it is 22 MB
    // narrow and 44 MB wide, and the overwhelming majority of tables never need
    // the second. So the width is chosen ONCE, from the resolved area kind, the
    // way detect_area_kind_from_version() chooses once from the version byte --
    // never per access. A classic 32-bit table cannot hold a recno above
    // UINT32_MAX, so the narrow vector there is provably sufficient rather than a
    // compromise: one engine API, three capacities.
    // PURE 64 (owner ruling, R70). An earlier version made this a two-width
    // variant to save 22 MB on a pinocchio-scale ordered browse. The owner ruled
    // the memory is not worth the second code path: a record number is uint64_t
    // everywhere, with no narrow backing to choose, mis-select or forget to widen.
    // What the variant was protecting against -- silent truncation -- is now
    // impossible rather than refused.
    std::vector<RecordNo> order_recnos_;
    // 0 = unpositioned. Was -1, which cost a signed type for one sentinel.
    RecordNo    order_pos_         = 0;
    RecordNo    last_emitted_recno_= 0;
    void refresh_bounds_only();
    void refresh_bounds_and_order();
    bool goto_physical_recno(RecordNo r);
    bool goto_order_pos(RecordNo p);        // 1-based
    bool goto_recno_internal(RecordNo r);
    bool step(RecordDelta delta);
    TupleRow build_current_tuple();
    bool passes_filter_on_tuple(const TupleRow& row) const;
    std::string current_order_hint() const;
};
} // namespace dottalk
