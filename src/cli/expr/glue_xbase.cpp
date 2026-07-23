// src/cli/expr/glue_xbase.cpp
#include "cli/expr/glue_xbase.hpp"

#include <algorithm>
#include <cctype>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <cstdint>

#include "value_normalize.hpp"   // util::normalize_for_compare
#include "xbase_field_getters.hpp"
#include "xbase_64.hpp"
#include "memo/memo_auto.hpp"
#include "memo/memostore.hpp"

using util::normalize_for_compare;

namespace {

inline std::string upper(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c){ return (char)std::toupper(c); });
    return s;
}

inline int field_index_ci(const xbase::DbArea& a, std::string_view name) {
    std::string N{name};
    const auto& Fs = a.fields();
    std::string U = upper(N);
    for (int i = 0; i < (int)Fs.size(); ++i) {
        std::string H = Fs[(size_t)i].name;
        if (upper(H) == U) return i + 1; // 1-based
    }
    return 0;
}

// Scan-evaluator lane M1: field-name -> 1-based index with a per-view cache, so
// repeated per-row field access during a scan does not re-scan (and re-allocate
// an uppercased copy of) every field descriptor on every access. The field
// layout is fixed for the bound area's lifetime, so the cache never staleness.
inline int field_index_ci_cached(const xbase::DbArea& a, std::string_view name,
                                 std::unordered_map<std::string, int>& cache) {
    std::string key = upper(std::string{name});
    if (auto it = cache.find(key); it != cache.end()) return it->second;
    const int idx = field_index_ci(a, name);
    cache.emplace(std::move(key), idx);
    return idx;
}

inline std::optional<double> logical_to_num(std::string v) {
    std::string U = upper(v);
    if (U == "T" || U == ".T." || U == "Y" || U == "1" || U == "TRUE")  return 1.0;
    if (U == "F" || U == ".F." || U == "N" || U == "0" || U == "FALSE") return 0.0;
    return std::nullopt;
}

static bool is_x64_memo_field(const xbase::DbArea& A, int field1) {
    if (field1 < 1 || field1 > A.fieldCount()) return false;
    if (A.versionByte() != xbase::DBF_VERSION_64) return false;

    const auto& f = A.fields()[static_cast<std::size_t>(field1 - 1)];
    return (f.type == 'M' || f.type == 'm') &&
           f.length == xbase::X64_MEMO_FIELD_LEN;
}

static std::uint64_t parse_u64_or_zero(const std::string& s) {
    if (s.empty()) return 0;
    try {
        std::size_t used = 0;
        const unsigned long long v = std::stoull(s, &used, 10);
        if (used != s.size()) return 0;
        return static_cast<std::uint64_t>(v);
    } catch (...) {
        return 0;
    }
}

static dottalk::memo::MemoStore* memo_store_for_area(xbase::DbArea& A) noexcept {
    auto* backend = cli_memo::memo_backend_for(A);
    if (!backend) return nullptr;
    return dynamic_cast<dottalk::memo::MemoStore*>(backend);
}

static std::string get_logical_field_text(xbase::DbArea& area, int field1) {
    if (field1 <= 0) return {};
    try {
        if (!is_x64_memo_field(area, field1)) {
            return area.get(field1);
        }

        const std::uint64_t oid = parse_u64_or_zero(area.get(field1));
        if (!oid) return {};

        auto* store = memo_store_for_area(area);
        if (!store) return {};

        std::string txt;
        if (!store->get_text_id(oid, txt, nullptr)) return {};
        return txt;
    } catch (...) {
        return {};
    }
}

// Raw analog of get_logical_field_text: sources the field from the record
// buffer via decodeFieldFromBuffer() (single-field decode) instead of the
// eager _fd cache, so a scan using readCurrentRaw() decodes only the fields the
// predicate touches. Memo handling is identical.
static std::string get_logical_field_text_raw(xbase::DbArea& area, int field1) {
    if (field1 <= 0) return {};
    try {
        if (!is_x64_memo_field(area, field1)) {
            return area.decodeFieldFromBuffer(field1);
        }

        const std::uint64_t oid = parse_u64_or_zero(area.decodeFieldFromBuffer(field1));
        if (!oid) return {};

        auto* store = memo_store_for_area(area);
        if (!store) return {};

        std::string txt;
        if (!store->get_text_id(oid, txt, nullptr)) return {};
        return txt;
    } catch (...) {
        return {};
    }
}

} // namespace

