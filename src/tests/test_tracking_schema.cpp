// @dottalk.file v1
// subsystem: tests
// layer: smoke
// project: project.x64base.runtime
// lane: AIF-086
// status: experimental
//
// Schema-lint smoke for portal/tracking_schema.hpp (SYSLANE / SYSRUN / SYSRUNLANE
// / SYSPROOF / SYSTASK). Asserts the DBF conventions hold BEFORE the tables are
// ever built: physical table + field names <= 10 chars, no duplicate field name in
// a table, and every 64-bit id/epoch field (name ends in ID / AT / VER) is N(20).
// Header-only -- no engine, no DBF; compiles and runs against the schema specs.
#include "portal/tracking_schema.hpp"

#include <cstdio>
#include <set>
#include <string>

namespace ps = dottalk::portal::schema;

static int fail(const std::string& msg) {
    std::fprintf(stderr, "FAIL: %s\n", msg.c_str());
    return 1;
}

static bool ends_with(const std::string& s, const char* suffix) {
    const std::string x(suffix);
    return s.size() >= x.size() && s.compare(s.size() - x.size(), x.size(), x) == 0;
}

int main() {
    const auto tables = ps::tracking_tables();
    if (tables.size() != 5) return fail("expected 5 tracking tables");

    std::set<std::string> table_names;
    for (const auto& t : tables) {
        const std::string tn = t.name;
        if (tn.size() > 10) return fail("table name >10 chars: " + tn);
        if (!table_names.insert(tn).second) return fail("duplicate table: " + tn);
        if (t.fields.empty()) return fail(tn + ": no fields");

        std::set<std::string> field_names;
        for (const auto& f : t.fields) {
            if (f.name.size() > 10) return fail(tn + ": field name >10 chars: " + f.name);
            if (!field_names.insert(f.name).second) return fail(tn + ": duplicate field: " + f.name);
            if (f.name == "ID" && (f.type != 'N' || f.len != 20))
                return fail(tn + ": ID must be N(20)");
            // 64-bit id/epoch fields (name ends in ID/AT/VER) must all be N(20).
            if ((ends_with(f.name, "ID") || ends_with(f.name, "AT") || ends_with(f.name, "VER"))
                && !(f.type == 'N' && f.len == 20))
                return fail(tn + ": " + f.name + " looks like a 64-bit id/epoch but is not N(20)");
        }
    }

    std::printf("PASS test_tracking_schema (5 tables, naming + id conventions hold)\n");
    return 0;
}
