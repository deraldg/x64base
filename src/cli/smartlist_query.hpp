#pragma once

#include "xbase.hpp"
#include "cli/order_iterator.hpp"
#include "cli/expr/api.hpp"

#include <cstdint>
#include <functional>
#include <memory>
#include <string>

namespace cli::smartlist {

enum class DelFilter {
    Any,
    OnlyDeleted,
    OnlyAlive
};

struct QuerySpec {
    bool all{false};
    int limit{20};
    DelFilter del{DelFilter::Any};

    bool debug{false};

    bool haveFieldFilter{false};
    std::string fld, op, val;

    std::shared_ptr<dottalk::expr::Expr> expr_prog;
};

struct QueryStats {
    int printed{0};
    bool iter_used{false};
    cli::OrderIterSpec iter_spec{};
    std::string iter_err;
};

using RecordConsumer = std::function<bool(xbase::DbArea& a, int32_t rn, int printed_so_far)>;

bool pass_deleted_filter(const xbase::DbArea& a, DelFilter del, bool all);
bool pass_all_filters(xbase::DbArea& a, const QuerySpec& spec);

QueryStats execute_query(
    xbase::DbArea& a,
    const QuerySpec& spec,
    const RecordConsumer& consumer);

} // namespace cli::smartlist