namespace dottalk { namespace expr { namespace glue {

RecordView make_record_view(xbase::DbArea& area) {
    RecordView rv;

    // M1: field-name -> index cache shared by this view's accessors, kept alive
    // for the view's lifetime (shared_ptr so the view stays copyable). During a
    // compile-once scan the same view is reused across every row, so after the
    // first row all field-name resolutions are cache hits.
    auto idx_cache = std::make_shared<std::unordered_map<std::string, int>>();

    // String accessor: return logical field text for the field.
    // For x64 memo fields, this dereferences the raw DBF object-id to memo text.
    rv.get_field_str = [&area, idx_cache](std::string_view name)->std::string {
        // Special symbol: DELETED
        {
            std::string up;
            up.reserve(name.size());
            for (char c: name) up.push_back((char)std::toupper((unsigned char)c));
            if (up == "DELETED") {
                return area.isDeleted() ? "T" : "F";
            }
        }

        int idx = field_index_ci_cached(area, name, *idx_cache);
        if (idx <= 0) return std::string();
        return get_logical_field_text(area, idx);
    };

    // Numeric accessor: typed coercion by DBF field type (and DELETED -> 1/0)
    rv.get_field_num = [&area, idx_cache](std::string_view name)->std::optional<double> {
        // Special symbol: DELETED
        {
            std::string up;
            up.reserve(name.size());
            for (char c: name) up.push_back((char)std::toupper((unsigned char)c));
            if (up == "DELETED") {
                return area.isDeleted() ? 1.0 : 0.0;
            }
        }

        int idx = field_index_ci_cached(area, name, *idx_cache);
        if (idx <= 0) return std::nullopt;

        const auto& f = area.fields()[(size_t)(idx - 1)];
        const char ftype = (char)std::toupper((unsigned char)f.type);
        const int  flen  = (int)f.length;
        const int  fdec  = (int)f.decimals;
        const std::string raw = get_logical_field_text(area, idx);

        if (ftype == 'N') {
            if (auto canon = normalize_for_compare('N', flen, fdec, raw)) {
                try { return std::stod(*canon); } catch (...) { return std::nullopt; }
            }
            return std::nullopt;
        }
        if (ftype == 'D') {
            if (auto canon = normalize_for_compare('D', flen, fdec, raw)) {
                try { return std::stod(*canon); } catch (...) { return std::nullopt; }
            }
            return std::nullopt;
        }
        if (ftype == 'L') {
            return logical_to_num(raw);
        }

        // Character/Memo: try numeric normalization as a soft fallback
        if (auto canon = normalize_for_compare('N', flen, fdec, raw)) {
            try { return std::stod(*canon); } catch (...) { /* fall through */ }
        }
        return std::nullopt;
    };

    return rv;
}

// Selective-decode record view (scan-evaluator lane M2). Identical accessor
// semantics to make_record_view(), but every field value is decoded on demand
// straight from the current record buffer (decodeFieldFromBuffer / the N/F
// numeric fast path) rather than from the eager per-field _fd cache. Intended
// for scans driven by readCurrentRaw(): only the fields the predicate reads are
// decoded, and N/F numerics decode with no heap allocation.
RecordView make_record_view_raw(xbase::DbArea& area) {
    RecordView rv;

    auto idx_cache = std::make_shared<std::unordered_map<std::string, int>>();

    rv.get_field_str = [&area, idx_cache](std::string_view name)->std::string {
        {
            std::string up;
            up.reserve(name.size());
            for (char c: name) up.push_back((char)std::toupper((unsigned char)c));
            if (up == "DELETED") {
                return area.isDeleted() ? "T" : "F";
            }
        }

        int idx = field_index_ci_cached(area, name, *idx_cache);
        if (idx <= 0) return std::string();
        return get_logical_field_text_raw(area, idx);
    };

    rv.get_field_num = [&area, idx_cache](std::string_view name)->std::optional<double> {
        {
            std::string up;
            up.reserve(name.size());
            for (char c: name) up.push_back((char)std::toupper((unsigned char)c));
            if (up == "DELETED") {
                return area.isDeleted() ? 1.0 : 0.0;
            }
        }

        int idx = field_index_ci_cached(area, name, *idx_cache);
        if (idx <= 0) return std::nullopt;

        // Fast path: N/F fields decode straight from the buffer with no alloc.
        double fast = 0.0;
        if (area.fieldNumFromBuffer(idx, fast)) return fast;

        // Fallback path mirrors make_record_view()'s numeric coercion exactly,
        // but sources the field text from the buffer (one field, not all).
        const auto& f = area.fields()[(size_t)(idx - 1)];
        const char ftype = (char)std::toupper((unsigned char)f.type);
        const int  flen  = (int)f.length;
        const int  fdec  = (int)f.decimals;
        const std::string raw = get_logical_field_text_raw(area, idx);

        if (ftype == 'N') {
            if (auto canon = normalize_for_compare('N', flen, fdec, raw)) {
                try { return std::stod(*canon); } catch (...) { return std::nullopt; }
            }
            return std::nullopt;
        }
        if (ftype == 'D') {
            if (auto canon = normalize_for_compare('D', flen, fdec, raw)) {
                try { return std::stod(*canon); } catch (...) { return std::nullopt; }
            }
            return std::nullopt;
        }
        if (ftype == 'L') {
            return logical_to_num(raw);
        }

        if (auto canon = normalize_for_compare('N', flen, fdec, raw)) {
            try { return std::stod(*canon); } catch (...) { /* fall through */ }
        }
        return std::nullopt;
    };

    return rv;
}

}}} // namespace dottalk::expr::glue