// @dottalk.file v1
// subsystem: cli
// layer: command
// owns:
// project: project.x64base.runtime
// lane: AIF-074
// owner: member.derald
// status: experimental

// @dottalk.usage v1
// owner: DOT|EVALDIFF
// command: EVALDIFF
// category: diagnostics
// status: experimental
// noargs: usage
// effect: report
// mutates: cursor_temporarily
// usage-access: EVALDIFF USAGE
// summary:
//   Compare the classic DbArea predicate evaluator with the TupleRow-bound
//   evaluator over every physical record in the current table.
//
// usage:
//   EVALDIFF FOR <predicate>
//   EVALDIFF <predicate>
//   EVALDIFF USAGE
//
// notes:
//   EVALDIFF is an observer for SQLSEL evaluator-consolidation work. It compiles
//   one predicate through both evaluator families, builds each TupleRow from
//   the same current record, and reports verdict or failure-parity differences.
//   The tuple build disables TABLE BUFFER overlay so the tuple side observes
//   committed table truth. The command includes deleted physical records,
//   ignores SET FILTER, and restores the original cursor before returning.
//   It does not repair, normalize, or choose either evaluator's semantics.
//   VERDICT-PARITY means only that TRUE/FALSE outcome classes agree; it is not
//   a correctness oracle. PARITY-ON-FAILURE means both paths failed every row.
//
// risk:
//   reads_table_records: yes
//   reads_engine_state: yes
//   mutates_table_data: no
//   mutates_cursor: temporarily_restored
//   triggers_relation_refresh: no
//
// related:
//   SQLSEL
//   TUPLE
//   REGRESSION

#include "cli/shell_commands.hpp"

#include <algorithm>
#include <cctype>
#include <iomanip>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>

#include "cli/expr/api.hpp"
#include "cli/expr/value_eval.hpp"
#include "expr_tuple_glue.hpp"
#include "tuple_builder.hpp"
#include "xbase.hpp"

namespace {

std::string trim_copy(std::string s) {
    const auto is_ws = [](unsigned char c) { return std::isspace(c) != 0; };
    while (!s.empty() && is_ws(static_cast<unsigned char>(s.front()))) {
        s.erase(s.begin());
    }
    while (!s.empty() && is_ws(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
    return s;
}

std::string upper_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) {
        return static_cast<char>(std::toupper(c));
    });
    return s;
}

void print_usage() {
    std::cout
        << "EVALDIFF FOR <predicate>\n"
        << "EVALDIFF <predicate>\n"
        << "EVALDIFF USAGE\n"
        << "  Compare classic DbArea and TupleRow evaluator outcomes over every\n"
        << "  physical record, including deleted records. The original cursor is\n"
        << "  restored. This command reports differences; it changes no semantics.\n";
}

enum class OutcomeKind { False, True, Error };

struct Outcome {
    OutcomeKind kind = OutcomeKind::Error;
    std::string error;
};

const char* outcome_name(const Outcome& outcome) {
    switch (outcome.kind) {
        case OutcomeKind::False: return "FALSE";
        case OutcomeKind::True:  return "TRUE";
        case OutcomeKind::Error: return "ERROR";
    }
    return "ERROR";
}

Outcome eval_classic(dottalk::expr::CompiledPredicate& predicate,
                     xbase::DbArea& area) {
    bool verdict = false;
    std::string error;
    if (!dottalk::expr::eval_bool_compiled(predicate, area, verdict, &error)) {
        return {OutcomeKind::Error, error.empty() ? "evaluation failed" : error};
    }
    return {verdict ? OutcomeKind::True : OutcomeKind::False, {}};
}

Outcome eval_tuple(const dottalk::expr::CompileResult& compiled,
                   const dottalk::TupleRow& row) {
    if (!compiled) {
        return {OutcomeKind::Error,
                compiled.error.empty() ? "compile failed" : compiled.error};
    }

    try {
        const auto view = dottalk::exprglue::make_record_view(row);
        const bool verdict = compiled.program->eval(view);
        return {verdict ? OutcomeKind::True : OutcomeKind::False, {}};
    } catch (const std::exception& ex) {
        return {OutcomeKind::Error, ex.what()};
    } catch (...) {
        return {OutcomeKind::Error, "unknown evaluation exception"};
    }
}

bool same_outcome_class(const Outcome& classic, const Outcome& tuple) {
    return classic.kind == tuple.kind;
}

void count_outcome(const Outcome& outcome,
                   int& true_count,
                   int& false_count,
                   int& error_count) {
    switch (outcome.kind) {
        case OutcomeKind::True:  ++true_count; break;
        case OutcomeKind::False: ++false_count; break;
        case OutcomeKind::Error: ++error_count; break;
    }
}

