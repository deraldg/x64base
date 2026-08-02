#include "reference/data_address.hpp"
#include "reference/qualified_reference.hpp"
#include "value/value.hpp"

#include <cassert>
#include <cstdint>
#include <iostream>
#include <string>
#include <variant>

using dottalk::reference::DataAddress;
using dottalk::reference::DbAreaIdentity;
using dottalk::reference::FieldIdentity;
using dottalk::reference::QualifiedReferenceParser;
using dottalk::reference::RecordSelector;
using dottalk::reference::RootSyntax;
using dottalk::reference::StorageFlavor;
using dottalk::reference::TableIdentity;
using dottalk::reference::WorkspaceIdentity;
using dottalk::reference::WorkspacePath;
using dottalk::value::ExactDecimal;
using dottalk::value::Value;
using dottalk::value::ValueKind;

namespace {

void require_parse(const QualifiedReferenceParser& parser,
                   const std::string& text,
                   const std::string& canonical) {
    const auto result = parser.parse(text);
    if (!result.ok) {
        std::cerr << "parse failed for '" << text << "': "
                  << result.error << "\n";
        std::abort();
    }
    assert(result.reference.canonical_syntax() == canonical);
}

void require_reject(const QualifiedReferenceParser& parser,
                    const std::string& text) {
    const auto result = parser.parse(text);
    if (result.ok) {
        std::cerr << "expected rejection for '" << text << "'\n";
        std::abort();
    }
}

} // namespace

