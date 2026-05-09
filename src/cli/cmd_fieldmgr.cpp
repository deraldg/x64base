// @dottalk.usage v1
// owner: DOT|FIELDMGR
// command: FIELDMGR
// category: schema
// status: supported
// noargs: report
// effect: mixed
// mutates: table-schema index metadata
// usage-access: FIELDMGR USAGE
// summary:
//   Inspect and modify field definitions for the current DBF through the shared
//   fields manager layer.
//
// usage:
//   FIELDMGR
//   FIELDMGR USAGE
//   FIELDMGR HELP
//   FIELDMGR SHOW
//   FIELDMGR LIST
//   FIELDMGR APPEND <name> <type>
//   FIELDMGR DELETE <name>
//   FIELDMGR MODIFY <name> NAME <newname>
//   FIELDMGR MODIFY <name> TYPE <type>
//   FIELDMGR MODIFY <name> TO <newname> <type>
//   FIELDMGR COPY TO <target>
//   FIELDMGR VALIDATE
//   FIELDMGR CHECK
//   FIELDMGR REBUILD INDEXES
//
// examples:
//   FIELDMGR SHOW
//   FIELDMGR APPEND ZIP C10
//   FIELDMGR DELETE ZIP
//   FIELDMGR MODIFY ZIP NAME POSTAL
//   FIELDMGR VALIDATE
//
// notes:
//   FIELDMGR with no arguments shows current field metadata.
//   SHOW and LIST are read-only reports.
//   APPEND, DELETE, and MODIFY mutate table schema.
//   COPY exports or copies field metadata through the fields manager layer.
//   VALIDATE and CHECK report field/schema consistency.
//   REBUILD INDEXES delegates index rebuild through the fields manager layer.
//   FIELDMGR is schema mutation capable and is not purely read-only.
//
// risk:
//   reads_schema: yes
//   mutates_schema: APPEND DELETE MODIFY
//   rebuilds_indexes: REBUILD INDEXES
//   writes_files: COPY may write through field manager behavior
//   mutates_table_data: schema operations may rewrite table structure through field manager behavior
//
// related:
//   STRUCT
//   FIELDS
//   DDL
//   CREATE
//   INDEX
//

#include "xbase/fields.hpp"

#include <cctype>
#include <iostream>
#include <iterator>
#include <sstream>
#include <string>
#include <vector>

