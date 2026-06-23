/*
@dottalk.usage v1
owner: DDICT
surface: DDICT
summary: Read-only Data Dictionary inspection command for active catalog metadata.
status: source_contract_review_candidate
profiles: ENGINE, PROFESSIONAL
read_mode: READ_ONLY
mutates: none

forms:
  DDICT STATUS
  DDICT TABLES
  DDICT FIELDS <table-or-alias>
  DDICT TAGS <table-or-alias>
  DDICT REL <object> [IN|OUT|BOTH]
  DDICT EVIDENCE <object>

alias_bridge:
  DDOBJECT -> DATA_DICTIONARY_OBJECTS
  DDATTR   -> DATA_DICTIONARY_OBJECT_ATTRIBUTES
  DDEDGE   -> DATA_DICTIONARY_RELATION_EDGES
  DDEVID   -> DATA_DICTIONARY_EVIDENCE_RECORDS
  DDGATE   -> DATA_DICTIONARY_GATE_RECORDS
  DDRUN    -> DATA_DICTIONARY_RUNS

active_roots:
  DBF  : dottalkpp/data/datadict
  CDX  : dottalkpp/data/indexes/datadict
  LMDB : dottalkpp/data/lmdb/datadict

contract_notes:
  - Preserve legacy DD* spellings as compatibility names.
  - Resolve DATA_DICTIONARY_* spellings as authoritative x64 catalog names.
  - FIELDS must keep DDICT FIELDS DDOBJECT working while bridging DATA_DICTIONARY_OBJECTS.
  - TAGS must distinguish catalog tag rows from physical CDX/LMDB artifacts.
  - If physical tag artifacts exist but catalog tag rows are absent, report an honest physical-artifact status instead of plain NO_CATALOG_TAGS_FOUND.

safety:
  - No DBF append, replace, delete, pack, zap, create, or load.
  - No active CDX/LMDB rebuild.
  - No HELP, CMDHELPCHK, manual publication, metadata catalog, or Data Dictionary catalog mutation.
  - Runtime surface remains read-only inspection.

evidence_lane:
  DD096Z-D2ZS reviewed source patch lane
@dottalk.end
*/

#include "cli/cmd_ddict.hpp"

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