int main() {
    ExactDecimal amount;
    std::string error;
    assert(ExactDecimal::parse("123.4500", amount, &error));
    assert(amount.canonical_text() == "123.4500");

    ExactDecimal equivalent;
    assert(ExactDecimal::parse("123.45", equivalent, &error));
    assert(amount.equivalent(equivalent));

    ExactDecimal negative;
    assert(ExactDecimal::parse("-0.2500", negative, &error));
    assert(negative.canonical_text() == "-0.2500");

    constexpr std::uint64_t beyond_double_safe_integer = 9007199254740993ULL;
    const Value recno_value = Value::unsigned_integer(beyond_double_safe_integer);
    assert(recno_value.kind() == ValueKind::UnsignedInteger);
    assert(std::get<std::uint64_t>(recno_value.payload()) ==
           beyond_double_safe_integer);

    constexpr std::uint64_t recno64_max = 18446744073709551615ULL;
    const Value max_recno_value = Value::unsigned_integer(recno64_max);
    assert(std::get<std::uint64_t>(max_recno_value.payload()) == recno64_max);

    QualifiedReferenceParser parser;
    require_parse(parser, "LNAME", "LNAME");
    require_parse(parser, "STUDENTS.LNAME", "STUDENTS.LNAME");
    require_parse(parser, "#2.LNAME", "#2.LNAME");
    require_parse(parser, "$students[1].LNAME", "$students[1].LNAME");
    require_parse(parser,
                  "$row[\"STUDENTS.LNAME\"]",
                  "$row[\"STUDENTS.LNAME\"]");

    const auto bare = parser.parse("LNAME");
    assert(bare.ok);
    assert(bare.reference.root_syntax() == RootSyntax::Bare);

    require_reject(parser, "STUDENTS.");
    require_reject(parser, ".STUDENTS");
    require_reject(parser, "STUDENTS..LNAME");
    require_reject(parser, "STUDENTS.LNAME EXTRA");
    require_reject(parser, "$students[1");
    require_reject(parser, "STUDENTS.@LNAME");

    const WorkspaceIdentity workspace{"MCC", "mcc.workspace", 7};
    const DbAreaIdentity area{2, "STUDENTS", 4};
    const TableIdentity table{
        "STUDENTS",
        "STUDENTS",
        "students",
        "data/x64/students.dbf",
        StorageFlavor::V64
    };
    const FieldIdentity field{"LNAME", "LNAME", 3, 'C'};

    const DataAddress normal(
        workspace,
        area,
        table,
        RecordSelector::physical(12),
        field);

    const DataAddress normal_copy(
        workspace,
        area,
        table,
        RecordSelector::physical(12),
        field);

    const DataAddress another_record(
        workspace,
        area,
        table,
        RecordSelector::physical(13),
        field);

    assert(normal.same_field_identity(another_record));
    assert(normal.same_cell_identity(normal_copy));
    assert(!normal.same_cell_identity(another_record));

    const DataAddress recno64_boundary(
        workspace,
        area,
        table,
        RecordSelector::physical(9007199254740993ULL),
        field);

    const std::string diagnostic = recno64_boundary.diagnostic_text();
    assert(diagnostic.find("9007199254740993") != std::string::npos);

    // ---- AIF-078 Q7: workspace scalar widened to a path -------------------
    //
    // The no-regression condition for the widening is that depth <= 1 renders
    // and compares EXACTLY as it did before. Depth > 1 is reserved and is
    // proven only to round-trip through the address; nothing resolves it.

    // 1. Depth 1 renders byte-identically to the pre-widening output.
    assert(normal.diagnostic_text() ==
           "MCC.#2.STUDENTS.RECNO(12).LNAME");

    // 2. The scalar ctor produces depth 1, and workspace() still answers with
    //    the same identity every pre-AIF-078 caller expects.
    assert(normal.workspace_depth() == 1);
    assert(normal.workspace().logical_name == "MCC");
    assert(normal.workspace_path().size() == 1);

    // 3. An unspecified workspace still renders CURRENT_WORKSPACE.
    const DataAddress no_workspace(
        WorkspaceIdentity{},
        area,
        table,
        RecordSelector::physical(12),
        field);
    assert(no_workspace.diagnostic_text() ==
           "CURRENT_WORKSPACE.#2.STUDENTS.RECNO(12).LNAME");
    assert(no_workspace.workspace_depth() == 0);
    assert(no_workspace.workspace().unspecified());

    // 4. An EMPTY path and a path of one unspecified identity mean the same
    //    thing and must compare equal -- the behavior this widening is not
    //    allowed to change.
    const DataAddress empty_path(
        WorkspacePath{},
        area,
        table,
        RecordSelector::physical(12),
        field);
    assert(empty_path.diagnostic_text() == no_workspace.diagnostic_text());
    assert(empty_path.same_cell_identity(no_workspace));
    assert(no_workspace.same_cell_identity(empty_path));

    // 5. Depth > 1 round-trips: outermost first, dot-joined; workspace()
    //    answers with the INNERMOST; depth counts specified levels only.
    const DataAddress nested(
        WorkspacePath{WorkspaceIdentity{"MCC", "mcc.workspace", 7},
                      WorkspaceIdentity{"FALL2026", "", 0},
                      WorkspaceIdentity{"SEC3", "", 0}},
        area,
        table,
        RecordSelector::physical(12),
        field);
    assert(nested.diagnostic_text() ==
           "MCC.FALL2026.SEC3.#2.STUDENTS.RECNO(12).LNAME");
    assert(nested.workspace_depth() == 3);
    assert(nested.workspace().logical_name == "SEC3");

    // 6. Different depth is a different address, not an accidental match.
    assert(!nested.same_field_identity(normal));
    assert(!normal.same_field_identity(nested));

    // 7. The parser already accepts the nested surface form and round-trips
    //    it; only RESOLUTION is missing. This is the claim AIF-078 sec 5b
    //    rests on, asserted here rather than left as prose.
    require_parse(parser,
                  "MCC.FALL2026.SEC3.STUDENTS.LNAME",
                  "MCC.FALL2026.SEC3.STUDENTS.LNAME");

    std::cout
        << "PDLC foundation smoke passed\n"
        << "  decimal=" << amount.canonical_text() << "\n"
        << "  reference=#2.LNAME\n"
        << "  address=" << diagnostic << "\n"
        << "  recno64_max=" << recno64_max << "\n";

    return 0;
}