namespace {
std::string trim_copy(std::string s)
{
    const auto is_space = [](unsigned char ch) { return std::isspace(ch); };

    while (!s.empty() && is_space(static_cast<unsigned char>(s.front()))) {
        s.erase(s.begin());
    }
    while (!s.empty() && is_space(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
    return s;
}

std::string upper_copy(std::string s)
{
    for (char& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

bool ieq(const std::string& a, const std::string& b)
{
    return upper_copy(trim_copy(a)) == upper_copy(trim_copy(b));
}

std::vector<std::string> split_ws(const std::string& text)
{
    std::vector<std::string> out;
    std::istringstream iss(text);
    std::string tok;
    while (iss >> tok) {
        out.push_back(tok);
    }
    return out;
}

void print_result(const fields::Result& r)
{
    if (!r.message.empty()) {
        std::cout << r.message << "\n";
    }
}

bool parse_append_spec(const std::string& rest,
                       xbase::FieldDef& fd,
                       std::string& err)
{
    return fields::parseFieldSpec(rest, fd, err);
}

void print_usage()
{
    std::cout << fields::usage();
}

} // namespace

void cmd_FIELDMGR(xbase::DbArea& db, std::istringstream& iss)
{
    const std::string rest = trim_copy(std::string{
        std::istreambuf_iterator<char>(iss),
        std::istreambuf_iterator<char>()
    });

    if (rest.empty()) {
        print_result(fields::show(db));
        return;
    }

    const std::vector<std::string> toks = split_ws(rest);
    if (toks.empty()) {
        print_result(fields::show(db));
        return;
    }

    const std::string op0 = upper_copy(toks[0]);

    if (op0 == "SHOW" || op0 == "LIST") {
        print_result(fields::show(db));
        return;
    }

    if (op0 == "APPEND") {
        std::string spec = trim_copy(rest.substr(toks[0].size()));
        if (spec.empty()) {
            std::cout << "FIELDMGR APPEND: missing field specification\n";
            std::cout << "Usage: FIELDMGR APPEND <name> <type>(<len>[,<dec>])\n";
            return;
        }

        xbase::FieldDef fd;
        std::string err;
        if (!parse_append_spec(spec, fd, err)) {
            std::cout << "FIELDMGR APPEND: " << err << "\n";
            return;
        }

        fields::AppendOptions opts;
        opts.rebuildIndexesIfPossible = false;
        opts.failIfIndexesPresent = false;

        const fields::Result r = fields::append(db, fd, opts);
        print_result(r);
        return;
    }

    if (op0 == "DELETE") {
        if (toks.size() < 2) {
            std::cout << "FIELDMGR DELETE: missing field name\n";
            std::cout << "Usage: FIELDMGR DELETE <name>\n";
            return;
        }

        const fields::Result r = fields::deleteField(db, toks[1]);
        print_result(r);
        return;
    }

    if (op0 == "MODIFY") {
        if (toks.size() < 3) {
            std::cout << "FIELDMGR MODIFY: incomplete command\n";
            std::cout << "Usage:\n";
            std::cout << "  FIELDMGR MODIFY <name> NAME <newname>\n";
            std::cout << "  FIELDMGR MODIFY <name> TYPE <type>(<len>[,<dec>])\n";
            std::cout << "  FIELDMGR MODIFY <name> TO <newname> <type>(<len>[,<dec>])\n";
            return;
        }

        const std::string fieldName = toks[1];
        const std::string mode = upper_copy(toks[2]);

        if (mode == "NAME") {
            if (toks.size() < 4) {
                std::cout << "FIELDMGR MODIFY NAME: missing new field name\n";
                return;
            }
            const fields::Result r = fields::modifyName(db, fieldName, toks[3]);
            print_result(r);
            return;
        }

        if (mode == "TYPE") {
            const std::string prefix =
                toks[0] + " " + toks[1] + " " + toks[2];
            std::string spec = trim_copy(rest.substr(prefix.size()));
            if (spec.empty()) {
                std::cout << "FIELDMGR MODIFY TYPE: missing type specification\n";
                return;
            }

            xbase::FieldDef fd;
            std::string err;
            if (!fields::parseFieldSpec(fieldName + " " + spec, fd, err)) {
                std::cout << "FIELDMGR MODIFY TYPE: " << err << "\n";
                return;
            }

            const fields::Result r = fields::modifyType(db, fieldName, fd);
            print_result(r);
            return;
        }

        if (mode == "TO") {
            if (toks.size() < 5) {
                std::cout << "FIELDMGR MODIFY TO: incomplete command\n";
                return;
            }

            const std::string newName = toks[3];
            const std::string prefix =
                toks[0] + " " + toks[1] + " " + toks[2] + " " + toks[3];
            std::string spec = trim_copy(rest.substr(prefix.size()));
            if (spec.empty()) {
                std::cout << "FIELDMGR MODIFY TO: missing type specification\n";
                return;
            }

            xbase::FieldDef fd;
            std::string err;
            if (!fields::parseFieldSpec(newName + " " + spec, fd, err)) {
                std::cout << "FIELDMGR MODIFY TO: " << err << "\n";
                return;
            }

            const fields::Result r = fields::modifyTo(db, fieldName, fd);
            print_result(r);
            return;
        }

        std::cout << "FIELDMGR MODIFY: unknown mode '" << toks[2] << "'\n";
        return;
    }

    if (op0 == "COPY") {
        if (toks.size() < 3 || !ieq(toks[1], "TO")) {
            std::cout << "FIELDMGR COPY: expected 'TO'\n";
            std::cout << "Usage: FIELDMGR COPY TO <target>\n";
            return;
        }

        const std::string target = toks[2];

        if (toks.size() >= 4 && ieq(toks[3], "MAP")) {
            fields::CopyPlan plan;
            const fields::Result r = fields::copyToMap(db, target, plan);
            print_result(r);
            return;
        }

        const fields::Result r = fields::copyTo(db, target);
        print_result(r);
        return;
    }

    if (op0 == "VALIDATE") {
        print_result(fields::validate(db));
        return;
    }

    if (op0 == "CHECK") {
        print_result(fields::check(db));
        return;
    }

    if (op0 == "REBUILD") {
        if (toks.size() >= 2 && ieq(toks[1], "INDEXES")) {
            print_result(fields::rebuildIndexes(db));
            return;
        }

        std::cout << "FIELDMGR REBUILD: expected 'INDEXES'\n";
        return;
    }

    if (op0 == "USAGE" || op0 == "HELP" || op0 == "?") {
        print_usage();
        return;
    }

    std::cout << "FIELDMGR: unknown subcommand '" << toks[0] << "'\n";
    std::cout << "Type FIELDMGR HELP for usage.\n";
}
