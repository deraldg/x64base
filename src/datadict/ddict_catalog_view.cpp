// @dottalk.file v1
// subsystem: datadict
// layer: helper
// project: project.x64base.runtime
// owner: member.derald
// status: supported
#include "datadict/ddict_catalog_view.hpp"
#include "datadict/ddict_read_helpers.hpp"
#include "memo/memostore.hpp"
#include <algorithm>
#include <set>
#include <map>
#include <ostream>

namespace dottalk::datadict {
namespace {
using Mapping = std::vector<std::pair<std::string, std::string>>;
struct Binding { const char* legacy; const char* extended; const char* id; Mapping mapping; };
const std::vector<Binding> bindings = {
 {"DDRUN", "DATA_DICTIONARY_RUNS", "RUNID", {{"RUNID","RUN_RECORD_ID"},{"KIND","RUN_KIND_CODE"},{"STATUS","RUN_STATUS_CODE"},{"PROFILE","RUN_PROFILE_CODE"},{"NOTES","RUN_DETAIL_TEXT"}}},
 {"DDBASE", "", "BASEID", {}}, {"DDSOURCE", "", "SRCID", {}},
 {"DDOBJECT", "DATA_DICTIONARY_OBJECTS", "OBJID", {{"OBJID","CATALOG_OBJECT_ID"},{"OBJTYPE","CATALOG_OBJECT_TYPE"},{"NAME","CATALOG_OBJECT_NAME"},{"OWNER","CATALOG_OWNER_NAME"},{"STATUS","CATALOG_STATUS_CODE"},{"PROFILE","CATALOG_PROFILE_CODE"},{"SRCID","SOURCE_ARTIFACT_ID"}}},
 {"DDATTR", "DATA_DICTIONARY_OBJECT_ATTRIBUTES", "ATTRID", {{"ATTRID","CATALOG_ATTRIBUTE_ID"},{"OBJID","CATALOG_OBJECT_ID"},{"ATTRNAME","CATALOG_ATTRIBUTE_NAME"},{"ATTRVAL","CATALOG_ATTRIBUTE_VALUE"},{"ATTRMEMO","CATALOG_ATTRIBUTE_DETAIL"},{"EVID","EVIDENCE_RECORD_ID"}}},
 {"DDEDGE", "DATA_DICTIONARY_RELATION_EDGES", "EDGEID", {{"EDGEID","RELATION_EDGE_ID"},{"FROMOBJ","RELATION_FROM_OBJECT_ID"},{"TOOBJ","RELATION_TO_OBJECT_ID"},{"EDGETYPE","RELATION_EDGE_TYPE"},{"EVID","EVIDENCE_RECORD_ID"}}},
 {"DDEVID", "DATA_DICTIONARY_EVIDENCE_RECORDS", "EVID", {{"EVID","EVIDENCE_RECORD_ID"},{"OBJID","CATALOG_OBJECT_ID"},{"SRCID","SOURCE_ARTIFACT_ID"},{"KIND","EVIDENCE_KIND_CODE"},{"CONF","EVIDENCE_CONFIDENCE_CODE"},{"DETAIL","EVIDENCE_DETAIL_TEXT"}}},
 {"DDGATE", "DATA_DICTIONARY_GATE_RECORDS", "GATEID", {{"GATEID","GATE_RECORD_ID"},{"RUNID","RUN_RECORD_ID"},{"GATENAME","GATE_NAME"},{"STATUS","GATE_STATUS_CODE"},{"DETAIL","GATE_DETAIL_TEXT"}}},
 {"DDREVIEW", "", "REVID", {}}, {"DDARTIF", "", "ARTID", {}}, {"DDPROFILE", "", "PROFID", {}}
};
void resolve_memos(TableReadResult& t, const std::filesystem::path& path,
                   std::vector<std::string>& diagnostics) {
    dottalk::memo::MemoStore store;
    bool attempted = false, opened = false;
    std::unordered_map<std::string, std::size_t> failures;
    for (auto& row : t.rows) for (const auto& field : t.fields) {
        if (field.type != 'M') continue;
        auto& raw = row[field.name];
        auto& memo_state = row["_DD_MEMO_STATE:" + field.name];
        memo_state = "UNAVAILABLE";
        // x64 DTX links are binary, eight-byte little endian object identities.
        // Other memo dialects must not be interpreted as DTX object ids.
        if (!t.x64 || field.width != 8) {
            ++failures[field.name + ": unsupported memo dialect or pointer width"];
            raw = "[memo unavailable]";
            continue;
        }
        if (std::all_of(raw.begin(), raw.end(), [](char c) { return c == ' '; })) {
            memo_state = "INVALID";
            ++failures[field.name + ": invalid space-filled x64 memo link"];
            raw = "[invalid memo link: space-filled]";
            continue;
        }
        std::uint64_t id = 0;
        for (unsigned i = 0; i < 8; ++i) id |= std::uint64_t(static_cast<unsigned char>(raw[i])) << (8*i);
        raw.clear();
        if (!id) { memo_state = "NULL"; continue; }
        if (!attempted) {
            attempted = true;
            opened = store.open_read_only(path.string()).ok;

        }
        std::string why;
        if (!opened || !store.get_text_id(id, raw, &why)) {
            raw = "[memo unavailable: " + std::to_string(id) + "]";
            ++failures[field.name + ": " + (opened ? why : "memo sidecar missing or unreadable")];
        } else memo_state = "RESOLVED";
    }
    for (const auto& failure : failures) diagnostics.push_back(path.stem().string() + ": " + failure.first + " (cells=" + std::to_string(failure.second) + ")");
}
}
const std::vector<DDictRow>& CatalogView::rows(const std::string& name) const {
    static const std::vector<DDictRow> empty;
    const auto it = tables.find(name);
    return it == tables.end() ? empty : it->second;
}
CatalogView read_catalog_view(const std::filesystem::path& directory) {
    CatalogView view;
    for (const auto& b : bindings) for (const bool extended : {false, true}) {
        const std::string physical = extended ? b.extended : b.legacy;
        if (physical.empty()) continue;
        const std::string family = extended ? "X64" : "LEGACY";
        auto t = read_dbf_table_checked(directory, physical);
        view.physical_tables.push_back({physical, t.logical_name, family, t.state, t.rows.size(), t.fields});
        if (t.state == TableReadState::Error) {
            view.diagnostics.push_back(physical + ": " + t.error);
            continue;
        }
        if (t.state != TableReadState::Ready) continue;
        std::set<std::string> fields;
        for (const auto& f : t.fields) fields.insert(f.name);
        std::string missing;
        if (!b.mapping.empty()) {
            for (const auto& m : b.mapping) {
                const auto& required = extended ? m.second : m.first;
                if (!fields.count(required)) { missing = required; break; }
            }
        } else if (!fields.count(b.id)) missing = b.id;
        if (!missing.empty()) {
            view.physical_tables.back().state = TableReadState::Error;
            view.diagnostics.push_back(physical + ": missing required field " + missing);
            continue;
        }
        resolve_memos(t, directory / (physical + ".dtx"), view.diagnostics);
        auto& dest = view.tables[b.legacy];
        std::set<std::string> ids;
        for (const auto& row : dest) ids.insert(value_of(row,b.id));
        for (auto& row : t.rows) {
            if (extended) for (const auto& m : b.mapping) row[m.first] = value_of(row,m.second);
            row["_DD_FAMILY"] = family;
            row["_DD_TABLE"] = physical;
            row["_DD_ID"] = value_of(row,b.id);
            if (extended) {
                for (const auto* key : {"OBJID","ATTRID","EDGEID","EVID","GATEID","RUNID","FROMOBJ","TOOBJ"}) {
                    auto it = row.find(key);
                    if (it != row.end() && !it->second.empty()) it->second = "x64:" + it->second;
                }
                if (!value_of(row,"SRCID").empty()) row["SRCID"] = "x64:artifact:" + row["SRCID"];
            }
            const auto id = value_of(row,b.id);
            if (id.empty() || !ids.insert(id).second) {
                view.diagnostics.push_back(physical + ": empty or duplicate identity " + id);
                continue;
            }
            dest.push_back(std::move(row));
        }
    }
    // Explicit endpoint typing: long-name HAS_CATALOG_ATTRIBUTE edges target
    // attributes, while the other relations target catalog objects.
    std::unordered_map<std::string,std::string> objects, attrs;
    for (const auto& r : view.rows("DDOBJECT")) objects[value_of(r,"OBJID")] = value_of(r,"NAME");
    for (const auto& r : view.rows("DDATTR")) attrs[value_of(r,"ATTRID")] = value_of(r,"ATTRNAME");
    for (auto& edge : view.tables["DDEDGE"]) {
        for (const bool to : {false,true}) {
            const auto id = value_of(edge,to ? "TOOBJ" : "FROMOBJ");
            const bool attribute = to && value_of(edge,"_DD_FAMILY") == "X64" && value_of(edge,"EDGETYPE") == "HAS_CATALOG_ATTRIBUTE";
            const auto& domain = attribute ? attrs : objects;
            const auto it = domain.find(id);
            edge[to ? "_DD_TO_KIND" : "_DD_FROM_KIND"] = attribute ? "ATTRIBUTE" : "OBJECT";
            if (it != domain.end()) edge[to ? "_DD_TO_NAME" : "_DD_FROM_NAME"] = it->second;
            else view.diagnostics.push_back(value_of(edge,"_DD_TABLE") + ": unresolved " + (to ? "target " : "source ") + id);
        }
    }
    if (view.rows("DDOBJECT").empty()) view.diagnostics.push_back("No readable catalog objects");
    return view;
}

namespace {
void json_string(std::ostream& out, const std::string& value) {
    static const char hex[] = "0123456789abcdef";
    out << '"';
    for (unsigned char c : value) {
        if (c == '"' || c == '\\') out << '\\' << static_cast<char>(c);
        else if (c < 32) out << "\\u00" << hex[c >> 4] << hex[c & 15];
        else out << static_cast<char>(c);
    }
    out << '"';
}
}
void write_catalog_json(const CatalogView& view, std::ostream& out) {
    out << "{\"schema\":\"dottalk.ddict.native.v1\",\"physical_tables\":[";
    bool first = true;
    for (const auto& table : view.physical_tables) {
        if (!first) out << ',';
        first = false;
        out << "{\"physical_name\":"; json_string(out, table.physical_name);
        out << ",\"logical_name\":"; json_string(out, table.logical_name);
        out << ",\"family\":"; json_string(out, table.family);
        out << ",\"state\":"; json_string(out, table.state == TableReadState::Ready ? "READY" : table.state == TableReadState::Missing ? "MISSING" : "ERROR");
        out << ",\"rows\":" << table.rows << ",\"fields\":[";
        bool field_first = true;
        for (const auto& field : table.fields) {
            if (!field_first) out << ',';
            field_first = false;
            out << "{\"name\":"; json_string(out, field.name);
            out << ",\"type\":"; json_string(out, std::string(1, field.type));
            out << ",\"width\":" << field.width << '}';
        }
        out << "]}";
    }
    out << "],\"tables\":{";
    first = true;
    // Fixed logical domains, with physical row order retained within each.
    for (const auto& binding : bindings) {
        if (!first) out << ',';
        first = false;
        json_string(out, binding.legacy); out << ":[";
        bool row_first = true;
        for (const auto& row : view.rows(binding.legacy)) {
            if (!row_first) out << ',';
            row_first = false;
            out << '{';
            bool cell_first = true;
            for (const auto& [key, value] : std::map<std::string,std::string>(row.begin(), row.end())) {
                if (!cell_first) out << ',';
                cell_first = false;
                json_string(out,key); out << ':'; json_string(out,value);
            }
            out << '}';
        }
        out << ']';
    }
    out << "},\"diagnostics\":[";
    auto diagnostics = view.diagnostics;
    std::sort(diagnostics.begin(), diagnostics.end());
    first = true;
    for (const auto& diagnostic : diagnostics) {
        if (!first) out << ',';
        first = false;
        json_string(out, diagnostic);
    }
    out << "]}\n";
}
} // namespace dottalk::datadict