#include "datadict/ddict_read_helpers.hpp"
#include "datadict/ddict_catalog_paths.hpp"
#include "datadict/ddict_dbf_reader.hpp"
#include "datadict/ddict_object_resolver.hpp"
#include "datadict/ddict_catalog_resolver.hpp"
#include "datadict/ddict_callsite_bridge.hpp"
namespace {

namespace fs = std::filesystem;
using namespace dottalk::datadict;
using dottalk::datadict::CatalogStats;
using dottalk::datadict::DDictRow;
using dottalk::datadict::FieldDef;
using Row = dottalk::datadict::DDictRow;
 // DD-089E preview: helper namespace bridge

struct TableInfo {
    const char* name;
};

constexpr std::array<TableInfo, 11> kTables{{
    TableInfo{"DDRUN"},
    TableInfo{"DDBASE"},
    TableInfo{"DDSOURCE"},
    TableInfo{"DDOBJECT"},
    TableInfo{"DDATTR"},
    TableInfo{"DDEDGE"},
    TableInfo{"DDEVID"},
    TableInfo{"DDGATE"},
    TableInfo{"DDREVIEW"},
    TableInfo{"DDARTIF"},
    TableInfo{"DDPROFILE"},
}};

// DD-089E preview: local helper `lower_copy` moved to datadict helper module.

// DD-089E preview: local helper `trim_copy` moved to datadict helper module.

// DD-089E preview: local helper `upper_copy` moved to datadict helper module.

// DD-089E preview: local helper `value_of` moved to datadict helper module.

// DD-089E preview: local helper `exists_quiet` moved to datadict helper module.

// DD-089E preview: local helper `size_quiet` moved to datadict helper module.

// DD-089E preview: local helper `normalize_quiet` moved to datadict helper module.

// DD-089E preview: local helper `base_roots` moved to datadict helper module.

// DD-089E preview: local helper `catalog_candidates` moved to datadict helper module.

// DD-089E preview: local helper `find_catalog_dir` moved to datadict helper module.

// DD-089E preview: local helper `find_cdx_file` moved to datadict helper module.

// DD-089E preview: local helper `find_lmdb_dir` moved to datadict helper module.

// DD-089E preview: local helper `collect_stats` moved to datadict helper module.

// DD-089E preview: local helper `plausible_name` moved to datadict helper module.

// DD-089E preview: local helper `plausible_descriptor` moved to datadict helper module.

// DD-089E preview: local helper `descriptor_start` moved to datadict helper module.

// DD-089E preview: local helper `le16` moved to datadict helper module.

// DD-089E preview: local helper `le32` moved to datadict helper module.

// DD-089E preview: local helper `descriptor_name` moved to datadict helper module.

// DD-089E preview: local helper `read_binary` moved to datadict helper module.

// DD-089E preview: local helper `parse_fields` moved to datadict helper module.

// DD-089E preview: local helper `read_dbf_table` moved to datadict helper module.

// DD-089E preview: local helper `short_text` moved to datadict helper module.

std::vector<std::string> owner_lookup_candidates(const std::string& token) {
    std::vector<std::string> candidates;

    auto add_candidate = [&](const std::string& value) {
        std::string normalized = upper_copy(trim_copy(value));
        if (!normalized.empty() &&
            std::find(candidates.begin(), candidates.end(), normalized) == candidates.end()) {
            candidates.push_back(normalized);
        }
    };

    add_candidate(token);
    add_candidate(ddict_bridge_legacy_owner_token(token));
    add_candidate(ddict_bridge_x64_owner_token(token));

    return candidates;
}

bool owner_matches_any(const std::string& owner,
                       const std::vector<std::string>& candidates) {
    std::string normalized_owner = upper_copy(trim_copy(owner));
    return std::find(candidates.begin(), candidates.end(), normalized_owner) != candidates.end();
}

std::string joined_owner_candidates(const std::vector<std::string>& candidates) {
    std::ostringstream out;
    for (std::size_t i = 0; i < candidates.size(); ++i) {
        if (i != 0) {
            out << ",";
        }
        out << candidates[i];
    }
    return out.str();
}

void print_ddict_usage() {
    std::cout
        << "Usage:\n"
        << "  DDICT HELP\n"
        << "  DDICT STATUS\n"
        << "  DDICT TABLES\n"
        << "  DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]\n"
        << "  DDICT FIELDS <table>\n"
        << "  DDICT TAGS <table>\n"
        << "  DDICT REL <object-id-or-name> [IN|OUT|BOTH]\n"
        << "  DDICT EVIDENCE <object-id-or-name>\n"
        << "Notes:\n"
        << "  DDICT is read-only over the active Data Dictionary catalog.\n";
}

void print_pending(const std::string& sub) {
    std::cout
        << "DDICT " << sub
        << " is accepted by contract but runtime read implementation is pending.\n";
}

void print_status() {
    CatalogStats stats = collect_stats();
    std::cout
        << "DDICT STATUS\n"
        << "  Active catalog: " << stats.dir.string() << "\n"
        << "  Read mode     : READ-ONLY\n"
        << "  DBF tables    : " << stats.dbf_present << " / " << kTables.size() << "\n"
        << "  DTX sidecars  : " << stats.dtx_present << " / " << kTables.size() << "\n"
        << "  DBF bytes     : " << stats.total_dbf_bytes << "\n";
    if (stats.dbf_present == static_cast<int>(kTables.size())) {
        std::cout << "  Catalog state : ACTIVE_CATALOG_PRESENT\n";
    } else {
        std::cout << "  Catalog state : ACTIVE_CATALOG_REVIEW\n";
    }
}

void print_tables() {
    fs::path dir = find_catalog_dir();
    std::cout
        << "DDICT TABLES\n"
        << "  Active catalog: " << dir.string() << "\n"
        << "  Read mode     : READ-ONLY\n"
        << "  Table       DBF  DTX  DBF_BYTES\n"
        << "  ----------  ---  ---  ---------\n";
    for (const auto& t : kTables) {
        fs::path dbf = dir / (std::string(t.name) + ".dbf");
        fs::path dtx = dir / (std::string(t.name) + ".dtx");
        bool has_dbf = exists_quiet(dbf);
        bool has_dtx = exists_quiet(dtx);
        std::cout
            << "  " << std::left << std::setw(10) << t.name
            << "  " << (has_dbf ? "YES" : "NO ")
            << "  " << (has_dtx ? "YES" : "NO ")
            << "  " << size_quiet(dbf)
            << "\n";
    }
}

void print_fields(std::istringstream& args) {
    std::string table_token;
    args >> table_token;
    table_token = upper_copy(trim_copy(table_token));

    if (table_token.empty()) {
        std::cout << "DDICT FIELDS requires a table name.\n";
        return;
    }

    fs::path dir = find_catalog_dir();
    std::vector<Row> objects = read_dbf_table(dir, "DDOBJECT");
    std::vector<Row> attrs = read_dbf_table(dir, "DDATTR");
    std::vector<Row> fields;
    std::vector<std::string> owner_candidates = owner_lookup_candidates(table_token);
    std::string metadata_owner_used;

    for (const auto& row : objects) {
        std::string objtype = upper_copy(value_of(row, "OBJTYPE"));
        std::string owner = upper_copy(value_of(row, "OWNER"));
        if (objtype == "CATALOG_FIELD" && owner_matches_any(owner, owner_candidates)) {
            if (metadata_owner_used.empty()) {
                metadata_owner_used = owner;
            }
            fields.push_back(row);
        }
    }

    std::cout
        << "DDICT FIELDS " << table_token << "\n"
        << "  Active catalog: " << dir.string() << "\n"
        << "  Read mode     : READ-ONLY\n"
        << "  Field rows    : " << fields.size() << "\n";

    if (!metadata_owner_used.empty() && metadata_owner_used != table_token) {
        std::cout << "  Metadata owner: " << metadata_owner_used << "\n";
    }

    if (fields.empty()) {
        // DD096Z-D2ZP FIELDS OWNER-LOOKUP PATCH MARKER
        // Runtime bridge: table aliases are resolved through owner_lookup_candidates() before final NO_FIELDS_FOUND.
        std::cout
            << "  Result        : NO_FIELDS_FOUND\n"
            << "  Note          : expected DDOBJECT rows where OBJTYPE=CATALOG_FIELD and OWNER in "
            << joined_owner_candidates(owner_candidates) << "\n";
        return;
    }

    std::unordered_map<std::string, int> attr_counts;
    for (const auto& attr : attrs) {
        std::string objid = value_of(attr, "OBJID");
        if (!objid.empty()) {
            ++attr_counts[objid];
        }
    }

    std::cout
        << "  Field       OBJID                     STATUS                    PROFILE       ATTRS\n"
        << "  ----------  ------------------------  ------------------------  ------------  -----\n";

    for (const auto& field : fields) {
        std::string objid = value_of(field, "OBJID");
        std::string name = value_of(field, "NAME");
        std::string status = value_of(field, "STATUS");
        std::string profile = value_of(field, "PROFILE");
        int acount = objid.empty() ? 0 : attr_counts[objid];

        std::cout
            << "  " << std::left << std::setw(10) << name.substr(0, 10)
            << "  " << std::setw(24) << objid.substr(0, 24)
            << "  " << std::setw(24) << status.substr(0, 24)
            << "  " << std::setw(12) << profile.substr(0, 12)
            << "  " << acount
            << "\n";
    }
}

void print_tags(std::istringstream& args) {
    std::string table_token;
    args >> table_token;
    table_token = upper_copy(trim_copy(table_token));

    if (table_token.empty()) {
        std::cout << "DDICT TAGS requires a table name.\n";
        return;
    }

    fs::path dir = find_catalog_dir();
    fs::path dbf = dir / (table_token + ".dbf");
    fs::path cdx = find_cdx_file(table_token);
    fs::path lmdb = find_lmdb_dir(table_token);
    std::vector<Row> objects = read_dbf_table(dir, "DDOBJECT");
    std::vector<Row> attrs = read_dbf_table(dir, "DDATTR");
    std::vector<Row> tags;
    std::vector<std::string> owner_candidates = owner_lookup_candidates(table_token);
    std::string metadata_owner_used;

    for (const auto& row : objects) {
        std::string objtype = upper_copy(value_of(row, "OBJTYPE"));
        std::string owner = upper_copy(value_of(row, "OWNER"));
        if (objtype == "CATALOG_TAG" && owner_matches_any(owner, owner_candidates)) {
            if (metadata_owner_used.empty()) {
                metadata_owner_used = owner;
            }
            tags.push_back(row);
        }
    }

    std::unordered_map<std::string, int> attr_counts;
    for (const auto& attr : attrs) {
        std::string objid = value_of(attr, "OBJID");
        if (!objid.empty()) {
            ++attr_counts[objid];
        }
    }

    std::cout
        << "DDICT TAGS " << table_token << "\n"
        << "  Active catalog: " << dir.string() << "\n"
        << "  Read mode     : READ-ONLY\n"
        << "  Table DBF     : " << (exists_quiet(dbf) ? "YES" : "NO") << "\n"
        << "  CDX artifact  : " << (cdx.empty() ? "NO" : cdx.string()) << "\n"
        << "  LMDB mirror   : " << (lmdb.empty() ? "NO" : lmdb.string()) << "\n"
        << "  Catalog tags  : " << tags.size() << "\n";

    if (!metadata_owner_used.empty() && metadata_owner_used != table_token) {
        std::cout << "  Metadata owner: " << metadata_owner_used << "\n";
    }

    if (tags.empty()) {
        // DD096Z-D2ZP TAGS PHYSICAL-REPORT PATCH MARKER
        // Runtime bridge: catalog tag lookup uses owner_lookup_candidates(); physical artifacts are reported honestly.
        bool has_physical_artifact = exists_quiet(dbf) || !cdx.empty() || !lmdb.empty();
        if (has_physical_artifact) {
            std::cout
                << "  Result        : PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS\n"
                << "  Note          : physical DBF/CDX/LMDB artifacts exist, but no DDOBJECT CATALOG_TAG rows were found for OWNER in "
                << joined_owner_candidates(owner_candidates) << "\n";
        } else {
            std::cout
                << "  Result        : NO_CATALOG_TAGS_FOUND\n"
                << "  Note          : expected DDOBJECT rows where OBJTYPE=CATALOG_TAG and OWNER in "
                << joined_owner_candidates(owner_candidates) << "\n";
        }
        return;
    }

    std::cout
        << "  Tag         OBJID                     STATUS                    PROFILE       ATTRS\n"
        << "  ----------  ------------------------  ------------------------  ------------  -----\n";

    for (const auto& tag : tags) {
        std::string objid = value_of(tag, "OBJID");
        std::string name = value_of(tag, "NAME");
        std::string status = value_of(tag, "STATUS");
        std::string profile = value_of(tag, "PROFILE");
        int acount = objid.empty() ? 0 : attr_counts[objid];

        std::cout
            << "  " << std::left << std::setw(10) << name.substr(0, 10)
            << "  " << std::setw(24) << objid.substr(0, 24)
            << "  " << std::setw(24) << status.substr(0, 24)
            << "  " << std::setw(12) << profile.substr(0, 12)
            << "  " << acount
            << "\n";
    }
}

// DD-089E preview: local helper `resolve_object` moved to datadict helper module.

// DD-089E preview: local helper `object_index` moved to datadict helper module.

void print_rel_edge_row(const std::string& dir_label,
                        const Row& edge,
                        const Row* other,
                        bool outgoing) {
    std::string edgeid = value_of(edge, "EDGEID");
    std::string edgetype = value_of(edge, "EDGETYPE");
    std::string evid = value_of(edge, "EVID");
    std::string other_id = value_of(edge, outgoing ? "TOOBJ" : "FROMOBJ");
    std::string other_type = other ? value_of(*other, "OBJTYPE") : "";
    std::string other_name = other ? value_of(*other, "NAME") : "";
    std::string other_owner = other ? value_of(*other, "OWNER") : "";

    std::cout
        << "  " << std::left << std::setw(3) << dir_label
        << "  " << std::setw(18) << short_text(edgetype, 18)
        << "  " << std::setw(24) << short_text(other_id, 24)
        << "  " << std::setw(18) << short_text(other_type, 18)
        << "  " << std::setw(14) << short_text(other_owner, 14)
        << "  " << std::setw(14) << short_text(other_name, 14)
        << "  " << short_text(evid, 20)
        << "\n";
}

void print_rel(std::istringstream& args) {
    std::string token;
    std::string direction;
    args >> token;
    args >> direction;
    token = upper_copy(trim_copy(token));
    direction = upper_copy(trim_copy(direction));
    if (direction.empty()) {
        direction = "BOTH";
    }

    if (token.empty()) {
        std::cout << "DDICT REL requires an object id or name.\n";
        return;
    }
    if (!(direction == "IN" || direction == "OUT" || direction == "BOTH")) {
        std::cout << "DDICT REL direction must be IN, OUT, or BOTH.\n";
        return;
    }

    fs::path dir = find_catalog_dir();
    std::vector<Row> objects = read_dbf_table(dir, "DDOBJECT");
    std::vector<Row> edges = read_dbf_table(dir, "DDEDGE");
    auto by_id = object_index(objects);
    const Row* obj = resolve_object(objects, token);

    std::cout
        << "DDICT REL " << token << " " << direction << "\n"
        << "  Active catalog: " << dir.string() << "\n"
        << "  Read mode     : READ-ONLY\n";

    if (!obj) {
        std::cout
            << "  Result        : OBJECT_NOT_FOUND\n"
            << "  Note          : token was matched against OBJID and DDOBJECT NAME/OWNER.\n";
        return;
    }

    std::string objid = value_of(*obj, "OBJID");
    std::string objtype = value_of(*obj, "OBJTYPE");
    std::string name = value_of(*obj, "NAME");
    std::string owner = value_of(*obj, "OWNER");

    std::cout
        << "  Object OBJID  : " << objid << "\n"
        << "  Object type   : " << objtype << "\n"
        << "  Object owner  : " << owner << "\n"
        << "  Object name   : " << name << "\n";

    std::vector<const Row*> incoming;
    std::vector<const Row*> outgoing;
    for (const auto& edge : edges) {
        if (value_of(edge, "FROMOBJ") == objid) {
            outgoing.push_back(&edge);
        }
        if (value_of(edge, "TOOBJ") == objid) {
            incoming.push_back(&edge);
        }
    }

    std::cout
        << "  Incoming edges: " << incoming.size() << "\n"
        << "  Outgoing edges: " << outgoing.size() << "\n"
        << "  Rows shown    : bounded to 40 per direction\n"
        << "  Dir  EdgeType            OtherOBJ                  OtherType          OtherOwner      OtherName       EVID\n"
        << "  ---  ------------------  ------------------------  -----------------  --------------  --------------  --------------------\n";

    constexpr std::size_t kLimit = 40;
    if (direction == "OUT" || direction == "BOTH") {
        std::size_t shown = 0;
        for (const Row* edge : outgoing) {
            if (shown++ >= kLimit) {
                break;
            }
            std::string other_id = value_of(*edge, "TOOBJ");
            const Row* other = nullptr;
            auto it = by_id.find(other_id);
            if (it != by_id.end()) {
                other = it->second;
            }
            print_rel_edge_row("OUT", *edge, other, true);
        }
    }
    if (direction == "IN" || direction == "BOTH") {
        std::size_t shown = 0;
        for (const Row* edge : incoming) {
            if (shown++ >= kLimit) {
                break;
            }
            std::string other_id = value_of(*edge, "FROMOBJ");
            const Row* other = nullptr;
            auto it = by_id.find(other_id);
            if (it != by_id.end()) {
                other = it->second;
            }
            print_rel_edge_row("IN", *edge, other, false);
        }
    }
}


void print_evidence(std::istringstream& args) {
    std::string token;
    args >> token;
    token = upper_copy(trim_copy(token));

    if (token.empty()) {
        std::cout << "DDICT EVIDENCE requires an object id or name.\n";
        return;
    }

    fs::path dir = find_catalog_dir();
    std::vector<Row> objects = read_dbf_table(dir, "DDOBJECT");
    std::vector<Row> attrs = read_dbf_table(dir, "DDATTR");
    std::vector<Row> evids = read_dbf_table(dir, "DDEVID");
    std::vector<Row> sources = read_dbf_table(dir, "DDSOURCE");
    std::vector<Row> artifacts = read_dbf_table(dir, "DDARTIF");

    const Row* obj = resolve_object(objects, token);

    std::cout
        << "DDICT EVIDENCE " << token << "\n"
        << "  Active catalog: " << dir.string() << "\n"
        << "  Read mode     : READ-ONLY\n";

    if (!obj) {
        std::cout
            << "  Result        : OBJECT_NOT_FOUND\n"
            << "  Note          : token was matched against OBJID and DDOBJECT NAME/OWNER.\n";
        return;
    }

    std::string objid = value_of(*obj, "OBJID");
    std::string objtype = value_of(*obj, "OBJTYPE");
    std::string name = value_of(*obj, "NAME");
    std::string owner = value_of(*obj, "OWNER");

    std::vector<const Row*> direct_evidence;
    for (const auto& ev : evids) {
        if (value_of(ev, "OBJID") == objid) {
            direct_evidence.push_back(&ev);
        }
    }

    std::vector<const Row*> object_attrs;
    for (const auto& attr : attrs) {
        if (value_of(attr, "OBJID") == objid) {
            object_attrs.push_back(&attr);
        }
    }

    std::unordered_map<std::string, const Row*> source_by_id;
    for (const auto& src : sources) {
        std::string srcid = value_of(src, "SRCID");
        if (!srcid.empty()) {
            source_by_id[srcid] = &src;
        }
    }

    std::unordered_map<std::string, const Row*> artifact_by_id;
    for (const auto& art : artifacts) {
        std::string artid = value_of(art, "ARTID");
        if (!artid.empty()) {
            artifact_by_id[artid] = &art;
        }
    }

    std::cout
        << "  Object OBJID  : " << objid << "\n"
        << "  Object type   : " << objtype << "\n"
        << "  Object owner  : " << owner << "\n"
        << "  Object name   : " << name << "\n"
        << "  Direct evidence rows: " << direct_evidence.size() << "\n"
        << "  Attribute evidence rows: " << object_attrs.size() << "\n"
        << "  Rows shown    : bounded to 20 per section\n";

    std::cout
        << "  Evidence rows\n"
        << "  EVID                  KIND                  SRCID                 SOURCE              ARTIFACT\n"
        << "  --------------------  --------------------  --------------------  ------------------  ------------------\n";

    std::size_t shown = 0;
    for (const Row* ev : direct_evidence) {
        if (shown++ >= 20) {
            break;
        }
        std::string srcid = value_of(*ev, "SRCID");
        std::string artid = value_of(*ev, "ARTID");
        const Row* src = nullptr;
        const Row* art = nullptr;
        auto sit = source_by_id.find(srcid);
        if (sit != source_by_id.end()) {
            src = sit->second;
        }
        auto ait = artifact_by_id.find(artid);
        if (ait != artifact_by_id.end()) {
            art = ait->second;
        }

        std::string src_name = src ? (value_of(*src, "PATH").empty() ? value_of(*src, "NAME") : value_of(*src, "PATH")) : "";
        std::string art_name = art ? (value_of(*art, "PATH").empty() ? value_of(*art, "NAME") : value_of(*art, "PATH")) : "";

        std::cout
            << "  " << std::left << std::setw(20) << short_text(value_of(*ev, "EVID"), 20)
            << "  " << std::setw(20) << short_text(value_of(*ev, "KIND"), 20)
            << "  " << std::setw(20) << short_text(srcid, 20)
            << "  " << std::setw(18) << short_text(src_name, 18)
            << "  " << short_text(art_name, 18)
            << "\n";
    }

    if (direct_evidence.empty()) {
        std::cout << "  (none)\n";
    }

    std::cout
        << "  Attribute evidence\n"
        << "  ATTRNAME            ATTRVAL                         EVID\n"
        << "  ------------------  ------------------------------  --------------------\n";

    shown = 0;
    for (const Row* attr : object_attrs) {
        if (shown++ >= 20) {
            break;
        }
        std::string attrval = value_of(*attr, "ATTRVAL");
        if (attrval.empty()) {
            attrval = value_of(*attr, "ATTRMEMO");
        }
        std::cout
            << "  " << std::left << std::setw(18) << short_text(value_of(*attr, "ATTRNAME"), 18)
            << "  " << std::setw(30) << short_text(attrval, 30)
            << "  " << short_text(value_of(*attr, "EVID"), 20)
            << "\n";
    }

    if (object_attrs.empty()) {
        std::cout << "  (none)\n";
    }
}


void print_objects(std::istringstream& args) {
    std::string word;
    std::string type_filter;
    std::string profile_filter;

    while (args >> word) {
        std::string key = upper_copy(trim_copy(word));
        if (key == "TYPE") {
            std::string value;
            args >> value;
            type_filter = upper_copy(trim_copy(value));
        } else if (key == "PROFILE") {
            std::string value;
            args >> value;
            profile_filter = upper_copy(trim_copy(value));
        } else if (type_filter.empty()) {
            type_filter = key;
        }
    }

    fs::path dir = find_catalog_dir();
    std::vector<Row> objects = read_dbf_table(dir, "DDOBJECT");
    std::vector<Row> attrs = read_dbf_table(dir, "DDATTR");

    std::unordered_map<std::string, int> attr_counts;
    for (const auto& attr : attrs) {
        std::string objid = value_of(attr, "OBJID");
        if (!objid.empty()) {
            ++attr_counts[objid];
        }
    }

    std::vector<const Row*> selected;
    for (const auto& obj : objects) {
        std::string objtype = upper_copy(value_of(obj, "OBJTYPE"));
        std::string profile = upper_copy(value_of(obj, "PROFILE"));

        if (!type_filter.empty() && objtype != type_filter) {
            continue;
        }
        if (!profile_filter.empty() && profile != profile_filter) {
            continue;
        }
        selected.push_back(&obj);
    }

    std::cout
        << "DDICT OBJECTS\n"
        << "  Active catalog: " << dir.string() << "\n"
        << "  Read mode     : READ-ONLY\n"
        << "  Type filter   : " << (type_filter.empty() ? "(none)" : type_filter) << "\n"
        << "  Profile filter: " << (profile_filter.empty() ? "(none)" : profile_filter) << "\n"
        << "  Object rows   : " << selected.size() << "\n"
        << "  Rows shown    : bounded to 80\n"
        << "  OBJTYPE             NAME              OWNER             STATUS                    PROFILE       ATTRS\n"
        << "  ------------------  ----------------  ----------------  ------------------------  ------------  -----\n";

    constexpr std::size_t kLimit = 80;
    std::size_t shown = 0;
    for (const Row* obj : selected) {
        if (shown++ >= kLimit) {
            break;
        }
        std::string objid = value_of(*obj, "OBJID");
        int acount = objid.empty() ? 0 : attr_counts[objid];

        std::cout
            << "  " << std::left << std::setw(18) << short_text(value_of(*obj, "OBJTYPE"), 18)
            << "  " << std::setw(16) << short_text(value_of(*obj, "NAME"), 16)
            << "  " << std::setw(16) << short_text(value_of(*obj, "OWNER"), 16)
            << "  " << std::setw(24) << short_text(value_of(*obj, "STATUS"), 24)
            << "  " << std::setw(12) << short_text(value_of(*obj, "PROFILE"), 12)
            << "  " << acount
            << "\n";
    }

    if (selected.empty()) {
        std::cout << "  (none)\n";
    }
}

} // anonymous namespace

void cmd_DDICT(xbase::DbArea& area, std::istringstream& args) {
    (void)area;

    std::string sub;
    args >> sub;
    sub = upper_copy(trim_copy(sub));

    if (sub.empty() || sub == "HELP" || sub == "?" || sub == "USAGE") {
        print_ddict_usage();
        return;
    }

    if (sub == "STATUS") {
        print_status();
        return;
    }

    if (sub == "TABLES") {
        print_tables();
        return;
    }

    if (sub == "FIELDS") {
        print_fields(args);
        return;
    }

    if (sub == "TAGS") {
        print_tags(args);
        return;
    }

    if (sub == "REL") {
        print_rel(args);
        return;
    }

    if (sub == "EVIDENCE") {
        print_evidence(args);
        return;
    }

    if (sub == "OBJECTS") {
        print_objects(args);
        return;
    }

    std::cout << "DDICT: unknown subcommand '" << sub << "'.\n";
    print_ddict_usage();
}
