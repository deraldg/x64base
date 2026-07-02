// ============================================================================
// File: src/help/message_catalog.cpp
// Purpose: Runtime Messaging catalog provider boundary.
// Phase: MSG-022F active DBF row-load provider.
// ============================================================================

#include "message_catalog.hpp"

#include "cli/memo_field_store.hpp"
#include "cli/path_resolver.hpp"
#include "helpdata_messages.hpp"

#include "cdx/cdx.hpp"
#include "memo/memo_auto.hpp"
#include "memo/memostore.hpp"
#include "xbase.hpp"
#include "xbase_64.hpp"
#include "xbase_locks.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <lmdb.h>
#include <sstream>
#include <stdexcept>
#include <string>
#include <system_error>
#include <unordered_map>
#include <vector>

namespace dottalk::helpdata {
namespace {

namespace fs = std::filesystem;

struct ActiveCatalogPaths {
    fs::path dbf_dir;
    fs::path indexes_dir;
    fs::path lmdb_dir;
    bool present = false;
};

struct ActiveMessageRow {
    std::string msgid;
    std::string symbol;
    std::string enumname;
    std::string facility;
    std::string owner;
    std::string category;
    std::string severity;
    std::string status;
    std::string src;
};

struct ActiveTextRow {
    std::string msgid;
    std::string symbol;
    std::string enumname;
    std::string locale;
    std::string msglocale;
    std::string symbolloc;
    std::string text;
    std::string txthash;
    std::string status;
    std::string src;
};

struct ActiveCatalogLoad {
    ActiveCatalogPaths paths;
    bool loaded = false;
    std::string detail;
    std::vector<ActiveMessageRow> messages;
    std::vector<ActiveTextRow> texts;
    std::unordered_map<std::string, std::string> text_by_symbol_locale;
};

struct SeedMessageRow {
    std::string msgid;
    std::string symbol;
    std::string enumname;
    std::string facility;
    std::string owner;
    std::string category;
    std::string severity;
    std::string status;
    std::string src;
};

struct SeedTextRow {
    std::string msgid;
    std::string symbol;
    std::string enumname;
    std::string locale;
    std::string msglocale;
    std::string symbolloc;
    std::string text;
    std::string txthash;
    std::string status;
    std::string src;
};

struct MessageFieldIndexes {
    int msgid = 0;
    int symbol = 0;
    int enumname = 0;
    int facility = 0;
    int owner = 0;
    int category = 0;
    int severity = 0;
    int status = 0;
    int src = 0;
};

struct TextFieldIndexes {
    int msgid = 0;
    int symbol = 0;
    int enumname = 0;
    int locale = 0;
    int msglocale = 0;
    int symbolloc = 0;
    int text = 0;
    int txthash = 0;
    int status = 0;
    int src = 0;
};

struct MatchResult {
    int first_recno = 0;
    int matches = 0;
};

struct AreaCloser {
    xbase::DbArea& area;
    ~AreaCloser()
    {
        try {
            if (area.isOpen()) {
                cli_memo::memo_auto_on_close(area);
            }
        } catch (...) {
        }

        try {
            if (area.isOpen()) {
                area.close();
            }
        } catch (...) {
        }
    }
};

struct TableLockGuard {
    xbase::DbArea* area = nullptr;
    bool locked = false;

    ~TableLockGuard()
    {
        if (locked && area) {
            xbase::locks::unlock_table(*area);
        }
    }
};

constexpr std::uint64_t MESSAGE_LMDB_MAPSIZE =
    128ULL * 1024ULL * 1024ULL;

std::string field_value(xbase::DbArea& area, int field1);

std::string generic_string(const fs::path& p)
{
    return p.lexically_normal().generic_string();
}

std::string trim_copy(std::string s)
{
    auto not_space = [](unsigned char ch) { return !std::isspace(ch); };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), not_space));
    s.erase(std::find_if(s.rbegin(), s.rend(), not_space).base(), s.end());
    return s;
}