class CursorRestore {
public:
    explicit CursorRestore(xbase::DbArea& area)
        : area_(area), saved_(area.recno()), restore_(area.isOpen() && saved_ > 0) {}

    ~CursorRestore() {
        if (restore_) {
            (void)area_.gotoRec(saved_);
            (void)area_.readCurrent();
        }
    }

private:
    xbase::DbArea& area_;
    int saved_ = 0;
    bool restore_ = false;
};

} // namespace

void cmd_EVALDIFF(DbArea& area, std::istringstream& args) {
    std::string expression;
    std::getline(args, expression);
    expression = trim_copy(expression);

    if (expression.empty() || upper_copy(expression) == "USAGE") {
        print_usage();
        return;
    }
    if (upper_copy(expression).rfind("FOR ", 0) == 0) {
        expression = trim_copy(expression.substr(4));
    }
    if (expression.empty()) {
        std::cerr << "EVALDIFF: predicate required. See EVALDIFF USAGE.\n";
        return;
    }
    if (!area.isOpen()) {
        std::cerr << "EVALDIFF: no table open. Open a table, then retry.\n";
        return;
    }

    auto classic_program =
        dottalk::expr::compile_bool_predicate(area, expression, false);
    const auto tuple_program = dottalk::expr::compile_where(expression);

    if (!classic_program) {
        std::cerr << "EVALDIFF: classic predicate compiler unavailable.\n";
        return;
    }

    dottalk::TupleBuildOptions tuple_options;
    tuple_options.strict_fields = true;
    tuple_options.refresh_relations = false;
    tuple_options.overlay_table_buffer = false;

    CursorRestore restore(area);
    const int record_count = area.recCount();
    int rows_observed = 0;
    int verdict_agreements = 0;
    int failure_parities = 0;
    int divergences = 0;
    int classic_true = 0;
    int classic_false = 0;
    int classic_error = 0;
    int tuple_true = 0;
    int tuple_false = 0;
    int tuple_error = 0;

    for (int record_number = 1; record_number <= record_count; ++record_number) {
        if (!area.gotoRec(record_number) || !area.readCurrent()) {
            std::cout << "EVALDIFF DIVERGENCE recno=" << record_number
                      << " classic=ERROR tuple=ERROR"
                      << " detail=\"record could not be read\"\n";
            ++divergences;
            continue;
        }
        ++rows_observed;

        const Outcome classic = eval_classic(*classic_program, area);
        const auto tuple_build =
            dottalk::build_tuple_from_spec("*", tuple_options);

        Outcome tuple;
        if (!tuple_build.ok) {
            tuple = {OutcomeKind::Error, tuple_build.error};
        } else {
            tuple = eval_tuple(tuple_program, tuple_build.row);
        }

        count_outcome(classic, classic_true, classic_false, classic_error);
        count_outcome(tuple, tuple_true, tuple_false, tuple_error);

        if (same_outcome_class(classic, tuple)) {
            if (classic.kind == OutcomeKind::Error) {
                if (trim_copy(classic.error) == trim_copy(tuple.error)) {
                    ++failure_parities;
                    continue;
                }
            } else {
                ++verdict_agreements;
                continue;
            }
        }

        ++divergences;
        std::cout << "EVALDIFF DIVERGENCE recno=" << record_number
                  << " deleted=" << (area.isDeleted() ? "YES" : "NO")
                  << " classic=" << outcome_name(classic)
                  << " tuple=" << outcome_name(tuple);
        if (!classic.error.empty()) {
            std::cout << " classic_error=" << std::quoted(classic.error);
        }
        if (!tuple.error.empty()) {
            std::cout << " tuple_error=" << std::quoted(tuple.error);
        }
        std::cout << "\n";
    }

    const char* summary_class = "DIFFERENCES";
    if (divergences == 0) {
        if (failure_parities == rows_observed) {
            summary_class = "PARITY-ON-FAILURE";
        } else if (failure_parities > 0) {
            summary_class = "MIXED-PARITY";
        } else {
            summary_class = "VERDICT-PARITY";
        }
    }

    std::cout << "EVALDIFF " << summary_class
              << " rows=" << rows_observed
              << " verdict_agreements=" << verdict_agreements
              << " failure_parities=" << failure_parities
              << " divergences=" << divergences
              << " classic[T/F/E]=" << classic_true << "/"
              << classic_false << "/" << classic_error
              << " tuple[T/F/E]=" << tuple_true << "/"
              << tuple_false << "/" << tuple_error
              << " predicate=" << std::quoted(expression) << "\n";
}
