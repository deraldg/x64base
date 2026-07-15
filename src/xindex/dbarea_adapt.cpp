// src/xbase/dbarea_adapt.cpp
// Adapter layer between xindex and xbase::DbArea.
//
// Keep this file thin. DbArea already exposes the canonical runtime truth for
// filename, record count, record length, fields, current record, and deleted
// status. Do not rediscover those facts by probing navigation unless there is
// no direct DbArea API.

#include "xindex/dbarea_adapt.hpp"
#include "xbase.hpp"

#include <algorithm>
#include <cctype>
#include <string>

namespace xindex {

// ---- helpers ---------------------------------------------------------------
static inline std::string trim(std::string s) {
    auto notsp = [](unsigned char c) { return !std::isspace(c); };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), notsp));
    s.erase(std::find_if(s.rbegin(), s.rend(), notsp).base(), s.end());
    return s;
}

static inline bool ieq(std::string a, std::string b) {
    auto up = [](std::string s) {
        std::transform(s.begin(), s.end(), s.begin(),
                       [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
        return s;
    };
    return up(std::move(a)) == up(std::move(b));
}

// Return a 0-based field index for adapter callers, or -1 when unknown.
static int field_index_ci(const xbase::DbArea& a, const std::string& name) {
    const auto& fields = a.fields();
    for (std::size_t i = 0; i < fields.size(); ++i) {
        if (ieq(fields[i].name, name)) {
            return static_cast<int>(i);
        }
    }
    return -1;
}

struct RecGuard {
    xbase::DbArea& a;
    int saved{0};

    explicit RecGuard(xbase::DbArea& area) : a(area), saved(area.recno()) {}

    ~RecGuard() {
        if (saved > 0 && a.recno() != saved) {
            (void)a.gotoRec(saved);
        }
    }

    RecGuard(const RecGuard&) = delete;
    RecGuard& operator=(const RecGuard&) = delete;
};

// ---- required adapter funcs ------------------------------------------------
std::string db_filename(const xbase::DbArea& a) {
    return a.filename();
}

int db_record_length(const xbase::DbArea& a) {
    return a.recordLength();
}

int db_recno(const xbase::DbArea& a) {
    return a.recno();
}

int db_record_count(const xbase::DbArea& a) {
    return a.recCount();
}

std::string db_get_string(const xbase::DbArea& a, int recno, const std::string& field) {
    if (recno <= 0) {
        return {};
    }

    const int idx0 = field_index_ci(a, field);
    if (idx0 < 0) {
        return {};
    }

    auto& A = const_cast<xbase::DbArea&>(a);
    RecGuard guard(A);

    if (!A.gotoRec(recno)) {
        return {};
    }

    return A.get(idx0 + 1); // DbArea::get is 1-based.
}

double db_get_double(const xbase::DbArea& a, int recno, const std::string& field) {
    std::string s = trim(db_get_string(a, recno, field));
    if (s.empty()) {
        return 0.0;
    }

    try {
        return std::stod(s);
    } catch (...) {
        return 0.0;
    }
}

bool db_is_deleted(const xbase::DbArea& a, int recno) {
    if (recno <= 0) {
        return false;
    }

    auto& A = const_cast<xbase::DbArea&>(a);
    RecGuard guard(A);

    if (!A.gotoRec(recno)) {
        return false;
    }

    return A.isDeleted();
}

} // namespace xindex