std::string upper_copy(std::string s)
{
    for (auto& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

std::string text_key(const std::string& symbol, const std::string& locale)
{
    return upper_copy(trim_copy(symbol)) + "\x1f" + upper_copy(trim_copy(locale));
}

std::vector<fs::path> data_root_candidates()
{
    std::vector<fs::path> roots;

    fs::path cur = fs::current_path();
    for (fs::path p = cur; !p.empty(); p = p.parent_path()) {
        roots.push_back(p / "dottalkpp" / "data");
        roots.push_back(p / "data");

        if (p == p.parent_path()) {
            break;
        }
    }

    roots.push_back(fs::path("dottalkpp") / "data");
    return roots;
}

bool messaging_artifacts_present(const fs::path& dbf_dir)
{
    return fs::exists(dbf_dir / "SYSTEM_MESSAGES.dbf")
        && fs::exists(dbf_dir / "SYSTEM_MESSAGE_TEXT.dbf")
        && fs::exists(dbf_dir / "SYSTEM_MESSAGE_TEXT.dtx");
}

ActiveCatalogPaths find_active_catalog_paths()
{
    for (const auto& data_root : data_root_candidates()) {
        ActiveCatalogPaths current{
            data_root / "messaging",
            data_root / "indexes" / "messaging",
            data_root / "lmdb" / "messaging",
            false
        };
        if (messaging_artifacts_present(current.dbf_dir)) {
            current.present = true;
            return current;
        }

        ActiveCatalogPaths dbf_subdir{
            data_root / "dbf" / "messaging",
            data_root / "indexes" / "messaging",
            data_root / "lmdb" / "messaging",
            false
        };
        if (messaging_artifacts_present(dbf_subdir.dbf_dir)) {
            dbf_subdir.present = true;
            return dbf_subdir;
        }
    }

    ActiveCatalogPaths fallback{
        fs::path("dottalkpp") / "data" / "messaging",
        fs::path("dottalkpp") / "data" / "indexes" / "messaging",
        fs::path("dottalkpp") / "data" / "lmdb" / "messaging",
        false
    };
    return fallback;
}

int field_index_ci(const xbase::DbArea& area, const std::string& wanted)
{
    const std::string w = upper_copy(wanted);
    const auto& fields = area.fields();
    for (std::size_t i = 0; i < fields.size(); ++i) {
        if (upper_copy(fields[i].name) == w) {
            return static_cast<int>(i + 1);
        }
    }
    return 0;
}

bool has_memo_fields(const xbase::DbArea& area)
{
    for (const auto& f : area.fields()) {
        if (f.type == 'M' || f.type == 'm') {
            return true;
        }
    }
    return false;
}

bool is_x64_memo_field(const xbase::DbArea& area, int field1)
{
    if (field1 < 1 || field1 > area.fieldCount()) return false;
    if (area.versionByte() != xbase::DBF_VERSION_64) return false;

    const auto& f = area.fields()[static_cast<std::size_t>(field1 - 1)];
    return (f.type == 'M' || f.type == 'm') &&
           f.length == xbase::X64_MEMO_FIELD_LEN;
}

std::uint64_t parse_u64_or_zero(const std::string& s)
{
    const std::string t = trim_copy(s);
    if (t.empty()) return 0;
    try {
        std::size_t used = 0;
        const auto v = std::stoull(t, &used, 10);
        if (used != t.size()) return 0;
        return static_cast<std::uint64_t>(v);
    } catch (...) {
        return 0;
    }
}

const std::vector<SeedMessageRow>& priority_a_message_rows()
{
    static const std::vector<SeedMessageRow> rows{
        {"15", "SET_MESSAGE_PROOF_USAGE_TEXT", "SetMessageProofUsageText",
         "COMMAND:SET", "COMMAND:SET", "USAGE", "INFO", "ACTIVE", "PHASE25A"},
        {"16", "SET_MESSAGE_EMIT_USAGE_TEXT", "SetMessageEmitUsageText",
         "COMMAND:SET", "COMMAND:SET", "USAGE", "INFO", "ACTIVE", "PHASE25A"},
        {"17", "MSGMGR_USAGE_TEXT", "MsgMgrUsageText",
         "COMMAND:MSGMGR", "COMMAND:MSGMGR", "STATUS", "INFO", "ACTIVE", "PHASE25A"},
        {"18", "MSGMGR_STATUS_TITLE", "MsgMgrStatusTitle",
         "COMMAND:MSGMGR", "COMMAND:MSGMGR", "STATUS", "INFO", "ACTIVE", "PHASE25A"},
        {"19", "MSGMGR_STATUS_BODY_TEXT", "MsgMgrStatusBodyText",
         "COMMAND:MSGMGR", "COMMAND:MSGMGR", "STATUS", "INFO", "ACTIVE", "PHASE25A"},
    };
    return rows;
}

const std::vector<SeedTextRow>& priority_a_text_rows()
{
    static const std::vector<SeedTextRow> rows{
        {"15", "SET_MESSAGE_PROOF_USAGE_TEXT", "SetMessageProofUsageText",
         "en-US", "0000000015|en-US", "SET_MESSAGE_PROOF_USAGE_TEXT|en-US",
         "Usage:\n  SET MESSAGE PROOF ON\n  SET MESSAGE PROOF OFF\n  SET MESSAGE PROOF CHECK",
         "540455748069168b59680257a71a2bece9767bcb9e63af69191fc5b276c95e83",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"16", "SET_MESSAGE_EMIT_USAGE_TEXT", "SetMessageEmitUsageText",
         "en-US", "0000000016|en-US", "SET_MESSAGE_EMIT_USAGE_TEXT|en-US",
         "Usage:\n  SET MESSAGE CATALOG CHECK\n  SET MESSAGE PROOF ON|OFF|CHECK\n  SET MESSAGE EMIT <symbol> [LOCALE <locale>] [ARG <name> <value>]",
         "2e57b202a4f8e2d756c82fc16a4f1b9d61374e75b06ab2159b49fc4c4c32ca86",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"17", "MSGMGR_USAGE_TEXT", "MsgMgrUsageText",
         "en-US", "0000000017|en-US", "MSGMGR_USAGE_TEXT|en-US",
         "Usage:\n  MSGMGR\n  MSGMGR USAGE\n  MSGMGR STATUS\n  MSGMGR CHECK\n  MSGMGR SEED PRIORITYA CHECK\n  MSGMGR SEED PRIORITYA APPLY\n  MSGMGR SEED PRIORITYB CHECK\n  MSGMGR SEED PRIORITYB APPLY\n  MSGMGR SEED PRIORITYC CHECK\n  MSGMGR SEED PRIORITYC APPLY\nNotes:\n  - STATUS and CHECK remain read/report surfaces.\n  - SEED PRIORITYA CHECK/APPLY maintains SET MESSAGE / MSGMGR rows.\n  - SEED PRIORITYB CHECK/APPLY maintains the demoed command-surface rows.\n  - SEED PRIORITYC CHECK/APPLY maintains USE / DISPLAY / navigation runtime lines.",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"18", "MSGMGR_STATUS_TITLE", "MsgMgrStatusTitle",
         "en-US", "0000000018|en-US", "MSGMGR_STATUS_TITLE|en-US",
         "MSGMGR STATUS",
         "11502412e665de744dd10df17fb346dd0cbeb01a5cda97869390d7929292460c",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"18", "MSGMGR_STATUS_TITLE", "MsgMgrStatusTitle",
         "es", "0000000018|es", "MSGMGR_STATUS_TITLE|es",
         "ESTADO DE MSGMGR",
         "9393751ab1b8859f75e337f388da4307e0d486ff94fe50d8a6415edb910b12c5",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"18", "MSGMGR_STATUS_TITLE", "MsgMgrStatusTitle",
         "fr", "0000000018|fr", "MSGMGR_STATUS_TITLE|fr",
         "ETAT MSGMGR",
         "24b238712671c1ee0e99a20fabe2be33119870602991c33fe48b75434cb93b82",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"18", "MSGMGR_STATUS_TITLE", "MsgMgrStatusTitle",
         "de", "0000000018|de", "MSGMGR_STATUS_TITLE|de",
         "MSGMGR-STATUS",
         "a7c99e8c8159be89d89f54964abaf89b85ac389b0003862524f4d92c2fb0dd64",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"18", "MSGMGR_STATUS_TITLE", "MsgMgrStatusTitle",
         "it", "0000000018|it", "MSGMGR_STATUS_TITLE|it",
         "STATO MSGMGR",
         "28a1413f73f5011dfb8d2a3244dc2053b5a5ba538c65b8c3b8b880b73fa2b62d",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"19", "MSGMGR_STATUS_BODY_TEXT", "MsgMgrStatusBodyText",
         "en-US", "0000000019|en-US", "MSGMGR_STATUS_BODY_TEXT|en-US",
         "  command house        : registered\n  read mode            : mixed\n  active message check : SET MESSAGE CATALOG CHECK\n  active message get   : SET MESSAGE CATALOG GET\n  seed bundle A        : MSGMGR SEED PRIORITYA CHECK|APPLY\n  seed bundle B        : MSGMGR SEED PRIORITYB CHECK|APPLY\n  seed bundle C        : MSGMGR SEED PRIORITYC CHECK|APPLY\n  provider mode        : active_dbf\n  message DBF root     : dottalkpp/data/messaging\n  message index root   : dottalkpp/data/indexes/messaging\n  message LMDB root    : dottalkpp/data/lmdb/messaging\n  locale spine         : scaffold present; runtime status wiring held\n  schema root          : dottalkpp/data/schemas\n  locale schema        : dottalkpp/data/schemas/locale/locale_spine.dtschema",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
    };
    return rows;
}

const std::vector<SeedMessageRow>& priority_b_message_rows()
{
    static const std::vector<SeedMessageRow> rows{
        {"20", "DISPLAY_USAGE_TEXT", "DisplayUsageText",
         "COMMAND:DISPLAY", "COMMAND:DISPLAY", "USAGE", "INFO", "ACTIVE", "PHASE25B"},
        {"21", "USE_USAGE_TEXT", "UseUsageText",
         "COMMAND:USE", "COMMAND:USE", "USAGE", "INFO", "ACTIVE", "PHASE25B"},
        {"22", "GO_USAGE_TEXT", "GoUsageText",
         "COMMAND:GO", "COMMAND:GO", "USAGE", "INFO", "ACTIVE", "PHASE25B"},
        {"23", "GOTO_USAGE_TEXT", "GotoUsageText",
         "COMMAND:GOTO", "COMMAND:GOTO", "USAGE", "INFO", "ACTIVE", "PHASE25B"},
        {"24", "SKIP_USAGE_TEXT", "SkipUsageText",
         "COMMAND:SKIP", "COMMAND:SKIP", "USAGE", "INFO", "ACTIVE", "PHASE25B"},
        {"25", "TOP_USAGE_TEXT", "TopUsageText",
         "COMMAND:TOP", "COMMAND:TOP", "USAGE", "INFO", "ACTIVE", "PHASE25B"},
        {"26", "BOTTOM_USAGE_TEXT", "BottomUsageText",
         "COMMAND:BOTTOM", "COMMAND:BOTTOM", "USAGE", "INFO", "ACTIVE", "PHASE25B"},
        {"27", "FIRST_USAGE_TEXT", "FirstUsageText",
         "COMMAND:FIRST", "COMMAND:FIRST", "USAGE", "INFO", "ACTIVE", "PHASE25B"},
        {"28", "LAST_USAGE_TEXT", "LastUsageText",
         "COMMAND:LAST", "COMMAND:LAST", "USAGE", "INFO", "ACTIVE", "PHASE25B"},
        {"29", "NEXT_USAGE_TEXT", "NextUsageText",
         "COMMAND:NEXT", "COMMAND:NEXT", "USAGE", "INFO", "ACTIVE", "PHASE25B"},
        {"30", "PRIOR_USAGE_TEXT", "PriorUsageText",
         "COMMAND:PRIOR", "COMMAND:PRIOR", "USAGE", "INFO", "ACTIVE", "PHASE25B"},
        {"31", "BBOX_MESSAGING_LANE_TEXT", "BBoxMessagingLaneText",
         "COMMAND:BBOX", "COMMAND:BBOX", "STATUS", "INFO", "ACTIVE", "PHASE25B"},
        {"32", "MAINT_BOUNDARY_TEXT", "MaintBoundaryText",
         "COMMAND:MAINT", "COMMAND:MAINT", "STATUS", "INFO", "ACTIVE", "PHASE25B"},
        {"33", "DDICT_USAGE_TEXT", "DDictUsageText",
         "COMMAND:DDICT", "COMMAND:DDICT", "STATUS", "INFO", "ACTIVE", "PHASE25B"},
    };
    return rows;
}

const std::vector<SeedTextRow>& priority_b_text_rows()
{
    static const std::vector<SeedTextRow> rows{
        {"20", "DISPLAY_USAGE_TEXT", "DisplayUsageText",
         "en-US", "0000000020|en-US", "DISPLAY_USAGE_TEXT|en-US",
         "Usage:\n  DISPLAY\n  DISPLAY USAGE\n  DISPLAY <recno>",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"21", "USE_USAGE_TEXT", "UseUsageText",
         "en-US", "0000000021|en-US", "USE_USAGE_TEXT|en-US",
         "Usage:\n  USE USAGE              (Show this usage)\n  USE <table>            (Open <DBF slot>/<table>.dbf in current area)\n  USE <table.dbf>        (Open named DBF; logical names resolve through DBF slot)\n  USE <path\\\\table.dbf>   (Open explicit path)\n  USE <table> NOINDEX    (Open in physical order; skip index auto-attach)\n  USE <table> NOIDX      (Alias of NOINDEX)\nNotes:\n  - USE closes/resets the current area before opening the target table.\n  - USE prevents duplicate opens of the same DBF path across work areas.\n  - USE auto-attaches memo storage when memo fields are present.\n  - USE auto-attaches flavor-appropriate indexes when present, unless NOINDEX/NOIDX is used.\n  - USE prefers the configured INDEXES slot and falls back to the DBF directory.\n  - x64/v128 tables prefer CDX; x32 tables prefer CNX, then INX/IDX.",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"22", "GO_USAGE_TEXT", "GoUsageText",
         "en-US", "0000000022|en-US", "GO_USAGE_TEXT|en-US",
         "Usage:\n  GO\n  GO USAGE\n  GO TOP\n  GO BOTTOM\n  GO FIRST\n  GO LAST\n  GO TO <recno>\n  GO RECORD <recno>\n  GO <recno>\n  GO +<n>\n  GO -<n>",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"23", "GOTO_USAGE_TEXT", "GotoUsageText",
         "en-US", "0000000023|en-US", "GOTO_USAGE_TEXT|en-US",
         "Usage:\n  GOTO USAGE\n  GOTO <recno>\n  GOTO FIRST\n  GOTO LAST",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"24", "SKIP_USAGE_TEXT", "SkipUsageText",
         "en-US", "0000000024|en-US", "SKIP_USAGE_TEXT|en-US",
         "Usage:\n  SKIP\n  SKIP USAGE\n  SKIP <n>",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"25", "TOP_USAGE_TEXT", "TopUsageText",
         "en-US", "0000000025|en-US", "TOP_USAGE_TEXT|en-US",
         "Usage:\n  TOP\n  TOP USAGE",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"26", "BOTTOM_USAGE_TEXT", "BottomUsageText",
         "en-US", "0000000026|en-US", "BOTTOM_USAGE_TEXT|en-US",
         "Usage:\n  BOTTOM\n  BOTTOM USAGE",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"27", "FIRST_USAGE_TEXT", "FirstUsageText",
         "en-US", "0000000027|en-US", "FIRST_USAGE_TEXT|en-US",
         "Usage:\n  FIRST\n  FIRST USAGE",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"28", "LAST_USAGE_TEXT", "LastUsageText",
         "en-US", "0000000028|en-US", "LAST_USAGE_TEXT|en-US",
         "Usage:\n  LAST\n  LAST USAGE",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"29", "NEXT_USAGE_TEXT", "NextUsageText",
         "en-US", "0000000029|en-US", "NEXT_USAGE_TEXT|en-US",
         "Usage:\n  NEXT\n  NEXT USAGE",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"30", "PRIOR_USAGE_TEXT", "PriorUsageText",
         "en-US", "0000000030|en-US", "PRIOR_USAGE_TEXT|en-US",
         "Usage:\n  PRIOR\n  PRIOR USAGE",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"31", "BBOX_MESSAGING_LANE_TEXT", "BBoxMessagingLaneText",
         "en-US", "0000000031|en-US", "BBOX_MESSAGING_LANE_TEXT|en-US",
         "MESSAGING BLACKBOX\n  DATA IN: hard-coded text, message IDs, message arguments, locale/language rows\n  PROCESS: extract, catalog, localize, validate placeholders, replace source strings gradually\n  OUT: x64base message catalog, localized runtime text, typed warnings/errors/status/help messages\n  CONTROL: SET LANGUAGE / SET LOCALE selects message-rendering locale where supported.",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"32", "MAINT_BOUNDARY_TEXT", "MaintBoundaryText",
         "en-US", "0000000032|en-US", "MAINT_BOUNDARY_TEXT|en-US",
         "MAINT BOUNDARY\n  first-wave MAINT is inspection-only.\n  It must not mutate:\n    - source files\n    - HELP DATA or raw HELP DBFs\n    - CMDHELPCHK expectations\n    - metadata catalogs\n    - DBF/CDX/LMDB artifacts\n    - runtime scripts\n    - publications or media\n  Mutation lanes require separate guarded packages and explicit authorization.",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"33", "DDICT_USAGE_TEXT", "DDictUsageText",
         "en-US", "0000000033|en-US", "DDICT_USAGE_TEXT|en-US",
         "Usage:\n  DDICT HELP\n  DDICT STATUS\n  DDICT TABLES\n  DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]\n  DDICT FIELDS <table>\n  DDICT TAGS <table>\n  DDICT REL <object-id-or-name> [IN|OUT|BOTH]\n  DDICT EVIDENCE <object-id-or-name>\nNotes:\n  DDICT is read-only over the active Data Dictionary catalog.",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
    };
    return rows;
}

const std::vector<SeedMessageRow>& priority_c_message_rows()
{
    static const std::vector<SeedMessageRow> rows{
        {"34", "USE_MISSING_TABLE_NAME_TEXT", "UseMissingTableNameText",
         "COMMAND:USE", "COMMAND:USE", "ERROR", "ERROR", "ACTIVE", "PHASE25C"},
        {"35", "USE_ALREADY_OPEN_CURRENT_AREA_TEXT", "UseAlreadyOpenCurrentAreaText",
         "COMMAND:USE", "COMMAND:USE", "STATUS", "INFO", "ACTIVE", "PHASE25C"},
        {"36", "USE_ALREADY_OPEN_OTHER_AREA_TEXT", "UseAlreadyOpenOtherAreaText",
         "COMMAND:USE", "COMMAND:USE", "STATUS", "INFO", "ACTIVE", "PHASE25C"},
        {"37", "USE_OPEN_FAILED_WITH_REASON_TEXT", "UseOpenFailedWithReasonText",
         "COMMAND:USE", "COMMAND:USE", "ERROR", "ERROR", "ACTIVE", "PHASE25C"},
        {"38", "USE_OPEN_FAILED_TEXT", "UseOpenFailedText",
         "COMMAND:USE", "COMMAND:USE", "ERROR", "ERROR", "ACTIVE", "PHASE25C"},
        {"39", "USE_MEMO_ATTACH_FAILED_TEXT", "UseMemoAttachFailedText",
         "COMMAND:USE", "COMMAND:USE", "ERROR", "ERROR", "ACTIVE", "PHASE25C"},
        {"40", "USE_OPENED_SUMMARY_TEXT", "UseOpenedSummaryText",
         "COMMAND:USE", "COMMAND:USE", "STATUS", "INFO", "ACTIVE", "PHASE25C"},
        {"41", "USE_VALID_INDEXES_LINE_TEXT", "UseValidIndexesLineText",
         "COMMAND:USE", "COMMAND:USE", "STATUS", "INFO", "ACTIVE", "PHASE25C"},
        {"42", "USE_NOINDEX_SKIPPED_TEXT", "UseNoIndexSkippedText",
         "COMMAND:USE", "COMMAND:USE", "STATUS", "INFO", "ACTIVE", "PHASE25C"},
        {"43", "USE_AUTO_ATTACHED_ORDER_TAG_UNIQUE_TEXT", "UseAutoAttachedOrderTagUniqueText",
         "COMMAND:USE", "COMMAND:USE", "STATUS", "INFO", "ACTIVE", "PHASE25C"},
        {"44", "USE_AUTO_ATTACHED_ORDER_TAG_TEXT", "UseAutoAttachedOrderTagText",
         "COMMAND:USE", "COMMAND:USE", "STATUS", "INFO", "ACTIVE", "PHASE25C"},
        {"45", "USE_AUTO_ATTACHED_ORDER_TEXT", "UseAutoAttachedOrderText",
         "COMMAND:USE", "COMMAND:USE", "STATUS", "INFO", "ACTIVE", "PHASE25C"},
        {"46", "NAV_NO_FILE_OPEN_TEXT", "NavNoFileOpenText",
         "SUBSYSTEM:NAV", "SUBSYSTEM:NAV", "ERROR", "ERROR", "ACTIVE", "PHASE25C"},
        {"47", "NAV_READ_CURRENT_FAILED_TEXT", "NavReadCurrentFailedText",
         "SUBSYSTEM:NAV", "SUBSYSTEM:NAV", "ERROR", "ERROR", "ACTIVE", "PHASE25C"},
        {"48", "NAV_AT_TOP_TEXT", "NavAtTopText",
         "SUBSYSTEM:NAV", "SUBSYSTEM:NAV", "STATUS", "INFO", "ACTIVE", "PHASE25C"},
        {"49", "NAV_AT_END_TEXT", "NavAtEndText",
         "SUBSYSTEM:NAV", "SUBSYSTEM:NAV", "STATUS", "INFO", "ACTIVE", "PHASE25C"},
        {"50", "NAV_FAILED_TEXT", "NavFailedText",
         "SUBSYSTEM:NAV", "SUBSYSTEM:NAV", "ERROR", "ERROR", "ACTIVE", "PHASE25C"},
        {"51", "NAV_RECNO_LINE", "NavRecnoLine",
         "SUBSYSTEM:NAV", "SUBSYSTEM:NAV", "STATUS", "INFO", "ACTIVE", "PHASE25C"},
        {"52", "NO_OPEN_TABLE", "NoOpenTable",
         "SUBSYSTEM:DBAREA", "SUBSYSTEM:DBAREA", "ERROR", "ERROR", "ACTIVE", "PHASE25C"},
        {"53", "GO_EXPECTED_POSITIVE_RECORD_NUMBER_TEXT", "GoExpectedPositiveRecordNumberText",
         "COMMAND:GO", "COMMAND:GO", "ERROR", "ERROR", "ACTIVE", "PHASE25C"},
        {"54", "GO_AREA_QUALIFIER_NOT_SUPPORTED_YET_TEXT", "GoAreaQualifierNotSupportedYetText",
         "COMMAND:GO", "COMMAND:GO", "ERROR", "ERROR", "ACTIVE", "PHASE25C"},
        {"55", "GO_UNRECOGNIZED_COMMAND_FORM_TEXT", "GoUnrecognizedCommandFormText",
         "COMMAND:GO", "COMMAND:GO", "ERROR", "ERROR", "ACTIVE", "PHASE25C"},
    };
    return rows;
}

const std::vector<SeedTextRow>& priority_c_text_rows()
{
    static const std::vector<SeedTextRow> rows{
        {"34", "USE_MISSING_TABLE_NAME_TEXT", "UseMissingTableNameText",
         "en-US", "0000000034|en-US", "USE_MISSING_TABLE_NAME_TEXT|en-US",
         "missing table name.",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"35", "USE_ALREADY_OPEN_CURRENT_AREA_TEXT", "UseAlreadyOpenCurrentAreaText",
         "en-US", "0000000035|en-US", "USE_ALREADY_OPEN_CURRENT_AREA_TEXT|en-US",
         "'{file}' is already open in current area {area}.",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"36", "USE_ALREADY_OPEN_OTHER_AREA_TEXT", "UseAlreadyOpenOtherAreaText",
         "en-US", "0000000036|en-US", "USE_ALREADY_OPEN_OTHER_AREA_TEXT|en-US",
         "'{file}' is already open in area {area}. Close it first (e.g., SCHEMAS CLOSE {area}).",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"37", "USE_OPEN_FAILED_WITH_REASON_TEXT", "UseOpenFailedWithReasonText",
         "en-US", "0000000037|en-US", "USE_OPEN_FAILED_WITH_REASON_TEXT|en-US",
         "Open failed: {reason}",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"38", "USE_OPEN_FAILED_TEXT", "UseOpenFailedText",
         "en-US", "0000000038|en-US", "USE_OPEN_FAILED_TEXT|en-US",
         "Open failed.",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"39", "USE_MEMO_ATTACH_FAILED_TEXT", "UseMemoAttachFailedText",
         "en-US", "0000000039|en-US", "USE_MEMO_ATTACH_FAILED_TEXT|en-US",
         "memo attach failed: {reason}",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"40", "USE_OPENED_SUMMARY_TEXT", "UseOpenedSummaryText",
         "en-US", "0000000040|en-US", "USE_OPENED_SUMMARY_TEXT|en-US",
         "Opened {name} ({version}) : Record count {count}",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"41", "USE_VALID_INDEXES_LINE_TEXT", "UseValidIndexesLineText",
         "en-US", "0000000041|en-US", "USE_VALID_INDEXES_LINE_TEXT|en-US",
         "Valid Index/Indices   : {types}",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"42", "USE_NOINDEX_SKIPPED_TEXT", "UseNoIndexSkippedText",
         "en-US", "0000000042|en-US", "USE_NOINDEX_SKIPPED_TEXT|en-US",
         "NOINDEX: auto-attach skipped (physical order).",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"43", "USE_AUTO_ATTACHED_ORDER_TAG_UNIQUE_TEXT", "UseAutoAttachedOrderTagUniqueText",
         "en-US", "0000000043|en-US", "USE_AUTO_ATTACHED_ORDER_TAG_UNIQUE_TEXT|en-US",
         "Auto-attached order: {file} (tag: {tag} [UNIQUE])",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"44", "USE_AUTO_ATTACHED_ORDER_TAG_TEXT", "UseAutoAttachedOrderTagText",
         "en-US", "0000000044|en-US", "USE_AUTO_ATTACHED_ORDER_TAG_TEXT|en-US",
         "Auto-attached order: {file} (tag: {tag})",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"45", "USE_AUTO_ATTACHED_ORDER_TEXT", "UseAutoAttachedOrderText",
         "en-US", "0000000045|en-US", "USE_AUTO_ATTACHED_ORDER_TEXT|en-US",
         "Auto-attached order: {file}",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"46", "NAV_NO_FILE_OPEN_TEXT", "NavNoFileOpenText",
         "en-US", "0000000046|en-US", "NAV_NO_FILE_OPEN_TEXT|en-US",
         "no file open.",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"47", "NAV_READ_CURRENT_FAILED_TEXT", "NavReadCurrentFailedText",
         "en-US", "0000000047|en-US", "NAV_READ_CURRENT_FAILED_TEXT|en-US",
         "failed to read record.",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"48", "NAV_AT_TOP_TEXT", "NavAtTopText",
         "en-US", "0000000048|en-US", "NAV_AT_TOP_TEXT|en-US",
         "at top.",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"49", "NAV_AT_END_TEXT", "NavAtEndText",
         "en-US", "0000000049|en-US", "NAV_AT_END_TEXT|en-US",
         "at end.",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"50", "NAV_FAILED_TEXT", "NavFailedText",
         "en-US", "0000000050|en-US", "NAV_FAILED_TEXT|en-US",
         "failed.",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"51", "NAV_RECNO_LINE", "NavRecnoLine",
         "en-US", "0000000051|en-US", "NAV_RECNO_LINE|en-US",
         "Recno: {recno}",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"52", "NO_OPEN_TABLE", "NoOpenTable",
         "en-US", "0000000052|en-US", "NO_OPEN_TABLE|en-US",
         "No table is currently open.",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"53", "GO_EXPECTED_POSITIVE_RECORD_NUMBER_TEXT", "GoExpectedPositiveRecordNumberText",
         "en-US", "0000000053|en-US", "GO_EXPECTED_POSITIVE_RECORD_NUMBER_TEXT|en-US",
         "expected a positive record number",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"54", "GO_AREA_QUALIFIER_NOT_SUPPORTED_YET_TEXT", "GoAreaQualifierNotSupportedYetText",
         "en-US", "0000000054|en-US", "GO_AREA_QUALIFIER_NOT_SUPPORTED_YET_TEXT|en-US",
         "'IN <alias>' not supported yet (SELECT the area, then GO ...)",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
        {"55", "GO_UNRECOGNIZED_COMMAND_FORM_TEXT", "GoUnrecognizedCommandFormText",
         "en-US", "0000000055|en-US", "GO_UNRECOGNIZED_COMMAND_FORM_TEXT|en-US",
         "unrecognized form",
         "",
         "ACTIVE", "src/help/helpdata_messages.cpp"},
    };
    return rows;
}

std::string describe_messages_match(const std::string& symbol)
{
    return "SYSTEM_MESSAGES SYMBOL=" + symbol;
}

std::string describe_text_match(const std::string& symbol, const std::string& locale)
{
    return "SYSTEM_MESSAGE_TEXT SYMBOL=" + symbol + " LOCALE=" + locale;
}

MessageFieldIndexes require_message_fields(const xbase::DbArea& area)
{
    MessageFieldIndexes f;
    f.msgid = field_index_ci(area, "MSGID");
    f.symbol = field_index_ci(area, "SYMBOL");
    f.enumname = field_index_ci(area, "ENUMNAME");
    f.facility = field_index_ci(area, "FACILITY");
    f.owner = field_index_ci(area, "OWNER");
    f.category = field_index_ci(area, "CATEGORY");
    f.severity = field_index_ci(area, "SEVERITY");
    f.status = field_index_ci(area, "STATUS");
    f.src = field_index_ci(area, "SRC");

    if (!f.msgid || !f.symbol || !f.enumname || !f.facility || !f.owner ||
        !f.category || !f.severity || !f.status || !f.src) {
        throw std::runtime_error("SYSTEM_MESSAGES required fields missing");
    }

    return f;
}

TextFieldIndexes require_text_fields(const xbase::DbArea& area)
{
    TextFieldIndexes f;
    f.msgid = field_index_ci(area, "MSGID");
    f.symbol = field_index_ci(area, "SYMBOL");
    f.enumname = field_index_ci(area, "ENUMNAME");
    f.locale = field_index_ci(area, "LOCALE");
    f.msglocale = field_index_ci(area, "MSGLOCALE");
    f.symbolloc = field_index_ci(area, "SYMBOLLOC");
    f.text = field_index_ci(area, "TEXT");
    f.txthash = field_index_ci(area, "TXTHASH");
    f.status = field_index_ci(area, "STATUS");
    f.src = field_index_ci(area, "SRC");

    if (!f.msgid || !f.symbol || !f.enumname || !f.locale || !f.msglocale ||
        !f.symbolloc || !f.text || !f.txthash || !f.status || !f.src) {
        throw std::runtime_error("SYSTEM_MESSAGE_TEXT required fields missing");
    }

    return f;
}

void open_writable_area(xbase::DbArea& area, const fs::path& path)
{
    area.open(path.string());

    std::string memo_err;
    if (!cli_memo::memo_auto_on_use(area, path.string(), has_memo_fields(area), memo_err)) {
        throw std::runtime_error(memo_err.empty() ? "memo attach failed" : memo_err);
    }
}

ActiveMessageRow read_message_row(xbase::DbArea& area, const MessageFieldIndexes& f)
{
    return ActiveMessageRow{
        field_value(area, f.msgid),
        field_value(area, f.symbol),
        field_value(area, f.enumname),
        field_value(area, f.facility),
        field_value(area, f.owner),
        field_value(area, f.category),
        field_value(area, f.severity),
        field_value(area, f.status),
        field_value(area, f.src),
    };
}

ActiveTextRow read_text_row(xbase::DbArea& area, const TextFieldIndexes& f)
{
    return ActiveTextRow{
        field_value(area, f.msgid),
        field_value(area, f.symbol),
        field_value(area, f.enumname),
        field_value(area, f.locale),
        field_value(area, f.msglocale),
        field_value(area, f.symbolloc),
        field_value(area, f.text),
        field_value(area, f.txthash),
        field_value(area, f.status),
        field_value(area, f.src),
    };
}

bool equals_seed(const ActiveMessageRow& row, const SeedMessageRow& seed)
{
    return row.msgid == seed.msgid &&
           row.symbol == seed.symbol &&
           row.enumname == seed.enumname &&
           row.facility == seed.facility &&
           row.owner == seed.owner &&
           row.category == seed.category &&
           row.severity == seed.severity &&
           row.status == seed.status &&
           row.src == seed.src;
}

bool equals_seed(const ActiveTextRow& row, const SeedTextRow& seed)
{
    return row.msgid == seed.msgid &&
           row.symbol == seed.symbol &&
           row.enumname == seed.enumname &&
           row.locale == seed.locale &&
           row.msglocale == seed.msglocale &&
           row.symbolloc == seed.symbolloc &&
           row.text == seed.text &&
           row.txthash == seed.txthash &&
           row.status == seed.status &&
           row.src == seed.src;
}

MatchResult find_message_match(xbase::DbArea& area,
                               const MessageFieldIndexes& f,
                               const std::string& symbol)
{
    MatchResult result;
    const std::string wanted = upper_copy(trim_copy(symbol));
    const std::uint64_t count = area.recCount64();

    for (std::uint64_t rec = 1; rec <= count; ++rec) {
        if (!area.gotoRec(static_cast<std::int32_t>(rec)) || !area.readCurrent()) {
            continue;
        }
        if (area.isDeleted()) {
            continue;
        }

        if (upper_copy(field_value(area, f.symbol)) == wanted) {
            ++result.matches;
            if (result.first_recno == 0) {
                result.first_recno = static_cast<int>(rec);
            }
        }
    }

    return result;
}

MatchResult find_text_match(xbase::DbArea& area,
                            const TextFieldIndexes& f,
                            const std::string& symbol,
                            const std::string& locale)
{
    MatchResult result;
    const std::string wanted_symbol = upper_copy(trim_copy(symbol));
    const std::string wanted_locale = upper_copy(trim_copy(locale));
    const std::uint64_t count = area.recCount64();

    for (std::uint64_t rec = 1; rec <= count; ++rec) {
        if (!area.gotoRec(static_cast<std::int32_t>(rec)) || !area.readCurrent()) {
            continue;
        }
        if (area.isDeleted()) {
            continue;
        }

        if (upper_copy(field_value(area, f.symbol)) == wanted_symbol &&
            upper_copy(field_value(area, f.locale)) == wanted_locale) {
            ++result.matches;
            if (result.first_recno == 0) {
                result.first_recno = static_cast<int>(rec);
            }
        }
    }

    return result;
}

bool set_field_or_throw(xbase::DbArea& area, int field1, const std::string& value)
{
    if (field1 <= 0) {
        return true;
    }
    if (!area.set(field1, value)) {
        return false;
    }
    return true;
}

void write_message_seed_row(xbase::DbArea& area,
                            const MessageFieldIndexes& f,
                            const SeedMessageRow& seed)
{
    if (!set_field_or_throw(area, f.msgid, seed.msgid) ||
        !set_field_or_throw(area, f.symbol, seed.symbol) ||
        !set_field_or_throw(area, f.enumname, seed.enumname) ||
        !set_field_or_throw(area, f.facility, seed.facility) ||
        !set_field_or_throw(area, f.owner, seed.owner) ||
        !set_field_or_throw(area, f.category, seed.category) ||
        !set_field_or_throw(area, f.severity, seed.severity) ||
        !set_field_or_throw(area, f.status, seed.status) ||
        !set_field_or_throw(area, f.src, seed.src) ||
        !area.writeCurrent()) {
        throw std::runtime_error("SYSTEM_MESSAGES row write failed");
    }
}

void write_text_seed_row(xbase::DbArea& area,
                         const TextFieldIndexes& f,
                         const SeedTextRow& seed)
{
    std::string memo_err;
    if (!set_field_or_throw(area, f.msgid, seed.msgid) ||
        !set_field_or_throw(area, f.symbol, seed.symbol) ||
        !set_field_or_throw(area, f.enumname, seed.enumname) ||
        !set_field_or_throw(area, f.locale, seed.locale) ||
        !set_field_or_throw(area, f.msglocale, seed.msglocale) ||
        !set_field_or_throw(area, f.symbolloc, seed.symbolloc) ||
        !dottalk::cli::memo_field_store::store_user_value(area, f.text, seed.text, memo_err) ||
        !set_field_or_throw(area, f.txthash, seed.txthash) ||
        !set_field_or_throw(area, f.status, seed.status) ||
        !set_field_or_throw(area, f.src, seed.src) ||
        !area.writeCurrent()) {
        const std::string detail = memo_err.empty()
            ? "SYSTEM_MESSAGE_TEXT row write failed"
            : ("SYSTEM_MESSAGE_TEXT row write failed: " + memo_err);
        throw std::runtime_error(detail);
    }
}

void pack_recno_le8(std::uint64_t recno, unsigned char out[8])
{
    out[0] = static_cast<unsigned char>(recno & 0xFF);
    out[1] = static_cast<unsigned char>((recno >> 8) & 0xFF);
    out[2] = static_cast<unsigned char>((recno >> 16) & 0xFF);
    out[3] = static_cast<unsigned char>((recno >> 24) & 0xFF);
    out[4] = static_cast<unsigned char>((recno >> 32) & 0xFF);
    out[5] = static_cast<unsigned char>((recno >> 40) & 0xFF);
    out[6] = static_cast<unsigned char>((recno >> 48) & 0xFF);
    out[7] = static_cast<unsigned char>((recno >> 56) & 0xFF);
}

bool build_tag_lmdb_from_field(xbase::DbArea& area,
                               MDB_env* env,
                               const std::string& tag_name_uc,
                               std::vector<std::string>& errors)
{
    if (!area.isOpen()) {
        errors.push_back("LMDB rebuild: area not open for tag " + tag_name_uc);
        return false;
    }

    int field1 = -1;
    const auto& defs = area.fields();
    for (int i = 0; i < static_cast<int>(defs.size()); ++i) {
        if (upper_copy(defs[static_cast<std::size_t>(i)].name) == tag_name_uc) {
            field1 = i + 1;
            break;
        }
    }

    if (field1 < 1) {
        errors.push_back("LMDB rebuild: missing field for tag " + tag_name_uc);
        return false;
    }

    const auto& def = defs[static_cast<std::size_t>(field1 - 1)];
    const int keylen = static_cast<int>(def.length);

    MDB_txn* txn = nullptr;
    int rc = mdb_txn_begin(env, nullptr, 0, &txn);
    if (rc != MDB_SUCCESS || !txn) {
        errors.push_back("LMDB rebuild: mdb_txn_begin failed for tag " + tag_name_uc);
        return false;
    }

    MDB_dbi dbi = 0;
    rc = mdb_dbi_open(txn, tag_name_uc.c_str(), MDB_CREATE, &dbi);
    if (rc != MDB_SUCCESS) {
        errors.push_back("LMDB rebuild: mdb_dbi_open failed for tag " + tag_name_uc);
        mdb_txn_abort(txn);
        return false;
    }

    rc = mdb_drop(txn, dbi, 0);
    if (rc != MDB_SUCCESS) {
        errors.push_back("LMDB rebuild: mdb_drop failed for tag " + tag_name_uc);
        mdb_txn_abort(txn);
        return false;
    }

    std::string key_text;
    key_text.reserve(static_cast<std::size_t>(keylen));
    std::string keybuf(static_cast<std::size_t>(keylen) + 8, '\0');
    unsigned char recbuf[8]{};
    const std::uint64_t total = area.recCount64();

    for (std::uint64_t rn = 1; rn <= total; ++rn) {
        if (!area.gotoRec(static_cast<std::int32_t>(rn)) || !area.readCurrent()) {
            continue;
        }
        if (area.isDeleted()) {
            continue;
        }

        key_text = area.get(field1);
        if (def.type == 'C' || def.type == 'c') {
            key_text = trim_copy(key_text);
            key_text = upper_copy(key_text);
        }

        if (static_cast<int>(key_text.size()) > keylen) {
            key_text.resize(static_cast<std::size_t>(keylen));
        }
        if (static_cast<int>(key_text.size()) < keylen) {
            key_text.append(static_cast<std::size_t>(keylen - static_cast<int>(key_text.size())), ' ');
        }

        std::memcpy(keybuf.data(), key_text.data(), static_cast<std::size_t>(keylen));
        pack_recno_le8(rn, recbuf);
        std::memcpy(keybuf.data() + keylen, recbuf, 8);

        MDB_val mkey{keybuf.size(), keybuf.data()};
        MDB_val mval{8, recbuf};
        rc = mdb_put(txn, dbi, &mkey, &mval, 0);
        if (rc != MDB_SUCCESS) {
            errors.push_back("LMDB rebuild: mdb_put failed for tag " + tag_name_uc);
            mdb_txn_abort(txn);
            return false;
        }
    }

    rc = mdb_txn_commit(txn);
    if (rc != MDB_SUCCESS) {
        errors.push_back("LMDB rebuild: txn_commit failed for tag " + tag_name_uc);
        return false;
    }

    return true;
}

bool rebuild_lmdb_env_for_cdx(xbase::DbArea& area,
                              const fs::path& cdx_container,
                              std::vector<std::string>& errors)
{
    const fs::path envdir = dottalk::paths::resolve_lmdb_env_for_cdx(cdx_container);

    std::error_code ec;
    fs::remove_all(envdir, ec);
    if (ec) {
        errors.push_back("LMDB rebuild: could not clear envdir " + envdir.string() + ": " + ec.message());
        return false;
    }

    fs::create_directories(envdir, ec);
    if (ec) {
        errors.push_back("LMDB rebuild: could not create envdir " + envdir.string() + ": " + ec.message());
        return false;
    }

    std::vector<cdxfile::TagInfo> tags;
    cdxfile::CDXHandle* handle = nullptr;
    if (!cdxfile::open(cdx_container.string(), handle)) {
        errors.push_back("LMDB rebuild: could not open CDX container " + cdx_container.string());
        return false;
    }
    const bool read_ok = cdxfile::read_tagdir(handle, tags);
    cdxfile::close(handle);
    if (!read_ok || tags.empty()) {
        errors.push_back("LMDB rebuild: tag directory unavailable for " + cdx_container.string());
        return false;
    }

    MDB_env* env = nullptr;
    int rc = mdb_env_create(&env);
    if (rc != MDB_SUCCESS || !env) {
        errors.push_back("LMDB rebuild: mdb_env_create failed for " + envdir.string());
        return false;
    }

    rc = mdb_env_set_maxdbs(env, 1024);
    if (rc == MDB_SUCCESS) {
        rc = mdb_env_set_mapsize(env, MESSAGE_LMDB_MAPSIZE);
    }
    if (rc == MDB_SUCCESS) {
        rc = mdb_env_open(env, envdir.string().c_str(), 0, 0664);
    }
    if (rc != MDB_SUCCESS) {
        errors.push_back("LMDB rebuild: env open failed for " + envdir.string());
        mdb_env_close(env);
        return false;
    }

    bool ok = true;
    for (const auto& tag : tags) {
        const std::string tag_uc = upper_copy(trim_copy(tag.name));
        if (tag_uc.empty()) {
            continue;
        }
        if (!build_tag_lmdb_from_field(area, env, tag_uc, errors)) {
            ok = false;
            break;
        }
    }

    mdb_env_close(env);
    return ok;
}

dottalk::memo::MemoStore* memo_store_for_area(xbase::DbArea& area) noexcept
{
    auto* backend = cli_memo::memo_backend_for(area);
    if (!backend) return nullptr;
    return dynamic_cast<dottalk::memo::MemoStore*>(backend);
}

std::string field_value(xbase::DbArea& area, int field1)
{
    if (field1 <= 0) return {};
    const std::string raw = trim_copy(area.get(field1));

    if (!is_x64_memo_field(area, field1)) {
        return raw;
    }

    const std::uint64_t object_id = parse_u64_or_zero(raw);
    if (object_id == 0) {
        return {};
    }

    auto* store = memo_store_for_area(area);
    if (!store) {
        return raw;
    }

    std::string text;
    if (!store->get_text_id(object_id, text, nullptr)) {
        return raw;
    }
    return text;
}

void open_readonly_area(xbase::DbArea& area, const fs::path& path)
{
    area.open(path.string());

    std::string memo_err;
    if (!cli_memo::memo_auto_on_use(area, path.string(), has_memo_fields(area), memo_err)) {
        throw std::runtime_error(memo_err.empty() ? "memo attach failed" : memo_err);
    }
}

std::vector<ActiveMessageRow> load_messages(const fs::path& dbf_dir)
{
    xbase::DbArea area;
    open_readonly_area(area, dbf_dir / "SYSTEM_MESSAGES.dbf");

    const int f_msgid = field_index_ci(area, "MSGID");
    const int f_symbol = field_index_ci(area, "SYMBOL");
    const int f_enumname = field_index_ci(area, "ENUMNAME");
    const int f_facility = field_index_ci(area, "FACILITY");
    const int f_owner = field_index_ci(area, "OWNER");
    const int f_category = field_index_ci(area, "CATEGORY");
    const int f_severity = field_index_ci(area, "SEVERITY");
    const int f_status = field_index_ci(area, "STATUS");
    const int f_src = field_index_ci(area, "SRC");

    if (!f_msgid || !f_symbol || !f_enumname) {
        throw std::runtime_error("SYSTEM_MESSAGES required fields missing");
    }

    std::vector<ActiveMessageRow> rows;
    const std::uint64_t count = area.recCount64();
    rows.reserve(static_cast<std::size_t>(count));

    for (std::uint64_t rec = 1; rec <= count; ++rec) {
        if (!area.gotoRec(static_cast<int32_t>(rec)) || !area.readCurrent()) {
            continue;
        }
        if (area.isDeleted()) {
            continue;
        }

        rows.push_back(ActiveMessageRow{
            field_value(area, f_msgid),
            field_value(area, f_symbol),
            field_value(area, f_enumname),
            field_value(area, f_facility),
            field_value(area, f_owner),
            field_value(area, f_category),
            field_value(area, f_severity),
            field_value(area, f_status),
            field_value(area, f_src),
        });
    }

    cli_memo::memo_auto_on_close(area);
    area.close();
    return rows;
}

std::vector<ActiveTextRow> load_texts(const fs::path& dbf_dir)
{
    xbase::DbArea area;
    open_readonly_area(area, dbf_dir / "SYSTEM_MESSAGE_TEXT.dbf");

    const int f_msgid = field_index_ci(area, "MSGID");
    const int f_symbol = field_index_ci(area, "SYMBOL");
    const int f_enumname = field_index_ci(area, "ENUMNAME");
    const int f_locale = field_index_ci(area, "LOCALE");
    const int f_msglocale = field_index_ci(area, "MSGLOCALE");
    const int f_symbolloc = field_index_ci(area, "SYMBOLLOC");
    const int f_text = field_index_ci(area, "TEXT");
    const int f_txthash = field_index_ci(area, "TXTHASH");
    const int f_status = field_index_ci(area, "STATUS");
    const int f_src = field_index_ci(area, "SRC");

    if (!f_msgid || !f_symbol || !f_locale || !f_text) {
        throw std::runtime_error("SYSTEM_MESSAGE_TEXT required fields missing");
    }

    std::vector<ActiveTextRow> rows;
    const std::uint64_t count = area.recCount64();
    rows.reserve(static_cast<std::size_t>(count));

    for (std::uint64_t rec = 1; rec <= count; ++rec) {
        if (!area.gotoRec(static_cast<int32_t>(rec)) || !area.readCurrent()) {
            continue;
        }
        if (area.isDeleted()) {
            continue;
        }

        rows.push_back(ActiveTextRow{
            field_value(area, f_msgid),
            field_value(area, f_symbol),
            field_value(area, f_enumname),
            field_value(area, f_locale),
            field_value(area, f_msglocale),
            field_value(area, f_symbolloc),
            field_value(area, f_text),
            field_value(area, f_txthash),
            field_value(area, f_status),
            field_value(area, f_src),
        });
    }

    cli_memo::memo_auto_on_close(area);
    area.close();
    return rows;
}

ActiveCatalogLoad load_active_catalog()
{
    ActiveCatalogLoad load;
    load.paths = find_active_catalog_paths();

    if (!load.paths.present) {
        load.detail = "active Messaging DBF artifacts not found; compiled fallback active";
        return load;
    }

    try {
        load.messages = load_messages(load.paths.dbf_dir);
        load.texts = load_texts(load.paths.dbf_dir);

        for (const auto& row : load.texts) {
            if (!row.symbol.empty() && !row.locale.empty()) {
                load.text_by_symbol_locale[text_key(row.symbol, row.locale)] = row.text;
            }
        }

        load.loaded = true;
        load.detail = "active Messaging DBF rows loaded; compiled fallback available";
        return load;
    }
    catch (const std::exception& ex) {
        load.loaded = false;
        load.detail = std::string("active Messaging DBF row load failed; compiled fallback active: ") + ex.what();
        return load;
    }
}

std::string apply_vars(std::string out,
                       const std::unordered_map<std::string, std::string>& vars)
{
    for (const auto& kv : vars) {
        const std::string needle = "{" + kv.first + "}";
        std::string::size_type pos = 0;
        while ((pos = out.find(needle, pos)) != std::string::npos) {
            out.replace(pos, needle.size(), kv.second);
            pos += kv.second.size();
        }
    }
    return out;
}

const char* fallback_locale()
{
    return "en-US";
}

MessageCatalogSeedReport build_seed_report_base(bool check_only,
                                                const std::vector<SeedMessageRow>& message_rows,
                                                const std::vector<SeedTextRow>& text_rows)
{
    MessageCatalogSeedReport report;
    report.check_only = check_only;
    report.expected_message_rows = static_cast<int>(message_rows.size());
    report.expected_text_rows = static_cast<int>(text_rows.size());

    const auto active = load_active_catalog();
    report.active_catalog_present = active.paths.present;
    report.active_catalog_loaded = active.loaded;
    report.active_dbf_dir = generic_string(active.paths.dbf_dir);
    report.active_indexes_dir = generic_string(active.paths.indexes_dir);
    report.active_lmdb_dir = generic_string(active.paths.lmdb_dir);
    report.detail = active.detail;
    return report;
}

void inspect_seed_message_rows(xbase::DbArea& area,
                               const MessageFieldIndexes& fields,
                               const std::vector<SeedMessageRow>& seeds,
                               MessageCatalogSeedReport& report)
{
    for (const auto& seed : seeds) {
        const auto match = find_message_match(area, fields, seed.symbol);
        if (match.matches > 1) {
            report.errors.push_back(
                "Duplicate " + describe_messages_match(seed.symbol));
            continue;
        }
        if (match.matches == 0) {
            continue;
        }

        if (!area.gotoRec(match.first_recno) || !area.readCurrent()) {
            report.errors.push_back(
                "Read failed for " + describe_messages_match(seed.symbol));
            continue;
        }

        ++report.present_message_rows;
        const auto current = read_message_row(area, fields);
        if (equals_seed(current, seed)) {
            ++report.message_rows_unchanged;
        } else {
            ++report.message_rows_updated;
        }
    }
}

void inspect_seed_text_rows(xbase::DbArea& area,
                            const TextFieldIndexes& fields,
                            const std::vector<SeedTextRow>& seeds,
                            MessageCatalogSeedReport& report)
{
    for (const auto& seed : seeds) {
        const auto match = find_text_match(area, fields, seed.symbol, seed.locale);
        if (match.matches > 1) {
            report.errors.push_back(
                "Duplicate " + describe_text_match(seed.symbol, seed.locale));
            continue;
        }
        if (match.matches == 0) {
            continue;
        }

        if (!area.gotoRec(match.first_recno) || !area.readCurrent()) {
            report.errors.push_back(
                "Read failed for " + describe_text_match(seed.symbol, seed.locale));
            continue;
        }

        ++report.present_text_rows;
        const auto current = read_text_row(area, fields);
        if (equals_seed(current, seed)) {
            ++report.text_rows_unchanged;
        } else {
            ++report.text_rows_updated;
        }
    }
}

bool apply_seed_message_rows(xbase::DbArea& area,
                             const MessageFieldIndexes& fields,
                             const std::vector<SeedMessageRow>& seeds,
                             MessageCatalogSeedReport& report)
{
    for (const auto& seed : seeds) {
        const auto match = find_message_match(area, fields, seed.symbol);
        if (match.matches > 1) {
            report.errors.push_back(
                "Duplicate " + describe_messages_match(seed.symbol));
            return false;
        }

        if (match.matches == 0) {
            if (!area.appendBlank() || !area.readCurrent()) {
                report.errors.push_back(
                    "Append failed for " + describe_messages_match(seed.symbol));
                return false;
            }

            try {
                write_message_seed_row(area, fields, seed);
            } catch (const std::exception& ex) {
                report.errors.push_back(ex.what());
                return false;
            }
            ++report.message_rows_inserted;
            ++report.present_message_rows;
            continue;
        }

        if (!area.gotoRec(match.first_recno) || !area.readCurrent()) {
            report.errors.push_back(
                "Read failed for " + describe_messages_match(seed.symbol));
            return false;
        }

        const auto current = read_message_row(area, fields);
        if (equals_seed(current, seed)) {
            ++report.message_rows_unchanged;
            ++report.present_message_rows;
            continue;
        }

        try {
            write_message_seed_row(area, fields, seed);
        } catch (const std::exception& ex) {
            report.errors.push_back(ex.what());
            return false;
        }
        ++report.message_rows_updated;
        ++report.present_message_rows;
    }

    return true;
}

bool apply_seed_text_rows(xbase::DbArea& area,
                          const TextFieldIndexes& fields,
                          const std::vector<SeedTextRow>& seeds,
                          MessageCatalogSeedReport& report)
{
    for (const auto& seed : seeds) {
        const auto match = find_text_match(area, fields, seed.symbol, seed.locale);
        if (match.matches > 1) {
            report.errors.push_back(
                "Duplicate " + describe_text_match(seed.symbol, seed.locale));
            return false;
        }

        if (match.matches == 0) {
            if (!area.appendBlank() || !area.readCurrent()) {
                report.errors.push_back(
                    "Append failed for " + describe_text_match(seed.symbol, seed.locale));
                return false;
            }

            try {
                write_text_seed_row(area, fields, seed);
            } catch (const std::exception& ex) {
                report.errors.push_back(ex.what());
                return false;
            }
            ++report.text_rows_inserted;
            ++report.present_text_rows;
            continue;
        }

        if (!area.gotoRec(match.first_recno) || !area.readCurrent()) {
            report.errors.push_back(
                "Read failed for " + describe_text_match(seed.symbol, seed.locale));
            return false;
        }

        const auto current = read_text_row(area, fields);
        if (equals_seed(current, seed)) {
            ++report.text_rows_unchanged;
            ++report.present_text_rows;
            continue;
        }

        try {
            write_text_seed_row(area, fields, seed);
        } catch (const std::exception& ex) {
            report.errors.push_back(ex.what());
            return false;
        }
        ++report.text_rows_updated;
        ++report.present_text_rows;
    }

    return true;
}

bool rebuild_seed_catalog_indexes(const ActiveCatalogPaths& paths,
                                  MessageCatalogSeedReport& report)
{
    xbase::DbArea message_area;
    AreaCloser close_messages{message_area};
    xbase::DbArea text_area;
    AreaCloser close_text{text_area};

    try {
        open_writable_area(message_area, paths.dbf_dir / "SYSTEM_MESSAGES.dbf");
        open_writable_area(text_area, paths.dbf_dir / "SYSTEM_MESSAGE_TEXT.dbf");
    } catch (const std::exception& ex) {
        report.errors.push_back(ex.what());
        return false;
    }

    const fs::path message_cdx = paths.indexes_dir / "SYSTEM_MESSAGES.cdx";
    const fs::path text_cdx = paths.indexes_dir / "SYSTEM_MESSAGE_TEXT.cdx";

    if (!rebuild_lmdb_env_for_cdx(message_area, message_cdx, report.errors)) {
        return false;
    }
    report.rebuilt_containers.push_back(message_cdx.string());

    if (!rebuild_lmdb_env_for_cdx(text_area, text_cdx, report.errors)) {
        return false;
    }
    report.rebuilt_containers.push_back(text_cdx.string());

    return true;
}

} // namespace

MessageCatalogStatus active_message_catalog_status()
{
    const auto active = load_active_catalog();

    MessageCatalogStatus status;
    status.mode = active.loaded ? MessageCatalogMode::ActiveDbf
                                : MessageCatalogMode::CompiledFallback;

    status.active_dbf_dir = generic_string(active.paths.dbf_dir);
    status.active_indexes_dir = generic_string(active.paths.indexes_dir);
    status.active_lmdb_dir = generic_string(active.paths.lmdb_dir);

    status.active_catalog_present = active.paths.present;
    status.active_catalog_loaded = active.loaded;
    status.message_count = active.loaded
        ? static_cast<int>(active.messages.size())
        : static_cast<int>(all_messages().size());
    status.text_row_count = active.loaded
        ? static_cast<int>(active.texts.size())
        : 0;
    status.detail = active.detail;
    return status;
}

MessageCatalogSeedReport check_priority_a_seed()
{
    auto report = build_seed_report_base(true, priority_a_message_rows(), priority_a_text_rows());
    if (!report.active_catalog_present) {
        report.detail = "active Messaging DBF artifacts not found";
        return report;
    }

    try {
        xbase::DbArea message_area;
        AreaCloser close_messages{message_area};
        open_writable_area(message_area, fs::path(report.active_dbf_dir) / "SYSTEM_MESSAGES.dbf");
        const auto message_fields = require_message_fields(message_area);
        report.message_rows_before = message_area.recCount();
        report.message_rows_after = report.message_rows_before;
        inspect_seed_message_rows(message_area, message_fields, priority_a_message_rows(), report);

        xbase::DbArea text_area;
        AreaCloser close_text{text_area};
        open_writable_area(text_area, fs::path(report.active_dbf_dir) / "SYSTEM_MESSAGE_TEXT.dbf");
        const auto text_fields = require_text_fields(text_area);
        report.text_rows_before = text_area.recCount();
        report.text_rows_after = report.text_rows_before;
        inspect_seed_text_rows(text_area, text_fields, priority_a_text_rows(), report);
    } catch (const std::exception& ex) {
        report.errors.push_back(ex.what());
    }

    report.seed_complete =
        report.present_message_rows == report.expected_message_rows &&
        report.present_text_rows == report.expected_text_rows &&
        report.message_rows_updated == 0 &&
        report.text_rows_updated == 0 &&
        report.errors.empty();
    report.success = report.errors.empty();
    report.detail = report.seed_complete
        ? "Priority A runtime messaging seed is complete."
        : "Priority A runtime messaging seed is incomplete.";
    return report;
}

MessageCatalogSeedReport apply_priority_a_seed()
{
    auto report = build_seed_report_base(false, priority_a_message_rows(), priority_a_text_rows());
    if (!report.active_catalog_present) {
        report.detail = "active Messaging DBF artifacts not found";
        return report;
    }

    ActiveCatalogPaths paths;
    paths.dbf_dir = fs::path(report.active_dbf_dir);
    paths.indexes_dir = fs::path(report.active_indexes_dir);
    paths.lmdb_dir = fs::path(report.active_lmdb_dir);
    paths.present = true;

    try {
        xbase::DbArea message_area;
        AreaCloser close_messages{message_area};
        open_writable_area(message_area, paths.dbf_dir / "SYSTEM_MESSAGES.dbf");
        const auto message_fields = require_message_fields(message_area);
        report.message_rows_before = message_area.recCount();

        std::string lock_err;
        TableLockGuard message_lock{&message_area, false};
        if (!xbase::locks::try_lock_table(message_area, &lock_err)) {
            report.errors.push_back("SYSTEM_MESSAGES lock failed: " + lock_err);
            return report;
        }
        message_lock.locked = true;

        if (!apply_seed_message_rows(message_area, message_fields, priority_a_message_rows(), report)) {
            return report;
        }
        report.message_rows_after = message_area.recCount();

        xbase::DbArea text_area;
        AreaCloser close_text{text_area};
        open_writable_area(text_area, paths.dbf_dir / "SYSTEM_MESSAGE_TEXT.dbf");
        const auto text_fields = require_text_fields(text_area);
        report.text_rows_before = text_area.recCount();

        TableLockGuard text_lock{&text_area, false};
        lock_err.clear();
        if (!xbase::locks::try_lock_table(text_area, &lock_err)) {
            report.errors.push_back("SYSTEM_MESSAGE_TEXT lock failed: " + lock_err);
            return report;
        }
        text_lock.locked = true;

        if (!apply_seed_text_rows(text_area, text_fields, priority_a_text_rows(), report)) {
            return report;
        }
        report.text_rows_after = text_area.recCount();
    } catch (const std::exception& ex) {
        report.errors.push_back(ex.what());
        return report;
    }

    if (!rebuild_seed_catalog_indexes(paths, report)) {
        report.detail = "Priority A rows applied but LMDB rebuild failed.";
        return report;
    }

    report.seed_complete =
        report.present_message_rows == report.expected_message_rows &&
        report.present_text_rows == report.expected_text_rows &&
        report.errors.empty();
    report.success = report.seed_complete && report.errors.empty();
    report.detail = report.success
        ? "Priority A runtime messaging seed applied and messaging LMDB backends rebuilt."
        : "Priority A runtime messaging seed apply completed with review items.";
    return report;
}

MessageCatalogSeedReport check_priority_b_seed()
{
    auto report = build_seed_report_base(true, priority_b_message_rows(), priority_b_text_rows());
    if (!report.active_catalog_present) {
        report.detail = "active Messaging DBF artifacts not found";
        return report;
    }

    try {
        xbase::DbArea message_area;
        AreaCloser close_messages{message_area};
        open_writable_area(message_area, fs::path(report.active_dbf_dir) / "SYSTEM_MESSAGES.dbf");
        const auto message_fields = require_message_fields(message_area);
        report.message_rows_before = message_area.recCount();
        report.message_rows_after = report.message_rows_before;
        inspect_seed_message_rows(message_area, message_fields, priority_b_message_rows(), report);

        xbase::DbArea text_area;
        AreaCloser close_text{text_area};
        open_writable_area(text_area, fs::path(report.active_dbf_dir) / "SYSTEM_MESSAGE_TEXT.dbf");
        const auto text_fields = require_text_fields(text_area);
        report.text_rows_before = text_area.recCount();
        report.text_rows_after = report.text_rows_before;
        inspect_seed_text_rows(text_area, text_fields, priority_b_text_rows(), report);
    } catch (const std::exception& ex) {
        report.errors.push_back(ex.what());
    }

    report.seed_complete =
        report.present_message_rows == report.expected_message_rows &&
        report.present_text_rows == report.expected_text_rows &&
        report.message_rows_updated == 0 &&
        report.text_rows_updated == 0 &&
        report.errors.empty();
    report.success = report.errors.empty();
    report.detail = report.seed_complete
        ? "Priority B runtime messaging seed is complete."
        : "Priority B runtime messaging seed is incomplete.";
    return report;
}

MessageCatalogSeedReport apply_priority_b_seed()
{
    auto report = build_seed_report_base(false, priority_b_message_rows(), priority_b_text_rows());
    if (!report.active_catalog_present) {
        report.detail = "active Messaging DBF artifacts not found";
        return report;
    }

    ActiveCatalogPaths paths;
    paths.dbf_dir = fs::path(report.active_dbf_dir);
    paths.indexes_dir = fs::path(report.active_indexes_dir);
    paths.lmdb_dir = fs::path(report.active_lmdb_dir);
    paths.present = true;

    try {
        xbase::DbArea message_area;
        AreaCloser close_messages{message_area};
        open_writable_area(message_area, paths.dbf_dir / "SYSTEM_MESSAGES.dbf");
        const auto message_fields = require_message_fields(message_area);
        report.message_rows_before = message_area.recCount();

        std::string lock_err;
        TableLockGuard message_lock{&message_area, false};
        if (!xbase::locks::try_lock_table(message_area, &lock_err)) {
            report.errors.push_back("SYSTEM_MESSAGES lock failed: " + lock_err);
            return report;
        }
        message_lock.locked = true;

        if (!apply_seed_message_rows(message_area, message_fields, priority_b_message_rows(), report)) {
            return report;
        }
        report.message_rows_after = message_area.recCount();

        xbase::DbArea text_area;
        AreaCloser close_text{text_area};
        open_writable_area(text_area, paths.dbf_dir / "SYSTEM_MESSAGE_TEXT.dbf");
        const auto text_fields = require_text_fields(text_area);
        report.text_rows_before = text_area.recCount();

        TableLockGuard text_lock{&text_area, false};
        lock_err.clear();
        if (!xbase::locks::try_lock_table(text_area, &lock_err)) {
            report.errors.push_back("SYSTEM_MESSAGE_TEXT lock failed: " + lock_err);
            return report;
        }
        text_lock.locked = true;

        if (!apply_seed_text_rows(text_area, text_fields, priority_b_text_rows(), report)) {
            return report;
        }
        report.text_rows_after = text_area.recCount();
    } catch (const std::exception& ex) {
        report.errors.push_back(ex.what());
        return report;
    }

    if (!rebuild_seed_catalog_indexes(paths, report)) {
        report.detail = "Priority B rows applied but LMDB rebuild failed.";
        return report;
    }

    report.seed_complete =
        report.present_message_rows == report.expected_message_rows &&
        report.present_text_rows == report.expected_text_rows &&
        report.errors.empty();
    report.success = report.seed_complete && report.errors.empty();
    report.detail = report.success
        ? "Priority B runtime messaging seed applied and messaging LMDB backends rebuilt."
        : "Priority B runtime messaging seed apply completed with review items.";
    return report;
}

MessageCatalogSeedReport check_priority_c_seed()
{
    auto report = build_seed_report_base(true, priority_c_message_rows(), priority_c_text_rows());
    if (!report.active_catalog_present) {
        report.detail = "active Messaging DBF artifacts not found";
        return report;
    }

    try {
        xbase::DbArea message_area;
        AreaCloser close_messages{message_area};
        open_writable_area(message_area, fs::path(report.active_dbf_dir) / "SYSTEM_MESSAGES.dbf");
        const auto message_fields = require_message_fields(message_area);
        report.message_rows_before = message_area.recCount();
        report.message_rows_after = report.message_rows_before;
        inspect_seed_message_rows(message_area, message_fields, priority_c_message_rows(), report);

        xbase::DbArea text_area;
        AreaCloser close_text{text_area};
        open_writable_area(text_area, fs::path(report.active_dbf_dir) / "SYSTEM_MESSAGE_TEXT.dbf");
        const auto text_fields = require_text_fields(text_area);
        report.text_rows_before = text_area.recCount();
        report.text_rows_after = report.text_rows_before;
        inspect_seed_text_rows(text_area, text_fields, priority_c_text_rows(), report);
    } catch (const std::exception& ex) {
        report.errors.push_back(ex.what());
    }

    report.seed_complete =
        report.present_message_rows == report.expected_message_rows &&
        report.present_text_rows == report.expected_text_rows &&
        report.message_rows_updated == 0 &&
        report.text_rows_updated == 0 &&
        report.errors.empty();
    report.success = report.errors.empty();
    report.detail = report.seed_complete
        ? "Priority C runtime messaging seed is complete."
        : "Priority C runtime messaging seed is incomplete.";
    return report;
}

MessageCatalogSeedReport apply_priority_c_seed()
{
    auto report = build_seed_report_base(false, priority_c_message_rows(), priority_c_text_rows());
    if (!report.active_catalog_present) {
        report.detail = "active Messaging DBF artifacts not found";
        return report;
    }

    ActiveCatalogPaths paths;
    paths.dbf_dir = fs::path(report.active_dbf_dir);
    paths.indexes_dir = fs::path(report.active_indexes_dir);
    paths.lmdb_dir = fs::path(report.active_lmdb_dir);
    paths.present = true;

    try {
        xbase::DbArea message_area;
        AreaCloser close_messages{message_area};
        open_writable_area(message_area, paths.dbf_dir / "SYSTEM_MESSAGES.dbf");
        const auto message_fields = require_message_fields(message_area);
        report.message_rows_before = message_area.recCount();

        std::string lock_err;
        TableLockGuard message_lock{&message_area, false};
        if (!xbase::locks::try_lock_table(message_area, &lock_err)) {
            report.errors.push_back("SYSTEM_MESSAGES lock failed: " + lock_err);
            return report;
        }
        message_lock.locked = true;

        if (!apply_seed_message_rows(message_area, message_fields, priority_c_message_rows(), report)) {
            return report;
        }
        report.message_rows_after = message_area.recCount();

        xbase::DbArea text_area;
        AreaCloser close_text{text_area};
        open_writable_area(text_area, paths.dbf_dir / "SYSTEM_MESSAGE_TEXT.dbf");
        const auto text_fields = require_text_fields(text_area);
        report.text_rows_before = text_area.recCount();

        TableLockGuard text_lock{&text_area, false};
        lock_err.clear();
        if (!xbase::locks::try_lock_table(text_area, &lock_err)) {
            report.errors.push_back("SYSTEM_MESSAGE_TEXT lock failed: " + lock_err);
            return report;
        }
        text_lock.locked = true;

        if (!apply_seed_text_rows(text_area, text_fields, priority_c_text_rows(), report)) {
            return report;
        }
        report.text_rows_after = text_area.recCount();
    } catch (const std::exception& ex) {
        report.errors.push_back(ex.what());
        return report;
    }

    if (!rebuild_seed_catalog_indexes(paths, report)) {
        report.detail = "Priority C rows applied but LMDB rebuild failed.";
        return report;
    }

    report.seed_complete =
        report.present_message_rows == report.expected_message_rows &&
        report.present_text_rows == report.expected_text_rows &&
        report.errors.empty();
    report.success = report.seed_complete && report.errors.empty();
    report.detail = report.success
        ? "Priority C runtime messaging seed applied and messaging LMDB backends rebuilt."
        : "Priority C runtime messaging seed apply completed with review items.";
    return report;
}

std::string format_message_catalog(const std::string& locale,
                                   const std::string& symbol,
                                   const std::unordered_map<std::string, std::string>& vars)
{
    const auto active = load_active_catalog();
    if (active.loaded) {
        const std::string wanted_locale = trim_copy(locale).empty()
            ? fallback_locale()
            : trim_copy(locale);

        auto it = active.text_by_symbol_locale.find(text_key(symbol, wanted_locale));
        if (it != active.text_by_symbol_locale.end()) {
            return apply_vars(it->second, vars);
        }

        it = active.text_by_symbol_locale.find(text_key(symbol, fallback_locale()));
        if (it != active.text_by_symbol_locale.end()) {
            return apply_vars(it->second, vars);
        }
    }

    const MessageDef* message = find_message_by_key(symbol);
    if (!message || !message->text) {
        return {};
    }
    return apply_vars(message->text, vars);
}


// MSG-022S1 BEGIN shared routing proof lane state
namespace {
bool& message_routing_proof_flag()
{
    static bool enabled = false;
    return enabled;
}
} // namespace

bool message_routing_proof_enabled()
{
    return message_routing_proof_flag();
}

void set_message_routing_proof_enabled(bool enabled)
{
    message_routing_proof_flag() = enabled;
}
// MSG-022S1 END shared routing proof lane state
} // namespace dottalk::helpdata
