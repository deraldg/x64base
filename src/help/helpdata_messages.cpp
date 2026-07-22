// ============================================================================
// File: src/help/helpdata_messages.cpp
// Purpose: Phase-two localized message resolver for DotTalk++.
// ============================================================================
#include "helpdata_messages.hpp"

#include <algorithm>
#include <cctype>
#include <map>
#include <set>
#include <sstream>

namespace dottalk::helpdata {

namespace {

std::string trim_copy(const std::string& s)
{
    std::string::size_type first = 0;
    while (first < s.size() && std::isspace(static_cast<unsigned char>(s[first]))) {
        ++first;
    }

    std::string::size_type last = s.size();
    while (last > first && std::isspace(static_cast<unsigned char>(s[last - 1]))) {
        --last;
    }

    return s.substr(first, last - first);
}

std::string lower_copy(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return s;
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

std::set<std::string> extract_placeholders(const std::string& text)
{
    std::set<std::string> out;
    std::string::size_type pos = 0;

    while ((pos = text.find('{', pos)) != std::string::npos) {
        const auto close = text.find('}', pos + 1);
        if (close == std::string::npos) {
            break;
        }

        const std::string name = text.substr(pos + 1, close - pos - 1);
        if (!name.empty()) {
            out.insert(name);
        }
        pos = close + 1;
    }

    return out;
}

std::string join_set(const std::set<std::string>& values)
{
    std::ostringstream oss;
    bool first = true;
    for (const auto& value : values) {
        if (!first) {
            oss << ",";
        }
        first = false;
        oss << value;
    }
    return oss.str();
}

void add_issue(std::vector<MessageCatalogIssue>& issues,
               std::string code,
               std::string key,
               std::string locale,
               std::string detail)
{
    issues.push_back(MessageCatalogIssue{
        std::move(code),
        std::move(key),
        std::move(locale),
        std::move(detail)
    });
}

} // anonymous namespace

const char* default_locale()
{
    return "en-US";
}

const std::vector<MessageDef>& all_messages()
{
    static const std::vector<MessageDef> messages = {
        {
            MessageId::HelpHintCommand,
            "HELP_HINT_COMMAND",
            "GLOBAL",
            "HINT",
            "INFO",
            "Type HELP {command} for more information."
        },
        {
            MessageId::MessageRoutingProofLine,
            "MESSAGE_ROUTING_PROOF_LINE",
            "SUBSYSTEM:MESSAGING",
            "STATUS",
            "INFO",
            "Message routing proof: {provider} {symbol}"
        },
        {
            MessageId::MessageLocaleSet,
            "MESSAGE_LOCALE_SET",
            "SUBSYSTEM:MESSAGING",
            "STATUS",
            "INFO",
            "Message locale is {locale}"
        },
        {
            MessageId::SetMessageCatalogValidationGreenLabel,
            "SET_MESSAGE_CATALOG_VALIDATION_GREEN_LABEL",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "green"
        },
        {
            MessageId::SetMessageCatalogValidationIssuesFoundLabel,
            "SET_MESSAGE_CATALOG_VALIDATION_ISSUES_FOUND_LABEL",
            "COMMAND:SET",
            "STATUS",
            "WARNING",
            "issues found"
        },
        {
            MessageId::SetMessageCatalogValidationStatusText,
            "SET_MESSAGE_CATALOG_VALIDATION_STATUS_TEXT",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "Message catalog validation: {status}\n  messages: {message_count}\n  text rows: {text_row_count}\n  locales: {locales}\n  issues: {issue_count}\n  boundary: report-only; no DBF, HELP DATA, CMDHELPCHK, source-mining, or catalog mutation."
        },
        {
            MessageId::SetLanguageStatusText,
            "SET_LANGUAGE_STATUS_TEXT",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "Message locale: {locale}\nSupported message locales: en-US, es, fr, de, it\nUsage: SET LANGUAGE [TO] <en-US|es|fr|de|it|DEFAULT>\n       SET LOCALE   [TO] <en-US|es|fr|de|it|DEFAULT>\n       SET LANGUAGE CHECK\n       SET LOCALE CHECK\n       SET LANGUAGE REPORT [locale]\n       SET LOCALE REPORT [locale]"
        },
        {
            MessageId::SetMessageCatalogProviderStatusText,
            "SET_MESSAGE_CATALOG_PROVIDER_STATUS_TEXT",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "Message catalog provider status:\n  mode: {mode}\n  active catalog present: {present}\n  active catalog loaded: {loaded}\n  message count: {message_count}\n  text row count: {text_row_count}\n  active dbf dir: {dbf_dir}\n  active indexes dir: {indexes_dir}\n  active lmdb dir: {lmdb_dir}\n  detail: {detail}\n  boundary: read-only status/load; no DBF/CDX/LMDB mutation; no runtime writeback"
        },
        {
            MessageId::SetLanguageActiveMessageEmissionText,
            "SET_LANGUAGE_ACTIVE_MESSAGE_EMISSION_TEXT",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "SET LANGUAGE active message emission:\n  current locale: {locale}\n  provider mode: {mode}\n  active catalog loaded: {loaded}\n  symbol: HELP_HINT_COMMAND\n  fallback locale: en-US\n  text: {text}\n  boundary: read-only emission; no DBF/CDX/LMDB mutation; no runtime writeback"
        },
        {
            MessageId::SetLanguageActiveCatalogCheckText,
            "SET_LANGUAGE_ACTIVE_CATALOG_CHECK_TEXT",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "SET LANGUAGE active catalog check:\n  current language: {locale}\n  message catalog mode: {mode}\n  active catalog present: {present}\n  active catalog loaded: {loaded}\n  message count: {message_count}\n  text row count: {text_row_count}\n  lookup symbol: MESSAGE_LOCALE_SET\n  lookup locale: {locale}\n  lookup text: {text}\n  runtime active catalog lookup proof: {proof}\n  boundary: read-only lookup; no DBF/CDX/LMDB mutation; no runtime writeback"
        },
        {
            MessageId::SetMessageProofUsageText,
            "SET_MESSAGE_PROOF_USAGE_TEXT",
            "COMMAND:SET",
            "USAGE",
            "INFO",
            "Usage:\n  SET MESSAGE PROOF ON\n  SET MESSAGE PROOF OFF\n  SET MESSAGE PROOF CHECK"
        },
        {
            MessageId::SetMessageEmitUsageText,
            "SET_MESSAGE_EMIT_USAGE_TEXT",
            "COMMAND:SET",
            "USAGE",
            "INFO",
            "Usage:\n  SET MESSAGE CATALOG CHECK\n  SET MESSAGE PROOF ON|OFF|CHECK\n  SET MESSAGE EMIT <symbol> [LOCALE <locale>] [ARG <name> <value>]"
        },
        {
            MessageId::SetMessageEmitStatusText,
            "SET_MESSAGE_EMIT_STATUS_TEXT",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "SET MESSAGE EMIT:\n  current locale: {current_locale}\n  provider mode: {mode}\n  active catalog present: {present}\n  active catalog loaded: {loaded}\n  message count: {message_count}\n  text row count: {text_row_count}\n  symbol: {symbol}\n  locale: {locale}\n  placeholder arg supplied: {placeholder_arg}\n  placeholder substitution proof: {substituted}\n  text: {text}\n  runtime controlled emission proof: {proof}\n  boundary: explicit diagnostic emission; no DBF/CDX/LMDB mutation; no runtime writeback"
        },
        {
            MessageId::SetMessageCatalogReportHeaderText,
            "SET_MESSAGE_CATALOG_REPORT_HEADER_TEXT",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "Message catalog report: report-only\n  schema intent: SYSTEM_MESSAGES + SYSTEM_MESSAGE_TEXT\n  messages: {message_count}\n  text rows: {text_row_count}\n  locales: {locales}\n  validation issues: {issue_count}\n  boundary: report-only console report; no DBF, HELP DATA, CMDHELPCHK, source-mining, file, or catalog mutation."
        },
        {
            MessageId::SetMessageCatalogReportLocaleFilterLine,
            "SET_MESSAGE_CATALOG_REPORT_LOCALE_FILTER_LINE",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "  locale filter: {locale}"
        },
        {
            MessageId::SetMessageCatalogReportSystemMessagesTitle,
            "SET_MESSAGE_CATALOG_REPORT_SYSTEM_MESSAGES_TITLE",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "SYSTEM_MESSAGES preview:"
        },
        {
            MessageId::SetMessageCatalogReportMessageRow,
            "SET_MESSAGE_CATALOG_REPORT_MESSAGE_ROW",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "  {key} | owner={owner} | category={category} | severity={severity}"
        },
        {
            MessageId::SetMessageCatalogReportSystemMessageTextTitle,
            "SET_MESSAGE_CATALOG_REPORT_SYSTEM_MESSAGE_TEXT_TITLE",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "SYSTEM_MESSAGE_TEXT preview:"
        },
        {
            MessageId::SetMessageCatalogReportNoMatchingTextRows,
            "SET_MESSAGE_CATALOG_REPORT_NO_MATCHING_TEXT_ROWS",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "<no matching text rows>"
        },
        {
            MessageId::SetMessageCatalogReportTextRow,
            "SET_MESSAGE_CATALOG_REPORT_TEXT_ROW",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "  {key}:{value}"
        },
        {
            MessageId::SetMessageCatalogValidationIssueRowText,
            "SET_MESSAGE_CATALOG_VALIDATION_ISSUE_ROW_TEXT",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "  {code} key={key} locale={locale} detail={detail}"
        },
        {
            MessageId::SetUsageText,
            "SET_USAGE_TEXT",
            "COMMAND:SET",
            "USAGE",
            "INFO",
            "Usage:\n  SET\n  SET USAGE\n  SET <option> [args]\nPublic options:\n  SET TABLE BUFFER ON|OFF [ALL]\n  SET CONSOLE ON|OFF\n  SET PRINT ON|OFF\n  SET PRINT TO <file>\n  SET DEVICE TO SCREEN\n  SET DEVICE TO FILE <path>\n  SET DEVICE TO PRINTER\n  SET DEVICE TO NULL\n  SET ALTERNATE ON|OFF\n  SET ALTERNATE TO <file>\n  SET TALK ON|OFF\n  SET ECHO ON|OFF\n  SET PAGING ON|OFF\n  SET WRAP ON|OFF\n  SET DELETED ON|OFF\n  SET CASE ON|OFF\n  SET NEAR ON|OFF\n  SET EDITOR TO <value>\n  SET EDITOR TO DEFAULT\n  SET EDITOR TO OFF\n  SET LANGUAGE [TO] <en-US|es|fr|de|it|DEFAULT>\n  SET LOCALE [TO] <en-US|es|fr|de|it|DEFAULT>\n  SET LANGUAGE CHECK\n  SET LOCALE CHECK\n  SET LANGUAGE REPORT [locale]\n  SET LOCALE REPORT [locale]\n  SET PATH <slot> <path>\n  SET MESSAGE CATALOG CHECK\n  SET MESSAGE EMIT <symbol> [LOCALE <locale>]\n  SET UNIQUE FIELD <name> ON|OFF\n  SET TIMER ON|OFF\n  SET POLLING ON|OFF\n  SET INDEX TO <file>\n  SET ORDER TO <tag|0>\n\nDeveloper / transitional:\n  SET FILTER TO <expr>\n  SET RELATION <args...>\n  SET RELATIONS <args...>\n  SET CNX [TO] <container.cnx>\n  SET CDX [TO] <container.cdx>\n  SET LMDB <args...>"
        },
        {
            MessageId::SetTableBufferUsageText,
            "SET_TABLE_BUFFER_USAGE_TEXT",
            "COMMAND:SET TABLE BUFFER",
            "USAGE",
            "INFO",
            "Usage: SET TABLE BUFFER ON|OFF [ALL]"
        },
        {
            MessageId::SetTableBufferEngineUnavailableText,
            "SET_TABLE_BUFFER_ENGINE_UNAVAILABLE_TEXT",
            "COMMAND:SET TABLE BUFFER",
            "ERROR",
            "ERROR",
            "TABLE BUFFER: engine not available."
        },
        {
            MessageId::SetTableBufferAllStatusText,
            "SET_TABLE_BUFFER_ALL_STATUS_TEXT",
            "COMMAND:SET TABLE BUFFER",
            "STATUS",
            "INFO",
            "TABLE BUFFER: {state} for {count} open area(s)."
        },
        {
            MessageId::SetTableBufferCannotDetermineCurrentAreaText,
            "SET_TABLE_BUFFER_CANNOT_DETERMINE_CURRENT_AREA_TEXT",
            "COMMAND:SET TABLE BUFFER",
            "ERROR",
            "ERROR",
            "TABLE BUFFER: cannot determine current area."
        },
        {
            MessageId::SetTableBufferAreaStatusText,
            "SET_TABLE_BUFFER_AREA_STATUS_TEXT",
            "COMMAND:SET TABLE BUFFER",
            "STATUS",
            "INFO",
            "TABLE BUFFER: {state} (area {area})"
        },
        {
            MessageId::TableBufferUsageText,
            "TABLE_BUFFER_USAGE_TEXT",
            "COMMAND:TABLE BUFFER",
            "USAGE",
            "INFO",
            "Usage:\n  TABLE\n  TABLE ALL\n  TABLE STATUS [ALL]\n  TABLE BUFFER ON [PERSISTENT|RAM] [<n>|ALL|n,m,...]\n  TABLE BUFFER OFF [<n>|ALL|n,m,...]\n  TABLE BUFFER PERSISTENT [ON|OFF] [<n>|ALL|n,m,...]\n  TABLE BUFFER DIRTY [<n>|ALL|n,m,...]\n  TABLE BUFFER CLEAN [<n>|ALL|n,m,...]\n  TABLE BUFFER STALE [<n>|ALL|n,m,...]\n  TABLE BUFFER FRESH [<n>|ALL|n,m,...]\n  TABLE BUFFER STATUS [area|ALL]\n  TABLE BUFFER DUMP [area|ALL]\n  TABLE BUFFER TESTADD <recno> [flags] [field1] [value]\n  TABLE BUFFER RESET\nLegacy compatibility:\n  TABLE ON|OFF|DIRTY|CLEAN|STALE|FRESH [<n>|ALL|n,m,...]\n  TABLE ONALL|OFFALL|DIRTYALL|CLEANALL|STALEALL|FRESHALL"
        },
        {
            MessageId::TableBufferTestAddUsageText,
            "TABLE_BUFFER_TESTADD_USAGE_TEXT",
            "COMMAND:TABLE BUFFER",
            "USAGE",
            "INFO",
            "Usage: TABLE BUFFER TESTADD <recno> [flags] [field1] [value]"
        },
        {
            MessageId::TableBufferAreasAllTitleText,
            "TABLE_BUFFER_AREAS_ALL_TITLE_TEXT",
            "COMMAND:TABLE BUFFER",
            "STATUS",
            "INFO",
            "areas 0..{last}"
        },
        {
            MessageId::TableBufferOccupiedAreasTitleText,
            "TABLE_BUFFER_OCCUPIED_AREAS_TITLE_TEXT",
            "COMMAND:TABLE BUFFER",
            "STATUS",
            "INFO",
            "occupied areas only"
        },
        {
            MessageId::TableBufferAreasUpdatedText,
            "TABLE_BUFFER_AREAS_UPDATED_TEXT",
            "COMMAND:TABLE BUFFER",
            "STATUS",
            "INFO",
            "{count} area(s) updated."
        },
        {
            MessageId::TableBufferPersistenceUpdatedText,
            "TABLE_BUFFER_PERSISTENCE_UPDATED_TEXT",
            "COMMAND:TABLE BUFFER",
            "STATUS",
            "INFO",
            "{count} area(s) persistence updated."
        },
        {
            MessageId::TableBufferInvalidAreaText,
            "TABLE_BUFFER_INVALID_AREA_TEXT",
            "COMMAND:TABLE BUFFER",
            "ERROR",
            "ERROR",
            "invalid area."
        },
        {
            MessageId::TableBufferStatusHeaderText,
            "TABLE_BUFFER_STATUS_HEADER_TEXT",
            "COMMAND:TABLE BUFFER",
            "STATUS",
            "INFO",
            "Area {area} buffer:"
        },
        {
            MessageId::TableBufferDumpHeaderText,
            "TABLE_BUFFER_DUMP_HEADER_TEXT",
            "COMMAND:TABLE BUFFER",
            "STATUS",
            "INFO",
            "Area {area} buffer dump:"
        },
        {
            MessageId::TableBufferEmptyBufferText,
            "TABLE_BUFFER_EMPTY_BUFFER_TEXT",
            "COMMAND:TABLE BUFFER",
            "STATUS",
            "INFO",
            "Area {area} buffer: empty"
        },
        {
            MessageId::TableBufferNoCurrentEnabledAreaText,
            "TABLE_BUFFER_NO_CURRENT_ENABLED_AREA_TEXT",
            "COMMAND:TABLE BUFFER",
            "ERROR",
            "ERROR",
            "no current enabled area."
        },
        {
            MessageId::TableBufferNoCurrentAreaSelectedOrEnabledText,
            "TABLE_BUFFER_NO_CURRENT_AREA_SELECTED_OR_ENABLED_TEXT",
            "COMMAND:TABLE BUFFER",
            "ERROR",
            "ERROR",
            "no current area selected or not enabled."
        },
        {
            MessageId::TableBufferInvalidRecnoText,
            "TABLE_BUFFER_INVALID_RECNO_TEXT",
            "COMMAND:TABLE BUFFER",
            "ERROR",
            "ERROR",
            "invalid recno."
        },
        {
            MessageId::TableBufferCannotDetermineCurrentAreaSpecifyText,
            "TABLE_BUFFER_CANNOT_DETERMINE_CURRENT_AREA_SPECIFY_TEXT",
            "COMMAND:TABLE BUFFER",
            "ERROR",
            "ERROR",
            "cannot determine current area; specify an area number."
        },
        {
            MessageId::TableBufferResetAllText,
            "TABLE_BUFFER_RESET_ALL_TEXT",
            "COMMAND:TABLE BUFFER",
            "STATUS",
            "INFO",
            "reset all areas."
        },
        {
            MessageId::TableBufferUnknownSubcommandText,
            "TABLE_BUFFER_UNKNOWN_SUBCOMMAND_TEXT",
            "COMMAND:TABLE BUFFER",
            "ERROR",
            "ERROR",
            "unknown subcommand '{subcommand}'."
        },
        {
            MessageId::SetConsoleUsageText,
            "SET_CONSOLE_USAGE_TEXT",
            "COMMAND:SET CONSOLE",
            "USAGE",
            "INFO",
            "Usage: SET CONSOLE ON|OFF"
        },
        {
            MessageId::SetPrintUsageText,
            "SET_PRINT_USAGE_TEXT",
            "COMMAND:SET PRINT",
            "USAGE",
            "INFO",
            "Usage: SET PRINT ON|OFF | SET PRINT TO <file>"
        },
        {
            MessageId::SetPrintToUsageText,
            "SET_PRINT_TO_USAGE_TEXT",
            "COMMAND:SET PRINT",
            "USAGE",
            "INFO",
            "Usage: SET PRINT TO <file>"
        },
        {
            MessageId::SetPrintToFailedText,
            "SET_PRINT_TO_FAILED_TEXT",
            "COMMAND:SET PRINT",
            "ERROR",
            "ERROR",
            "PRINT TO failed: {path}"
        },
        {
            MessageId::SetPrintOnRequiresFileText,
            "SET_PRINT_ON_REQUIRES_FILE_TEXT",
            "COMMAND:SET PRINT",
            "ERROR",
            "ERROR",
            "SET PRINT ON requires a file. Use: SET PRINT TO <file>"
        },
        {
            MessageId::SetAlternateUsageText,
            "SET_ALTERNATE_USAGE_TEXT",
            "COMMAND:SET ALTERNATE",
            "USAGE",
            "INFO",
            "Usage: SET ALTERNATE ON|OFF | SET ALTERNATE TO <file>"
        },
        {
            MessageId::SetAlternateToUsageText,
            "SET_ALTERNATE_TO_USAGE_TEXT",
            "COMMAND:SET ALTERNATE",
            "USAGE",
            "INFO",
            "Usage: SET ALTERNATE TO <file>"
        },
        {
            MessageId::SetAlternateToFailedText,
            "SET_ALTERNATE_TO_FAILED_TEXT",
            "COMMAND:SET ALTERNATE",
            "ERROR",
            "ERROR",
            "ALTERNATE TO failed: {path}"
        },
        {
            MessageId::SetAlternateToStatusText,
            "SET_ALTERNATE_TO_STATUS_TEXT",
            "COMMAND:SET ALTERNATE",
            "STATUS",
            "INFO",
            "ALTERNATE TO: {path}"
        },
        {
            MessageId::SetAlternateStatusText,
            "SET_ALTERNATE_STATUS_TEXT",
            "COMMAND:SET ALTERNATE",
            "STATUS",
            "INFO",
            "Alternate is {state}"
        },
        {
            MessageId::SetTalkUsageText,
            "SET_TALK_USAGE_TEXT",
            "COMMAND:SET TALK",
            "USAGE",
            "INFO",
            "Usage: SET TALK ON|OFF"
        },
        {
            MessageId::SetTalkStatusText,
            "SET_TALK_STATUS_TEXT",
            "COMMAND:SET TALK",
            "STATUS",
            "INFO",
            "Talk is {state}"
        },
        {
            MessageId::SetEchoUsageText,
            "SET_ECHO_USAGE_TEXT",
            "COMMAND:SET ECHO",
            "USAGE",
            "INFO",
            "Usage: SET ECHO ON|OFF"
        },
        {
            MessageId::SetEchoStatusText,
            "SET_ECHO_STATUS_TEXT",
            "COMMAND:SET ECHO",
            "STATUS",
            "INFO",
            "Echo is {state}"
        },
        {
            MessageId::EchoUsageText,
            "ECHO_USAGE_TEXT",
            "COMMAND:ECHO",
            "USAGE",
            "INFO",
            "Usage:\n  ECHO\n  ECHO USAGE\n  ECHO <text>\nNotes:\n  - ECHO ON is not the toggle command; use SET ECHO ON or SET ECHO OFF."
        },
        {
            MessageId::SetPagingUsageText,
            "SET_PAGING_USAGE_TEXT",
            "COMMAND:SET PAGING",
            "USAGE",
            "INFO",
            "Usage: SET PAGING ON|OFF"
        },
        {
            MessageId::SetPagingStatusText,
            "SET_PAGING_STATUS_TEXT",
            "COMMAND:SET PAGING",
            "STATUS",
            "INFO",
            "Paging is {state}"
        },
        {
            MessageId::SetWrapUsageText,
            "SET_WRAP_USAGE_TEXT",
            "COMMAND:SET WRAP",
            "USAGE",
            "INFO",
            "Usage: SET WRAP ON|OFF"
        },
        {
            MessageId::SetWrapStatusText,
            "SET_WRAP_STATUS_TEXT",
            "COMMAND:SET WRAP",
            "STATUS",
            "INFO",
            "Wrap is {state}"
        },
        {
            MessageId::SetDevdiagUsageText,
            "SET_DEVDIAG_USAGE_TEXT",
            "COMMAND:SET DEVDIAG",
            "USAGE",
            "INFO",
            "Usage: SET DEVDIAG ON|OFF|STATUS"
        },
        {
            MessageId::SetDevdiagStatusText,
            "SET_DEVDIAG_STATUS_TEXT",
            "COMMAND:SET DEVDIAG",
            "STATUS",
            "INFO",
            "Passive dev diagnostics are {state}"
        },
        {
            MessageId::SetTimerUsageText,
            "SET_TIMER_USAGE_TEXT",
            "COMMAND:SET TIMER",
            "USAGE",
            "INFO",
            "Usage: SET TIMER ON|OFF"
        },
        {
            MessageId::SetTimerStatusText,
            "SET_TIMER_STATUS_TEXT",
            "COMMAND:SET TIMER",
            "STATUS",
            "INFO",
            "Timer is {state}"
        },
        {
            MessageId::SetPollingUsageText,
            "SET_POLLING_USAGE_TEXT",
            "COMMAND:SET POLLING",
            "USAGE",
            "INFO",
            "Usage: SET POLLING ON|OFF"
        },
        {
            MessageId::SetPollingStatusText,
            "SET_POLLING_STATUS_TEXT",
            "COMMAND:SET POLLING",
            "STATUS",
            "INFO",
            "Polling is {state}"
        },
        {
            MessageId::SetDeletedUsageText,
            "SET_DELETED_USAGE_TEXT",
            "COMMAND:SET DELETED",
            "USAGE",
            "INFO",
            "Usage: SET DELETED ON|OFF"
        },
        {
            MessageId::SetDeletedStatusText,
            "SET_DELETED_STATUS_TEXT",
            "COMMAND:SET DELETED",
            "STATUS",
            "INFO",
            "Deleted visibility: {state}"
        },
        {
            MessageId::SetEditorUsageText,
            "SET_EDITOR_USAGE_TEXT",
            "COMMAND:SET EDITOR",
            "USAGE",
            "INFO",
            "Usage: SET EDITOR TO <value|DEFAULT|OFF>"
        },
        {
            MessageId::SetEditorOffStatusText,
            "SET_EDITOR_OFF_STATUS_TEXT",
            "COMMAND:SET EDITOR",
            "STATUS",
            "INFO",
            "EDITOR is OFF"
        },
        {
            MessageId::SetEditorDefaultStatusText,
            "SET_EDITOR_DEFAULT_STATUS_TEXT",
            "COMMAND:SET EDITOR",
            "STATUS",
            "INFO",
            "EDITOR set to DEFAULT"
        },
        {
            MessageId::SetEditorCustomStatusText,
            "SET_EDITOR_CUSTOM_STATUS_TEXT",
            "COMMAND:SET EDITOR",
            "STATUS",
            "INFO",
            "EDITOR set to: {value}"
        },
        {
            MessageId::SetDeviceUsageText,
            "SET_DEVICE_USAGE_TEXT",
            "COMMAND:SET DEVICE",
            "USAGE",
            "INFO",
            "Usage: SET DEVICE TO SCREEN|FILE <path>|PRINTER [name]|NULL"
        },
        {
            MessageId::SetDeviceFileUsageText,
            "SET_DEVICE_FILE_USAGE_TEXT",
            "COMMAND:SET DEVICE",
            "USAGE",
            "INFO",
            "Usage: SET DEVICE TO FILE <path>"
        },
        {
            MessageId::SetDeviceFileFailedText,
            "SET_DEVICE_FILE_FAILED_TEXT",
            "COMMAND:SET DEVICE",
            "ERROR",
            "ERROR",
            "SET DEVICE TO FILE failed: {path}"
        },
        {
            MessageId::SetDevicePrinterFailedText,
            "SET_DEVICE_PRINTER_FAILED_TEXT",
            "COMMAND:SET DEVICE",
            "ERROR",
            "ERROR",
            "SET DEVICE TO PRINTER failed."
        },
        {
            MessageId::SetPrnConsoleNoteText,
            "SET_PRN_CONSOLE_NOTE_TEXT",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "PRN: CONSOLE"
        },
        {
            MessageId::SetPrnNullNoteText,
            "SET_PRN_NULL_NOTE_TEXT",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "PRN: NULL"
        },
        {
            MessageId::SetPrnFileNoteText,
            "SET_PRN_FILE_NOTE_TEXT",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "PRN: FILE -> {path}"
        },
        {
            MessageId::SetPrnPrinterDefaultStagedNoteText,
            "SET_PRN_PRINTER_DEFAULT_STAGED_NOTE_TEXT",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "PRN: PRINTER -> (system default) [staged only]"
        },
        {
            MessageId::SetPrnPrinterNamedStagedNoteText,
            "SET_PRN_PRINTER_NAMED_STAGED_NOTE_TEXT",
            "COMMAND:SET",
            "STATUS",
            "INFO",
            "PRN: PRINTER -> {name} [staged only]"
        },
        {
            MessageId::AreaUsageText,
            "AREA_USAGE_TEXT",
            "COMMAND:AREA",
            "USAGE",
            "INFO",
            "Usage:\n  AREA                   (Report current work-area state)\n  AREA USAGE             (Show this usage)\nNotes:\n  - AREA is read-only; it reports the current area slot/file/order state."
        },
        {
            MessageId::DisplayUsageText,
            "DISPLAY_USAGE_TEXT",
            "COMMAND:DISPLAY",
            "USAGE",
            "INFO",
            "Usage:\n  DISPLAY\n  DISPLAY USAGE\n  DISPLAY <recno>"
        },
        {
            MessageId::DisplayRecordHeaderText,
            "DISPLAY_RECORD_HEADER_TEXT",
            "COMMAND:DISPLAY",
            "STATUS",
            "INFO",
            "Record {recno}{deleted_suffix}"
        },
        {
            MessageId::DisplayRecordDeletedSuffixText,
            "DISPLAY_RECORD_DELETED_SUFFIX_TEXT",
            "COMMAND:DISPLAY",
            "STATUS",
            "INFO",
            " [DELETED]"
        },
        {
            MessageId::DisplayFieldLineText,
            "DISPLAY_FIELD_LINE_TEXT",
            "COMMAND:DISPLAY",
            "STATUS",
            "INFO",
            "  {field} = {value}"
        },
        {
            MessageId::SetPathUsageText,
            "SET_PATH_USAGE_TEXT",
            "COMMAND:SET PATH",
            "USAGE",
            "INFO",
            "Usage:\n  SETPATH\n  SETPATH USAGE\n  SETPATH RESET\n  SETPATH <slot> [TO|=] <path>\n  SET PATH <slot> [TO|=] <path>\nSlots:\n  DATA DBF XDBF INDEXES LMDB WORKSPACES SCHEMAS PROJECTS SCRIPTS TESTS HELP LOGS TMP"
        },
        {
            MessageId::SetPathResetText,
            "SET_PATH_RESET_TEXT",
            "COMMAND:SET PATH",
            "STATUS",
            "INFO",
            "reset to defaults."
        },
        {
            MessageId::SetPathUnknownSlotText,
            "SET_PATH_UNKNOWN_SLOT_TEXT",
            "COMMAND:SET PATH",
            "ERROR",
            "ERROR",
            "unknown slot: {slot}"
        },
        {
            MessageId::SetPathAssignedText,
            "SET_PATH_ASSIGNED_TEXT",
            "COMMAND:SET PATH",
            "STATUS",
            "INFO",
            "{slot} = {path}"
        },
        {
            MessageId::SetPathWarnMissingText,
            "SET_PATH_WARN_MISSING_TEXT",
            "COMMAND:SET PATH",
            "WARNING",
            "WARNING",
            "warning: path does not exist"
        },
        {
            MessageId::SetPathWarnExpectedDirectoryText,
            "SET_PATH_WARN_EXPECTED_DIRECTORY_TEXT",
            "COMMAND:SET PATH",
            "WARNING",
            "WARNING",
            "warning: expected directory, found file"
        },
        {
            MessageId::SetIndexUsageText,
            "SET_INDEX_USAGE_TEXT",
            "COMMAND:SET INDEX",
            "USAGE",
            "INFO",
            "Usage:\n  SET INDEX USAGE\n  SET INDEX TO\n  SET INDEX TO <container>\n  SET INDEX TO <container> TAG <tag>\n  SET INDEX TO <container> <tag>\n  SETINDEX USAGE\n  SETINDEX TO\n  SETINDEX TO <container>\n  SETINDEX TO <container> TAG <tag>\n  SETINDEX TO <container> <tag>"
        },
        {
            MessageId::SetIndexNoTableOpenText,
            "SET_INDEX_NO_TABLE_OPEN_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "no table open."
        },
        {
            MessageId::SetIndexMissingFilenameText,
            "SET_INDEX_MISSING_FILENAME_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "missing filename."
        },
        {
            MessageId::SetIndexTagRequiresNameText,
            "SET_INDEX_TAG_REQUIRES_NAME_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "TAG requires a name."
        },
        {
            MessageId::SetIndexUnexpectedTrailingTokenText,
            "SET_INDEX_UNEXPECTED_TRAILING_TOKEN_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "unexpected trailing token '{token}'."
        },
        {
            MessageId::SetIndexUnsupportedContainerText,
            "SET_INDEX_UNSUPPORTED_CONTAINER_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "unsupported index container: {path}\nSupported: .inx, .cnx, .cdx"
        },
        {
            MessageId::SetIndexV32AcceptsInxOrCnxText,
            "SET_INDEX_V32_ACCEPTS_INX_OR_CNX_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "v32 tables accept INX or CNX, not CDX.\nUse .inx or .cnx for this table."
        },
        {
            MessageId::SetIndexV64RequiresCdxText,
            "SET_INDEX_V64_REQUIRES_CDX_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "v64 tables require CDX (LMDB-backed).\nUse .cdx for this table."
        },
        {
            MessageId::SetIndexUnknownFlavorText,
            "SET_INDEX_UNKNOWN_FLAVOR_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "unknown/unsupported table flavor for current area."
        },
        {
            MessageId::SetIndexNoValidV32IndexText,
            "SET_INDEX_NO_VALID_V32_INDEX_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "no valid v32 index found for '{token}'.\nLooked for .cnx, then .inx."
        },
        {
            MessageId::SetIndexUnableOpenCdxContainerText,
            "SET_INDEX_UNABLE_OPEN_CDX_CONTAINER_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "unable to open CDX container."
        },
        {
            MessageId::SetIndexUnableReadCdxTagDirectoryText,
            "SET_INDEX_UNABLE_READ_CDX_TAG_DIRECTORY_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "unable to read CDX tag directory."
        },
        {
            MessageId::SetIndexTagNotFoundInContainerText,
            "SET_INDEX_TAG_NOT_FOUND_IN_CONTAINER_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "tag '{tag}' not found in {container}"
        },
        {
            MessageId::SetIndexOpenCdxContainerNotFoundText,
            "SET_INDEX_OPEN_CDX_CONTAINER_NOT_FOUND_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "openCdx: container not found: {container}"
        },
        {
            MessageId::SetIndexOpenCdxEnvMissingText,
            "SET_INDEX_OPEN_CDX_ENV_MISSING_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "openCdx: LMDB env missing: {env}"
        },
        {
            MessageId::SetIndexOpenCdxBackendOpenFailedText,
            "SET_INDEX_OPEN_CDX_BACKEND_OPEN_FAILED_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "openCdx: backend open() failed [container={container}, env={env}]"
        },
        {
            MessageId::SetIndexOpenCdxBackendOpenFailedDetailText,
            "SET_INDEX_OPEN_CDX_BACKEND_OPEN_FAILED_DETAIL_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "{detail} [container={container}, env={env}]"
        },
        {
            MessageId::SetIndexOpenCnxContainerNotFoundText,
            "SET_INDEX_OPEN_CNX_CONTAINER_NOT_FOUND_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "openCnx: container not found: {container}"
        },
        {
            MessageId::SetIndexOpenCnxBackendOpenFailedText,
            "SET_INDEX_OPEN_CNX_BACKEND_OPEN_FAILED_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "openCnx: backend open failed"
        },
        {
            MessageId::SetIndexFileNotFoundText,
            "SET_INDEX_FILE_NOT_FOUND_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "file not found: {path}"
        },
        {
            MessageId::SetIndexCdxEnvMissingText,
            "SET_INDEX_CDX_ENV_MISSING_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "CDX container found but LMDB env missing"
        },
        {
            MessageId::SetIndexContainerLine,
            "SET_INDEX_CONTAINER_LINE",
            "COMMAND:SET INDEX",
            "STATUS",
            "INFO",
            "  Container: {path}"
        },
        {
            MessageId::SetIndexExpectedEnvLine,
            "SET_INDEX_EXPECTED_ENV_LINE",
            "COMMAND:SET INDEX",
            "STATUS",
            "INFO",
            "  Expected : {path}"
        },
        {
            MessageId::SetIndexLmdbEnvLine,
            "SET_INDEX_LMDB_ENV_LINE",
            "COMMAND:SET INDEX",
            "STATUS",
            "INFO",
            "  LMDB env : {path}"
        },
        {
            MessageId::SetIndexHintReindexBuildLmdbText,
            "SET_INDEX_HINT_REINDEX_BUILDLMDB_TEXT",
            "COMMAND:SET INDEX",
            "HINT",
            "INFO",
            "Hint: run REINDEX CDX or BUILDLMDB"
        },
        {
            MessageId::SetIndexCdxAttachedText,
            "SET_INDEX_CDX_ATTACHED_TEXT",
            "COMMAND:SET INDEX",
            "STATUS",
            "INFO",
            "CDX attached"
        },
        {
            MessageId::SetIndexCnxAttachedText,
            "SET_INDEX_CNX_ATTACHED_TEXT",
            "COMMAND:SET INDEX",
            "STATUS",
            "INFO",
            "CNX attached"
        },
        {
            MessageId::SetIndexInxAttachedText,
            "SET_INDEX_INX_ATTACHED_TEXT",
            "COMMAND:SET INDEX",
            "STATUS",
            "INFO",
            "INX attached"
        },
        {
            MessageId::SetIndexUseSetOrderHintText,
            "SET_INDEX_USE_SET_ORDER_HINT_TEXT",
            "COMMAND:SET INDEX",
            "HINT",
            "INFO",
            "Use SET ORDER TO TAG <tag>"
        },
        {
            MessageId::SetIndexTagNotFoundText,
            "SET_INDEX_TAG_NOT_FOUND_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "Tag '{tag}' not found."
        },
        {
            MessageId::SetIndexTagInvalidForTableText,
            "SET_INDEX_TAG_INVALID_FOR_TABLE_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "Tag '{tag}' not valid for this table."
        },
        {
            MessageId::SetIndexInxTagIgnoredText,
            "SET_INDEX_INX_TAG_IGNORED_TEXT",
            "COMMAND:SET INDEX",
            "STATUS",
            "INFO",
            "  Note: INX is single-order; tag ignored."
        },
        {
            MessageId::SetIndexUnsupportedResolvedExtensionText,
            "SET_INDEX_UNSUPPORTED_RESOLVED_EXTENSION_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "unsupported resolved extension: {path}"
        },
        {
            MessageId::SetIndexUnableActivateTagText,
            "SET_INDEX_UNABLE_ACTIVATE_TAG_TEXT",
            "COMMAND:SET INDEX",
            "ERROR",
            "ERROR",
            "unable to activate tag."
        },
        {
            MessageId::SetIndexAttachedActivatedText,
            "SET_INDEX_ATTACHED_ACTIVATED_TEXT",
            "COMMAND:SET INDEX",
            "STATUS",
            "INFO",
            "attached + activated"
        },
        {
            MessageId::SetIndexTagAscLine,
            "SET_INDEX_TAG_ASC_LINE",
            "COMMAND:SET INDEX",
            "STATUS",
            "INFO",
            "  TAG: '{tag}' (ASC)"
        },
        {
            MessageId::SetOrderUsageText,
            "SET_ORDER_USAGE_TEXT",
            "COMMAND:SET ORDER",
            "USAGE",
            "INFO",
            "Usage:\n  SET ORDER\n  SET ORDER USAGE\n  SET ORDER 0\n  SET ORDER PHYSICAL\n  SET ORDER NATURAL\n  SET ORDER <tag>\n  SET ORDER TAG <tag>\n  SET ORDER TAG <tag> IN <alias>\n  SET ORDER <container> <tag> [ASC|DESC]\n  SETORDER\n  SETORDER USAGE\n  SETORDER <tag>"
        },
        {
            MessageId::SetOrderNonePhysicalText,
            "SET_ORDER_NONE_PHYSICAL_TEXT",
            "COMMAND:SET ORDER",
            "STATUS",
            "INFO",
            "none (physical order)."
        },
        {
            MessageId::SetOrderStatusText,
            "SET_ORDER_STATUS_TEXT",
            "COMMAND:SET ORDER",
            "STATUS",
            "INFO",
            "{type} '{name}'{tag_clause} ({direction})"
        },
        {
            MessageId::SetOrderTagClauseText,
            "SET_ORDER_TAG_CLAUSE_TEXT",
            "COMMAND:SET ORDER",
            "STATUS",
            "INFO",
            " TAG '{tag}'"
        },
        {
            MessageId::SetOrderMissingTargetText,
            "SET_ORDER_MISSING_TARGET_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "missing target."
        },
        {
            MessageId::SetOrderEngineUnavailableText,
            "SET_ORDER_ENGINE_UNAVAILABLE_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "engine not available."
        },
        {
            MessageId::SetOrderUnknownAreaAliasText,
            "SET_ORDER_UNKNOWN_AREA_ALIAS_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "unknown area/alias: {alias}"
        },
        {
            MessageId::SetOrderNoTableOpenTargetAreaText,
            "SET_ORDER_NO_TABLE_OPEN_TARGET_AREA_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "no table open in target area."
        },
        {
            MessageId::SetOrderClearedPhysicalText,
            "SET_ORDER_CLEARED_PHYSICAL_TEXT",
            "COMMAND:SET ORDER",
            "STATUS",
            "INFO",
            "cleared (physical order)."
        },
        {
            MessageId::SetOrderNumericNotImplementedText,
            "SET_ORDER_NUMERIC_NOT_IMPLEMENTED_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "numeric tag orders not yet implemented (requested {number})."
        },
        {
            MessageId::SetOrderMissingTagNameAfterTagText,
            "SET_ORDER_MISSING_TAG_NAME_AFTER_TAG_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "missing tag name after TAG."
        },
        {
            MessageId::SetOrderExpectsTagNotContainerText,
            "SET_ORDER_EXPECTS_TAG_NOT_CONTAINER_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "expects a tag name, not a container filename."
        },
        {
            MessageId::SetOrderUseTitleText,
            "SET_ORDER_USE_TITLE_TEXT",
            "COMMAND:SET ORDER",
            "HINT",
            "INFO",
            "Use:"
        },
        {
            MessageId::SetOrderUnableResolveContainerText,
            "SET_ORDER_UNABLE_RESOLVE_CONTAINER_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "unable to resolve container."
        },
        {
            MessageId::SetOrderMissingTagText,
            "SET_ORDER_MISSING_TAG_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "missing tag."
        },
        {
            MessageId::SetOrderFileNotFoundText,
            "SET_ORDER_FILE_NOT_FOUND_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "file not found: {path}"
        },
        {
            MessageId::SetOrderInxNotImplementedText,
            "SET_ORDER_INX_NOT_IMPLEMENTED_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            ".INX activation is not implemented here."
        },
        {
            MessageId::SetOrderTagNotAvailableForCnxText,
            "SET_ORDER_TAG_NOT_AVAILABLE_FOR_CNX_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "tag '{tag}' not available for CNX on current table."
        },
        {
            MessageId::SetOrderUnsupportedIndexContainerText,
            "SET_ORDER_UNSUPPORTED_INDEX_CONTAINER_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "unsupported index container: {container}"
        },
        {
            MessageId::SetOrderUnableActivateOrderText,
            "SET_ORDER_UNABLE_ACTIVATE_ORDER_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "unable to activate order."
        },
        {
            MessageId::SetOrderActivatedText,
            "SET_ORDER_ACTIVATED_TEXT",
            "COMMAND:SET ORDER",
            "STATUS",
            "INFO",
            "{kind} TAG '{tag}' ({direction})"
        },
        {
            MessageId::SetOrderUnableOpenCdxContainerText,
            "SET_ORDER_UNABLE_OPEN_CDX_CONTAINER_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "unable to open CDX container."
        },
        {
            MessageId::SetOrderUnableReadCdxTagDirectoryText,
            "SET_ORDER_UNABLE_READ_CDX_TAG_DIRECTORY_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "unable to read CDX tag directory."
        },
        {
            MessageId::SetOrderTagNotFoundInContainerText,
            "SET_ORDER_TAG_NOT_FOUND_IN_CONTAINER_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "tag '{tag}' not found in {container}"
        },
        {
            MessageId::SetOrderV32UsesCnxNotCdxText,
            "SET_ORDER_V32_USES_CNX_NOT_CDX_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "v32 tables use CNX for SET ORDER tag activation, not CDX."
        },
        {
            MessageId::SetOrderV64RequiresCdxText,
            "SET_ORDER_V64_REQUIRES_CDX_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "v64 tables require CDX for SET ORDER."
        },
        {
            MessageId::SetOrderOpenCdxContainerNotFoundText,
            "SET_ORDER_OPEN_CDX_CONTAINER_NOT_FOUND_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "openCdx: container not found: {container}"
        },
        {
            MessageId::SetOrderOpenCdxEnvMissingText,
            "SET_ORDER_OPEN_CDX_ENV_MISSING_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "openCdx: LMDB env missing: {env}"
        },
        {
            MessageId::SetOrderOpenCdxBackendOpenFailedText,
            "SET_ORDER_OPEN_CDX_BACKEND_OPEN_FAILED_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "openCdx: backend open() failed [container={container}, env={env}]"
        },
        {
            MessageId::SetOrderOpenCdxBackendOpenFailedDetailText,
            "SET_ORDER_OPEN_CDX_BACKEND_OPEN_FAILED_DETAIL_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "{detail} [container={container}, env={env}]"
        },
        {
            MessageId::SetOrderOpenCnxContainerNotFoundText,
            "SET_ORDER_OPEN_CNX_CONTAINER_NOT_FOUND_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "openCnx: container not found: {container}"
        },
        {
            MessageId::SetOrderOpenCnxBackendOpenFailedText,
            "SET_ORDER_OPEN_CNX_BACKEND_OPEN_FAILED_TEXT",
            "COMMAND:SET ORDER",
            "ERROR",
            "ERROR",
            "openCnx: backend open failed"
        },
        {
            MessageId::SetCdxUsageText,
            "SET_CDX_USAGE_TEXT",
            "COMMAND:SET CDX",
            "USAGE",
            "INFO",
            "Usage:\n  SET CDX USAGE\n  SET CDX\n  SET CDX <name-or-path>\n  SETCDX\n  SETCDX USAGE\n  SETCDX <name-or-path>"
        },
        {
            MessageId::SetCdxAttachedText,
            "SET_CDX_ATTACHED_TEXT",
            "COMMAND:SET CDX",
            "STATUS",
            "INFO",
            "attached \"{path}\""
        },
        {
            MessageId::SetCdxFailedText,
            "SET_CDX_FAILED_TEXT",
            "COMMAND:SET CDX",
            "ERROR",
            "ERROR",
            "failed: {detail}"
        },
        {
            MessageId::SetCnxUsageText,
            "SET_CNX_USAGE_TEXT",
            "COMMAND:SET CNX",
            "USAGE",
            "INFO",
            "Usage:\n  SET CNX USAGE\n  SET CNX\n  SET CNX <name-or-path>\n  SETCNX\n  SETCNX USAGE\n  SETCNX <name-or-path>"
        },
        {
            MessageId::SetCnxAttachedText,
            "SET_CNX_ATTACHED_TEXT",
            "COMMAND:SET CNX",
            "STATUS",
            "INFO",
            "attached \"{path}\""
        },
        {
            MessageId::SetCnxFailedText,
            "SET_CNX_FAILED_TEXT",
            "COMMAND:SET CNX",
            "ERROR",
            "ERROR",
            "failed: {detail}"
        },
        {
            MessageId::SetLmdbUsageText,
            "SET_LMDB_USAGE_TEXT",
            "COMMAND:SET LMDB",
            "USAGE",
            "INFO",
            "Usage:\n  SET LMDB\n  SET LMDB USAGE\n  SET LMDB 0\n  SET LMDB <stem> [<tag>] [--asc|--desc]\n  SET LMDB <container.cdx> [<tag>] [--asc|--desc]\n  SET LMDB <envdir.cdx.d> [<tag>] [--asc|--desc]\n  SETLMDB\n  SETLMDB USAGE\n  SETLMDB 0\n  SETLMDB <stem> [<tag>] [--asc|--desc]"
        },
        {
            MessageId::SetLmdbStatusText,
            "SET_LMDB_STATUS_TEXT",
            "COMMAND:SET LMDB",
            "STATUS",
            "INFO",
            "container '{container}' TAG '{tag}' ({direction})"
        },
        {
            MessageId::SetLmdbBackendLineText,
            "SET_LMDB_BACKEND_LINE_TEXT",
            "COMMAND:SET LMDB",
            "STATUS",
            "INFO",
            "  backend: {backend}"
        },
        {
            MessageId::SetLmdbOpenCdxFailedText,
            "SET_LMDB_OPEN_CDX_FAILED_TEXT",
            "COMMAND:SET LMDB",
            "ERROR",
            "ERROR",
            "error: {detail}"
        },
        {
            MessageId::SetLmdbUsingText,
            "SET_LMDB_USING_TEXT",
            "COMMAND:SET LMDB",
            "STATUS",
            "INFO",
            "using CDX '{container}' TAG '{tag}' ({direction})"
        },
        {
            MessageId::SetLmdbEnvdirLineText,
            "SET_LMDB_ENVDIR_LINE_TEXT",
            "COMMAND:SET LMDB",
            "STATUS",
            "INFO",
            "  envdir: {path}"
        },
        {
            MessageId::SetUniqueUsageText,
            "SET_UNIQUE_USAGE_TEXT",
            "COMMAND:SET UNIQUE",
            "USAGE",
            "INFO",
            "Usage:\n  SET UNIQUE\n  SET UNIQUE USAGE\n  SET UNIQUE FIELD <name> ON\n  SET UNIQUE FIELD <name> OFF"
        },
        {
            MessageId::SetUniqueNoneText,
            "SET_UNIQUE_NONE_TEXT",
            "COMMAND:SET UNIQUE",
            "STATUS",
            "INFO",
            "UNIQUE: (none)"
        },
        {
            MessageId::SetUniqueFieldsText,
            "SET_UNIQUE_FIELDS_TEXT",
            "COMMAND:SET UNIQUE",
            "STATUS",
            "INFO",
            "UNIQUE fields: {fields}"
        },
        {
            MessageId::SetUniqueFieldStatusText,
            "SET_UNIQUE_FIELD_STATUS_TEXT",
            "COMMAND:SET UNIQUE",
            "STATUS",
            "INFO",
            "UNIQUE {state} for FIELD {field}."
        },
        {
            MessageId::SetCaseUsageText,
            "SET_CASE_USAGE_TEXT",
            "COMMAND:SET CASE",
            "USAGE",
            "INFO",
            "Usage:\n  SET CASE\n  SET CASE USAGE\n  SET CASE ON\n  SET CASE OFF\n  SETCASE\n  SETCASE USAGE\n  SETCASE ON\n  SETCASE OFF"
        },
        {
            MessageId::SetCaseStatusText,
            "SET_CASE_STATUS_TEXT",
            "COMMAND:SET CASE",
            "STATUS",
            "INFO",
            "CASE SENSITIVE: {state}"
        },
        {
            MessageId::SetNearUsageText,
            "SET_NEAR_USAGE_TEXT",
            "COMMAND:SET NEAR",
            "USAGE",
            "INFO",
            "Usage:\n  SET NEAR\n  SET NEAR USAGE\n  SET NEAR ON\n  SET NEAR OFF\n  SETNEAR\n  SETNEAR USAGE\n  SETNEAR ON\n  SETNEAR OFF"
        },
        {
            MessageId::SetNearStatusText,
            "SET_NEAR_STATUS_TEXT",
            "COMMAND:SET NEAR",
            "STATUS",
            "INFO",
            "NEAR: {state}"
        },
        {
            MessageId::SetFilterUsageText,
            "SET_FILTER_USAGE_TEXT",
            "COMMAND:SET FILTER",
            "USAGE",
            "INFO",
            "Usage:\n  SET FILTER USAGE\n  SET FILTER TO <expr>\n  SET FILTER TO\n  SETFILTER USAGE\n  SETFILTER TO <expr>\n  SETFILTER TO"
        },
        {
            MessageId::SetFilterExpectedToText,
            "SET_FILTER_EXPECTED_TO_TEXT",
            "COMMAND:SET FILTER",
            "ERROR",
            "ERROR",
            "expected 'TO'."
        },
        {
            MessageId::SetFilterClearedText,
            "SET_FILTER_CLEARED_TEXT",
            "COMMAND:SET FILTER",
            "STATUS",
            "INFO",
            "cleared."
        },
        {
            MessageId::SetFilterErrorText,
            "SET_FILTER_ERROR_TEXT",
            "COMMAND:SET FILTER",
            "ERROR",
            "ERROR",
            "error: {detail}"
        },
        {
            MessageId::SetFilterAppliedText,
            "SET_FILTER_APPLIED_TEXT",
            "COMMAND:SET FILTER",
            "STATUS",
            "INFO",
            "TO {expr}"
        },
        {
            MessageId::SetRelationUsageText,
            "SET_RELATION_USAGE_TEXT",
            "COMMAND:SET RELATION",
            "USAGE",
            "INFO",
            "Usage:\n  SET RELATION USAGE\n  SET RELATION TO <expr> INTO <child>\n  SET RELATION TO <expr> INTO <child>, <expr> INTO <child>\n  SET RELATION ADDITIVE TO <expr> INTO <child>\n  SET RELATION OFF ALL\n  SET RELATION OFF INTO <child>"
        },
        {
            MessageId::SetRelationNoCurrentParentText,
            "SET_RELATION_NO_CURRENT_PARENT_TEXT",
            "COMMAND:SET RELATION",
            "ERROR",
            "ERROR",
            "no current parent area"
        },
        {
            MessageId::SetRelationOkText,
            "SET_RELATION_OK_TEXT",
            "COMMAND:SET RELATION",
            "STATUS",
            "INFO",
            "OK"
        },
        {
            MessageId::SetRelationOffIntoRequiresChildText,
            "SET_RELATION_OFF_INTO_REQUIRES_CHILD_TEXT",
            "COMMAND:SET RELATION",
            "ERROR",
            "ERROR",
            "OFF INTO requires child area"
        },
        {
            MessageId::SetRelationExpectedOffTailText,
            "SET_RELATION_EXPECTED_OFF_TAIL_TEXT",
            "COMMAND:SET RELATION",
            "ERROR",
            "ERROR",
            "expected INTO <child> or ALL after OFF"
        },
        {
            MessageId::SetRelationAdditiveRequiresToIntoText,
            "SET_RELATION_ADDITIVE_REQUIRES_TO_INTO_TEXT",
            "COMMAND:SET RELATION",
            "ERROR",
            "ERROR",
            "ADDITIVE requires TO <expr> INTO <child>"
        },
        {
            MessageId::SetRelationAdditiveExpectsToText,
            "SET_RELATION_ADDITIVE_EXPECTS_TO_TEXT",
            "COMMAND:SET RELATION",
            "ERROR",
            "ERROR",
            "ADDITIVE expects TO"
        },
        {
            MessageId::SetRelationExpectedToAdditiveOffText,
            "SET_RELATION_EXPECTED_TO_ADDITIVE_OFF_TEXT",
            "COMMAND:SET RELATION",
            "ERROR",
            "ERROR",
            "expected TO, ADDITIVE, or OFF"
        },
        {
            MessageId::SetRelationInvalidClauseText,
            "SET_RELATION_INVALID_CLAUSE_TEXT",
            "COMMAND:SET RELATION",
            "ERROR",
            "ERROR",
            "invalid TO ... INTO ... clause"
        },
        {
            MessageId::SetRelationEmptyExpressionForChildText,
            "SET_RELATION_EMPTY_EXPRESSION_FOR_CHILD_TEXT",
            "COMMAND:SET RELATION",
            "ERROR",
            "ERROR",
            "empty expression for child {child}"
        },
        {
            MessageId::RelDiagAddFailedNoFieldsText,
            "REL_DIAG_ADD_FAILED_NO_FIELDS_TEXT",
            "SUBSYSTEM:REL",
            "STATUS",
            "INFO",
            "add failed (no fields provided)"
        },
        {
            MessageId::RelDiagAddFailedFieldCountMismatchText,
            "REL_DIAG_ADD_FAILED_FIELD_COUNT_MISMATCH_TEXT",
            "SUBSYSTEM:REL",
            "STATUS",
            "INFO",
            "add failed (parent/child field counts differ)"
        },
        {
            MessageId::RelDiagAddFailedNotOpenText,
            "REL_DIAG_ADD_FAILED_NOT_OPEN_TEXT",
            "SUBSYSTEM:REL",
            "STATUS",
            "INFO",
            "add failed (parent/child not open)"
        },
        {
            MessageId::RelDiagParentFieldNotFoundText,
            "REL_DIAG_PARENT_FIELD_NOT_FOUND_TEXT",
            "SUBSYSTEM:REL",
            "STATUS",
            "INFO",
            "parent field not found: {field}"
        },
        {
            MessageId::RelDiagChildFieldNotFoundText,
            "REL_DIAG_CHILD_FIELD_NOT_FOUND_TEXT",
            "SUBSYSTEM:REL",
            "STATUS",
            "INFO",
            "child field not found: {field}"
        },
        {
            MessageId::RelDiagAddedText,
            "REL_DIAG_ADDED_TEXT",
            "SUBSYSTEM:REL",
            "STATUS",
            "INFO",
            "{parent} -> {child} ON {fields}"
        },
        {
            MessageId::RelDiagNoRelationsDefinedText,
            "REL_DIAG_NO_RELATIONS_DEFINED_TEXT",
            "SUBSYSTEM:REL",
            "STATUS",
            "INFO",
            "no relations defined for {parent}"
        },
        {
            MessageId::RelDiagRelationNotFoundText,
            "REL_DIAG_RELATION_NOT_FOUND_TEXT",
            "SUBSYSTEM:REL",
            "STATUS",
            "INFO",
            "relation not found: {parent} -> {child}"
        },
        {
            MessageId::RelDiagRemovedText,
            "REL_DIAG_REMOVED_TEXT",
            "SUBSYSTEM:REL",
            "STATUS",
            "INFO",
            "removed {parent} -> {child}"
        },
        {
            MessageId::RelDiagClearedForText,
            "REL_DIAG_CLEARED_FOR_TEXT",
            "SUBSYSTEM:REL",
            "STATUS",
            "INFO",
            "cleared for {parent}"
        },
        {
            MessageId::RelDiagClearedAllText,
            "REL_DIAG_CLEARED_ALL_TEXT",
            "SUBSYSTEM:REL",
            "STATUS",
            "INFO",
            "cleared all"
        },
        {
            MessageId::SetRelationsUsageText,
            "SET_RELATIONS_USAGE_TEXT",
            "COMMAND:SET RELATIONS",
            "USAGE",
            "INFO",
            "Usage:\n  SET RELATIONS\n  SET RELATIONS USAGE\n  SET RELATIONS ADD <parent> <child> ON f1[,f2...]\n  SET RELATIONS ADD <parent> <child> ON parent_f1[,parent_f2...] TO child_f1[,child_f2...]\n  SET RELATIONS CLEAR <parent>\n  SET RELATIONS CLEAR ALL\nExamples:\n  SET RELATIONS ADD STUDENTS ENROLL ON SID\n  SET RELATIONS CLEAR STUDENTS\n  SET RELATIONS CLEAR ALL"
        },
        {
            MessageId::RelationsUsageText,
            "RELATIONS_USAGE_TEXT",
            "COMMAND:RELATIONS",
            "USAGE",
            "INFO",
            "Usage:\n  RELATIONS\n  RELATIONS USAGE\n  RELATIONS ALL\n  SET RELATIONS\n  SET RELATIONS USAGE\n  SET RELATIONS ADD <parent> <child> ON f1[,f2...] [TO child_f1[,child_f2...]]\n  SET RELATIONS CLEAR <parent|ALL>\nExamples:\n  RELATIONS\n  RELATIONS ALL\n  SET RELATIONS ADD STUDENTS ENROLL ON SID\n  SET RELATIONS CLEAR ALL\nNotes:\n  - RELATIONS USAGE does not inspect or mutate relation state.\n  - SET RELATIONS USAGE does not mutate relation definitions."
        },
        {
            MessageId::RelationsFileUsageText,
            "RELATIONS_FILE_USAGE_TEXT",
            "COMMAND:REL",
            "USAGE",
            "INFO",
            "REL SAVE/LOAD syntax\n  REL SAVE [<file>|DEFAULT|DATASET <name>]\n  REL LOAD [<file>|DEFAULT|DATASET <name>]"
        },
        {
            MessageId::SetRelationsAddUsageText,
            "SET_RELATIONS_ADD_USAGE_TEXT",
            "COMMAND:SET RELATIONS",
            "USAGE",
            "INFO",
            "Usage: SET RELATIONS ADD <parent> <child> ON f1,f2"
        },
        {
            MessageId::SetRelationsAddUsageWithToText,
            "SET_RELATIONS_ADD_USAGE_WITH_TO_TEXT",
            "COMMAND:SET RELATIONS",
            "USAGE",
            "INFO",
            "Usage: SET RELATIONS ADD <parent> <child> ON f1,f2 [TO child_f1,child_f2]"
        },
        {
            MessageId::SetRelationsNoFieldsText,
            "SET_RELATIONS_NO_FIELDS_TEXT",
            "COMMAND:SET RELATIONS",
            "ERROR",
            "ERROR",
            "no fields provided"
        },
        {
            MessageId::SetRelationsFieldCountMismatchText,
            "SET_RELATIONS_FIELD_COUNT_MISMATCH_TEXT",
            "COMMAND:SET RELATIONS",
            "ERROR",
            "ERROR",
            "parent/child field counts differ"
        },
        {
            MessageId::SetRelationsClearUsageText,
            "SET_RELATIONS_CLEAR_USAGE_TEXT",
            "COMMAND:SET RELATIONS",
            "USAGE",
            "INFO",
            "Usage: SET RELATIONS CLEAR <parent>|ALL"
        },
        {
            MessageId::SetRelationsUnknownOpText,
            "SET_RELATIONS_UNKNOWN_OP_TEXT",
            "COMMAND:SET RELATIONS",
            "ERROR",
            "ERROR",
            "unknown op. Try: ADD / CLEAR"
        },
        {
            MessageId::RelListNoCurrentParentText,
            "REL_LIST_NO_CURRENT_PARENT_TEXT",
            "COMMAND:RELATIONS",
            "ERROR",
            "ERROR",
            "no current parent"
        },
        {
            MessageId::RelListTreeRootedAtText,
            "REL_LIST_TREE_ROOTED_AT_TEXT",
            "COMMAND:RELATIONS",
            "STATUS",
            "INFO",
            "Relations (tree) rooted at: {parent}"
        },
        {
            MessageId::RelListNoneText,
            "REL_LIST_NONE_TEXT",
            "COMMAND:RELATIONS",
            "STATUS",
            "INFO",
            "  (none)"
        },
        {
            MessageId::RelListParentHeaderText,
            "REL_LIST_PARENT_HEADER_TEXT",
            "COMMAND:RELATIONS",
            "STATUS",
            "INFO",
            "Relations for parent: {parent}"
        },
        {
            MessageId::RelListMatchLineText,
            "REL_LIST_MATCH_LINE_TEXT",
            "COMMAND:RELATIONS",
            "STATUS",
            "INFO",
            "  -> {child}  (matches: {count})"
        },
        {
            MessageId::RelSaveCannotWriteText,
            "REL_SAVE_CANNOT_WRITE_TEXT",
            "COMMAND:REL SAVE",
            "ERROR",
            "ERROR",
            "cannot write file: {path}"
        },
        {
            MessageId::RelSaveOkText,
            "REL_SAVE_OK_TEXT",
            "COMMAND:REL SAVE",
            "STATUS",
            "INFO",
            "OK ({count} relation(s) saved to {path})"
        },
        {
            MessageId::RelLoadCannotReadText,
            "REL_LOAD_CANNOT_READ_TEXT",
            "COMMAND:REL LOAD",
            "ERROR",
            "ERROR",
            "cannot read file or file empty: {path}"
        },
        {
            MessageId::RelLoadNoRelationsFoundText,
            "REL_LOAD_NO_RELATIONS_FOUND_TEXT",
            "COMMAND:REL LOAD",
            "ERROR",
            "ERROR",
            "no relations found in file"
        },
        {
            MessageId::RelLoadOkText,
            "REL_LOAD_OK_TEXT",
            "COMMAND:REL LOAD",
            "STATUS",
            "INFO",
            "OK ({count} relation(s) loaded from {path})"
        },
        {
            MessageId::RelJoinUsageText,
            "REL_JOIN_USAGE_TEXT",
            "COMMAND:REL JOIN",
            "USAGE",
            "INFO",
            "REL JOIN syntax\n  REL JOIN [ONE] [DISTINCT|ALL] [LIMIT <n>] [<child1> <child2> ...] TUPLE <fields>\nFlags\n  ONE       emit exactly one row using the current relation context (historical behavior)\n  DISTINCT  de-duplicate tuples (field lists only)\n  ALL       allow duplicates (default; overrides DISTINCT)"
        },
        {
            MessageId::RelJoinLimitRequiresNumberText,
            "REL_JOIN_LIMIT_REQUIRES_NUMBER_TEXT",
            "COMMAND:REL JOIN",
            "ERROR",
            "ERROR",
            "LIMIT requires a number"
        },
        {
            MessageId::RelJoinMissingTupleText,
            "REL_JOIN_MISSING_TUPLE_TEXT",
            "COMMAND:REL JOIN",
            "ERROR",
            "ERROR",
            "missing TUPLE"
        },
        {
            MessageId::RelJoinTupleRequiresExpressionText,
            "REL_JOIN_TUPLE_REQUIRES_EXPRESSION_TEXT",
            "COMMAND:REL JOIN",
            "ERROR",
            "ERROR",
            "TUPLE requires an expression"
        },
        {
            MessageId::RelEnumUsageText,
            "REL_ENUM_USAGE_TEXT",
            "COMMAND:REL ENUM",
            "USAGE",
            "INFO",
            "REL ENUM syntax\n  REL ENUM [DISTINCT|ALL] [LIMIT <n>] [<child1> <child2> ...] TUPLE <fields>\nFlags\n  DISTINCT  de-duplicate tuples (field lists only)\n  ALL       allow duplicates (default; overrides DISTINCT)"
        },
        {
            MessageId::RelEnumLimitRequiresNumberText,
            "REL_ENUM_LIMIT_REQUIRES_NUMBER_TEXT",
            "COMMAND:REL ENUM",
            "ERROR",
            "ERROR",
            "LIMIT requires a number"
        },
        {
            MessageId::RelEnumMissingTupleText,
            "REL_ENUM_MISSING_TUPLE_TEXT",
            "COMMAND:REL ENUM",
            "ERROR",
            "ERROR",
            "missing TUPLE"
        },
        {
            MessageId::RelEnumTupleRequiresExpressionText,
            "REL_ENUM_TUPLE_REQUIRES_EXPRESSION_TEXT",
            "COMMAND:REL ENUM",
            "ERROR",
            "ERROR",
            "TUPLE requires an expression"
        },
        {
            MessageId::ErsatzUsageText,
            "ERSATZ_USAGE_TEXT",
            "COMMAND:ERSATZ",
            "USAGE",
            "INFO",
            "Usage:\n  ERSATZ\n  ERSATZ USAGE\n  ERSATZ SAMPLE\n  ERSATZ SHOW\n  ERSATZ REFRESH\n  ERSATZ TREE\n  ERSATZ GRID\n  ERSATZ STATUS\n  ERSATZ ORDER\n  ERSATZ TOP\n  ERSATZ BOTTOM\n  ERSATZ NEXT [<n>]\n  ERSATZ PREV [<n>]\n  ERSATZ SKIP <n>\n  ERSATZ ROOT [<alias>]\n  ERSATZ LIMIT <n>\n  ERSATZ PATH <alias>\n  ERSATZ CLEARPATH\n  ERSATZ BACK\n  ERSATZ OPEN <workspace>\n  ERSATZ LOAD <name>\n  ERSATZ SAVE <name>\n  ERSATZ WLOAD <name>\n  ERSATZ DELTA MARK [<name>] [LIMIT <n>]\n  ERSATZ DELTA SHOW [<name>] [LIMIT <n>]\n  ERSATZ DELTA CLEAR <name>\n  ERSATZ DELTA CLEAR ALL\n  ERSATZ DELTA STATUS\n  ERSATZ RESET\nNotes:\n  - ERSATZ with no arguments renders the current browser snapshot.\n  - Navigation commands move the root cursor and render again.\n  - LOAD/SAVE/WLOAD interact with workspace files.\n  - SAMPLE prints a DotScript smoke test for MCC/ERSATZ smart-root behavior."
        },
        {
            MessageId::ErsatzStatusHeaderText,
            "ERSATZ_STATUS_HEADER_TEXT",
            "COMMAND:ERSATZ",
            "INFO",
            "INFO",
            "ERSATZ STATUS"
        },
        {
            MessageId::ErsatzSessionResetText,
            "ERSATZ_SESSION_RESET_TEXT",
            "COMMAND:ERSATZ",
            "INFO",
            "INFO",
            "session reset."
        },
        {
            MessageId::ErsatzOrderLine,
            "ERSATZ_ORDER_LINE",
            "COMMAND:ERSATZ",
            "INFO",
            "INFO",
            "ERSATZ ORDER: {value}"
        },
        {
            MessageId::ErsatzRecnoStatusText,
            "ERSATZ_RECNO_STATUS_TEXT",
            "COMMAND:ERSATZ",
            "INFO",
            "INFO",
            "ERSATZ {verb}: recno {recno} ({order})"
        },
        {
            MessageId::ErsatzRootLine,
            "ERSATZ_ROOT_LINE",
            "COMMAND:ERSATZ",
            "INFO",
            "INFO",
            "ERSATZ ROOT: {value}"
        },
        {
            MessageId::ErsatzRootSetText,
            "ERSATZ_ROOT_SET_TEXT",
            "COMMAND:ERSATZ",
            "INFO",
            "INFO",
            "ERSATZ ROOT set to {value}."
        },
        {
            MessageId::ErsatzLimitRequiresNumberText,
            "ERSATZ_LIMIT_REQUIRES_NUMBER_TEXT",
            "COMMAND:ERSATZ",
            "ERROR",
            "ERROR",
            "LIMIT requires a number."
        },
        {
            MessageId::ErsatzLimitSetText,
            "ERSATZ_LIMIT_SET_TEXT",
            "COMMAND:ERSATZ",
            "INFO",
            "INFO",
            "ERSATZ LIMIT set to {value}."
        },
        {
            MessageId::ErsatzPathLine,
            "ERSATZ_PATH_LINE",
            "COMMAND:ERSATZ",
            "INFO",
            "INFO",
            "ERSATZ PATH: {value}"
        },
        {
            MessageId::ErsatzPathClearedText,
            "ERSATZ_PATH_CLEARED_TEXT",
            "COMMAND:ERSATZ",
            "INFO",
            "INFO",
            "path cleared."
        },
        {
            MessageId::ErsatzPathAlreadyEmptyText,
            "ERSATZ_PATH_ALREADY_EMPTY_TEXT",
            "COMMAND:ERSATZ",
            "INFO",
            "INFO",
            "path already empty."
        },
        {
            MessageId::ErsatzOpenRequiresAliasText,
            "ERSATZ_OPEN_REQUIRES_ALIAS_TEXT",
            "COMMAND:ERSATZ",
            "ERROR",
            "ERROR",
            "OPEN requires a child alias."
        },
        {
            MessageId::ErsatzInvalidNextChildText,
            "ERSATZ_INVALID_NEXT_CHILD_TEXT",
            "COMMAND:ERSATZ",
            "ERROR",
            "ERROR",
            "alias '{alias}' is not a valid next child for the current path."
        },
        {
            MessageId::ErsatzLoadFailedText,
            "ERSATZ_LOAD_FAILED_TEXT",
            "COMMAND:ERSATZ",
            "ERROR",
            "ERROR",
            "LOAD failed ({detail})"
        },
        {
            MessageId::ErsatzSaveFailedText,
            "ERSATZ_SAVE_FAILED_TEXT",
            "COMMAND:ERSATZ",
            "ERROR",
            "ERROR",
            "SAVE failed ({detail})"
        },
        {
            MessageId::ErsatzPositiveCountRequiredText,
            "ERSATZ_POSITIVE_COUNT_REQUIRED_TEXT",
            "COMMAND:ERSATZ",
            "ERROR",
            "ERROR",
            "{verb} requires a positive count."
        },
        {
            MessageId::ErsatzSignedCountRequiredText,
            "ERSATZ_SIGNED_COUNT_REQUIRED_TEXT",
            "COMMAND:ERSATZ",
            "ERROR",
            "ERROR",
            "{verb} requires a signed count."
        },
        {
            MessageId::ErsatzUnknownSubcommandText,
            "ERSATZ_UNKNOWN_SUBCOMMAND_TEXT",
            "COMMAND:ERSATZ",
            "ERROR",
            "ERROR",
            "unknown subcommand: {subcommand}"
        },
        {
            MessageId::ErsatzAutoLoadedProfileText,
            "ERSATZ_AUTO_LOADED_PROFILE_TEXT",
            "COMMAND:ERSATZ",
            "INFO",
            "INFO",
            "auto-loaded browser profile for active workspace ({status})."
        },
        {
            MessageId::ErsatzRootSelectedFallbackText,
            "ERSATZ_ROOT_SELECTED_FALLBACK_TEXT",
            "COMMAND:ERSATZ",
            "INFO",
            "INFO",
            "root {existing} has no child relations; using selected alias {selected}."
        },
        {
            MessageId::ErsatzSelectedAliasRootText,
            "ERSATZ_SELECTED_ALIAS_ROOT_TEXT",
            "COMMAND:ERSATZ",
            "INFO",
            "INFO",
            "using selected alias {selected} as relational browser root."
        },
        {
            MessageId::ErsatzRootInferredFallbackText,
            "ERSATZ_ROOT_INFERRED_FALLBACK_TEXT",
            "COMMAND:ERSATZ",
            "INFO",
            "INFO",
            "root {existing} has no child relations; inferred root {inferred} from active relation graph."
        },
        {
            MessageId::ErsatzInferredRootText,
            "ERSATZ_INFERRED_ROOT_TEXT",
            "COMMAND:ERSATZ",
            "INFO",
            "INFO",
            "inferred root {inferred} from active relation graph."
        },
        {
            MessageId::ErsatzDeltaLimitRequiresNumberText,
            "ERSATZ_DELTA_LIMIT_REQUIRES_NUMBER_TEXT",
            "COMMAND:ERSATZ DELTA",
            "ERROR",
            "ERROR",
            "LIMIT requires a number."
        },
        {
            MessageId::ErsatzDeltaUsageText,
            "ERSATZ_DELTA_USAGE_TEXT",
            "COMMAND:ERSATZ DELTA",
            "USAGE",
            "INFO",
            "ERSATZ DELTA syntax\n  ERSATZ DELTA MARK [name] [LIMIT n]   capture current tuple stream baseline\n  ERSATZ DELTA SHOW [name] [LIMIT n]   compare current tuple stream to baseline\n  ERSATZ DELTA [name] [LIMIT n]        same as SHOW\n  ERSATZ DELTA CLEAR [name|ALL]        clear saved baseline(s)\n  ERSATZ DELTA STATUS                  list saved baselines\n\nNotes:\n  Baselines are in-memory and session-local.\n  Identity currently uses the first tuple value, falling back to RECNO.\n  The tuple stream respects active order because it uses DbTupleStream."
        },
        {
            MessageId::ErsatzDeltaStatusHeaderText,
            "ERSATZ_DELTA_STATUS_HEADER_TEXT",
            "COMMAND:ERSATZ DELTA",
            "INFO",
            "INFO",
            "ERSATZ DELTA STATUS"
        },
        {
            MessageId::ErsatzDeltaNoBaselinesText,
            "ERSATZ_DELTA_NO_BASELINES_TEXT",
            "COMMAND:ERSATZ DELTA",
            "INFO",
            "INFO",
            "  (no baselines)"
        },
        {
            MessageId::ErsatzDeltaAllBaselinesClearedText,
            "ERSATZ_DELTA_ALL_BASELINES_CLEARED_TEXT",
            "COMMAND:ERSATZ DELTA",
            "INFO",
            "INFO",
            "all baselines cleared."
        },
        {
            MessageId::ErsatzDeltaClearResultText,
            "ERSATZ_DELTA_CLEAR_RESULT_TEXT",
            "COMMAND:ERSATZ DELTA",
            "INFO",
            "INFO",
            "{result} {name}."
        },
        {
            MessageId::ErsatzDeltaCapturedText,
            "ERSATZ_DELTA_CAPTURED_TEXT",
            "COMMAND:ERSATZ DELTA",
            "INFO",
            "INFO",
            "baseline {name} captured rows={rows} table={table}{limit_suffix}."
        },
        {
            MessageId::ErsatzDeltaNoBaselineNamedText,
            "ERSATZ_DELTA_NO_BASELINE_NAMED_TEXT",
            "COMMAND:ERSATZ DELTA",
            "ERROR",
            "ERROR",
            "no baseline named {name}. Use ERSATZ DELTA MARK {name} first."
        },
        {
            MessageId::ErsatzDeltaSummaryText,
            "ERSATZ_DELTA_SUMMARY_TEXT",
            "COMMAND:ERSATZ DELTA",
            "INFO",
            "INFO",
            "{name} table={table} baseline_rows={baseline_rows} current_rows={current_rows} changes={changes}"
        },
        {
            MessageId::ErsatzDeltaNoTupleChangesText,
            "ERSATZ_DELTA_NO_TUPLE_CHANGES_TEXT",
            "COMMAND:ERSATZ DELTA",
            "INFO",
            "INFO",
            "No tuple changes."
        },
        {
            MessageId::UseUsageText,
            "USE_USAGE_TEXT",
            "COMMAND:USE",
            "USAGE",
            "INFO",
            "Usage:\n  USE USAGE              (Show this usage)\n  USE <table>            (Open <DBF slot>/<table>.dbf in current area)\n  USE <table.dbf>        (Open named DBF; logical names resolve through DBF slot)\n  USE <path\\\\table.dbf>   (Open explicit path)\n  USE <table> NOINDEX    (Open in physical order; skip index auto-attach)\n  USE <table> NOIDX      (Alias of NOINDEX)\nNotes:\n  - USE closes/resets the current area before opening the target table.\n  - USE prevents duplicate opens of the same DBF path across work areas.\n  - USE auto-attaches memo storage when memo fields are present.\n  - USE auto-attaches flavor-appropriate indexes when present, unless NOINDEX/NOIDX is used.\n  - USE prefers the configured INDEXES slot and falls back to the DBF directory.\n  - x64/v128 tables prefer CDX.\n  - x32 tables prefer CNX, then INX."
        },
        {
            MessageId::LocateUsageText,
            "LOCATE_USAGE_TEXT",
            "COMMAND:LOCATE",
            "USAGE",
            "INFO",
            "Usage:\n  LOCATE USAGE\n  LOCATE FOR <expr>\n  LOCATE <field> <op> <value>\nExamples:\n  LOCATE FOR LNAME = Smith\n  LOCATE LNAME = Smith\n  LOCATE FOR BALANCE > 100\nNotes:\n  - LOCATE requires an open table except for LOCATE USAGE.\n  - LOCATE positions on the first matching record and updates CONTINUE state."
        },
        {
            MessageId::LocateFoundText,
            "LOCATE_FOUND_TEXT",
            "COMMAND:LOCATE",
            "STATUS",
            "INFO",
            "Located."
        },
        {
            MessageId::LocateNotFoundText,
            "LOCATE_NOT_FOUND_TEXT",
            "COMMAND:LOCATE",
            "STATUS",
            "INFO",
            "Not Located."
        },
        {
            MessageId::AppendUsageText,
            "APPEND_USAGE_TEXT",
            "COMMAND:APPEND",
            "USAGE",
            "INFO",
            "Usage:\n  APPEND USAGE\n  APPEND\n  APPEND <count>\n  APPEND MANY <count>\n  APPEND RAW\n  APPEND RAW MANY <count>\nNotes:\n  - APPEND with no arguments appends one blank record through the shared smart append path.\n  - APPEND MANY uses the smart batch append path.\n  - APPEND RAW uses the raw append path without inline index update."
        },
        {
            MessageId::AppendBlankUsageText,
            "APPEND_BLANK_USAGE_TEXT",
            "COMMAND:APPEND_BLANK",
            "USAGE",
            "INFO",
            "Usage:\n  APPEND_BLANK USAGE\n  APPEND_BLANK\n  APPEND BLANK\nNotes:\n  - Appends one blank record through shared append support."
        },
        {
            MessageId::GoUsageText,
            "GO_USAGE_TEXT",
            "COMMAND:GO",
            "USAGE",
            "INFO",
            "Usage:\n  GO\n  GO USAGE\n  GO TOP\n  GO BOTTOM\n  GO FIRST\n  GO LAST\n  GO TO <recno>\n  GO RECORD <recno>\n  GO <recno>\n  GO +<n>\n  GO -<n>"
        },
        {
            MessageId::GotoUsageText,
            "GOTO_USAGE_TEXT",
            "COMMAND:GOTO",
            "USAGE",
            "INFO",
            "Usage:\n  GOTO USAGE\n  GOTO <recno>\n  GOTO FIRST\n  GOTO LAST"
        },
        {
            MessageId::ContinueUsageText,
            "CONTINUE_USAGE_TEXT",
            "COMMAND:CONTINUE",
            "USAGE",
            "INFO",
            "Usage:\n  CONTINUE\n  CONTINUE USAGE\n  CONTINUE FOR <expr>"
        },
        {
            MessageId::FindUsageText,
            "FIND_USAGE_TEXT",
            "COMMAND:FIND",
            "USAGE",
            "INFO",
            "Usage:\n  FIND USAGE\n  FIND <text>\n  FIND <field> <text>\n  FIND <text> IN <field>\nNotes:\n  - FIND requires an open table except for FIND USAGE.\n  - FIND delegates to SEEK when the active order can satisfy the request.\n  - Otherwise FIND scans the requested field and positions on the found record."
        },
        {
            MessageId::SeekUsageText,
            "SEEK_USAGE_TEXT",
            "COMMAND:SEEK",
            "USAGE",
            "INFO",
            "Usage:\n  SEEK USAGE\n  SEEK <value> IN <field> [TRACE ON|OFF]\n  SEEK <field> = <value> [TRACE ON|OFF]\n  SEEK <field> <value>   [TRACE ON|OFF]\n  SEEK <value>           (uses active order/tag when set)\n  SEEK TRACE ON|OFF\nNotes:\n  SEEK requires an open table except for SEEK USAGE.\n  SEEK <value> uses the active order/tag when one is set."
        },
        {
            MessageId::IndexUsageText,
            "INDEX_USAGE_TEXT",
            "COMMAND:INDEX",
            "USAGE",
            "INFO",
            "Usage: INDEX ON <field> TAG <name> [ASC|DESC] [1INX|2INX]\n   Field-number tokens are also accepted by the parser.\nDefaults: ASC, 2INX\nExamples:\n  INDEX ON LNAME TAG students\n  INDEX ON LNAME TAG students DESC\n  INDEX ON LNAME TAG students DESC 2INX\nNotes:\n  - INDEX requires an open table except for INDEX USAGE.\n  - Deleted records are excluded.\n  - TAG resolves through the INDEXES path and must name an .inx target."
        },
        {
            MessageId::IndexInvalidTagPathText,
            "INDEX_INVALID_TAG_PATH_TEXT",
            "COMMAND:INDEX",
            "ERROR",
            "ERROR",
            "invalid TAG path '{tag}'."
        },
        {
            MessageId::IndexUseBareNameHintText,
            "INDEX_USE_BARE_NAME_HINT_TEXT",
            "COMMAND:INDEX",
            "HINT",
            "INFO",
            "Use a bare name (TAG students), an absolute path, or a slot path:"
        },
        {
            MessageId::IndexUnknownFieldText,
            "INDEX_UNKNOWN_FIELD_TEXT",
            "COMMAND:INDEX",
            "ERROR",
            "ERROR",
            "unknown field '{field}'."
        },
        {
            MessageId::IndexAvailableFieldsTitle,
            "INDEX_AVAILABLE_FIELDS_TITLE",
            "COMMAND:INDEX",
            "STATUS",
            "INFO",
            "Available:"
        },
        {
            MessageId::IndexTipFieldNumberText,
            "INDEX_TIP_FIELD_NUMBER_TEXT",
            "COMMAND:INDEX",
            "HINT",
            "INFO",
            "Tip: INDEX ON #3 TAG students"
        },
        {
            MessageId::IndexTagMustNameInxText,
            "INDEX_TAG_MUST_NAME_INX_TEXT",
            "COMMAND:INDEX",
            "ERROR",
            "ERROR",
            "TAG must name an .inx file."
        },
        {
            MessageId::IndexGotPathText,
            "INDEX_GOT_PATH_TEXT",
            "COMMAND:INDEX",
            "STATUS",
            "INFO",
            "Got: {path}"
        },
        {
            MessageId::IndexCannotWriteFileText,
            "INDEX_CANNOT_WRITE_FILE_TEXT",
            "COMMAND:INDEX",
            "ERROR",
            "ERROR",
            "cannot write file: {path}"
        },
        {
            MessageId::IndexWrittenText,
            "INDEX_WRITTEN_TEXT",
            "COMMAND:INDEX",
            "STATUS",
            "INFO",
            "written: {file} ({format}, expr: {expr}, {direction})"
        },
        {
            MessageId::IdxUsageText,
            "IDX_USAGE_TEXT",
            "COMMAND:IDX",
            "USAGE",
            "INFO",
            "IDX is a memory-only educational index lab.\nIt teaches sorting and index concepts without writing .inx files.\nUse INDEX for persistent INX files.\n\nUsage:\n  IDX\n  IDX USAGE\n  IDX ON <field|#n> TAG <name> [SORT <algo>|<algo>] [ASC|DESC]\n  IDX LIST\n  IDX DROP <tag>\n  IDX DROP ALL\n  IDX HELP\n\nSort algorithms, Phase 1:\n  STD       C++ std::sort baseline\n  BUBBLE    classroom bubble sort\n\nExamples:\n  IDX ON LNAME TAG lname_std\n  IDX ON LNAME TAG lname_bubble BUBBLE\n  IDX ON LNAME TAG lname_bubble2 SORT BUBBLE DESC"
        },
        {
            MessageId::IdxExpectedOnText,
            "IDX_EXPECTED_ON_TEXT",
            "COMMAND:IDX",
            "ERROR",
            "ERROR",
            "expected ON."
        },
        {
            MessageId::IdxMissingFieldTokenText,
            "IDX_MISSING_FIELD_TOKEN_TEXT",
            "COMMAND:IDX",
            "ERROR",
            "ERROR",
            "missing field token."
        },
        {
            MessageId::IdxExpectedTagText,
            "IDX_EXPECTED_TAG_TEXT",
            "COMMAND:IDX",
            "ERROR",
            "ERROR",
            "expected TAG."
        },
        {
            MessageId::IdxMissingTagNameText,
            "IDX_MISSING_TAG_NAME_TEXT",
            "COMMAND:IDX",
            "ERROR",
            "ERROR",
            "missing TAG name."
        },
        {
            MessageId::IdxDuplicateSortOptionText,
            "IDX_DUPLICATE_SORT_OPTION_TEXT",
            "COMMAND:IDX",
            "ERROR",
            "ERROR",
            "duplicate SORT option."
        },
        {
            MessageId::IdxSortRequiresAlgorithmText,
            "IDX_SORT_REQUIRES_ALGORITHM_TEXT",
            "COMMAND:IDX",
            "ERROR",
            "ERROR",
            "SORT requires an algorithm name."
        },
        {
            MessageId::IdxUnknownSortAlgorithmText,
            "IDX_UNKNOWN_SORT_ALGORITHM_TEXT",
            "COMMAND:IDX",
            "ERROR",
            "ERROR",
            "unknown SORT algorithm '{algorithm}'. Supported: STD, BUBBLE."
        },
        {
            MessageId::IdxDuplicateDirectionOptionText,
            "IDX_DUPLICATE_DIRECTION_OPTION_TEXT",
            "COMMAND:IDX",
            "ERROR",
            "ERROR",
            "duplicate direction option."
        },
        {
            MessageId::IdxUnexpectedTokenText,
            "IDX_UNEXPECTED_TOKEN_TEXT",
            "COMMAND:IDX",
            "ERROR",
            "ERROR",
            "unexpected token '{token}'."
        },
        {
            MessageId::IdxBuildCreatedText,
            "IDX_BUILD_CREATED_TEXT",
            "COMMAND:IDX",
            "STATUS",
            "INFO",
            "Memory index {verb}: {tag}"
        },
        {
            MessageId::IdxExprLineText,
            "IDX_EXPR_LINE_TEXT",
            "COMMAND:IDX",
            "STATUS",
            "INFO",
            "  expr       : {value}"
        },
        {
            MessageId::IdxSortLineText,
            "IDX_SORT_LINE_TEXT",
            "COMMAND:IDX",
            "STATUS",
            "INFO",
            "  sort       : {value}"
        },
        {
            MessageId::IdxDirectionLineText,
            "IDX_DIRECTION_LINE_TEXT",
            "COMMAND:IDX",
            "STATUS",
            "INFO",
            "  direction  : {value}"
        },
        {
            MessageId::IdxRecordsLineText,
            "IDX_RECORDS_LINE_TEXT",
            "COMMAND:IDX",
            "STATUS",
            "INFO",
            "  records    : {indexed} indexed / {scanned} scanned"
        },
        {
            MessageId::IdxDeletedLineText,
            "IDX_DELETED_LINE_TEXT",
            "COMMAND:IDX",
            "STATUS",
            "INFO",
            "  deleted    : {count} skipped"
        },
        {
            MessageId::IdxBuildElapsedLineText,
            "IDX_BUILD_ELAPSED_LINE_TEXT",
            "COMMAND:IDX",
            "STATUS",
            "INFO",
            "  build      : {value}"
        },
        {
            MessageId::IdxSortElapsedLineText,
            "IDX_SORT_ELAPSED_LINE_TEXT",
            "COMMAND:IDX",
            "STATUS",
            "INFO",
            "  sort       : {value}"
        },
        {
            MessageId::IdxComparisonsLineText,
            "IDX_COMPARISONS_LINE_TEXT",
            "COMMAND:IDX",
            "STATUS",
            "INFO",
            "  compares   : {value}"
        },
        {
            MessageId::IdxSwapsLineText,
            "IDX_SWAPS_LINE_TEXT",
            "COMMAND:IDX",
            "STATUS",
            "INFO",
            "  swaps      : {value}"
        },
        {
            MessageId::IdxNoMemoryIndexesText,
            "IDX_NO_MEMORY_INDEXES_TEXT",
            "COMMAND:IDX",
            "STATUS",
            "INFO",
            "no memory indexes."
        },
        {
            MessageId::IdxMemoryIndexesTitle,
            "IDX_MEMORY_INDEXES_TITLE",
            "COMMAND:IDX",
            "STATUS",
            "INFO",
            "IDX memory indexes:"
        },
        {
            MessageId::IdxListHeaderLineText,
            "IDX_LIST_HEADER_LINE_TEXT",
            "COMMAND:IDX",
            "STATUS",
            "INFO",
            "TAG               EXPR        SORT      DIR   ENTRIES   BUILD"
        },
        {
            MessageId::IdxDropUsageText,
            "IDX_DROP_USAGE_TEXT",
            "COMMAND:IDX",
            "USAGE",
            "INFO",
            "Usage: IDX DROP <tag>|ALL"
        },
        {
            MessageId::IdxNoMemoryIndexesToDropText,
            "IDX_NO_MEMORY_INDEXES_TO_DROP_TEXT",
            "COMMAND:IDX",
            "STATUS",
            "INFO",
            "no memory indexes to drop."
        },
        {
            MessageId::IdxDroppedAllText,
            "IDX_DROPPED_ALL_TEXT",
            "COMMAND:IDX",
            "STATUS",
            "INFO",
            "dropped all memory indexes."
        },
        {
            MessageId::IdxDroppedMemoryIndexText,
            "IDX_DROPPED_MEMORY_INDEX_TEXT",
            "COMMAND:IDX",
            "STATUS",
            "INFO",
            "dropped memory index {tag}."
        },
        {
            MessageId::IdxMemoryIndexNotFoundText,
            "IDX_MEMORY_INDEX_NOT_FOUND_TEXT",
            "COMMAND:IDX",
            "ERROR",
            "ERROR",
            "memory index not found: {tag}"
        },
        {
            MessageId::IdxBuildUsageText,
            "IDX_BUILD_USAGE_TEXT",
            "COMMAND:IDX",
            "USAGE",
            "INFO",
            "Usage: IDX ON <field|#n> TAG <name> [SORT <algo>|<algo>] [ASC|DESC]"
        },
        {
            MessageId::IdxUnknownCommandText,
            "IDX_UNKNOWN_COMMAND_TEXT",
            "COMMAND:IDX",
            "ERROR",
            "ERROR",
            "unknown command '{command}'."
        },
        {
            MessageId::SkipUsageText,
            "SKIP_USAGE_TEXT",
            "COMMAND:SKIP",
            "USAGE",
            "INFO",
            "Usage:\n  SKIP\n  SKIP USAGE\n  SKIP <n>"
        },
        {
            MessageId::CountUsageText,
            "COUNT_USAGE_TEXT",
            "COMMAND:COUNT",
            "USAGE",
            "INFO",
            "Usage:\n  COUNT\n  COUNT USAGE\n  COUNT ALL\n  COUNT FOR <expr>\n  COUNT WHERE <expr>\n  COUNT <expr>\n  COUNT DELETED\n  COUNT NOT DELETED\n  COUNT !DELETED\nNotes:\n  - COUNT with no arguments counts the current logical rowset.\n  - With no open table, COUNT preserves existing behavior and prints 0.\n  - COUNT preserves the active cursor where possible after scans."
        },
        {
            MessageId::TopUsageText,
            "TOP_USAGE_TEXT",
            "COMMAND:TOP",
            "USAGE",
            "INFO",
            "Usage:\n  TOP\n  TOP USAGE"
        },
        {
            MessageId::BottomUsageText,
            "BOTTOM_USAGE_TEXT",
            "COMMAND:BOTTOM",
            "USAGE",
            "INFO",
            "Usage:\n  BOTTOM\n  BOTTOM USAGE"
        },
        {
            MessageId::FirstUsageText,
            "FIRST_USAGE_TEXT",
            "COMMAND:FIRST",
            "USAGE",
            "INFO",
            "Usage:\n  FIRST\n  FIRST USAGE"
        },
        {
            MessageId::LastUsageText,
            "LAST_USAGE_TEXT",
            "COMMAND:LAST",
            "USAGE",
            "INFO",
            "Usage:\n  LAST\n  LAST USAGE"
        },
        {
            MessageId::NextUsageText,
            "NEXT_USAGE_TEXT",
            "COMMAND:NEXT",
            "USAGE",
            "INFO",
            "Usage:\n  NEXT\n  NEXT USAGE"
        },
        {
            MessageId::PriorUsageText,
            "PRIOR_USAGE_TEXT",
            "COMMAND:PRIOR",
            "USAGE",
            "INFO",
            "Usage:\n  PRIOR\n  PRIOR USAGE"
        },
        {
            MessageId::UseMissingTableNameText,
            "USE_MISSING_TABLE_NAME_TEXT",
            "COMMAND:USE",
            "ERROR",
            "ERROR",
            "missing table name."
        },
        {
            MessageId::UseAlreadyOpenCurrentAreaText,
            "USE_ALREADY_OPEN_CURRENT_AREA_TEXT",
            "COMMAND:USE",
            "STATUS",
            "INFO",
            "'{file}' is already open in current area {area}."
        },
        {
            MessageId::UseAlreadyOpenOtherAreaText,
            "USE_ALREADY_OPEN_OTHER_AREA_TEXT",
            "COMMAND:USE",
            "STATUS",
            "INFO",
            "'{file}' is already open in area {area}. Close it first (e.g., SCHEMAS CLOSE {area})."
        },
        {
            MessageId::UseOpenFailedWithReasonText,
            "USE_OPEN_FAILED_WITH_REASON_TEXT",
            "COMMAND:USE",
            "ERROR",
            "ERROR",
            "Open failed: {reason}"
        },
        {
            MessageId::UseOpenFailedText,
            "USE_OPEN_FAILED_TEXT",
            "COMMAND:USE",
            "ERROR",
            "ERROR",
            "Open failed."
        },
        {
            MessageId::UseMemoAttachFailedText,
            "USE_MEMO_ATTACH_FAILED_TEXT",
            "COMMAND:USE",
            "ERROR",
            "ERROR",
            "memo attach failed: {reason}"
        },
        {
            MessageId::UseOpenedSummaryText,
            "USE_OPENED_SUMMARY_TEXT",
            "COMMAND:USE",
            "STATUS",
            "INFO",
            "Opened {name} ({version}) : Record count {count}"
        },
        {
            MessageId::UseValidIndexesLineText,
            "USE_VALID_INDEXES_LINE_TEXT",
            "COMMAND:USE",
            "STATUS",
            "INFO",
            "Valid Index/Indices   : {types}"
        },
        {
            MessageId::UseNoIndexSkippedText,
            "USE_NOINDEX_SKIPPED_TEXT",
            "COMMAND:USE",
            "STATUS",
            "INFO",
            "NOINDEX: auto-attach skipped (physical order)."
        },
        {
            MessageId::UseAutoAttachedOrderTagUniqueText,
            "USE_AUTO_ATTACHED_ORDER_TAG_UNIQUE_TEXT",
            "COMMAND:USE",
            "STATUS",
            "INFO",
            "Auto-attached order: {file} (tag: {tag} [UNIQUE])"
        },
        {
            MessageId::UseAutoAttachedOrderTagText,
            "USE_AUTO_ATTACHED_ORDER_TAG_TEXT",
            "COMMAND:USE",
            "STATUS",
            "INFO",
            "Auto-attached order: {file} (tag: {tag})"
        },
        {
            MessageId::UseAutoAttachedOrderText,
            "USE_AUTO_ATTACHED_ORDER_TEXT",
            "COMMAND:USE",
            "STATUS",
            "INFO",
            "Auto-attached order: {file}"
        },
        {
            MessageId::ContinueNoActiveLocateText,
            "CONTINUE_NO_ACTIVE_LOCATE_TEXT",
            "COMMAND:CONTINUE",
            "ERROR",
            "ERROR",
            "no active locate."
        },
        {
            MessageId::ContinueNotFoundText,
            "CONTINUE_NOT_FOUND_TEXT",
            "COMMAND:CONTINUE",
            "STATUS",
            "INFO",
            "not found."
        },
        {
            MessageId::ContinueFoundAtText,
            "CONTINUE_FOUND_AT_TEXT",
            "COMMAND:CONTINUE",
            "STATUS",
            "INFO",
            "Found at {recno}."
        },
        {
            MessageId::NavNoFileOpenText,
            "NAV_NO_FILE_OPEN_TEXT",
            "SUBSYSTEM:NAV",
            "ERROR",
            "ERROR",
            "no file open."
        },
        {
            MessageId::NavReadCurrentFailedText,
            "NAV_READ_CURRENT_FAILED_TEXT",
            "SUBSYSTEM:NAV",
            "ERROR",
            "ERROR",
            "failed to read record."
        },
        {
            MessageId::NavAtTopText,
            "NAV_AT_TOP_TEXT",
            "SUBSYSTEM:NAV",
            "STATUS",
            "INFO",
            "at top."
        },
        {
            MessageId::NavAtEndText,
            "NAV_AT_END_TEXT",
            "SUBSYSTEM:NAV",
            "STATUS",
            "INFO",
            "at end."
        },
        {
            MessageId::NavFailedText,
            "NAV_FAILED_TEXT",
            "SUBSYSTEM:NAV",
            "ERROR",
            "ERROR",
            "failed."
        },
        {
            MessageId::NavRecnoLine,
            "NAV_RECNO_LINE",
            "SUBSYSTEM:NAV",
            "STATUS",
            "INFO",
            "Recno: {recno}"
        },
        {
            MessageId::GoExpectedPositiveRecordNumberText,
            "GO_EXPECTED_POSITIVE_RECORD_NUMBER_TEXT",
            "COMMAND:GO",
            "ERROR",
            "ERROR",
            "expected a positive record number"
        },
        {
            MessageId::GoAreaQualifierNotSupportedYetText,
            "GO_AREA_QUALIFIER_NOT_SUPPORTED_YET_TEXT",
            "COMMAND:GO",
            "ERROR",
            "ERROR",
            "'IN <alias>' not supported yet (SELECT the area, then GO ...)"
        },
        {
            MessageId::GoUnrecognizedCommandFormText,
            "GO_UNRECOGNIZED_COMMAND_FORM_TEXT",
            "COMMAND:GO",
            "ERROR",
            "ERROR",
            "unrecognized form"
        },
        {
            MessageId::GpsUsageText,
            "GPS_USAGE_TEXT",
            "COMMAND:GPS",
            "USAGE",
            "INFO",
            "Usage:\n  GPS\n  GPS USAGE\nNotes:\n  - Reports area slot, table label, physical recno, and logical row.\n  - With no open table, GPS reports the no-table cursor state."
        },
        {
            MessageId::GpsNoTableCursorLineText,
            "GPS_NO_TABLE_CURSOR_LINE_TEXT",
            "COMMAND:GPS",
            "STATUS",
            "INFO",
            "Cursor: Area {area} of {occupied} ... No table open"
        },
        {
            MessageId::GpsCursorLineText,
            "GPS_CURSOR_LINE_TEXT",
            "COMMAND:GPS",
            "STATUS",
            "INFO",
            "Cursor: Area {area} of {occupied} ... Table {table} ... Physical Recno {recno}, Logical Row {logical_row}"
        },
        {
            MessageId::GpsUnnamedTableText,
            "GPS_UNNAMED_TABLE_TEXT",
            "COMMAND:GPS",
            "STATUS",
            "INFO",
            "(unnamed)"
        },
        {
            MessageId::CalcUsageText,
            "CALC_USAGE_TEXT",
            "COMMAND:CALC",
            "USAGE",
            "INFO",
            "Usage:\n  CALC USAGE             (Show this usage)\n  CALC <expr>            (Evaluate expression and print result)\n  CALC (<expr>)          (Outer parentheses are allowed)\n  CALC <field> = <expr>  (If <field> exists, delegate to CALCWRITE)\nExamples:\n  CALC 1 + 2\n  CALC DATE()\n  CALC UPPER(LNAME)\n  CALC BALANCE = BALANCE + 10\nNotes:\n  - CALC expression-only mode is read-only.\n  - CALC field-assignment mode mutates through CALCWRITE.\n  - Empty CALC preserves existing behavior and prints .F."
        },
        {
            MessageId::CalcWriteUsageText,
            "CALCWRITE_USAGE_TEXT",
            "COMMAND:CALCWRITE",
            "USAGE",
            "INFO",
            "Usage:\n  CALCWRITE USAGE\n  CALCWRITE <field> = <expr>\nExamples:\n  CALCWRITE BALANCE = BALANCE + 10\n  CALCWRITE LNAME = UPPER(LNAME)\n  CALCWRITE POSTED = TODAY\nNotes:\n  - CALCWRITE requires an open table and a current record.\n  - RHS expressions are evaluated with xexpr against the current area.\n  - Values are normalized and validated for the target field type.\n  - X64 memo fields update memo payloads and store memo object-id text.\n  - TABLE ON buffers changes and marks fields stale/dirty.\n  - TABLE OFF writes through DbArea::replaceFieldStored for index-safe mutation."
        },
        {
            MessageId::CalcWriteNoFileOpenText,
            "CALCWRITE_NO_FILE_OPEN_TEXT",
            "COMMAND:CALCWRITE",
            "ERROR",
            "ERROR",
            "no file open. Use: USE <table>"
        },
        {
            MessageId::CalcWriteUnknownFieldText,
            "CALCWRITE_UNKNOWN_FIELD_TEXT",
            "COMMAND:CALCWRITE",
            "ERROR",
            "ERROR",
            "unknown field '{field}'"
        },
        {
            MessageId::CalcWriteNoCurrentRecordText,
            "CALCWRITE_NO_CURRENT_RECORD_TEXT",
            "COMMAND:CALCWRITE",
            "ERROR",
            "ERROR",
            "no current record."
        },
        {
            MessageId::CalcWriteCannotDetermineCurrentAreaText,
            "CALCWRITE_CANNOT_DETERMINE_CURRENT_AREA_TEXT",
            "COMMAND:CALCWRITE",
            "ERROR",
            "ERROR",
            "cannot determine current area."
        },
        {
            MessageId::CalcWriteEvaluationFailedText,
            "CALCWRITE_EVALUATION_FAILED_TEXT",
            "COMMAND:CALCWRITE",
            "ERROR",
            "ERROR",
            "evaluation failed"
        },
        {
            MessageId::CalcWriteDetailText,
            "CALCWRITE_DETAIL_TEXT",
            "COMMAND:CALCWRITE",
            "ERROR",
            "ERROR",
            "{detail}"
        },
        {
            MessageId::CalcWriteBufferedFieldValueText,
            "CALCWRITE_BUFFERED_FIELD_VALUE_TEXT",
            "COMMAND:CALCWRITE",
            "STATUS",
            "INFO",
            "buffered {field} = {value} at rec {recno}."
        },
        {
            MessageId::CalcWriteBufferedFieldText,
            "CALCWRITE_BUFFERED_FIELD_TEXT",
            "COMMAND:CALCWRITE",
            "STATUS",
            "INFO",
            "buffered {field}."
        },
        {
            MessageId::CalcWriteWroteFieldValueText,
            "CALCWRITE_WROTE_FIELD_VALUE_TEXT",
            "COMMAND:CALCWRITE",
            "STATUS",
            "INFO",
            "wrote {field} = {value}"
        },
        {
            MessageId::ReplaceUsageText,
            "REPLACE_USAGE_TEXT",
            "COMMAND:REPLACE",
            "USAGE",
            "INFO",
            "Usage:\n  REPLACE USAGE\n  REPLACE <field_index> WITH <value>\n  REPLACE <field_name>  WITH <value>\nExamples:\n  REPLACE LNAME WITH \"Smith\"\n  REPLACE 3 WITH TODAY\nNotes:\n  - REPLACE requires an open table and a current record.\n  - RHS values are evaluated before validation/storage.\n  - X64 memo text is converted to stored memo object-id text.\n  - TABLE ON buffers field changes and marks fields stale/dirty.\n  - TABLE OFF writes immediately through DbArea storage."
        },
        {
            MessageId::ReplaceNoFileOpenText,
            "REPLACE_NO_FILE_OPEN_TEXT",
            "COMMAND:REPLACE",
            "ERROR",
            "ERROR",
            "no file open."
        },
        {
            MessageId::ReplaceFieldNotFoundText,
            "REPLACE_FIELD_NOT_FOUND_TEXT",
            "COMMAND:REPLACE",
            "ERROR",
            "ERROR",
            "field not found."
        },
        {
            MessageId::ReplaceNoCurrentRecordText,
            "REPLACE_NO_CURRENT_RECORD_TEXT",
            "COMMAND:REPLACE",
            "ERROR",
            "ERROR",
            "no current record."
        },
        {
            MessageId::ReplaceCannotDetermineCurrentAreaText,
            "REPLACE_CANNOT_DETERMINE_CURRENT_AREA_TEXT",
            "COMMAND:REPLACE",
            "ERROR",
            "ERROR",
            "cannot determine current area."
        },
        {
            MessageId::ReplaceDetailText,
            "REPLACE_DETAIL_TEXT",
            "COMMAND:REPLACE",
            "ERROR",
            "ERROR",
            "{detail}"
        },
        {
            MessageId::ReplaceBufferedFieldRecordText,
            "REPLACE_BUFFERED_FIELD_RECORD_TEXT",
            "COMMAND:REPLACE",
            "STATUS",
            "INFO",
            "buffered field #{field} at rec {recno}."
        },
        {
            MessageId::ReplaceReplacedFieldRecordText,
            "REPLACE_REPLACED_FIELD_RECORD_TEXT",
            "COMMAND:REPLACE",
            "STATUS",
            "INFO",
            "Replaced field #{field} at rec {recno}."
        },
        {
            MessageId::ReplaceWriteFailedDetailText,
            "REPLACE_WRITE_FAILED_DETAIL_TEXT",
            "COMMAND:REPLACE",
            "ERROR",
            "ERROR",
            "write failed ({detail})."
        },
        {
            MessageId::ReplaceWriteFailedText,
            "REPLACE_WRITE_FAILED_TEXT",
            "COMMAND:REPLACE",
            "ERROR",
            "ERROR",
            "write failed."
        },
        {
            MessageId::RollbackUsageText,
            "ROLLBACK_USAGE_TEXT",
            "COMMAND:ROLLBACK",
            "USAGE",
            "INFO",
            "Usage:\n  ROLLBACK USAGE\n  ROLLBACK\n  ROLLBACK ALL\nExamples:\n  ROLLBACK\n  ROLLBACK ALL\nNotes:\n  - ROLLBACK USAGE does not modify buffer state.\n  - ROLLBACK discards buffered/uncommitted table changes."
        },
        {
            MessageId::RollbackEngineUnavailableText,
            "ROLLBACK_ENGINE_UNAVAILABLE_TEXT",
            "COMMAND:ROLLBACK",
            "ERROR",
            "ERROR",
            "engine unavailable."
        },
        {
            MessageId::RollbackAllDiscardedText,
            "ROLLBACK_ALL_DISCARDED_TEXT",
            "COMMAND:ROLLBACK",
            "STATUS",
            "INFO",
            "discarded {changes} change(s) across {areas} area(s)."
        },
        {
            MessageId::RollbackCannotDetermineCurrentAreaText,
            "ROLLBACK_CANNOT_DETERMINE_CURRENT_AREA_TEXT",
            "COMMAND:ROLLBACK",
            "ERROR",
            "ERROR",
            "cannot determine current area."
        },
        {
            MessageId::RollbackDiscardedText,
            "ROLLBACK_DISCARDED_TEXT",
            "COMMAND:ROLLBACK",
            "STATUS",
            "INFO",
            "discarded {changes} change(s)."
        },
        {
            MessageId::DeleteUsageText,
            "DELETE_USAGE_TEXT",
            "COMMAND:DELETE",
            "USAGE",
            "INFO",
            "Usage:\n  DELETE USAGE\n  DELETE                         (delete current record)\n  DELETE ALL\n  DELETE REST\n  DELETE NEXT <n>\n  DELETE FOR <field> <op> <value>\nNotes:\n  - DELETE requires an open table except for DELETE USAGE.\n  - DELETE honors active SET FILTER in ALL/REST/NEXT/FOR scans.\n  - Direct-write mode updates active index backends best-effort."
        },
        {
            MessageId::DeleteIndexStaleWarningText,
            "DELETE_INDEX_STALE_WARNING_TEXT",
            "COMMAND:DELETE",
            "WARNING",
            "WARNING",
            "warning - active index/order may now be stale after {stage}. Rebuild/rebind indexes if needed."
        },
        {
            MessageId::DeleteNoTableOpenText,
            "DELETE_NO_TABLE_OPEN_TEXT",
            "COMMAND:DELETE",
            "ERROR",
            "ERROR",
            "No table is open. Use USE <file> first."
        },
        {
            MessageId::DeleteCountText,
            "DELETE_COUNT_TEXT",
            "COMMAND:DELETE",
            "STATUS",
            "INFO",
            "{count} deleted"
        },
        {
            MessageId::RecallUsageText,
            "RECALL_USAGE_TEXT",
            "COMMAND:RECALL",
            "USAGE",
            "INFO",
            "Usage:\n  RECALL USAGE\n  RECALL\n  RECALL ALL\n  RECALL REST\n  RECALL NEXT <n>\n  RECALL FOR <expr>\nExamples:\n  RECALL\n  RECALL ALL\n  RECALL REST\n  RECALL NEXT 10\n  RECALL FOR LNAME = \"SMITH\"\nNotes:\n  - RECALL USAGE does not require an open table.\n  - RECALL with no arguments recalls the current record.\n  - RECALL target selection is deleted-only."
        },
        {
            MessageId::RecallIndexStaleWarningText,
            "RECALL_INDEX_STALE_WARNING_TEXT",
            "COMMAND:RECALL",
            "WARNING",
            "WARNING",
            "warning - active index/order may now be stale after index update. Rebuild/rebind indexes if needed."
        },
        {
            MessageId::RecallNoTableOpenText,
            "RECALL_NO_TABLE_OPEN_TEXT",
            "COMMAND:RECALL",
            "ERROR",
            "ERROR",
            "No table is open. Use USE <file> first."
        },
        {
            MessageId::RecallCountText,
            "RECALL_COUNT_TEXT",
            "COMMAND:RECALL",
            "STATUS",
            "INFO",
            "{count} recalled"
        },
        {
            MessageId::RecallNextUsageText,
            "RECALL_NEXT_USAGE_TEXT",
            "COMMAND:RECALL",
            "USAGE",
            "INFO",
            "Usage: RECALL NEXT <n>"
        },
        {
            MessageId::EraseUsageText,
            "ERASE_USAGE_TEXT",
            "COMMAND:ERASE",
            "USAGE",
            "INFO",
            "Usage:\n  ERASE USAGE\n  ERASE <table> [CONFIRM]\n  ERASE TABLE <table> [CONFIRM]\nExamples:\n  ERASE TABLE clients\n  ERASE TABLE clients CONFIRM\n  ERASE students.dbf CONFIRM\nNotes:\n  - ERASE USAGE does not inspect or delete files.\n  - Physically deletes <table>.dbf and known same-stem sidecars.\n  - Without CONFIRM, performs a dry-run and prints what would be deleted.\n  - CONFIRM performs deletion."
        },
        {
            MessageId::EraseTableNotFoundText,
            "ERASE_TABLE_NOT_FOUND_TEXT",
            "COMMAND:ERASE",
            "ERROR",
            "ERROR",
            "Table not found: {table}"
        },
        {
            MessageId::EraseNothingToDeleteText,
            "ERASE_NOTHING_TO_DELETE_TEXT",
            "COMMAND:ERASE",
            "STATUS",
            "INFO",
            "Nothing to delete for: {path}"
        },
        {
            MessageId::EraseDryRunHeaderText,
            "ERASE_DRY_RUN_HEADER_TEXT",
            "COMMAND:ERASE",
            "STATUS",
            "INFO",
            "would delete {count} file(s) for table: {table}"
        },
        {
            MessageId::EraseReRunConfirmText,
            "ERASE_RERUN_CONFIRM_TEXT",
            "COMMAND:ERASE",
            "STATUS",
            "INFO",
            "Re-run with CONFIRM to perform deletion."
        },
        {
            MessageId::EraseDeletingHeaderText,
            "ERASE_DELETING_HEADER_TEXT",
            "COMMAND:ERASE",
            "STATUS",
            "INFO",
            "deleting {count} file(s) for table: {table}"
        },
        {
            MessageId::EraseFailedLineText,
            "ERASE_FAILED_LINE_TEXT",
            "COMMAND:ERASE",
            "WARNING",
            "WARNING",
            "  FAILED: {file}  ({error})"
        },
        {
            MessageId::EraseDeletedEntriesLineText,
            "ERASE_DELETED_ENTRIES_LINE_TEXT",
            "COMMAND:ERASE",
            "STATUS",
            "INFO",
            "  Deleted: {file}  ({entries} entries)"
        },
        {
            MessageId::EraseDeletedLineText,
            "ERASE_DELETED_LINE_TEXT",
            "COMMAND:ERASE",
            "STATUS",
            "INFO",
            "  Deleted: {file}"
        },
        {
            MessageId::EraseCompleteText,
            "ERASE_COMPLETE_TEXT",
            "COMMAND:ERASE",
            "STATUS",
            "INFO",
            "ERASE complete. Deleted: {deleted}, Failed: {failed}"
        },
        {
            MessageId::ScriptUnableToOpenText,
            "SCRIPT_UNABLE_TO_OPEN_TEXT",
            "RUNTIME:SCRIPT",
            "ERROR",
            "ERROR",
            "unable to open {file}"
        },
        {
            MessageId::ScriptLineErrorText,
            "SCRIPT_LINE_ERROR_TEXT",
            "RUNTIME:SCRIPT",
            "ERROR",
            "ERROR",
            "{file}:{line}: {detail}"
        },
        {
            MessageId::ImportUsageText,
            "IMPORT_USAGE_TEXT",
            "COMMAND:IMPORT",
            "USAGE",
            "INFO",
            "Usage:\n  IMPORT USAGE\n  IMPORT <csvfile>\nNotes:\n  - IMPORT requires an open table except for IMPORT USAGE.\n  - CSV headers are matched to field names case-insensitively.\n  - IMPORT appends records to the current table."
        },
        {
            MessageId::ImportNoFileOpenText,
            "IMPORT_NO_FILE_OPEN_TEXT",
            "COMMAND:IMPORT",
            "ERROR",
            "ERROR",
            "No file open"
        },
        {
            MessageId::ImportCannotOpenText,
            "IMPORT_CANNOT_OPEN_TEXT",
            "COMMAND:IMPORT",
            "ERROR",
            "ERROR",
            "Cannot open {file} for read."
        },
        {
            MessageId::ImportEmptyCsvText,
            "IMPORT_EMPTY_CSV_TEXT",
            "COMMAND:IMPORT",
            "ERROR",
            "ERROR",
            "Empty CSV."
        },
        {
            MessageId::ImportAppendFailedText,
            "IMPORT_APPEND_FAILED_TEXT",
            "COMMAND:IMPORT",
            "ERROR",
            "ERROR",
            "Append failed."
        },
        {
            MessageId::ImportStoreErrorText,
            "IMPORT_STORE_ERROR_TEXT",
            "COMMAND:IMPORT",
            "ERROR",
            "ERROR",
            "{detail} at rec {recno}, column {column}."
        },
        {
            MessageId::ImportWriteFailedText,
            "IMPORT_WRITE_FAILED_TEXT",
            "COMMAND:IMPORT",
            "ERROR",
            "ERROR",
            "Write failed at rec {recno}"
        },
        {
            MessageId::ImportedCountText,
            "IMPORTED_COUNT_TEXT",
            "COMMAND:IMPORT",
            "STATUS",
            "INFO",
            "Imported {count} records from {file}"
        },
        {
            MessageId::ExportUsageText,
            "EXPORT_USAGE_TEXT",
            "COMMAND:EXPORT",
            "USAGE",
            "INFO",
            "Usage:\n  EXPORT USAGE\n  EXPORT [TO] <file> [CSV|PIPE]\n  EXPORT <open-area-token> TO <file> [CSV|PIPE]\nNotes:\n  - EXPORT writes the current table as CSV by default.\n  - EXPORT <open-area-token> TO <file> writes an already-open named work area.\n  - Named EXPORT does not auto-open tables from disk.\n  - PIPE uses | as the delimiter.\n  - A missing extension is added automatically (.csv for CSV, .txt for PIPE).\n  - EXPORT honors the active SET FILTER for the exported area.\n  - EXPORT requires an open table except for EXPORT USAGE."
        },
        {
            MessageId::ExportAmbiguousTokenText,
            "EXPORT_AMBIGUOUS_TOKEN_TEXT",
            "COMMAND:EXPORT",
            "ERROR",
            "ERROR",
            "ambiguous area token '{token}'{matches}"
        },
        {
            MessageId::ExportUnableToOpenText,
            "EXPORT_UNABLE_TO_OPEN_TEXT",
            "COMMAND:EXPORT",
            "ERROR",
            "ERROR",
            "Unable to open {dest} for write"
        },
        {
            MessageId::ExportWriteFailedText,
            "EXPORT_WRITE_FAILED_TEXT",
            "COMMAND:EXPORT",
            "ERROR",
            "ERROR",
            "write failed while exporting {dest}"
        },
        {
            MessageId::ExportCursorRestoreWarningText,
            "EXPORT_CURSOR_RESTORE_WARNING_TEXT",
            "COMMAND:EXPORT",
            "WARNING",
            "WARNING",
            "export completed but cursor restore reported: {detail}"
        },
        {
            MessageId::ExportedCountText,
            "EXPORTED_COUNT_TEXT",
            "COMMAND:EXPORT",
            "STATUS",
            "INFO",
            "Exported {count} records to {dest}"
        },
        {
            MessageId::ExportNoFileOpenText,
            "EXPORT_NO_FILE_OPEN_TEXT",
            "COMMAND:EXPORT",
            "ERROR",
            "ERROR",
            "No file open"
        },
        {
            MessageId::ExportErrorDetailText,
            "EXPORT_ERROR_DETAIL_TEXT",
            "COMMAND:EXPORT",
            "ERROR",
            "ERROR",
            "{detail}"
        },
        {
            MessageId::ExportNoOpenAreaMatchText,
            "EXPORT_NO_OPEN_AREA_MATCH_TEXT",
            "COMMAND:EXPORT",
            "ERROR",
            "ERROR",
            "no open area matches '{token}'"
        },
        {
            MessageId::CreateUsageText,
            "CREATE_USAGE_TEXT",
            "COMMAND:CREATE",
            "USAGE",
            "INFO",
            "Usage:\n  CREATE USAGE\n  CREATE <name> (<field> <type>[, ...])\n  CREATE MSDOS <name> (<field> <type>[, ...])\n  CREATE DBASE <name> (<field> <type>[, ...])\n  CREATE FOX26 <name> (<field> <type>[, ...])\n  CREATE FOXPRO <name> (<field> <type>[, ...])\n  CREATE VFP <name> (<field> <type>[, ...])\n  CREATE X64 <name> (<field> <type>[, ...])\nTypes:\n  XBASE currently implemented: C(n), N(n[,d]), F(n[,d]), D, L, M\n  VFP/X64 currently implemented: C(n), N(n[,d]), F(n[,d]), D, L, M, I, B, Y, T\nExamples:\n  CREATE students (sid N(6), lname C(20), fname C(15))\n  CREATE X64 teachers (teacher_id I, full_name C(80), bio M)\nNotes:\n  - CREATE writes a DBF file under the configured DBF path slot for relative names.\n  - CREATE clears active order state and closes the current area before writing.\n  - CREATE opens the created table after a successful write.\n  - M fields trigger automatic memo attach after opening.\n  - X64 CREATE may use descriptor fallback tokens for DBF/VFP descriptor safety."
        },
        {
            MessageId::CreateDetailText,
            "CREATE_DETAIL_TEXT",
            "COMMAND:CREATE",
            "ERROR",
            "ERROR",
            "{detail}"
        },
        {
            MessageId::CreateFailedText,
            "CREATE_FAILED_TEXT",
            "COMMAND:CREATE",
            "ERROR",
            "ERROR",
            "CREATE failed: {detail}"
        },
        {
            MessageId::CreateReopenFailedDetailText,
            "CREATE_REOPEN_FAILED_DETAIL_TEXT",
            "COMMAND:CREATE",
            "ERROR",
            "ERROR",
            "CREATE failed: file written but could not reopen table: {detail}"
        },
        {
            MessageId::CreateReopenFailedText,
            "CREATE_REOPEN_FAILED_TEXT",
            "COMMAND:CREATE",
            "ERROR",
            "ERROR",
            "CREATE failed: file written but could not reopen table."
        },
        {
            MessageId::CreateMemoAttachFailedText,
            "CREATE_MEMO_ATTACH_FAILED_TEXT",
            "COMMAND:CREATE",
            "ERROR",
            "ERROR",
            "Memo attach failed: {detail}"
        },
        {
            MessageId::CreatedText,
            "CREATED_TEXT",
            "COMMAND:CREATE",
            "STATUS",
            "INFO",
            "Created {path} [{flavor}]{memo}"
        },
        {
            MessageId::CreateOpenedText,
            "CREATE_OPENED_TEXT",
            "COMMAND:CREATE",
            "STATUS",
            "INFO",
            "Opened {file} with {count} records."
        },
        {
            MessageId::CreateX64NameTooLongWarningText,
            "CREATE_X64_NAME_TOO_LONG_WARNING_TEXT",
            "COMMAND:CREATE",
            "WARNING",
            "WARNING",
            "field name '{name}' exceeds current x64 logical field-name length {limit}; it will not be stored as an authoritative x64 metadata name; descriptor fallback token is '{token}'{suffix}."
        },
        {
            MessageId::CreateX64FallbackTokenWarningText,
            "CREATE_X64_FALLBACK_TOKEN_WARNING_TEXT",
            "COMMAND:CREATE",
            "WARNING",
            "WARNING",
            "field name '{name}' uses DBF/VFP descriptor fallback token '{token}'; authoritative x64 metadata name will be preserved{suffix}."
        },
        { MessageId::ZapUsageText, "ZAP_USAGE_TEXT", "COMMAND:ZAP", "USAGE", "INFO",
          "Usage:\n  ZAP USAGE\n  ZAP\nExamples:\n  ZAP\nNotes:\n  - ZAP USAGE does not require an open table.\n  - ZAP removes all records from the current non-memo DBF while preserving structure.\n  - ZAP closes the table on success; reopen with USE <table>.\n  - Index containers must be rebuilt/rebound after ZAP." },
        { MessageId::ZapNoTableOpenText, "ZAP_NO_TABLE_OPEN_TEXT", "COMMAND:ZAP", "ERROR", "ERROR", "No table open" },
        { MessageId::ZapCannotZapMemoText, "ZAP_CANNOT_ZAP_MEMO_TEXT", "COMMAND:ZAP", "ERROR", "ERROR", "Cannot zap memo table (memo block handling not implemented)." },
        { MessageId::ZapFileNotFoundText, "ZAP_FILE_NOT_FOUND_TEXT", "COMMAND:ZAP", "ERROR", "ERROR", "File not found: {path}" },
        { MessageId::ZapZappingText, "ZAP_ZAPPING_TEXT", "COMMAND:ZAP", "STATUS", "INFO", "Zapping: {path}" },
        { MessageId::ZapCannotOpenReadText, "ZAP_CANNOT_OPEN_READ_TEXT", "COMMAND:ZAP", "ERROR", "ERROR", "Cannot open file for reading" },
        { MessageId::ZapFailedReadHeaderText, "ZAP_FAILED_READ_HEADER_TEXT", "COMMAND:ZAP", "ERROR", "ERROR", "Failed to read header" },
        { MessageId::ZapInvalidHeaderLenText, "ZAP_INVALID_HEADER_LEN_TEXT", "COMMAND:ZAP", "ERROR", "ERROR", "Invalid header length ({len})" },
        { MessageId::ZapFailedReadHeaderBlockText, "ZAP_FAILED_READ_HEADER_BLOCK_TEXT", "COMMAND:ZAP", "ERROR", "ERROR", "Failed to read full header block" },
        { MessageId::ZapHeaderNoTerminatorText, "ZAP_HEADER_NO_TERMINATOR_TEXT", "COMMAND:ZAP", "WARNING", "WARNING", "header does not end with 0x0D terminator" },
        { MessageId::ZapCannotCreateTempText, "ZAP_CANNOT_CREATE_TEMP_TEXT", "COMMAND:ZAP", "ERROR", "ERROR", "Cannot create temporary file: {path}" },
        { MessageId::ZapFailedWriteHeaderText, "ZAP_FAILED_WRITE_HEADER_TEXT", "COMMAND:ZAP", "ERROR", "ERROR", "Failed writing header to temp file" },
        { MessageId::ZapFailedWriteEofText, "ZAP_FAILED_WRITE_EOF_TEXT", "COMMAND:ZAP", "ERROR", "ERROR", "Failed writing EOF marker" },
        { MessageId::ZapFailedRenameBackupText, "ZAP_FAILED_RENAME_BACKUP_TEXT", "COMMAND:ZAP", "ERROR", "ERROR", "Failed to rename original to backup: {detail}" },
        { MessageId::ZapFailedReplaceText, "ZAP_FAILED_REPLACE_TEXT", "COMMAND:ZAP", "ERROR", "ERROR", "Failed to replace original: {detail}" },
        { MessageId::ZapRollbackFailedText, "ZAP_ROLLBACK_FAILED_TEXT", "COMMAND:ZAP", "ERROR", "ERROR", "  Rollback also failed — manual recovery needed!" },
        { MessageId::ZapOriginalRestoredText, "ZAP_ORIGINAL_RESTORED_TEXT", "COMMAND:ZAP", "STATUS", "INFO", "  Original restored." },
        { MessageId::ZapCnxMarkedDirtyText, "ZAP_CNX_MARKED_DIRTY_TEXT", "COMMAND:ZAP", "STATUS", "INFO", "CNX marked dirty (reindex recommended): {file}" },
        { MessageId::ZapCnxCouldNotMarkText, "ZAP_CNX_COULD_NOT_MARK_TEXT", "COMMAND:ZAP", "WARNING", "WARNING", "note: CNX found but could not mark dirty" },
        { MessageId::ZapIndexRebuildText, "ZAP_INDEX_REBUILD_TEXT", "COMMAND:ZAP", "STATUS", "INFO", "note: index container should be rebuilt: {file}" },
        { MessageId::ZapOrderRebuildText, "ZAP_ORDER_REBUILD_TEXT", "COMMAND:ZAP", "STATUS", "INFO", "note: order container should be rebuilt: {file}" },
        { MessageId::ZapCompleteText, "ZAP_COMPLETE_TEXT", "COMMAND:ZAP", "STATUS", "INFO", "ZAP complete. All records removed." },
        { MessageId::ZapReadyForUseText, "ZAP_READY_FOR_USE_TEXT", "COMMAND:ZAP", "STATUS", "INFO", "{file} ready for use." },
        { MessageId::ZapSidecarsNoneText, "ZAP_SIDECARS_NONE_TEXT", "COMMAND:ZAP", "STATUS", "INFO", "Sidecar(s): none." },
        { MessageId::ZapReopenText, "ZAP_REOPEN_TEXT", "COMMAND:ZAP", "STATUS", "INFO", "Table is closed. Reopen with: USE {stem}" },
        { MessageId::ZapRebuildIndexesText, "ZAP_REBUILD_INDEXES_TEXT", "COMMAND:ZAP", "STATUS", "INFO", "Rebuild/rebind indexes as needed." },
        { MessageId::PackUsageText, "PACK_USAGE_TEXT", "COMMAND:PACK", "USAGE", "INFO", "Usage:\n  PACK USAGE\n  PACK\nExamples:\n  PACK\nNotes:\n  - PACK USAGE does not require an open table and does not rewrite files.\n  - PACK physically removes deleted records from the current DBF.\n  - PACK closes the table on success; reopen with USE <table>.\n  - PACK supports x64 M(8) memo tables by rebuilding DBF and DTX together.\n  - Legacy memo tables are refused.\n  - Index containers must be rebuilt/rebound after PACK." },
        { MessageId::PackNoTableOpenText, "PACK_NO_TABLE_OPEN_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "No table open" },
        { MessageId::PackMemoNotSupportedText, "PACK_MEMO_NOT_SUPPORTED_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Memo tables not supported yet (legacy memo block remapping missing)." },
        { MessageId::PackFileNotFoundText, "PACK_FILE_NOT_FOUND_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "File not found on disk: {path}" },
        { MessageId::PackDetailText, "PACK_DETAIL_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "{detail}" },
        { MessageId::PackAbortedText, "PACK_ABORTED_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "operation aborted. Table remains closed." },
        { MessageId::PackCannotOpenReadText, "PACK_CANNOT_OPEN_READ_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Cannot open original file for reading" },
        { MessageId::PackFailedRead32Text, "PACK_FAILED_READ_32_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Failed to read first 32 bytes of header" },
        { MessageId::PackInvalidHeaderText, "PACK_INVALID_HEADER_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Invalid DBF header (headerLen={hl}, recordLen={rl})" },
        { MessageId::PackFailedReadHeaderBlockText, "PACK_FAILED_READ_HEADER_BLOCK_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Failed to read full header block" },
        { MessageId::PackHeaderNoTerminatorText, "PACK_HEADER_NO_TERMINATOR_TEXT", "COMMAND:PACK", "WARNING", "WARNING", "header does not end with 0x0D terminator byte" },
        { MessageId::PackHeaderCountMismatchText, "PACK_HEADER_COUNT_MISMATCH_TEXT", "COMMAND:PACK", "WARNING", "WARNING", "Warning — header record count ({orig}) does not match physical record count ({actual}); using safe count {safe}." },
        { MessageId::PackCannotCreateTempText, "PACK_CANNOT_CREATE_TEMP_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Cannot create temporary file: {path}" },
        { MessageId::PackFailedWriteInitialHeaderText, "PACK_FAILED_WRITE_INITIAL_HEADER_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Failed to write initial header" },
        { MessageId::PackCannotReopenText, "PACK_CANNOT_REOPEN_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Cannot reopen original file for record copy" },
        { MessageId::PackFailedReadRecordsText, "PACK_FAILED_READ_RECORDS_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Failed while reading source records" },
        { MessageId::PackFailedWriteRecordsText, "PACK_FAILED_WRITE_RECORDS_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Failed while writing packed records" },
        { MessageId::PackFailedWriteEofText, "PACK_FAILED_WRITE_EOF_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Failed writing EOF marker" },
        { MessageId::PackFailedRewriteHeaderText, "PACK_FAILED_REWRITE_HEADER_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Failed rewriting final header" },
        { MessageId::PackMemoNotFoundText, "PACK_MEMO_NOT_FOUND_TEXT", "COMMAND:PACK", "WARNING", "WARNING", "warning — memo object {id} not found, clearing reference" },
        { MessageId::PackFailedRenameBackupText, "PACK_FAILED_RENAME_BACKUP_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Failed to rename original to backup: {detail}" },
        { MessageId::PackFailedReplaceText, "PACK_FAILED_REPLACE_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Failed to replace original with packed file: {detail}" },
        { MessageId::PackRollbackFailedText, "PACK_ROLLBACK_FAILED_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "  Rollback also failed: {detail} — manual recovery may be needed!" },
        { MessageId::PackOriginalRestoredText, "PACK_ORIGINAL_RESTORED_TEXT", "COMMAND:PACK", "STATUS", "INFO", "  Original file restored." },
        { MessageId::PackFailedRenameDbfBackupText, "PACK_FAILED_RENAME_DBF_BACKUP_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Failed to rename original DBF to backup: {detail}" },
        { MessageId::PackFailedRenameDtxBackupText, "PACK_FAILED_RENAME_DTX_BACKUP_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Failed to rename original DTX to backup: {detail}" },
        { MessageId::PackFailedReplaceDbfText, "PACK_FAILED_REPLACE_DBF_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Failed to replace DBF with packed DBF: {detail}" },
        { MessageId::PackFailedReplaceDtxText, "PACK_FAILED_REPLACE_DTX_TEXT", "COMMAND:PACK", "ERROR", "ERROR", "Failed to replace DTX with packed DTX: {detail}" },
        { MessageId::PackCnxMarkedDirtyText, "PACK_CNX_MARKED_DIRTY_TEXT", "COMMAND:PACK", "STATUS", "INFO", "CNX marked dirty (reindex recommended): {file}" },
        { MessageId::PackCnxCouldNotMarkText, "PACK_CNX_COULD_NOT_MARK_TEXT", "COMMAND:PACK", "WARNING", "WARNING", "note: CNX found but could not mark dirty" },
        { MessageId::PackIndexRebuildText, "PACK_INDEX_REBUILD_TEXT", "COMMAND:PACK", "STATUS", "INFO", "note: index container should be rebuilt: {file}" },
        { MessageId::PackOrderRebuildText, "PACK_ORDER_REBUILD_TEXT", "COMMAND:PACK", "STATUS", "INFO", "note: order container should be rebuilt: {file}" },
        { MessageId::PackCompleteText, "PACK_COMPLETE_TEXT", "COMMAND:PACK", "STATUS", "INFO", "PACK complete. Kept {kept} record(s), removed {deleted} deleted record(s)." },
        { MessageId::PackReadyForUseText, "PACK_READY_FOR_USE_TEXT", "COMMAND:PACK", "STATUS", "INFO", "{file} ready for use." },
        { MessageId::PackSidecarsRebuiltText, "PACK_SIDECARS_REBUILT_TEXT", "COMMAND:PACK", "STATUS", "INFO", "Sidecar(s): DBF and DTX rebuilt and synchronized." },
        { MessageId::PackSidecarsNoneText, "PACK_SIDECARS_NONE_TEXT", "COMMAND:PACK", "STATUS", "INFO", "Sidecar(s): none." },
        { MessageId::PackReopenText, "PACK_REOPEN_TEXT", "COMMAND:PACK", "STATUS", "INFO", "Table is closed. Reopen with: USE {stem}" },
        { MessageId::PackRebuildIndexesText, "PACK_REBUILD_INDEXES_TEXT", "COMMAND:PACK", "STATUS", "INFO", "Rebuild/rebind indexes as needed." },
        { MessageId::CopyUsageText, "COPY_USAGE_TEXT", "COMMAND:COPY", "USAGE", "INFO", "Usage:\n  COPY USAGE\n  COPY TO <DBFNAME> [WITH SIDECARS] [OVERWRITE]\n  COPY TO <DBFNAME> AS <MSDOS|DBASE|FOX26|FOXPRO|VFP|X64> [OVERWRITE]\n  COPY TO <DBFNAME> AS X64 VECTOR [OVERWRITE]\n  COPY FILE <SRC> TO <DST> [OVERWRITE]\n\nExamples:\n  COPY TO students_copy\n  COPY TO students_x64 AS X64 VECTOR OVERWRITE\n  COPY TO students_vfp AS VFP\n  COPY TO students_backup WITH SIDECARS OVERWRITE\n  COPY FILE source.txt TO tmp\\source_copy.txt OVERWRITE\n\nNotes:\n  - COPY USAGE prints usage and does not require an open table.\n  - COPY TO <name>                 : binary copy of the current DBF\n  - COPY TO <name> AS <flavor>     : logical table copy/conversion\n  - COPY TO <name> AS X64 VECTOR   : one-step copy from any open table to x64 vector form\n  - VECTOR is target-driven and is valid only with AS X64\n  - AS X64 controls output format only; the destination path is honored\n  - AS VFP/FOX/MSDOS writes free-table 10-byte descriptor field names\n  - COPY AS free-table fails if 10-byte descriptor names would collide\n  - WITH SIDECARS applies to binary COPY TO only\n  - OVERWRITE is required when the destination already exists\n  - x64 output still writes .dbf for now (no .dbfx yet)\n\nSIDECARS (if present next to the DBF): .inx .cnx .dtx .dti.json" },
        { MessageId::CopySidecarFailedText, "COPY_SIDECAR_FAILED_TEXT", "COMMAND:COPY", "ERROR", "ERROR", "COPY SIDECAR failed: {detail}" },
        { MessageId::CopySidecarsNoneText, "COPY_SIDECARS_NONE_TEXT", "COMMAND:COPY", "STATUS", "INFO", "COPY SIDECARS: none found." },
        { MessageId::CopySidecarsFoundText, "COPY_SIDECARS_FOUND_TEXT", "COMMAND:COPY", "STATUS", "INFO", "COPY SIDECARS: found {found}, copied {copied}{failed}." },
        { MessageId::CopyWarningDetailText, "COPY_WARNING_DETAIL_TEXT", "COMMAND:COPY", "WARNING", "WARNING", "{detail}" },
        { MessageId::CopyDetailText, "COPY_DETAIL_TEXT", "COMMAND:COPY", "ERROR", "ERROR", "{detail}" },
        { MessageId::CopiedFileText, "COPIED_FILE_TEXT", "COMMAND:COPY", "STATUS", "INFO", "Copied file to {dst}" },
        { MessageId::CopyFileFailedText, "COPY_FILE_FAILED_TEXT", "COMMAND:COPY", "ERROR", "ERROR", "COPY FILE failed: {detail}" },
        { MessageId::CopyToNoFileOpenText, "COPY_TO_NO_FILE_OPEN_TEXT", "COMMAND:COPY", "ERROR", "ERROR", "COPY TO: no file open." },
        { MessageId::CopyAsUnexpectedTokenText, "COPY_AS_UNEXPECTED_TOKEN_TEXT", "COMMAND:COPY", "ERROR", "ERROR", "COPY TO AS failed: unexpected token between destination and AS: '{token}'" },
        { MessageId::CopyAsUseHintText, "COPY_AS_USE_HINT_TEXT", "COMMAND:COPY", "STATUS", "INFO", "Use: COPY TO <destination> AS <flavor> [VECTOR] [OVERWRITE]" },
        { MessageId::CopyAsUnknownFlavorText, "COPY_AS_UNKNOWN_FLAVOR_TEXT", "COMMAND:COPY", "ERROR", "ERROR", "COPY TO AS failed: unknown flavor '{flavor}'" },
        { MessageId::CopyAsSidecarsIgnoredText, "COPY_AS_SIDECARS_IGNORED_TEXT", "COMMAND:COPY", "STATUS", "INFO", "COPY TO AS: WITH SIDECARS ignored for logical conversion." },
        { MessageId::CopyAsVectorPolicyText, "COPY_AS_VECTOR_POLICY_TEXT", "COMMAND:COPY", "STATUS", "INFO", "COPY TO AS X64 VECTOR: using current x64 vector metadata policy." },
        { MessageId::CopyAsFailedText, "COPY_AS_FAILED_TEXT", "COMMAND:COPY", "ERROR", "ERROR", "COPY TO AS failed: {detail}" },
        { MessageId::CopiedTableText, "COPIED_TABLE_TEXT", "COMMAND:COPY", "STATUS", "INFO", "Copied table to {dst} [{flavor}]{vector}" },
        { MessageId::CopyToFailedText, "COPY_TO_FAILED_TEXT", "COMMAND:COPY", "ERROR", "ERROR", "COPY TO failed: {detail}" },
        { MessageId::CopiedDbfText, "COPIED_DBF_TEXT", "COMMAND:COPY", "STATUS", "INFO", "Copied DBF to {dst}" },
        { MessageId::CommitUsageText, "COMMIT_USAGE_TEXT", "COMMAND:COMMIT", "USAGE", "INFO", "Usage:\n  COMMIT USAGE\n  COMMIT\n  COMMIT ALL\n  COMMIT MANUAL\n  COMMIT INTERACTIVE\n  COMMIT AUTO\n  COMMIT ALL MANUAL\n  COMMIT ALL INTERACTIVE\n  COMMIT ALL AUTO\nNotes:\n  - COMMIT applies buffered TABLE changes with locking at commit time.\n  - COMMIT ALL applies all open buffered areas.\n  - CDX/LMDB rebuilds are intentionally not performed by COMMIT." },
        { MessageId::CommitRecLockedText, "COMMIT_REC_LOCKED_TEXT", "COMMAND:COMMIT", "ERROR", "ERROR", "rec {rn} locked ({detail})" },
        { MessageId::CommitNoActiveOrderText, "COMMIT_NO_ACTIVE_ORDER_TEXT", "COMMAND:COMMIT", "STATUS", "INFO", "no active order; index rebuild skipped." },
        { MessageId::CommitCdxSkippedText, "COMMIT_CDX_SKIPPED_TEXT", "COMMAND:COMMIT", "STATUS", "INFO", "CDX/LMDB rebuild skipped{tag}; runtime mutation hooks own index updates." },
        { MessageId::CommitRebuildingCnxText, "COMMIT_REBUILDING_CNX_TEXT", "COMMAND:COMMIT", "STATUS", "INFO", "rebuilding CNX..." },
        { MessageId::CommitCnxNotClearedText, "COMMIT_CNX_NOT_CLEARED_TEXT", "COMMAND:COMMIT", "ERROR", "ERROR", "CNX rebuild did not clear stale state." },
        { MessageId::CommitReindexingText, "COMMIT_REINDEXING_TEXT", "COMMAND:COMMIT", "STATUS", "INFO", "reindexing INX/IDX..." },
        { MessageId::CommitReindexNotClearedText, "COMMIT_REINDEX_NOT_CLEARED_TEXT", "COMMAND:COMMIT", "ERROR", "ERROR", "INX/IDX reindex did not clear stale state." },
        { MessageId::CommitNoChangesText, "COMMIT_NO_CHANGES_TEXT", "COMMAND:COMMIT", "STATUS", "INFO", "no changes in buffer." },
        { MessageId::CommitPartialRemainingText, "COMMIT_PARTIAL_REMAINING_TEXT", "COMMAND:COMMIT", "WARNING", "WARNING", "partial. OK={ok} FAIL={fail} (remaining buffered)" },
        { MessageId::CommitPartialText, "COMMIT_PARTIAL_TEXT", "COMMAND:COMMIT", "WARNING", "WARNING", "partial. OK={ok} FAIL={fail}." },
        { MessageId::CommitMemoFlushFailedText, "COMMIT_MEMO_FLUSH_FAILED_TEXT", "COMMAND:COMMIT", "ERROR", "ERROR", "failed during memo flush{detail}; buffer retained for retry. DBF writes may already have occurred." },
        { MessageId::CommitIndexFinalizeFailedText, "COMMIT_INDEX_FINALIZE_FAILED_TEXT", "COMMAND:COMMIT", "ERROR", "ERROR", "failed during index finalization; buffer retained for retry. DBF and memo writes may already have occurred." },
        { MessageId::CommitJournalFinalizeFailedText, "COMMIT_JOURNAL_FINALIZE_FAILED_TEXT", "COMMAND:COMMIT", "ERROR", "ERROR", "failed during journal finalization; buffer retained for retry." },
        { MessageId::CommitCompleteText, "COMMIT_COMPLETE_TEXT", "COMMAND:COMMIT", "STATUS", "INFO", "complete. ({ok} recs)" },
        { MessageId::CommitEngineUnavailableText, "COMMIT_ENGINE_UNAVAILABLE_TEXT", "COMMAND:COMMIT", "ERROR", "ERROR", "engine not available." },
        { MessageId::CommitCannotDetermineAreaText, "COMMIT_CANNOT_DETERMINE_AREA_TEXT", "COMMAND:COMMIT", "ERROR", "ERROR", "cannot determine current area." },
        { MessageId::CommitAllNoBufferedText, "COMMIT_ALL_NO_BUFFERED_TEXT", "COMMAND:COMMIT", "STATUS", "INFO", "no buffered changes." },
        { MessageId::CommitAllCompleteText, "COMMIT_ALL_COMPLETE_TEXT", "COMMAND:COMMIT", "STATUS", "INFO", "complete={committed} failed={failed}." },
        { MessageId::TurbopackUsageText, "TURBOPACK_USAGE_TEXT", "COMMAND:TURBOPACK", "USAGE", "INFO", "Usage:\n  TURBOPACK USAGE\n  TURBOPACK\nExamples:\n  TURBOPACK\nNotes:\n  - TURBOPACK USAGE does not require an open table and does not rewrite files.\n  - TURBOPACK is a fast path for plain non-memo, non-x64 DBF tables only.\n  - Memo tables and x64 tables are refused; use PACK instead.\n  - TURBOPACK closes the table on success; reopen with USE <table>.\n  - Index containers must be rebuilt/rebound after TURBOPACK." },
        { MessageId::TurbopackNoTableOpenText, "TURBOPACK_NO_TABLE_OPEN_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "No table open." },
        { MessageId::TurbopackMemoNotSupportedText, "TURBOPACK_MEMO_NOT_SUPPORTED_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "Memo tables not supported. Use PACK instead." },
        { MessageId::TurbopackX64NotSupportedText, "TURBOPACK_X64_NOT_SUPPORTED_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "X64 tables not supported. Use PACK instead." },
        { MessageId::TurbopackCannotDeterminePathText, "TURBOPACK_CANNOT_DETERMINE_PATH_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "Cannot determine DBF file path." },
        { MessageId::TurbopackNotDbfText, "TURBOPACK_NOT_DBF_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "Not a .dbf file: {file}" },
        { MessageId::TurbopackFileNotFoundText, "TURBOPACK_FILE_NOT_FOUND_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "File not found: {file}" },
        { MessageId::TurbopackProcessingText, "TURBOPACK_PROCESSING_TEXT", "COMMAND:TURBOPACK", "STATUS", "INFO", "TURBOPACK processing: {file}" },
        { MessageId::TurbopackCannotOpenSourceText, "TURBOPACK_CANNOT_OPEN_SOURCE_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "Cannot open source file." },
        { MessageId::TurbopackCannotReadHeaderText, "TURBOPACK_CANNOT_READ_HEADER_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "Cannot read header." },
        { MessageId::TurbopackInvalidHeaderLenText, "TURBOPACK_INVALID_HEADER_LEN_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "Invalid header lengths." },
        { MessageId::TurbopackDetailText, "TURBOPACK_DETAIL_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "{detail}" },
        { MessageId::TurbopackInvalidHeaderTermText, "TURBOPACK_INVALID_HEADER_TERM_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "Invalid or incomplete header (missing 0x0D terminator)." },
        { MessageId::TurbopackHeaderCountMismatchText, "TURBOPACK_HEADER_COUNT_MISMATCH_TEXT", "COMMAND:TURBOPACK", "WARNING", "WARNING", "Warning — header count ({orig}) does not match physical count ({actual}); using safe count {safe}." },
        { MessageId::TurbopackNoValidRecordsText, "TURBOPACK_NO_VALID_RECORDS_TEXT", "COMMAND:TURBOPACK", "WARNING", "WARNING", "Warning — no valid physical records detected; table may be corrupt." },
        { MessageId::TurbopackCannotCreateTempText, "TURBOPACK_CANNOT_CREATE_TEMP_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "Cannot create temp file {file}" },
        { MessageId::TurbopackFailedWriteHeaderText, "TURBOPACK_FAILED_WRITE_HEADER_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "Failed writing header to temp." },
        { MessageId::TurbopackReadErrorText, "TURBOPACK_READ_ERROR_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "Read error at source record {rec} after {kept} kept records." },
        { MessageId::TurbopackWriteErrorText, "TURBOPACK_WRITE_ERROR_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "Write error after {kept} kept records." },
        { MessageId::TurbopackFailedUpdateHeaderText, "TURBOPACK_FAILED_UPDATE_HEADER_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "Failed to update header with final count." },
        { MessageId::TurbopackCannotCreateBackupText, "TURBOPACK_CANNOT_CREATE_BACKUP_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "Cannot create backup: {detail}" },
        { MessageId::TurbopackCannotReplaceText, "TURBOPACK_CANNOT_REPLACE_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "Cannot replace original file: {detail}" },
        { MessageId::TurbopackRollbackFailedText, "TURBOPACK_ROLLBACK_FAILED_TEXT", "COMMAND:TURBOPACK", "ERROR", "ERROR", "  Rollback also failed. Original may be lost." },
        { MessageId::TurbopackCompleteText, "TURBOPACK_COMPLETE_TEXT", "COMMAND:TURBOPACK", "STATUS", "INFO", "TURBOPACK complete. Kept {kept} of {orig} records." },
        { MessageId::TurbopackReadyForUseText, "TURBOPACK_READY_FOR_USE_TEXT", "COMMAND:TURBOPACK", "STATUS", "INFO", "{file} ready for use." },
        { MessageId::TurbopackSidecarsNoneText, "TURBOPACK_SIDECARS_NONE_TEXT", "COMMAND:TURBOPACK", "STATUS", "INFO", "Sidecar(s): none." },
        { MessageId::TurbopackReopenText, "TURBOPACK_REOPEN_TEXT", "COMMAND:TURBOPACK", "STATUS", "INFO", "Table is closed. Reopen with: USE {stem}" },
        { MessageId::TurbopackReindexOrderText, "TURBOPACK_REINDEX_ORDER_TEXT", "COMMAND:TURBOPACK", "STATUS", "INFO", "Reindex recommended. Previous order '{order}' detached." },
        { MessageId::TurbopackReindexText, "TURBOPACK_REINDEX_TEXT", "COMMAND:TURBOPACK", "STATUS", "INFO", "Reindex recommended." },
        { MessageId::RebuildUsageText, "REBUILD_USAGE_TEXT", "COMMAND:REBUILD", "USAGE", "INFO", "Usage:\n  REBUILD USAGE\n  REBUILD\n  REBUILD <name-or-path.cnx>\nNotes:\n  - Rebuilds the CNX container once.\n  - No args uses current CNX or defaults to <table>.cnx.\n  - Dirty TABLE buffers are committed only after confirmation." },
        { MessageId::RebuildCanceledDirtyText, "REBUILD_CANCELED_DIRTY_TEXT", "COMMAND:REBUILD", "ERROR", "ERROR", "canceled (dirty table)." },
        { MessageId::RebuildStillDirtyText, "REBUILD_STILL_DIRTY_TEXT", "COMMAND:REBUILD", "ERROR", "ERROR", "still dirty after COMMIT; canceling." },
        { MessageId::RebuildNoTableOpenText, "REBUILD_NO_TABLE_OPEN_TEXT", "COMMAND:REBUILD", "ERROR", "ERROR", "no table open." },
        { MessageId::RebuildCnxNotFoundText, "REBUILD_CNX_NOT_FOUND_TEXT", "COMMAND:REBUILD", "ERROR", "ERROR", "CNX not found: {path}" },
        { MessageId::RebuildReindexBannerText, "REBUILD_REINDEX_BANNER_TEXT", "COMMAND:REBUILD", "STATUS", "INFO", "REINDEX CNX -> REBUILD" },
        { MessageId::RebuildCnxContainerText, "REBUILD_CNX_CONTAINER_TEXT", "COMMAND:REBUILD", "STATUS", "INFO", "CNX container: {path}" },
        { MessageId::RebuildUnableOpenCnxText, "REBUILD_UNABLE_OPEN_CNX_TEXT", "COMMAND:REBUILD", "ERROR", "ERROR", "unable to open CNX" },
        { MessageId::RebuildFailedReadTagdirText, "REBUILD_FAILED_READ_TAGDIR_TEXT", "COMMAND:REBUILD", "ERROR", "ERROR", "failed to read tag directory" },
        { MessageId::RebuildBackendOpenFailedText, "REBUILD_BACKEND_OPEN_FAILED_TEXT", "COMMAND:REBUILD", "ERROR", "ERROR", "backend open failed" },
        { MessageId::RebuildTagOkText, "REBUILD_TAG_OK_TEXT", "COMMAND:REBUILD", "STATUS", "INFO", "  [{id}] {tag} : OK" },
        { MessageId::RebuildStaleClearedText, "REBUILD_STALE_CLEARED_TEXT", "COMMAND:REBUILD", "STATUS", "INFO", "TABLE STALE cleared (fresh)" },
        { MessageId::RebuildDoneText, "REBUILD_DONE_TEXT", "COMMAND:REBUILD", "STATUS", "INFO", "done  OK={ok}  SKIP=0  FAIL=0" },
        { MessageId::RebuildFailDetailText, "REBUILD_FAIL_DETAIL_TEXT", "COMMAND:REBUILD", "ERROR", "ERROR", "FAIL ({detail})" },
        { MessageId::RebuildFailText, "REBUILD_FAIL_TEXT", "COMMAND:REBUILD", "ERROR", "ERROR", "FAIL" },
        { MessageId::SortUsageText, "SORT_USAGE_TEXT", "COMMAND:SORT", "USAGE", "INFO", "Usage:\n  SORT USAGE\n  SORT TO <outdbf> ON <expr>\n  SORT TO <outdbf> ON <expr> ASC\n  SORT TO <outdbf> ON <expr> DESC\n  SORT TO <outdbf> ON <expr>, <expr>\n  SORT ALL TO <outdbf> ON <expr>\n  SORT DELETED TO <outdbf> ON <expr>\n  SORT OVERWRITE TO <outdbf> ON <expr>\n  SORT TO <outdbf> ON <expr> FOR <expr>\n  SORT TO <outdbf> ON <expr> WHILE <expr>\n  SORT TO <outdbf> ON <expr> FIELDS <fieldlist>\n  SORT TO <outdbf> ON <expr> UNIQUE" },
        { MessageId::SortNoTableOpenText, "SORT_NO_TABLE_OPEN_TEXT", "COMMAND:SORT", "ERROR", "ERROR", "no table is open." },
        { MessageId::SortMissingOutputText, "SORT_MISSING_OUTPUT_TEXT", "COMMAND:SORT", "ERROR", "ERROR", "missing output file after TO." },
        { MessageId::SortMissingOnKeysText, "SORT_MISSING_ON_KEYS_TEXT", "COMMAND:SORT", "ERROR", "ERROR", "missing ON key list." },
        { MessageId::SortErrorDetailText, "SORT_ERROR_DETAIL_TEXT", "COMMAND:SORT", "ERROR", "ERROR", "{detail}" },
        { MessageId::SortNoUsableKeysText, "SORT_NO_USABLE_KEYS_TEXT", "COMMAND:SORT", "ERROR", "ERROR", "no usable keys found in ON list." },
        { MessageId::SortOutputExistsText, "SORT_OUTPUT_EXISTS_TEXT", "COMMAND:SORT", "ERROR", "ERROR", "output exists (use OVERWRITE): {path}" },
        { MessageId::SortCannotOverwriteText, "SORT_CANNOT_OVERWRITE_TEXT", "COMMAND:SORT", "ERROR", "ERROR", "cannot overwrite existing file: {path}" },
        { MessageId::SortWhileEvalFailedText, "SORT_WHILE_EVAL_FAILED_TEXT", "COMMAND:SORT", "ERROR", "ERROR", "WHILE evaluation failed." },
        { MessageId::SortForEvalFailedText, "SORT_FOR_EVAL_FAILED_TEXT", "COMMAND:SORT", "ERROR", "ERROR", "FOR evaluation failed." },
        { MessageId::SortSummaryText, "SORT_SUMMARY_TEXT", "COMMAND:SORT", "STATUS", "INFO", "scanned {scanned}, selected {kept}, wrote {written}{unique} -> {path}" },
        { MessageId::ReindexUsageText, "REINDEX_USAGE_TEXT", "COMMAND:REINDEX", "USAGE", "INFO", "Usage:\n  REINDEX USAGE\n  REINDEX\n  REINDEX INX [<tagfile>]\n  REINDEX CNX [<name-or-path.cnx>]\n  REINDEX CDX [YES|AUTO|NOPROMPT] [CLEAN|FORCE] [QUIET]\n  REINDEX SIX [<tagfile>]\n  REINDEX SCX [<tagfile>]\n  REINDEX ALL\n  REINDEX CUSTOM\n  REINDEX <tagfile>\nNotes:\n  - Default: v64-like table -> CDX; v32-like table -> INX.\n  - CNX delegates to REBUILD; CDX delegates to BUILDLMDB.\n  - REINDEX <tagfile> is treated as REINDEX INX <tagfile>." },
        { MessageId::ReindexCanceledDirtyText, "REINDEX_CANCELED_DIRTY_TEXT", "COMMAND:REINDEX", "ERROR", "ERROR", "canceled (dirty table)." },
        { MessageId::ReindexStillDirtyText, "REINDEX_STILL_DIRTY_TEXT", "COMMAND:REINDEX", "ERROR", "ERROR", "still dirty after COMMIT; canceling." },
        { MessageId::ReindexNoTableOpenText, "REINDEX_NO_TABLE_OPEN_TEXT", "COMMAND:REINDEX", "ERROR", "ERROR", "no table open." },
        { MessageId::ReindexNoTableOpenPlainText, "REINDEX_NO_TABLE_OPEN_PLAIN_TEXT", "COMMAND:REINDEX", "ERROR", "ERROR", "No table open." },
        { MessageId::ReindexUnknownFieldText, "REINDEX_UNKNOWN_FIELD_TEXT", "COMMAND:REINDEX", "ERROR", "ERROR", "unknown field token '{token}'." },
        { MessageId::ReindexCannotWriteText, "REINDEX_CANNOT_WRITE_TEXT", "COMMAND:REINDEX", "ERROR", "ERROR", "cannot write file: {path}" },
        { MessageId::ReindexWroteText, "REINDEX_WROTE_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "wrote {file}  (2INX v2, expr: {expr}, ASC)" },
        { MessageId::ReindexCannotInferTagText, "REINDEX_CANNOT_INFER_TAG_TEXT", "COMMAND:REINDEX", "ERROR", "ERROR", "cannot infer tag path (unknown table name).\nSpecify a tag file: REINDEX INX <tagfile.inx>" },
        { MessageId::ReindexTagNotFoundText, "REINDEX_TAG_NOT_FOUND_TEXT", "COMMAND:REINDEX", "ERROR", "ERROR", "tag file not found: {path}" },
        { MessageId::ReindexTagNotFoundHintText, "REINDEX_TAG_NOT_FOUND_HINT_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "Hint: create it with: INDEX ON <field|#n> TAG {filename}" },
        { MessageId::ReindexCannotReadExprText, "REINDEX_CANNOT_READ_EXPR_TEXT", "COMMAND:REINDEX", "ERROR", "ERROR", "cannot read tag expression from: {path}" },
        { MessageId::ReindexInxBannerText, "REINDEX_INX_BANNER_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "REINDEX INX" },
        { MessageId::ReindexInxIndexFileText, "REINDEX_INX_INDEX_FILE_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "  Index file   : {path}" },
        { MessageId::ReindexInxTagExprText, "REINDEX_INX_TAG_EXPR_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "  Tag expr     : {expr}" },
        { MessageId::ReindexFailedText, "REINDEX_FAILED_TEXT", "COMMAND:REINDEX", "ERROR", "ERROR", "failed." },
        { MessageId::ReindexStaleClearedText, "REINDEX_STALE_CLEARED_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "TABLE STALE cleared (fresh)." },
        { MessageId::ReindexRegeneratedNoteText, "REINDEX_REGENERATED_NOTE_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "Note: INX file was regenerated from its stored tag expression." },
        { MessageId::ReindexCdxRequiresLmdbText, "REINDEX_CDX_REQUIRES_LMDB_TEXT", "COMMAND:REINDEX", "ERROR", "ERROR", "REINDEX CDX requires DOTTALK_INDEX_MODE=LMDB." },
        { MessageId::ReindexSixBannerText, "REINDEX_SIX_BANNER_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "REINDEX SIX (student single-tag)" },
        { MessageId::ReindexScxBannerText, "REINDEX_SCX_BANNER_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "REINDEX SCX (student compound)" },
        { MessageId::ReindexTableLineText, "REINDEX_TABLE_LINE_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "  Table : {table}" },
        { MessageId::ReindexArgLineText, "REINDEX_ARG_LINE_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "  Arg   : {arg}" },
        { MessageId::ReindexStubStatusText, "REINDEX_STUB_STATUS_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "  Status: stub (no backend)" },
        { MessageId::ReindexAllCdxText, "REINDEX_ALL_CDX_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "REINDEX ALL -> CDX (v64-like table)" },
        { MessageId::ReindexAllInxCnxText, "REINDEX_ALL_INX_CNX_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "REINDEX ALL -> INX + CNX (v32-like table)" },
        { MessageId::ReindexCustomText, "REINDEX_CUSTOM_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "REINDEX CUSTOM -> SIX + SCX" },
        { MessageId::ReindexDefaultCdxText, "REINDEX_DEFAULT_CDX_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "REINDEX default -> CDX (v64-like table, via BUILDLMDB)" },
        { MessageId::ReindexDefaultInxText, "REINDEX_DEFAULT_INX_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "REINDEX default -> INX (v32-like table)" },
        { MessageId::ReindexCnxBannerText, "REINDEX_CNX_BANNER_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "REINDEX CNX" },
        { MessageId::ReindexCdxBuildlmdbText, "REINDEX_CDX_BUILDLMDB_TEXT", "COMMAND:REINDEX", "STATUS", "INFO", "REINDEX CDX -> BUILDLMDB" },
        { MessageId::ExportFunctionsUsageText, "EXPORTFUNCTIONS_USAGE_TEXT", "COMMAND:EXPORTFUNCTIONS", "USAGE", "INFO", "Usage:\n  EXPORTFUNCTIONS\n  EXPORTFUNCTIONS USAGE\n  EXPORTFUNCTIONS MD\n  EXPORTFUNCTIONS MD <path>\n  EXPORTFUNCTIONS <path>\n\nDefault output:\n  ./data/docs/functions.md\n" },
        { MessageId::ExportFunctionsUnsupportedFormatText, "EXPORTFUNCTIONS_UNSUPPORTED_FORMAT_TEXT", "COMMAND:EXPORTFUNCTIONS", "ERROR", "ERROR", "Unsupported format: {format}" },
        { MessageId::ExportFunctionsFailedText, "EXPORTFUNCTIONS_FAILED_TEXT", "COMMAND:EXPORTFUNCTIONS", "ERROR", "ERROR", "EXPORTFUNCTIONS failed: {detail}" },
        { MessageId::ExportFunctionsExportedText, "EXPORTFUNCTIONS_EXPORTED_TEXT", "COMMAND:EXPORTFUNCTIONS", "STATUS", "INFO", "Function reference exported to: {path}" },
        { MessageId::IndexseekUsageText, "INDEXSEEK_USAGE_TEXT", "COMMAND:INDEXSEEK", "USAGE", "INFO", "Usage:\n  INDEXSEEK USAGE\n  INDEXSEEK <value>\n  INDEXSEEK <value> SOFT\n  INDEXSEEK <value> TAG <tag-or-path>\n  INDEXSEEK <value> SOFT TAG <tag-or-path>\nExamples:\n  INDEXSEEK \"TAYLOR\"\n  INDEXSEEK \"TAYLOR\" SOFT\n  INDEXSEEK \"TAYLOR\" TAG students.cdx\nNotes:\n  - INDEXSEEK prints INDEXSEEK(): <recno> and restores the cursor best-effort.\n  - INDEXSEEK USAGE works without an open table.\n" },
        { MessageId::ScxUsageText, "SCX_USAGE_TEXT", "COMMAND:SCX", "USAGE", "INFO", "Usage:\n  SCX USAGE\n  SCX CREATE <file>\n  SCX ADDTAG <file> <name> FIELD <n> [DESC]\n  SCX BUILD <file>\n  SCX TAGS <file>\n  SCX INFO <file>" },
        { MessageId::ScxCreateUsageText, "SCX_CREATE_USAGE_TEXT", "COMMAND:SCX", "USAGE", "INFO", "Usage: SCX CREATE <file>" },
        { MessageId::ScxAddtagUsageText, "SCX_ADDTAG_USAGE_TEXT", "COMMAND:SCX", "USAGE", "INFO", "Usage: SCX ADDTAG <file> <name> FIELD <n> [DESC]" },
        { MessageId::ScxBuildUsageText, "SCX_BUILD_USAGE_TEXT", "COMMAND:SCX", "USAGE", "INFO", "Usage: SCX BUILD <file>" },
        { MessageId::ScxTagsUsageText, "SCX_TAGS_USAGE_TEXT", "COMMAND:SCX", "USAGE", "INFO", "Usage: SCX TAGS <file>" },
        { MessageId::ScxInfoUsageText, "SCX_INFO_USAGE_TEXT", "COMMAND:SCX", "USAGE", "INFO", "Usage: SCX INFO <file>" },
        { MessageId::ScxDetailText, "SCX_DETAIL_TEXT", "COMMAND:SCX", "ERROR", "ERROR", "{detail}" },
        { MessageId::ScxCreateWroteText, "SCX_CREATE_WROTE_TEXT", "COMMAND:SCX", "STATUS", "INFO", "wrote {file}" },
        { MessageId::ScxAddtagAddedText, "SCX_ADDTAG_ADDED_TEXT", "COMMAND:SCX", "STATUS", "INFO", "added '{name}'" },
        { MessageId::ScxBuildDoneText, "SCX_BUILD_DONE_TEXT", "COMMAND:SCX", "STATUS", "INFO", "done {file}" },
        { MessageId::ScxUnknownSubText, "SCX_UNKNOWN_SUB_TEXT", "COMMAND:SCX", "ERROR", "ERROR", "unknown subcommand: {sub}" },
        {
            MessageId::ReplaceMultiUsageText,
            "REPLACE_MULTI_USAGE_TEXT",
            "COMMAND:MULTIREP",
            "USAGE",
            "INFO",
            "Usage:\n  MULTIREP USAGE\n  MULTIREP <field> WITH <value>[, <field> WITH <value>]...\nExamples:\n  MULTIREP LNAME WITH \"Smith\", FNAME WITH \"John\"\n  MULTIREP DOB WITH 20000101, ACTIVE WITH .T.\nNotes:\n  - MULTIREP requires an open table and a current record.\n  - All assignments are validated before the physical write.\n  - MULTIREP uses one record lock and one DBF write.\n  - Memo fields are written through the memo backend.\n  - Direct index maintenance uses before/after snapshots.\n  - Changed fields are marked STALE only if index maintenance fails."
        },
        {
            MessageId::ReplaceMultiExpectedFieldAfterFieldText,
            "REPLACE_MULTI_EXPECTED_FIELD_AFTER_FIELD_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "expected field after FIELD."
        },
        {
            MessageId::ReplaceMultiExpectedWithAfterFieldText,
            "REPLACE_MULTI_EXPECTED_WITH_AFTER_FIELD_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "expected WITH after field."
        },
        {
            MessageId::ReplaceMultiEmptyValueText,
            "REPLACE_MULTI_EMPTY_VALUE_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "empty value."
        },
        {
            MessageId::ReplaceMultiInvalidFieldTokenText,
            "REPLACE_MULTI_INVALID_FIELD_TOKEN_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "invalid field token '{field}'."
        },
        {
            MessageId::ReplaceMultiUnknownFieldText,
            "REPLACE_MULTI_UNKNOWN_FIELD_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "unknown field '{field}'."
        },
        {
            MessageId::ReplaceMultiNoAssignmentsText,
            "REPLACE_MULTI_NO_ASSIGNMENTS_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "no assignments."
        },
        {
            MessageId::ReplaceMultiNoFileOpenText,
            "REPLACE_MULTI_NO_FILE_OPEN_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "no file open."
        },
        {
            MessageId::ReplaceMultiNoCurrentRecordText,
            "REPLACE_MULTI_NO_CURRENT_RECORD_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "no current record."
        },
        {
            MessageId::ReplaceMultiRecordLockedText,
            "REPLACE_MULTI_RECORD_LOCKED_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "record is locked ({detail})."
        },
        {
            MessageId::ReplaceMultiInvalidDateForFieldText,
            "REPLACE_MULTI_INVALID_DATE_FOR_FIELD_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "invalid date for field."
        },
        {
            MessageId::ReplaceMultiInvalidLogicalForFieldText,
            "REPLACE_MULTI_INVALID_LOGICAL_FOR_FIELD_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "invalid logical for field."
        },
        {
            MessageId::ReplaceMultiInvalidNumericForFieldText,
            "REPLACE_MULTI_INVALID_NUMERIC_FOR_FIELD_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "invalid numeric for field."
        },
        {
            MessageId::ReplaceMultiInvalidFloatForFieldText,
            "REPLACE_MULTI_INVALID_FLOAT_FOR_FIELD_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "invalid float for field."
        },
        {
            MessageId::ReplaceMultiInvalidInt32ForFieldText,
            "REPLACE_MULTI_INVALID_INT32_FOR_FIELD_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "invalid int32 for field."
        },
        {
            MessageId::ReplaceMultiInvalidDoubleForFieldText,
            "REPLACE_MULTI_INVALID_DOUBLE_FOR_FIELD_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "invalid double for field."
        },
        {
            MessageId::ReplaceMultiInvalidCurrencyForFieldText,
            "REPLACE_MULTI_INVALID_CURRENCY_FOR_FIELD_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "invalid currency for field."
        },
        {
            MessageId::ReplaceMultiDetailText,
            "REPLACE_MULTI_DETAIL_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "{detail}"
        },
        {
            MessageId::ReplaceMultiMemoBackendNotAttachedText,
            "REPLACE_MULTI_MEMO_BACKEND_NOT_ATTACHED_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "memo backend not attached."
        },
        {
            MessageId::ReplaceMultiMemoWriteFailedText,
            "REPLACE_MULTI_MEMO_WRITE_FAILED_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "memo write failed{detail}"
        },
        {
            MessageId::ReplaceMultiStoreMemoTokenFailedText,
            "REPLACE_MULTI_STORE_MEMO_TOKEN_FAILED_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "failed to store memo token in DBF field."
        },
        {
            MessageId::ReplaceMultiFieldSetFailedText,
            "REPLACE_MULTI_FIELD_SET_FAILED_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "field set failed."
        },
        {
            MessageId::ReplaceMultiExceptionDuringWriteText,
            "REPLACE_MULTI_EXCEPTION_DURING_WRITE_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "exception during write."
        },
        {
            MessageId::ReplaceMultiWriteFailedText,
            "REPLACE_MULTI_WRITE_FAILED_TEXT",
            "COMMAND:REPLACE_MULTI",
            "ERROR",
            "ERROR",
            "write failed."
        },
        {
            MessageId::ReplaceMultiUpdatedFieldsText,
            "REPLACE_MULTI_UPDATED_FIELDS_TEXT",
            "COMMAND:REPLACE_MULTI",
            "STATUS",
            "INFO",
            "updated {count} field(s)."
        },
        {
            MessageId::UnsupportedMessageLocale,
            "UNSUPPORTED_MESSAGE_LOCALE",
            "SUBSYSTEM:MESSAGING",
            "ERROR",
            "ERROR",
            "Unsupported message locale: {locale}"
        },
        {
            MessageId::UnknownCommand,
            "UNKNOWN_COMMAND",
            "GLOBAL",
            "ERROR",
            "ERROR",
            "Unknown command: {command}"
        },
        {
            MessageId::MacroUndefinedVariable,
            "MACRO_UNDEFINED_VARIABLE",
            "GLOBAL",
            "ERROR",
            "ERROR",
            "MACRO: undefined variable: {name}"
        },
        {
            MessageId::MissingArgument,
            "MISSING_ARGUMENT",
            "GLOBAL",
            "ERROR",
            "ERROR",
            "Missing required argument."
        },
        {
            MessageId::TooManyArguments,
            "TOO_MANY_ARGUMENTS",
            "GLOBAL",
            "ERROR",
            "ERROR",
            "Too many arguments."
        },
        {
            MessageId::InvalidSyntax,
            "INVALID_SYNTAX",
            "GLOBAL",
            "ERROR",
            "ERROR",
            "Invalid command syntax."
        },
        {
            MessageId::InvalidOption,
            "INVALID_OPTION",
            "GLOBAL",
            "ERROR",
            "ERROR",
            "Invalid option: {option}"
        },
        {
            MessageId::CommandNotImplemented,
            "COMMAND_NOT_IMPLEMENTED",
            "GLOBAL",
            "STATUS",
            "WARNING",
            "Command is recognized but not implemented: {command}"
        },
        {
            MessageId::CommandDeprecated,
            "COMMAND_DEPRECATED",
            "GLOBAL",
            "DEPRECATION",
            "WARNING",
            "Command is deprecated: {command}"
        },
        {
            MessageId::GlobalUsageTitle,
            "GLOBAL_USAGE_TITLE",
            "GLOBAL",
            "STATUS",
            "INFO",
            "Usage:"
        },
        {
            MessageId::GlobalSyntaxTitle,
            "GLOBAL_SYNTAX_TITLE",
            "GLOBAL",
            "STATUS",
            "INFO",
            "Syntax:"
        },
        {
            MessageId::GlobalExamplesTitle,
            "GLOBAL_EXAMPLES_TITLE",
            "GLOBAL",
            "STATUS",
            "INFO",
            "Examples:"
        },
        {
            MessageId::GlobalDirectAliasTitle,
            "GLOBAL_DIRECT_ALIAS_TITLE",
            "GLOBAL",
            "STATUS",
            "INFO",
            "Direct alias:"
        },
        {
            MessageId::GlobalDefaultsTitle,
            "GLOBAL_DEFAULTS_TITLE",
            "GLOBAL",
            "STATUS",
            "INFO",
            "Defaults:"
        },
        {
            MessageId::GlobalNotesTitle,
            "GLOBAL_NOTES_TITLE",
            "GLOBAL",
            "STATUS",
            "INFO",
            "Notes:"
        },
        {
            MessageId::GlobalWarningsTitle,
            "GLOBAL_WARNINGS_TITLE",
            "GLOBAL",
            "STATUS",
            "INFO",
            "Warnings:"
        },
        {
            MessageId::GlobalCategoryLine,
            "GLOBAL_CATEGORY_LINE",
            "GLOBAL",
            "STATUS",
            "INFO",
            "Category: {value}"
        },
        {
            MessageId::GlobalArgumentsLine,
            "GLOBAL_ARGUMENTS_LINE",
            "GLOBAL",
            "STATUS",
            "INFO",
            "Arguments: {min}..{max}"
        },
        {
            MessageId::GlobalAliasesLine,
            "GLOBAL_ALIASES_LINE",
            "GLOBAL",
            "STATUS",
            "INFO",
            "Aliases: {value}"
        },
        {
            MessageId::GlobalSubcommandsTitle,
            "GLOBAL_SUBCOMMANDS_TITLE",
            "GLOBAL",
            "STATUS",
            "INFO",
            "Subcommands:"
        },
        {
            MessageId::GlobalDevTransitionalTitle,
            "GLOBAL_DEV_TRANSITIONAL_TITLE",
            "GLOBAL",
            "STATUS",
            "INFO",
            "Dev / Transitional:"
        },
        {
            MessageId::GlobalFunctionFallbackSyntaxLine,
            "GLOBAL_FUNCTION_FALLBACK_SYNTAX_LINE",
            "GLOBAL",
            "STATUS",
            "INFO",
            "  {name}(...)"
        },
        {
            MessageId::NoOpenTable,
            "NO_OPEN_TABLE",
            "SUBSYSTEM:DBAREA",
            "ERROR",
            "ERROR",
            "No table is currently open."
        },
        {
            MessageId::NoSelectedArea,
            "NO_SELECTED_AREA",
            "SUBSYSTEM:DBAREA",
            "ERROR",
            "ERROR",
            "No current work area is selected."
        },
        {
            MessageId::NoActiveIndex,
            "NO_ACTIVE_INDEX",
            "SUBSYSTEM:XINDEX",
            "ERROR",
            "ERROR",
            "No active index."
        },
        {
            MessageId::FindFoundText,
            "FIND_FOUND_TEXT",
            "COMMAND:FIND",
            "STATUS",
            "INFO",
            "Found."
        },
        {
            MessageId::FindNotFoundText,
            "FIND_NOT_FOUND_TEXT",
            "COMMAND:FIND",
            "STATUS",
            "INFO",
            "Not found."
        },
        {
            MessageId::SeekEmptyText,
            "SEEK_EMPTY_TEXT",
            "COMMAND:SEEK",
            "STATUS",
            "INFO",
            "(empty)"
        },
        {
            MessageId::SmartlistUsageText,
            "SMARTLIST_USAGE_TEXT",
            "COMMAND:SMARTLIST",
            "USAGE",
            "INFO",
            "Usage:\n  SMARTLIST\n  SMARTLIST USAGE\n  SMARTLIST <fields>\n  SMARTLIST ALL\n  SMARTLIST <limit>\n  SMARTLIST NEXT <n>\n  SMARTLIST FIRST <n>\n  SMARTLIST DELETED\n  SMARTLIST DEBUG\n  SMARTLIST TUPLES\n  SMARTLIST FOR <pred>"
        },
        {
            MessageId::SmartlistUnknownProjectionFieldText,
            "SMARTLIST_UNKNOWN_PROJECTION_FIELD_TEXT",
            "COMMAND:SMARTLIST",
            "WARNING",
            "WARNING",
            "unknown projection field '{field}'; using full row."
        },
        {
            MessageId::SeekTraceStatusText,
            "SEEK_TRACE_STATUS_TEXT",
            "COMMAND:SEEK",
            "STATUS",
            "INFO",
            "SEEK TRACE is {state}."
        },
        {
            MessageId::SeekUnknownFieldText,
            "SEEK_UNKNOWN_FIELD_TEXT",
            "COMMAND:SEEK",
            "ERROR",
            "ERROR",
            "unknown field: {field}"
        },
        {
            MessageId::SeekFoundAtText,
            "SEEK_FOUND_AT_TEXT",
            "COMMAND:SEEK",
            "STATUS",
            "INFO",
            "Found at {recno}."
        },
        {
            MessageId::SeekNearMatchAtText,
            "SEEK_NEAR_MATCH_AT_TEXT",
            "COMMAND:SEEK",
            "STATUS",
            "INFO",
            "Near match at {recno}."
        },
        {
            MessageId::SeekNotFoundText,
            "SEEK_NOT_FOUND_TEXT",
            "COMMAND:SEEK",
            "STATUS",
            "INFO",
            "Not found."
        },
        {
            MessageId::AscendUsageText,
            "ASCEND_USAGE_TEXT",
            "COMMAND:ASCEND",
            "USAGE",
            "INFO",
            "Usage:\n  ASCEND\n  ASCEND USAGE\n"
        },
        {
            MessageId::OrderAscendingSet,
            "ORDER_ASCENDING_SET",
            "SUBSYSTEM:XINDEX",
            "STATUS",
            "INFO",
            "Order: ASCENDING."
        },
        {
            MessageId::AreaUsageReadOnlyNote,
            "AREA_USAGE_READ_ONLY_NOTE",
            "COMMAND:AREA",
            "STATUS",
            "INFO",
            "AREA is read-only; it reports the current area slot/file/order state."
        },
        {
            MessageId::AreaCurrentAreaLine,
            "AREA_CURRENT_AREA_LINE",
            "COMMAND:AREA",
            "STATUS",
            "INFO",
            "Current area: {index} of {occupied}"
        },
        {
            MessageId::AreaCurrentAreaUnknownLine,
            "AREA_CURRENT_AREA_UNKNOWN_LINE",
            "COMMAND:AREA",
            "STATUS",
            "INFO",
            "Current area: (unknown)"
        },
        {
            MessageId::AreaNoFileOpenLine,
            "AREA_NO_FILE_OPEN_LINE",
            "COMMAND:AREA",
            "STATUS",
            "INFO",
            "  (no file open in Area)"
        },
        {
            MessageId::AreaFileSummaryLine,
            "AREA_FILE_SUMMARY_LINE",
            "COMMAND:AREA",
            "STATUS",
            "INFO",
            "  File: {label}  Recs: {recs}  Recno: {recno}"
        },
        {
            MessageId::AreaDbfAbsoluteLine,
            "AREA_DBF_ABSOLUTE_LINE",
            "COMMAND:AREA",
            "STATUS",
            "INFO",
            "  DBF (abs)           : {value}"
        },
        {
            MessageId::AreaDbfFlavorLine,
            "AREA_DBF_FLAVOR_LINE",
            "COMMAND:AREA",
            "STATUS",
            "INFO",
            "  DBF Flavor          : {value}"
        },
        {
            MessageId::AreaRuntimeKindLine,
            "AREA_RUNTIME_KIND_LINE",
            "COMMAND:AREA",
            "STATUS",
            "INFO",
            "  Runtime kind        : {value}"
        },
        {
            MessageId::AreaLogicalNameLine,
            "AREA_LOGICAL_NAME_LINE",
            "COMMAND:AREA",
            "STATUS",
            "INFO",
            "  Logical name        : {value}"
        },
        {
            MessageId::AreaLegacyNameLine,
            "AREA_LEGACY_NAME_LINE",
            "COMMAND:AREA",
            "STATUS",
            "INFO",
            "  Legacy name()       : {value}"
        },
        {
            MessageId::AreaPathLine,
            "AREA_PATH_LINE",
            "COMMAND:AREA",
            "STATUS",
            "INFO",
            "  Path: {value}"
        },
        {
            MessageId::StatusUsageText,
            "STATUS_USAGE_TEXT",
            "COMMAND:STATUS",
            "STATUS",
            "INFO",
            "Usage:\n  STATUS                 (Report current work-area status)\n  STATUS USAGE           (Show this usage)\n  STATUS ALL             (Report all open work areas)\n  STATUS VERBOSE         (Include field structure for current area)\n  STATUS ALL VERBOSE     (Report all open areas with field structure)\nNotes:\n  - STATUS is read-only; it reports work-area/index state.\n"
        },
        {
            MessageId::StatusAreaHeaderLine,
            "STATUS_AREA_HEADER_LINE",
            "COMMAND:STATUS",
            "STATUS",
            "INFO",
            "Area {slot}: {path}  ({base}){current}"
        },
        {
            MessageId::StatusWorkspaceLine,
            "STATUS_WORKSPACE_LINE",
            "COMMAND:STATUS",
            "STATUS",
            "INFO",
            "Workspace : {value}"
        },
        {
            MessageId::StatusDbfFlavorLine,
            "STATUS_DBF_FLAVOR_LINE",
            "COMMAND:STATUS",
            "STATUS",
            "INFO",
            "  DBF Flavor   : {value}"
        },
        {
            MessageId::StatusTagsSummaryLine,
            "STATUS_TAGS_SUMMARY_LINE",
            "COMMAND:STATUS",
            "STATUS",
            "INFO",
            "  Tags        : {value}"
        },
        {
            MessageId::StatusTagsTitle,
            "STATUS_TAGS_TITLE",
            "COMMAND:STATUS",
            "STATUS",
            "INFO",
            "  Tags"
        },
        {
            MessageId::StatusTagColumnHeaderText,
            "STATUS_TAG_COLUMN_HEADER_TEXT",
            "COMMAND:STATUS",
            "STATUS",
            "INFO",
            "  Field Name    Type    Len   Dec   Dir"
        },
        {
            MessageId::StatusTagDividerText,
            "STATUS_TAG_DIVIDER_TEXT",
            "COMMAND:STATUS",
            "STATUS",
            "INFO",
            "  ------------ ------- ------ ------ ----"
        },
        {
            MessageId::StatusRecordsLine,
            "STATUS_RECORDS_LINE",
            "COMMAND:STATUS",
            "STATUS",
            "INFO",
            "  Records     : {value}"
        },
        {
            MessageId::StatusLmdbClosedLine,
            "STATUS_LMDB_CLOSED_LINE",
            "COMMAND:STATUS",
            "STATUS",
            "INFO",
            "  LMDB        : (closed)"
        },
        {
            MessageId::StatusLmdbEnvLine,
            "STATUS_LMDB_ENV_LINE",
            "COMMAND:STATUS",
            "STATUS",
            "INFO",
            "  LMDB        : envdir={envdir}{tag_clause}"
        },
        {
            MessageId::StatusFieldsTitle,
            "STATUS_FIELDS_TITLE",
            "COMMAND:STATUS",
            "STATUS",
            "INFO",
            "Fields ({count})"
        },
        {
            MessageId::StatusFieldColumnHeaderText,
            "STATUS_FIELD_COLUMN_HEADER_TEXT",
            "COMMAND:STATUS",
            "STATUS",
            "INFO",
            "  #  Name        Type  Len   Dec"
        },
        {
            MessageId::StatusOrderPhysicalLine,
            "STATUS_ORDER_PHYSICAL_LINE",
            "COMMAND:STATUS",
            "STATUS",
            "INFO",
            "Order       : PHYSICAL"
        },
        {
            MessageId::StructUsageText,
            "STRUCT_USAGE_TEXT",
            "COMMAND:STRUCT",
            "STATUS",
            "INFO",
            "Usage:\n  STRUCT                 (Current area fields + index info)\n  STRUCT USAGE           (Show this usage)\n  STRUCT INDEX           (Explicit index info mode; default)\n  STRUCT FIELDS          (Fields only)\n  STRUCT ALL             (All open areas)\n  STRUCT ALL INDEX       (All open areas + index info)\n  STRUCT ALL VERBOSE     (All open areas + verbose CNX tag info)\nNotes:\n  - STRUCT is read-only; it reports DBF structure/index metadata.\n"
        },
        {
            MessageId::StructNoEngineText,
            "STRUCT_NO_ENGINE_TEXT",
            "COMMAND:STRUCT",
            "ERROR",
            "ERROR",
            "No engine available."
        },
        {
            MessageId::StructNoOpenAreasText,
            "STRUCT_NO_OPEN_AREAS_TEXT",
            "COMMAND:STRUCT",
            "STATUS",
            "INFO",
            "No open areas."
        },
        {
            MessageId::StructNoFileOpenCurrentAreaText,
            "STRUCT_NO_FILE_OPEN_CURRENT_AREA_TEXT",
            "COMMAND:STRUCT",
            "STATUS",
            "INFO",
            "No file open in current area."
        },
        {
            MessageId::StructAreaHeaderLine,
            "STRUCT_AREA_HEADER_LINE",
            "COMMAND:STRUCT",
            "STATUS",
            "INFO",
            "Area {slot}: {path}  ({base})"
        },
        {
            MessageId::StructFieldsTitle,
            "STRUCT_FIELDS_TITLE",
            "COMMAND:STRUCT",
            "STATUS",
            "INFO",
            "Fields ({count})"
        },
        {
            MessageId::StructFieldColumnHeaderText,
            "STRUCT_FIELD_COLUMN_HEADER_TEXT",
            "COMMAND:STRUCT",
            "STATUS",
            "INFO",
            "  #  Name          Type   Len   Dec"
        },
        {
            MessageId::StructDbfileLine,
            "STRUCT_DBFILE_LINE",
            "COMMAND:STRUCT",
            "STATUS",
            "INFO",
            "Dbfile      : {path}  ({base})"
        },
        {
            MessageId::StructIndexFileLine,
            "STRUCT_INDEX_FILE_LINE",
            "COMMAND:STRUCT",
            "STATUS",
            "INFO",
            "Index file  : {value}"
        },
        {
            MessageId::StructTagsSummaryLine,
            "STRUCT_TAGS_SUMMARY_LINE",
            "COMMAND:STRUCT",
            "STATUS",
            "INFO",
            "Tags        : {value}"
        },
        {
            MessageId::StructActiveTagLine,
            "STRUCT_ACTIVE_TAG_LINE",
            "COMMAND:STRUCT",
            "STATUS",
            "INFO",
            "Active tag  : {value}"
        },
        {
            MessageId::StructCnxTagsVerboseTitle,
            "STRUCT_CNX_TAGS_VERBOSE_TITLE",
            "COMMAND:STRUCT",
            "STATUS",
            "INFO",
            "CNX Tags (verbose)"
        },
        {
            MessageId::StructCnxMarksActiveNote,
            "STRUCT_CNX_MARKS_ACTIVE_NOTE",
            "COMMAND:STRUCT",
            "STATUS",
            "INFO",
            "  * marks active"
        },
        {
            MessageId::StructVerboseCnxColumnHeaderText,
            "STRUCT_VERBOSE_CNX_COLUMN_HEADER_TEXT",
            "COMMAND:STRUCT",
            "STATUS",
            "INFO",
            "    Tag             Expression"
        },
        {
            MessageId::DbareaUsageText,
            "DBAREA_USAGE_TEXT",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "Usage:\n  DBAREA\n  DBAREA USAGE\nNotes:\n  - DBAREA is read-only; it reports the current work-area summary.\n"
        },
        {
            MessageId::DbareaNoTableOpenText,
            "DBAREA_NO_TABLE_OPEN_TEXT",
            "COMMAND:DBAREA",
            "ERROR",
            "ERROR",
            "DBAREA: no table open."
        },
        {
            MessageId::DbareaBannerTitle,
            "DBAREA_BANNER_TITLE",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "DBAREA - Current Work Area Summary"
        },
        {
            MessageId::DbareaBannerDividerText,
            "DBAREA_BANNER_DIVIDER_TEXT",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "============================================================"
        },
        {
            MessageId::DbareaAreaSlotLineText,
            "DBAREA_AREA_SLOT_LINE_TEXT",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "Area (slot)"
        },
        {
            MessageId::DbareaDbfAbsoluteLineText,
            "DBAREA_DBF_ABSOLUTE_LINE_TEXT",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "DBF (abs)"
        },
        {
            MessageId::DbareaLogicalNameLineText,
            "DBAREA_LOGICAL_NAME_LINE_TEXT",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "Logical name"
        },
        {
            MessageId::DbareaLegacyNameLineText,
            "DBAREA_LEGACY_NAME_LINE_TEXT",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "Legacy name()"
        },
        {
            MessageId::DbareaRecordsLineText,
            "DBAREA_RECORDS_LINE_TEXT",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "Records"
        },
        {
            MessageId::DbareaRecordLengthLineText,
            "DBAREA_RECORD_LENGTH_LINE_TEXT",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "Record length"
        },
        {
            MessageId::DbareaRecordLengthMethodLineText,
            "DBAREA_RECORD_LENGTH_METHOD_LINE_TEXT",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "recordLength()"
        },
        {
            MessageId::DbareaFieldsCountLineText,
            "DBAREA_FIELDS_COUNT_LINE_TEXT",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "Fields"
        },
        {
            MessageId::DbareaRecnoLineText,
            "DBAREA_RECNO_LINE_TEXT",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "Recno"
        },
        {
            MessageId::DbareaDeletedFlagLineText,
            "DBAREA_DELETED_FLAG_LINE_TEXT",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "Deleted flag"
        },
        {
            MessageId::DbareaIndexOrderTitle,
            "DBAREA_INDEX_ORDER_TITLE",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "Index / Order"
        },
        {
            MessageId::DbareaSectionDividerText,
            "DBAREA_SECTION_DIVIDER_TEXT",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "-------------"
        },
        {
            MessageId::DbareaIndexFileLineText,
            "DBAREA_INDEX_FILE_LINE_TEXT",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "Index file"
        },
        {
            MessageId::DbareaFieldsTitle,
            "DBAREA_FIELDS_TITLE",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "Fields"
        },
        {
            MessageId::DbareaFieldsNoneText,
            "DBAREA_FIELDS_NONE_TEXT",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "(none)"
        },
        {
            MessageId::DbareaFieldColumnHeaderText,
            "DBAREA_FIELD_COLUMN_HEADER_TEXT",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "#    Name              Type      Len     Dec"
        },
        {
            MessageId::DbareaFieldDividerText,
            "DBAREA_FIELD_DIVIDER_TEXT",
            "COMMAND:DBAREA",
            "STATUS",
            "INFO",
            "-------------------------------------------------"
        },
        {
            MessageId::DbareasUsageText,
            "DBAREAS_USAGE_TEXT",
            "COMMAND:DBAREAS",
            "WORKSPACE",
            "INFO",
            "Usage:\n  DBAREAS\n  DBAREAS USAGE\n  DBAREAS <n>\n  DBAREAS ALL\n  DBAREAS REL\nNotes:\n  - DBAREAS with no arguments reports the current area by delegating to DBAREA.\n  - DBAREAS <n> reports slot n when that slot is open.\n  - DBAREAS ALL reports all open slots using filename() as the open-area truth.\n  - DBAREAS REL reports the current area and appends relation summary/tree context.\n  - DBAREAS is read-only; it reports session/work-area state and does not mutate table data.\n"
        },
        {
            MessageId::DbareasNoOpenWorkAreasText,
            "DBAREAS_NO_OPEN_WORK_AREAS_TEXT",
            "COMMAND:DBAREAS",
            "WORKSPACE",
            "INFO",
            "DBAREAS: no open work areas."
        },
        {
            MessageId::DbareasSlotOutOfRangeText,
            "DBAREAS_SLOT_OUT_OF_RANGE_TEXT",
            "COMMAND:DBAREAS",
            "WORKSPACE",
            "INFO",
            "DBAREAS: slot out of range: {slot} (0..{max})"
        },
        {
            MessageId::DbareasAreaNotOpenText,
            "DBAREAS_AREA_NOT_OPEN_TEXT",
            "COMMAND:DBAREAS",
            "WORKSPACE",
            "INFO",
            "DBAREAS: area {slot} is not open."
        },
        {
            MessageId::DbareasRelationsModuleMissingText,
            "DBAREAS_RELATIONS_MODULE_MISSING_TEXT",
            "COMMAND:DBAREAS",
            "WORKSPACE",
            "INFO",
            "Relations: (module not present)"
        },
        {
            MessageId::DbareasRelationsTitleText,
            "DBAREAS_RELATIONS_TITLE_TEXT",
            "COMMAND:DBAREAS",
            "WORKSPACE",
            "INFO",
            "Relations"
        },
        {
            MessageId::DbareasRelationsDividerText,
            "DBAREAS_RELATIONS_DIVIDER_TEXT",
            "COMMAND:DBAREAS",
            "WORKSPACE",
            "INFO",
            "---------"
        },
        {
            MessageId::DbareasParentAnchorLineText,
            "DBAREAS_PARENT_ANCHOR_LINE_TEXT",
            "COMMAND:DBAREAS",
            "WORKSPACE",
            "INFO",
            "Parent anchor        : {value}"
        },
        {
            MessageId::DbareasChildrenNoneText,
            "DBAREAS_CHILDREN_NONE_TEXT",
            "COMMAND:DBAREAS",
            "WORKSPACE",
            "INFO",
            "Children             : (none configured)"
        },
        {
            MessageId::DbareasChildrenDirectTitleText,
            "DBAREAS_CHILDREN_DIRECT_TITLE_TEXT",
            "COMMAND:DBAREAS",
            "WORKSPACE",
            "INFO",
            "Children (direct)"
        },
        {
            MessageId::DbareasChildMatchLineText,
            "DBAREAS_CHILD_MATCH_LINE_TEXT",
            "COMMAND:DBAREAS",
            "WORKSPACE",
            "INFO",
            "  -> {child}  (matches: {count})"
        },
        {
            MessageId::DbareasRelationTreeTitleText,
            "DBAREAS_RELATION_TREE_TITLE_TEXT",
            "COMMAND:DBAREAS",
            "WORKSPACE",
            "INFO",
            "Relation tree"
        },
        {
            MessageId::DbareasRelationTreeDividerText,
            "DBAREAS_RELATION_TREE_DIVIDER_TEXT",
            "COMMAND:DBAREAS",
            "WORKSPACE",
            "INFO",
            "-------------"
        },
        {
            MessageId::FieldsUsageText,
            "FIELDS_USAGE_TEXT",
            "COMMAND:FIELDS",
            "STATUS",
            "INFO",
            "Usage:\n  FIELDS\n  FIELDS USAGE\nNotes:\n  - Reports field number, name, type, length, and decimals for the current area.\n  - FIELDS is read-only.\n"
        },
        {
            MessageId::FieldsNoFieldsText,
            "FIELDS_NO_FIELDS_TEXT",
            "COMMAND:FIELDS",
            "STATUS",
            "INFO",
            "(No fields)"
        },
        {
            MessageId::FieldsColumnHeaderText,
            "FIELDS_COLUMN_HEADER_TEXT",
            "COMMAND:FIELDS",
            "STATUS",
            "INFO",
            "# Name Type Len Dec"
        },
        {
            MessageId::FieldsDividerText,
            "FIELDS_DIVIDER_TEXT",
            "COMMAND:FIELDS",
            "STATUS",
            "INFO",
            "- ---- ---- --- ---"
        },
        {
            MessageId::DescendUsageText,
            "DESCEND_USAGE_TEXT",
            "COMMAND:DESCEND",
            "STATUS",
            "INFO",
            "Usage:\n  DESCEND\n  DESCEND USAGE\n"
        },
        {
            MessageId::OrderDescendingSet,
            "ORDER_DESCENDING_SET",
            "SUBSYSTEM:XINDEX",
            "STATUS",
            "INFO",
            "Order: DESCENDING."
        },
        {
            MessageId::ColorUsageText,
            "COLOR_USAGE_TEXT",
            "COMMAND:COLOR",
            "STATUS",
            "INFO",
            "Usage:\n  COLOR\n  COLOR USAGE\n  COLOR DEFAULT\n  COLOR GREEN\n  COLOR AMBER\n  COLOR TREE ON\n  COLOR TREE OFF\n  COLOR TREECOLOR ON\n  COLOR TREECOLOR OFF\nNotes:\n  - COLOR with no arguments reports current theme and tree palette state.\n  - COLOR TREE/TREECOLOR toggles tree-color behavior.\n"
        },
        {
            MessageId::ColorStatusText,
            "COLOR_STATUS_TEXT",
            "COMMAND:COLOR",
            "STATUS",
            "INFO",
            "COLOR is {value}"
        },
        {
            MessageId::ColorTreeColorStatusText,
            "COLOR_TREECOLOR_STATUS_TEXT",
            "COMMAND:COLOR",
            "STATUS",
            "INFO",
            "TREECOLOR is {value}"
        },
        {
            MessageId::ColorTreePaletteHeaderText,
            "COLOR_TREE_PALETTE_HEADER_TEXT",
            "COMMAND:COLOR",
            "STATUS",
            "INFO",
            "TREE palette rotates across {count} levels:"
        },
        {
            MessageId::ColorTreeLevelLineText,
            "COLOR_TREE_LEVEL_LINE_TEXT",
            "COMMAND:COLOR",
            "STATUS",
            "INFO",
            "  Level {level}: {value}"
        },
        {
            MessageId::ColorTreeSetStatusText,
            "COLOR_TREE_SET_STATUS_TEXT",
            "COMMAND:COLOR",
            "STATUS",
            "INFO",
            "TREECOLOR set to {value}"
        },
        {
            MessageId::ColorSetStatusText,
            "COLOR_SET_STATUS_TEXT",
            "COMMAND:COLOR",
            "STATUS",
            "INFO",
            "COLOR set to {value}"
        },
        {
            MessageId::ValidateUsageText,
            "VALIDATE_USAGE_TEXT",
            "COMMAND:VALIDATE",
            "STATUS",
            "INFO",
            "Usage:\n  VALIDATE USAGE\n  VALIDATE UNIQUE USAGE\n  VALIDATE UNIQUE FIELD <name> [IGNORE DELETED] [REPAIR] [REPORT TO <path>]\nExamples:\n  VALIDATE UNIQUE FIELD SID\n  VALIDATE UNIQUE FIELD EMAIL IGNORE DELETED\n  VALIDATE UNIQUE FIELD SID REPAIR\n  VALIDATE UNIQUE FIELD SID REPORT TO tmp\\sid_dupes.txt\nNotes:\n  - REPAIR may mutate field values; use it intentionally.\n"
        },
        {
            MessageId::ValidateUnknownSubcommandText,
            "VALIDATE_UNKNOWN_SUBCOMMAND_TEXT",
            "COMMAND:VALIDATE",
            "ERROR",
            "ERROR",
            "VALIDATE: unknown subcommand '{command}'."
        },
        {
            MessageId::DotHelpUsageText,
            "DOTHELP_USAGE_TEXT",
            "COMMAND:DOTHELP",
            "STATUS",
            "INFO",
            "Usage:\n  DOTHELP\n  DOTHELP USAGE\n  DOTHELP <term>\n  HELP /DOT <term>\n"
        },
        {
            MessageId::DotHelpTitleText,
            "DOTHELP_TITLE_TEXT",
            "COMMAND:DOTHELP",
            "STATUS",
            "INFO",
            "DOTTALK REFERENCE"
        },
        {
            MessageId::DotHelpSubtitleText,
            "DOTHELP_SUBTITLE_TEXT",
            "COMMAND:DOTHELP",
            "STATUS",
            "INFO",
            "Project-native commands and subsystems"
        },
        {
            MessageId::DotHelpSearchUsageText,
            "DOTHELP_SEARCH_USAGE_TEXT",
            "COMMAND:DOTHELP",
            "STATUS",
            "INFO",
            "Usage:\n  DOTHELP <term>\n  HELP /DOT <term>"
        },
        {
            MessageId::DotHelpMatchesTitleText,
            "DOTHELP_MATCHES_TITLE_TEXT",
            "COMMAND:DOTHELP",
            "STATUS",
            "INFO",
            "Matching DotTalk helpers:"
        },
        {
            MessageId::DotHelpNoTopicText,
            "DOTHELP_NO_TOPIC_TEXT",
            "COMMAND:DOTHELP",
            "ERROR",
            "ERROR",
            "No DotTalk help found for: {command}"
        },
        {
            MessageId::DotHelpTryHelpHintText,
            "DOTHELP_TRY_HELP_HINT_TEXT",
            "COMMAND:DOTHELP",
            "STATUS",
            "INFO",
            "Try HELP /DOT <term> or plain HELP <term>."
        },
        {
            MessageId::DotHelpUnsupportedNoteText,
            "DOTHELP_UNSUPPORTED_NOTE_TEXT",
            "COMMAND:DOTHELP",
            "STATUS",
            "INFO",
            "  (documented, but not fully supported yet)"
        },
        {
            MessageId::FoxHelpUsageText,
            "FOXHELP_USAGE_TEXT",
            "COMMAND:FOXHELP",
            "STATUS",
            "INFO",
            "Usage:\n  FOXHELP\n  FOXHELP USAGE\n  FOXHELP <name>\n  FOXHELP <search>\n  FH\n  FH <name>\n  FH <search>\nNotes:\n  - FOXHELP with no arguments lists the FoxPro-style command subset.\n  - FH is a short alias for FOXHELP.\n"
        },
        {
            MessageId::FoxHelpSubsetTitleText,
            "FOXHELP_SUBSET_TITLE_TEXT",
            "COMMAND:FOXHELP",
            "STATUS",
            "INFO",
            "FoxPro-style commands (subset):"
        },
        {
            MessageId::FoxHelpTipText,
            "FOXHELP_TIP_TEXT",
            "COMMAND:FOXHELP",
            "STATUS",
            "INFO",
            "Tip: FOXHELP <NAME> for details, e.g. FOXHELP INDEX"
        },
        {
            MessageId::FoxHelpMatchesTitleText,
            "FOXHELP_MATCHES_TITLE_TEXT",
            "COMMAND:FOXHELP",
            "STATUS",
            "INFO",
            "Matches for \"{command}\":"
        },
        {
            MessageId::FoxHelpNoTopicText,
            "FOXHELP_NO_TOPIC_TEXT",
            "COMMAND:FOXHELP",
            "ERROR",
            "ERROR",
            "No help found for: {command}"
        },
        {
            MessageId::FoxHelpTryListHintText,
            "FOXHELP_TRY_LIST_HINT_TEXT",
            "COMMAND:FOXHELP",
            "STATUS",
            "INFO",
            "Try FOXHELP (no args) to list commands."
        },
        {
            MessageId::FoxHelpUnsupportedSuffixText,
            "FOXHELP_UNSUPPORTED_SUFFIX_TEXT",
            "COMMAND:FOXHELP",
            "STATUS",
            "INFO",
            "[unsupported]"
        },
        {
            MessageId::FoxStandardUsageText,
            "FOXSTANDARD_USAGE_TEXT",
            "COMMAND:FOXSTANDARD",
            "USAGE",
            "INFO",
            "Usage:\n  FOXSTANDARD USAGE\n  FOXSTANDARD <command>\n  FOXSTANDARD ALL\n  FOXSTANDARD TOPICS\n  FOXSTANDARD LIST"
        },
        {
            MessageId::PshellUsageText,
            "PSHELL_USAGE_TEXT",
            "COMMAND:PSHELL",
            "STATUS",
            "INFO",
            "Usage:\n  PSHELL\n  PSHELL USAGE\n  PSHELL LIST-CATEGORIES\n  PSHELL <category>\n  PSHELL <term>\nExamples:\n  PSHELL PYTHON\n  PSHELL PY-VENV-CREATE\n  PSHELL CLEAN\nNotes:\n  - PSHELL is a read-only reference command; it does not execute PowerShell.\n"
        },
        {
            MessageId::AppendUsageBlankNoArgsNote,
            "APPEND_USAGE_BLANK_NO_ARGS_NOTE",
            "COMMAND:APPEND",
            "STATUS",
            "INFO",
            "APPEND with no arguments appends one blank record."
        },
        {
            MessageId::AppendUsageManySmartNote,
            "APPEND_USAGE_MANY_SMART_NOTE",
            "COMMAND:APPEND",
            "STATUS",
            "INFO",
            "APPEND MANY uses the smart batch append path."
        },
        {
            MessageId::AppendUsageRawNoInlineIndexNote,
            "APPEND_USAGE_RAW_NO_INLINE_INDEX_NOTE",
            "COMMAND:APPEND",
            "STATUS",
            "INFO",
            "APPEND RAW uses the raw append path without inline index update."
        },
        {
            MessageId::AppendUsageRawManyLine,
            "APPEND_USAGE_RAW_MANY_LINE",
            "COMMAND:APPEND",
            "ERROR",
            "ERROR",
            "Usage: APPEND RAW MANY <count>"
        },
        {
            MessageId::AppendUsageRawSummaryLine,
            "APPEND_USAGE_RAW_SUMMARY_LINE",
            "COMMAND:APPEND",
            "ERROR",
            "ERROR",
            "Usage: APPEND RAW | APPEND RAW MANY <count>"
        },
        {
            MessageId::AppendUsageManyLine,
            "APPEND_USAGE_MANY_LINE",
            "COMMAND:APPEND",
            "ERROR",
            "ERROR",
            "Usage: APPEND MANY <count>"
        },
        {
            MessageId::AppendInvalidCount,
            "APPEND_INVALID_COUNT",
            "COMMAND:APPEND",
            "ERROR",
            "ERROR",
            "invalid count '{value}'"
        },
        {
            MessageId::AppendTableLocked,
            "APPEND_TABLE_LOCKED",
            "COMMAND:APPEND",
            "ERROR",
            "ERROR",
            "table locked ({detail})"
        },
        {
            MessageId::AppendManyStopped,
            "APPEND_MANY_STOPPED",
            "COMMAND:APPEND",
            "ERROR",
            "ERROR",
            "MANY stopped after {count} successful append(s)"
        },
        {
            MessageId::AppendFailed,
            "APPEND_FAILED",
            "COMMAND:APPEND",
            "ERROR",
            "ERROR",
            "append failed"
        },
        {
            MessageId::AppendRawManyStopped,
            "APPEND_RAW_MANY_STOPPED",
            "COMMAND:APPEND",
            "ERROR",
            "ERROR",
            "RAW MANY stopped after {count} successful append(s)"
        },
        {
            MessageId::AppendManySuccess,
            "APPEND_MANY_SUCCESS",
            "COMMAND:APPEND",
            "STATUS",
            "INFO",
            "Appended {count} blank record(s)"
        },
        {
            MessageId::AppendRawManySuccess,
            "APPEND_RAW_MANY_SUCCESS",
            "COMMAND:APPEND",
            "STATUS",
            "INFO",
            "Appended {count} raw blank record(s)"
        },
        {
            MessageId::AppendBlankSuccess,
            "APPEND_BLANK_SUCCESS",
            "COMMAND:APPEND",
            "STATUS",
            "INFO",
            "Appended blank record {recno}"
        },
        {
            MessageId::AppendBlankUsageSharedNote,
            "APPEND_BLANK_USAGE_SHARED_NOTE",
            "COMMAND:APPEND_BLANK",
            "STATUS",
            "INFO",
            "Appends one blank record through shared append support."
        },
        {
            MessageId::SetVarUsageLine,
            "SET_VAR_USAGE_LINE",
            "SUBSYSTEM:SHELL_VARS",
            "ERROR",
            "ERROR",
            "Usage: SET VAR <name> = <text>"
        },
        {
            MessageId::ShowVarUsageLine,
            "SHOW_VAR_USAGE_LINE",
            "SUBSYSTEM:SHELL_VARS",
            "ERROR",
            "ERROR",
            "Usage: SHOW VAR [<name>]"
        },
        {
            MessageId::ClearVarUsageLine,
            "CLEAR_VAR_USAGE_LINE",
            "SUBSYSTEM:SHELL_VARS",
            "ERROR",
            "ERROR",
            "Usage: CLEAR VAR <name|ALL>"
        },
        {
            MessageId::VarInvalidName,
            "VAR_INVALID_NAME",
            "SUBSYSTEM:SHELL_VARS",
            "ERROR",
            "ERROR",
            "invalid name: {name}"
        },
        {
            MessageId::VarBangEvalError,
            "VAR_BANG_EVAL_ERROR",
            "SUBSYSTEM:SHELL_VARS",
            "ERROR",
            "ERROR",
            "{detail}"
        },
        {
            MessageId::VarsDefinedCount,
            "VARS_DEFINED_COUNT",
            "SUBSYSTEM:SHELL_VARS",
            "STATUS",
            "INFO",
            "VARS: {count} defined."
        },
        {
            MessageId::VarNotDefined,
            "VAR_NOT_DEFINED",
            "SUBSYSTEM:SHELL_VARS",
            "ERROR",
            "ERROR",
            "VAR not defined: {name}"
        },
        {
            MessageId::VarCommandUsageLine,
            "VAR_COMMAND_USAGE_LINE",
            "SUBSYSTEM:SHELL_VARS",
            "ERROR",
            "ERROR",
            "Usage: SET VAR | SHOW VAR | CLEAR VAR"
        },
        {
            MessageId::AggsFamilyTitle,
            "AGGS_FAMILY_TITLE",
            "COMMAND:AGGS",
            "STATUS",
            "INFO",
            "Aggregate verbs owned by AGGS"
        },
        {
            MessageId::AggsDirectVerbsTitle,
            "AGGS_DIRECT_VERBS_TITLE",
            "COMMAND:AGGS",
            "STATUS",
            "INFO",
            "Direct aggregate verbs:"
        },
        {
            MessageId::AggUsageHeading,
            "AGG_USAGE_HEADING",
            "COMMAND:AGGS",
            "STATUS",
            "INFO",
            "usage:"
        },
        {
            MessageId::AggErrorDetail,
            "AGG_ERROR_DETAIL",
            "COMMAND:AGGS",
            "ERROR",
            "ERROR",
            "error: {detail}"
        },
        {
            MessageId::AggsOwnerNote,
            "AGGS_OWNER_NOTE",
            "COMMAND:AGGS",
            "STATUS",
            "INFO",
            "AGGS owns the usage/help contract for these aggregate verbs."
        },
        {
            MessageId::AggsDirectAliasNote,
            "AGGS_DIRECT_ALIAS_NOTE",
            "COMMAND:AGGS",
            "STATUS",
            "INFO",
            "Direct SUM, AVG, MIN, and MAX are command aliases for normal use."
        },
        {
            MessageId::AggsForWhereAcceptedNote,
            "AGGS_FOR_WHERE_ACCEPTED_NOTE",
            "COMMAND:AGGS",
            "STATUS",
            "INFO",
            "FOR and WHERE are both accepted predicate introducers."
        },
        {
            MessageId::AggsDeletedOnlyNote,
            "AGGS_DELETED_ONLY_NOTE",
            "COMMAND:AGGS",
            "STATUS",
            "INFO",
            "DELETED limits the aggregate to deleted records."
        },
        {
            MessageId::AggsNotDeletedOnlyNote,
            "AGGS_NOT_DELETED_ONLY_NOTE",
            "COMMAND:AGGS",
            "STATUS",
            "INFO",
            "NOT DELETED and !DELETED limit the aggregate to visible/non-deleted records."
        },
        {
            MessageId::AggsCursorRestoreNote,
            "AGGS_CURSOR_RESTORE_NOTE",
            "COMMAND:AGGS",
            "STATUS",
            "INFO",
            "Aggregate scans restore the cursor best-effort."
        },
        {
            MessageId::AggsReadOnlyNote,
            "AGGS_READ_ONLY_NOTE",
            "COMMAND:AGGS",
            "STATUS",
            "INFO",
            "Aggregates report values; they do not mutate table data."
        },
        {
            MessageId::AggUsageOwnerNote,
            "AGG_USAGE_OWNER_NOTE",
            "COMMAND:AGGS",
            "STATUS",
            "INFO",
            "AGGS owns this usage contract."
        },
        {
            MessageId::AggUsageDirectVerbNote,
            "AGG_USAGE_DIRECT_VERB_NOTE",
            "COMMAND:AGGS",
            "STATUS",
            "INFO",
            "{verb} is the direct aggregate verb for normal command-line use."
        },
        {
            MessageId::AggUsageReadOnlyNote,
            "AGG_USAGE_READ_ONLY_NOTE",
            "COMMAND:AGGS",
            "STATUS",
            "INFO",
            "This aggregate reports a value and does not mutate table data."
        },
        {
            MessageId::AutoDbfUsageLine,
            "AUTODBF_USAGE_LINE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "AUTODBF <table> FROM <csvfile> [HEADER|NOHEADER|AUTO] [INFER|TEXTONLY] [OVERWRITE]"
        },
        {
            MessageId::AutoDbfUsageX64Line,
            "AUTODBF_USAGE_X64_LINE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "AUTODBF X64 <table> FROM <csvfile> [HEADER|NOHEADER|AUTO] [INFER|TEXTONLY] [OVERWRITE]"
        },
        {
            MessageId::AutoDbfDefaultFlavorNote,
            "AUTODBF_DEFAULT_FLAVOR_NOTE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "X64 table flavor"
        },
        {
            MessageId::AutoDbfDefaultHeaderNote,
            "AUTODBF_DEFAULT_HEADER_NOTE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "AUTO header detection, conservative"
        },
        {
            MessageId::AutoDbfDefaultInferNote,
            "AUTODBF_DEFAULT_INFER_NOTE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "INFER field types"
        },
        {
            MessageId::AutoDbfDefaultOverwriteNote,
            "AUTODBF_DEFAULT_OVERWRITE_NOTE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "no overwrite unless OVERWRITE is supplied"
        },
        {
            MessageId::AutoDbfCsvParserNote,
            "AUTODBF_CSV_PARSER_NOTE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "CSV parsing uses the existing comma CSV parser."
        },
        {
            MessageId::AutoDbfLongTextRejectedNote,
            "AUTODBF_LONG_TEXT_REJECTED_NOTE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "Long text is rejected for now rather than auto-promoted to M."
        },
        {
            MessageId::AutoDbfHeaderNormalizeNote,
            "AUTODBF_HEADER_NORMALIZE_NOTE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "Header names are normalized, uniquified, and sent through x64 fallback-name mangling."
        },
        {
            MessageId::AutoDbfMissingTableName,
            "AUTODBF_MISSING_TABLE_NAME",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "missing table name."
        },
        {
            MessageId::AutoDbfMissingTableNameAfterX64,
            "AUTODBF_MISSING_TABLE_NAME_AFTER_X64",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "missing table name after X64."
        },
        {
            MessageId::AutoDbfExpectedFrom,
            "AUTODBF_EXPECTED_FROM",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "expected FROM after table name."
        },
        {
            MessageId::AutoDbfMissingCsvFile,
            "AUTODBF_MISSING_CSV_FILE",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "missing CSV file name after FROM."
        },
        {
            MessageId::AutoDbfMaxCharRequiresValue,
            "AUTODBF_MAXCHAR_REQUIRES_VALUE",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "MAXCHAR requires a value."
        },
        {
            MessageId::AutoDbfInvalidMaxCharValue,
            "AUTODBF_INVALID_MAXCHAR_VALUE",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "invalid MAXCHAR value."
        },
        {
            MessageId::AutoDbfMaxCharRange,
            "AUTODBF_MAXCHAR_RANGE",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "MAXCHAR must be between 1 and 254."
        },
        {
            MessageId::AutoDbfUnknownOption,
            "AUTODBF_UNKNOWN_OPTION",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "unknown option '{option}'."
        },
        {
            MessageId::AutoDbfCannotOpenRead,
            "AUTODBF_CANNOT_OPEN_READ",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "Cannot open {path} for read."
        },
        {
            MessageId::AutoDbfEmptyCsv,
            "AUTODBF_EMPTY_CSV",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "Empty CSV."
        },
        {
            MessageId::AutoDbfColumnCountMismatch,
            "AUTODBF_COLUMN_COUNT_MISMATCH",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "column count mismatch"
        },
        {
            MessageId::AutoDbfTextWidthExceedsLimit,
            "AUTODBF_TEXT_WIDTH_EXCEEDS_LIMIT",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "text width {width} exceeds current fixed-field limit {limit}"
        },
        {
            MessageId::AutoDbfLongTextRequiresBytes,
            "AUTODBF_LONG_TEXT_REQUIRES_BYTES",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "long text requires {bytes} bytes; AUTODBF does not auto-promote to memo yet"
        },
        {
            MessageId::AutoDbfMemoInferenceDisabled,
            "AUTODBF_MEMO_INFERENCE_DISABLED",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "memo inference is disabled for AUTODBF first pass"
        },
        {
            MessageId::AutoDbfFieldWidthOutOfRange,
            "AUTODBF_FIELD_WIDTH_OUT_OF_RANGE",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "field width {width} is outside current fixed-field limits"
        },
        {
            MessageId::AutoDbfDecimalCountInvalid,
            "AUTODBF_DECIMAL_COUNT_INVALID",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "decimal count {decimals} is invalid for width {width}"
        },
        {
            MessageId::AutoDbfColumnDetail,
            "AUTODBF_COLUMN_DETAIL",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "column {index} ({name}): {detail}"
        },
        {
            MessageId::AutoDbfCharacterWidthOverflow,
            "AUTODBF_CHARACTER_WIDTH_OVERFLOW",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "character width overflow"
        },
        {
            MessageId::AutoDbfInvalidNumericValue,
            "AUTODBF_INVALID_NUMERIC_VALUE",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "invalid numeric value"
        },
        {
            MessageId::AutoDbfNumericWidthOverflow,
            "AUTODBF_NUMERIC_WIDTH_OVERFLOW",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "numeric width overflow"
        },
        {
            MessageId::AutoDbfInvalidDateValue,
            "AUTODBF_INVALID_DATE_VALUE",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "invalid date value; expected YYYY-MM-DD"
        },
        {
            MessageId::AutoDbfInvalidLogicalValue,
            "AUTODBF_INVALID_LOGICAL_VALUE",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "invalid logical value"
        },
        {
            MessageId::AutoDbfUnsupportedFieldType,
            "AUTODBF_UNSUPPORTED_FIELD_TYPE",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "unsupported AUTODBF field type"
        },
        {
            MessageId::AutoDbfLineExpectedColumnsFound,
            "AUTODBF_LINE_EXPECTED_COLUMNS_FOUND",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "line {line}: expected {expected} column(s), found {found}"
        },
        {
            MessageId::AutoDbfLineColumnDetail,
            "AUTODBF_LINE_COLUMN_DETAIL",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "line {line}, column {column} ({name}): {detail}"
        },
        {
            MessageId::AutoDbfAppendBlankFailed,
            "AUTODBF_APPEND_BLANK_FAILED",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "line {line}: appendBlank failed"
        },
        {
            MessageId::AutoDbfSetFailed,
            "AUTODBF_SET_FAILED",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "line {line}, column {column} ({name}): set failed"
        },
        {
            MessageId::AutoDbfWriteCurrentFailed,
            "AUTODBF_WRITE_CURRENT_FAILED",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "line {line}: writeCurrent failed"
        },
        {
            MessageId::AutoDbfPlanTitle,
            "AUTODBF_PLAN_TITLE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "AUTODBF plan"
        },
        {
            MessageId::AutoDbfPlanCsvLine,
            "AUTODBF_PLAN_CSV_LINE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "  CSV: {path}"
        },
        {
            MessageId::AutoDbfPlanHeaderLine,
            "AUTODBF_PLAN_HEADER_LINE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "  Header: {mode}{suffix}"
        },
        {
            MessageId::AutoDbfPlanDataRowsLine,
            "AUTODBF_PLAN_DATA_ROWS_LINE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "  Data rows: {count}"
        },
        {
            MessageId::AutoDbfPlanColumnsLine,
            "AUTODBF_PLAN_COLUMNS_LINE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "  Columns: {count}"
        },
        {
            MessageId::AutoDbfPlanDescriptorSuffix,
            "AUTODBF_PLAN_DESCRIPTOR_SUFFIX",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "  descriptor={name}"
        },
        {
            MessageId::AutoDbfPlanSourceSuffix,
            "AUTODBF_PLAN_SOURCE_SUFFIX",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "  source='{name}'"
        },
        {
            MessageId::AutoDbfTargetExists,
            "AUTODBF_TARGET_EXISTS",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "target exists: {path}"
        },
        {
            MessageId::AutoDbfUseOverwriteNote,
            "AUTODBF_USE_OVERWRITE_NOTE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "Use OVERWRITE to replace it."
        },
        {
            MessageId::AutoDbfScanFailedAtLine,
            "AUTODBF_SCAN_FAILED_AT_LINE",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "{detail} at line {line} (expected {expected}, found {found})"
        },
        {
            MessageId::AutoDbfNoDataRows,
            "AUTODBF_NO_DATA_ROWS",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "no data rows found."
        },
        {
            MessageId::AutoDbfCreateFailed,
            "AUTODBF_CREATE_FAILED",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "create failed: {detail}"
        },
        {
            MessageId::AutoDbfReopenFailedDetail,
            "AUTODBF_REOPEN_FAILED_DETAIL",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "file written but could not reopen table: {detail}"
        },
        {
            MessageId::AutoDbfReopenFailedGeneric,
            "AUTODBF_REOPEN_FAILED_GENERIC",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "file written but could not reopen table."
        },
        {
            MessageId::AutoDbfImportFailed,
            "AUTODBF_IMPORT_FAILED",
            "COMMAND:AUTODBF",
            "ERROR",
            "ERROR",
            "failed during import: {detail}"
        },
        {
            MessageId::AutoDbfPartialRowsImported,
            "AUTODBF_PARTIAL_ROWS_IMPORTED",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "  Partial rows imported: {count}"
        },
        {
            MessageId::AutoDbfOkTitle,
            "AUTODBF_OK_TITLE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "AUTODBF OK"
        },
        {
            MessageId::AutoDbfCreatedLine,
            "AUTODBF_CREATED_LINE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "  Created: {path} [X64]"
        },
        {
            MessageId::AutoDbfImportedRowsLine,
            "AUTODBF_IMPORTED_ROWS_LINE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "  Imported rows: {count}"
        },
        {
            MessageId::AutoDbfOpenedLine,
            "AUTODBF_OPENED_LINE",
            "COMMAND:AUTODBF",
            "STATUS",
            "INFO",
            "  Opened: {path}"
        },
        {
            MessageId::AboutUsageLine,
            "ABOUT_USAGE_LINE",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "ABOUT"
        },
        {
            MessageId::AboutUsageUsageLine,
            "ABOUT_USAGE_USAGE_LINE",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "ABOUT USAGE"
        },
        {
            MessageId::AboutPage1Text,
            "ABOUT_PAGE1_TEXT",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "ABOUT - Page 1 of 2\n"
            "===================\n"
            "\n"
            "DotTalk++\n"
            "\n"
            "Author\n"
            " Derald Grimwood\n"
            "\n"
            "Dedicated to\n"
            " Kathy Grimwood\n"
            "\n"
            "Project\n"
            " DotTalk++ is a modern C++ xBase-inspired database runtime and command shell.\n"
            "\n"
            "Heritage\n"
            " The DotTalk++ command model draws inspiration from the classic xBase\n"
            " lineage of database languages:\n"
            "\n"
            " dBase - early interactive database shell\n"
            " Clipper - compiled xBase systems\n"
            " FoxPro - relational navigation and index-driven querying\n"
            "\n"
            " DotTalk++ preserves many of the familiar commands and workflows from\n"
            " these systems while extending them with:\n"
            "\n"
            " modern help catalogs\n"
            " relational traversal (REL ENUM)\n"
            " tuple projection\n"
            " scripting and automation\n"
            "\n"
            " DotTalk++ also combines aspects of both the interactive xBase model\n"
            " and the compiled application model. Like dBase and FoxPro, it provides\n"
            " a live command shell for exploring data. Like Clipper, it can be extended\n"
            " through source code and compiled. It is also structured as modular\n"
            " runtime libraries, including xbase and xindex, beneath the shell.\n"
            "\n"
            "History\n"
            " The project traces back to 1993, when Derald Grimwood wrote a small\n"
            " ANSI C database program as a practical and experimental system,\n"
            " including fixed-length record storage and a simple in-memory B-tree.\n"
            "\n"
            " In 2025, that earlier work was revived and used as the conceptual basis\n"
            " for a modern 64-bit rebuild in C++. The result became DotTalk++:\n"
            " not a direct port, but a broader reimplementation and expansion.\n"
            "\n"
            "Current Direction\n"
            " DotTalk++ aims to retain the clarity of the xBase interaction model\n"
            " while making the engine suitable for modern experimentation and\n"
            " education.\n"
            "\n"
            " It is intended to serve as:\n"
            " - a working DBF database runtime\n"
            " - a relational exploration environment\n"
            " - a scripting and automation shell\n"
            " - a teaching system for database concepts\n"
            "\n"
            " Internally, DotTalk++ is also organized as a modular system:\n"
            " - xbase : core DBF/table/runtime library\n"
            " - xindex : indexing library\n"
            " - dottalk : command shell and interactive environment\n"
            "\n"
            " In this sense, DotTalk++ sits between FoxPro and Clipper:\n"
            " - interactive and stateful like FoxPro\n"
            " - extensible and compilable like Clipper\n"
            "\n"
            "Design Philosophy\n"
            " DotTalk++ is intentionally stateful and interactive.\n"
            "\n"
            " It exposes important runtime concepts directly, including:\n"
            " - current work area\n"
            " - current record pointer\n"
            " - active order/index\n"
            " - active filter\n"
            " - relation graph\n"
            " - buffering state\n"
            "\n"
            " The goal is to make database behavior visible and understandable during\n"
            " live operation, rather than hiding it behind abstraction.\n"
            "\n"
            "Working Model\n"
            " DotTalk++ can be understood as four cooperating layers:\n"
            "\n"
            " 1. Command Layer - interactive commands and scripting\n"
            " 2. Data Layer - tables, records, fields, indexes\n"
            " 3. Logic Layer - expressions, predicates, control flow\n"
            " 4. Projection Layer - LIST, SMARTLIST, TUPLE, REL ENUM, browsers\n"
            "\n"
            "Runtime Environment\n"
            " OS family   : {os_family}\n"
            " Architecture: {arch}\n"
            " C++ standard: {cpp_standard}\n"
            " Compiler    : {compiler}\n"
            "\n"
            "Years\n"
            " Origin: 1993 ANSI C\n"
            " Revival / C++ X64 modern rebuild: 2025-\n"
            "\n"
            "Summary\n"
            " DotTalk++ honors the xBase tradition while extending it into a modern,\n"
            " teachable, experiment-friendly database runtime.\n"
            "\n"
            " User interfaces change, languages change, but the underlying database principles remain constant. -- Derald Grimwood"
        },
        {
            MessageId::AboutPage2Title,
            "ABOUT_PAGE2_TITLE",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "ABOUT - Page 2 of 2"
        },
        {
            MessageId::AboutSectionApplication,
            "ABOUT_SECTION_APPLICATION",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Application"
        },
        {
            MessageId::AboutSectionOperatingSystem,
            "ABOUT_SECTION_OPERATING_SYSTEM",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Operating System"
        },
        {
            MessageId::AboutSectionHardware,
            "ABOUT_SECTION_HARDWARE",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Hardware"
        },
        {
            MessageId::AboutSectionStorage,
            "ABOUT_SECTION_STORAGE",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Storage"
        },
        {
            MessageId::AboutSectionConsole,
            "ABOUT_SECTION_CONSOLE",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Console"
        },
        {
            MessageId::AboutSectionNetwork,
            "ABOUT_SECTION_NETWORK",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Network"
        },
        {
            MessageId::AboutSectionCurrentSession,
            "ABOUT_SECTION_CURRENT_SESSION",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Current Session"
        },
        {
            MessageId::AboutKeyName,
            "ABOUT_KEY_NAME",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Name"
        },
        {
            MessageId::AboutKeyBuildMode,
            "ABOUT_KEY_BUILD_MODE",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Build Mode"
        },
        {
            MessageId::AboutKeyBuildDate,
            "ABOUT_KEY_BUILD_DATE",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Build Date"
        },
        {
            MessageId::AboutKeyArchitecture,
            "ABOUT_KEY_ARCHITECTURE",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Architecture"
        },
        {
            MessageId::AboutKeyCompiler,
            "ABOUT_KEY_COMPILER",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Compiler"
        },
        {
            MessageId::AboutKeyCppStd,
            "ABOUT_KEY_CPP_STD",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "C++ Std"
        },
        {
            MessageId::AboutKeyOs,
            "ABOUT_KEY_OS",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "OS"
        },
        {
            MessageId::AboutKeyCpuThreads,
            "ABOUT_KEY_CPU_THREADS",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "CPU Threads"
        },
        {
            MessageId::AboutKeyInstalledRam,
            "ABOUT_KEY_INSTALLED_RAM",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Installed RAM"
        },
        {
            MessageId::AboutKeyDiskRoot,
            "ABOUT_KEY_DISK_ROOT",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Disk Root"
        },
        {
            MessageId::AboutKeyDiskFree,
            "ABOUT_KEY_DISK_FREE",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Disk Free"
        },
        {
            MessageId::AboutKeyDiskTotal,
            "ABOUT_KEY_DISK_TOTAL",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Disk Total"
        },
        {
            MessageId::AboutKeySize,
            "ABOUT_KEY_SIZE",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Size"
        },
        {
            MessageId::AboutKeyAnsiVt,
            "ABOUT_KEY_ANSI_VT",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "ANSI / VT"
        },
        {
            MessageId::AboutKeyComputerName,
            "ABOUT_KEY_COMPUTER_NAME",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Computer Name"
        },
        {
            MessageId::AboutKeyLocalIpv4,
            "ABOUT_KEY_LOCAL_IPV4",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Local IPv4"
        },
        {
            MessageId::AboutKeyFileOpen,
            "ABOUT_KEY_FILE_OPEN",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "File Open"
        },
        {
            MessageId::AboutKeyDbfile,
            "ABOUT_KEY_DBFILE",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Dbfile"
        },
        {
            MessageId::AboutKeyRecords,
            "ABOUT_KEY_RECORDS",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Records"
        },
        {
            MessageId::AboutKeyFields,
            "ABOUT_KEY_FIELDS",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Fields"
        },
        {
            MessageId::AboutYes,
            "ABOUT_YES",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "Yes"
        },
        {
            MessageId::AboutNo,
            "ABOUT_NO",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "No"
        },
        {
            MessageId::AboutEnabled,
            "ABOUT_ENABLED",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "enabled"
        },
        {
            MessageId::AboutDisabled,
            "ABOUT_DISABLED",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "disabled"
        },
        {
            MessageId::AboutNone,
            "ABOUT_NONE",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "(none)"
        },
        {
            MessageId::AboutUnavailable,
            "ABOUT_UNAVAILABLE",
            "COMMAND:ABOUT",
            "STATUS",
            "INFO",
            "(unavailable)"
        },
        {
            MessageId::ShellStartupBannerLine,
            "SHELL_STARTUP_BANNER_LINE",
            "SUBSYSTEM:SHELL",
            "STATUS",
            "INFO",
            "DotTalk++ type HELP. USE, SELECT <n>, AREA, COLOR <GREEN|AMBER|DEFAULT>, ABOUT, QUIT."
        },
        {
            MessageId::ShellStartupDevLine,
            "SHELL_STARTUP_DEV_LINE",
            "SUBSYSTEM:SHELL",
            "STATUS",
            "INFO",
            "Dev: CMDHELPCHK, GPS, WORKSPACE, ERSATZ."
        },
        {
            MessageId::ShellStartupHelloLine,
            "SHELL_STARTUP_HELLO_LINE",
            "SUBSYSTEM:SHELL",
            "STATUS",
            "INFO",
            "Hello World!"
        },
        {
            MessageId::ShellBlockCancelled,
            "SHELL_BLOCK_CANCELLED",
            "SUBSYSTEM:SHELL",
            "STATUS",
            "INFO",
            "BLOCK: cancelled"
        },
        {
            MessageId::ShellLoopBlockCancelled,
            "SHELL_LOOP_BLOCK_CANCELLED",
            "SUBSYSTEM:SHELL",
            "STATUS",
            "INFO",
            "LOOP BLOCK: cancelled"
        },
        {
            MessageId::ShellQuitCanceled,
            "SHELL_QUIT_CANCELED",
            "SUBSYSTEM:SHELL",
            "STATUS",
            "INFO",
            "QUIT canceled."
        },
        {
            MessageId::BuildLmdbUsageText,
            "BUILDLMDB_USAGE_TEXT",
            "COMMAND:BUILDLMDB",
            "STATUS",
            "INFO",
            "Usage: BUILDLMDB [HELP|?] [MAPSIZE <n[K|M|G]> | SIZE <n[K|M|G]> |\n"
            "                  TINY|SMALL|MEDIUM|LARGE|XL|HUGE]\n"
            "                 [YES|AUTO|NOPROMPT] [CLEAN|FORCE] [QUIET]\n"
            "\n"
            "  BUILDLMDB\n"
            "      Rebuild LMDB backing store for the current CDX container.\n"
            "      Default mapsize is 128 MiB.\n"
            "\n"
            "  BUILDLMDB SMALL\n"
            "      Use preset mapsize 64 MiB.\n"
            "\n"
            "  BUILDLMDB MEDIUM\n"
            "      Use preset mapsize 128 MiB.\n"
            "\n"
            "  BUILDLMDB LARGE\n"
            "      Use preset mapsize 256 MiB.\n"
            "\n"
            "  BUILDLMDB MAPSIZE 1G YES\n"
            "      Rebuild using 1 GiB mapsize for empirical/speed testing.\n"
            "\n"
            "  BUILDLMDB CLEAN MAPSIZE 512M YES\n"
            "      Archive existing LMDB env first, then rebuild at 512 MiB.\n"
            "\n"
            "Presets:\n"
            "  TINY=32 MiB  SMALL=64 MiB  MEDIUM=128 MiB\n"
            "  LARGE=256 MiB  XL=512 MiB  HUGE=1 GiB"
        },
        {
            MessageId::BuildLmdbEnvPathNotDirectory,
            "BUILDLMDB_ENV_PATH_NOT_DIRECTORY",
            "COMMAND:BUILDLMDB",
            "ERROR",
            "ERROR",
            "env path exists but is not a directory: {path}"
        },
        {
            MessageId::BuildLmdbUnableCreateBackupsDir,
            "BUILDLMDB_UNABLE_CREATE_BACKUPS_DIR",
            "COMMAND:BUILDLMDB",
            "ERROR",
            "ERROR",
            "unable to create backups dir: {path}"
        },
        {
            MessageId::BuildLmdbCopyFailed,
            "BUILDLMDB_COPY_FAILED",
            "COMMAND:BUILDLMDB",
            "ERROR",
            "ERROR",
            "copy failed: {detail}"
        },
        {
            MessageId::BuildLmdbRemoveAllFailed,
            "BUILDLMDB_REMOVE_ALL_FAILED",
            "COMMAND:BUILDLMDB",
            "ERROR",
            "ERROR",
            "remove_all failed after copy: {detail}"
        },
        {
            MessageId::BuildLmdbArchivedEnvdir,
            "BUILDLMDB_ARCHIVED_ENVDIR",
            "COMMAND:BUILDLMDB",
            "STATUS",
            "INFO",
            "archived envdir to: {path}"
        },
        {
            MessageId::BuildLmdbLmdbStepTagFailed,
            "BUILDLMDB_LMDB_STEP_TAG_FAILED",
            "COMMAND:BUILDLMDB",
            "ERROR",
            "ERROR",
            "{step} failed for tag {tag}: {code} ({detail})"
        },
        {
            MessageId::BuildLmdbPutFailed,
            "BUILDLMDB_PUT_FAILED",
            "COMMAND:BUILDLMDB",
            "ERROR",
            "ERROR",
            "put failed for tag {tag} rec {recno}: {code} ({detail})"
        },
        {
            MessageId::BuildLmdbUnableCreateEnvDir,
            "BUILDLMDB_UNABLE_CREATE_ENV_DIR",
            "COMMAND:BUILDLMDB",
            "ERROR",
            "ERROR",
            "unable to create env dir: {path}"
        },
        {
            MessageId::BuildLmdbLmdbStepFailed,
            "BUILDLMDB_LMDB_STEP_FAILED",
            "COMMAND:BUILDLMDB",
            "ERROR",
            "ERROR",
            "{step} failed: {code} ({detail})"
        },
        {
            MessageId::BuildLmdbMapsizeRequiresValue,
            "BUILDLMDB_MAPSIZE_REQUIRES_VALUE",
            "COMMAND:BUILDLMDB",
            "ERROR",
            "ERROR",
            "{keyword} requires a value like 64M, 128M, 1G."
        },
        {
            MessageId::BuildLmdbInvalidMapsize,
            "BUILDLMDB_INVALID_MAPSIZE",
            "COMMAND:BUILDLMDB",
            "ERROR",
            "ERROR",
            "invalid mapsize: {value}"
        },
        {
            MessageId::BuildLmdbUnknownOptions,
            "BUILDLMDB_UNKNOWN_OPTIONS",
            "COMMAND:BUILDLMDB",
            "ERROR",
            "ERROR",
            "unknown option(s): {options}"
        },
        {
            MessageId::BuildLmdbNoTableOpen,
            "BUILDLMDB_NO_TABLE_OPEN",
            "COMMAND:BUILDLMDB",
            "ERROR",
            "ERROR",
            "No table open."
        },
        {
            MessageId::BuildLmdbTargetContainerLine,
            "BUILDLMDB_TARGET_CONTAINER_LINE",
            "COMMAND:BUILDLMDB",
            "STATUS",
            "INFO",
            "target container {path}"
        },
        {
            MessageId::BuildLmdbEnvLine,
            "BUILDLMDB_ENV_LINE",
            "COMMAND:BUILDLMDB",
            "STATUS",
            "INFO",
            "LMDB env        {path}"
        },
        {
            MessageId::BuildLmdbMapsizeInfoLine,
            "BUILDLMDB_MAPSIZE_INFO_LINE",
            "COMMAND:BUILDLMDB",
            "STATUS",
            "INFO",
            "mapsize         {value}"
        },
        {
            MessageId::BuildLmdbDestructiveWarningText,
            "BUILDLMDB_DESTRUCTIVE_WARNING_TEXT",
            "COMMAND:BUILDLMDB",
            "WARNING",
            "WARNING",
            "\nWARNING: LMDB environment directory already exists and appears to contain data:\n"
            "  {path}\n"
            "Rebuilding will DROP and recreate all tag databases inside it.\n"
            "This is a destructive operation -- existing index data will be lost.\n"
            "\n"
            "BUILDLMDB: confirmation required. Re-run with YES, AUTO, or NOPROMPT.\n"
            "Examples:\n"
            "  BUILDLMDB YES\n"
            "  BUILDLMDB CLEAN YES\n"
            "  BUILDLMDB MAPSIZE 1G YES"
        },
        {
            MessageId::BuildLmdbAutoConfirmed,
            "BUILDLMDB_AUTO_CONFIRMED",
            "COMMAND:BUILDLMDB",
            "STATUS",
            "INFO",
            "auto-confirmed rebuild of existing env."
        },
        {
            MessageId::BuildLmdbReleasingActiveIndex,
            "BUILDLMDB_RELEASING_ACTIVE_INDEX",
            "COMMAND:BUILDLMDB",
            "STATUS",
            "INFO",
            "releasing active index/order before rebuild."
        },
        {
            MessageId::BuildLmdbArchiveFailedAborting,
            "BUILDLMDB_ARCHIVE_FAILED_ABORTING",
            "COMMAND:BUILDLMDB",
            "ERROR",
            "ERROR",
            "archive failed - aborting."
        },
        {
            MessageId::BuildLmdbTagOkLine,
            "BUILDLMDB_TAG_OK_LINE",
            "COMMAND:BUILDLMDB",
            "STATUS",
            "INFO",
            " [{index}] {tag} : OK"
        },
        {
            MessageId::BuildLmdbDoneTagsRebuilt,
            "BUILDLMDB_DONE_TAGS_REBUILT",
            "COMMAND:BUILDLMDB",
            "STATUS",
            "INFO",
            "done OK={count} tags rebuilt."
        },
        {
            MessageId::BuildLmdbCdxContainerLine,
            "BUILDLMDB_CDX_CONTAINER_LINE",
            "COMMAND:BUILDLMDB",
            "STATUS",
            "INFO",
            "CDX container   : {path}"
        },
        {
            MessageId::BuildLmdbLmdbEnvironmentLine,
            "BUILDLMDB_LMDB_ENVIRONMENT_LINE",
            "COMMAND:BUILDLMDB",
            "STATUS",
            "INFO",
            "LMDB environment: {path}"
        },
        {
            MessageId::BuildLmdbMapsizeReportLine,
            "BUILDLMDB_MAPSIZE_REPORT_LINE",
            "COMMAND:BUILDLMDB",
            "STATUS",
            "INFO",
            "Mapsize         : {value}"
        },
        {
            MessageId::BuildLmdbFailedToBuildEnv,
            "BUILDLMDB_FAILED_TO_BUILD_ENV",
            "COMMAND:BUILDLMDB",
            "ERROR",
            "ERROR",
            "failed to build LMDB environment."
        },
        {
            MessageId::BBoxUsageText,
            "BBOX_USAGE_TEXT",
            "COMMAND:BBOX",
            "STATUS",
            "INFO",
            "Usage:\n"
            "  BBOX\n"
            "  BBOX USAGE\n"
            "  BBOX MODEL\n"
            "  BBOX LANES\n"
            "  BBOX COMMENTS\n"
            "  BBOX HELP\n"
            "  BBOX MANUALGEN\n"
            "  BBOX DATADICT\n"
            "  BBOX MESSAGING\n"
            "  BBOX MAINT\n"
            "Notes:\n"
            "  - BBOX is read-only and educational.\n"
            "  - BBOX teaches the Blackbox model: data in, processing, information out.\n"
            "  - BBOX does not mutate DBFs, HELP, META, CMDHELPCHK, source, scripts, or publications."
        },
        {
            MessageId::BBoxModelText,
            "BBOX_MODEL_TEXT",
            "COMMAND:BBOX",
            "STATUS",
            "INFO",
            "BLACKBOX MODEL\n"
            "  DATA IN\n"
            "    source comments, usage contracts, DBFs, scripts, Markdown, media, source code, catalogs\n"
            "\n"
            "  PROCESSING\n"
            "    scan, harvest, classify, import, build, validate, publish, smoke test\n"
            "\n"
            "  INFORMATION OUT\n"
            "    HELP, CMDHELP, manuals, data dictionary, comments workspace, MAN*/DD*/SRC* catalogs, reports, diagrams\n"
            "\n"
            "  CONTROL\n"
            "    backup, rollback, boundary ledger, runtime smoke, savepoint, next gate"
        },
        {
            MessageId::BBoxLanesText,
            "BBOX_LANES_TEXT",
            "COMMAND:BBOX",
            "STATUS",
            "INFO",
            "BBOX LANES\n"
            "  COMMENTS   source comments and @dottalk.usage -> SRC* evidence catalogs\n"
            "  HELP       registry, DOTREF, usage contracts -> HELP DATA and CMDHELP\n"
            "  MANUALGEN  manual sections/media/manifests -> MAN* catalog and published manuals\n"
            "  DATADICT   repo/schema/help evidence -> DD* catalog and DDICT runtime view\n"
            "  MESSAGING  hard-coded text/message IDs/locales -> typed localized runtime messages\n"
            "  CMDHELPCHK command/help contracts -> validation evidence\n"
            "  MAINT      maintenance lanes, cookbooks, gates, and read-only status"
        },
        {
            MessageId::BBoxCommentsLaneText,
            "BBOX_COMMENTS_LANE_TEXT",
            "COMMAND:BBOX",
            "STATUS",
            "INFO",
            "COMMENTS BLACKBOX\n"
            "  DATA IN: source files, header comments, @dottalk.usage v1 blocks\n"
            "  PROCESS: harvest, classify, import, validate, review disposition\n"
            "  OUT: SRCFILE, SRCBLOCK, SRCLINE, SRCUSAGE, SRCCLASS, SRCDISP, SRCALIAS, MEMO_LINES\n"
            "  CURRENT WORKSPACE: dottalkpp/data/workspaces/comments.dtschema"
        },
        {
            MessageId::BBoxHelpLaneText,
            "BBOX_HELP_LANE_TEXT",
            "COMMAND:BBOX",
            "STATUS",
            "INFO",
            "HELP BLACKBOX\n"
            "  DATA IN: command registry, dotref.hpp, foxref.hpp, usage contracts, curated rows, source-mined facts\n"
            "  PROCESS: CMDHELP BUILD, HELP DATA generation, validation, runtime smoke\n"
            "  OUT: help_line.dbf, help_topic.dbf, help_artifacts.dbf, commands.dbf, cmd_args.dbf, HELP/CMDHELP output\n"
            "  NOTE: CMDHELP and HELP /DOT are related consumers but not identical proof surfaces."
        },
        {
            MessageId::BBoxManualgenLaneText,
            "BBOX_MANUALGEN_LANE_TEXT",
            "COMMAND:BBOX",
            "STATUS",
            "INFO",
            "MANUALGEN BLACKBOX\n"
            "  DATA IN: section files, appendices, media anchors, review queues, manifests\n"
            "  PROCESS: assemble, normalize, validate, publish, catalog, runtime smoke\n"
            "  OUT: published manual, MAN* catalog, MANUAL runtime command, regeneration evidence"
        },
        {
            MessageId::BBoxDatadictLaneText,
            "BBOX_DATADICT_LANE_TEXT",
            "COMMAND:BBOX",
            "STATUS",
            "INFO",
            "DATADICT BLACKBOX\n"
            "  DATA IN: data dictionary manifests, DD* candidate rows, x64 DATA_DICTIONARY_* physical tables\n"
            "  PROCESS: stage, import, validate, CDX/LMDB build, runtime smoke\n"
            "  OUT: DD* catalog, DDICT STATUS/TABLES/OBJECTS/FIELDS/TAGS/REL/EVIDENCE\n"
            "  RULE: use bridge policy; report metadata owner and physical artifact."
        },
        {
            MessageId::BBoxMessagingLaneText,
            "BBOX_MESSAGING_LANE_TEXT",
            "COMMAND:BBOX",
            "STATUS",
            "INFO",
            "MESSAGING BLACKBOX\n"
            "  DATA IN: hard-coded text, message IDs, message arguments, locale/language rows\n"
            "  PROCESS: extract, catalog, localize, validate placeholders, replace source strings gradually\n"
            "  OUT: x64base message catalog, localized runtime text, typed warnings/errors/status/help messages\n"
            "  CONTROL: SET LANGUAGE / SET LOCALE selects message-rendering locale where supported."
        },
        {
            MessageId::BBoxMaintLaneText,
            "BBOX_MAINT_LANE_TEXT",
            "COMMAND:BBOX",
            "STATUS",
            "INFO",
            "MAINT BLACKBOX\n"
            "  PURPOSE: developer/SDLC maintenance inspection over documented lanes and cookbooks\n"
            "  PRIMARY APP: native C++ MAINT surface, planned separately\n"
            "  EXTERNAL TOOLS: Python 3.12 for portable report tooling; PowerShell only for temporary scaffolding\n"
            "  RULE: MAINT starts read-only; mutation lanes require explicit guarded packages."
        },
        {
            MessageId::BBoxUnknownTopic,
            "BBOX_UNKNOWN_TOPIC",
            "COMMAND:BBOX",
            "ERROR",
            "ERROR",
            "unknown topic: {topic}"
        },
        {
            MessageId::MaintUsageText,
            "MAINT_USAGE_TEXT",
            "COMMAND:MAINT",
            "STATUS",
            "INFO",
            "Usage:\n"
            "  MAINT\n"
            "  MAINT USAGE\n"
            "  MAINT STATUS\n"
            "  MAINT LANES\n"
            "  MAINT COOKBOOK\n"
            "  MAINT BOUNDARY\n"
            "  MAINT BBOX\n"
            "  MAINT DOCS\n"
            "  MAINT GUI\n"
            "  MAINT AI\n"
            "  MAINT AI USAGE\n"
            "  MAINT AI STATUS\n"
            "  MAINT AI DASHBOARD\n"
            "  MAINT AI ASSIMILATE\n"
            "  MAINT AI BOOK\n"
            "  MAINT AI INTAKE\n"
            "  MAINT AI GATES\n"
            "  MAINT AI VISIBILITY\n"
            "  MAINT CONTRACTS\n"
            "  MAINT CONTRACTS USAGE\n"
            "  MAINT CONTRACTS STATUS\n"
            "  MAINT CONTRACTS SCAN\n"
            "  MAINT CONTRACTS REGISTRY\n"
            "  MAINT CONTRACTS INTAKE\n"
            "  MAINT CONTRACTS DRIFT\n"
            "  MAINT CONTRACTS GATES\n"
            "Notes:\n"
            "  - MAINT is read-only first wave.\n"
            "  - MAINT inspects maintenance lanes, cookbooks, status, and boundaries.\n"
            "  - MAINT AI is a read-only native visibility surface for AI Portal partner onboarding and routing.\n"
            "  - MAINT AI ASSIMILATE points new or second-opinion AI development partners to the repo-local AI Portal.\n"
            "  - The AI Portal is an Alpha Python/registry surface; MAINT AI does not launch it or grant mutation authority.\n"
            "  - MAINT does not run scripts or mutate HELP, CMDHELPCHK, DBFs, source, runtime scripts, or publications."
        },
        {
            MessageId::MaintStatusText,
            "MAINT_STATUS_TEXT",
            "COMMAND:MAINT",
            "STATUS",
            "INFO",
            "MAINT STATUS\n"
            "  mode: read-only\n"
            "  purpose: inspect DotTalk++ maintenance/SDLC lanes and boundaries\n"
            "  native app: yes, C++ command surface\n"
            "  executes maintenance scripts: no\n"
            "  mutates protected systems: no\n"
            "  related teaching surface: BBOX"
        },
        {
            MessageId::MaintLanesText,
            "MAINT_LANES_TEXT",
            "COMMAND:MAINT",
            "STATUS",
            "INFO",
            "MAINT LANES\n"
            "  comments    - source comments and @dottalk.usage evidence\n"
            "  help        - HELP, CMDHELP, DOTREF, and help-route evidence\n"
            "  cmdhelpchk  - HELP/registry/source-contract validation\n"
            "  manualgen   - developer manual generation and MAN* catalog evidence\n"
            "  datadict    - DD* / DATA_DICTIONARY_* catalog and DDICT evidence\n"
            "  messaging   - message catalog, language/locale, and output text migration\n"
            "  ai-friendly - AI-assisted work capture, curation, routing, and user visibility\n"
            "  gui         - wx, Python/Tkinter, and TUI synchronization over shared runtime contracts\n"
            "  contracts   - durable rules, usage contracts, registry, intake, and drift review\n"
            "  blackbox    - data in, processing, information out teaching model\n"
            "  maintenance - SDLC cookbooks, gates, boundaries, and closeouts"
        },
        {
            MessageId::MaintCookbookText,
            "MAINT_COOKBOOK_TEXT",
            "COMMAND:MAINT",
            "STATUS",
            "INFO",
            "MAINT COOKBOOK\n"
            "  docs root   : docs\\maintenance\n"
            "  script root : dottalkpp\\scripts\\maintenance\n"
            "  runtime scripts stay under dottalkpp\\data\\scripts\n"
            "  native source support is reserved under src\\maintenance when needed\n"
            "  PowerShell is temporary MDO scaffolding; permanent app surface is C++.\n"
            "  Python 3.12 may support portable external helper/report tooling."
        },
        {
            MessageId::MaintBoundaryText,
            "MAINT_BOUNDARY_TEXT",
            "COMMAND:MAINT",
            "STATUS",
            "INFO",
            "MAINT BOUNDARY\n"
            "  first-wave MAINT is inspection-only.\n"
            "  It must not mutate:\n"
            "    - source files\n"
            "    - HELP DATA or raw HELP DBFs\n"
            "    - CMDHELPCHK expectations\n"
            "    - metadata catalogs\n"
            "    - DBF/CDX/LMDB artifacts\n"
            "    - runtime scripts\n"
            "    - publications or media\n"
            "  Mutation lanes require separate guarded packages and explicit authorization."
        },
        {
            MessageId::MaintBboxRelationText,
            "MAINT_BBOX_RELATION_TEXT",
            "COMMAND:MAINT",
            "STATUS",
            "INFO",
            "MAINT BBOX\n"
            "  BBOX teaches the Blackbox model: data in, processing, information out.\n"
            "  MAINT inspects the SDLC maintenance controls around those transformations.\n"
            "  Relationship:\n"
            "    BBOX explains the model.\n"
            "    MAINT explains the maintenance process, gates, cookbooks, and boundaries."
        },
        {
            MessageId::MaintUnknownTopic,
            "MAINT_UNKNOWN_TOPIC",
            "COMMAND:MAINT",
            "ERROR",
            "ERROR",
            "unknown topic: {topic}\nUse MAINT USAGE."
        },
        {
            MessageId::DDictUsageText,
            "DDICT_USAGE_TEXT",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "Usage:\n"
            "  DDICT HELP\n"
            "  DDICT STATUS\n"
            "  DDICT TABLES\n"
            "  DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]\n"
            "  DDICT FIELDS <table>\n"
            "  DDICT TAGS <table>\n"
            "  DDICT REL <object-id-or-name> [IN|OUT|BOTH]\n"
            "  DDICT EVIDENCE <object-id-or-name>\n"
            "Notes:\n"
            "  DDICT is read-only over the active Data Dictionary catalog."
        },
        {
            MessageId::DDictStatusTitle,
            "DDICT_STATUS_TITLE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "DDICT STATUS"
        },
        {
            MessageId::DDictActiveCatalogLine,
            "DDICT_ACTIVE_CATALOG_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Active catalog: {path}"
        },
        {
            MessageId::DDictReadModeLine,
            "DDICT_READ_MODE_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Read mode     : READ-ONLY"
        },
        {
            MessageId::DDictDbfTablesLine,
            "DDICT_DBF_TABLES_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  DBF tables    : {present} / {expected}"
        },
        {
            MessageId::DDictDtxSidecarsLine,
            "DDICT_DTX_SIDECARS_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  DTX sidecars  : {present} / {expected}"
        },
        {
            MessageId::DDictDbfBytesLine,
            "DDICT_DBF_BYTES_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  DBF bytes     : {bytes}"
        },
        {
            MessageId::DDictCatalogStatePresentLine,
            "DDICT_CATALOG_STATE_PRESENT_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Catalog state : ACTIVE_CATALOG_PRESENT"
        },
        {
            MessageId::DDictCatalogStateReviewLine,
            "DDICT_CATALOG_STATE_REVIEW_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Catalog state : ACTIVE_CATALOG_REVIEW"
        },
        {
            MessageId::DDictTablesTitle,
            "DDICT_TABLES_TITLE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "DDICT TABLES"
        },
        {
            MessageId::DDictTablesColumnHeader,
            "DDICT_TABLES_COLUMN_HEADER",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Table       DBF  DTX  DBF_BYTES"
        },
        {
            MessageId::DDictTablesDivider,
            "DDICT_TABLES_DIVIDER",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  ----------  ---  ---  ---------"
        },
        {
            MessageId::DDictFieldsRequiresTableName,
            "DDICT_FIELDS_REQUIRES_TABLE_NAME",
            "COMMAND:DDICT",
            "ERROR",
            "ERROR",
            "FIELDS requires a table name."
        },
        {
            MessageId::DDictFieldsTitle,
            "DDICT_FIELDS_TITLE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "DDICT FIELDS {table}"
        },
        {
            MessageId::DDictFieldRowsLine,
            "DDICT_FIELD_ROWS_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Field rows    : {count}"
        },
        {
            MessageId::DDictMetadataOwnerLine,
            "DDICT_METADATA_OWNER_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Metadata owner: {owner}"
        },
        {
            MessageId::DDictFieldsNoFieldsLine,
            "DDICT_FIELDS_NO_FIELDS_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Result        : NO_FIELDS_FOUND"
        },
        {
            MessageId::DDictFieldsExpectedOwnersNote,
            "DDICT_FIELDS_EXPECTED_OWNERS_NOTE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Note          : expected DDOBJECT rows where OBJTYPE=CATALOG_FIELD and OWNER in {owners}"
        },
        {
            MessageId::DDictFieldsColumnHeader,
            "DDICT_FIELDS_COLUMN_HEADER",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Field       OBJID                     STATUS                    PROFILE       ATTRS"
        },
        {
            MessageId::DDictFieldsDivider,
            "DDICT_FIELDS_DIVIDER",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  ----------  ------------------------  ------------------------  ------------  -----"
        },
        {
            MessageId::DDictTagsRequiresTableName,
            "DDICT_TAGS_REQUIRES_TABLE_NAME",
            "COMMAND:DDICT",
            "ERROR",
            "ERROR",
            "TAGS requires a table name."
        },
        {
            MessageId::DDictTagsTitle,
            "DDICT_TAGS_TITLE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "DDICT TAGS {table}"
        },
        {
            MessageId::DDictTableDbfLine,
            "DDICT_TABLE_DBF_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Table DBF     : {value}"
        },
        {
            MessageId::DDictCdxArtifactLine,
            "DDICT_CDX_ARTIFACT_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  CDX artifact  : {value}"
        },
        {
            MessageId::DDictLmdbMirrorLine,
            "DDICT_LMDB_MIRROR_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  LMDB mirror   : {value}"
        },
        {
            MessageId::DDictCatalogTagsLine,
            "DDICT_CATALOG_TAGS_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Catalog tags  : {count}"
        },
        {
            MessageId::DDictTagsPhysicalNoCatalogLine,
            "DDICT_TAGS_PHYSICAL_NO_CATALOG_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Result        : PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS"
        },
        {
            MessageId::DDictTagsNoCatalogLine,
            "DDICT_TAGS_NO_CATALOG_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Result        : NO_CATALOG_TAGS_FOUND"
        },
        {
            MessageId::DDictTagsPhysicalArtifactsNote,
            "DDICT_TAGS_PHYSICAL_ARTIFACTS_NOTE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Note          : physical DBF/CDX/LMDB artifacts exist, but no DDOBJECT CATALOG_TAG rows were found for OWNER in {owners}"
        },
        {
            MessageId::DDictTagsExpectedOwnersNote,
            "DDICT_TAGS_EXPECTED_OWNERS_NOTE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Note          : expected DDOBJECT rows where OBJTYPE=CATALOG_TAG and OWNER in {owners}"
        },
        {
            MessageId::DDictTagsColumnHeader,
            "DDICT_TAGS_COLUMN_HEADER",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Tag         OBJID                     STATUS                    PROFILE       ATTRS"
        },
        {
            MessageId::DDictTagsDivider,
            "DDICT_TAGS_DIVIDER",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  ----------  ------------------------  ------------------------  ------------  -----"
        },
        {
            MessageId::DDictUnknownSubcommand,
            "DDICT_UNKNOWN_SUBCOMMAND",
            "COMMAND:DDICT",
            "ERROR",
            "ERROR",
            "unknown subcommand '{subcommand}'."
        },
        {
            MessageId::DDictRelRequiresObjectToken,
            "DDICT_REL_REQUIRES_OBJECT_TOKEN",
            "COMMAND:DDICT",
            "ERROR",
            "ERROR",
            "REL requires an object id or name."
        },
        {
            MessageId::DDictRelInvalidDirection,
            "DDICT_REL_INVALID_DIRECTION",
            "COMMAND:DDICT",
            "ERROR",
            "ERROR",
            "REL direction must be IN, OUT, or BOTH."
        },
        {
            MessageId::DDictRelTitle,
            "DDICT_REL_TITLE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "DDICT REL {token} {direction}"
        },
        {
            MessageId::DDictObjectNotFoundLine,
            "DDICT_OBJECT_NOT_FOUND_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Result        : OBJECT_NOT_FOUND"
        },
        {
            MessageId::DDictObjectLookupNote,
            "DDICT_OBJECT_LOOKUP_NOTE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Note          : token was matched against OBJID and DDOBJECT NAME/OWNER."
        },
        {
            MessageId::DDictObjectObjidLine,
            "DDICT_OBJECT_OBJID_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Object OBJID  : {value}"
        },
        {
            MessageId::DDictObjectTypeLine,
            "DDICT_OBJECT_TYPE_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Object type   : {value}"
        },
        {
            MessageId::DDictObjectOwnerLine,
            "DDICT_OBJECT_OWNER_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Object owner  : {value}"
        },
        {
            MessageId::DDictObjectNameLine,
            "DDICT_OBJECT_NAME_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Object name   : {value}"
        },
        {
            MessageId::DDictIncomingEdgesLine,
            "DDICT_INCOMING_EDGES_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Incoming edges: {count}"
        },
        {
            MessageId::DDictOutgoingEdgesLine,
            "DDICT_OUTGOING_EDGES_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Outgoing edges: {count}"
        },
        {
            MessageId::DDictRowsShownPerDirectionLine,
            "DDICT_ROWS_SHOWN_PER_DIRECTION_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Rows shown    : bounded to {count} per direction"
        },
        {
            MessageId::DDictRelColumnHeader,
            "DDICT_REL_COLUMN_HEADER",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Dir  EdgeType            OtherOBJ                  OtherType          OtherOwner      OtherName       EVID"
        },
        {
            MessageId::DDictRelDivider,
            "DDICT_REL_DIVIDER",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  ---  ------------------  ------------------------  -----------------  --------------  --------------  --------------------"
        },
        {
            MessageId::DDictEvidenceRequiresObjectToken,
            "DDICT_EVIDENCE_REQUIRES_OBJECT_TOKEN",
            "COMMAND:DDICT",
            "ERROR",
            "ERROR",
            "EVIDENCE requires an object id or name."
        },
        {
            MessageId::DDictEvidenceTitle,
            "DDICT_EVIDENCE_TITLE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "DDICT EVIDENCE {token}"
        },
        {
            MessageId::DDictDirectEvidenceRowsLine,
            "DDICT_DIRECT_EVIDENCE_ROWS_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Direct evidence rows: {count}"
        },
        {
            MessageId::DDictAttributeEvidenceRowsLine,
            "DDICT_ATTRIBUTE_EVIDENCE_ROWS_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Attribute evidence rows: {count}"
        },
        {
            MessageId::DDictRowsShownPerSectionLine,
            "DDICT_ROWS_SHOWN_PER_SECTION_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Rows shown    : bounded to {count} per section"
        },
        {
            MessageId::DDictEvidenceRowsTitle,
            "DDICT_EVIDENCE_ROWS_TITLE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Evidence rows"
        },
        {
            MessageId::DDictEvidenceColumnHeader,
            "DDICT_EVIDENCE_COLUMN_HEADER",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  EVID                  KIND                  SRCID                 SOURCE              ARTIFACT"
        },
        {
            MessageId::DDictEvidenceDivider,
            "DDICT_EVIDENCE_DIVIDER",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  --------------------  --------------------  --------------------  ------------------  ------------------"
        },
        {
            MessageId::DDictNoneLine,
            "DDICT_NONE_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  (none)"
        },
        {
            MessageId::DDictAttributeEvidenceTitle,
            "DDICT_ATTRIBUTE_EVIDENCE_TITLE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Attribute evidence"
        },
        {
            MessageId::DDictAttributeEvidenceColumnHeader,
            "DDICT_ATTRIBUTE_EVIDENCE_COLUMN_HEADER",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  ATTRNAME            ATTRVAL                         EVID"
        },
        {
            MessageId::DDictAttributeEvidenceDivider,
            "DDICT_ATTRIBUTE_EVIDENCE_DIVIDER",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  ------------------  ------------------------------  --------------------"
        },
        {
            MessageId::DDictObjectsTitle,
            "DDICT_OBJECTS_TITLE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "DDICT OBJECTS"
        },
        {
            MessageId::DDictTypeFilterLine,
            "DDICT_TYPE_FILTER_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Type filter   : {value}"
        },
        {
            MessageId::DDictProfileFilterLine,
            "DDICT_PROFILE_FILTER_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Profile filter: {value}"
        },
        {
            MessageId::DDictObjectRowsLine,
            "DDICT_OBJECT_ROWS_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Object rows   : {count}"
        },
        {
            MessageId::DDictRowsShownBoundedLine,
            "DDICT_ROWS_SHOWN_BOUNDED_LINE",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  Rows shown    : bounded to {count}"
        },
        {
            MessageId::DDictObjectsColumnHeader,
            "DDICT_OBJECTS_COLUMN_HEADER",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  OBJTYPE             NAME              OWNER             STATUS                    PROFILE       ATTRS"
        },
        {
            MessageId::DDictObjectsDivider,
            "DDICT_OBJECTS_DIVIDER",
            "COMMAND:DDICT",
            "STATUS",
            "INFO",
            "  ------------------  ----------------  ----------------  ------------------------  ------------  -----"
        },
        {
            MessageId::CmdHelpChkReflectionReportsTitle,
            "CMDHELPCHK_REFLECTION_REPORTS_TITLE",
            "COMMAND:CMDHELPCHK",
            "STATUS",
            "INFO",
            "=== REFLECTION REPORTS ==="
        },
        {
            MessageId::CmdHelpChkArtifactsSummaryTitle,
            "CMDHELPCHK_ARTIFACTS_SUMMARY_TITLE",
            "COMMAND:CMDHELPCHK",
            "STATUS",
            "INFO",
            "HELP DATA v2 artifact summary"
        },
        {
            MessageId::CmdHelpChkSetFamilyCanonicalizationTitle,
            "CMDHELPCHK_SET_FAMILY_CANONICALIZATION_TITLE",
            "COMMAND:CMDHELPCHK",
            "STATUS",
            "INFO",
            "SET-family canonicalization"
        },
        {
            MessageId::CmdHelpChkMissingV2Columns,
            "CMDHELPCHK_MISSING_V2_COLUMNS",
            "COMMAND:CMDHELPCHK",
            "ERROR",
            "ERROR",
            "Missing expected HELP DATA v2 columns; need at least KIND, SOURCE, CONFID."
        },
        {
            MessageId::CmdHelpChkMissingLegacyColumns,
            "CMDHELPCHK_MISSING_LEGACY_COLUMNS",
            "COMMAND:CMDHELPCHK",
            "ERROR",
            "ERROR",
            "Missing expected columns; need at least ID, COMMAND, and one memo (USAGE)."
        },
        {
            MessageId::CmdHelpChkArtifactsError,
            "CMDHELPCHK_ARTIFACTS_ERROR",
            "COMMAND:CMDHELPCHK",
            "ERROR",
            "ERROR",
            "ARTIFACTS error: {detail}"
        },
        {
            MessageId::CmdHelpChkRuntimeError,
            "CMDHELPCHK_RUNTIME_ERROR",
            "COMMAND:CMDHELPCHK",
            "ERROR",
            "ERROR",
            "error: {detail}"
        },
        {
            MessageId::CmdHelpChkNoRowsShown,
            "CMDHELPCHK_NO_ROWS_SHOWN",
            "COMMAND:CMDHELPCHK",
            "STATUS",
            "INFO",
            "(no rows shown; try increasing limit)"
        },
        {
            MessageId::MsgMgrUsageText,
            "MSGMGR_USAGE_TEXT",
            "COMMAND:MSGMGR",
            "STATUS",
            "INFO",
            "Usage:\n"
            "  MSGMGR                 (Show this usage)\n"
            "  MSGMGR USAGE           (Show this usage)\n"
            "  MSGMGR STATUS          (Report Message Manager command-house status)\n"
            "  MSGMGR CHECK           (Read-only command-house check)\n"
            "Notes:\n"
            "  - MSGMGR is read-only in this phase.\n"
            "  - Runtime message catalog proof remains available through SET MESSAGE CATALOG CHECK.\n"
            "  - Locale-spine runtime wiring remains guarded for a later phase."
        },
        {
            MessageId::MsgMgrStatusTitle,
            "MSGMGR_STATUS_TITLE",
            "COMMAND:MSGMGR",
            "STATUS",
            "INFO",
            "MSGMGR STATUS"
        },
        {
            MessageId::MsgMgrStatusBodyText,
            "MSGMGR_STATUS_BODY_TEXT",
            "COMMAND:MSGMGR",
            "STATUS",
            "INFO",
            "  command house        : registered\n"
            "  read mode            : read-only\n"
            "  active message check : SET MESSAGE CATALOG CHECK\n"
            "  active message get   : SET MESSAGE CATALOG GET\n"
            "  provider mode        : active_dbf\n"
            "  message DBF root     : dottalkpp/data/messaging\n"
            "  message index root   : dottalkpp/data/indexes/messaging\n"
            "  message LMDB root    : dottalkpp/data/lmdb/messaging\n"
            "  locale spine         : scaffold present; runtime status wiring held\n"
            "  schema root          : dottalkpp/data/schemas\n"
            "  locale schema        : dottalkpp/data/schemas/locale/locale_spine.dtschema\n"
            "  messaging schema     : dottalkpp/data/schemas/messaging/message_catalog.dtschema\n"
            "  boundary             : no DBF/CDX/LMDB mutation; no runtime writeback"
        },
        {
            MessageId::MsgMgrUnknownSubcommand,
            "MSGMGR_UNKNOWN_SUBCOMMAND",
            "COMMAND:MSGMGR",
            "ERROR",
            "ERROR",
            "Unknown subcommand: {command}"
        },
        {
            MessageId::HelpNoFunctionFound,
            "HELP_NO_FUNCTION_FOUND",
            "COMMAND:HELP",
            "ERROR",
            "ERROR",
            "No function help found for: {command}"
        },
        {
            MessageId::HelpNoDotTalkTopicFound,
            "HELP_NO_DOTTALK_TOPIC_FOUND",
            "COMMAND:HELP",
            "ERROR",
            "ERROR",
            "No DotTalk help found for: {command}"
        },
        {
            MessageId::HelpNoEducationalTopicFound,
            "HELP_NO_EDUCATIONAL_TOPIC_FOUND",
            "COMMAND:HELP",
            "ERROR",
            "ERROR",
            "No educational help found for: {command}"
        },
        {
            MessageId::HelpNoTopicFound,
            "HELP_NO_TOPIC_FOUND",
            "COMMAND:HELP",
            "ERROR",
            "ERROR",
            "No help found for: {command}"
        },
        {
            MessageId::HelpTopLevelHint,
            "HELP_TOP_LEVEL_HINT",
            "COMMAND:HELP",
            "HINT",
            "INFO",
            "Type HELP GIANT, HELP /GIANT, HELP GIANT TOPICS, HELP BETA, HELP PS, HELP SQL, HELP FUNCTION <name>, or HELP <command>"
        },
        {
            MessageId::HelpUsageText,
            "HELP_USAGE_TEXT",
            "COMMAND:HELP",
            "USAGE",
            "INFO",
            "DotTalk++ Help System\n\n  HELP GIANT            - full HELP DATA report\n  HELP GIANT USAGE      - GIANT surface usage\n  HELP GIANT TOPICS     - list current HELP DATA topics\n  HELP GIANT KIND       - group current HELP DATA by kind\n  HELP GIANT SOURCE     - group current HELP DATA by source\n  HELP /GIANT ...       - alias for GIANT help surface\n  HELP BETA             - beta checklist\n  HELP PS / PSHELL      - PowerShell helpers\n  HELP SQL              - SQL reference (SQLite + MSSQL)\n  HELP PREDICATES       - COUNT/LOCATE syntax\n  HELP FUNCTION <name>  - expression function help\n  HELP FUNCTIONS        - list documented expression functions\n  HELP /FOX <topic>     - FoxPro compatibility reference\n  HELP /DOT <topic>     - DotTalk-native command reference\n  HELP /ED <topic>      - educational/system concepts\n  HELP <command>        - default topic lookup\n\n  Paging for long HELP GIANT output follows SET PAGING ON|OFF."
        },
        {
            MessageId::CmdHelpCurrentLoadFailed,
            "CMDHELP_CURRENT_LOAD_FAILED",
            "COMMAND:CMDHELP",
            "ERROR",
            "ERROR",
            "could not load current HELP DATA lines from \"{dir}\"."
        },
        {
            MessageId::CmdHelpBuildTip,
            "CMDHELP_BUILD_TIP",
            "COMMAND:CMDHELP",
            "HINT",
            "INFO",
            "Tip: run CMDHELP BUILD . <source-root>"
        },
        {
            MessageId::CmdHelpNoTopicMatched,
            "CMDHELP_NO_TOPIC_MATCHED",
            "COMMAND:CMDHELP",
            "ERROR",
            "ERROR",
            "no current HELP DATA topic matched \"{topic}\"."
        },
        {
            MessageId::CmdHelpSummaryTip,
            "CMDHELP_SUMMARY_TIP",
            "COMMAND:CMDHELP",
            "HINT",
            "INFO",
            "Tip: run CMDHELP with no arguments for a HELP DATA summary."
        },
        {
            MessageId::CmdHelpCurrentBuildWritten,
            "CMDHELP_CURRENT_BUILD_WRITTEN",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "CMDHELP wrote current HELP DATA -> {dir}"
        },
        {
            MessageId::CmdHelpArtifactsMinedFrom,
            "CMDHELP_ARTIFACTS_MINED_FROM",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "Artifacts mined from: {root}"
        },
        {
            MessageId::CmdHelpUsageContractsMined,
            "CMDHELP_USAGE_CONTRACTS_MINED",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "Usage contracts mined directly: {rows} row(s) from {files} file(s)"
        },
        {
            MessageId::CmdHelpLegacyBuildWritten,
            "CMDHELP_LEGACY_BUILD_WRITTEN",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "CMDHELP LEGACY wrote: {commands} command rows, {args} arg rows -> {dir}"
        },
        {
            MessageId::CmdHelpSwitchesMinedFrom,
            "CMDHELP_SWITCHES_MINED_FROM",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "Switches mined from: {root}"
        },
        {
            MessageId::CmdHelpLegacyReadFailed,
            "CMDHELP_LEGACY_READ_FAILED",
            "COMMAND:CMDHELP",
            "ERROR",
            "ERROR",
            "LEGACY: could not read commands.dbf/cmd_args.dbf in \"{dir}\"."
        },
        {
            MessageId::CmdHelpLegacyBuildTip,
            "CMDHELP_LEGACY_BUILD_TIP",
            "COMMAND:CMDHELP",
            "HINT",
            "INFO",
            "Tip: run: CMDHELP BUILD LEGACY"
        },
        {
            MessageId::CmdHelpCurrentReadFailed,
            "CMDHELP_CURRENT_READ_FAILED",
            "COMMAND:CMDHELP",
            "ERROR",
            "ERROR",
            "could not read current HELP DATA in \"{dir}\"."
        },
        {
            MessageId::CmdHelpCurrentExpectedFile,
            "CMDHELP_CURRENT_EXPECTED_FILE",
            "COMMAND:CMDHELP",
            "HINT",
            "INFO",
            "Expected: help_line.dbf"
        },
        {
            MessageId::CmdHelpCurrentMissingColumns,
            "CMDHELP_CURRENT_MISSING_COLUMNS",
            "COMMAND:CMDHELP",
            "ERROR",
            "ERROR",
            "help_line.dbf is missing expected columns."
        },
        {
            MessageId::CmdHelpCurrentNeedColumns,
            "CMDHELP_CURRENT_NEED_COLUMNS",
            "COMMAND:CMDHELP",
            "HINT",
            "INFO",
            "Need at least TOPICKEY, KIND, SOURCE, TEXT."
        },
        {
            MessageId::CmdHelpCurrentReportTitle,
            "CMDHELP_CURRENT_REPORT_TITLE",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "CMDHELP Report (current HELP DATA)"
        },
        {
            MessageId::CmdHelpPreviewRowsTitle,
            "CMDHELP_PREVIEW_ROWS_TITLE",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "Preview rows"
        },
        {
            MessageId::CmdHelpTopicNoRenderableSections,
            "CMDHELP_TOPIC_NO_RENDERABLE_SECTIONS",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "(topic exists, but no renderable help sections were found)"
        },
        {
            MessageId::CmdHelpUsageTitle,
            "CMDHELP_USAGE_TITLE",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "CMDHELP usage"
        },
        {
            MessageId::CmdHelpNotesTitle,
            "CMDHELP_NOTES_TITLE",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "Notes:"
        },
        {
            MessageId::CmdHelpUsageNoteBuild,
            "CMDHELP_USAGE_NOTE_BUILD",
            "COMMAND:CMDHELP",
            "HINT",
            "INFO",
            "CMDHELP BUILD writes current HELP DATA tables."
        },
        {
            MessageId::CmdHelpUsageNoteLegacy,
            "CMDHELP_USAGE_NOTE_LEGACY",
            "COMMAND:CMDHELP",
            "HINT",
            "INFO",
            "CMDHELP LEGACY reads the old commands.dbf/cmd_args.dbf report."
        },
        {
            MessageId::CmdHelpCurrentDirectoryLine,
            "CMDHELP_CURRENT_DIRECTORY_LINE",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "  directory : {dir}"
        },
        {
            MessageId::CmdHelpCurrentLineRowsLine,
            "CMDHELP_CURRENT_LINE_ROWS_LINE",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "  line rows : {count}"
        },
        {
            MessageId::CmdHelpCurrentTopicsLine,
            "CMDHELP_CURRENT_TOPICS_LINE",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "  topics    : {count}"
        },
        {
            MessageId::CmdHelpByKindTitle,
            "CMDHELP_BY_KIND_TITLE",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "By KIND"
        },
        {
            MessageId::CmdHelpBySourceTitle,
            "CMDHELP_BY_SOURCE_TITLE",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "By SOURCE"
        },
        {
            MessageId::CmdHelpMatchedTopicsLabel,
            "CMDHELP_MATCHED_TOPICS_LABEL",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "Matched topics:"
        },
        {
            MessageId::CmdHelpPreviewTopicKeyHeader,
            "CMDHELP_PREVIEW_TOPICKEY_HEADER",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "TOPICKEY"
        },
        {
            MessageId::CmdHelpPreviewKindHeader,
            "CMDHELP_PREVIEW_KIND_HEADER",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "KIND"
        },
        {
            MessageId::CmdHelpPreviewSourceHeader,
            "CMDHELP_PREVIEW_SOURCE_HEADER",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "SOURCE"
        },
        {
            MessageId::CmdHelpPreviewConfidHeader,
            "CMDHELP_PREVIEW_CONFID_HEADER",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "CONFID"
        },
        {
            MessageId::CmdHelpPreviewRoleHeader,
            "CMDHELP_PREVIEW_ROLE_HEADER",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "ROLE"
        },
        {
            MessageId::CmdHelpPreviewTextHeader,
            "CMDHELP_PREVIEW_TEXT_HEADER",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "TEXT"
        },
        {
            MessageId::CmdHelpPreviewDivider,
            "CMDHELP_PREVIEW_DIVIDER",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "--------------------------------------------------------------------------------"
        },
        {
            MessageId::CmdHelpQueryLine,
            "CMDHELP_QUERY_LINE",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "CMDHELP {qualifier}{query}"
        },
        {
            MessageId::CmdHelpUsageBodyText,
            "CMDHELP_USAGE_BODY_TEXT",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "  CMDHELP\n"
            "  CMDHELP USAGE\n"
            "  CMDHELP BUILD\n"
            "  CMDHELP BUILD . <source-root>\n"
            "  CMDHELP <topic>\n"
            "  CMDHELP USAGE <topic>\n"
            "  CMDHELP <topic> USAGE\n"
            "  CMDHELP BUILD LEGACY\n"
            "  CMDHELP LEGACY"
        },
        {
            MessageId::CmdHelpLegacyReportLine,
            "CMDHELP_LEGACY_REPORT_LINE",
            "COMMAND:CMDHELP",
            "STATUS",
            "INFO",
            "CMDHELP LEGACY Report: {commands} command rows, {args} arg rows -> {dir}"
        },
        {
            MessageId::LmdbUsageText,
            "LMDB_USAGE_TEXT",
            "COMMAND:LMDB",
            "USAGE",
            "INFO",
            "Usage:\n  LMDB USAGE\n  LMDB INFO\n  LMDB OPEN <container.cdx>\n  LMDB OPEN <envdir.cdx.d>\n  LMDB OPEN <stem>\n  LMDB USE <tag>\n  LMDB SEEK <key>\n  LMDB DUMP\n  LMDB DUMP <max>\n  LMDB SCAN <low> <high>\n  LMDB CLOSE\nNotes:\n  - LMDB is per-area and uses the current DbArea IndexManager/CDX backend.\n  - Bare stems resolve through the INDEXES path slot.\n  - LMDB_UTIL is deprecated and disabled."
        },
        {
            MessageId::LmdbActionNoTableOpenText,
            "LMDB_ACTION_NO_TABLE_OPEN_TEXT",
            "COMMAND:LMDB",
            "ERROR",
            "ERROR",
            "{action}: no table open in current area"
        },
        {
            MessageId::LmdbInfoNoneText,
            "LMDB_INFO_NONE_TEXT",
            "COMMAND:LMDB",
            "STATUS",
            "INFO",
            "(none)"
        },
        {
            MessageId::LmdbInfoTitleText,
            "LMDB_INFO_TITLE_TEXT",
            "COMMAND:LMDB",
            "STATUS",
            "INFO",
            "LMDB INFO"
        },
        {
            MessageId::LmdbInfoContainerLineText,
            "LMDB_INFO_CONTAINER_LINE_TEXT",
            "COMMAND:LMDB",
            "STATUS",
            "INFO",
            "  container: {path}"
        },
        {
            MessageId::LmdbInfoTagLineText,
            "LMDB_INFO_TAG_LINE_TEXT",
            "COMMAND:LMDB",
            "STATUS",
            "INFO",
            "  tag      : {tag}"
        },
        {
            MessageId::LmdbOpenMissingPathText,
            "LMDB_OPEN_MISSING_PATH_TEXT",
            "COMMAND:LMDB",
            "ERROR",
            "ERROR",
            "missing path"
        },
        {
            MessageId::LmdbOpenInvalidPathText,
            "LMDB_OPEN_INVALID_PATH_TEXT",
            "COMMAND:LMDB",
            "ERROR",
            "ERROR",
            "invalid path"
        },
        {
            MessageId::LmdbOpenFailedText,
            "LMDB_OPEN_FAILED_TEXT",
            "COMMAND:LMDB",
            "ERROR",
            "ERROR",
            "OPEN failed: {detail}"
        },
        {
            MessageId::LmdbOpenText,
            "LMDB_OPEN_TEXT",
            "COMMAND:LMDB",
            "STATUS",
            "INFO",
            "OPEN: {path}"
        },
        {
            MessageId::LmdbUseMissingTagText,
            "LMDB_USE_MISSING_TAG_TEXT",
            "COMMAND:LMDB",
            "ERROR",
            "ERROR",
            "missing TAG"
        },
        {
            MessageId::LmdbUseFailedText,
            "LMDB_USE_FAILED_TEXT",
            "COMMAND:LMDB",
            "ERROR",
            "ERROR",
            "USE failed: {detail}"
        },
        {
            MessageId::LmdbUseText,
            "LMDB_USE_TEXT",
            "COMMAND:LMDB",
            "STATUS",
            "INFO",
            "USE: {tag}"
        },
        {
            MessageId::LmdbSeekMissingKeyText,
            "LMDB_SEEK_MISSING_KEY_TEXT",
            "COMMAND:LMDB",
            "ERROR",
            "ERROR",
            "missing key"
        },
        {
            MessageId::LmdbSeekFailedText,
            "LMDB_SEEK_FAILED_TEXT",
            "COMMAND:LMDB",
            "ERROR",
            "ERROR",
            "SEEK failed: {detail}"
        },
        {
            MessageId::LmdbSeekRecnoText,
            "LMDB_SEEK_RECNO_TEXT",
            "COMMAND:LMDB",
            "STATUS",
            "INFO",
            "SEEK: recno={recno}"
        },
        {
            MessageId::LmdbDumpNoneText,
            "LMDB_DUMP_NONE_TEXT",
            "COMMAND:LMDB",
            "STATUS",
            "INFO",
            "DUMP: (none)"
        },
        {
            MessageId::LmdbDumpNoTagSelectedText,
            "LMDB_DUMP_NO_TAG_SELECTED_TEXT",
            "COMMAND:LMDB",
            "ERROR",
            "ERROR",
            "DUMP: no TAG selected. Try: LMDB USE <TAG>"
        },
        {
            MessageId::LmdbDumpCursorOpenFailedText,
            "LMDB_DUMP_CURSOR_OPEN_FAILED_TEXT",
            "COMMAND:LMDB",
            "ERROR",
            "ERROR",
            "DUMP: cursor open failed"
        },
        {
            MessageId::LmdbDumpPrintedText,
            "LMDB_DUMP_PRINTED_TEXT",
            "COMMAND:LMDB",
            "STATUS",
            "INFO",
            "DUMP: printed {count}"
        },
        {
            MessageId::LmdbScanUsageText,
            "LMDB_SCAN_USAGE_TEXT",
            "COMMAND:LMDB",
            "USAGE",
            "INFO",
            "SCAN usage: LMDB SCAN <low> <high>"
        },
        {
            MessageId::LmdbScanNoneText,
            "LMDB_SCAN_NONE_TEXT",
            "COMMAND:LMDB",
            "STATUS",
            "INFO",
            "SCAN: (none)"
        },
        {
            MessageId::LmdbScanNoTagSelectedText,
            "LMDB_SCAN_NO_TAG_SELECTED_TEXT",
            "COMMAND:LMDB",
            "ERROR",
            "ERROR",
            "SCAN: no TAG selected. Try: LMDB USE <TAG>"
        },
        {
            MessageId::LmdbScanCursorOpenFailedText,
            "LMDB_SCAN_CURSOR_OPEN_FAILED_TEXT",
            "COMMAND:LMDB",
            "ERROR",
            "ERROR",
            "SCAN: cursor open failed"
        },
        {
            MessageId::LmdbScanShownText,
            "LMDB_SCAN_SHOWN_TEXT",
            "COMMAND:LMDB",
            "STATUS",
            "INFO",
            "SCAN: shown {count}"
        },
        {
            MessageId::LmdbCloseText,
            "LMDB_CLOSE_TEXT",
            "COMMAND:LMDB",
            "STATUS",
            "INFO",
            "CLOSE"
        },
        {
            MessageId::LmdbUtilDisabledText,
            "LMDB_UTIL_DISABLED_TEXT",
            "COMMAND:LMDB_UTIL",
            "STATUS",
            "INFO",
            "LMDB_UTIL is deprecated and disabled.\nUse: LMDB (per-area)\nUsage:\n  LMDB_UTIL\n  LMDB_UTIL USAGE\nRelated:\n  LMDB INFO\n  LMDB OPEN <container.cdx>\n  LMDB USE <tag>\n  LMDB SEEK <key>\n  LMDB DUMP\n  LMDB SCAN <low> <high>\n  LMDB CLOSE"
        },
        {
            MessageId::ManualCatalogStatusTitle,
            "MANUAL_CATALOG_STATUS_TITLE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "MANUAL CATALOG STATUS"
        },
        {
            MessageId::ManualCatalogTablesTitle,
            "MANUAL_CATALOG_TABLES_TITLE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "MANUAL CATALOG TABLES"
        },
        {
            MessageId::ManualCatalogCountsTitle,
            "MANUAL_CATALOG_COUNTS_TITLE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "MANUAL CATALOG COUNTS"
        },
        {
            MessageId::ManualCatalogCountsNote,
            "MANUAL_CATALOG_COUNTS_NOTE",
            "COMMAND:MANUAL",
            "HINT",
            "INFO",
            "note: this lightweight native surface reports expected counts and DBF presence; DBF row readback remains in manualgen reports."
        },
        {
            MessageId::ManualCatalogResolveTitle,
            "MANUAL_CATALOG_RESOLVE_TITLE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "MANUAL CATALOG RESOLVE"
        },
        {
            MessageId::ManualResolveUnknownToken,
            "MANUAL_RESOLVE_UNKNOWN_TOKEN",
            "COMMAND:MANUAL",
            "ERROR",
            "ERROR",
            "unknown MAN* table token or alias"
        },
        {
            MessageId::ManualInternalTableSpecMissing,
            "MANUAL_INTERNAL_TABLE_SPEC_MISSING",
            "COMMAND:MANUAL",
            "ERROR",
            "ERROR",
            "internal error: table specification missing"
        },
        {
            MessageId::ManualUsageTitle,
            "MANUAL_USAGE_TITLE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "Usage:"
        },
        {
            MessageId::ManualNotesTitle,
            "MANUAL_NOTES_TITLE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "Notes:"
        },
        {
            MessageId::ManualReadOnlyNote,
            "MANUAL_READ_ONLY_NOTE",
            "COMMAND:MANUAL",
            "HINT",
            "INFO",
            "MANUAL is read-only."
        },
        {
            MessageId::ManualReportsEvidenceNote,
            "MANUAL_REPORTS_EVIDENCE_NOTE",
            "COMMAND:MANUAL",
            "HINT",
            "INFO",
            "MANUAL reports accepted MAN* manualgen catalog evidence."
        },
        {
            MessageId::ManualDoesNotMutateNote,
            "MANUAL_DOES_NOT_MUTATE_NOTE",
            "COMMAND:MANUAL",
            "HINT",
            "INFO",
            "MANUAL does not mutate DBFs, HELP, META, CMDHELPCHK, source, or publication artifacts."
        },
        {
            MessageId::ManualSectionsTitle,
            "MANUAL_SECTIONS_TITLE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "MANUAL SECTIONS"
        },
        {
            MessageId::ManualMediaTitle,
            "MANUAL_MEDIA_TITLE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "MANUAL MEDIA"
        },
        {
            MessageId::ManualMediaAnchorsTitle,
            "MANUAL_MEDIA_ANCHORS_TITLE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "MANUAL MEDIA ANCHORS"
        },
        {
            MessageId::ManualReviewTitle,
            "MANUAL_REVIEW_TITLE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "MANUAL REVIEW"
        },
        {
            MessageId::ManualStatusModeLine,
            "MANUAL_STATUS_MODE_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  mode: read-only"
        },
        {
            MessageId::ManualStatusRepoRootLine,
            "MANUAL_STATUS_REPO_ROOT_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  repo_root: {value}"
        },
        {
            MessageId::ManualStatusAcceptedDbfDirLine,
            "MANUAL_STATUS_ACCEPTED_DBF_DIR_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  accepted_dbf_dir: {value}"
        },
        {
            MessageId::ManualStatusAcceptedDbfDirExistsLine,
            "MANUAL_STATUS_ACCEPTED_DBF_DIR_EXISTS_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  accepted_dbf_dir_exists: {value}"
        },
        {
            MessageId::ManualStatusExpectedTablesLine,
            "MANUAL_STATUS_EXPECTED_TABLES_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  expected_MAN_tables: {value}"
        },
        {
            MessageId::ManualStatusPresentTablesLine,
            "MANUAL_STATUS_PRESENT_TABLES_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  present_MAN_tables: {value}"
        },
        {
            MessageId::ManualTableLine,
            "MANUAL_TABLE_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  {compact} alias={alias} expected={expected} exists={exists} purpose=\"{purpose}\""
        },
        {
            MessageId::ManualCountLine,
            "MANUAL_COUNT_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  {compact} expected={expected} dbf_exists={exists}"
        },
        {
            MessageId::ManualResolveRequestedTokenLine,
            "MANUAL_RESOLVE_REQUESTED_TOKEN_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  requested_token: {value}"
        },
        {
            MessageId::ManualResolveResolvedLine,
            "MANUAL_RESOLVE_RESOLVED_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  resolved: {value}"
        },
        {
            MessageId::ManualResolveMessageLine,
            "MANUAL_RESOLVE_MESSAGE_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  message: {value}"
        },
        {
            MessageId::ManualResolveCompactNameLine,
            "MANUAL_RESOLVE_COMPACT_NAME_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  compact_name: {value}"
        },
        {
            MessageId::ManualResolveAliasCandidateLine,
            "MANUAL_RESOLVE_ALIAS_CANDIDATE_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  alias_candidate: {value}"
        },
        {
            MessageId::ManualResolvePhysicalTableLine,
            "MANUAL_RESOLVE_PHYSICAL_TABLE_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  physical_table: {value}"
        },
        {
            MessageId::ManualResolveDbfExistsLine,
            "MANUAL_RESOLVE_DBF_EXISTS_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  dbf_exists: {value}"
        },
        {
            MessageId::ManualFocusCompactNameLine,
            "MANUAL_FOCUS_COMPACT_NAME_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  compact_name: {value}"
        },
        {
            MessageId::ManualFocusAliasCandidateLine,
            "MANUAL_FOCUS_ALIAS_CANDIDATE_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  alias_candidate: {value}"
        },
        {
            MessageId::ManualFocusExpectedRecordsLine,
            "MANUAL_FOCUS_EXPECTED_RECORDS_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  expected_records: {value}"
        },
        {
            MessageId::ManualFocusDbfExistsLine,
            "MANUAL_FOCUS_DBF_EXISTS_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  dbf_exists: {value}"
        },
        {
            MessageId::ManualFocusPhysicalTableLine,
            "MANUAL_FOCUS_PHYSICAL_TABLE_LINE",
            "COMMAND:MANUAL",
            "STATUS",
            "INFO",
            "  physical_table: {value}"
        },
        {
            MessageId::ManualFocusDetailFutureNoteLine,
            "MANUAL_FOCUS_DETAIL_FUTURE_NOTE_LINE",
            "COMMAND:MANUAL",
            "HINT",
            "INFO",
            "  note: detailed row rendering remains a future read-only native enhancement."
        },
        {
            MessageId::ManualUnsupportedSubcommand,
            "MANUAL_UNSUPPORTED_SUBCOMMAND",
            "COMMAND:MANUAL",
            "ERROR",
            "ERROR",
            "unsupported read-only subcommand. Use MANUAL USAGE."
        },
        {
            MessageId::PrnUsageText,
            "PRN_USAGE_TEXT",
            "COMMAND:PRN",
            "USAGE",
            "INFO",
            "Usage:\n  PRN\n  PRN USAGE\n  PRN STATUS\n  PRN SHOW\n  PRN OFF\n  PRN TO CONSOLE\n  PRN TO SCREEN\n  PRN TO FILE <path>\n  PRN TO PRINTER\n  PRN TO PRINTER <name>\n  PRN TO NULL"
        },
        {
            MessageId::PrnStatusLineText,
            "PRN_STATUS_LINE_TEXT",
            "COMMAND:PRN",
            "STATUS",
            "INFO",
            "PRN: {dest}"
        },
        {
            MessageId::PrnFileLineText,
            "PRN_FILE_LINE_TEXT",
            "COMMAND:PRN",
            "STATUS",
            "INFO",
            "  File       : {path}"
        },
        {
            MessageId::PrnPrinterDefaultLineText,
            "PRN_PRINTER_DEFAULT_LINE_TEXT",
            "COMMAND:PRN",
            "STATUS",
            "INFO",
            "  Printer    : (system default)"
        },
        {
            MessageId::PrnPrinterNamedLineText,
            "PRN_PRINTER_NAMED_LINE_TEXT",
            "COMMAND:PRN",
            "STATUS",
            "INFO",
            "  Printer    : {name}"
        },
        {
            MessageId::PrnPrinterJobLineText,
            "PRN_PRINTER_JOB_LINE_TEXT",
            "COMMAND:PRN",
            "STATUS",
            "INFO",
            "  Printer job: staged only (OS handoff disabled)"
        },
        {
            MessageId::PrnAlternateLineText,
            "PRN_ALTERNATE_LINE_TEXT",
            "COMMAND:PRN",
            "STATUS",
            "INFO",
            "  Alternate  : {value}"
        },
        {
            MessageId::PrnPagingLineText,
            "PRN_PAGING_LINE_TEXT",
            "COMMAND:PRN",
            "STATUS",
            "INFO",
            "  Paging     : {state}"
        },
        {
            MessageId::PrnFileUsageText,
            "PRN_FILE_USAGE_TEXT",
            "COMMAND:PRN",
            "USAGE",
            "INFO",
            "Usage: PRN TO FILE <path>"
        },
        {
            MessageId::PrnFileOpenFailedText,
            "PRN_FILE_OPEN_FAILED_TEXT",
            "COMMAND:PRN",
            "ERROR",
            "ERROR",
            "PRN: failed to open file: {path}"
        },
        {
            MessageId::PrnPrinterConfigureFailedText,
            "PRN_PRINTER_CONFIGURE_FAILED_TEXT",
            "COMMAND:PRN",
            "ERROR",
            "ERROR",
            "PRN: failed to configure printer destination."
        },
        {
            MessageId::BangUsageText,
            "BANG_USAGE_TEXT",
            "COMMAND:BANG",
            "USAGE",
            "INFO",
            "Usage:\n  BANG\n  BANG USAGE\n  BANG <command>\n  !\n  ! <command>\nNotes:\n  - BANG with no arguments launches an interactive host shell.\n  - BANG <command> executes a host shell command."
        },
        {
            MessageId::BellUsageText,
            "BELL_USAGE_TEXT",
            "COMMAND:BELL",
            "USAGE",
            "INFO",
            "Usage:\n  BELL\n  BELL USAGE\n  BELL ON\n  BELL OFF"
        },
        {
            MessageId::BellRungText,
            "BELL_RUNG_TEXT",
            "COMMAND:BELL",
            "STATUS",
            "INFO",
            "Bell rung."
        },
        {
            MessageId::BellIsOffText,
            "BELL_IS_OFF_TEXT",
            "COMMAND:BELL",
            "STATUS",
            "INFO",
            "Bell is OFF."
        },
        {
            MessageId::BellStatusText,
            "BELL_STATUS_TEXT",
            "COMMAND:BELL",
            "STATUS",
            "INFO",
            "Bell is {state}"
        },
        {
            MessageId::CloseUsageText,
            "CLOSE_USAGE_TEXT",
            "COMMAND:CLOSE",
            "USAGE",
            "INFO",
            "Usage:\n  CLOSE USAGE\n  CLOSE\n  CLOSE ALL\nNotes:\n  - CLOSE closes the current work area.\n  - CLOSE ALL clears all relations before closing the current work area.\n  - Dirty table-buffer state may prompt or cancel close."
        },
        {
            MessageId::CloseCanceledText,
            "CLOSE_CANCELED_TEXT",
            "COMMAND:CLOSE",
            "STATUS",
            "INFO",
            "CLOSE canceled."
        },
        {
            MessageId::CloseCompletedText,
            "CLOSE_COMPLETED_TEXT",
            "COMMAND:CLOSE",
            "STATUS",
            "INFO",
            "Closed."
        },
        {
            MessageId::CdxUsageText,
            "CDX_USAGE_TEXT",
            "COMMAND:CDX",
            "USAGE",
            "INFO",
            "Usage:\n  CDX USAGE\n  CDX INFO [<path.cdx>]\n  CDX TAGS [<path.cdx>]\n  CDX CREATE [<path.cdx>]\n  CDX ADDTAG <name> [<path.cdx>]\n  CDX DROPTAG <name> [<path.cdx>]\nNotes:\n  - CDX with no arguments shows usage.\n  - CREATE refuses to overwrite an existing CDX file.\n  - INFO/TAGS inspect metadata; ADDTAG/DROPTAG mutate tag metadata."
        },
        {
            MessageId::CdxCreateUnableResolvePathText,
            "CDX_CREATE_UNABLE_RESOLVE_PATH_TEXT",
            "COMMAND:CDX",
            "ERROR",
            "ERROR",
            "unable to resolve path."
        },
        {
            MessageId::CdxCreateFileExistsText,
            "CDX_CREATE_FILE_EXISTS_TEXT",
            "COMMAND:CDX",
            "ERROR",
            "ERROR",
            "file already exists: \"{path}\""
        },
        {
            MessageId::CdxCreateOpenFailedText,
            "CDX_CREATE_OPEN_FAILED_TEXT",
            "COMMAND:CDX",
            "ERROR",
            "ERROR",
            "open/create failed."
        },
        {
            MessageId::CdxCreatedText,
            "CDX_CREATED_TEXT",
            "COMMAND:CDX",
            "STATUS",
            "INFO",
            "created: \"{path}\""
        },
        {
            MessageId::CdxFileNotFoundText,
            "CDX_FILE_NOT_FOUND_TEXT",
            "COMMAND:CDX",
            "ERROR",
            "ERROR",
            "file not found: \"{path}\""
        },
        {
            MessageId::CdxUnableOpenText,
            "CDX_UNABLE_OPEN_TEXT",
            "COMMAND:CDX",
            "ERROR",
            "ERROR",
            "unable to open: \"{path}\""
        },
        {
            MessageId::CdxInfoInvalidHeaderText,
            "CDX_INFO_INVALID_HEADER_TEXT",
            "COMMAND:CDX",
            "ERROR",
            "ERROR",
            "invalid header."
        },
        {
            MessageId::CdxInfoFileLineText,
            "CDX_INFO_FILE_LINE_TEXT",
            "COMMAND:CDX",
            "STATUS",
            "INFO",
            "CDX file : {path}"
        },
        {
            MessageId::CdxInfoTagsLineText,
            "CDX_INFO_TAGS_LINE_TEXT",
            "COMMAND:CDX",
            "STATUS",
            "INFO",
            "Tags     : {count}"
        },
        {
            MessageId::CdxInfoTagLineText,
            "CDX_INFO_TAG_LINE_TEXT",
            "COMMAND:CDX",
            "STATUS",
            "INFO",
            "  [{tag_id}] {name}  root_off={root_off}  recs={recs}"
        },
        {
            MessageId::CdxTagsReadFailedText,
            "CDX_TAGS_READ_FAILED_TEXT",
            "COMMAND:CDX",
            "ERROR",
            "ERROR",
            "read failed."
        },
        {
            MessageId::CdxNoTagsText,
            "CDX_NO_TAGS_TEXT",
            "COMMAND:CDX",
            "STATUS",
            "INFO",
            "(no tags)"
        },
        {
            MessageId::CdxTagLineText,
            "CDX_TAG_LINE_TEXT",
            "COMMAND:CDX",
            "STATUS",
            "INFO",
            "  [{tag_id}] {name}"
        },
        {
            MessageId::CdxAddTagMissingNameText,
            "CDX_ADDTAG_MISSING_NAME_TEXT",
            "COMMAND:CDX",
            "ERROR",
            "ERROR",
            "missing <name>."
        },
        {
            MessageId::CdxAddTagUnableResolvePathText,
            "CDX_ADDTAG_UNABLE_RESOLVE_PATH_TEXT",
            "COMMAND:CDX",
            "ERROR",
            "ERROR",
            "unable to resolve path."
        },
        {
            MessageId::CdxAddTagOpenFailedText,
            "CDX_ADDTAG_OPEN_FAILED_TEXT",
            "COMMAND:CDX",
            "ERROR",
            "ERROR",
            "open failed."
        },
        {
            MessageId::CdxAddTagAlreadyExistsText,
            "CDX_ADDTAG_ALREADY_EXISTS_TEXT",
            "COMMAND:CDX",
            "ERROR",
            "ERROR",
            "tag already exists."
        },
        {
            MessageId::CdxAddTagAddedText,
            "CDX_ADDTAG_ADDED_TEXT",
            "COMMAND:CDX",
            "STATUS",
            "INFO",
            "added '{tag}'."
        },
        {
            MessageId::CdxDropTagMissingNameText,
            "CDX_DROPTAG_MISSING_NAME_TEXT",
            "COMMAND:CDX",
            "ERROR",
            "ERROR",
            "missing <name>."
        },
        {
            MessageId::CdxDropTagUnableResolvePathText,
            "CDX_DROPTAG_UNABLE_RESOLVE_PATH_TEXT",
            "COMMAND:CDX",
            "ERROR",
            "ERROR",
            "unable to resolve path."
        },
        {
            MessageId::CdxDropTagOpenFailedText,
            "CDX_DROPTAG_OPEN_FAILED_TEXT",
            "COMMAND:CDX",
            "ERROR",
            "ERROR",
            "open failed."
        },
        {
            MessageId::CdxDropTagNotFoundText,
            "CDX_DROPTAG_NOT_FOUND_TEXT",
            "COMMAND:CDX",
            "ERROR",
            "ERROR",
            "not found."
        },
        {
            MessageId::CdxDropTagRemovedText,
            "CDX_DROPTAG_REMOVED_TEXT",
            "COMMAND:CDX",
            "STATUS",
            "INFO",
            "removed '{tag}'."
        },
        {
            MessageId::CdxUnknownSubcommandText,
            "CDX_UNKNOWN_SUBCOMMAND_TEXT",
            "COMMAND:CDX",
            "ERROR",
            "ERROR",
            "unknown subcommand: {subcommand}"
        },
        {
            MessageId::CnxUsageText,
            "CNX_USAGE_TEXT",
            "COMMAND:CNX",
            "USAGE",
            "INFO",
            "Usage:\n  CNX USAGE\n  CNX INFO [<path.cnx>]\n  CNX TAGS [<path.cnx>]\n  CNX CREATE [<path.cnx>]\n  CNX ADDTAG <name> [<path.cnx>]\n  CNX DROPTAG <name> [<path.cnx>]\n  CNX WALK <tag> [<path.cnx>]\n  CNX TRACE <tag> [<path.cnx>]\nNotes:\n  - CNX with no arguments shows usage.\n  - CREATE refuses to overwrite an existing CNX file.\n  - INFO/TAGS/WALK/TRACE inspect metadata; ADDTAG/DROPTAG mutate tag metadata."
        },
        {
            MessageId::CnxCreateUnableResolvePathText,
            "CNX_CREATE_UNABLE_RESOLVE_PATH_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "unable to resolve path."
        },
        {
            MessageId::CnxCreateFileExistsText,
            "CNX_CREATE_FILE_EXISTS_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "file already exists: \"{path}\""
        },
        {
            MessageId::CnxCreateOpenFailedText,
            "CNX_CREATE_OPEN_FAILED_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "open/create failed."
        },
        {
            MessageId::CnxCreatedText,
            "CNX_CREATED_TEXT",
            "COMMAND:CNX",
            "STATUS",
            "INFO",
            "created: \"{path}\""
        },
        {
            MessageId::CnxFileNotFoundText,
            "CNX_FILE_NOT_FOUND_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "file not found: \"{path}\""
        },
        {
            MessageId::CnxUnableOpenText,
            "CNX_UNABLE_OPEN_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "unable to open: \"{path}\""
        },
        {
            MessageId::CnxInfoInvalidHeaderText,
            "CNX_INFO_INVALID_HEADER_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "invalid header."
        },
        {
            MessageId::CnxInfoFileLineText,
            "CNX_INFO_FILE_LINE_TEXT",
            "COMMAND:CNX",
            "STATUS",
            "INFO",
            "CNX file : {path}"
        },
        {
            MessageId::CnxInfoTagsLineText,
            "CNX_INFO_TAGS_LINE_TEXT",
            "COMMAND:CNX",
            "STATUS",
            "INFO",
            "Tags     : {count}"
        },
        {
            MessageId::CnxInfoTagLineText,
            "CNX_INFO_TAG_LINE_TEXT",
            "COMMAND:CNX",
            "STATUS",
            "INFO",
            "  [{tag_id}] {name}  root_off={root_off}  recs={recs}"
        },
        {
            MessageId::CnxTagsReadFailedText,
            "CNX_TAGS_READ_FAILED_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "read failed."
        },
        {
            MessageId::CnxNoTagsText,
            "CNX_NO_TAGS_TEXT",
            "COMMAND:CNX",
            "STATUS",
            "INFO",
            "(no tags)"
        },
        {
            MessageId::CnxTagLineText,
            "CNX_TAG_LINE_TEXT",
            "COMMAND:CNX",
            "STATUS",
            "INFO",
            "  [{tag_id}] {name}"
        },
        {
            MessageId::CnxWalkMissingTagText,
            "CNX_WALK_MISSING_TAG_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "missing <tag>."
        },
        {
            MessageId::CnxWalkUnableResolvePathText,
            "CNX_WALK_UNABLE_RESOLVE_PATH_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "unable to resolve path."
        },
        {
            MessageId::CnxWalkUnableOpenText,
            "CNX_WALK_UNABLE_OPEN_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "unable to open: \"{path}\""
        },
        {
            MessageId::CnxWalkReadTagDirectoryFailedText,
            "CNX_WALK_READ_TAG_DIRECTORY_FAILED_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "failed to read tag directory."
        },
        {
            MessageId::CnxWalkTagNotFoundText,
            "CNX_WALK_TAG_NOT_FOUND_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "tag not found: {tag}"
        },
        {
            MessageId::CnxWalkFileSummaryText,
            "CNX_WALK_FILE_SUMMARY_TEXT",
            "COMMAND:CNX",
            "STATUS",
            "INFO",
            "file=\"{path}\"  tag={tag}  root_off={root_off}  stats_rec={stats_rec}"
        },
        {
            MessageId::CnxWalkPageSizeText,
            "CNX_WALK_PAGE_SIZE_TEXT",
            "COMMAND:CNX",
            "STATUS",
            "INFO",
            "page_size={size}"
        },
        {
            MessageId::CnxWalkRootZeroText,
            "CNX_WALK_ROOT_ZERO_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "root_page_off is 0"
        },
        {
            MessageId::CnxAddTagMissingNameText,
            "CNX_ADDTAG_MISSING_NAME_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "missing <name>."
        },
        {
            MessageId::CnxAddTagUnableResolvePathText,
            "CNX_ADDTAG_UNABLE_RESOLVE_PATH_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "unable to resolve path."
        },
        {
            MessageId::CnxAddTagOpenFailedText,
            "CNX_ADDTAG_OPEN_FAILED_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "open failed."
        },
        {
            MessageId::CnxAddTagAlreadyExistsText,
            "CNX_ADDTAG_ALREADY_EXISTS_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "tag already exists."
        },
        {
            MessageId::CnxAddTagAddedText,
            "CNX_ADDTAG_ADDED_TEXT",
            "COMMAND:CNX",
            "STATUS",
            "INFO",
            "added '{tag}'."
        },
        {
            MessageId::CnxDropTagMissingNameText,
            "CNX_DROPTAG_MISSING_NAME_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "missing <name>."
        },
        {
            MessageId::CnxDropTagUnableResolvePathText,
            "CNX_DROPTAG_UNABLE_RESOLVE_PATH_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "unable to resolve path."
        },
        {
            MessageId::CnxDropTagOpenFailedText,
            "CNX_DROPTAG_OPEN_FAILED_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "open failed."
        },
        {
            MessageId::CnxDropTagNotFoundText,
            "CNX_DROPTAG_NOT_FOUND_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "not found."
        },
        {
            MessageId::CnxDropTagRemovedText,
            "CNX_DROPTAG_REMOVED_TEXT",
            "COMMAND:CNX",
            "STATUS",
            "INFO",
            "removed '{tag}'."
        },
        {
            MessageId::CnxUnknownSubcommandText,
            "CNX_UNKNOWN_SUBCOMMAND_TEXT",
            "COMMAND:CNX",
            "ERROR",
            "ERROR",
            "unknown subcommand: {subcommand}"
        },
        {
            MessageId::ClearUsageText,
            "CLEAR_USAGE_TEXT",
            "COMMAND:CLEAR",
            "USAGE",
            "INFO",
            "Usage:\n  CLEAR USAGE\n  CLEAR\n  CLS\nNotes:\n  - Clears the console screen only."
        },
        {
            MessageId::VersionUsageText,
            "VERSION_USAGE_TEXT",
            "COMMAND:VERSION",
            "USAGE",
            "INFO",
            "Usage:\n  VERSION\n  VERSION USAGE"
        },
        {
            MessageId::VersionBannerLineText,
            "VERSION_BANNER_LINE_TEXT",
            "COMMAND:VERSION",
            "STATUS",
            "INFO",
            "dottalk++ {version}  ({stamp})"
        },
        {
            MessageId::VersionBuildLineText,
            "VERSION_BUILD_LINE_TEXT",
            "COMMAND:VERSION",
            "STATUS",
            "INFO",
            "DotTalk++ build {stamp}"
        },
        {
            MessageId::SqlverUsageText,
            "SQLVER_USAGE_TEXT",
            "COMMAND:SQLVER",
            "USAGE",
            "INFO",
            "Usage:\n  SQLVER\n  SQLVER USAGE"
        },
        {
            MessageId::SqlverAvailableLineText,
            "SQLVER_AVAILABLE_LINE_TEXT",
            "COMMAND:SQLVER",
            "STATUS",
            "INFO",
            "SQLite available: 1, version: {version}"
        },
        {
            MessageId::SqlverUnavailableLineText,
            "SQLVER_UNAVAILABLE_LINE_TEXT",
            "COMMAND:SQLVER",
            "STATUS",
            "INFO",
            "SQLite available: 0"
        },
        {
            MessageId::ShutdownUsageText,
            "SHUTDOWN_USAGE_TEXT",
            "COMMAND:SHUTDOWN",
            "USAGE",
            "INFO",
            "Usage:\n  SHUTDOWN\n  SHUTDOWN USAGE\nNotes:\n  - SHUTDOWN with no arguments executes shutdown.ini when present.\n  - SHUTDOWN USAGE prints this usage and does not execute shutdown.ini."
        },
        {
            MessageId::ShutdownUnableOpenText,
            "SHUTDOWN_UNABLE_OPEN_TEXT",
            "COMMAND:SHUTDOWN",
            "ERROR",
            "ERROR",
            "SHUTDOWN: unable to open {path}"
        },
        {
            MessageId::ShutdownProcessingText,
            "SHUTDOWN_PROCESSING_TEXT",
            "COMMAND:SHUTDOWN",
            "STATUS",
            "INFO",
            "SHUTDOWN: processing {path}"
        },
        {
            MessageId::ShutdownLineFailedText,
            "SHUTDOWN_LINE_FAILED_TEXT",
            "COMMAND:SHUTDOWN",
            "ERROR",
            "ERROR",
            "SHUTDOWN: {file}:{line}: {detail}"
        },
        {
            MessageId::ShutdownLineUnknownErrorText,
            "SHUTDOWN_LINE_UNKNOWN_ERROR_TEXT",
            "COMMAND:SHUTDOWN",
            "ERROR",
            "ERROR",
            "SHUTDOWN: {file}:{line}: unknown error"
        },
        {
            MessageId::ShutdownNoIniFoundText,
            "SHUTDOWN_NO_INI_FOUND_TEXT",
            "COMMAND:SHUTDOWN",
            "STATUS",
            "INFO",
            "SHUTDOWN: no shutdown.ini found in {path}"
        },
        {
            MessageId::ShutdownProcessingFailedText,
            "SHUTDOWN_PROCESSING_FAILED_TEXT",
            "COMMAND:SHUTDOWN",
            "ERROR",
            "ERROR",
            "SHUTDOWN: ini processing failed: {detail}"
        },
        {
            MessageId::ShutdownProcessingFailedUnknownText,
            "SHUTDOWN_PROCESSING_FAILED_UNKNOWN_TEXT",
            "COMMAND:SHUTDOWN",
            "ERROR",
            "ERROR",
            "SHUTDOWN: ini processing failed (unknown error)"
        },
        {
            MessageId::SelectUsageText,
            "SELECT_USAGE_TEXT",
            "COMMAND:SELECT",
            "USAGE",
            "INFO",
            "Usage:\n  SELECT USAGE\n  SELECT <0..{max_slot}>\n  SELECT <name>\n  SELECT <table.dbf>"
        },
        {
            MessageId::SelectEngineUnavailableText,
            "SELECT_ENGINE_UNAVAILABLE_TEXT",
            "COMMAND:SELECT",
            "ERROR",
            "ERROR",
            "SELECT: engine unavailable."
        },
        {
            MessageId::SelectOutOfRangeText,
            "SELECT_OUT_OF_RANGE_TEXT",
            "COMMAND:SELECT",
            "ERROR",
            "ERROR",
            "SELECT: out of range (valid 0..{max_slot})."
        },
        {
            MessageId::SelectNoAreaMatchesText,
            "SELECT_NO_AREA_MATCHES_TEXT",
            "COMMAND:SELECT",
            "ERROR",
            "ERROR",
            "SELECT: no area matches '{name}'. Use SELECT <0..{max_slot}> or a known name."
        },
        {
            MessageId::SelectSelectedAreaText,
            "SELECT_SELECTED_AREA_TEXT",
            "COMMAND:SELECT",
            "STATUS",
            "INFO",
            "Selected area {slot}."
        },
        {
            MessageId::SelectCurrentAreaText,
            "SELECT_CURRENT_AREA_TEXT",
            "COMMAND:SELECT",
            "STATUS",
            "INFO",
            "Current area: {slot}"
        },
        {
            MessageId::SelectCurrentAreaFileSummaryText,
            "SELECT_CURRENT_AREA_FILE_SUMMARY_TEXT",
            "COMMAND:SELECT",
            "STATUS",
            "INFO",
            "  File: {path}  Recs: {recs}  Recno: {recno}"
        },
        {
            MessageId::QuitUsageText,
            "QUIT_USAGE_TEXT",
            "COMMAND:QUIT",
            "USAGE",
            "INFO",
            "Usage:\n  QUIT\n  EXIT\nNotes:\n  Requests normal DotTalk++ shutdown."
        },
        {
            MessageId::UnlockUsageText,
            "UNLOCK_USAGE_TEXT",
            "COMMAND:UNLOCK",
            "USAGE",
            "INFO",
            "Usage:\n  UNLOCK USAGE\n  UNLOCK\n  UNLOCK <recno>\n  UNLOCK ALL\n  UNLOCK TABLE\nExamples:\n  UNLOCK\n  UNLOCK 10\n  UNLOCK ALL\n  UNLOCK TABLE\nNotes:\n  - UNLOCK USAGE does not require an open table.\n  - UNLOCK with no arguments unlocks the current record."
        },
        {
            MessageId::UnlockNoTableOpenText,
            "UNLOCK_NO_TABLE_OPEN_TEXT",
            "COMMAND:UNLOCK",
            "ERROR",
            "ERROR",
            "UNLOCK: no table open."
        },
        {
            MessageId::UnlockNoCurrentRecordText,
            "UNLOCK_NO_CURRENT_RECORD_TEXT",
            "COMMAND:UNLOCK",
            "ERROR",
            "ERROR",
            "UNLOCK: no current record."
        },
        {
            MessageId::UnlockRecordUnlockedText,
            "UNLOCK_RECORD_UNLOCKED_TEXT",
            "COMMAND:UNLOCK",
            "STATUS",
            "INFO",
            "UNLOCK: record {recno} unlocked."
        },
        {
            MessageId::UnlockTableUnlockedText,
            "UNLOCK_TABLE_UNLOCKED_TEXT",
            "COMMAND:UNLOCK",
            "STATUS",
            "INFO",
            "UNLOCK: table unlocked."
        },
        {
            MessageId::RefreshUsageText,
            "REFRESH_USAGE_TEXT",
            "COMMAND:REFRESH",
            "USAGE",
            "INFO",
            "Usage:\n  REFRESH\n  REFRESH USAGE"
        },
        {
            MessageId::RefreshNoTableOpenText,
            "REFRESH_NO_TABLE_OPEN_TEXT",
            "COMMAND:REFRESH",
            "ERROR",
            "ERROR",
            "No table open."
        },
        {
            MessageId::RefreshMissingFilenameText,
            "REFRESH_MISSING_FILENAME_TEXT",
            "COMMAND:REFRESH",
            "ERROR",
            "ERROR",
            "Refresh failed: current table has no filename()."
        },
        {
            MessageId::RefreshFileNotFoundText,
            "REFRESH_FILE_NOT_FOUND_TEXT",
            "COMMAND:REFRESH",
            "ERROR",
            "ERROR",
            "Refresh failed: file not found: {path}"
        },
        {
            MessageId::RefreshOrderRestoreWarningText,
            "REFRESH_ORDER_RESTORE_WARNING_TEXT",
            "COMMAND:REFRESH",
            "WARNING",
            "WARNING",
            "REFRESH warning: order restore failed: {detail}"
        },
        {
            MessageId::RefreshSuccessText,
            "REFRESH_SUCCESS_TEXT",
            "COMMAND:REFRESH",
            "STATUS",
            "INFO",
            "Refreshed {name} ({count} records)."
        },
        {
            MessageId::RefreshFailedText,
            "REFRESH_FAILED_TEXT",
            "COMMAND:REFRESH",
            "ERROR",
            "ERROR",
            "Refresh failed: {detail}"
        },
        {
            MessageId::ErrorClearUsageText,
            "ERROR_CLEAR_USAGE_TEXT",
            "COMMAND:ERROR_CLEAR",
            "USAGE",
            "INFO",
            "Usage:\n  ERROR_CLEAR\n  ERROR_CLEAR USAGE"
        },
        {
            MessageId::ErrorClearStatusText,
            "ERROR_CLEAR_STATUS_TEXT",
            "COMMAND:ERROR_CLEAR",
            "STATUS",
            "INFO",
            "Last error cleared."
        },
        {
            MessageId::ErrorStatusUsageText,
            "ERROR_STATUS_USAGE_TEXT",
            "COMMAND:ERROR_STATUS",
            "USAGE",
            "INFO",
            "Usage:\n  ERROR_STATUS\n  ERROR_STATUS USAGE"
        },
        {
            MessageId::ErrorStatusHeaderText,
            "ERROR_STATUS_HEADER_TEXT",
            "COMMAND:ERROR_STATUS",
            "STATUS",
            "INFO",
            "Last Error:"
        },
        {
            MessageId::ErrorStatusSeverityLineText,
            "ERROR_STATUS_SEVERITY_LINE_TEXT",
            "COMMAND:ERROR_STATUS",
            "STATUS",
            "INFO",
            "  Severity : {value}"
        },
        {
            MessageId::ErrorStatusFacilityLineText,
            "ERROR_STATUS_FACILITY_LINE_TEXT",
            "COMMAND:ERROR_STATUS",
            "STATUS",
            "INFO",
            "  Facility : {value} ({hex})"
        },
        {
            MessageId::ErrorStatusNumberLineText,
            "ERROR_STATUS_NUMBER_LINE_TEXT",
            "COMMAND:ERROR_STATUS",
            "STATUS",
            "INFO",
            "  Number   : {value}"
        },
        {
            MessageId::ErrorStatusHresultLineText,
            "ERROR_STATUS_HRESULT_LINE_TEXT",
            "COMMAND:ERROR_STATUS",
            "STATUS",
            "INFO",
            "  HRESULT  : {value}"
        },
        {
            MessageId::ErrorStatusMessageLineText,
            "ERROR_STATUS_MESSAGE_LINE_TEXT",
            "COMMAND:ERROR_STATUS",
            "STATUS",
            "INFO",
            "  Message  : {value}"
        },
        {
            MessageId::ErrorTestUsageText,
            "ERROR_TEST_USAGE_TEXT",
            "COMMAND:ERROR_TEST",
            "USAGE",
            "INFO",
            "Usage:\n  ERROR_TEST\n  ERROR_TEST USAGE"
        },
        {
            MessageId::ErrorTestHeaderText,
            "ERROR_TEST_HEADER_TEXT",
            "COMMAND:ERROR_TEST",
            "STATUS",
            "INFO",
            "ERROR subsystem self-test:"
        },
        {
            MessageId::ErrorTestResultLineText,
            "ERROR_TEST_RESULT_LINE_TEXT",
            "COMMAND:ERROR_TEST",
            "STATUS",
            "INFO",
            "  {name} {result}"
        },
        {
            MessageId::ErrorTestPassedText,
            "ERROR_TEST_PASSED_TEXT",
            "COMMAND:ERROR_TEST",
            "STATUS",
            "INFO",
            "All tests passed."
        },
        {
            MessageId::ErrorTestFailedText,
            "ERROR_TEST_FAILED_TEXT",
            "COMMAND:ERROR_TEST",
            "ERROR",
            "ERROR",
            "One or more tests FAILED."
        },
        {
            MessageId::ErrorTestOkLabel,
            "ERROR_TEST_OK_LABEL",
            "COMMAND:ERROR_TEST",
            "STATUS",
            "INFO",
            "OK"
        },
        {
            MessageId::ErrorTestFailLabel,
            "ERROR_TEST_FAIL_LABEL",
            "COMMAND:ERROR_TEST",
            "STATUS",
            "ERROR",
            "FAIL"
        },
        {
            MessageId::LockUsageText,
            "LOCK_USAGE_TEXT",
            "COMMAND:LOCK",
            "USAGE",
            "INFO",
            "Usage:\n  LOCK USAGE           - show this usage\n  LOCK                 - lock current record\n  LOCK <n>             - lock record <n>\n  LOCK ALL             - lock entire table\n  LOCK TABLE           - lock entire table\n  LOCK STATUS          - show lock status\n  LOCK WHO <n>         - show owner of record <n>"
        },
        {
            MessageId::LockStatusNoTableOpenText,
            "LOCK_STATUS_NO_TABLE_OPEN_TEXT",
            "COMMAND:LOCK",
            "ERROR",
            "ERROR",
            "LOCK STATUS: no table open."
        },
        {
            MessageId::LockStatusTableLineText,
            "LOCK_STATUS_TABLE_LINE_TEXT",
            "COMMAND:LOCK",
            "STATUS",
            "INFO",
            "Table: {state}{owner_clause}"
        },
        {
            MessageId::LockStatusRecordLineText,
            "LOCK_STATUS_RECORD_LINE_TEXT",
            "COMMAND:LOCK",
            "STATUS",
            "INFO",
            "Record {recno}: {state}{owner_clause}"
        },
        {
            MessageId::LockStateLockedText,
            "LOCK_STATE_LOCKED_TEXT",
            "COMMAND:LOCK",
            "STATUS",
            "INFO",
            "LOCKED"
        },
        {
            MessageId::LockStateUnlockedText,
            "LOCK_STATE_UNLOCKED_TEXT",
            "COMMAND:LOCK",
            "STATUS",
            "INFO",
            "unlocked"
        },
        {
            MessageId::LockOwnerClauseText,
            "LOCK_OWNER_CLAUSE_TEXT",
            "COMMAND:LOCK",
            "STATUS",
            "INFO",
            " (owner {owner})"
        },
        {
            MessageId::LockWhoNoneText,
            "LOCK_WHO_NONE_TEXT",
            "COMMAND:LOCK",
            "STATUS",
            "INFO",
            "LOCK WHO: no lock recorded for {recno}."
        },
        {
            MessageId::LockWhoOwnedText,
            "LOCK_WHO_OWNED_TEXT",
            "COMMAND:LOCK",
            "STATUS",
            "INFO",
            "LOCK WHO: record {recno} owned by {owner}"
        },
        {
            MessageId::LockNoTableOpenText,
            "LOCK_NO_TABLE_OPEN_TEXT",
            "COMMAND:LOCK",
            "ERROR",
            "ERROR",
            "LOCK: no table open."
        },
        {
            MessageId::LockNoCurrentRecordText,
            "LOCK_NO_CURRENT_RECORD_TEXT",
            "COMMAND:LOCK",
            "ERROR",
            "ERROR",
            "LOCK: no current record."
        },
        {
            MessageId::LockRecordLockedText,
            "LOCK_RECORD_LOCKED_TEXT",
            "COMMAND:LOCK",
            "STATUS",
            "INFO",
            "LOCK: record {recno} locked."
        },
        {
            MessageId::LockTableLockedText,
            "LOCK_TABLE_LOCKED_TEXT",
            "COMMAND:LOCK",
            "STATUS",
            "INFO",
            "LOCK: table locked."
        },
        {
            MessageId::LockFailedText,
            "LOCK_FAILED_TEXT",
            "COMMAND:LOCK",
            "ERROR",
            "ERROR",
            "LOCK: failed ({detail})."
        },
        {
            MessageId::RecnoUsageText,
            "RECNO_USAGE_TEXT",
            "COMMAND:RECNO",
            "USAGE",
            "INFO",
            "Usage:\n  RECNO\n  RECNO USAGE\n  RECNO <n>"
        },
        {
            MessageId::RecnoOutOfRangeText,
            "RECNO_OUT_OF_RANGE_TEXT",
            "COMMAND:RECNO",
            "ERROR",
            "ERROR",
            "Record number out of range (1..{max})."
        },
        {
            MessageId::RecnoUnableNavigateText,
            "RECNO_UNABLE_NAVIGATE_TEXT",
            "COMMAND:RECNO",
            "ERROR",
            "ERROR",
            "Unable to navigate to record {recno}."
        },
        {
            MessageId::ShowIniUsageText,
            "SHOWINI_USAGE_TEXT",
            "COMMAND:SHOWINI",
            "USAGE",
            "INFO",
            "Usage:\n  SHOWINI\n  SHOWINI USAGE\n  SHOWINI <table-or-ini>\n  SHOWINI PATH <ini-file>\nExamples:\n  SHOWINI\n  SHOWINI students\n  SHOWINI students.ini\n  SHOWINI PATH d:\\data\\students.ini"
        },
        {
            MessageId::ShowIniNoTableOpenText,
            "SHOWINI_NO_TABLE_OPEN_TEXT",
            "COMMAND:SHOWINI",
            "ERROR",
            "ERROR",
            "SHOWINI: no table open."
        },
        {
            MessageId::ShowIniPathRequiresFilenameText,
            "SHOWINI_PATH_REQUIRES_FILENAME_TEXT",
            "COMMAND:SHOWINI",
            "ERROR",
            "ERROR",
            "SHOWINI: PATH requires filename."
        },
        {
            MessageId::ShowIniFileNotFoundText,
            "SHOWINI_FILE_NOT_FOUND_TEXT",
            "COMMAND:SHOWINI",
            "ERROR",
            "ERROR",
            "SHOWINI: ini file not found: {path}"
        },
        {
            MessageId::ShowIniLoadFailedText,
            "SHOWINI_LOAD_FAILED_TEXT",
            "COMMAND:SHOWINI",
            "ERROR",
            "ERROR",
            "SHOWINI: load failed: {detail}"
        },
        {
            MessageId::ShowIniReportTitleText,
            "SHOWINI_REPORT_TITLE_TEXT",
            "COMMAND:SHOWINI",
            "STATUS",
            "INFO",
            "INI SETTINGS REPORT"
        },
        {
            MessageId::ShowIniFileLineText,
            "SHOWINI_FILE_LINE_TEXT",
            "COMMAND:SHOWINI",
            "STATUS",
            "INFO",
            "File: {path}"
        },
        {
            MessageId::ShowIniSectionHeaderText,
            "SHOWINI_SECTION_HEADER_TEXT",
            "COMMAND:SHOWINI",
            "STATUS",
            "INFO",
            "[{name}]"
        },
        {
            MessageId::ShowIniSectionDividerText,
            "SHOWINI_SECTION_DIVIDER_TEXT",
            "COMMAND:SHOWINI",
            "STATUS",
            "INFO",
            "----------------------------------------"
        },
        {
            MessageId::ShowIniKeyValueLineText,
            "SHOWINI_KEY_VALUE_LINE_TEXT",
            "COMMAND:SHOWINI",
            "STATUS",
            "INFO",
            "{key_padded} = {value}"
        }
    };
    return messages;
}

const std::vector<MessageTextDef>& all_message_texts()
{
    static const std::vector<MessageTextDef> texts = {
        // en-US is explicit even though MessageDef::text remains the final fallback.
        { MessageId::HelpHintCommand,       "en-US", "Type HELP {command} for more information." },
        { MessageId::MessageRoutingProofLine, "en-US", "Message routing proof: {provider} {symbol}" },
        { MessageId::MessageLocaleSet,      "en-US", "Message locale is {locale}" },
        { MessageId::SetMessageCatalogValidationGreenLabel, "en-US", "green" },
        { MessageId::SetMessageCatalogValidationIssuesFoundLabel, "en-US", "issues found" },
        { MessageId::SetMessageCatalogValidationStatusText, "en-US", "Message catalog validation: {status}\n  messages: {message_count}\n  text rows: {text_row_count}\n  locales: {locales}\n  issues: {issue_count}\n  boundary: report-only; no DBF, HELP DATA, CMDHELPCHK, source-mining, or catalog mutation." },
        { MessageId::SetLanguageStatusText, "en-US", "Message locale: {locale}\nSupported message locales: en-US, es, fr, de, it\nUsage: SET LANGUAGE [TO] <en-US|es|fr|de|it|DEFAULT>\n       SET LOCALE   [TO] <en-US|es|fr|de|it|DEFAULT>\n       SET LANGUAGE CHECK\n       SET LOCALE CHECK\n       SET LANGUAGE REPORT [locale]\n       SET LOCALE REPORT [locale]" },
        { MessageId::SetMessageCatalogProviderStatusText, "en-US", "Message catalog provider status:\n  mode: {mode}\n  active catalog present: {present}\n  active catalog loaded: {loaded}\n  message count: {message_count}\n  text row count: {text_row_count}\n  active dbf dir: {dbf_dir}\n  active indexes dir: {indexes_dir}\n  active lmdb dir: {lmdb_dir}\n  detail: {detail}\n  boundary: read-only status/load; no DBF/CDX/LMDB mutation; no runtime writeback" },
        { MessageId::SetLanguageActiveMessageEmissionText, "en-US", "SET LANGUAGE active message emission:\n  current locale: {locale}\n  provider mode: {mode}\n  active catalog loaded: {loaded}\n  symbol: HELP_HINT_COMMAND\n  fallback locale: en-US\n  text: {text}\n  boundary: read-only emission; no DBF/CDX/LMDB mutation; no runtime writeback" },
        { MessageId::SetLanguageActiveCatalogCheckText, "en-US", "SET LANGUAGE active catalog check:\n  current language: {locale}\n  message catalog mode: {mode}\n  active catalog present: {present}\n  active catalog loaded: {loaded}\n  message count: {message_count}\n  text row count: {text_row_count}\n  lookup symbol: MESSAGE_LOCALE_SET\n  lookup locale: {locale}\n  lookup text: {text}\n  runtime active catalog lookup proof: {proof}\n  boundary: read-only lookup; no DBF/CDX/LMDB mutation; no runtime writeback" },
        { MessageId::SetMessageProofUsageText, "en-US", "Usage:\n  SET MESSAGE PROOF ON\n  SET MESSAGE PROOF OFF\n  SET MESSAGE PROOF CHECK" },
        { MessageId::SetMessageEmitUsageText, "en-US", "Usage:\n  SET MESSAGE CATALOG CHECK\n  SET MESSAGE PROOF ON|OFF|CHECK\n  SET MESSAGE EMIT <symbol> [LOCALE <locale>] [ARG <name> <value>]" },
        { MessageId::SetMessageEmitStatusText, "en-US", "SET MESSAGE EMIT:\n  current locale: {current_locale}\n  provider mode: {mode}\n  active catalog present: {present}\n  active catalog loaded: {loaded}\n  message count: {message_count}\n  text row count: {text_row_count}\n  symbol: {symbol}\n  locale: {locale}\n  placeholder arg supplied: {placeholder_arg}\n  placeholder substitution proof: {substituted}\n  text: {text}\n  runtime controlled emission proof: {proof}\n  boundary: explicit diagnostic emission; no DBF/CDX/LMDB mutation; no runtime writeback" },
        { MessageId::SetMessageCatalogReportHeaderText, "en-US", "Message catalog report: report-only\n  schema intent: SYSTEM_MESSAGES + SYSTEM_MESSAGE_TEXT\n  messages: {message_count}\n  text rows: {text_row_count}\n  locales: {locales}\n  validation issues: {issue_count}\n  boundary: report-only console report; no DBF, HELP DATA, CMDHELPCHK, source-mining, file, or catalog mutation." },
        { MessageId::SetMessageCatalogReportLocaleFilterLine, "en-US", "  locale filter: {locale}" },
        { MessageId::SetMessageCatalogReportSystemMessagesTitle, "en-US", "SYSTEM_MESSAGES preview:" },
        { MessageId::SetMessageCatalogReportMessageRow, "en-US", "  {key} | owner={owner} | category={category} | severity={severity}" },
        { MessageId::SetMessageCatalogReportSystemMessageTextTitle, "en-US", "SYSTEM_MESSAGE_TEXT preview:" },
        { MessageId::SetMessageCatalogReportNoMatchingTextRows, "en-US", "<no matching text rows>" },
        { MessageId::SetMessageCatalogReportTextRow, "en-US", "  {key}:{value}" },
        { MessageId::SetMessageCatalogValidationIssueRowText, "en-US", "  {code} key={key} locale={locale} detail={detail}" },
        { MessageId::SetUsageText, "en-US", "Usage:\n  SET\n  SET USAGE\n  SET <option> [args]\nPublic options:\n  SET TABLE BUFFER ON|OFF [ALL]\n  SET CONSOLE ON|OFF\n  SET PRINT ON|OFF\n  SET PRINT TO <file>\n  SET DEVICE TO SCREEN\n  SET DEVICE TO FILE <path>\n  SET DEVICE TO PRINTER\n  SET DEVICE TO NULL\n  SET ALTERNATE ON|OFF\n  SET ALTERNATE TO <file>\n  SET TALK ON|OFF\n  SET ECHO ON|OFF\n  SET PAGING ON|OFF\n  SET WRAP ON|OFF\n  SET DELETED ON|OFF\n  SET CASE ON|OFF\n  SET NEAR ON|OFF\n  SET EDITOR TO <value>\n  SET EDITOR TO DEFAULT\n  SET EDITOR TO OFF\n  SET LANGUAGE [TO] <en-US|es|fr|de|it|DEFAULT>\n  SET LOCALE [TO] <en-US|es|fr|de|it|DEFAULT>\n  SET LANGUAGE CHECK\n  SET LOCALE CHECK\n  SET LANGUAGE REPORT [locale]\n  SET LOCALE REPORT [locale]\n  SET PATH <slot> <path>\n  SET MESSAGE CATALOG CHECK\n  SET MESSAGE EMIT <symbol> [LOCALE <locale>]\n  SET UNIQUE FIELD <name> ON|OFF\n  SET DEVDIAG ON|OFF|STATUS\n  SET TIMER ON|OFF\n  SET POLLING ON|OFF\n  SET INDEX TO <file>\n  SET ORDER TO <tag|0>\n\nDeveloper / transitional:\n  SET FILTER TO <expr>\n  SET RELATION <args...>\n  SET RELATIONS <args...>\n  SET CNX [TO] <container.cnx>\n  SET CDX [TO] <container.cdx>\n  SET LMDB <args...>" },
        { MessageId::SetTableBufferUsageText, "en-US", "Usage: SET TABLE BUFFER ON|OFF [ALL]" },
        { MessageId::SetTableBufferEngineUnavailableText, "en-US", "TABLE BUFFER: engine not available." },
        { MessageId::SetTableBufferAllStatusText, "en-US", "TABLE BUFFER: {state} for {count} open area(s)." },
        { MessageId::SetTableBufferCannotDetermineCurrentAreaText, "en-US", "TABLE BUFFER: cannot determine current area." },
        { MessageId::SetTableBufferAreaStatusText, "en-US", "TABLE BUFFER: {state} (area {area})" },
        { MessageId::TableBufferUsageText, "en-US", "Usage:\n  TABLE\n  TABLE ALL\n  TABLE STATUS [ALL]\n  TABLE BUFFER ON [PERSISTENT|RAM] [<n>|ALL|n,m,...]\n  TABLE BUFFER OFF [<n>|ALL|n,m,...]\n  TABLE BUFFER PERSISTENT [ON|OFF] [<n>|ALL|n,m,...]\n  TABLE BUFFER DIRTY [<n>|ALL|n,m,...]\n  TABLE BUFFER CLEAN [<n>|ALL|n,m,...]\n  TABLE BUFFER STALE [<n>|ALL|n,m,...]\n  TABLE BUFFER FRESH [<n>|ALL|n,m,...]\n  TABLE BUFFER STATUS [area|ALL]\n  TABLE BUFFER DUMP [area|ALL]\n  TABLE BUFFER TESTADD <recno> [flags] [field1] [value]\n  TABLE BUFFER RESET\nLegacy compatibility:\n  TABLE ON|OFF|DIRTY|CLEAN|STALE|FRESH [<n>|ALL|n,m,...]\n  TABLE ONALL|OFFALL|DIRTYALL|CLEANALL|STALEALL|FRESHALL" },
        { MessageId::TableBufferTestAddUsageText, "en-US", "Usage: TABLE BUFFER TESTADD <recno> [flags] [field1] [value]" },
        { MessageId::TableBufferAreasAllTitleText, "en-US", "areas 0..{last}" },
        { MessageId::TableBufferOccupiedAreasTitleText, "en-US", "occupied areas only" },
        { MessageId::TableBufferAreasUpdatedText, "en-US", "{count} area(s) updated." },
        { MessageId::TableBufferPersistenceUpdatedText, "en-US", "{count} area(s) persistence updated." },
        { MessageId::TableBufferInvalidAreaText, "en-US", "invalid area." },
        { MessageId::TableBufferStatusHeaderText, "en-US", "Area {area} buffer:" },
        { MessageId::TableBufferDumpHeaderText, "en-US", "Area {area} buffer dump:" },
        { MessageId::TableBufferEmptyBufferText, "en-US", "Area {area} buffer: empty" },
        { MessageId::TableBufferNoCurrentEnabledAreaText, "en-US", "no current enabled area." },
        { MessageId::TableBufferNoCurrentAreaSelectedOrEnabledText, "en-US", "no current area selected or not enabled." },
        { MessageId::TableBufferInvalidRecnoText, "en-US", "invalid recno." },
        { MessageId::TableBufferCannotDetermineCurrentAreaSpecifyText, "en-US", "cannot determine current area; specify an area number." },
        { MessageId::TableBufferResetAllText, "en-US", "reset all areas." },
        { MessageId::TableBufferUnknownSubcommandText, "en-US", "unknown subcommand '{subcommand}'." },
        { MessageId::SetConsoleUsageText, "en-US", "Usage: SET CONSOLE ON|OFF" },
        { MessageId::SetPrintUsageText, "en-US", "Usage: SET PRINT ON|OFF | SET PRINT TO <file>" },
        { MessageId::SetPrintToUsageText, "en-US", "Usage: SET PRINT TO <file>" },
        { MessageId::SetPrintToFailedText, "en-US", "PRINT TO failed: {path}" },
        { MessageId::SetPrintOnRequiresFileText, "en-US", "SET PRINT ON requires a file. Use: SET PRINT TO <file>" },
        { MessageId::SetAlternateUsageText, "en-US", "Usage: SET ALTERNATE ON|OFF | SET ALTERNATE TO <file>" },
        { MessageId::SetAlternateToUsageText, "en-US", "Usage: SET ALTERNATE TO <file>" },
        { MessageId::SetAlternateToFailedText, "en-US", "ALTERNATE TO failed: {path}" },
        { MessageId::SetAlternateToStatusText, "en-US", "ALTERNATE TO: {path}" },
        { MessageId::SetAlternateStatusText, "en-US", "Alternate is {state}" },
        { MessageId::SetTalkUsageText, "en-US", "Usage: SET TALK ON|OFF" },
        { MessageId::SetTalkStatusText, "en-US", "Talk is {state}" },
        { MessageId::SetEchoUsageText, "en-US", "Usage: SET ECHO ON|OFF" },
        { MessageId::SetEchoStatusText, "en-US", "Echo is {state}" },
        { MessageId::EchoUsageText, "en-US", "Usage:\n  ECHO\n  ECHO USAGE\n  ECHO <text>\nNotes:\n  - ECHO ON is not the toggle command; use SET ECHO ON or SET ECHO OFF." },
        { MessageId::SetPagingUsageText, "en-US", "Usage: SET PAGING ON|OFF" },
        { MessageId::SetPagingStatusText, "en-US", "Paging is {state}" },
        { MessageId::SetWrapUsageText, "en-US", "Usage: SET WRAP ON|OFF" },
        { MessageId::SetWrapStatusText, "en-US", "Wrap is {state}" },
        { MessageId::SetDevdiagUsageText, "en-US", "Usage: SET DEVDIAG ON|OFF|STATUS" },
        { MessageId::SetDevdiagStatusText, "en-US", "Passive dev diagnostics are {state}" },
        { MessageId::SetTimerUsageText, "en-US", "Usage: SET TIMER ON|OFF" },
        { MessageId::SetTimerStatusText, "en-US", "Timer is {state}" },
        { MessageId::SetPollingUsageText, "en-US", "Usage: SET POLLING ON|OFF" },
        { MessageId::SetPollingStatusText, "en-US", "Polling is {state}" },
        { MessageId::SetDeletedUsageText, "en-US", "Usage: SET DELETED ON|OFF" },
        { MessageId::SetDeletedStatusText, "en-US", "Deleted visibility: {state}" },
        { MessageId::SetEditorUsageText, "en-US", "Usage: SET EDITOR TO <value|DEFAULT|OFF>" },
        { MessageId::SetEditorOffStatusText, "en-US", "EDITOR is OFF" },
        { MessageId::SetEditorDefaultStatusText, "en-US", "EDITOR set to DEFAULT" },
        { MessageId::SetEditorCustomStatusText, "en-US", "EDITOR set to: {value}" },
        { MessageId::SetDeviceUsageText, "en-US", "Usage: SET DEVICE TO SCREEN|FILE <path>|PRINTER [name]|NULL" },
        { MessageId::SetDeviceFileUsageText, "en-US", "Usage: SET DEVICE TO FILE <path>" },
        { MessageId::SetDeviceFileFailedText, "en-US", "SET DEVICE TO FILE failed: {path}" },
        { MessageId::SetDevicePrinterFailedText, "en-US", "SET DEVICE TO PRINTER failed." },
        { MessageId::SetPrnConsoleNoteText, "en-US", "PRN: CONSOLE" },
        { MessageId::SetPrnNullNoteText, "en-US", "PRN: NULL" },
        { MessageId::SetPrnFileNoteText, "en-US", "PRN: FILE -> {path}" },
        { MessageId::SetPrnPrinterDefaultStagedNoteText, "en-US", "PRN: PRINTER -> (system default) [staged only]" },
        { MessageId::SetPrnPrinterNamedStagedNoteText, "en-US", "PRN: PRINTER -> {name} [staged only]" },
        { MessageId::AreaUsageText,         "en-US", "Usage:\n  AREA                   (Report current work-area state)\n  AREA USAGE             (Show this usage)\nNotes:\n  - AREA is read-only; it reports the current area slot/file/order state." },
        { MessageId::DisplayUsageText,      "en-US", "Usage:\n  DISPLAY\n  DISPLAY USAGE\n  DISPLAY <recno>" },
        { MessageId::DisplayRecordHeaderText, "en-US", "Record {recno}{deleted_suffix}" },
        { MessageId::DisplayRecordDeletedSuffixText, "en-US", " [DELETED]" },
        { MessageId::DisplayFieldLineText,  "en-US", "  {field} = {value}" },
        { MessageId::SetPathUsageText,      "en-US", "Usage:\n  SETPATH\n  SETPATH USAGE\n  SETPATH RESET\n  SETPATH <slot> [TO|=] <path>\n  SET PATH <slot> [TO|=] <path>\nSlots:\n  DATA DBF XDBF INDEXES LMDB WORKSPACES SCHEMAS PROJECTS SCRIPTS TESTS HELP LOGS TMP" },
        { MessageId::SetPathResetText,      "en-US", "reset to defaults." },
        { MessageId::SetPathUnknownSlotText, "en-US", "unknown slot: {slot}" },
        { MessageId::SetPathAssignedText,   "en-US", "{slot} = {path}" },
        { MessageId::SetPathWarnMissingText, "en-US", "warning: path does not exist" },
        { MessageId::SetPathWarnExpectedDirectoryText, "en-US", "warning: expected directory, found file" },
        { MessageId::SetIndexUsageText,     "en-US", "Usage:\n  SET INDEX USAGE\n  SET INDEX TO\n  SET INDEX TO <container>\n  SET INDEX TO <container> TAG <tag>\n  SET INDEX TO <container> <tag>\n  SETINDEX USAGE\n  SETINDEX TO\n  SETINDEX TO <container>\n  SETINDEX TO <container> TAG <tag>\n  SETINDEX TO <container> <tag>" },
        { MessageId::SetIndexNoTableOpenText, "en-US", "no table open." },
        { MessageId::SetIndexMissingFilenameText, "en-US", "missing filename." },
        { MessageId::SetIndexTagRequiresNameText, "en-US", "TAG requires a name." },
        { MessageId::SetIndexUnexpectedTrailingTokenText, "en-US", "unexpected trailing token '{token}'." },
        { MessageId::SetIndexUnsupportedContainerText, "en-US", "unsupported index container: {path}\nSupported: .inx, .cnx, .cdx" },
        { MessageId::SetIndexV32AcceptsInxOrCnxText, "en-US", "Classic xBase/VFP tables accept INX or CNX, not CDX.\nUse .inx or .cnx for this table." },
        { MessageId::SetIndexV64RequiresCdxText, "en-US", "True x64/v128 tables require CDX (LMDB-backed).\nUse .cdx for this table." },
        { MessageId::SetIndexUnknownFlavorText, "en-US", "unknown/unsupported table flavor for current area." },
        { MessageId::SetIndexNoValidV32IndexText, "en-US", "no valid v32 index found for '{token}'.\nLooked for .cnx, then .inx." },
        { MessageId::SetIndexUnableOpenCdxContainerText, "en-US", "unable to open CDX container." },
        { MessageId::SetIndexUnableReadCdxTagDirectoryText, "en-US", "unable to read CDX tag directory." },
        { MessageId::SetIndexTagNotFoundInContainerText, "en-US", "tag '{tag}' not found in {container}" },
        { MessageId::SetIndexOpenCdxContainerNotFoundText, "en-US", "openCdx: container not found: {container}" },
        { MessageId::SetIndexOpenCdxEnvMissingText, "en-US", "openCdx: LMDB env missing: {env}" },
        { MessageId::SetIndexOpenCdxBackendOpenFailedText, "en-US", "openCdx: backend open() failed [container={container}, env={env}]" },
        { MessageId::SetIndexOpenCdxBackendOpenFailedDetailText, "en-US", "{detail} [container={container}, env={env}]" },
        { MessageId::SetIndexOpenCnxContainerNotFoundText, "en-US", "openCnx: container not found: {container}" },
        { MessageId::SetIndexOpenCnxBackendOpenFailedText, "en-US", "openCnx: backend open failed" },
        { MessageId::SetIndexFileNotFoundText, "en-US", "file not found: {path}" },
        { MessageId::SetIndexCdxEnvMissingText, "en-US", "CDX container found but LMDB env missing" },
        { MessageId::SetIndexContainerLine, "en-US", "  Container: {path}" },
        { MessageId::SetIndexExpectedEnvLine, "en-US", "  Expected : {path}" },
        { MessageId::SetIndexLmdbEnvLine, "en-US", "  LMDB env : {path}" },
        { MessageId::SetIndexHintReindexBuildLmdbText, "en-US", "Hint: run REINDEX CDX or BUILDLMDB" },
        { MessageId::SetIndexCdxAttachedText, "en-US", "CDX attached" },
        { MessageId::SetIndexCnxAttachedText, "en-US", "CNX attached" },
        { MessageId::SetIndexInxAttachedText, "en-US", "INX attached" },
        { MessageId::SetIndexUseSetOrderHintText, "en-US", "Use SET ORDER TO TAG <tag>" },
        { MessageId::SetIndexTagNotFoundText, "en-US", "Tag '{tag}' not found." },
        { MessageId::SetIndexTagInvalidForTableText, "en-US", "Tag '{tag}' not valid for this table." },
        { MessageId::SetIndexInxTagIgnoredText, "en-US", "  Note: INX is single-order; tag ignored." },
        { MessageId::SetIndexUnsupportedResolvedExtensionText, "en-US", "unsupported resolved extension: {path}" },
        { MessageId::SetIndexUnableActivateTagText, "en-US", "unable to activate tag." },
        { MessageId::SetIndexAttachedActivatedText, "en-US", "attached + activated" },
        { MessageId::SetIndexTagAscLine, "en-US", "  TAG: '{tag}' (ASC)" },
        { MessageId::SetOrderUsageText, "en-US", "Usage:\n  SET ORDER\n  SET ORDER USAGE\n  SET ORDER 0\n  SET ORDER PHYSICAL\n  SET ORDER NATURAL\n  SET ORDER <tag>\n  SET ORDER TAG <tag>\n  SET ORDER TAG <tag> IN <alias>\n  SET ORDER <container> <tag> [ASC|DESC]\n  SETORDER\n  SETORDER USAGE\n  SETORDER <tag>" },
        { MessageId::SetOrderNonePhysicalText, "en-US", "none (physical order)." },
        { MessageId::SetOrderStatusText, "en-US", "{type} '{name}'{tag_clause} ({direction})" },
        { MessageId::SetOrderTagClauseText, "en-US", " TAG '{tag}'" },
        { MessageId::SetOrderMissingTargetText, "en-US", "missing target." },
        { MessageId::SetOrderEngineUnavailableText, "en-US", "engine not available." },
        { MessageId::SetOrderUnknownAreaAliasText, "en-US", "unknown area/alias: {alias}" },
        { MessageId::SetOrderNoTableOpenTargetAreaText, "en-US", "no table open in target area." },
        { MessageId::SetOrderClearedPhysicalText, "en-US", "cleared (physical order)." },
        { MessageId::SetOrderNumericNotImplementedText, "en-US", "numeric tag orders not yet implemented (requested {number})." },
        { MessageId::SetOrderMissingTagNameAfterTagText, "en-US", "missing tag name after TAG." },
        { MessageId::SetOrderExpectsTagNotContainerText, "en-US", "expects a tag name, not a container filename." },
        { MessageId::SetOrderUseTitleText, "en-US", "Use:" },
        { MessageId::SetOrderUnableResolveContainerText, "en-US", "unable to resolve container." },
        { MessageId::SetOrderMissingTagText, "en-US", "missing tag." },
        { MessageId::SetOrderFileNotFoundText, "en-US", "file not found: {path}" },
        { MessageId::SetOrderInxNotImplementedText, "en-US", ".INX activation is not implemented here." },
        { MessageId::SetOrderTagNotAvailableForCnxText, "en-US", "tag '{tag}' not available for CNX on current table." },
        { MessageId::SetOrderUnsupportedIndexContainerText, "en-US", "unsupported index container: {container}" },
        { MessageId::SetOrderUnableActivateOrderText, "en-US", "unable to activate order." },
        { MessageId::SetOrderActivatedText, "en-US", "{kind} TAG '{tag}' ({direction})" },
        { MessageId::SetOrderUnableOpenCdxContainerText, "en-US", "unable to open CDX container." },
        { MessageId::SetOrderUnableReadCdxTagDirectoryText, "en-US", "unable to read CDX tag directory." },
        { MessageId::SetOrderTagNotFoundInContainerText, "en-US", "tag '{tag}' not found in {container}" },
        { MessageId::SetOrderV32UsesCnxNotCdxText, "en-US", "Classic xBase/VFP tables use CNX for SET ORDER tag activation, not CDX." },
        { MessageId::SetOrderV64RequiresCdxText, "en-US", "True x64/v128 tables require CDX for SET ORDER." },
        { MessageId::SetOrderOpenCdxContainerNotFoundText, "en-US", "openCdx: container not found: {container}" },
        { MessageId::SetOrderOpenCdxEnvMissingText, "en-US", "openCdx: LMDB env missing: {env}" },
        { MessageId::SetOrderOpenCdxBackendOpenFailedText, "en-US", "openCdx: backend open() failed [container={container}, env={env}]" },
        { MessageId::SetOrderOpenCdxBackendOpenFailedDetailText, "en-US", "{detail} [container={container}, env={env}]" },
        { MessageId::SetOrderOpenCnxContainerNotFoundText, "en-US", "openCnx: container not found: {container}" },
        { MessageId::SetOrderOpenCnxBackendOpenFailedText, "en-US", "openCnx: backend open failed" },
        { MessageId::SetCdxUsageText, "en-US", "Usage:\n  SET CDX USAGE\n  SET CDX\n  SET CDX <name-or-path>\n  SETCDX\n  SETCDX USAGE\n  SETCDX <name-or-path>" },
        { MessageId::SetCdxAttachedText, "en-US", "attached \"{path}\"" },
        { MessageId::SetCdxFailedText, "en-US", "failed: {detail}" },
        { MessageId::SetCnxUsageText, "en-US", "Usage:\n  SET CNX USAGE\n  SET CNX\n  SET CNX <name-or-path>\n  SETCNX\n  SETCNX USAGE\n  SETCNX <name-or-path>" },
        { MessageId::SetCnxAttachedText, "en-US", "attached \"{path}\"" },
        { MessageId::SetCnxFailedText, "en-US", "failed: {detail}" },
        { MessageId::SetLmdbUsageText, "en-US", "Usage:\n  SET LMDB\n  SET LMDB USAGE\n  SET LMDB 0\n  SET LMDB <stem> [<tag>] [--asc|--desc]\n  SET LMDB <container.cdx> [<tag>] [--asc|--desc]\n  SET LMDB <envdir.cdx.d> [<tag>] [--asc|--desc]\n  SETLMDB\n  SETLMDB USAGE\n  SETLMDB 0\n  SETLMDB <stem> [<tag>] [--asc|--desc]" },
        { MessageId::SetLmdbStatusText, "en-US", "container '{container}' TAG '{tag}' ({direction})" },
        { MessageId::SetLmdbBackendLineText, "en-US", "  backend: {backend}" },
        { MessageId::SetLmdbOpenCdxFailedText, "en-US", "error: {detail}" },
        { MessageId::SetLmdbUsingText, "en-US", "using CDX '{container}' TAG '{tag}' ({direction})" },
        { MessageId::SetLmdbEnvdirLineText, "en-US", "  envdir: {path}" },
        { MessageId::SetUniqueUsageText, "en-US", "Usage:\n  SET UNIQUE\n  SET UNIQUE USAGE\n  SET UNIQUE FIELD <name> ON\n  SET UNIQUE FIELD <name> OFF" },
        { MessageId::SetUniqueNoneText, "en-US", "UNIQUE: (none)" },
        { MessageId::SetUniqueFieldsText, "en-US", "UNIQUE fields: {fields}" },
        { MessageId::SetUniqueFieldStatusText, "en-US", "UNIQUE {state} for FIELD {field}." },
        { MessageId::SetCaseUsageText, "en-US", "Usage:\n  SET CASE\n  SET CASE USAGE\n  SET CASE ON\n  SET CASE OFF\n  SETCASE\n  SETCASE USAGE\n  SETCASE ON\n  SETCASE OFF" },
        { MessageId::SetCaseStatusText, "en-US", "CASE SENSITIVE: {state}" },
        { MessageId::SetNearUsageText, "en-US", "Usage:\n  SET NEAR\n  SET NEAR USAGE\n  SET NEAR ON\n  SET NEAR OFF\n  SETNEAR\n  SETNEAR USAGE\n  SETNEAR ON\n  SETNEAR OFF" },
        { MessageId::SetNearStatusText, "en-US", "NEAR: {state}" },
        { MessageId::SetFilterUsageText, "en-US", "Usage:\n  SET FILTER USAGE\n  SET FILTER TO <expr>\n  SET FILTER TO\n  SETFILTER USAGE\n  SETFILTER TO <expr>\n  SETFILTER TO" },
        { MessageId::SetFilterExpectedToText, "en-US", "expected 'TO'." },
        { MessageId::SetFilterClearedText, "en-US", "cleared." },
        { MessageId::SetFilterErrorText, "en-US", "error: {detail}" },
        { MessageId::SetFilterAppliedText, "en-US", "TO {expr}" },
        { MessageId::SetRelationUsageText, "en-US", "Usage:\n  SET RELATION USAGE\n  SET RELATION TO <expr> INTO <child>\n  SET RELATION TO <expr> INTO <child>, <expr> INTO <child>\n  SET RELATION ADDITIVE TO <expr> INTO <child>\n  SET RELATION OFF ALL\n  SET RELATION OFF INTO <child>" },
        { MessageId::SetRelationNoCurrentParentText, "en-US", "no current parent area" },
        { MessageId::SetRelationOkText, "en-US", "OK" },
        { MessageId::SetRelationOffIntoRequiresChildText, "en-US", "OFF INTO requires child area" },
        { MessageId::SetRelationExpectedOffTailText, "en-US", "expected INTO <child> or ALL after OFF" },
        { MessageId::SetRelationAdditiveRequiresToIntoText, "en-US", "ADDITIVE requires TO <expr> INTO <child>" },
        { MessageId::SetRelationAdditiveExpectsToText, "en-US", "ADDITIVE expects TO" },
        { MessageId::SetRelationExpectedToAdditiveOffText, "en-US", "expected TO, ADDITIVE, or OFF" },
        { MessageId::SetRelationInvalidClauseText, "en-US", "invalid TO ... INTO ... clause" },
        { MessageId::SetRelationEmptyExpressionForChildText, "en-US", "empty expression for child {child}" },
        { MessageId::RelDiagAddFailedNoFieldsText, "en-US", "add failed (no fields provided)" },
        { MessageId::RelDiagAddFailedFieldCountMismatchText, "en-US", "add failed (parent/child field counts differ)" },
        { MessageId::RelDiagAddFailedNotOpenText, "en-US", "add failed (parent/child not open)" },
        { MessageId::RelDiagParentFieldNotFoundText, "en-US", "parent field not found: {field}" },
        { MessageId::RelDiagChildFieldNotFoundText, "en-US", "child field not found: {field}" },
        { MessageId::RelDiagAddedText, "en-US", "{parent} -> {child} ON {fields}" },
        { MessageId::RelDiagNoRelationsDefinedText, "en-US", "no relations defined for {parent}" },
        { MessageId::RelDiagRelationNotFoundText, "en-US", "relation not found: {parent} -> {child}" },
        { MessageId::RelDiagRemovedText, "en-US", "removed {parent} -> {child}" },
        { MessageId::RelDiagClearedForText, "en-US", "cleared for {parent}" },
        { MessageId::RelDiagClearedAllText, "en-US", "cleared all" },
        { MessageId::SetRelationsUsageText, "en-US", "Usage:\n  SET RELATIONS\n  SET RELATIONS USAGE\n  SET RELATIONS ADD <parent> <child> ON f1[,f2...]\n  SET RELATIONS ADD <parent> <child> ON parent_f1[,parent_f2...] TO child_f1[,child_f2...]\n  SET RELATIONS CLEAR <parent>\n  SET RELATIONS CLEAR ALL\nExamples:\n  SET RELATIONS ADD STUDENTS ENROLL ON SID\n  SET RELATIONS CLEAR STUDENTS\n  SET RELATIONS CLEAR ALL" },
        { MessageId::RelationsUsageText, "en-US", "Usage:\n  RELATIONS\n  RELATIONS USAGE\n  RELATIONS ALL\n  SET RELATIONS\n  SET RELATIONS USAGE\n  SET RELATIONS ADD <parent> <child> ON f1[,f2...] [TO child_f1[,child_f2...]]\n  SET RELATIONS CLEAR <parent|ALL>\nExamples:\n  RELATIONS\n  RELATIONS ALL\n  SET RELATIONS ADD STUDENTS ENROLL ON SID\n  SET RELATIONS CLEAR ALL\nNotes:\n  - RELATIONS USAGE does not inspect or mutate relation state.\n  - SET RELATIONS USAGE does not mutate relation definitions." },
        { MessageId::RelationsFileUsageText, "en-US", "REL SAVE/LOAD syntax\n  REL SAVE [<file>|DEFAULT|DATASET <name>]\n  REL LOAD [<file>|DEFAULT|DATASET <name>]" },
        { MessageId::SetRelationsAddUsageText, "en-US", "Usage: SET RELATIONS ADD <parent> <child> ON f1,f2" },
        { MessageId::SetRelationsAddUsageWithToText, "en-US", "Usage: SET RELATIONS ADD <parent> <child> ON f1,f2 [TO child_f1,child_f2]" },
        { MessageId::SetRelationsNoFieldsText, "en-US", "no fields provided" },
        { MessageId::SetRelationsFieldCountMismatchText, "en-US", "parent/child field counts differ" },
        { MessageId::SetRelationsClearUsageText, "en-US", "Usage: SET RELATIONS CLEAR <parent>|ALL" },
        { MessageId::SetRelationsUnknownOpText, "en-US", "unknown op. Try: ADD / CLEAR" },
        { MessageId::RelListNoCurrentParentText, "en-US", "no current parent" },
        { MessageId::RelListTreeRootedAtText, "en-US", "Relations (tree) rooted at: {parent}" },
        { MessageId::RelListNoneText, "en-US", "  (none)" },
        { MessageId::RelListParentHeaderText, "en-US", "Relations for parent: {parent}" },
        { MessageId::RelListMatchLineText, "en-US", "  -> {child}  (matches: {count})" },
        { MessageId::RelSaveCannotWriteText, "en-US", "cannot write file: {path}" },
        { MessageId::RelSaveOkText, "en-US", "OK ({count} relation(s) saved to {path})" },
        { MessageId::RelLoadCannotReadText, "en-US", "cannot read file or file empty: {path}" },
        { MessageId::RelLoadNoRelationsFoundText, "en-US", "no relations found in file" },
        { MessageId::RelLoadOkText, "en-US", "OK ({count} relation(s) loaded from {path})" },
        { MessageId::RelJoinUsageText, "en-US", "REL JOIN syntax\n  REL JOIN [ONE] [DISTINCT|ALL] [LIMIT <n>] [<child1> <child2> ...] TUPLE <fields>\nFlags\n  ONE       emit exactly one row using the current relation context (historical behavior)\n  DISTINCT  de-duplicate tuples (field lists only)\n  ALL       allow duplicates (default; overrides DISTINCT)" },
        { MessageId::RelJoinLimitRequiresNumberText, "en-US", "LIMIT requires a number" },
        { MessageId::RelJoinMissingTupleText, "en-US", "missing TUPLE" },
        { MessageId::RelJoinTupleRequiresExpressionText, "en-US", "TUPLE requires an expression" },
        { MessageId::RelEnumUsageText, "en-US", "REL ENUM syntax\n  REL ENUM [DISTINCT|ALL] [LIMIT <n>] [<child1> <child2> ...] TUPLE <fields>\nFlags\n  DISTINCT  de-duplicate tuples (field lists only)\n  ALL       allow duplicates (default; overrides DISTINCT)" },
        { MessageId::RelEnumLimitRequiresNumberText, "en-US", "LIMIT requires a number" },
        { MessageId::RelEnumMissingTupleText, "en-US", "missing TUPLE" },
        { MessageId::RelEnumTupleRequiresExpressionText, "en-US", "TUPLE requires an expression" },
        { MessageId::ErsatzUsageText, "en-US", "Usage:\n  ERSATZ\n  ERSATZ USAGE\n  ERSATZ SAMPLE\n  ERSATZ SHOW\n  ERSATZ REFRESH\n  ERSATZ TREE\n  ERSATZ GRID\n  ERSATZ STATUS\n  ERSATZ ORDER\n  ERSATZ TOP\n  ERSATZ BOTTOM\n  ERSATZ NEXT [<n>]\n  ERSATZ PREV [<n>]\n  ERSATZ SKIP <n>\n  ERSATZ ROOT [<alias>]\n  ERSATZ LIMIT <n>\n  ERSATZ PATH <alias>\n  ERSATZ CLEARPATH\n  ERSATZ BACK\n  ERSATZ OPEN <workspace>\n  ERSATZ LOAD <name>\n  ERSATZ SAVE <name>\n  ERSATZ WLOAD <name>\n  ERSATZ DELTA MARK [<name>] [LIMIT <n>]\n  ERSATZ DELTA SHOW [<name>] [LIMIT <n>]\n  ERSATZ DELTA CLEAR <name>\n  ERSATZ DELTA CLEAR ALL\n  ERSATZ DELTA STATUS\n  ERSATZ RESET\nNotes:\n  - ERSATZ with no arguments renders the current browser snapshot.\n  - Navigation commands move the root cursor and render again.\n  - LOAD/SAVE/WLOAD interact with workspace files.\n  - SAMPLE prints a DotScript smoke test for MCC/ERSATZ smart-root behavior." },
        { MessageId::ErsatzStatusHeaderText, "en-US", "ERSATZ STATUS" },
        { MessageId::ErsatzSessionResetText, "en-US", "session reset." },
        { MessageId::ErsatzOrderLine, "en-US", "ERSATZ ORDER: {value}" },
        { MessageId::ErsatzRecnoStatusText, "en-US", "ERSATZ {verb}: recno {recno} ({order})" },
        { MessageId::ErsatzRootLine, "en-US", "ERSATZ ROOT: {value}" },
        { MessageId::ErsatzRootSetText, "en-US", "ERSATZ ROOT set to {value}." },
        { MessageId::ErsatzLimitRequiresNumberText, "en-US", "LIMIT requires a number." },
        { MessageId::ErsatzLimitSetText, "en-US", "ERSATZ LIMIT set to {value}." },
        { MessageId::ErsatzPathLine, "en-US", "ERSATZ PATH: {value}" },
        { MessageId::ErsatzPathClearedText, "en-US", "path cleared." },
        { MessageId::ErsatzPathAlreadyEmptyText, "en-US", "path already empty." },
        { MessageId::ErsatzOpenRequiresAliasText, "en-US", "OPEN requires a child alias." },
        { MessageId::ErsatzInvalidNextChildText, "en-US", "alias '{alias}' is not a valid next child for the current path." },
        { MessageId::ErsatzLoadFailedText, "en-US", "LOAD failed ({detail})" },
        { MessageId::ErsatzSaveFailedText, "en-US", "SAVE failed ({detail})" },
        { MessageId::ErsatzPositiveCountRequiredText, "en-US", "{verb} requires a positive count." },
        { MessageId::ErsatzSignedCountRequiredText, "en-US", "{verb} requires a signed count." },
        { MessageId::ErsatzUnknownSubcommandText, "en-US", "unknown subcommand: {subcommand}" },
        { MessageId::ErsatzAutoLoadedProfileText, "en-US", "auto-loaded browser profile for active workspace ({status})." },
        { MessageId::ErsatzRootSelectedFallbackText, "en-US", "root {existing} has no child relations; using selected alias {selected}." },
        { MessageId::ErsatzSelectedAliasRootText, "en-US", "using selected alias {selected} as relational browser root." },
        { MessageId::ErsatzRootInferredFallbackText, "en-US", "root {existing} has no child relations; inferred root {inferred} from active relation graph." },
        { MessageId::ErsatzInferredRootText, "en-US", "inferred root {inferred} from active relation graph." },
        { MessageId::ErsatzDeltaLimitRequiresNumberText, "en-US", "LIMIT requires a number." },
        { MessageId::ErsatzDeltaUsageText, "en-US", "ERSATZ DELTA syntax\n  ERSATZ DELTA MARK [name] [LIMIT n]   capture current tuple stream baseline\n  ERSATZ DELTA SHOW [name] [LIMIT n]   compare current tuple stream to baseline\n  ERSATZ DELTA [name] [LIMIT n]        same as SHOW\n  ERSATZ DELTA CLEAR [name|ALL]        clear saved baseline(s)\n  ERSATZ DELTA STATUS                  list saved baselines\n\nNotes:\n  Baselines are in-memory and session-local.\n  Identity currently uses the first tuple value, falling back to RECNO.\n  The tuple stream respects active order because it uses DbTupleStream." },
        { MessageId::ErsatzDeltaStatusHeaderText, "en-US", "ERSATZ DELTA STATUS" },
        { MessageId::ErsatzDeltaNoBaselinesText, "en-US", "  (no baselines)" },
        { MessageId::ErsatzDeltaAllBaselinesClearedText, "en-US", "all baselines cleared." },
        { MessageId::ErsatzDeltaClearResultText, "en-US", "{result} {name}." },
        { MessageId::ErsatzDeltaCapturedText, "en-US", "baseline {name} captured rows={rows} table={table}{limit_suffix}." },
        { MessageId::ErsatzDeltaNoBaselineNamedText, "en-US", "no baseline named {name}. Use ERSATZ DELTA MARK {name} first." },
        { MessageId::ErsatzDeltaSummaryText, "en-US", "{name} table={table} baseline_rows={baseline_rows} current_rows={current_rows} changes={changes}" },
        { MessageId::ErsatzDeltaNoTupleChangesText, "en-US", "No tuple changes." },
        { MessageId::UseUsageText,          "en-US", "Usage:\n  USE USAGE              (Show this usage)\n  USE <table>            (Open <DBF slot>/<table>.dbf in current area)\n  USE <table.dbf>        (Open named DBF; logical names resolve through DBF slot)\n  USE <path\\\\table.dbf>   (Open explicit path)\n  USE <table> NOINDEX    (Open in physical order; skip index auto-attach)\n  USE <table> NOIDX      (Alias of NOINDEX)\nNotes:\n  - USE closes/resets the current area before opening the target table.\n  - USE prevents duplicate opens of the same DBF path across work areas.\n  - USE auto-attaches memo storage when memo fields are present.\n  - USE auto-attaches flavor-appropriate indexes when present, unless NOINDEX/NOIDX is used.\n  - USE prefers the configured INDEXES slot and falls back to the DBF directory.\n  - x64/v128 tables prefer CDX.\n  - x32 tables prefer CNX, then INX." },
        { MessageId::LocateUsageText,       "en-US", "Usage:\n  LOCATE USAGE\n  LOCATE FOR <expr>\n  LOCATE <field> <op> <value>\nExamples:\n  LOCATE FOR LNAME = Smith\n  LOCATE LNAME = Smith\n  LOCATE FOR BALANCE > 100\nNotes:\n  - LOCATE requires an open table except for LOCATE USAGE.\n  - LOCATE positions on the first matching record and updates CONTINUE state." },
        { MessageId::LocateFoundText,       "en-US", "Located." },
        { MessageId::LocateNotFoundText,    "en-US", "Not Located." },
        { MessageId::AppendUsageText,       "en-US", "Usage:\n  APPEND USAGE\n  APPEND\n  APPEND <count>\n  APPEND MANY <count>\n  APPEND RAW\n  APPEND RAW MANY <count>\nNotes:\n  - APPEND with no arguments appends one blank record through the shared smart append path.\n  - APPEND MANY uses the smart batch append path.\n  - APPEND RAW uses the raw append path without inline index update." },
        { MessageId::AppendBlankUsageText,  "en-US", "Usage:\n  APPEND_BLANK USAGE\n  APPEND_BLANK\n  APPEND BLANK\nNotes:\n  - Appends one blank record through shared append support." },
        { MessageId::GoUsageText,           "en-US", "Usage:\n  GO\n  GO USAGE\n  GO TOP\n  GO BOTTOM\n  GO FIRST\n  GO LAST\n  GO TO <recno>\n  GO RECORD <recno>\n  GO <recno>\n  GO +<n>\n  GO -<n>" },
        { MessageId::GotoUsageText,         "en-US", "Usage:\n  GOTO USAGE\n  GOTO <recno>\n  GOTO FIRST\n  GOTO LAST" },
        { MessageId::ContinueUsageText,     "en-US", "Usage:\n  CONTINUE\n  CONTINUE USAGE\n  CONTINUE FOR <expr>" },
        { MessageId::FindUsageText,         "en-US", "Usage:\n  FIND USAGE\n  FIND <text>\n  FIND <field> <text>\n  FIND <text> IN <field>\nNotes:\n  - FIND requires an open table except for FIND USAGE.\n  - FIND delegates to SEEK when the active order can satisfy the request.\n  - Otherwise FIND scans the requested field and positions on the found record." },
        { MessageId::SeekUsageText,         "en-US", "Usage:\n  SEEK USAGE\n  SEEK <value> IN <field> [TRACE ON|OFF]\n  SEEK <field> = <value> [TRACE ON|OFF]\n  SEEK <field> <value>   [TRACE ON|OFF]\n  SEEK <value>           (uses active order/tag when set)\n  SEEK TRACE ON|OFF\nNotes:\n  SEEK requires an open table except for SEEK USAGE.\n  SEEK <value> uses the active order/tag when one is set." },
        { MessageId::IndexUsageText,        "en-US", "Usage: INDEX ON <field> TAG <name> [ASC|DESC] [1INX|2INX]\n   Field-number tokens are also accepted by the parser.\nDefaults: ASC, 2INX\nExamples:\n  INDEX ON LNAME TAG students\n  INDEX ON LNAME TAG students DESC\n  INDEX ON LNAME TAG students DESC 2INX\nNotes:\n  - INDEX requires an open table except for INDEX USAGE.\n  - Deleted records are excluded.\n  - TAG resolves through the INDEXES path and must name an .inx target." },
        { MessageId::IndexInvalidTagPathText, "en-US", "invalid TAG path '{tag}'." },
        { MessageId::IndexUseBareNameHintText, "en-US", "Use a bare name (TAG students), an absolute path, or a slot path:" },
        { MessageId::IndexUnknownFieldText, "en-US", "unknown field '{field}'." },
        { MessageId::IndexAvailableFieldsTitle, "en-US", "Available:" },
        { MessageId::IndexTipFieldNumberText, "en-US", "Tip: INDEX ON #3 TAG students" },
        { MessageId::IndexTagMustNameInxText, "en-US", "TAG must name an .inx file." },
        { MessageId::IndexGotPathText, "en-US", "Got: {path}" },
        { MessageId::IndexCannotWriteFileText, "en-US", "cannot write file: {path}" },
        { MessageId::IndexWrittenText, "en-US", "written: {file} ({format}, expr: {expr}, {direction})" },
        { MessageId::IdxUsageText,          "en-US", "IDX is a memory-only educational index lab.\nIt teaches sorting and index concepts without writing .inx files.\nUse INDEX for persistent INX files.\n\nUsage:\n  IDX\n  IDX USAGE\n  IDX ON <field|#n> TAG <name> [SORT <algo>|<algo>] [ASC|DESC]\n  IDX LIST\n  IDX DROP <tag>\n  IDX DROP ALL\n  IDX HELP\n\nSort algorithms, Phase 1:\n  STD       C++ std::sort baseline\n  BUBBLE    classroom bubble sort\n\nExamples:\n  IDX ON LNAME TAG lname_std\n  IDX ON LNAME TAG lname_bubble BUBBLE\n  IDX ON LNAME TAG lname_bubble2 SORT BUBBLE DESC" },
        { MessageId::IdxExpectedOnText,     "en-US", "expected ON." },
        { MessageId::IdxMissingFieldTokenText, "en-US", "missing field token." },
        { MessageId::IdxExpectedTagText,    "en-US", "expected TAG." },
        { MessageId::IdxMissingTagNameText, "en-US", "missing TAG name." },
        { MessageId::IdxDuplicateSortOptionText, "en-US", "duplicate SORT option." },
        { MessageId::IdxSortRequiresAlgorithmText, "en-US", "SORT requires an algorithm name." },
        { MessageId::IdxUnknownSortAlgorithmText, "en-US", "unknown SORT algorithm '{algorithm}'. Supported: STD, BUBBLE." },
        { MessageId::IdxDuplicateDirectionOptionText, "en-US", "duplicate direction option." },
        { MessageId::IdxUnexpectedTokenText, "en-US", "unexpected token '{token}'." },
        { MessageId::IdxBuildCreatedText,   "en-US", "Memory index {verb}: {tag}" },
        { MessageId::IdxExprLineText,       "en-US", "  expr       : {value}" },
        { MessageId::IdxSortLineText,       "en-US", "  sort       : {value}" },
        { MessageId::IdxDirectionLineText,  "en-US", "  direction  : {value}" },
        { MessageId::IdxRecordsLineText,    "en-US", "  records    : {indexed} indexed / {scanned} scanned" },
        { MessageId::IdxDeletedLineText,    "en-US", "  deleted    : {count} skipped" },
        { MessageId::IdxBuildElapsedLineText, "en-US", "  build      : {value}" },
        { MessageId::IdxSortElapsedLineText, "en-US", "  sort       : {value}" },
        { MessageId::IdxComparisonsLineText, "en-US", "  compares   : {value}" },
        { MessageId::IdxSwapsLineText,      "en-US", "  swaps      : {value}" },
        { MessageId::IdxNoMemoryIndexesText, "en-US", "no memory indexes." },
        { MessageId::IdxMemoryIndexesTitle, "en-US", "IDX memory indexes:" },
        { MessageId::IdxListHeaderLineText, "en-US", "TAG               EXPR        SORT      DIR   ENTRIES   BUILD" },
        { MessageId::IdxDropUsageText,      "en-US", "Usage: IDX DROP <tag>|ALL" },
        { MessageId::IdxNoMemoryIndexesToDropText, "en-US", "no memory indexes to drop." },
        { MessageId::IdxDroppedAllText,     "en-US", "dropped all memory indexes." },
        { MessageId::IdxDroppedMemoryIndexText, "en-US", "dropped memory index {tag}." },
        { MessageId::IdxMemoryIndexNotFoundText, "en-US", "memory index not found: {tag}" },
        { MessageId::IdxBuildUsageText,     "en-US", "Usage: IDX ON <field|#n> TAG <name> [SORT <algo>|<algo>] [ASC|DESC]" },
        { MessageId::IdxUnknownCommandText, "en-US", "unknown command '{command}'." },
        { MessageId::SkipUsageText,         "en-US", "Usage:\n  SKIP\n  SKIP USAGE\n  SKIP <n>" },
        { MessageId::CountUsageText,        "en-US", "Usage:\n  COUNT\n  COUNT USAGE\n  COUNT ALL\n  COUNT FOR <expr>\n  COUNT WHERE <expr>\n  COUNT <expr>\n  COUNT DELETED\n  COUNT NOT DELETED\n  COUNT !DELETED\nNotes:\n  - COUNT with no arguments counts the current logical rowset.\n  - With no open table, COUNT preserves existing behavior and prints 0.\n  - COUNT preserves the active cursor where possible after scans." },
        { MessageId::TopUsageText,          "en-US", "Usage:\n  TOP\n  TOP USAGE" },
        { MessageId::BottomUsageText,       "en-US", "Usage:\n  BOTTOM\n  BOTTOM USAGE" },
        { MessageId::FirstUsageText,        "en-US", "Usage:\n  FIRST\n  FIRST USAGE" },
        { MessageId::LastUsageText,         "en-US", "Usage:\n  LAST\n  LAST USAGE" },
        { MessageId::NextUsageText,         "en-US", "Usage:\n  NEXT\n  NEXT USAGE" },
        { MessageId::PriorUsageText,        "en-US", "Usage:\n  PRIOR\n  PRIOR USAGE" },
        { MessageId::UseMissingTableNameText, "en-US", "missing table name." },
        { MessageId::UseAlreadyOpenCurrentAreaText, "en-US", "'{file}' is already open in current area {area}." },
        { MessageId::UseAlreadyOpenOtherAreaText, "en-US", "'{file}' is already open in area {area}. Close it first (e.g., SCHEMAS CLOSE {area})." },
        { MessageId::UseOpenFailedWithReasonText, "en-US", "Open failed: {reason}" },
        { MessageId::UseOpenFailedText,     "en-US", "Open failed." },
        { MessageId::UseMemoAttachFailedText, "en-US", "memo attach failed: {reason}" },
        { MessageId::UseOpenedSummaryText,  "en-US", "Opened {name} ({version}) : Record count {count}" },
        { MessageId::UseValidIndexesLineText, "en-US", "Valid Index/Indices   : {types}" },
        { MessageId::UseNoIndexSkippedText, "en-US", "NOINDEX: auto-attach skipped (physical order)." },
        { MessageId::UseAutoAttachedOrderTagUniqueText, "en-US", "Auto-attached order: {file} (tag: {tag} [UNIQUE])" },
        { MessageId::UseAutoAttachedOrderTagText, "en-US", "Auto-attached order: {file} (tag: {tag})" },
        { MessageId::UseAutoAttachedOrderText, "en-US", "Auto-attached order: {file}" },
        { MessageId::ContinueNoActiveLocateText, "en-US", "no active locate." },
        { MessageId::ContinueNotFoundText, "en-US", "not found." },
        { MessageId::ContinueFoundAtText,  "en-US", "Found at {recno}." },
        { MessageId::NavNoFileOpenText,     "en-US", "no file open." },
        { MessageId::NavReadCurrentFailedText, "en-US", "failed to read record." },
        { MessageId::NavAtTopText,          "en-US", "at top." },
        { MessageId::NavAtEndText,          "en-US", "at end." },
        { MessageId::NavFailedText,         "en-US", "failed." },
        { MessageId::NavRecnoLine,          "en-US", "Recno: {recno}" },
        { MessageId::GoExpectedPositiveRecordNumberText, "en-US", "expected a positive record number" },
        { MessageId::GoAreaQualifierNotSupportedYetText, "en-US", "'IN <alias>' not supported yet (SELECT the area, then GO ...)" },
        { MessageId::GoUnrecognizedCommandFormText, "en-US", "unrecognized form" },
        { MessageId::GpsUsageText,         "en-US", "Usage:\n  GPS\n  GPS USAGE\nNotes:\n  - Reports area slot, table label, physical recno, and logical row.\n  - With no open table, GPS reports the no-table cursor state." },
        { MessageId::GpsNoTableCursorLineText, "en-US", "Cursor: Area {area} of {occupied} ... No table open" },
        { MessageId::GpsCursorLineText,    "en-US", "Cursor: Area {area} of {occupied} ... Table {table} ... Physical Recno {recno}, Logical Row {logical_row}" },
        { MessageId::GpsUnnamedTableText,  "en-US", "(unnamed)" },
        { MessageId::CalcUsageText,         "en-US", "Usage:\n  CALC USAGE             (Show this usage)\n  CALC <expr>            (Evaluate expression and print result)\n  CALC (<expr>)          (Outer parentheses are allowed)\n  CALC <field> = <expr>  (If <field> exists, delegate to CALCWRITE)\nExamples:\n  CALC 1 + 2\n  CALC DATE()\n  CALC UPPER(LNAME)\n  CALC BALANCE = BALANCE + 10\nNotes:\n  - CALC expression-only mode is read-only.\n  - CALC field-assignment mode mutates through CALCWRITE.\n  - Empty CALC preserves existing behavior and prints .F." },
        { MessageId::CalcWriteUsageText,    "en-US", "Usage:\n  CALCWRITE USAGE\n  CALCWRITE <field> = <expr>\nExamples:\n  CALCWRITE BALANCE = BALANCE + 10\n  CALCWRITE LNAME = UPPER(LNAME)\n  CALCWRITE POSTED = TODAY\nNotes:\n  - CALCWRITE requires an open table and a current record.\n  - RHS expressions are evaluated with xexpr against the current area.\n  - Values are normalized and validated for the target field type.\n  - X64 memo fields update memo payloads and store memo object-id text.\n  - TABLE ON buffers changes and marks fields stale/dirty.\n  - TABLE OFF writes through DbArea::replaceFieldStored for index-safe mutation." },
        { MessageId::CalcWriteNoFileOpenText, "en-US", "no file open. Use: USE <table>" },
        { MessageId::CalcWriteUnknownFieldText, "en-US", "unknown field '{field}'" },
        { MessageId::CalcWriteNoCurrentRecordText, "en-US", "no current record." },
        { MessageId::CalcWriteCannotDetermineCurrentAreaText, "en-US", "cannot determine current area." },
        { MessageId::CalcWriteEvaluationFailedText, "en-US", "evaluation failed" },
        { MessageId::CalcWriteDetailText,   "en-US", "{detail}" },
        { MessageId::CalcWriteBufferedFieldValueText, "en-US", "buffered {field} = {value} at rec {recno}." },
        { MessageId::CalcWriteBufferedFieldText, "en-US", "buffered {field}." },
        { MessageId::CalcWriteWroteFieldValueText, "en-US", "wrote {field} = {value}" },
        { MessageId::ReplaceUsageText,      "en-US", "Usage:\n  REPLACE USAGE\n  REPLACE <field_index> WITH <value>\n  REPLACE <field_name>  WITH <value>\nExamples:\n  REPLACE LNAME WITH \"Smith\"\n  REPLACE 3 WITH TODAY\nNotes:\n  - REPLACE requires an open table and a current record.\n  - RHS values are evaluated before validation/storage.\n  - X64 memo text is converted to stored memo object-id text.\n  - TABLE ON buffers field changes and marks fields stale/dirty.\n  - TABLE OFF writes immediately through DbArea storage." },
        { MessageId::ReplaceNoFileOpenText, "en-US", "no file open." },
        { MessageId::ReplaceFieldNotFoundText, "en-US", "field not found." },
        { MessageId::ReplaceNoCurrentRecordText, "en-US", "no current record." },
        { MessageId::ReplaceCannotDetermineCurrentAreaText, "en-US", "cannot determine current area." },
        { MessageId::ReplaceDetailText,     "en-US", "{detail}" },
        { MessageId::ReplaceBufferedFieldRecordText, "en-US", "buffered field #{field} at rec {recno}." },
        { MessageId::ReplaceReplacedFieldRecordText, "en-US", "Replaced field #{field} at rec {recno}." },
        { MessageId::ReplaceWriteFailedDetailText, "en-US", "write failed ({detail})." },
        { MessageId::ReplaceWriteFailedText, "en-US", "write failed." },
        { MessageId::RollbackUsageText, "en-US", "Usage:\n  ROLLBACK USAGE\n  ROLLBACK\n  ROLLBACK ALL\nExamples:\n  ROLLBACK\n  ROLLBACK ALL\nNotes:\n  - ROLLBACK USAGE does not modify buffer state.\n  - ROLLBACK discards buffered/uncommitted table changes." },
        { MessageId::RollbackUsageText, "es", "Uso:\n  ROLLBACK USAGE\n  ROLLBACK\n  ROLLBACK ALL\nEjemplos:\n  ROLLBACK\n  ROLLBACK ALL\nNotas:\n  - ROLLBACK USAGE no modifica el estado del búfer.\n  - ROLLBACK descarta los cambios de tabla almacenados/sin confirmar." },
        { MessageId::RollbackUsageText, "fr", "Utilisation :\n  ROLLBACK USAGE\n  ROLLBACK\n  ROLLBACK ALL\nExemples :\n  ROLLBACK\n  ROLLBACK ALL\nRemarques :\n  - ROLLBACK USAGE ne modifie pas l'état du tampon.\n  - ROLLBACK abandonne les modifications de table en mémoire tampon/non validées." },
        { MessageId::RollbackUsageText, "de", "Verwendung:\n  ROLLBACK USAGE\n  ROLLBACK\n  ROLLBACK ALL\nBeispiele:\n  ROLLBACK\n  ROLLBACK ALL\nHinweise:\n  - ROLLBACK USAGE ändert den Pufferzustand nicht.\n  - ROLLBACK verwirft gepufferte/nicht bestätigte Tabellenänderungen." },
        { MessageId::RollbackUsageText, "it", "Uso:\n  ROLLBACK USAGE\n  ROLLBACK\n  ROLLBACK ALL\nEsempi:\n  ROLLBACK\n  ROLLBACK ALL\nNote:\n  - ROLLBACK USAGE non modifica lo stato del buffer.\n  - ROLLBACK annulla le modifiche alla tabella nel buffer/non confermate." },
        { MessageId::RollbackEngineUnavailableText, "en-US", "engine unavailable." },
        { MessageId::RollbackEngineUnavailableText, "es", "motor no disponible." },
        { MessageId::RollbackEngineUnavailableText, "fr", "moteur indisponible." },
        { MessageId::RollbackEngineUnavailableText, "de", "Engine nicht verfügbar." },
        { MessageId::RollbackEngineUnavailableText, "it", "motore non disponibile." },
        { MessageId::RollbackAllDiscardedText, "en-US", "discarded {changes} change(s) across {areas} area(s)." },
        { MessageId::RollbackAllDiscardedText, "es", "se descartaron {changes} cambio(s) en {areas} área(s)." },
        { MessageId::RollbackAllDiscardedText, "fr", "{changes} modification(s) abandonnée(s) sur {areas} zone(s)." },
        { MessageId::RollbackAllDiscardedText, "de", "{changes} Änderung(en) in {areas} Bereich(en) verworfen." },
        { MessageId::RollbackAllDiscardedText, "it", "scartate {changes} modifica/che in {areas} area/e." },
        { MessageId::RollbackCannotDetermineCurrentAreaText, "en-US", "cannot determine current area." },
        { MessageId::RollbackCannotDetermineCurrentAreaText, "es", "no se puede determinar el área actual." },
        { MessageId::RollbackCannotDetermineCurrentAreaText, "fr", "impossible de déterminer la zone active." },
        { MessageId::RollbackCannotDetermineCurrentAreaText, "de", "aktueller Bereich kann nicht ermittelt werden." },
        { MessageId::RollbackCannotDetermineCurrentAreaText, "it", "impossibile determinare l'area corrente." },
        { MessageId::RollbackDiscardedText, "en-US", "discarded {changes} change(s)." },
        { MessageId::RollbackDiscardedText, "es", "se descartaron {changes} cambio(s)." },
        { MessageId::RollbackDiscardedText, "fr", "{changes} modification(s) abandonnée(s)." },
        { MessageId::RollbackDiscardedText, "de", "{changes} Änderung(en) verworfen." },
        { MessageId::RollbackDiscardedText, "it", "scartate {changes} modifica/che." },
        { MessageId::DeleteUsageText, "en-US", "Usage:\n  DELETE USAGE\n  DELETE                         (delete current record)\n  DELETE ALL\n  DELETE REST\n  DELETE NEXT <n>\n  DELETE FOR <field> <op> <value>\nNotes:\n  - DELETE requires an open table except for DELETE USAGE.\n  - DELETE honors active SET FILTER in ALL/REST/NEXT/FOR scans.\n  - Direct-write mode updates active index backends best-effort." },
        { MessageId::DeleteUsageText, "es", "Uso:\n  DELETE USAGE\n  DELETE                         (elimina el registro actual)\n  DELETE ALL\n  DELETE REST\n  DELETE NEXT <n>\n  DELETE FOR <field> <op> <value>\nNotas:\n  - DELETE requiere una tabla abierta, excepto DELETE USAGE.\n  - DELETE respeta el SET FILTER activo en los recorridos ALL/REST/NEXT/FOR.\n  - El modo de escritura directa actualiza los índices activos según sea posible." },
        { MessageId::DeleteUsageText, "fr", "Utilisation :\n  DELETE USAGE\n  DELETE                         (supprime l'enregistrement courant)\n  DELETE ALL\n  DELETE REST\n  DELETE NEXT <n>\n  DELETE FOR <field> <op> <value>\nRemarques :\n  - DELETE requiert une table ouverte, sauf DELETE USAGE.\n  - DELETE respecte le SET FILTER actif dans les parcours ALL/REST/NEXT/FOR.\n  - Le mode écriture directe met à jour les index actifs au mieux." },
        { MessageId::DeleteUsageText, "de", "Verwendung:\n  DELETE USAGE\n  DELETE                         (löscht den aktuellen Datensatz)\n  DELETE ALL\n  DELETE REST\n  DELETE NEXT <n>\n  DELETE FOR <field> <op> <value>\nHinweise:\n  - DELETE erfordert eine geöffnete Tabelle, außer DELETE USAGE.\n  - DELETE berücksichtigt das aktive SET FILTER bei ALL/REST/NEXT/FOR-Durchläufen.\n  - Der Direktschreibmodus aktualisiert aktive Indizes nach Möglichkeit." },
        { MessageId::DeleteUsageText, "it", "Uso:\n  DELETE USAGE\n  DELETE                         (elimina il record corrente)\n  DELETE ALL\n  DELETE REST\n  DELETE NEXT <n>\n  DELETE FOR <field> <op> <value>\nNote:\n  - DELETE richiede una tabella aperta, tranne DELETE USAGE.\n  - DELETE rispetta il SET FILTER attivo nelle scansioni ALL/REST/NEXT/FOR.\n  - La modalità di scrittura diretta aggiorna gli indici attivi al meglio." },
        { MessageId::DeleteIndexStaleWarningText, "en-US", "warning - active index/order may now be stale after {stage}. Rebuild/rebind indexes if needed." },
        { MessageId::DeleteIndexStaleWarningText, "es", "advertencia: el índice/orden activo puede estar obsoleto tras {stage}. Reconstruya/revincule los índices si es necesario." },
        { MessageId::DeleteIndexStaleWarningText, "fr", "avertissement : l'index/ordre actif peut être obsolète après {stage}. Reconstruisez/reliez les index si nécessaire." },
        { MessageId::DeleteIndexStaleWarningText, "de", "Warnung: aktiver Index/aktive Ordnung kann nach {stage} veraltet sein. Indizes bei Bedarf neu erstellen/neu binden." },
        { MessageId::DeleteIndexStaleWarningText, "it", "avviso: l'indice/ordine attivo potrebbe essere obsoleto dopo {stage}. Ricostruire/ricollegare gli indici se necessario." },
        { MessageId::DeleteNoTableOpenText, "en-US", "No table is open. Use USE <file> first." },
        { MessageId::DeleteNoTableOpenText, "es", "No hay ninguna tabla abierta. Use primero USE <file>." },
        { MessageId::DeleteNoTableOpenText, "fr", "Aucune table ouverte. Utilisez d'abord USE <file>." },
        { MessageId::DeleteNoTableOpenText, "de", "Keine Tabelle geöffnet. Verwenden Sie zuerst USE <file>." },
        { MessageId::DeleteNoTableOpenText, "it", "Nessuna tabella aperta. Usare prima USE <file>." },
        { MessageId::DeleteCountText, "en-US", "{count} deleted" },
        { MessageId::DeleteCountText, "es", "{count} eliminado(s)" },
        { MessageId::DeleteCountText, "fr", "{count} supprimé(s)" },
        { MessageId::DeleteCountText, "de", "{count} gelöscht" },
        { MessageId::DeleteCountText, "it", "{count} eliminato/i" },
        { MessageId::RecallUsageText, "en-US", "Usage:\n  RECALL USAGE\n  RECALL\n  RECALL ALL\n  RECALL REST\n  RECALL NEXT <n>\n  RECALL FOR <expr>\nExamples:\n  RECALL\n  RECALL ALL\n  RECALL REST\n  RECALL NEXT 10\n  RECALL FOR LNAME = \"SMITH\"\nNotes:\n  - RECALL USAGE does not require an open table.\n  - RECALL with no arguments recalls the current record.\n  - RECALL target selection is deleted-only." },
        { MessageId::RecallUsageText, "es", "Uso:\n  RECALL USAGE\n  RECALL\n  RECALL ALL\n  RECALL REST\n  RECALL NEXT <n>\n  RECALL FOR <expr>\nEjemplos:\n  RECALL\n  RECALL ALL\n  RECALL REST\n  RECALL NEXT 10\n  RECALL FOR LNAME = \"SMITH\"\nNotas:\n  - RECALL USAGE no requiere una tabla abierta.\n  - RECALL sin argumentos recupera el registro actual.\n  - La selección de RECALL es solo de registros eliminados." },
        { MessageId::RecallUsageText, "fr", "Utilisation :\n  RECALL USAGE\n  RECALL\n  RECALL ALL\n  RECALL REST\n  RECALL NEXT <n>\n  RECALL FOR <expr>\nExemples :\n  RECALL\n  RECALL ALL\n  RECALL REST\n  RECALL NEXT 10\n  RECALL FOR LNAME = \"SMITH\"\nRemarques :\n  - RECALL USAGE ne requiert pas de table ouverte.\n  - RECALL sans argument restaure l'enregistrement courant.\n  - La sélection de RECALL ne concerne que les enregistrements supprimés." },
        { MessageId::RecallUsageText, "de", "Verwendung:\n  RECALL USAGE\n  RECALL\n  RECALL ALL\n  RECALL REST\n  RECALL NEXT <n>\n  RECALL FOR <expr>\nBeispiele:\n  RECALL\n  RECALL ALL\n  RECALL REST\n  RECALL NEXT 10\n  RECALL FOR LNAME = \"SMITH\"\nHinweise:\n  - RECALL USAGE erfordert keine geöffnete Tabelle.\n  - RECALL ohne Argumente stellt den aktuellen Datensatz wieder her.\n  - Die RECALL-Auswahl betrifft nur gelöschte Datensätze." },
        { MessageId::RecallUsageText, "it", "Uso:\n  RECALL USAGE\n  RECALL\n  RECALL ALL\n  RECALL REST\n  RECALL NEXT <n>\n  RECALL FOR <expr>\nEsempi:\n  RECALL\n  RECALL ALL\n  RECALL REST\n  RECALL NEXT 10\n  RECALL FOR LNAME = \"SMITH\"\nNote:\n  - RECALL USAGE non richiede una tabella aperta.\n  - RECALL senza argomenti ripristina il record corrente.\n  - La selezione di RECALL riguarda solo i record eliminati." },
        { MessageId::RecallIndexStaleWarningText, "en-US", "warning - active index/order may now be stale after index update. Rebuild/rebind indexes if needed." },
        { MessageId::RecallIndexStaleWarningText, "es", "advertencia: el índice/orden activo puede estar obsoleto tras la actualización del índice. Reconstruya/revincule los índices si es necesario." },
        { MessageId::RecallIndexStaleWarningText, "fr", "avertissement : l'index/ordre actif peut être obsolète après la mise à jour de l'index. Reconstruisez/reliez les index si nécessaire." },
        { MessageId::RecallIndexStaleWarningText, "de", "Warnung: aktiver Index/aktive Ordnung kann nach der Indexaktualisierung veraltet sein. Indizes bei Bedarf neu erstellen/neu binden." },
        { MessageId::RecallIndexStaleWarningText, "it", "avviso: l'indice/ordine attivo potrebbe essere obsoleto dopo l'aggiornamento dell'indice. Ricostruire/ricollegare gli indici se necessario." },
        { MessageId::RecallNoTableOpenText, "en-US", "No table is open. Use USE <file> first." },
        { MessageId::RecallNoTableOpenText, "es", "No hay ninguna tabla abierta. Use primero USE <file>." },
        { MessageId::RecallNoTableOpenText, "fr", "Aucune table ouverte. Utilisez d'abord USE <file>." },
        { MessageId::RecallNoTableOpenText, "de", "Keine Tabelle geöffnet. Verwenden Sie zuerst USE <file>." },
        { MessageId::RecallNoTableOpenText, "it", "Nessuna tabella aperta. Usare prima USE <file>." },
        { MessageId::RecallCountText, "en-US", "{count} recalled" },
        { MessageId::RecallCountText, "es", "{count} recuperado(s)" },
        { MessageId::RecallCountText, "fr", "{count} restauré(s)" },
        { MessageId::RecallCountText, "de", "{count} wiederhergestellt" },
        { MessageId::RecallCountText, "it", "{count} ripristinato/i" },
        { MessageId::RecallNextUsageText, "en-US", "Usage: RECALL NEXT <n>" },
        { MessageId::RecallNextUsageText, "es", "Uso: RECALL NEXT <n>" },
        { MessageId::RecallNextUsageText, "fr", "Utilisation : RECALL NEXT <n>" },
        { MessageId::RecallNextUsageText, "de", "Verwendung: RECALL NEXT <n>" },
        { MessageId::RecallNextUsageText, "it", "Uso: RECALL NEXT <n>" },
        { MessageId::EraseUsageText, "en-US", "Usage:\n  ERASE USAGE\n  ERASE <table> [CONFIRM]\n  ERASE TABLE <table> [CONFIRM]\nExamples:\n  ERASE TABLE clients\n  ERASE TABLE clients CONFIRM\n  ERASE students.dbf CONFIRM\nNotes:\n  - ERASE USAGE does not inspect or delete files.\n  - Physically deletes <table>.dbf and known same-stem sidecars.\n  - Without CONFIRM, performs a dry-run and prints what would be deleted.\n  - CONFIRM performs deletion." },
        { MessageId::EraseUsageText, "es", "Uso:\n  ERASE USAGE\n  ERASE <table> [CONFIRM]\n  ERASE TABLE <table> [CONFIRM]\nEjemplos:\n  ERASE TABLE clients\n  ERASE TABLE clients CONFIRM\n  ERASE students.dbf CONFIRM\nNotas:\n  - ERASE USAGE no inspecciona ni elimina archivos.\n  - Elimina físicamente <table>.dbf y los archivos complementarios del mismo nombre base.\n  - Sin CONFIRM, realiza una simulación e imprime lo que se eliminaría.\n  - CONFIRM realiza la eliminación." },
        { MessageId::EraseUsageText, "fr", "Utilisation :\n  ERASE USAGE\n  ERASE <table> [CONFIRM]\n  ERASE TABLE <table> [CONFIRM]\nExemples :\n  ERASE TABLE clients\n  ERASE TABLE clients CONFIRM\n  ERASE students.dbf CONFIRM\nRemarques :\n  - ERASE USAGE n'inspecte ni ne supprime de fichiers.\n  - Supprime physiquement <table>.dbf et les fichiers annexes de même racine.\n  - Sans CONFIRM, effectue une simulation et affiche ce qui serait supprimé.\n  - CONFIRM effectue la suppression." },
        { MessageId::EraseUsageText, "de", "Verwendung:\n  ERASE USAGE\n  ERASE <table> [CONFIRM]\n  ERASE TABLE <table> [CONFIRM]\nBeispiele:\n  ERASE TABLE clients\n  ERASE TABLE clients CONFIRM\n  ERASE students.dbf CONFIRM\nHinweise:\n  - ERASE USAGE prüft oder löscht keine Dateien.\n  - Löscht physisch <table>.dbf und bekannte Begleitdateien mit gleichem Stamm.\n  - Ohne CONFIRM wird ein Probelauf ausgeführt und angezeigt, was gelöscht würde.\n  - CONFIRM führt die Löschung aus." },
        { MessageId::EraseUsageText, "it", "Uso:\n  ERASE USAGE\n  ERASE <table> [CONFIRM]\n  ERASE TABLE <table> [CONFIRM]\nEsempi:\n  ERASE TABLE clients\n  ERASE TABLE clients CONFIRM\n  ERASE students.dbf CONFIRM\nNote:\n  - ERASE USAGE non ispeziona né elimina file.\n  - Elimina fisicamente <table>.dbf e i file collaterali con lo stesso stem.\n  - Senza CONFIRM esegue una simulazione e stampa ciò che verrebbe eliminato.\n  - CONFIRM esegue l'eliminazione." },
        { MessageId::EraseTableNotFoundText, "en-US", "Table not found: {table}" },
        { MessageId::EraseTableNotFoundText, "es", "Tabla no encontrada: {table}" },
        { MessageId::EraseTableNotFoundText, "fr", "Table introuvable : {table}" },
        { MessageId::EraseTableNotFoundText, "de", "Tabelle nicht gefunden: {table}" },
        { MessageId::EraseTableNotFoundText, "it", "Tabella non trovata: {table}" },
        { MessageId::EraseNothingToDeleteText, "en-US", "Nothing to delete for: {path}" },
        { MessageId::EraseNothingToDeleteText, "es", "Nada que eliminar para: {path}" },
        { MessageId::EraseNothingToDeleteText, "fr", "Rien à supprimer pour : {path}" },
        { MessageId::EraseNothingToDeleteText, "de", "Nichts zu löschen für: {path}" },
        { MessageId::EraseNothingToDeleteText, "it", "Niente da eliminare per: {path}" },
        { MessageId::EraseDryRunHeaderText, "en-US", "would delete {count} file(s) for table: {table}" },
        { MessageId::EraseDryRunHeaderText, "es", "se eliminarían {count} archivo(s) de la tabla: {table}" },
        { MessageId::EraseDryRunHeaderText, "fr", "supprimerait {count} fichier(s) pour la table : {table}" },
        { MessageId::EraseDryRunHeaderText, "de", "würde {count} Datei(en) für Tabelle löschen: {table}" },
        { MessageId::EraseDryRunHeaderText, "it", "eliminerebbe {count} file per la tabella: {table}" },
        { MessageId::EraseReRunConfirmText, "en-US", "Re-run with CONFIRM to perform deletion." },
        { MessageId::EraseReRunConfirmText, "es", "Vuelva a ejecutar con CONFIRM para realizar la eliminación." },
        { MessageId::EraseReRunConfirmText, "fr", "Relancez avec CONFIRM pour effectuer la suppression." },
        { MessageId::EraseReRunConfirmText, "de", "Mit CONFIRM erneut ausführen, um die Löschung durchzuführen." },
        { MessageId::EraseReRunConfirmText, "it", "Rieseguire con CONFIRM per effettuare l'eliminazione." },
        { MessageId::EraseDeletingHeaderText, "en-US", "deleting {count} file(s) for table: {table}" },
        { MessageId::EraseDeletingHeaderText, "es", "eliminando {count} archivo(s) de la tabla: {table}" },
        { MessageId::EraseDeletingHeaderText, "fr", "suppression de {count} fichier(s) pour la table : {table}" },
        { MessageId::EraseDeletingHeaderText, "de", "lösche {count} Datei(en) für Tabelle: {table}" },
        { MessageId::EraseDeletingHeaderText, "it", "eliminazione di {count} file per la tabella: {table}" },
        { MessageId::EraseFailedLineText, "en-US", "  FAILED: {file}  ({error})" },
        { MessageId::EraseFailedLineText, "es", "  ERROR: {file}  ({error})" },
        { MessageId::EraseFailedLineText, "fr", "  ÉCHEC : {file}  ({error})" },
        { MessageId::EraseFailedLineText, "de", "  FEHLGESCHLAGEN: {file}  ({error})" },
        { MessageId::EraseFailedLineText, "it", "  NON RIUSCITO: {file}  ({error})" },
        { MessageId::EraseDeletedEntriesLineText, "en-US", "  Deleted: {file}  ({entries} entries)" },
        { MessageId::EraseDeletedEntriesLineText, "es", "  Eliminado: {file}  ({entries} entradas)" },
        { MessageId::EraseDeletedEntriesLineText, "fr", "  Supprimé : {file}  ({entries} entrées)" },
        { MessageId::EraseDeletedEntriesLineText, "de", "  Gelöscht: {file}  ({entries} Einträge)" },
        { MessageId::EraseDeletedEntriesLineText, "it", "  Eliminato: {file}  ({entries} voci)" },
        { MessageId::EraseDeletedLineText, "en-US", "  Deleted: {file}" },
        { MessageId::EraseDeletedLineText, "es", "  Eliminado: {file}" },
        { MessageId::EraseDeletedLineText, "fr", "  Supprimé : {file}" },
        { MessageId::EraseDeletedLineText, "de", "  Gelöscht: {file}" },
        { MessageId::EraseDeletedLineText, "it", "  Eliminato: {file}" },
        { MessageId::EraseCompleteText, "en-US", "ERASE complete. Deleted: {deleted}, Failed: {failed}" },
        { MessageId::EraseCompleteText, "es", "ERASE completado. Eliminados: {deleted}, Fallidos: {failed}" },
        { MessageId::EraseCompleteText, "fr", "ERASE terminé. Supprimés : {deleted}, Échecs : {failed}" },
        { MessageId::EraseCompleteText, "de", "ERASE abgeschlossen. Gelöscht: {deleted}, Fehlgeschlagen: {failed}" },
        { MessageId::EraseCompleteText, "it", "ERASE completato. Eliminati: {deleted}, Falliti: {failed}" },
        { MessageId::ScriptUnableToOpenText, "en-US", "unable to open {file}" },
        { MessageId::ScriptUnableToOpenText, "es", "no se puede abrir {file}" },
        { MessageId::ScriptUnableToOpenText, "fr", "impossible d'ouvrir {file}" },
        { MessageId::ScriptUnableToOpenText, "de", "{file} kann nicht geöffnet werden" },
        { MessageId::ScriptUnableToOpenText, "it", "impossibile aprire {file}" },
        { MessageId::ScriptLineErrorText, "en-US", "{file}:{line}: {detail}" },
        { MessageId::ScriptLineErrorText, "es", "{file}:{line}: {detail}" },
        { MessageId::ScriptLineErrorText, "fr", "{file}:{line}: {detail}" },
        { MessageId::ScriptLineErrorText, "de", "{file}:{line}: {detail}" },
        { MessageId::ScriptLineErrorText, "it", "{file}:{line}: {detail}" },
        { MessageId::ImportUsageText, "en-US", "Usage:\n  IMPORT USAGE\n  IMPORT <csvfile>\nNotes:\n  - IMPORT requires an open table except for IMPORT USAGE.\n  - CSV headers are matched to field names case-insensitively.\n  - IMPORT appends records to the current table." },
        { MessageId::ImportUsageText, "es", "Uso:\n  IMPORT USAGE\n  IMPORT <csvfile>\nNotas:\n  - IMPORT requiere una tabla abierta, excepto IMPORT USAGE.\n  - Los encabezados CSV se asignan a los nombres de campo sin distinguir mayúsculas.\n  - IMPORT añade registros a la tabla actual." },
        { MessageId::ImportUsageText, "fr", "Utilisation :\n  IMPORT USAGE\n  IMPORT <csvfile>\nRemarques :\n  - IMPORT requiert une table ouverte, sauf IMPORT USAGE.\n  - Les en-têtes CSV sont associés aux noms de champs sans tenir compte de la casse.\n  - IMPORT ajoute des enregistrements à la table courante." },
        { MessageId::ImportUsageText, "de", "Verwendung:\n  IMPORT USAGE\n  IMPORT <csvfile>\nHinweise:\n  - IMPORT erfordert eine geöffnete Tabelle, außer IMPORT USAGE.\n  - CSV-Kopfzeilen werden den Feldnamen ohne Beachtung der Groß-/Kleinschreibung zugeordnet.\n  - IMPORT fügt Datensätze an die aktuelle Tabelle an." },
        { MessageId::ImportUsageText, "it", "Uso:\n  IMPORT USAGE\n  IMPORT <csvfile>\nNote:\n  - IMPORT richiede una tabella aperta, tranne IMPORT USAGE.\n  - Le intestazioni CSV vengono associate ai nomi dei campi senza distinzione tra maiuscole e minuscole.\n  - IMPORT aggiunge record alla tabella corrente." },
        { MessageId::ImportNoFileOpenText, "en-US", "No file open" },
        { MessageId::ImportNoFileOpenText, "es", "No hay archivo abierto" },
        { MessageId::ImportNoFileOpenText, "fr", "Aucun fichier ouvert" },
        { MessageId::ImportNoFileOpenText, "de", "Keine Datei geöffnet" },
        { MessageId::ImportNoFileOpenText, "it", "Nessun file aperto" },
        { MessageId::ImportCannotOpenText, "en-US", "Cannot open {file} for read." },
        { MessageId::ImportCannotOpenText, "es", "No se puede abrir {file} para lectura." },
        { MessageId::ImportCannotOpenText, "fr", "Impossible d'ouvrir {file} en lecture." },
        { MessageId::ImportCannotOpenText, "de", "{file} kann nicht zum Lesen geöffnet werden." },
        { MessageId::ImportCannotOpenText, "it", "Impossibile aprire {file} in lettura." },
        { MessageId::ImportEmptyCsvText, "en-US", "Empty CSV." },
        { MessageId::ImportEmptyCsvText, "es", "CSV vacío." },
        { MessageId::ImportEmptyCsvText, "fr", "CSV vide." },
        { MessageId::ImportEmptyCsvText, "de", "Leere CSV." },
        { MessageId::ImportEmptyCsvText, "it", "CSV vuoto." },
        { MessageId::ImportAppendFailedText, "en-US", "Append failed." },
        { MessageId::ImportAppendFailedText, "es", "Error al añadir." },
        { MessageId::ImportAppendFailedText, "fr", "Échec de l'ajout." },
        { MessageId::ImportAppendFailedText, "de", "Anhängen fehlgeschlagen." },
        { MessageId::ImportAppendFailedText, "it", "Aggiunta non riuscita." },
        { MessageId::ImportStoreErrorText, "en-US", "{detail} at rec {recno}, column {column}." },
        { MessageId::ImportStoreErrorText, "es", "{detail} en el registro {recno}, columna {column}." },
        { MessageId::ImportStoreErrorText, "fr", "{detail} à l'enregistrement {recno}, colonne {column}." },
        { MessageId::ImportStoreErrorText, "de", "{detail} bei Datensatz {recno}, Spalte {column}." },
        { MessageId::ImportStoreErrorText, "it", "{detail} al record {recno}, colonna {column}." },
        { MessageId::ImportWriteFailedText, "en-US", "Write failed at rec {recno}" },
        { MessageId::ImportWriteFailedText, "es", "Error de escritura en el registro {recno}" },
        { MessageId::ImportWriteFailedText, "fr", "Échec de l'écriture à l'enregistrement {recno}" },
        { MessageId::ImportWriteFailedText, "de", "Schreiben bei Datensatz {recno} fehlgeschlagen" },
        { MessageId::ImportWriteFailedText, "it", "Scrittura non riuscita al record {recno}" },
        { MessageId::ImportedCountText, "en-US", "Imported {count} records from {file}" },
        { MessageId::ImportedCountText, "es", "Se importaron {count} registros de {file}" },
        { MessageId::ImportedCountText, "fr", "{count} enregistrements importés depuis {file}" },
        { MessageId::ImportedCountText, "de", "{count} Datensätze aus {file} importiert" },
        { MessageId::ImportedCountText, "it", "Importati {count} record da {file}" },
        { MessageId::ExportUsageText, "en-US", "Usage:\n  EXPORT USAGE\n  EXPORT [TO] <file> [CSV|PIPE]\n  EXPORT <open-area-token> TO <file> [CSV|PIPE]\nNotes:\n  - EXPORT writes the current table as CSV by default.\n  - EXPORT <open-area-token> TO <file> writes an already-open named work area.\n  - Named EXPORT does not auto-open tables from disk.\n  - PIPE uses | as the delimiter.\n  - A missing extension is added automatically (.csv for CSV, .txt for PIPE).\n  - EXPORT honors the active SET FILTER for the exported area.\n  - EXPORT requires an open table except for EXPORT USAGE." },
        { MessageId::ExportUsageText, "es", "Uso:\n  EXPORT USAGE\n  EXPORT [TO] <file> [CSV|PIPE]\n  EXPORT <open-area-token> TO <file> [CSV|PIPE]\nNotas:\n  - EXPORT escribe la tabla actual como CSV de forma predeterminada.\n  - EXPORT <open-area-token> TO <file> escribe un área de trabajo ya abierta.\n  - EXPORT con nombre no abre tablas desde el disco automáticamente.\n  - PIPE usa | como delimitador.\n  - Se añade automáticamente una extensión que falte (.csv para CSV, .txt para PIPE).\n  - EXPORT respeta el SET FILTER activo del área exportada.\n  - EXPORT requiere una tabla abierta, excepto EXPORT USAGE." },
        { MessageId::ExportUsageText, "fr", "Utilisation :\n  EXPORT USAGE\n  EXPORT [TO] <file> [CSV|PIPE]\n  EXPORT <open-area-token> TO <file> [CSV|PIPE]\nRemarques :\n  - EXPORT écrit la table courante au format CSV par défaut.\n  - EXPORT <open-area-token> TO <file> écrit une zone de travail déjà ouverte.\n  - EXPORT nommé n'ouvre pas de tables depuis le disque.\n  - PIPE utilise | comme délimiteur.\n  - Une extension manquante est ajoutée automatiquement (.csv pour CSV, .txt pour PIPE).\n  - EXPORT respecte le SET FILTER actif de la zone exportée.\n  - EXPORT requiert une table ouverte, sauf EXPORT USAGE." },
        { MessageId::ExportUsageText, "de", "Verwendung:\n  EXPORT USAGE\n  EXPORT [TO] <file> [CSV|PIPE]\n  EXPORT <open-area-token> TO <file> [CSV|PIPE]\nHinweise:\n  - EXPORT schreibt die aktuelle Tabelle standardmäßig als CSV.\n  - EXPORT <open-area-token> TO <file> schreibt einen bereits geöffneten Arbeitsbereich.\n  - Benanntes EXPORT öffnet keine Tabellen von der Festplatte.\n  - PIPE verwendet | als Trennzeichen.\n  - Eine fehlende Erweiterung wird automatisch ergänzt (.csv für CSV, .txt für PIPE).\n  - EXPORT berücksichtigt das aktive SET FILTER des exportierten Bereichs.\n  - EXPORT erfordert eine geöffnete Tabelle, außer EXPORT USAGE." },
        { MessageId::ExportUsageText, "it", "Uso:\n  EXPORT USAGE\n  EXPORT [TO] <file> [CSV|PIPE]\n  EXPORT <open-area-token> TO <file> [CSV|PIPE]\nNote:\n  - EXPORT scrive la tabella corrente come CSV per impostazione predefinita.\n  - EXPORT <open-area-token> TO <file> scrive un'area di lavoro già aperta.\n  - EXPORT con nome non apre tabelle dal disco.\n  - PIPE usa | come delimitatore.\n  - Un'estensione mancante viene aggiunta automaticamente (.csv per CSV, .txt per PIPE).\n  - EXPORT rispetta il SET FILTER attivo dell'area esportata.\n  - EXPORT richiede una tabella aperta, tranne EXPORT USAGE." },
        { MessageId::ExportAmbiguousTokenText, "en-US", "ambiguous area token '{token}'{matches}" },
        { MessageId::ExportAmbiguousTokenText, "es", "token de área ambiguo '{token}'{matches}" },
        { MessageId::ExportAmbiguousTokenText, "fr", "jeton de zone ambigu '{token}'{matches}" },
        { MessageId::ExportAmbiguousTokenText, "de", "mehrdeutiges Bereichstoken '{token}'{matches}" },
        { MessageId::ExportAmbiguousTokenText, "it", "token di area ambiguo '{token}'{matches}" },
        { MessageId::ExportUnableToOpenText, "en-US", "Unable to open {dest} for write" },
        { MessageId::ExportUnableToOpenText, "es", "No se puede abrir {dest} para escritura" },
        { MessageId::ExportUnableToOpenText, "fr", "Impossible d'ouvrir {dest} en écriture" },
        { MessageId::ExportUnableToOpenText, "de", "{dest} kann nicht zum Schreiben geöffnet werden" },
        { MessageId::ExportUnableToOpenText, "it", "Impossibile aprire {dest} in scrittura" },
        { MessageId::ExportWriteFailedText, "en-US", "write failed while exporting {dest}" },
        { MessageId::ExportWriteFailedText, "es", "error de escritura al exportar {dest}" },
        { MessageId::ExportWriteFailedText, "fr", "échec de l'écriture lors de l'exportation de {dest}" },
        { MessageId::ExportWriteFailedText, "de", "Schreiben beim Exportieren von {dest} fehlgeschlagen" },
        { MessageId::ExportWriteFailedText, "it", "scrittura non riuscita durante l'esportazione di {dest}" },
        { MessageId::ExportCursorRestoreWarningText, "en-US", "export completed but cursor restore reported: {detail}" },
        { MessageId::ExportCursorRestoreWarningText, "es", "exportación completada, pero la restauración del cursor informó: {detail}" },
        { MessageId::ExportCursorRestoreWarningText, "fr", "exportation terminée, mais la restauration du curseur a signalé : {detail}" },
        { MessageId::ExportCursorRestoreWarningText, "de", "Export abgeschlossen, aber die Cursor-Wiederherstellung meldete: {detail}" },
        { MessageId::ExportCursorRestoreWarningText, "it", "esportazione completata, ma il ripristino del cursore ha segnalato: {detail}" },
        { MessageId::ExportedCountText, "en-US", "Exported {count} records to {dest}" },
        { MessageId::ExportedCountText, "es", "Se exportaron {count} registros a {dest}" },
        { MessageId::ExportedCountText, "fr", "{count} enregistrements exportés vers {dest}" },
        { MessageId::ExportedCountText, "de", "{count} Datensätze nach {dest} exportiert" },
        { MessageId::ExportedCountText, "it", "Esportati {count} record in {dest}" },
        { MessageId::ExportNoFileOpenText, "en-US", "No file open" },
        { MessageId::ExportNoFileOpenText, "es", "No hay archivo abierto" },
        { MessageId::ExportNoFileOpenText, "fr", "Aucun fichier ouvert" },
        { MessageId::ExportNoFileOpenText, "de", "Keine Datei geöffnet" },
        { MessageId::ExportNoFileOpenText, "it", "Nessun file aperto" },
        { MessageId::ExportErrorDetailText, "en-US", "{detail}" },
        { MessageId::ExportErrorDetailText, "es", "{detail}" },
        { MessageId::ExportErrorDetailText, "fr", "{detail}" },
        { MessageId::ExportErrorDetailText, "de", "{detail}" },
        { MessageId::ExportErrorDetailText, "it", "{detail}" },
        { MessageId::ExportNoOpenAreaMatchText, "en-US", "no open area matches '{token}'" },
        { MessageId::ExportNoOpenAreaMatchText, "es", "ningún área abierta coincide con '{token}'" },
        { MessageId::ExportNoOpenAreaMatchText, "fr", "aucune zone ouverte ne correspond à '{token}'" },
        { MessageId::ExportNoOpenAreaMatchText, "de", "kein geöffneter Bereich entspricht '{token}'" },
        { MessageId::ExportNoOpenAreaMatchText, "it", "nessuna area aperta corrisponde a '{token}'" },
        { MessageId::CreateUsageText, "en-US", "Usage:\n  CREATE USAGE\n  CREATE <name> (<field> <type>[, ...])\n  CREATE MSDOS <name> (<field> <type>[, ...])\n  CREATE DBASE <name> (<field> <type>[, ...])\n  CREATE FOX26 <name> (<field> <type>[, ...])\n  CREATE FOXPRO <name> (<field> <type>[, ...])\n  CREATE VFP <name> (<field> <type>[, ...])\n  CREATE X64 <name> (<field> <type>[, ...])\nTypes:\n  XBASE currently implemented: C(n), N(n[,d]), F(n[,d]), D, L, M\n  VFP/X64 currently implemented: C(n), N(n[,d]), F(n[,d]), D, L, M, I, B, Y, T\nExamples:\n  CREATE students (sid N(6), lname C(20), fname C(15))\n  CREATE X64 teachers (teacher_id I, full_name C(80), bio M)\nNotes:\n  - CREATE writes a DBF file under the configured DBF path slot for relative names.\n  - CREATE clears active order state and closes the current area before writing.\n  - CREATE opens the created table after a successful write.\n  - M fields trigger automatic memo attach after opening.\n  - X64 CREATE may use descriptor fallback tokens for DBF/VFP descriptor safety." },
        { MessageId::CreateUsageText, "es", "Uso:\n  CREATE USAGE\n  CREATE <name> (<field> <type>[, ...])\n  CREATE MSDOS <name> (<field> <type>[, ...])\n  CREATE DBASE <name> (<field> <type>[, ...])\n  CREATE FOX26 <name> (<field> <type>[, ...])\n  CREATE FOXPRO <name> (<field> <type>[, ...])\n  CREATE VFP <name> (<field> <type>[, ...])\n  CREATE X64 <name> (<field> <type>[, ...])\nTipos:\n  XBASE implementados actualmente: C(n), N(n[,d]), F(n[,d]), D, L, M\n  VFP/X64 implementados actualmente: C(n), N(n[,d]), F(n[,d]), D, L, M, I, B, Y, T\nEjemplos:\n  CREATE students (sid N(6), lname C(20), fname C(15))\n  CREATE X64 teachers (teacher_id I, full_name C(80), bio M)\nNotas:\n  - CREATE escribe un archivo DBF en la ranura de ruta DBF configurada para nombres relativos.\n  - CREATE borra el estado de orden activo y cierra el área actual antes de escribir.\n  - CREATE abre la tabla creada tras una escritura correcta.\n  - Los campos M activan la vinculación automática de memo tras la apertura.\n  - CREATE X64 puede usar tokens de reserva de descriptor para la seguridad del descriptor DBF/VFP." },
        { MessageId::CreateUsageText, "fr", "Utilisation :\n  CREATE USAGE\n  CREATE <name> (<field> <type>[, ...])\n  CREATE MSDOS <name> (<field> <type>[, ...])\n  CREATE DBASE <name> (<field> <type>[, ...])\n  CREATE FOX26 <name> (<field> <type>[, ...])\n  CREATE FOXPRO <name> (<field> <type>[, ...])\n  CREATE VFP <name> (<field> <type>[, ...])\n  CREATE X64 <name> (<field> <type>[, ...])\nTypes :\n  XBASE actuellement implémentés : C(n), N(n[,d]), F(n[,d]), D, L, M\n  VFP/X64 actuellement implémentés : C(n), N(n[,d]), F(n[,d]), D, L, M, I, B, Y, T\nExemples :\n  CREATE students (sid N(6), lname C(20), fname C(15))\n  CREATE X64 teachers (teacher_id I, full_name C(80), bio M)\nRemarques :\n  - CREATE écrit un fichier DBF dans l'emplacement de chemin DBF configuré pour les noms relatifs.\n  - CREATE efface l'état d'ordre actif et ferme la zone courante avant d'écrire.\n  - CREATE ouvre la table créée après une écriture réussie.\n  - Les champs M déclenchent l'attachement mémo automatique après ouverture.\n  - CREATE X64 peut utiliser des jetons de secours de descripteur pour la sécurité du descripteur DBF/VFP." },
        { MessageId::CreateUsageText, "de", "Verwendung:\n  CREATE USAGE\n  CREATE <name> (<field> <type>[, ...])\n  CREATE MSDOS <name> (<field> <type>[, ...])\n  CREATE DBASE <name> (<field> <type>[, ...])\n  CREATE FOX26 <name> (<field> <type>[, ...])\n  CREATE FOXPRO <name> (<field> <type>[, ...])\n  CREATE VFP <name> (<field> <type>[, ...])\n  CREATE X64 <name> (<field> <type>[, ...])\nTypen:\n  XBASE derzeit implementiert: C(n), N(n[,d]), F(n[,d]), D, L, M\n  VFP/X64 derzeit implementiert: C(n), N(n[,d]), F(n[,d]), D, L, M, I, B, Y, T\nBeispiele:\n  CREATE students (sid N(6), lname C(20), fname C(15))\n  CREATE X64 teachers (teacher_id I, full_name C(80), bio M)\nHinweise:\n  - CREATE schreibt bei relativen Namen eine DBF-Datei in den konfigurierten DBF-Pfad-Slot.\n  - CREATE löscht den aktiven Ordnungszustand und schließt den aktuellen Bereich vor dem Schreiben.\n  - CREATE öffnet die erstellte Tabelle nach erfolgreichem Schreiben.\n  - M-Felder lösen nach dem Öffnen das automatische Memo-Anhängen aus.\n  - CREATE X64 kann Deskriptor-Ersatztoken für die DBF/VFP-Deskriptorsicherheit verwenden." },
        { MessageId::CreateUsageText, "it", "Uso:\n  CREATE USAGE\n  CREATE <name> (<field> <type>[, ...])\n  CREATE MSDOS <name> (<field> <type>[, ...])\n  CREATE DBASE <name> (<field> <type>[, ...])\n  CREATE FOX26 <name> (<field> <type>[, ...])\n  CREATE FOXPRO <name> (<field> <type>[, ...])\n  CREATE VFP <name> (<field> <type>[, ...])\n  CREATE X64 <name> (<field> <type>[, ...])\nTipi:\n  XBASE attualmente implementati: C(n), N(n[,d]), F(n[,d]), D, L, M\n  VFP/X64 attualmente implementati: C(n), N(n[,d]), F(n[,d]), D, L, M, I, B, Y, T\nEsempi:\n  CREATE students (sid N(6), lname C(20), fname C(15))\n  CREATE X64 teachers (teacher_id I, full_name C(80), bio M)\nNote:\n  - CREATE scrive un file DBF nello slot di percorso DBF configurato per i nomi relativi.\n  - CREATE cancella lo stato di ordine attivo e chiude l'area corrente prima di scrivere.\n  - CREATE apre la tabella creata dopo una scrittura riuscita.\n  - I campi M attivano il collegamento memo automatico dopo l'apertura.\n  - CREATE X64 può usare token di ripiego del descrittore per la sicurezza del descrittore DBF/VFP." },
        { MessageId::CreateDetailText, "en-US", "{detail}" },
        { MessageId::CreateDetailText, "es", "{detail}" },
        { MessageId::CreateDetailText, "fr", "{detail}" },
        { MessageId::CreateDetailText, "de", "{detail}" },
        { MessageId::CreateDetailText, "it", "{detail}" },
        { MessageId::CreateFailedText, "en-US", "CREATE failed: {detail}" },
        { MessageId::CreateFailedText, "es", "CREATE falló: {detail}" },
        { MessageId::CreateFailedText, "fr", "Échec de CREATE : {detail}" },
        { MessageId::CreateFailedText, "de", "CREATE fehlgeschlagen: {detail}" },
        { MessageId::CreateFailedText, "it", "CREATE non riuscito: {detail}" },
        { MessageId::CreateReopenFailedDetailText, "en-US", "CREATE failed: file written but could not reopen table: {detail}" },
        { MessageId::CreateReopenFailedDetailText, "es", "CREATE falló: el archivo se escribió pero no se pudo reabrir la tabla: {detail}" },
        { MessageId::CreateReopenFailedDetailText, "fr", "Échec de CREATE : le fichier a été écrit mais la table n'a pas pu être rouverte : {detail}" },
        { MessageId::CreateReopenFailedDetailText, "de", "CREATE fehlgeschlagen: Datei geschrieben, aber Tabelle konnte nicht erneut geöffnet werden: {detail}" },
        { MessageId::CreateReopenFailedDetailText, "it", "CREATE non riuscito: file scritto ma impossibile riaprire la tabella: {detail}" },
        { MessageId::CreateReopenFailedText, "en-US", "CREATE failed: file written but could not reopen table." },
        { MessageId::CreateReopenFailedText, "es", "CREATE falló: el archivo se escribió pero no se pudo reabrir la tabla." },
        { MessageId::CreateReopenFailedText, "fr", "Échec de CREATE : le fichier a été écrit mais la table n'a pas pu être rouverte." },
        { MessageId::CreateReopenFailedText, "de", "CREATE fehlgeschlagen: Datei geschrieben, aber Tabelle konnte nicht erneut geöffnet werden." },
        { MessageId::CreateReopenFailedText, "it", "CREATE non riuscito: file scritto ma impossibile riaprire la tabella." },
        { MessageId::CreateMemoAttachFailedText, "en-US", "Memo attach failed: {detail}" },
        { MessageId::CreateMemoAttachFailedText, "es", "Error al vincular memo: {detail}" },
        { MessageId::CreateMemoAttachFailedText, "fr", "Échec de l'attachement mémo : {detail}" },
        { MessageId::CreateMemoAttachFailedText, "de", "Memo-Anhängen fehlgeschlagen: {detail}" },
        { MessageId::CreateMemoAttachFailedText, "it", "Collegamento memo non riuscito: {detail}" },
        { MessageId::CreatedText, "en-US", "Created {path} [{flavor}]{memo}" },
        { MessageId::CreatedText, "es", "Creado {path} [{flavor}]{memo}" },
        { MessageId::CreatedText, "fr", "Créé {path} [{flavor}]{memo}" },
        { MessageId::CreatedText, "de", "Erstellt {path} [{flavor}]{memo}" },
        { MessageId::CreatedText, "it", "Creato {path} [{flavor}]{memo}" },
        { MessageId::CreateOpenedText, "en-US", "Opened {file} with {count} records." },
        { MessageId::CreateOpenedText, "es", "Abierto {file} con {count} registros." },
        { MessageId::CreateOpenedText, "fr", "Ouvert {file} avec {count} enregistrements." },
        { MessageId::CreateOpenedText, "de", "{file} mit {count} Datensätzen geöffnet." },
        { MessageId::CreateOpenedText, "it", "Aperto {file} con {count} record." },
        { MessageId::CreateX64NameTooLongWarningText, "en-US", "field name '{name}' exceeds current x64 logical field-name length {limit}; it will not be stored as an authoritative x64 metadata name; descriptor fallback token is '{token}'{suffix}." },
        { MessageId::CreateX64NameTooLongWarningText, "es", "el nombre de campo '{name}' supera la longitud actual de nombre lógico de campo x64 de {limit}; no se almacenará como nombre de metadatos x64 autorizado; el token de reserva del descriptor es '{token}'{suffix}." },
        { MessageId::CreateX64NameTooLongWarningText, "fr", "le nom de champ '{name}' dépasse la longueur actuelle du nom logique de champ x64 de {limit} ; il ne sera pas stocké comme nom de métadonnées x64 faisant autorité ; le jeton de secours du descripteur est '{token}'{suffix}." },
        { MessageId::CreateX64NameTooLongWarningText, "de", "Feldname '{name}' überschreitet die aktuelle logische x64-Feldnamenlänge {limit}; er wird nicht als maßgeblicher x64-Metadatenname gespeichert; das Deskriptor-Ersatztoken ist '{token}'{suffix}." },
        { MessageId::CreateX64NameTooLongWarningText, "it", "il nome del campo '{name}' supera l'attuale lunghezza del nome logico del campo x64 di {limit}; non verrà memorizzato come nome di metadati x64 autorevole; il token di ripiego del descrittore è '{token}'{suffix}." },
        { MessageId::CreateX64FallbackTokenWarningText, "en-US", "field name '{name}' uses DBF/VFP descriptor fallback token '{token}'; authoritative x64 metadata name will be preserved{suffix}." },
        { MessageId::CreateX64FallbackTokenWarningText, "es", "el nombre de campo '{name}' usa el token de reserva del descriptor DBF/VFP '{token}'; el nombre de metadatos x64 autorizado se conservará{suffix}." },
        { MessageId::CreateX64FallbackTokenWarningText, "fr", "le nom de champ '{name}' utilise le jeton de secours du descripteur DBF/VFP '{token}' ; le nom de métadonnées x64 faisant autorité sera conservé{suffix}." },
        { MessageId::CreateX64FallbackTokenWarningText, "de", "Feldname '{name}' verwendet das DBF/VFP-Deskriptor-Ersatztoken '{token}'; der maßgebliche x64-Metadatenname bleibt erhalten{suffix}." },
        { MessageId::CreateX64FallbackTokenWarningText, "it", "il nome del campo '{name}' usa il token di ripiego del descrittore DBF/VFP '{token}'; il nome di metadati x64 autorevole verrà conservato{suffix}." },
        { MessageId::ZapUsageText, "en-US", "Usage:\n  ZAP USAGE\n  ZAP\nExamples:\n  ZAP\nNotes:\n  - ZAP USAGE does not require an open table.\n  - ZAP removes all records from the current non-memo DBF while preserving structure.\n  - ZAP closes the table on success; reopen with USE <table>.\n  - Index containers must be rebuilt/rebound after ZAP." },
        { MessageId::ZapUsageText, "es", "Uso:\n  ZAP USAGE\n  ZAP\nEjemplos:\n  ZAP\nNotas:\n  - ZAP USAGE no requiere una tabla abierta.\n  - ZAP elimina todos los registros del DBF no-memo actual conservando la estructura.\n  - ZAP cierra la tabla al finalizar correctamente; reábrala con USE <table>.\n  - Los contenedores de índice deben reconstruirse/revincularse después de ZAP." },
        { MessageId::ZapUsageText, "fr", "Utilisation :\n  ZAP USAGE\n  ZAP\nExemples :\n  ZAP\nRemarques :\n  - ZAP USAGE ne requiert pas de table ouverte.\n  - ZAP supprime tous les enregistrements du DBF non-mémo courant en conservant la structure.\n  - ZAP ferme la table en cas de succès ; rouvrez-la avec USE <table>.\n  - Les conteneurs d'index doivent être reconstruits/reliés après ZAP." },
        { MessageId::ZapUsageText, "de", "Verwendung:\n  ZAP USAGE\n  ZAP\nBeispiele:\n  ZAP\nHinweise:\n  - ZAP USAGE erfordert keine geöffnete Tabelle.\n  - ZAP entfernt alle Datensätze aus der aktuellen Nicht-Memo-DBF unter Beibehaltung der Struktur.\n  - ZAP schließt die Tabelle bei Erfolg; mit USE <table> erneut öffnen.\n  - Index-Container müssen nach ZAP neu erstellt/neu gebunden werden." },
        { MessageId::ZapUsageText, "it", "Uso:\n  ZAP USAGE\n  ZAP\nEsempi:\n  ZAP\nNote:\n  - ZAP USAGE non richiede una tabella aperta.\n  - ZAP rimuove tutti i record dal DBF non-memo corrente mantenendo la struttura.\n  - ZAP chiude la tabella in caso di successo; riaprirla con USE <table>.\n  - I contenitori di indice devono essere ricostruiti/ricollegati dopo ZAP." },
        { MessageId::ZapNoTableOpenText, "en-US", "No table open" },
        { MessageId::ZapNoTableOpenText, "es", "No hay tabla abierta" },
        { MessageId::ZapNoTableOpenText, "fr", "Aucune table ouverte" },
        { MessageId::ZapNoTableOpenText, "de", "Keine Tabelle geöffnet" },
        { MessageId::ZapNoTableOpenText, "it", "Nessuna tabella aperta" },
        { MessageId::ZapCannotZapMemoText, "en-US", "Cannot zap memo table (memo block handling not implemented)." },
        { MessageId::ZapCannotZapMemoText, "es", "No se puede aplicar ZAP a una tabla memo (manejo de bloques memo no implementado)." },
        { MessageId::ZapCannotZapMemoText, "fr", "Impossible d'appliquer ZAP à une table mémo (gestion des blocs mémo non implémentée)." },
        { MessageId::ZapCannotZapMemoText, "de", "ZAP für Memo-Tabelle nicht möglich (Memo-Block-Behandlung nicht implementiert)." },
        { MessageId::ZapCannotZapMemoText, "it", "Impossibile eseguire ZAP su una tabella memo (gestione dei blocchi memo non implementata)." },
        { MessageId::ZapFileNotFoundText, "en-US", "File not found: {path}" },
        { MessageId::ZapFileNotFoundText, "es", "Archivo no encontrado: {path}" },
        { MessageId::ZapFileNotFoundText, "fr", "Fichier introuvable : {path}" },
        { MessageId::ZapFileNotFoundText, "de", "Datei nicht gefunden: {path}" },
        { MessageId::ZapFileNotFoundText, "it", "File non trovato: {path}" },
        { MessageId::ZapZappingText, "en-US", "Zapping: {path}" },
        { MessageId::ZapZappingText, "es", "Aplicando ZAP: {path}" },
        { MessageId::ZapZappingText, "fr", "ZAP en cours : {path}" },
        { MessageId::ZapZappingText, "de", "ZAP läuft: {path}" },
        { MessageId::ZapZappingText, "it", "ZAP in corso: {path}" },
        { MessageId::ZapCannotOpenReadText, "en-US", "Cannot open file for reading" },
        { MessageId::ZapCannotOpenReadText, "es", "No se puede abrir el archivo para lectura" },
        { MessageId::ZapCannotOpenReadText, "fr", "Impossible d'ouvrir le fichier en lecture" },
        { MessageId::ZapCannotOpenReadText, "de", "Datei kann nicht zum Lesen geöffnet werden" },
        { MessageId::ZapCannotOpenReadText, "it", "Impossibile aprire il file in lettura" },
        { MessageId::ZapFailedReadHeaderText, "en-US", "Failed to read header" },
        { MessageId::ZapFailedReadHeaderText, "es", "Error al leer el encabezado" },
        { MessageId::ZapFailedReadHeaderText, "fr", "Échec de la lecture de l'en-tête" },
        { MessageId::ZapFailedReadHeaderText, "de", "Header konnte nicht gelesen werden" },
        { MessageId::ZapFailedReadHeaderText, "it", "Lettura dell'intestazione non riuscita" },
        { MessageId::ZapInvalidHeaderLenText, "en-US", "Invalid header length ({len})" },
        { MessageId::ZapInvalidHeaderLenText, "es", "Longitud de encabezado no válida ({len})" },
        { MessageId::ZapInvalidHeaderLenText, "fr", "Longueur d'en-tête non valide ({len})" },
        { MessageId::ZapInvalidHeaderLenText, "de", "Ungültige Header-Länge ({len})" },
        { MessageId::ZapInvalidHeaderLenText, "it", "Lunghezza dell'intestazione non valida ({len})" },
        { MessageId::ZapFailedReadHeaderBlockText, "en-US", "Failed to read full header block" },
        { MessageId::ZapFailedReadHeaderBlockText, "es", "Error al leer el bloque de encabezado completo" },
        { MessageId::ZapFailedReadHeaderBlockText, "fr", "Échec de la lecture du bloc d'en-tête complet" },
        { MessageId::ZapFailedReadHeaderBlockText, "de", "Vollständiger Header-Block konnte nicht gelesen werden" },
        { MessageId::ZapFailedReadHeaderBlockText, "it", "Lettura del blocco di intestazione completo non riuscita" },
        { MessageId::ZapHeaderNoTerminatorText, "en-US", "header does not end with 0x0D terminator" },
        { MessageId::ZapHeaderNoTerminatorText, "es", "el encabezado no termina con el terminador 0x0D" },
        { MessageId::ZapHeaderNoTerminatorText, "fr", "l'en-tête ne se termine pas par le terminateur 0x0D" },
        { MessageId::ZapHeaderNoTerminatorText, "de", "Header endet nicht mit dem Abschlusszeichen 0x0D" },
        { MessageId::ZapHeaderNoTerminatorText, "it", "l'intestazione non termina con il terminatore 0x0D" },
        { MessageId::ZapCannotCreateTempText, "en-US", "Cannot create temporary file: {path}" },
        { MessageId::ZapCannotCreateTempText, "es", "No se puede crear el archivo temporal: {path}" },
        { MessageId::ZapCannotCreateTempText, "fr", "Impossible de créer le fichier temporaire : {path}" },
        { MessageId::ZapCannotCreateTempText, "de", "Temporäre Datei kann nicht erstellt werden: {path}" },
        { MessageId::ZapCannotCreateTempText, "it", "Impossibile creare il file temporaneo: {path}" },
        { MessageId::ZapFailedWriteHeaderText, "en-US", "Failed writing header to temp file" },
        { MessageId::ZapFailedWriteHeaderText, "es", "Error al escribir el encabezado en el archivo temporal" },
        { MessageId::ZapFailedWriteHeaderText, "fr", "Échec de l'écriture de l'en-tête dans le fichier temporaire" },
        { MessageId::ZapFailedWriteHeaderText, "de", "Header konnte nicht in die temporäre Datei geschrieben werden" },
        { MessageId::ZapFailedWriteHeaderText, "it", "Scrittura dell'intestazione nel file temporaneo non riuscita" },
        { MessageId::ZapFailedWriteEofText, "en-US", "Failed writing EOF marker" },
        { MessageId::ZapFailedWriteEofText, "es", "Error al escribir el marcador EOF" },
        { MessageId::ZapFailedWriteEofText, "fr", "Échec de l'écriture du marqueur EOF" },
        { MessageId::ZapFailedWriteEofText, "de", "EOF-Markierung konnte nicht geschrieben werden" },
        { MessageId::ZapFailedWriteEofText, "it", "Scrittura del marcatore EOF non riuscita" },
        { MessageId::ZapFailedRenameBackupText, "en-US", "Failed to rename original to backup: {detail}" },
        { MessageId::ZapFailedRenameBackupText, "es", "Error al renombrar el original como copia de seguridad: {detail}" },
        { MessageId::ZapFailedRenameBackupText, "fr", "Échec du renommage de l'original en sauvegarde : {detail}" },
        { MessageId::ZapFailedRenameBackupText, "de", "Umbenennen des Originals in Sicherung fehlgeschlagen: {detail}" },
        { MessageId::ZapFailedRenameBackupText, "it", "Ridenominazione dell'originale in backup non riuscita: {detail}" },
        { MessageId::ZapFailedReplaceText, "en-US", "Failed to replace original: {detail}" },
        { MessageId::ZapFailedReplaceText, "es", "Error al reemplazar el original: {detail}" },
        { MessageId::ZapFailedReplaceText, "fr", "Échec du remplacement de l'original : {detail}" },
        { MessageId::ZapFailedReplaceText, "de", "Ersetzen des Originals fehlgeschlagen: {detail}" },
        { MessageId::ZapFailedReplaceText, "it", "Sostituzione dell'originale non riuscita: {detail}" },
        { MessageId::ZapRollbackFailedText, "en-US", "  Rollback also failed — manual recovery needed!" },
        { MessageId::ZapRollbackFailedText, "es", "  ¡La reversión también falló, se necesita recuperación manual!" },
        { MessageId::ZapRollbackFailedText, "fr", "  La restauration a également échoué — récupération manuelle nécessaire !" },
        { MessageId::ZapRollbackFailedText, "de", "  Rollback ebenfalls fehlgeschlagen — manuelle Wiederherstellung erforderlich!" },
        { MessageId::ZapRollbackFailedText, "it", "  Anche il rollback non è riuscito — è necessario un ripristino manuale!" },
        { MessageId::ZapOriginalRestoredText, "en-US", "  Original restored." },
        { MessageId::ZapOriginalRestoredText, "es", "  Original restaurado." },
        { MessageId::ZapOriginalRestoredText, "fr", "  Original restauré." },
        { MessageId::ZapOriginalRestoredText, "de", "  Original wiederhergestellt." },
        { MessageId::ZapOriginalRestoredText, "it", "  Originale ripristinato." },
        { MessageId::ZapCnxMarkedDirtyText, "en-US", "CNX marked dirty (reindex recommended): {file}" },
        { MessageId::ZapCnxMarkedDirtyText, "es", "CNX marcado como modificado (se recomienda reindexar): {file}" },
        { MessageId::ZapCnxMarkedDirtyText, "fr", "CNX marqué comme modifié (réindexation recommandée) : {file}" },
        { MessageId::ZapCnxMarkedDirtyText, "de", "CNX als geändert markiert (Neuindizierung empfohlen): {file}" },
        { MessageId::ZapCnxMarkedDirtyText, "it", "CNX contrassegnato come modificato (reindicizzazione consigliata): {file}" },
        { MessageId::ZapCnxCouldNotMarkText, "en-US", "note: CNX found but could not mark dirty" },
        { MessageId::ZapCnxCouldNotMarkText, "es", "nota: se encontró CNX pero no se pudo marcar como modificado" },
        { MessageId::ZapCnxCouldNotMarkText, "fr", "note : CNX trouvé mais impossible de le marquer comme modifié" },
        { MessageId::ZapCnxCouldNotMarkText, "de", "Hinweis: CNX gefunden, konnte aber nicht als geändert markiert werden" },
        { MessageId::ZapCnxCouldNotMarkText, "it", "nota: CNX trovato ma impossibile contrassegnarlo come modificato" },
        { MessageId::ZapIndexRebuildText, "en-US", "note: index container should be rebuilt: {file}" },
        { MessageId::ZapIndexRebuildText, "es", "nota: el contenedor de índice debe reconstruirse: {file}" },
        { MessageId::ZapIndexRebuildText, "fr", "note : le conteneur d'index doit être reconstruit : {file}" },
        { MessageId::ZapIndexRebuildText, "de", "Hinweis: Index-Container sollte neu erstellt werden: {file}" },
        { MessageId::ZapIndexRebuildText, "it", "nota: il contenitore di indice deve essere ricostruito: {file}" },
        { MessageId::ZapOrderRebuildText, "en-US", "note: order container should be rebuilt: {file}" },
        { MessageId::ZapOrderRebuildText, "es", "nota: el contenedor de orden debe reconstruirse: {file}" },
        { MessageId::ZapOrderRebuildText, "fr", "note : le conteneur d'ordre doit être reconstruit : {file}" },
        { MessageId::ZapOrderRebuildText, "de", "Hinweis: Ordnungs-Container sollte neu erstellt werden: {file}" },
        { MessageId::ZapOrderRebuildText, "it", "nota: il contenitore di ordine deve essere ricostruito: {file}" },
        { MessageId::ZapCompleteText, "en-US", "ZAP complete. All records removed." },
        { MessageId::ZapCompleteText, "es", "ZAP completado. Se eliminaron todos los registros." },
        { MessageId::ZapCompleteText, "fr", "ZAP terminé. Tous les enregistrements ont été supprimés." },
        { MessageId::ZapCompleteText, "de", "ZAP abgeschlossen. Alle Datensätze wurden entfernt." },
        { MessageId::ZapCompleteText, "it", "ZAP completato. Tutti i record sono stati rimossi." },
        { MessageId::ZapReadyForUseText, "en-US", "{file} ready for use." },
        { MessageId::ZapReadyForUseText, "es", "{file} listo para usar." },
        { MessageId::ZapReadyForUseText, "fr", "{file} prêt à l'emploi." },
        { MessageId::ZapReadyForUseText, "de", "{file} einsatzbereit." },
        { MessageId::ZapReadyForUseText, "it", "{file} pronto per l'uso." },
        { MessageId::ZapSidecarsNoneText, "en-US", "Sidecar(s): none." },
        { MessageId::ZapSidecarsNoneText, "es", "Archivos complementarios: ninguno." },
        { MessageId::ZapSidecarsNoneText, "fr", "Fichiers annexes : aucun." },
        { MessageId::ZapSidecarsNoneText, "de", "Begleitdateien: keine." },
        { MessageId::ZapSidecarsNoneText, "it", "File collaterali: nessuno." },
        { MessageId::ZapReopenText, "en-US", "Table is closed. Reopen with: USE {stem}" },
        { MessageId::ZapReopenText, "es", "La tabla está cerrada. Reábrala con: USE {stem}" },
        { MessageId::ZapReopenText, "fr", "La table est fermée. Rouvrez-la avec : USE {stem}" },
        { MessageId::ZapReopenText, "de", "Die Tabelle ist geschlossen. Erneut öffnen mit: USE {stem}" },
        { MessageId::ZapReopenText, "it", "La tabella è chiusa. Riaprirla con: USE {stem}" },
        { MessageId::ZapRebuildIndexesText, "en-US", "Rebuild/rebind indexes as needed." },
        { MessageId::ZapRebuildIndexesText, "es", "Reconstruya/revincule los índices según sea necesario." },
        { MessageId::ZapRebuildIndexesText, "fr", "Reconstruisez/reliez les index selon les besoins." },
        { MessageId::ZapRebuildIndexesText, "de", "Indizes nach Bedarf neu erstellen/neu binden." },
        { MessageId::ZapRebuildIndexesText, "it", "Ricostruire/ricollegare gli indici secondo necessità." },
        { MessageId::PackUsageText, "en-US", "Usage:\n  PACK USAGE\n  PACK\nExamples:\n  PACK\nNotes:\n  - PACK USAGE does not require an open table and does not rewrite files.\n  - PACK physically removes deleted records from the current DBF.\n  - PACK closes the table on success; reopen with USE <table>.\n  - PACK supports x64 M(8) memo tables by rebuilding DBF and DTX together.\n  - Legacy memo tables are refused.\n  - Index containers must be rebuilt/rebound after PACK." },
        { MessageId::PackUsageText, "es", "Uso:\n  PACK USAGE\n  PACK\nEjemplos:\n  PACK\nNotas:\n  - PACK USAGE no requiere una tabla abierta y no reescribe archivos.\n  - PACK elimina físicamente los registros borrados del DBF actual.\n  - PACK cierra la tabla si tiene éxito; reábrala con USE <table>.\n  - PACK admite tablas memo x64 M(8) reconstruyendo DBF y DTX juntos.\n  - Las tablas memo heredadas se rechazan.\n  - Los contenedores de índice deben reconstruirse/revincularse tras PACK." },
        { MessageId::PackUsageText, "fr", "Utilisation :\n  PACK USAGE\n  PACK\nExemples :\n  PACK\nRemarques :\n  - PACK USAGE ne nécessite pas de table ouverte et ne réécrit aucun fichier.\n  - PACK supprime physiquement les enregistrements supprimés du DBF actuel.\n  - PACK ferme la table en cas de succès ; rouvrez avec USE <table>.\n  - PACK prend en charge les tables mémo x64 M(8) en reconstruisant DBF et DTX ensemble.\n  - Les tables mémo héritées sont refusées.\n  - Les conteneurs d'index doivent être reconstruits/reliés après PACK." },
        { MessageId::PackUsageText, "de", "Verwendung:\n  PACK USAGE\n  PACK\nBeispiele:\n  PACK\nHinweise:\n  - PACK USAGE erfordert keine geöffnete Tabelle und schreibt keine Dateien neu.\n  - PACK entfernt gelöschte Datensätze physisch aus der aktuellen DBF.\n  - PACK schließt die Tabelle bei Erfolg; erneut öffnen mit USE <table>.\n  - PACK unterstützt x64-M(8)-Memotabellen durch gemeinsames Neuaufbauen von DBF und DTX.\n  - Ältere Memotabellen werden abgelehnt.\n  - Indexcontainer müssen nach PACK neu aufgebaut/neu gebunden werden." },
        { MessageId::PackUsageText, "it", "Uso:\n  PACK USAGE\n  PACK\nEsempi:\n  PACK\nNote:\n  - PACK USAGE non richiede una tabella aperta e non riscrive file.\n  - PACK rimuove fisicamente i record eliminati dal DBF corrente.\n  - PACK chiude la tabella in caso di successo; riaprire con USE <table>.\n  - PACK supporta le tabelle memo x64 M(8) ricostruendo insieme DBF e DTX.\n  - Le tabelle memo legacy vengono rifiutate.\n  - I contenitori di indice devono essere ricostruiti/ricollegati dopo PACK." },
        { MessageId::PackNoTableOpenText, "en-US", "No table open" },
        { MessageId::PackNoTableOpenText, "es", "No hay tabla abierta" },
        { MessageId::PackNoTableOpenText, "fr", "Aucune table ouverte" },
        { MessageId::PackNoTableOpenText, "de", "Keine Tabelle geöffnet" },
        { MessageId::PackNoTableOpenText, "it", "Nessuna tabella aperta" },
        { MessageId::PackMemoNotSupportedText, "en-US", "Memo tables not supported yet (legacy memo block remapping missing)." },
        { MessageId::PackMemoNotSupportedText, "es", "Tablas memo aún no admitidas (falta el remapeo de bloques memo heredados)." },
        { MessageId::PackMemoNotSupportedText, "fr", "Tables mémo pas encore prises en charge (remappage des blocs mémo hérités manquant)." },
        { MessageId::PackMemoNotSupportedText, "de", "Memotabellen noch nicht unterstützt (Neuzuordnung älterer Memoblöcke fehlt)." },
        { MessageId::PackMemoNotSupportedText, "it", "Tabelle memo non ancora supportate (manca il rimappamento dei blocchi memo legacy)." },
        { MessageId::PackFileNotFoundText, "en-US", "File not found on disk: {path}" },
        { MessageId::PackFileNotFoundText, "es", "Archivo no encontrado en disco: {path}" },
        { MessageId::PackFileNotFoundText, "fr", "Fichier introuvable sur le disque : {path}" },
        { MessageId::PackFileNotFoundText, "de", "Datei nicht auf dem Datenträger gefunden: {path}" },
        { MessageId::PackFileNotFoundText, "it", "File non trovato sul disco: {path}" },
        { MessageId::PackDetailText, "en-US", "{detail}" },
        { MessageId::PackDetailText, "es", "{detail}" },
        { MessageId::PackDetailText, "fr", "{detail}" },
        { MessageId::PackDetailText, "de", "{detail}" },
        { MessageId::PackDetailText, "it", "{detail}" },
        { MessageId::PackAbortedText, "en-US", "operation aborted. Table remains closed." },
        { MessageId::PackAbortedText, "es", "operación cancelada. La tabla permanece cerrada." },
        { MessageId::PackAbortedText, "fr", "opération annulée. La table reste fermée." },
        { MessageId::PackAbortedText, "de", "Vorgang abgebrochen. Tabelle bleibt geschlossen." },
        { MessageId::PackAbortedText, "it", "operazione annullata. La tabella resta chiusa." },
        { MessageId::PackCannotOpenReadText, "en-US", "Cannot open original file for reading" },
        { MessageId::PackCannotOpenReadText, "es", "No se puede abrir el archivo original para lectura" },
        { MessageId::PackCannotOpenReadText, "fr", "Impossible d'ouvrir le fichier original en lecture" },
        { MessageId::PackCannotOpenReadText, "de", "Originaldatei kann nicht zum Lesen geöffnet werden" },
        { MessageId::PackCannotOpenReadText, "it", "Impossibile aprire il file originale in lettura" },
        { MessageId::PackFailedRead32Text, "en-US", "Failed to read first 32 bytes of header" },
        { MessageId::PackFailedRead32Text, "es", "No se pudieron leer los primeros 32 bytes del encabezado" },
        { MessageId::PackFailedRead32Text, "fr", "Échec de lecture des 32 premiers octets de l'en-tête" },
        { MessageId::PackFailedRead32Text, "de", "Die ersten 32 Bytes des Headers konnten nicht gelesen werden" },
        { MessageId::PackFailedRead32Text, "it", "Impossibile leggere i primi 32 byte dell'intestazione" },
        { MessageId::PackInvalidHeaderText, "en-US", "Invalid DBF header (headerLen={hl}, recordLen={rl})" },
        { MessageId::PackInvalidHeaderText, "es", "Encabezado DBF no válido (headerLen={hl}, recordLen={rl})" },
        { MessageId::PackInvalidHeaderText, "fr", "En-tête DBF non valide (headerLen={hl}, recordLen={rl})" },
        { MessageId::PackInvalidHeaderText, "de", "Ungültiger DBF-Header (headerLen={hl}, recordLen={rl})" },
        { MessageId::PackInvalidHeaderText, "it", "Intestazione DBF non valida (headerLen={hl}, recordLen={rl})" },
        { MessageId::PackFailedReadHeaderBlockText, "en-US", "Failed to read full header block" },
        { MessageId::PackFailedReadHeaderBlockText, "es", "No se pudo leer el bloque de encabezado completo" },
        { MessageId::PackFailedReadHeaderBlockText, "fr", "Échec de lecture du bloc d'en-tête complet" },
        { MessageId::PackFailedReadHeaderBlockText, "de", "Vollständiger Headerblock konnte nicht gelesen werden" },
        { MessageId::PackFailedReadHeaderBlockText, "it", "Impossibile leggere il blocco di intestazione completo" },
        { MessageId::PackHeaderNoTerminatorText, "en-US", "header does not end with 0x0D terminator byte" },
        { MessageId::PackHeaderNoTerminatorText, "es", "el encabezado no termina con el byte terminador 0x0D" },
        { MessageId::PackHeaderNoTerminatorText, "fr", "l'en-tête ne se termine pas par l'octet terminateur 0x0D" },
        { MessageId::PackHeaderNoTerminatorText, "de", "Header endet nicht mit dem Abschlussbyte 0x0D" },
        { MessageId::PackHeaderNoTerminatorText, "it", "l'intestazione non termina con il byte terminatore 0x0D" },
        { MessageId::PackHeaderCountMismatchText, "en-US", "Warning — header record count ({orig}) does not match physical record count ({actual}); using safe count {safe}." },
        { MessageId::PackHeaderCountMismatchText, "es", "Advertencia — el recuento de registros del encabezado ({orig}) no coincide con el recuento físico ({actual}); usando recuento seguro {safe}." },
        { MessageId::PackHeaderCountMismatchText, "fr", "Avertissement — le nombre d'enregistrements de l'en-tête ({orig}) ne correspond pas au nombre physique ({actual}) ; utilisation du nombre sûr {safe}." },
        { MessageId::PackHeaderCountMismatchText, "de", "Warnung — Datensatzanzahl im Header ({orig}) stimmt nicht mit der physischen Anzahl ({actual}) überein; sichere Anzahl {safe} wird verwendet." },
        { MessageId::PackHeaderCountMismatchText, "it", "Avviso — il conteggio dei record dell'intestazione ({orig}) non corrisponde al conteggio fisico ({actual}); si usa il conteggio sicuro {safe}." },
        { MessageId::PackCannotCreateTempText, "en-US", "Cannot create temporary file: {path}" },
        { MessageId::PackCannotCreateTempText, "es", "No se puede crear el archivo temporal: {path}" },
        { MessageId::PackCannotCreateTempText, "fr", "Impossible de créer le fichier temporaire : {path}" },
        { MessageId::PackCannotCreateTempText, "de", "Temporäre Datei kann nicht erstellt werden: {path}" },
        { MessageId::PackCannotCreateTempText, "it", "Impossibile creare il file temporaneo: {path}" },
        { MessageId::PackFailedWriteInitialHeaderText, "en-US", "Failed to write initial header" },
        { MessageId::PackFailedWriteInitialHeaderText, "es", "No se pudo escribir el encabezado inicial" },
        { MessageId::PackFailedWriteInitialHeaderText, "fr", "Échec d'écriture de l'en-tête initial" },
        { MessageId::PackFailedWriteInitialHeaderText, "de", "Anfänglicher Header konnte nicht geschrieben werden" },
        { MessageId::PackFailedWriteInitialHeaderText, "it", "Impossibile scrivere l'intestazione iniziale" },
        { MessageId::PackCannotReopenText, "en-US", "Cannot reopen original file for record copy" },
        { MessageId::PackCannotReopenText, "es", "No se puede reabrir el archivo original para copiar registros" },
        { MessageId::PackCannotReopenText, "fr", "Impossible de rouvrir le fichier original pour la copie des enregistrements" },
        { MessageId::PackCannotReopenText, "de", "Originaldatei kann nicht zum Kopieren der Datensätze erneut geöffnet werden" },
        { MessageId::PackCannotReopenText, "it", "Impossibile riaprire il file originale per la copia dei record" },
        { MessageId::PackFailedReadRecordsText, "en-US", "Failed while reading source records" },
        { MessageId::PackFailedReadRecordsText, "es", "Error al leer los registros de origen" },
        { MessageId::PackFailedReadRecordsText, "fr", "Échec lors de la lecture des enregistrements source" },
        { MessageId::PackFailedReadRecordsText, "de", "Fehler beim Lesen der Quelldatensätze" },
        { MessageId::PackFailedReadRecordsText, "it", "Errore durante la lettura dei record di origine" },
        { MessageId::PackFailedWriteRecordsText, "en-US", "Failed while writing packed records" },
        { MessageId::PackFailedWriteRecordsText, "es", "Error al escribir los registros compactados" },
        { MessageId::PackFailedWriteRecordsText, "fr", "Échec lors de l'écriture des enregistrements compactés" },
        { MessageId::PackFailedWriteRecordsText, "de", "Fehler beim Schreiben der gepackten Datensätze" },
        { MessageId::PackFailedWriteRecordsText, "it", "Errore durante la scrittura dei record compattati" },
        { MessageId::PackFailedWriteEofText, "en-US", "Failed writing EOF marker" },
        { MessageId::PackFailedWriteEofText, "es", "Error al escribir el marcador EOF" },
        { MessageId::PackFailedWriteEofText, "fr", "Échec d'écriture du marqueur EOF" },
        { MessageId::PackFailedWriteEofText, "de", "Fehler beim Schreiben der EOF-Markierung" },
        { MessageId::PackFailedWriteEofText, "it", "Errore durante la scrittura del marcatore EOF" },
        { MessageId::PackFailedRewriteHeaderText, "en-US", "Failed rewriting final header" },
        { MessageId::PackFailedRewriteHeaderText, "es", "Error al reescribir el encabezado final" },
        { MessageId::PackFailedRewriteHeaderText, "fr", "Échec de réécriture de l'en-tête final" },
        { MessageId::PackFailedRewriteHeaderText, "de", "Fehler beim Neuschreiben des finalen Headers" },
        { MessageId::PackFailedRewriteHeaderText, "it", "Errore durante la riscrittura dell'intestazione finale" },
        { MessageId::PackMemoNotFoundText, "en-US", "warning — memo object {id} not found, clearing reference" },
        { MessageId::PackMemoNotFoundText, "es", "advertencia — objeto memo {id} no encontrado, borrando referencia" },
        { MessageId::PackMemoNotFoundText, "fr", "avertissement — objet mémo {id} introuvable, effacement de la référence" },
        { MessageId::PackMemoNotFoundText, "de", "Warnung — Memoobjekt {id} nicht gefunden, Referenz wird gelöscht" },
        { MessageId::PackMemoNotFoundText, "it", "avviso — oggetto memo {id} non trovato, riferimento cancellato" },
        { MessageId::PackFailedRenameBackupText, "en-US", "Failed to rename original to backup: {detail}" },
        { MessageId::PackFailedRenameBackupText, "es", "No se pudo renombrar el original a copia de seguridad: {detail}" },
        { MessageId::PackFailedRenameBackupText, "fr", "Échec du renommage de l'original en sauvegarde : {detail}" },
        { MessageId::PackFailedRenameBackupText, "de", "Original konnte nicht in Sicherung umbenannt werden: {detail}" },
        { MessageId::PackFailedRenameBackupText, "it", "Impossibile rinominare l'originale in backup: {detail}" },
        { MessageId::PackFailedReplaceText, "en-US", "Failed to replace original with packed file: {detail}" },
        { MessageId::PackFailedReplaceText, "es", "No se pudo reemplazar el original con el archivo compactado: {detail}" },
        { MessageId::PackFailedReplaceText, "fr", "Échec du remplacement de l'original par le fichier compacté : {detail}" },
        { MessageId::PackFailedReplaceText, "de", "Original konnte nicht durch die gepackte Datei ersetzt werden: {detail}" },
        { MessageId::PackFailedReplaceText, "it", "Impossibile sostituire l'originale con il file compattato: {detail}" },
        { MessageId::PackRollbackFailedText, "en-US", "  Rollback also failed: {detail} — manual recovery may be needed!" },
        { MessageId::PackRollbackFailedText, "es", "  La reversión también falló: {detail} — ¡puede ser necesaria una recuperación manual!" },
        { MessageId::PackRollbackFailedText, "fr", "  La restauration a également échoué : {detail} — une récupération manuelle peut être nécessaire !" },
        { MessageId::PackRollbackFailedText, "de", "  Rollback ist ebenfalls fehlgeschlagen: {detail} — manuelle Wiederherstellung könnte nötig sein!" },
        { MessageId::PackRollbackFailedText, "it", "  Anche il rollback è fallito: {detail} — potrebbe essere necessario un ripristino manuale!" },
        { MessageId::PackOriginalRestoredText, "en-US", "  Original file restored." },
        { MessageId::PackOriginalRestoredText, "es", "  Archivo original restaurado." },
        { MessageId::PackOriginalRestoredText, "fr", "  Fichier original restauré." },
        { MessageId::PackOriginalRestoredText, "de", "  Originaldatei wiederhergestellt." },
        { MessageId::PackOriginalRestoredText, "it", "  File originale ripristinato." },
        { MessageId::PackFailedRenameDbfBackupText, "en-US", "Failed to rename original DBF to backup: {detail}" },
        { MessageId::PackFailedRenameDbfBackupText, "es", "No se pudo renombrar el DBF original a copia de seguridad: {detail}" },
        { MessageId::PackFailedRenameDbfBackupText, "fr", "Échec du renommage du DBF original en sauvegarde : {detail}" },
        { MessageId::PackFailedRenameDbfBackupText, "de", "Original-DBF konnte nicht in Sicherung umbenannt werden: {detail}" },
        { MessageId::PackFailedRenameDbfBackupText, "it", "Impossibile rinominare il DBF originale in backup: {detail}" },
        { MessageId::PackFailedRenameDtxBackupText, "en-US", "Failed to rename original DTX to backup: {detail}" },
        { MessageId::PackFailedRenameDtxBackupText, "es", "No se pudo renombrar el DTX original a copia de seguridad: {detail}" },
        { MessageId::PackFailedRenameDtxBackupText, "fr", "Échec du renommage du DTX original en sauvegarde : {detail}" },
        { MessageId::PackFailedRenameDtxBackupText, "de", "Original-DTX konnte nicht in Sicherung umbenannt werden: {detail}" },
        { MessageId::PackFailedRenameDtxBackupText, "it", "Impossibile rinominare il DTX originale in backup: {detail}" },
        { MessageId::PackFailedReplaceDbfText, "en-US", "Failed to replace DBF with packed DBF: {detail}" },
        { MessageId::PackFailedReplaceDbfText, "es", "No se pudo reemplazar el DBF con el DBF compactado: {detail}" },
        { MessageId::PackFailedReplaceDbfText, "fr", "Échec du remplacement du DBF par le DBF compacté : {detail}" },
        { MessageId::PackFailedReplaceDbfText, "de", "DBF konnte nicht durch gepackte DBF ersetzt werden: {detail}" },
        { MessageId::PackFailedReplaceDbfText, "it", "Impossibile sostituire il DBF con il DBF compattato: {detail}" },
        { MessageId::PackFailedReplaceDtxText, "en-US", "Failed to replace DTX with packed DTX: {detail}" },
        { MessageId::PackFailedReplaceDtxText, "es", "No se pudo reemplazar el DTX con el DTX compactado: {detail}" },
        { MessageId::PackFailedReplaceDtxText, "fr", "Échec du remplacement du DTX par le DTX compacté : {detail}" },
        { MessageId::PackFailedReplaceDtxText, "de", "DTX konnte nicht durch gepackte DTX ersetzt werden: {detail}" },
        { MessageId::PackFailedReplaceDtxText, "it", "Impossibile sostituire il DTX con il DTX compattato: {detail}" },
        { MessageId::PackCnxMarkedDirtyText, "en-US", "CNX marked dirty (reindex recommended): {file}" },
        { MessageId::PackCnxMarkedDirtyText, "es", "CNX marcado como sucio (se recomienda reindexar): {file}" },
        { MessageId::PackCnxMarkedDirtyText, "fr", "CNX marqué comme modifié (réindexation recommandée) : {file}" },
        { MessageId::PackCnxMarkedDirtyText, "de", "CNX als geändert markiert (Neuindizierung empfohlen): {file}" },
        { MessageId::PackCnxMarkedDirtyText, "it", "CNX contrassegnato come modificato (reindicizzazione consigliata): {file}" },
        { MessageId::PackCnxCouldNotMarkText, "en-US", "note: CNX found but could not mark dirty" },
        { MessageId::PackCnxCouldNotMarkText, "es", "nota: se encontró CNX pero no se pudo marcar como sucio" },
        { MessageId::PackCnxCouldNotMarkText, "fr", "remarque : CNX trouvé mais impossible de le marquer comme modifié" },
        { MessageId::PackCnxCouldNotMarkText, "de", "Hinweis: CNX gefunden, konnte aber nicht als geändert markiert werden" },
        { MessageId::PackCnxCouldNotMarkText, "it", "nota: CNX trovato ma impossibile contrassegnarlo come modificato" },
        { MessageId::PackIndexRebuildText, "en-US", "note: index container should be rebuilt: {file}" },
        { MessageId::PackIndexRebuildText, "es", "nota: el contenedor de índice debe reconstruirse: {file}" },
        { MessageId::PackIndexRebuildText, "fr", "remarque : le conteneur d'index doit être reconstruit : {file}" },
        { MessageId::PackIndexRebuildText, "de", "Hinweis: Indexcontainer sollte neu aufgebaut werden: {file}" },
        { MessageId::PackIndexRebuildText, "it", "nota: il contenitore di indice deve essere ricostruito: {file}" },
        { MessageId::PackOrderRebuildText, "en-US", "note: order container should be rebuilt: {file}" },
        { MessageId::PackOrderRebuildText, "es", "nota: el contenedor de orden debe reconstruirse: {file}" },
        { MessageId::PackOrderRebuildText, "fr", "remarque : le conteneur d'ordre doit être reconstruit : {file}" },
        { MessageId::PackOrderRebuildText, "de", "Hinweis: Ordnungscontainer sollte neu aufgebaut werden: {file}" },
        { MessageId::PackOrderRebuildText, "it", "nota: il contenitore di ordine deve essere ricostruito: {file}" },
        { MessageId::PackCompleteText, "en-US", "PACK complete. Kept {kept} record(s), removed {deleted} deleted record(s)." },
        { MessageId::PackCompleteText, "es", "PACK completado. Se conservaron {kept} registro(s), se eliminaron {deleted} registro(s) borrado(s)." },
        { MessageId::PackCompleteText, "fr", "PACK terminé. {kept} enregistrement(s) conservé(s), {deleted} enregistrement(s) supprimé(s) retiré(s)." },
        { MessageId::PackCompleteText, "de", "PACK abgeschlossen. {kept} Datensätze behalten, {deleted} gelöschte Datensätze entfernt." },
        { MessageId::PackCompleteText, "it", "PACK completato. Conservati {kept} record, rimossi {deleted} record eliminati." },
        { MessageId::PackReadyForUseText, "en-US", "{file} ready for use." },
        { MessageId::PackReadyForUseText, "es", "{file} listo para usar." },
        { MessageId::PackReadyForUseText, "fr", "{file} prêt à l'emploi." },
        { MessageId::PackReadyForUseText, "de", "{file} einsatzbereit." },
        { MessageId::PackReadyForUseText, "it", "{file} pronto all'uso." },
        { MessageId::PackSidecarsRebuiltText, "en-US", "Sidecar(s): DBF and DTX rebuilt and synchronized." },
        { MessageId::PackSidecarsRebuiltText, "es", "Archivo(s) complementario(s): DBF y DTX reconstruidos y sincronizados." },
        { MessageId::PackSidecarsRebuiltText, "fr", "Fichier(s) annexe(s) : DBF et DTX reconstruits et synchronisés." },
        { MessageId::PackSidecarsRebuiltText, "de", "Begleitdatei(en): DBF und DTX neu aufgebaut und synchronisiert." },
        { MessageId::PackSidecarsRebuiltText, "it", "File collaterali: DBF e DTX ricostruiti e sincronizzati." },
        { MessageId::PackSidecarsNoneText, "en-US", "Sidecar(s): none." },
        { MessageId::PackSidecarsNoneText, "es", "Archivo(s) complementario(s): ninguno." },
        { MessageId::PackSidecarsNoneText, "fr", "Fichier(s) annexe(s) : aucun." },
        { MessageId::PackSidecarsNoneText, "de", "Begleitdatei(en): keine." },
        { MessageId::PackSidecarsNoneText, "it", "File collaterali: nessuno." },
        { MessageId::PackReopenText, "en-US", "Table is closed. Reopen with: USE {stem}" },
        { MessageId::PackReopenText, "es", "La tabla está cerrada. Reábrala con: USE {stem}" },
        { MessageId::PackReopenText, "fr", "La table est fermée. Rouvrez avec : USE {stem}" },
        { MessageId::PackReopenText, "de", "Tabelle ist geschlossen. Erneut öffnen mit: USE {stem}" },
        { MessageId::PackReopenText, "it", "La tabella è chiusa. Riaprire con: USE {stem}" },
        { MessageId::PackRebuildIndexesText, "en-US", "Rebuild/rebind indexes as needed." },
        { MessageId::PackRebuildIndexesText, "es", "Reconstruya/revincule los índices según sea necesario." },
        { MessageId::PackRebuildIndexesText, "fr", "Reconstruisez/reliez les index selon les besoins." },
        { MessageId::PackRebuildIndexesText, "de", "Indizes nach Bedarf neu aufbauen/neu binden." },
        { MessageId::PackRebuildIndexesText, "it", "Ricostruire/ricollegare gli indici secondo necessità." },
        { MessageId::CopyUsageText, "en-US", "Usage:\n  COPY USAGE\n  COPY TO <DBFNAME> [WITH SIDECARS] [OVERWRITE]\n  COPY TO <DBFNAME> AS <MSDOS|DBASE|FOX26|FOXPRO|VFP|X64> [OVERWRITE]\n  COPY TO <DBFNAME> AS X64 VECTOR [OVERWRITE]\n  COPY FILE <SRC> TO <DST> [OVERWRITE]\n\nExamples:\n  COPY TO students_copy\n  COPY TO students_x64 AS X64 VECTOR OVERWRITE\n  COPY TO students_vfp AS VFP\n  COPY TO students_backup WITH SIDECARS OVERWRITE\n  COPY FILE source.txt TO tmp\\source_copy.txt OVERWRITE\n\nNotes:\n  - COPY USAGE prints usage and does not require an open table.\n  - COPY TO <name>                 : binary copy of the current DBF\n  - COPY TO <name> AS <flavor>     : logical table copy/conversion\n  - COPY TO <name> AS X64 VECTOR   : one-step copy from any open table to x64 vector form\n  - VECTOR is target-driven and is valid only with AS X64\n  - AS X64 controls output format only; the destination path is honored\n  - AS VFP/FOX/MSDOS writes free-table 10-byte descriptor field names\n  - COPY AS free-table fails if 10-byte descriptor names would collide\n  - WITH SIDECARS applies to binary COPY TO only\n  - OVERWRITE is required when the destination already exists\n  - x64 output still writes .dbf for now (no .dbfx yet)\n\nSIDECARS (if present next to the DBF): .inx .cnx .dtx .dti.json" },
        { MessageId::CopyUsageText, "es", "Uso:\n  COPY USAGE\n  COPY TO <DBFNAME> [WITH SIDECARS] [OVERWRITE]\n  COPY TO <DBFNAME> AS <MSDOS|DBASE|FOX26|FOXPRO|VFP|X64> [OVERWRITE]\n  COPY TO <DBFNAME> AS X64 VECTOR [OVERWRITE]\n  COPY FILE <SRC> TO <DST> [OVERWRITE]\n\nEjemplos:\n  COPY TO students_copy\n  COPY TO students_x64 AS X64 VECTOR OVERWRITE\n  COPY TO students_vfp AS VFP\n  COPY TO students_backup WITH SIDECARS OVERWRITE\n  COPY FILE source.txt TO tmp\\source_copy.txt OVERWRITE\n\nNotas:\n  - COPY USAGE imprime el uso y no requiere una tabla abierta.\n  - COPY TO <name>                 : copia binaria del DBF actual\n  - COPY TO <name> AS <flavor>     : copia/conversión lógica de la tabla\n  - COPY TO <name> AS X64 VECTOR   : copia en un paso desde cualquier tabla abierta a forma vectorial x64\n  - VECTOR está determinado por el destino y solo es válido con AS X64\n  - AS X64 controla solo el formato de salida; se respeta la ruta de destino\n  - AS VFP/FOX/MSDOS escribe nombres de campo con descriptor de 10 bytes de tabla libre\n  - COPY AS de tabla libre falla si los nombres de descriptor de 10 bytes colisionaran\n  - WITH SIDECARS se aplica solo a COPY TO binario\n  - OVERWRITE es obligatorio cuando el destino ya existe\n  - la salida x64 aún escribe .dbf por ahora (todavía sin .dbfx)\n\nARCHIVOS COMPLEMENTARIOS (si están junto al DBF): .inx .cnx .dtx .dti.json" },
        { MessageId::CopyUsageText, "fr", "Utilisation :\n  COPY USAGE\n  COPY TO <DBFNAME> [WITH SIDECARS] [OVERWRITE]\n  COPY TO <DBFNAME> AS <MSDOS|DBASE|FOX26|FOXPRO|VFP|X64> [OVERWRITE]\n  COPY TO <DBFNAME> AS X64 VECTOR [OVERWRITE]\n  COPY FILE <SRC> TO <DST> [OVERWRITE]\n\nExemples :\n  COPY TO students_copy\n  COPY TO students_x64 AS X64 VECTOR OVERWRITE\n  COPY TO students_vfp AS VFP\n  COPY TO students_backup WITH SIDECARS OVERWRITE\n  COPY FILE source.txt TO tmp\\source_copy.txt OVERWRITE\n\nRemarques :\n  - COPY USAGE affiche l'utilisation et ne nécessite pas de table ouverte.\n  - COPY TO <name>                 : copie binaire du DBF actuel\n  - COPY TO <name> AS <flavor>     : copie/conversion logique de la table\n  - COPY TO <name> AS X64 VECTOR   : copie en une étape de toute table ouverte vers la forme vectorielle x64\n  - VECTOR est déterminé par la cible et n'est valide qu'avec AS X64\n  - AS X64 contrôle uniquement le format de sortie ; le chemin de destination est respecté\n  - AS VFP/FOX/MSDOS écrit des noms de champ à descripteur de 10 octets de table libre\n  - COPY AS table libre échoue si les noms de descripteur de 10 octets entrent en collision\n  - WITH SIDECARS s'applique uniquement à COPY TO binaire\n  - OVERWRITE est requis lorsque la destination existe déjà\n  - la sortie x64 écrit encore .dbf pour l'instant (pas encore de .dbfx)\n\nFICHIERS ANNEXES (s'ils sont présents à côté du DBF) : .inx .cnx .dtx .dti.json" },
        { MessageId::CopyUsageText, "de", "Verwendung:\n  COPY USAGE\n  COPY TO <DBFNAME> [WITH SIDECARS] [OVERWRITE]\n  COPY TO <DBFNAME> AS <MSDOS|DBASE|FOX26|FOXPRO|VFP|X64> [OVERWRITE]\n  COPY TO <DBFNAME> AS X64 VECTOR [OVERWRITE]\n  COPY FILE <SRC> TO <DST> [OVERWRITE]\n\nBeispiele:\n  COPY TO students_copy\n  COPY TO students_x64 AS X64 VECTOR OVERWRITE\n  COPY TO students_vfp AS VFP\n  COPY TO students_backup WITH SIDECARS OVERWRITE\n  COPY FILE source.txt TO tmp\\source_copy.txt OVERWRITE\n\nHinweise:\n  - COPY USAGE gibt die Verwendung aus und erfordert keine geöffnete Tabelle.\n  - COPY TO <name>                 : binäre Kopie der aktuellen DBF\n  - COPY TO <name> AS <flavor>     : logische Tabellenkopie/-konvertierung\n  - COPY TO <name> AS X64 VECTOR   : einstufige Kopie einer beliebigen geöffneten Tabelle in die x64-Vektorform\n  - VECTOR wird vom Ziel bestimmt und ist nur mit AS X64 gültig\n  - AS X64 steuert nur das Ausgabeformat; der Zielpfad wird beachtet\n  - AS VFP/FOX/MSDOS schreibt Feldnamen mit 10-Byte-Deskriptor für freie Tabellen\n  - COPY AS für freie Tabellen schlägt fehl, wenn 10-Byte-Deskriptornamen kollidieren würden\n  - WITH SIDECARS gilt nur für binäres COPY TO\n  - OVERWRITE ist erforderlich, wenn das Ziel bereits existiert\n  - x64-Ausgabe schreibt vorerst weiterhin .dbf (noch kein .dbfx)\n\nBEGLEITDATEIEN (falls neben der DBF vorhanden): .inx .cnx .dtx .dti.json" },
        { MessageId::CopyUsageText, "it", "Uso:\n  COPY USAGE\n  COPY TO <DBFNAME> [WITH SIDECARS] [OVERWRITE]\n  COPY TO <DBFNAME> AS <MSDOS|DBASE|FOX26|FOXPRO|VFP|X64> [OVERWRITE]\n  COPY TO <DBFNAME> AS X64 VECTOR [OVERWRITE]\n  COPY FILE <SRC> TO <DST> [OVERWRITE]\n\nEsempi:\n  COPY TO students_copy\n  COPY TO students_x64 AS X64 VECTOR OVERWRITE\n  COPY TO students_vfp AS VFP\n  COPY TO students_backup WITH SIDECARS OVERWRITE\n  COPY FILE source.txt TO tmp\\source_copy.txt OVERWRITE\n\nNote:\n  - COPY USAGE stampa l'uso e non richiede una tabella aperta.\n  - COPY TO <name>                 : copia binaria del DBF corrente\n  - COPY TO <name> AS <flavor>     : copia/conversione logica della tabella\n  - COPY TO <name> AS X64 VECTOR   : copia in un passaggio da qualsiasi tabella aperta alla forma vettoriale x64\n  - VECTOR è determinato dalla destinazione ed è valido solo con AS X64\n  - AS X64 controlla solo il formato di output; il percorso di destinazione viene rispettato\n  - AS VFP/FOX/MSDOS scrive nomi di campo con descrittore a 10 byte per tabelle libere\n  - COPY AS per tabelle libere fallisce se i nomi del descrittore a 10 byte collidono\n  - WITH SIDECARS si applica solo a COPY TO binario\n  - OVERWRITE è obbligatorio quando la destinazione esiste già\n  - l'output x64 scrive ancora .dbf per ora (ancora nessun .dbfx)\n\nFILE COLLATERALI (se presenti accanto al DBF): .inx .cnx .dtx .dti.json" },
        { MessageId::CopySidecarFailedText, "en-US", "COPY SIDECAR failed: {detail}" },
        { MessageId::CopySidecarFailedText, "es", "COPY SIDECAR falló: {detail}" },
        { MessageId::CopySidecarFailedText, "fr", "COPY SIDECAR a échoué : {detail}" },
        { MessageId::CopySidecarFailedText, "de", "COPY SIDECAR fehlgeschlagen: {detail}" },
        { MessageId::CopySidecarFailedText, "it", "COPY SIDECAR non riuscito: {detail}" },
        { MessageId::CopySidecarsNoneText, "en-US", "COPY SIDECARS: none found." },
        { MessageId::CopySidecarsNoneText, "es", "COPY SIDECARS: no se encontró ninguno." },
        { MessageId::CopySidecarsNoneText, "fr", "COPY SIDECARS : aucun trouvé." },
        { MessageId::CopySidecarsNoneText, "de", "COPY SIDECARS: keine gefunden." },
        { MessageId::CopySidecarsNoneText, "it", "COPY SIDECARS: nessuno trovato." },
        { MessageId::CopySidecarsFoundText, "en-US", "COPY SIDECARS: found {found}, copied {copied}{failed}." },
        { MessageId::CopySidecarsFoundText, "es", "COPY SIDECARS: encontrados {found}, copiados {copied}{failed}." },
        { MessageId::CopySidecarsFoundText, "fr", "COPY SIDECARS : {found} trouvé(s), {copied} copié(s){failed}." },
        { MessageId::CopySidecarsFoundText, "de", "COPY SIDECARS: {found} gefunden, {copied} kopiert{failed}." },
        { MessageId::CopySidecarsFoundText, "it", "COPY SIDECARS: trovati {found}, copiati {copied}{failed}." },
        { MessageId::CopyWarningDetailText, "en-US", "{detail}" },
        { MessageId::CopyWarningDetailText, "es", "{detail}" },
        { MessageId::CopyWarningDetailText, "fr", "{detail}" },
        { MessageId::CopyWarningDetailText, "de", "{detail}" },
        { MessageId::CopyWarningDetailText, "it", "{detail}" },
        { MessageId::CopyDetailText, "en-US", "{detail}" },
        { MessageId::CopyDetailText, "es", "{detail}" },
        { MessageId::CopyDetailText, "fr", "{detail}" },
        { MessageId::CopyDetailText, "de", "{detail}" },
        { MessageId::CopyDetailText, "it", "{detail}" },
        { MessageId::CopiedFileText, "en-US", "Copied file to {dst}" },
        { MessageId::CopyFileFailedText, "en-US", "COPY FILE failed: {detail}" },
        { MessageId::CopyFileFailedText, "es", "COPY FILE falló: {detail}" },
        { MessageId::CopyFileFailedText, "fr", "COPY FILE a échoué : {detail}" },
        { MessageId::CopyFileFailedText, "de", "COPY FILE fehlgeschlagen: {detail}" },
        { MessageId::CopyFileFailedText, "it", "COPY FILE non riuscito: {detail}" },
        { MessageId::CopyToNoFileOpenText, "en-US", "COPY TO: no file open." },
        { MessageId::CopyToNoFileOpenText, "es", "COPY TO: no hay archivo abierto." },
        { MessageId::CopyToNoFileOpenText, "fr", "COPY TO : aucun fichier ouvert." },
        { MessageId::CopyToNoFileOpenText, "de", "COPY TO: keine Datei geöffnet." },
        { MessageId::CopyToNoFileOpenText, "it", "COPY TO: nessun file aperto." },
        { MessageId::CopyAsUnexpectedTokenText, "en-US", "COPY TO AS failed: unexpected token between destination and AS: '{token}'" },
        { MessageId::CopyAsUnexpectedTokenText, "es", "COPY TO AS falló: token inesperado entre el destino y AS: '{token}'" },
        { MessageId::CopyAsUnexpectedTokenText, "fr", "COPY TO AS a échoué : jeton inattendu entre la destination et AS : '{token}'" },
        { MessageId::CopyAsUnexpectedTokenText, "de", "COPY TO AS fehlgeschlagen: unerwartetes Token zwischen Ziel und AS: '{token}'" },
        { MessageId::CopyAsUnexpectedTokenText, "it", "COPY TO AS non riuscito: token imprevisto tra la destinazione e AS: '{token}'" },
        { MessageId::CopyAsUseHintText, "en-US", "Use: COPY TO <destination> AS <flavor> [VECTOR] [OVERWRITE]" },
        { MessageId::CopyAsUseHintText, "es", "Use: COPY TO <destination> AS <flavor> [VECTOR] [OVERWRITE]" },
        { MessageId::CopyAsUseHintText, "fr", "Utilisez : COPY TO <destination> AS <flavor> [VECTOR] [OVERWRITE]" },
        { MessageId::CopyAsUseHintText, "de", "Verwenden Sie: COPY TO <destination> AS <flavor> [VECTOR] [OVERWRITE]" },
        { MessageId::CopyAsUseHintText, "it", "Usare: COPY TO <destination> AS <flavor> [VECTOR] [OVERWRITE]" },
        { MessageId::CopyAsUnknownFlavorText, "en-US", "COPY TO AS failed: unknown flavor '{flavor}'" },
        { MessageId::CopyAsUnknownFlavorText, "es", "COPY TO AS falló: variante desconocida '{flavor}'" },
        { MessageId::CopyAsUnknownFlavorText, "fr", "COPY TO AS a échoué : variante inconnue '{flavor}'" },
        { MessageId::CopyAsUnknownFlavorText, "de", "COPY TO AS fehlgeschlagen: unbekannte Variante '{flavor}'" },
        { MessageId::CopyAsUnknownFlavorText, "it", "COPY TO AS non riuscito: variante sconosciuta '{flavor}'" },
        { MessageId::CopyAsSidecarsIgnoredText, "en-US", "COPY TO AS: WITH SIDECARS ignored for logical conversion." },
        { MessageId::CopyAsSidecarsIgnoredText, "es", "COPY TO AS: WITH SIDECARS se ignora para la conversión lógica." },
        { MessageId::CopyAsSidecarsIgnoredText, "fr", "COPY TO AS : WITH SIDECARS ignoré pour la conversion logique." },
        { MessageId::CopyAsSidecarsIgnoredText, "de", "COPY TO AS: WITH SIDECARS wird bei logischer Konvertierung ignoriert." },
        { MessageId::CopyAsSidecarsIgnoredText, "it", "COPY TO AS: WITH SIDECARS ignorato per la conversione logica." },
        { MessageId::CopyAsVectorPolicyText, "en-US", "COPY TO AS X64 VECTOR: using current x64 vector metadata policy." },
        { MessageId::CopyAsVectorPolicyText, "es", "COPY TO AS X64 VECTOR: usando la política actual de metadatos vectoriales x64." },
        { MessageId::CopyAsVectorPolicyText, "fr", "COPY TO AS X64 VECTOR : utilisation de la politique de métadonnées vectorielles x64 actuelle." },
        { MessageId::CopyAsVectorPolicyText, "de", "COPY TO AS X64 VECTOR: aktuelle x64-Vektor-Metadatenrichtlinie wird verwendet." },
        { MessageId::CopyAsVectorPolicyText, "it", "COPY TO AS X64 VECTOR: si usa l'attuale criterio dei metadati vettoriali x64." },
        { MessageId::CopyAsFailedText, "en-US", "COPY TO AS failed: {detail}" },
        { MessageId::CopyAsFailedText, "es", "COPY TO AS falló: {detail}" },
        { MessageId::CopyAsFailedText, "fr", "COPY TO AS a échoué : {detail}" },
        { MessageId::CopyAsFailedText, "de", "COPY TO AS fehlgeschlagen: {detail}" },
        { MessageId::CopyAsFailedText, "it", "COPY TO AS non riuscito: {detail}" },
        { MessageId::CopiedTableText, "en-US", "Copied table to {dst} [{flavor}]{vector}" },
        { MessageId::CopyToFailedText, "en-US", "COPY TO failed: {detail}" },
        { MessageId::CopyToFailedText, "es", "COPY TO falló: {detail}" },
        { MessageId::CopyToFailedText, "fr", "COPY TO a échoué : {detail}" },
        { MessageId::CopyToFailedText, "de", "COPY TO fehlgeschlagen: {detail}" },
        { MessageId::CopyToFailedText, "it", "COPY TO non riuscito: {detail}" },
        { MessageId::CopiedDbfText, "en-US", "Copied DBF to {dst}" },
        { MessageId::CommitUsageText, "en-US", "Usage:\n  COMMIT USAGE\n  COMMIT\n  COMMIT ALL\n  COMMIT MANUAL\n  COMMIT INTERACTIVE\n  COMMIT AUTO\n  COMMIT ALL MANUAL\n  COMMIT ALL INTERACTIVE\n  COMMIT ALL AUTO\nNotes:\n  - COMMIT applies buffered TABLE changes with locking at commit time.\n  - COMMIT ALL applies all open buffered areas.\n  - CDX/LMDB rebuilds are intentionally not performed by COMMIT." },
        { MessageId::CommitUsageText, "es", "Uso:\n  COMMIT USAGE\n  COMMIT\n  COMMIT ALL\n  COMMIT MANUAL\n  COMMIT INTERACTIVE\n  COMMIT AUTO\n  COMMIT ALL MANUAL\n  COMMIT ALL INTERACTIVE\n  COMMIT ALL AUTO\nNotas:\n  - COMMIT aplica los cambios TABLE en búfer con bloqueo en el momento de la confirmación.\n  - COMMIT ALL aplica todas las áreas en búfer abiertas.\n  - Las reconstrucciones CDX/LMDB no las realiza COMMIT intencionadamente." },
        { MessageId::CommitUsageText, "fr", "Utilisation :\n  COMMIT USAGE\n  COMMIT\n  COMMIT ALL\n  COMMIT MANUAL\n  COMMIT INTERACTIVE\n  COMMIT AUTO\n  COMMIT ALL MANUAL\n  COMMIT ALL INTERACTIVE\n  COMMIT ALL AUTO\nRemarques :\n  - COMMIT applique les modifications TABLE en mémoire tampon avec verrouillage au moment de la validation.\n  - COMMIT ALL applique toutes les zones en mémoire tampon ouvertes.\n  - Les reconstructions CDX/LMDB ne sont volontairement pas effectuées par COMMIT." },
        { MessageId::CommitUsageText, "de", "Verwendung:\n  COMMIT USAGE\n  COMMIT\n  COMMIT ALL\n  COMMIT MANUAL\n  COMMIT INTERACTIVE\n  COMMIT AUTO\n  COMMIT ALL MANUAL\n  COMMIT ALL INTERACTIVE\n  COMMIT ALL AUTO\nHinweise:\n  - COMMIT wendet gepufferte TABLE-Änderungen mit Sperrung zum Commit-Zeitpunkt an.\n  - COMMIT ALL wendet alle geöffneten gepufferten Bereiche an.\n  - CDX/LMDB-Neuaufbauten werden von COMMIT bewusst nicht durchgeführt." },
        { MessageId::CommitUsageText, "it", "Uso:\n  COMMIT USAGE\n  COMMIT\n  COMMIT ALL\n  COMMIT MANUAL\n  COMMIT INTERACTIVE\n  COMMIT AUTO\n  COMMIT ALL MANUAL\n  COMMIT ALL INTERACTIVE\n  COMMIT ALL AUTO\nNote:\n  - COMMIT applica le modifiche TABLE nel buffer con blocco al momento del commit.\n  - COMMIT ALL applica tutte le aree bufferizzate aperte.\n  - Le ricostruzioni CDX/LMDB non vengono eseguite intenzionalmente da COMMIT." },
        { MessageId::CommitRecLockedText, "en-US", "rec {rn} locked ({detail})" },
        { MessageId::CommitRecLockedText, "es", "registro {rn} bloqueado ({detail})" },
        { MessageId::CommitRecLockedText, "fr", "enregistrement {rn} verrouillé ({detail})" },
        { MessageId::CommitRecLockedText, "de", "Datensatz {rn} gesperrt ({detail})" },
        { MessageId::CommitRecLockedText, "it", "record {rn} bloccato ({detail})" },
        { MessageId::CommitNoActiveOrderText, "en-US", "no active order; index rebuild skipped." },
        { MessageId::CommitNoActiveOrderText, "es", "sin orden activo; reconstrucción de índice omitida." },
        { MessageId::CommitNoActiveOrderText, "fr", "aucun ordre actif ; reconstruction de l'index ignorée." },
        { MessageId::CommitNoActiveOrderText, "de", "keine aktive Ordnung; Indexneuaufbau übersprungen." },
        { MessageId::CommitNoActiveOrderText, "it", "nessun ordine attivo; ricostruzione indice saltata." },
        { MessageId::CommitCdxSkippedText, "en-US", "CDX/LMDB rebuild skipped{tag}; runtime mutation hooks own index updates." },
        { MessageId::CommitCdxSkippedText, "es", "reconstrucción CDX/LMDB omitida{tag}; los ganchos de mutación en tiempo de ejecución gestionan las actualizaciones de índice." },
        { MessageId::CommitCdxSkippedText, "fr", "reconstruction CDX/LMDB ignorée{tag} ; les hooks de mutation d'exécution gèrent les mises à jour d'index." },
        { MessageId::CommitCdxSkippedText, "de", "CDX/LMDB-Neuaufbau übersprungen{tag}; Laufzeit-Mutations-Hooks verwalten die Indexaktualisierungen." },
        { MessageId::CommitCdxSkippedText, "it", "ricostruzione CDX/LMDB saltata{tag}; gli hook di mutazione runtime gestiscono gli aggiornamenti dell'indice." },
        { MessageId::CommitRebuildingCnxText, "en-US", "rebuilding CNX..." },
        { MessageId::CommitRebuildingCnxText, "es", "reconstruyendo CNX..." },
        { MessageId::CommitRebuildingCnxText, "fr", "reconstruction du CNX..." },
        { MessageId::CommitRebuildingCnxText, "de", "CNX wird neu aufgebaut..." },
        { MessageId::CommitRebuildingCnxText, "it", "ricostruzione CNX..." },
        { MessageId::CommitCnxNotClearedText, "en-US", "CNX rebuild did not clear stale state." },
        { MessageId::CommitCnxNotClearedText, "es", "la reconstrucción de CNX no eliminó el estado obsoleto." },
        { MessageId::CommitCnxNotClearedText, "fr", "la reconstruction du CNX n'a pas effacé l'état obsolète." },
        { MessageId::CommitCnxNotClearedText, "de", "CNX-Neuaufbau hat den veralteten Zustand nicht bereinigt." },
        { MessageId::CommitCnxNotClearedText, "it", "la ricostruzione CNX non ha eliminato lo stato obsoleto." },
        { MessageId::CommitReindexingText, "en-US", "reindexing INX/IDX..." },
        { MessageId::CommitReindexingText, "es", "reindexando INX/IDX..." },
        { MessageId::CommitReindexingText, "fr", "réindexation INX/IDX..." },
        { MessageId::CommitReindexingText, "de", "INX/IDX werden neu indiziert..." },
        { MessageId::CommitReindexingText, "it", "reindicizzazione INX/IDX..." },
        { MessageId::CommitReindexNotClearedText, "en-US", "INX/IDX reindex did not clear stale state." },
        { MessageId::CommitReindexNotClearedText, "es", "la reindexación de INX/IDX no eliminó el estado obsoleto." },
        { MessageId::CommitReindexNotClearedText, "fr", "la réindexation INX/IDX n'a pas effacé l'état obsolète." },
        { MessageId::CommitReindexNotClearedText, "de", "INX/IDX-Neuindizierung hat den veralteten Zustand nicht bereinigt." },
        { MessageId::CommitReindexNotClearedText, "it", "la reindicizzazione INX/IDX non ha eliminato lo stato obsoleto." },
        { MessageId::CommitNoChangesText, "en-US", "no changes in buffer." },
        { MessageId::CommitNoChangesText, "es", "no hay cambios en el búfer." },
        { MessageId::CommitNoChangesText, "fr", "aucune modification dans la mémoire tampon." },
        { MessageId::CommitNoChangesText, "de", "keine Änderungen im Puffer." },
        { MessageId::CommitNoChangesText, "it", "nessuna modifica nel buffer." },
        { MessageId::CommitPartialRemainingText, "en-US", "partial. OK={ok} FAIL={fail} (remaining buffered)" },
        { MessageId::CommitPartialRemainingText, "es", "parcial. OK={ok} FALLO={fail} (restantes en búfer)" },
        { MessageId::CommitPartialRemainingText, "fr", "partiel. OK={ok} ÉCHEC={fail} (reste en mémoire tampon)" },
        { MessageId::CommitPartialRemainingText, "de", "teilweise. OK={ok} FEHLER={fail} (verbleibend gepuffert)" },
        { MessageId::CommitPartialRemainingText, "it", "parziale. OK={ok} FALLITI={fail} (rimanenti nel buffer)" },
        { MessageId::CommitPartialText, "en-US", "partial. OK={ok} FAIL={fail}." },
        { MessageId::CommitPartialText, "es", "parcial. OK={ok} FALLO={fail}." },
        { MessageId::CommitPartialText, "fr", "partiel. OK={ok} ÉCHEC={fail}." },
        { MessageId::CommitPartialText, "de", "teilweise. OK={ok} FEHLER={fail}." },
        { MessageId::CommitPartialText, "it", "parziale. OK={ok} FALLITI={fail}." },
        { MessageId::CommitMemoFlushFailedText, "en-US", "failed during memo flush{detail}; buffer retained for retry. DBF writes may already have occurred." },
        { MessageId::CommitMemoFlushFailedText, "es", "falló durante el vaciado de memo{detail}; búfer conservado para reintento. Es posible que ya se hayan producido escrituras en DBF." },
        { MessageId::CommitMemoFlushFailedText, "fr", "échec lors du vidage du mémo{detail} ; mémoire tampon conservée pour nouvelle tentative. Des écritures DBF ont pu déjà avoir lieu." },
        { MessageId::CommitMemoFlushFailedText, "de", "Fehler beim Memo-Flush{detail}; Puffer für erneuten Versuch beibehalten. DBF-Schreibvorgänge könnten bereits erfolgt sein." },
        { MessageId::CommitMemoFlushFailedText, "it", "errore durante lo scaricamento del memo{detail}; buffer conservato per riprovare. Le scritture DBF potrebbero essere già avvenute." },
        { MessageId::CommitIndexFinalizeFailedText, "en-US", "failed during index finalization; buffer retained for retry. DBF and memo writes may already have occurred." },
        { MessageId::CommitIndexFinalizeFailedText, "es", "falló durante la finalización del índice; búfer conservado para reintento. Es posible que ya se hayan producido escrituras en DBF y memo." },
        { MessageId::CommitIndexFinalizeFailedText, "fr", "échec lors de la finalisation de l'index ; mémoire tampon conservée pour nouvelle tentative. Des écritures DBF et mémo ont pu déjà avoir lieu." },
        { MessageId::CommitIndexFinalizeFailedText, "de", "Fehler bei der Indexfinalisierung; Puffer für erneuten Versuch beibehalten. DBF- und Memo-Schreibvorgänge könnten bereits erfolgt sein." },
        { MessageId::CommitIndexFinalizeFailedText, "it", "errore durante la finalizzazione dell'indice; buffer conservato per riprovare. Le scritture DBF e memo potrebbero essere già avvenute." },
        { MessageId::CommitJournalFinalizeFailedText, "en-US", "failed during journal finalization; buffer retained for retry." },
        { MessageId::CommitJournalFinalizeFailedText, "es", "falló durante la finalización del diario; búfer conservado para reintento." },
        { MessageId::CommitJournalFinalizeFailedText, "fr", "échec lors de la finalisation du journal ; mémoire tampon conservée pour nouvelle tentative." },
        { MessageId::CommitJournalFinalizeFailedText, "de", "Fehler bei der Journalfinalisierung; Puffer für erneuten Versuch beibehalten." },
        { MessageId::CommitJournalFinalizeFailedText, "it", "errore durante la finalizzazione del journal; buffer conservato per riprovare." },
        { MessageId::CommitCompleteText, "en-US", "complete. ({ok} recs)" },
        { MessageId::CommitCompleteText, "es", "completado. ({ok} registros)" },
        { MessageId::CommitCompleteText, "fr", "terminé. ({ok} enreg.)" },
        { MessageId::CommitCompleteText, "de", "abgeschlossen. ({ok} Datensätze)" },
        { MessageId::CommitCompleteText, "it", "completato. ({ok} record)" },
        { MessageId::CommitEngineUnavailableText, "en-US", "engine not available." },
        { MessageId::CommitEngineUnavailableText, "es", "motor no disponible." },
        { MessageId::CommitEngineUnavailableText, "fr", "moteur non disponible." },
        { MessageId::CommitEngineUnavailableText, "de", "Engine nicht verfügbar." },
        { MessageId::CommitEngineUnavailableText, "it", "motore non disponibile." },
        { MessageId::CommitCannotDetermineAreaText, "en-US", "cannot determine current area." },
        { MessageId::CommitCannotDetermineAreaText, "es", "no se puede determinar el área actual." },
        { MessageId::CommitCannotDetermineAreaText, "fr", "impossible de déterminer la zone actuelle." },
        { MessageId::CommitCannotDetermineAreaText, "de", "aktueller Bereich kann nicht bestimmt werden." },
        { MessageId::CommitCannotDetermineAreaText, "it", "impossibile determinare l'area corrente." },
        { MessageId::CommitAllNoBufferedText, "en-US", "no buffered changes." },
        { MessageId::CommitAllNoBufferedText, "es", "no hay cambios en búfer." },
        { MessageId::CommitAllNoBufferedText, "fr", "aucune modification en mémoire tampon." },
        { MessageId::CommitAllNoBufferedText, "de", "keine gepufferten Änderungen." },
        { MessageId::CommitAllNoBufferedText, "it", "nessuna modifica bufferizzata." },
        { MessageId::CommitAllCompleteText, "en-US", "complete={committed} failed={failed}." },
        { MessageId::CommitAllCompleteText, "es", "completados={committed} fallidos={failed}." },
        { MessageId::CommitAllCompleteText, "fr", "validés={committed} échoués={failed}." },
        { MessageId::CommitAllCompleteText, "de", "abgeschlossen={committed} fehlgeschlagen={failed}." },
        { MessageId::CommitAllCompleteText, "it", "completati={committed} falliti={failed}." },
        { MessageId::TurbopackUsageText, "en-US", "Usage:\n  TURBOPACK USAGE\n  TURBOPACK\nExamples:\n  TURBOPACK\nNotes:\n  - TURBOPACK USAGE does not require an open table and does not rewrite files.\n  - TURBOPACK is a fast path for plain non-memo, non-x64 DBF tables only.\n  - Memo tables and x64 tables are refused; use PACK instead.\n  - TURBOPACK closes the table on success; reopen with USE <table>.\n  - Index containers must be rebuilt/rebound after TURBOPACK." },
        { MessageId::TurbopackUsageText, "es", "Uso:\n  TURBOPACK USAGE\n  TURBOPACK\nEjemplos:\n  TURBOPACK\nNotas:\n  - TURBOPACK USAGE no requiere una tabla abierta y no reescribe archivos.\n  - TURBOPACK es una vía rápida solo para tablas DBF planas sin memo y sin x64.\n  - Las tablas memo y x64 se rechazan; use PACK en su lugar.\n  - TURBOPACK cierra la tabla si tiene éxito; reábrala con USE <table>.\n  - Los contenedores de índice deben reconstruirse/revincularse tras TURBOPACK." },
        { MessageId::TurbopackUsageText, "fr", "Utilisation :\n  TURBOPACK USAGE\n  TURBOPACK\nExemples :\n  TURBOPACK\nRemarques :\n  - TURBOPACK USAGE ne nécessite pas de table ouverte et ne réécrit aucun fichier.\n  - TURBOPACK est une voie rapide uniquement pour les tables DBF simples sans mémo et non x64.\n  - Les tables mémo et x64 sont refusées ; utilisez PACK à la place.\n  - TURBOPACK ferme la table en cas de succès ; rouvrez avec USE <table>.\n  - Les conteneurs d'index doivent être reconstruits/reliés après TURBOPACK." },
        { MessageId::TurbopackUsageText, "de", "Verwendung:\n  TURBOPACK USAGE\n  TURBOPACK\nBeispiele:\n  TURBOPACK\nHinweise:\n  - TURBOPACK USAGE erfordert keine geöffnete Tabelle und schreibt keine Dateien neu.\n  - TURBOPACK ist ein schneller Pfad nur für einfache DBF-Tabellen ohne Memo und ohne x64.\n  - Memo- und x64-Tabellen werden abgelehnt; verwenden Sie stattdessen PACK.\n  - TURBOPACK schließt die Tabelle bei Erfolg; erneut öffnen mit USE <table>.\n  - Indexcontainer müssen nach TURBOPACK neu aufgebaut/neu gebunden werden." },
        { MessageId::TurbopackUsageText, "it", "Uso:\n  TURBOPACK USAGE\n  TURBOPACK\nEsempi:\n  TURBOPACK\nNote:\n  - TURBOPACK USAGE non richiede una tabella aperta e non riscrive file.\n  - TURBOPACK è un percorso rapido solo per tabelle DBF semplici senza memo e non x64.\n  - Le tabelle memo e x64 vengono rifiutate; usare PACK.\n  - TURBOPACK chiude la tabella in caso di successo; riaprire con USE <table>.\n  - I contenitori di indice devono essere ricostruiti/ricollegati dopo TURBOPACK." },
        { MessageId::TurbopackNoTableOpenText, "en-US", "No table open." },
        { MessageId::TurbopackNoTableOpenText, "es", "No hay tabla abierta." },
        { MessageId::TurbopackNoTableOpenText, "fr", "Aucune table ouverte." },
        { MessageId::TurbopackNoTableOpenText, "de", "Keine Tabelle geöffnet." },
        { MessageId::TurbopackNoTableOpenText, "it", "Nessuna tabella aperta." },
        { MessageId::TurbopackMemoNotSupportedText, "en-US", "Memo tables not supported. Use PACK instead." },
        { MessageId::TurbopackMemoNotSupportedText, "es", "Tablas memo no admitidas. Use PACK en su lugar." },
        { MessageId::TurbopackMemoNotSupportedText, "fr", "Tables mémo non prises en charge. Utilisez PACK à la place." },
        { MessageId::TurbopackMemoNotSupportedText, "de", "Memotabellen nicht unterstützt. Verwenden Sie stattdessen PACK." },
        { MessageId::TurbopackMemoNotSupportedText, "it", "Tabelle memo non supportate. Usare PACK." },
        { MessageId::TurbopackX64NotSupportedText, "en-US", "X64 tables not supported. Use PACK instead." },
        { MessageId::TurbopackX64NotSupportedText, "es", "Tablas X64 no admitidas. Use PACK en su lugar." },
        { MessageId::TurbopackX64NotSupportedText, "fr", "Tables X64 non prises en charge. Utilisez PACK à la place." },
        { MessageId::TurbopackX64NotSupportedText, "de", "X64-Tabellen nicht unterstützt. Verwenden Sie stattdessen PACK." },
        { MessageId::TurbopackX64NotSupportedText, "it", "Tabelle X64 non supportate. Usare PACK." },
        { MessageId::TurbopackCannotDeterminePathText, "en-US", "Cannot determine DBF file path." },
        { MessageId::TurbopackCannotDeterminePathText, "es", "No se puede determinar la ruta del archivo DBF." },
        { MessageId::TurbopackCannotDeterminePathText, "fr", "Impossible de déterminer le chemin du fichier DBF." },
        { MessageId::TurbopackCannotDeterminePathText, "de", "DBF-Dateipfad kann nicht bestimmt werden." },
        { MessageId::TurbopackCannotDeterminePathText, "it", "Impossibile determinare il percorso del file DBF." },
        { MessageId::TurbopackNotDbfText, "en-US", "Not a .dbf file: {file}" },
        { MessageId::TurbopackNotDbfText, "es", "No es un archivo .dbf: {file}" },
        { MessageId::TurbopackNotDbfText, "fr", "Ce n'est pas un fichier .dbf : {file}" },
        { MessageId::TurbopackNotDbfText, "de", "Keine .dbf-Datei: {file}" },
        { MessageId::TurbopackNotDbfText, "it", "Non è un file .dbf: {file}" },
        { MessageId::TurbopackFileNotFoundText, "en-US", "File not found: {file}" },
        { MessageId::TurbopackFileNotFoundText, "es", "Archivo no encontrado: {file}" },
        { MessageId::TurbopackFileNotFoundText, "fr", "Fichier introuvable : {file}" },
        { MessageId::TurbopackFileNotFoundText, "de", "Datei nicht gefunden: {file}" },
        { MessageId::TurbopackFileNotFoundText, "it", "File non trovato: {file}" },
        { MessageId::TurbopackProcessingText, "en-US", "TURBOPACK processing: {file}" },
        { MessageId::TurbopackProcessingText, "es", "TURBOPACK procesando: {file}" },
        { MessageId::TurbopackProcessingText, "fr", "TURBOPACK traitement : {file}" },
        { MessageId::TurbopackProcessingText, "de", "TURBOPACK verarbeitet: {file}" },
        { MessageId::TurbopackProcessingText, "it", "TURBOPACK elaborazione: {file}" },
        { MessageId::TurbopackCannotOpenSourceText, "en-US", "Cannot open source file." },
        { MessageId::TurbopackCannotOpenSourceText, "es", "No se puede abrir el archivo de origen." },
        { MessageId::TurbopackCannotOpenSourceText, "fr", "Impossible d'ouvrir le fichier source." },
        { MessageId::TurbopackCannotOpenSourceText, "de", "Quelldatei kann nicht geöffnet werden." },
        { MessageId::TurbopackCannotOpenSourceText, "it", "Impossibile aprire il file di origine." },
        { MessageId::TurbopackCannotReadHeaderText, "en-US", "Cannot read header." },
        { MessageId::TurbopackCannotReadHeaderText, "es", "No se puede leer el encabezado." },
        { MessageId::TurbopackCannotReadHeaderText, "fr", "Impossible de lire l'en-tête." },
        { MessageId::TurbopackCannotReadHeaderText, "de", "Header kann nicht gelesen werden." },
        { MessageId::TurbopackCannotReadHeaderText, "it", "Impossibile leggere l'intestazione." },
        { MessageId::TurbopackInvalidHeaderLenText, "en-US", "Invalid header lengths." },
        { MessageId::TurbopackInvalidHeaderLenText, "es", "Longitudes de encabezado no válidas." },
        { MessageId::TurbopackInvalidHeaderLenText, "fr", "Longueurs d'en-tête non valides." },
        { MessageId::TurbopackInvalidHeaderLenText, "de", "Ungültige Headerlängen." },
        { MessageId::TurbopackInvalidHeaderLenText, "it", "Lunghezze dell'intestazione non valide." },
        { MessageId::TurbopackDetailText, "en-US", "{detail}" },
        { MessageId::TurbopackDetailText, "es", "{detail}" },
        { MessageId::TurbopackDetailText, "fr", "{detail}" },
        { MessageId::TurbopackDetailText, "de", "{detail}" },
        { MessageId::TurbopackDetailText, "it", "{detail}" },
        { MessageId::TurbopackInvalidHeaderTermText, "en-US", "Invalid or incomplete header (missing 0x0D terminator)." },
        { MessageId::TurbopackInvalidHeaderTermText, "es", "Encabezado no válido o incompleto (falta el terminador 0x0D)." },
        { MessageId::TurbopackInvalidHeaderTermText, "fr", "En-tête non valide ou incomplet (terminateur 0x0D manquant)." },
        { MessageId::TurbopackInvalidHeaderTermText, "de", "Ungültiger oder unvollständiger Header (0x0D-Abschluss fehlt)." },
        { MessageId::TurbopackInvalidHeaderTermText, "it", "Intestazione non valida o incompleta (manca il terminatore 0x0D)." },
        { MessageId::TurbopackHeaderCountMismatchText, "en-US", "Warning — header count ({orig}) does not match physical count ({actual}); using safe count {safe}." },
        { MessageId::TurbopackHeaderCountMismatchText, "es", "Advertencia — el recuento del encabezado ({orig}) no coincide con el recuento físico ({actual}); usando recuento seguro {safe}." },
        { MessageId::TurbopackHeaderCountMismatchText, "fr", "Avertissement — le nombre de l'en-tête ({orig}) ne correspond pas au nombre physique ({actual}) ; utilisation du nombre sûr {safe}." },
        { MessageId::TurbopackHeaderCountMismatchText, "de", "Warnung — Headeranzahl ({orig}) stimmt nicht mit der physischen Anzahl ({actual}) überein; sichere Anzahl {safe} wird verwendet." },
        { MessageId::TurbopackHeaderCountMismatchText, "it", "Avviso — il conteggio dell'intestazione ({orig}) non corrisponde al conteggio fisico ({actual}); si usa il conteggio sicuro {safe}." },
        { MessageId::TurbopackNoValidRecordsText, "en-US", "Warning — no valid physical records detected; table may be corrupt." },
        { MessageId::TurbopackNoValidRecordsText, "es", "Advertencia — no se detectaron registros físicos válidos; la tabla puede estar dañada." },
        { MessageId::TurbopackNoValidRecordsText, "fr", "Avertissement — aucun enregistrement physique valide détecté ; la table est peut-être corrompue." },
        { MessageId::TurbopackNoValidRecordsText, "de", "Warnung — keine gültigen physischen Datensätze erkannt; Tabelle ist möglicherweise beschädigt." },
        { MessageId::TurbopackNoValidRecordsText, "it", "Avviso — nessun record fisico valido rilevato; la tabella potrebbe essere danneggiata." },
        { MessageId::TurbopackCannotCreateTempText, "en-US", "Cannot create temp file {file}" },
        { MessageId::TurbopackCannotCreateTempText, "es", "No se puede crear el archivo temporal {file}" },
        { MessageId::TurbopackCannotCreateTempText, "fr", "Impossible de créer le fichier temporaire {file}" },
        { MessageId::TurbopackCannotCreateTempText, "de", "Temporäre Datei {file} kann nicht erstellt werden" },
        { MessageId::TurbopackCannotCreateTempText, "it", "Impossibile creare il file temporaneo {file}" },
        { MessageId::TurbopackFailedWriteHeaderText, "en-US", "Failed writing header to temp." },
        { MessageId::TurbopackFailedWriteHeaderText, "es", "Error al escribir el encabezado en el temporal." },
        { MessageId::TurbopackFailedWriteHeaderText, "fr", "Échec d'écriture de l'en-tête dans le fichier temporaire." },
        { MessageId::TurbopackFailedWriteHeaderText, "de", "Fehler beim Schreiben des Headers in die temporäre Datei." },
        { MessageId::TurbopackFailedWriteHeaderText, "it", "Errore durante la scrittura dell'intestazione nel file temporaneo." },
        { MessageId::TurbopackReadErrorText, "en-US", "Read error at source record {rec} after {kept} kept records." },
        { MessageId::TurbopackReadErrorText, "es", "Error de lectura en el registro de origen {rec} tras {kept} registros conservados." },
        { MessageId::TurbopackReadErrorText, "fr", "Erreur de lecture à l'enregistrement source {rec} après {kept} enregistrements conservés." },
        { MessageId::TurbopackReadErrorText, "de", "Lesefehler beim Quelldatensatz {rec} nach {kept} beibehaltenen Datensätzen." },
        { MessageId::TurbopackReadErrorText, "it", "Errore di lettura al record di origine {rec} dopo {kept} record conservati." },
        { MessageId::TurbopackWriteErrorText, "en-US", "Write error after {kept} kept records." },
        { MessageId::TurbopackWriteErrorText, "es", "Error de escritura tras {kept} registros conservados." },
        { MessageId::TurbopackWriteErrorText, "fr", "Erreur d'écriture après {kept} enregistrements conservés." },
        { MessageId::TurbopackWriteErrorText, "de", "Schreibfehler nach {kept} beibehaltenen Datensätzen." },
        { MessageId::TurbopackWriteErrorText, "it", "Errore di scrittura dopo {kept} record conservati." },
        { MessageId::TurbopackFailedUpdateHeaderText, "en-US", "Failed to update header with final count." },
        { MessageId::TurbopackFailedUpdateHeaderText, "es", "Error al actualizar el encabezado con el recuento final." },
        { MessageId::TurbopackFailedUpdateHeaderText, "fr", "Échec de mise à jour de l'en-tête avec le nombre final." },
        { MessageId::TurbopackFailedUpdateHeaderText, "de", "Fehler beim Aktualisieren des Headers mit der finalen Anzahl." },
        { MessageId::TurbopackFailedUpdateHeaderText, "it", "Errore durante l'aggiornamento dell'intestazione con il conteggio finale." },
        { MessageId::TurbopackCannotCreateBackupText, "en-US", "Cannot create backup: {detail}" },
        { MessageId::TurbopackCannotCreateBackupText, "es", "No se puede crear la copia de seguridad: {detail}" },
        { MessageId::TurbopackCannotCreateBackupText, "fr", "Impossible de créer la sauvegarde : {detail}" },
        { MessageId::TurbopackCannotCreateBackupText, "de", "Sicherung kann nicht erstellt werden: {detail}" },
        { MessageId::TurbopackCannotCreateBackupText, "it", "Impossibile creare il backup: {detail}" },
        { MessageId::TurbopackCannotReplaceText, "en-US", "Cannot replace original file: {detail}" },
        { MessageId::TurbopackCannotReplaceText, "es", "No se puede reemplazar el archivo original: {detail}" },
        { MessageId::TurbopackCannotReplaceText, "fr", "Impossible de remplacer le fichier original : {detail}" },
        { MessageId::TurbopackCannotReplaceText, "de", "Originaldatei kann nicht ersetzt werden: {detail}" },
        { MessageId::TurbopackCannotReplaceText, "it", "Impossibile sostituire il file originale: {detail}" },
        { MessageId::TurbopackRollbackFailedText, "en-US", "  Rollback also failed. Original may be lost." },
        { MessageId::TurbopackRollbackFailedText, "es", "  La reversión también falló. El original puede haberse perdido." },
        { MessageId::TurbopackRollbackFailedText, "fr", "  La restauration a également échoué. L'original est peut-être perdu." },
        { MessageId::TurbopackRollbackFailedText, "de", "  Rollback ist ebenfalls fehlgeschlagen. Das Original könnte verloren sein." },
        { MessageId::TurbopackRollbackFailedText, "it", "  Anche il rollback è fallito. L'originale potrebbe essere perso." },
        { MessageId::TurbopackCompleteText, "en-US", "TURBOPACK complete. Kept {kept} of {orig} records." },
        { MessageId::TurbopackCompleteText, "es", "TURBOPACK completado. Se conservaron {kept} de {orig} registros." },
        { MessageId::TurbopackCompleteText, "fr", "TURBOPACK terminé. {kept} enregistrements conservés sur {orig}." },
        { MessageId::TurbopackCompleteText, "de", "TURBOPACK abgeschlossen. {kept} von {orig} Datensätzen behalten." },
        { MessageId::TurbopackCompleteText, "it", "TURBOPACK completato. Conservati {kept} di {orig} record." },
        { MessageId::TurbopackReadyForUseText, "en-US", "{file} ready for use." },
        { MessageId::TurbopackReadyForUseText, "es", "{file} listo para usar." },
        { MessageId::TurbopackReadyForUseText, "fr", "{file} prêt à l'emploi." },
        { MessageId::TurbopackReadyForUseText, "de", "{file} einsatzbereit." },
        { MessageId::TurbopackReadyForUseText, "it", "{file} pronto all'uso." },
        { MessageId::TurbopackSidecarsNoneText, "en-US", "Sidecar(s): none." },
        { MessageId::TurbopackSidecarsNoneText, "es", "Archivo(s) complementario(s): ninguno." },
        { MessageId::TurbopackSidecarsNoneText, "fr", "Fichier(s) annexe(s) : aucun." },
        { MessageId::TurbopackSidecarsNoneText, "de", "Begleitdatei(en): keine." },
        { MessageId::TurbopackSidecarsNoneText, "it", "File collaterali: nessuno." },
        { MessageId::TurbopackReopenText, "en-US", "Table is closed. Reopen with: USE {stem}" },
        { MessageId::TurbopackReopenText, "es", "La tabla está cerrada. Reábrala con: USE {stem}" },
        { MessageId::TurbopackReopenText, "fr", "La table est fermée. Rouvrez avec : USE {stem}" },
        { MessageId::TurbopackReopenText, "de", "Tabelle ist geschlossen. Erneut öffnen mit: USE {stem}" },
        { MessageId::TurbopackReopenText, "it", "La tabella è chiusa. Riaprire con: USE {stem}" },
        { MessageId::TurbopackReindexOrderText, "en-US", "Reindex recommended. Previous order '{order}' detached." },
        { MessageId::TurbopackReindexOrderText, "es", "Se recomienda reindexar. Orden anterior '{order}' desvinculado." },
        { MessageId::TurbopackReindexOrderText, "fr", "Réindexation recommandée. Ordre précédent '{order}' détaché." },
        { MessageId::TurbopackReindexOrderText, "de", "Neuindizierung empfohlen. Vorherige Ordnung '{order}' getrennt." },
        { MessageId::TurbopackReindexOrderText, "it", "Reindicizzazione consigliata. Ordine precedente '{order}' scollegato." },
        { MessageId::TurbopackReindexText, "en-US", "Reindex recommended." },
        { MessageId::TurbopackReindexText, "es", "Se recomienda reindexar." },
        { MessageId::TurbopackReindexText, "fr", "Réindexation recommandée." },
        { MessageId::TurbopackReindexText, "de", "Neuindizierung empfohlen." },
        { MessageId::TurbopackReindexText, "it", "Reindicizzazione consigliata." },
        { MessageId::RebuildUsageText, "en-US", "Usage:\n  REBUILD USAGE\n  REBUILD\n  REBUILD <name-or-path.cnx>\nNotes:\n  - Rebuilds the CNX container once.\n  - No args uses current CNX or defaults to <table>.cnx.\n  - Dirty TABLE buffers are committed only after confirmation." },
        { MessageId::RebuildUsageText, "es", "Uso:\n  REBUILD USAGE\n  REBUILD\n  REBUILD <name-or-path.cnx>\nNotas:\n  - Reconstruye el contenedor CNX una vez.\n  - Sin argumentos usa el CNX actual o toma <table>.cnx por defecto.\n  - Los búferes TABLE sucios se confirman solo tras confirmación." },
        { MessageId::RebuildUsageText, "fr", "Utilisation :\n  REBUILD USAGE\n  REBUILD\n  REBUILD <name-or-path.cnx>\nRemarques :\n  - Reconstruit le conteneur CNX une fois.\n  - Sans argument, utilise le CNX actuel ou <table>.cnx par défaut.\n  - Les tampons TABLE modifiés ne sont validés qu'après confirmation." },
        { MessageId::RebuildUsageText, "de", "Verwendung:\n  REBUILD USAGE\n  REBUILD\n  REBUILD <name-or-path.cnx>\nHinweise:\n  - Baut den CNX-Container einmal neu auf.\n  - Ohne Argumente wird der aktuelle CNX oder standardmäßig <table>.cnx verwendet.\n  - Geänderte TABLE-Puffer werden erst nach Bestätigung committet." },
        { MessageId::RebuildUsageText, "it", "Uso:\n  REBUILD USAGE\n  REBUILD\n  REBUILD <name-or-path.cnx>\nNote:\n  - Ricostruisce il contenitore CNX una volta.\n  - Senza argomenti usa il CNX corrente o per impostazione predefinita <table>.cnx.\n  - I buffer TABLE modificati vengono confermati solo dopo conferma." },
        { MessageId::RebuildCanceledDirtyText, "en-US", "canceled (dirty table)." },
        { MessageId::RebuildCanceledDirtyText, "es", "cancelado (tabla sucia)." },
        { MessageId::RebuildCanceledDirtyText, "fr", "annulé (table modifiée)." },
        { MessageId::RebuildCanceledDirtyText, "de", "abgebrochen (Tabelle geändert)." },
        { MessageId::RebuildCanceledDirtyText, "it", "annullato (tabella modificata)." },
        { MessageId::RebuildStillDirtyText, "en-US", "still dirty after COMMIT; canceling." },
        { MessageId::RebuildStillDirtyText, "es", "aún sucia tras COMMIT; cancelando." },
        { MessageId::RebuildStillDirtyText, "fr", "toujours modifiée après COMMIT ; annulation." },
        { MessageId::RebuildStillDirtyText, "de", "nach COMMIT immer noch geändert; wird abgebrochen." },
        { MessageId::RebuildStillDirtyText, "it", "ancora modificata dopo COMMIT; annullamento." },
        { MessageId::RebuildNoTableOpenText, "en-US", "no table open." },
        { MessageId::RebuildNoTableOpenText, "es", "no hay tabla abierta." },
        { MessageId::RebuildNoTableOpenText, "fr", "aucune table ouverte." },
        { MessageId::RebuildNoTableOpenText, "de", "keine Tabelle geöffnet." },
        { MessageId::RebuildNoTableOpenText, "it", "nessuna tabella aperta." },
        { MessageId::RebuildCnxNotFoundText, "en-US", "CNX not found: {path}" },
        { MessageId::RebuildCnxNotFoundText, "es", "CNX no encontrado: {path}" },
        { MessageId::RebuildCnxNotFoundText, "fr", "CNX introuvable : {path}" },
        { MessageId::RebuildCnxNotFoundText, "de", "CNX nicht gefunden: {path}" },
        { MessageId::RebuildCnxNotFoundText, "it", "CNX non trovato: {path}" },
        { MessageId::RebuildReindexBannerText, "en-US", "REINDEX CNX -> REBUILD" },
        { MessageId::RebuildReindexBannerText, "es", "REINDEX CNX -> REBUILD" },
        { MessageId::RebuildReindexBannerText, "fr", "REINDEX CNX -> REBUILD" },
        { MessageId::RebuildReindexBannerText, "de", "REINDEX CNX -> REBUILD" },
        { MessageId::RebuildReindexBannerText, "it", "REINDEX CNX -> REBUILD" },
        { MessageId::RebuildCnxContainerText, "en-US", "CNX container: {path}" },
        { MessageId::RebuildCnxContainerText, "es", "contenedor CNX: {path}" },
        { MessageId::RebuildCnxContainerText, "fr", "conteneur CNX : {path}" },
        { MessageId::RebuildCnxContainerText, "de", "CNX-Container: {path}" },
        { MessageId::RebuildCnxContainerText, "it", "contenitore CNX: {path}" },
        { MessageId::RebuildUnableOpenCnxText, "en-US", "unable to open CNX" },
        { MessageId::RebuildUnableOpenCnxText, "es", "no se puede abrir el CNX" },
        { MessageId::RebuildUnableOpenCnxText, "fr", "impossible d'ouvrir le CNX" },
        { MessageId::RebuildUnableOpenCnxText, "de", "CNX kann nicht geöffnet werden" },
        { MessageId::RebuildUnableOpenCnxText, "it", "impossibile aprire il CNX" },
        { MessageId::RebuildFailedReadTagdirText, "en-US", "failed to read tag directory" },
        { MessageId::RebuildFailedReadTagdirText, "es", "no se pudo leer el directorio de etiquetas" },
        { MessageId::RebuildFailedReadTagdirText, "fr", "échec de lecture du répertoire des tags" },
        { MessageId::RebuildFailedReadTagdirText, "de", "Tag-Verzeichnis konnte nicht gelesen werden" },
        { MessageId::RebuildFailedReadTagdirText, "it", "impossibile leggere la directory dei tag" },
        { MessageId::RebuildBackendOpenFailedText, "en-US", "backend open failed" },
        { MessageId::RebuildBackendOpenFailedText, "es", "fallo al abrir el backend" },
        { MessageId::RebuildBackendOpenFailedText, "fr", "échec d'ouverture du backend" },
        { MessageId::RebuildBackendOpenFailedText, "de", "Backend-Öffnung fehlgeschlagen" },
        { MessageId::RebuildBackendOpenFailedText, "it", "apertura del backend non riuscita" },
        { MessageId::RebuildTagOkText, "en-US", "  [{id}] {tag} : OK" },
        { MessageId::RebuildTagOkText, "es", "  [{id}] {tag} : OK" },
        { MessageId::RebuildTagOkText, "fr", "  [{id}] {tag} : OK" },
        { MessageId::RebuildTagOkText, "de", "  [{id}] {tag} : OK" },
        { MessageId::RebuildTagOkText, "it", "  [{id}] {tag} : OK" },
        { MessageId::RebuildStaleClearedText, "en-US", "TABLE STALE cleared (fresh)" },
        { MessageId::RebuildStaleClearedText, "es", "TABLE STALE eliminado (actualizado)" },
        { MessageId::RebuildStaleClearedText, "fr", "TABLE STALE effacé (à jour)" },
        { MessageId::RebuildStaleClearedText, "de", "TABLE STALE bereinigt (aktuell)" },
        { MessageId::RebuildStaleClearedText, "it", "TABLE STALE eliminato (aggiornato)" },
        { MessageId::RebuildDoneText, "en-US", "done  OK={ok}  SKIP=0  FAIL=0" },
        { MessageId::RebuildDoneText, "es", "listo  OK={ok}  OMITIDOS=0  FALLOS=0" },
        { MessageId::RebuildDoneText, "fr", "terminé  OK={ok}  IGNORÉS=0  ÉCHECS=0" },
        { MessageId::RebuildDoneText, "de", "fertig  OK={ok}  ÜBERSPRUNGEN=0  FEHLER=0" },
        { MessageId::RebuildDoneText, "it", "fatto  OK={ok}  SALTATI=0  FALLITI=0" },
        { MessageId::RebuildFailDetailText, "en-US", "FAIL ({detail})" },
        { MessageId::RebuildFailDetailText, "es", "FALLO ({detail})" },
        { MessageId::RebuildFailDetailText, "fr", "ÉCHEC ({detail})" },
        { MessageId::RebuildFailDetailText, "de", "FEHLER ({detail})" },
        { MessageId::RebuildFailDetailText, "it", "FALLITO ({detail})" },
        { MessageId::RebuildFailText, "en-US", "FAIL" },
        { MessageId::RebuildFailText, "es", "FALLO" },
        { MessageId::RebuildFailText, "fr", "ÉCHEC" },
        { MessageId::RebuildFailText, "de", "FEHLER" },
        { MessageId::RebuildFailText, "it", "FALLITO" },
        { MessageId::SortUsageText, "en-US", "Usage:\n  SORT USAGE\n  SORT TO <outdbf> ON <expr>\n  SORT TO <outdbf> ON <expr> ASC\n  SORT TO <outdbf> ON <expr> DESC\n  SORT TO <outdbf> ON <expr>, <expr>\n  SORT ALL TO <outdbf> ON <expr>\n  SORT DELETED TO <outdbf> ON <expr>\n  SORT OVERWRITE TO <outdbf> ON <expr>\n  SORT TO <outdbf> ON <expr> FOR <expr>\n  SORT TO <outdbf> ON <expr> WHILE <expr>\n  SORT TO <outdbf> ON <expr> FIELDS <fieldlist>\n  SORT TO <outdbf> ON <expr> UNIQUE" },
        { MessageId::SortUsageText, "es", "Uso:\n  SORT USAGE\n  SORT TO <outdbf> ON <expr>\n  SORT TO <outdbf> ON <expr> ASC\n  SORT TO <outdbf> ON <expr> DESC\n  SORT TO <outdbf> ON <expr>, <expr>\n  SORT ALL TO <outdbf> ON <expr>\n  SORT DELETED TO <outdbf> ON <expr>\n  SORT OVERWRITE TO <outdbf> ON <expr>\n  SORT TO <outdbf> ON <expr> FOR <expr>\n  SORT TO <outdbf> ON <expr> WHILE <expr>\n  SORT TO <outdbf> ON <expr> FIELDS <fieldlist>\n  SORT TO <outdbf> ON <expr> UNIQUE" },
        { MessageId::SortUsageText, "fr", "Utilisation :\n  SORT USAGE\n  SORT TO <outdbf> ON <expr>\n  SORT TO <outdbf> ON <expr> ASC\n  SORT TO <outdbf> ON <expr> DESC\n  SORT TO <outdbf> ON <expr>, <expr>\n  SORT ALL TO <outdbf> ON <expr>\n  SORT DELETED TO <outdbf> ON <expr>\n  SORT OVERWRITE TO <outdbf> ON <expr>\n  SORT TO <outdbf> ON <expr> FOR <expr>\n  SORT TO <outdbf> ON <expr> WHILE <expr>\n  SORT TO <outdbf> ON <expr> FIELDS <fieldlist>\n  SORT TO <outdbf> ON <expr> UNIQUE" },
        { MessageId::SortUsageText, "de", "Verwendung:\n  SORT USAGE\n  SORT TO <outdbf> ON <expr>\n  SORT TO <outdbf> ON <expr> ASC\n  SORT TO <outdbf> ON <expr> DESC\n  SORT TO <outdbf> ON <expr>, <expr>\n  SORT ALL TO <outdbf> ON <expr>\n  SORT DELETED TO <outdbf> ON <expr>\n  SORT OVERWRITE TO <outdbf> ON <expr>\n  SORT TO <outdbf> ON <expr> FOR <expr>\n  SORT TO <outdbf> ON <expr> WHILE <expr>\n  SORT TO <outdbf> ON <expr> FIELDS <fieldlist>\n  SORT TO <outdbf> ON <expr> UNIQUE" },
        { MessageId::SortUsageText, "it", "Uso:\n  SORT USAGE\n  SORT TO <outdbf> ON <expr>\n  SORT TO <outdbf> ON <expr> ASC\n  SORT TO <outdbf> ON <expr> DESC\n  SORT TO <outdbf> ON <expr>, <expr>\n  SORT ALL TO <outdbf> ON <expr>\n  SORT DELETED TO <outdbf> ON <expr>\n  SORT OVERWRITE TO <outdbf> ON <expr>\n  SORT TO <outdbf> ON <expr> FOR <expr>\n  SORT TO <outdbf> ON <expr> WHILE <expr>\n  SORT TO <outdbf> ON <expr> FIELDS <fieldlist>\n  SORT TO <outdbf> ON <expr> UNIQUE" },
        { MessageId::SortNoTableOpenText, "en-US", "no table is open." },
        { MessageId::SortNoTableOpenText, "es", "no hay ninguna tabla abierta." },
        { MessageId::SortNoTableOpenText, "fr", "aucune table n'est ouverte." },
        { MessageId::SortNoTableOpenText, "de", "keine Tabelle geöffnet." },
        { MessageId::SortNoTableOpenText, "it", "nessuna tabella è aperta." },
        { MessageId::SortMissingOutputText, "en-US", "missing output file after TO." },
        { MessageId::SortMissingOutputText, "es", "falta el archivo de salida después de TO." },
        { MessageId::SortMissingOutputText, "fr", "fichier de sortie manquant après TO." },
        { MessageId::SortMissingOutputText, "de", "Ausgabedatei nach TO fehlt." },
        { MessageId::SortMissingOutputText, "it", "file di output mancante dopo TO." },
        { MessageId::SortMissingOnKeysText, "en-US", "missing ON key list." },
        { MessageId::SortMissingOnKeysText, "es", "falta la lista de claves ON." },
        { MessageId::SortMissingOnKeysText, "fr", "liste de clés ON manquante." },
        { MessageId::SortMissingOnKeysText, "de", "ON-Schlüsselliste fehlt." },
        { MessageId::SortMissingOnKeysText, "it", "elenco di chiavi ON mancante." },
        { MessageId::SortErrorDetailText, "en-US", "{detail}" },
        { MessageId::SortErrorDetailText, "es", "{detail}" },
        { MessageId::SortErrorDetailText, "fr", "{detail}" },
        { MessageId::SortErrorDetailText, "de", "{detail}" },
        { MessageId::SortErrorDetailText, "it", "{detail}" },
        { MessageId::SortNoUsableKeysText, "en-US", "no usable keys found in ON list." },
        { MessageId::SortNoUsableKeysText, "es", "no se encontraron claves utilizables en la lista ON." },
        { MessageId::SortNoUsableKeysText, "fr", "aucune clé utilisable trouvée dans la liste ON." },
        { MessageId::SortNoUsableKeysText, "de", "keine verwendbaren Schlüssel in der ON-Liste gefunden." },
        { MessageId::SortNoUsableKeysText, "it", "nessuna chiave utilizzabile trovata nell'elenco ON." },
        { MessageId::SortOutputExistsText, "en-US", "output exists (use OVERWRITE): {path}" },
        { MessageId::SortOutputExistsText, "es", "la salida ya existe (use OVERWRITE): {path}" },
        { MessageId::SortOutputExistsText, "fr", "la sortie existe déjà (utilisez OVERWRITE) : {path}" },
        { MessageId::SortOutputExistsText, "de", "Ausgabe existiert bereits (verwenden Sie OVERWRITE): {path}" },
        { MessageId::SortOutputExistsText, "it", "l'output esiste già (usare OVERWRITE): {path}" },
        { MessageId::SortCannotOverwriteText, "en-US", "cannot overwrite existing file: {path}" },
        { MessageId::SortCannotOverwriteText, "es", "no se puede sobrescribir el archivo existente: {path}" },
        { MessageId::SortCannotOverwriteText, "fr", "impossible d'écraser le fichier existant : {path}" },
        { MessageId::SortCannotOverwriteText, "de", "vorhandene Datei kann nicht überschrieben werden: {path}" },
        { MessageId::SortCannotOverwriteText, "it", "impossibile sovrascrivere il file esistente: {path}" },
        { MessageId::SortWhileEvalFailedText, "en-US", "WHILE evaluation failed." },
        { MessageId::SortWhileEvalFailedText, "es", "falló la evaluación de WHILE." },
        { MessageId::SortWhileEvalFailedText, "fr", "échec de l'évaluation de WHILE." },
        { MessageId::SortWhileEvalFailedText, "de", "WHILE-Auswertung fehlgeschlagen." },
        { MessageId::SortWhileEvalFailedText, "it", "valutazione di WHILE non riuscita." },
        { MessageId::SortForEvalFailedText, "en-US", "FOR evaluation failed." },
        { MessageId::SortForEvalFailedText, "es", "falló la evaluación de FOR." },
        { MessageId::SortForEvalFailedText, "fr", "échec de l'évaluation de FOR." },
        { MessageId::SortForEvalFailedText, "de", "FOR-Auswertung fehlgeschlagen." },
        { MessageId::SortForEvalFailedText, "it", "valutazione di FOR non riuscita." },
        { MessageId::SortSummaryText, "en-US", "scanned {scanned}, selected {kept}, wrote {written}{unique} -> {path}" },
        { MessageId::SortSummaryText, "es", "analizados {scanned}, seleccionados {kept}, escritos {written}{unique} -> {path}" },
        { MessageId::SortSummaryText, "fr", "analysés {scanned}, sélectionnés {kept}, écrits {written}{unique} -> {path}" },
        { MessageId::SortSummaryText, "de", "geprüft {scanned}, ausgewählt {kept}, geschrieben {written}{unique} -> {path}" },
        { MessageId::SortSummaryText, "it", "analizzati {scanned}, selezionati {kept}, scritti {written}{unique} -> {path}" },
        { MessageId::ReindexUsageText, "en-US", "Usage:\n  REINDEX USAGE\n  REINDEX\n  REINDEX INX [<tagfile>]\n  REINDEX CNX [<name-or-path.cnx>]\n  REINDEX CDX [YES|AUTO|NOPROMPT] [CLEAN|FORCE] [QUIET]\n  REINDEX SIX [<tagfile>]\n  REINDEX SCX [<tagfile>]\n  REINDEX ALL\n  REINDEX CUSTOM\n  REINDEX <tagfile>\nNotes:\n  - Default: v64-like table -> CDX; v32-like table -> INX.\n  - CNX delegates to REBUILD; CDX delegates to BUILDLMDB.\n  - REINDEX <tagfile> is treated as REINDEX INX <tagfile>." },
        { MessageId::ReindexUsageText, "es", "Uso:\n  REINDEX USAGE\n  REINDEX\n  REINDEX INX [<tagfile>]\n  REINDEX CNX [<name-or-path.cnx>]\n  REINDEX CDX [YES|AUTO|NOPROMPT] [CLEAN|FORCE] [QUIET]\n  REINDEX SIX [<tagfile>]\n  REINDEX SCX [<tagfile>]\n  REINDEX ALL\n  REINDEX CUSTOM\n  REINDEX <tagfile>\nNotas:\n  - Predeterminado: tabla tipo v64 -> CDX; tabla tipo v32 -> INX.\n  - CNX delega en REBUILD; CDX delega en BUILDLMDB.\n  - REINDEX <tagfile> se trata como REINDEX INX <tagfile>." },
        { MessageId::ReindexUsageText, "fr", "Utilisation :\n  REINDEX USAGE\n  REINDEX\n  REINDEX INX [<tagfile>]\n  REINDEX CNX [<name-or-path.cnx>]\n  REINDEX CDX [YES|AUTO|NOPROMPT] [CLEAN|FORCE] [QUIET]\n  REINDEX SIX [<tagfile>]\n  REINDEX SCX [<tagfile>]\n  REINDEX ALL\n  REINDEX CUSTOM\n  REINDEX <tagfile>\nRemarques :\n  - Par défaut : table de type v64 -> CDX ; table de type v32 -> INX.\n  - CNX délègue à REBUILD ; CDX délègue à BUILDLMDB.\n  - REINDEX <tagfile> est traité comme REINDEX INX <tagfile>." },
        { MessageId::ReindexUsageText, "de", "Verwendung:\n  REINDEX USAGE\n  REINDEX\n  REINDEX INX [<tagfile>]\n  REINDEX CNX [<name-or-path.cnx>]\n  REINDEX CDX [YES|AUTO|NOPROMPT] [CLEAN|FORCE] [QUIET]\n  REINDEX SIX [<tagfile>]\n  REINDEX SCX [<tagfile>]\n  REINDEX ALL\n  REINDEX CUSTOM\n  REINDEX <tagfile>\nHinweise:\n  - Standard: v64-ähnliche Tabelle -> CDX; v32-ähnliche Tabelle -> INX.\n  - CNX delegiert an REBUILD; CDX delegiert an BUILDLMDB.\n  - REINDEX <tagfile> wird als REINDEX INX <tagfile> behandelt." },
        { MessageId::ReindexUsageText, "it", "Uso:\n  REINDEX USAGE\n  REINDEX\n  REINDEX INX [<tagfile>]\n  REINDEX CNX [<name-or-path.cnx>]\n  REINDEX CDX [YES|AUTO|NOPROMPT] [CLEAN|FORCE] [QUIET]\n  REINDEX SIX [<tagfile>]\n  REINDEX SCX [<tagfile>]\n  REINDEX ALL\n  REINDEX CUSTOM\n  REINDEX <tagfile>\nNote:\n  - Predefinito: tabella tipo v64 -> CDX; tabella tipo v32 -> INX.\n  - CNX delega a REBUILD; CDX delega a BUILDLMDB.\n  - REINDEX <tagfile> è trattato come REINDEX INX <tagfile>." },
        { MessageId::ReindexCanceledDirtyText, "en-US", "canceled (dirty table)." },
        { MessageId::ReindexCanceledDirtyText, "es", "cancelado (tabla sucia)." },
        { MessageId::ReindexCanceledDirtyText, "fr", "annulé (table modifiée)." },
        { MessageId::ReindexCanceledDirtyText, "de", "abgebrochen (Tabelle geändert)." },
        { MessageId::ReindexCanceledDirtyText, "it", "annullato (tabella modificata)." },
        { MessageId::ReindexStillDirtyText, "en-US", "still dirty after COMMIT; canceling." },
        { MessageId::ReindexStillDirtyText, "es", "aún sucia tras COMMIT; cancelando." },
        { MessageId::ReindexStillDirtyText, "fr", "toujours modifiée après COMMIT ; annulation." },
        { MessageId::ReindexStillDirtyText, "de", "nach COMMIT immer noch geändert; wird abgebrochen." },
        { MessageId::ReindexStillDirtyText, "it", "ancora modificata dopo COMMIT; annullamento." },
        { MessageId::ReindexNoTableOpenText, "en-US", "no table open." },
        { MessageId::ReindexNoTableOpenText, "es", "no hay tabla abierta." },
        { MessageId::ReindexNoTableOpenText, "fr", "aucune table ouverte." },
        { MessageId::ReindexNoTableOpenText, "de", "keine Tabelle geöffnet." },
        { MessageId::ReindexNoTableOpenText, "it", "nessuna tabella aperta." },
        { MessageId::ReindexNoTableOpenPlainText, "en-US", "No table open." },
        { MessageId::ReindexNoTableOpenPlainText, "es", "No hay tabla abierta." },
        { MessageId::ReindexNoTableOpenPlainText, "fr", "Aucune table ouverte." },
        { MessageId::ReindexNoTableOpenPlainText, "de", "Keine Tabelle geöffnet." },
        { MessageId::ReindexNoTableOpenPlainText, "it", "Nessuna tabella aperta." },
        { MessageId::ReindexUnknownFieldText, "en-US", "unknown field token '{token}'." },
        { MessageId::ReindexUnknownFieldText, "es", "token de campo desconocido '{token}'." },
        { MessageId::ReindexUnknownFieldText, "fr", "jeton de champ inconnu '{token}'." },
        { MessageId::ReindexUnknownFieldText, "de", "unbekanntes Feldtoken '{token}'." },
        { MessageId::ReindexUnknownFieldText, "it", "token di campo sconosciuto '{token}'." },
        { MessageId::ReindexCannotWriteText, "en-US", "cannot write file: {path}" },
        { MessageId::ReindexCannotWriteText, "es", "no se puede escribir el archivo: {path}" },
        { MessageId::ReindexCannotWriteText, "fr", "impossible d'écrire le fichier : {path}" },
        { MessageId::ReindexCannotWriteText, "de", "Datei kann nicht geschrieben werden: {path}" },
        { MessageId::ReindexCannotWriteText, "it", "impossibile scrivere il file: {path}" },
        { MessageId::ReindexWroteText, "en-US", "wrote {file}  (2INX v2, expr: {expr}, ASC)" },
        { MessageId::ReindexWroteText, "es", "escrito {file}  (2INX v2, expr: {expr}, ASC)" },
        { MessageId::ReindexWroteText, "fr", "écrit {file}  (2INX v2, expr : {expr}, ASC)" },
        { MessageId::ReindexWroteText, "de", "{file} geschrieben  (2INX v2, expr: {expr}, ASC)" },
        { MessageId::ReindexWroteText, "it", "scritto {file}  (2INX v2, expr: {expr}, ASC)" },
        { MessageId::ReindexCannotInferTagText, "en-US", "cannot infer tag path (unknown table name).\nSpecify a tag file: REINDEX INX <tagfile.inx>" },
        { MessageId::ReindexCannotInferTagText, "es", "no se puede inferir la ruta de la etiqueta (nombre de tabla desconocido).\nEspecifique un archivo de etiqueta: REINDEX INX <tagfile.inx>" },
        { MessageId::ReindexCannotInferTagText, "fr", "impossible de déduire le chemin du tag (nom de table inconnu).\nSpécifiez un fichier de tag : REINDEX INX <tagfile.inx>" },
        { MessageId::ReindexCannotInferTagText, "de", "Tag-Pfad kann nicht abgeleitet werden (unbekannter Tabellenname).\nGeben Sie eine Tag-Datei an: REINDEX INX <tagfile.inx>" },
        { MessageId::ReindexCannotInferTagText, "it", "impossibile dedurre il percorso del tag (nome tabella sconosciuto).\nSpecificare un file di tag: REINDEX INX <tagfile.inx>" },
        { MessageId::ReindexTagNotFoundText, "en-US", "tag file not found: {path}" },
        { MessageId::ReindexTagNotFoundText, "es", "archivo de etiqueta no encontrado: {path}" },
        { MessageId::ReindexTagNotFoundText, "fr", "fichier de tag introuvable : {path}" },
        { MessageId::ReindexTagNotFoundText, "de", "Tag-Datei nicht gefunden: {path}" },
        { MessageId::ReindexTagNotFoundText, "it", "file di tag non trovato: {path}" },
        { MessageId::ReindexTagNotFoundHintText, "en-US", "Hint: create it with: INDEX ON <field|#n> TAG {filename}" },
        { MessageId::ReindexTagNotFoundHintText, "es", "Sugerencia: créelo con: INDEX ON <field|#n> TAG {filename}" },
        { MessageId::ReindexTagNotFoundHintText, "fr", "Astuce : créez-le avec : INDEX ON <field|#n> TAG {filename}" },
        { MessageId::ReindexTagNotFoundHintText, "de", "Hinweis: erstellen Sie sie mit: INDEX ON <field|#n> TAG {filename}" },
        { MessageId::ReindexTagNotFoundHintText, "it", "Suggerimento: crearlo con: INDEX ON <field|#n> TAG {filename}" },
        { MessageId::ReindexCannotReadExprText, "en-US", "cannot read tag expression from: {path}" },
        { MessageId::ReindexCannotReadExprText, "es", "no se puede leer la expresión de etiqueta de: {path}" },
        { MessageId::ReindexCannotReadExprText, "fr", "impossible de lire l'expression du tag depuis : {path}" },
        { MessageId::ReindexCannotReadExprText, "de", "Tag-Ausdruck kann nicht gelesen werden aus: {path}" },
        { MessageId::ReindexCannotReadExprText, "it", "impossibile leggere l'espressione del tag da: {path}" },
        { MessageId::ReindexInxBannerText, "en-US", "REINDEX INX" },
        { MessageId::ReindexInxBannerText, "es", "REINDEX INX" },
        { MessageId::ReindexInxBannerText, "fr", "REINDEX INX" },
        { MessageId::ReindexInxBannerText, "de", "REINDEX INX" },
        { MessageId::ReindexInxBannerText, "it", "REINDEX INX" },
        { MessageId::ReindexInxIndexFileText, "en-US", "  Index file   : {path}" },
        { MessageId::ReindexInxIndexFileText, "es", "  Archivo de índice: {path}" },
        { MessageId::ReindexInxIndexFileText, "fr", "  Fichier d'index : {path}" },
        { MessageId::ReindexInxIndexFileText, "de", "  Indexdatei   : {path}" },
        { MessageId::ReindexInxIndexFileText, "it", "  File di indice: {path}" },
        { MessageId::ReindexInxTagExprText, "en-US", "  Tag expr     : {expr}" },
        { MessageId::ReindexInxTagExprText, "es", "  Expr etiqueta : {expr}" },
        { MessageId::ReindexInxTagExprText, "fr", "  Expr du tag   : {expr}" },
        { MessageId::ReindexInxTagExprText, "de", "  Tag-Ausdruck  : {expr}" },
        { MessageId::ReindexInxTagExprText, "it", "  Espr. tag     : {expr}" },
        { MessageId::ReindexFailedText, "en-US", "failed." },
        { MessageId::ReindexFailedText, "es", "falló." },
        { MessageId::ReindexFailedText, "fr", "échec." },
        { MessageId::ReindexFailedText, "de", "fehlgeschlagen." },
        { MessageId::ReindexFailedText, "it", "non riuscito." },
        { MessageId::ReindexStaleClearedText, "en-US", "TABLE STALE cleared (fresh)." },
        { MessageId::ReindexStaleClearedText, "es", "TABLE STALE eliminado (actualizado)." },
        { MessageId::ReindexStaleClearedText, "fr", "TABLE STALE effacé (à jour)." },
        { MessageId::ReindexStaleClearedText, "de", "TABLE STALE bereinigt (aktuell)." },
        { MessageId::ReindexStaleClearedText, "it", "TABLE STALE eliminato (aggiornato)." },
        { MessageId::ReindexRegeneratedNoteText, "en-US", "Note: INX file was regenerated from its stored tag expression." },
        { MessageId::ReindexRegeneratedNoteText, "es", "Nota: el archivo INX se regeneró a partir de su expresión de etiqueta almacenada." },
        { MessageId::ReindexRegeneratedNoteText, "fr", "Remarque : le fichier INX a été régénéré à partir de son expression de tag stockée." },
        { MessageId::ReindexRegeneratedNoteText, "de", "Hinweis: Die INX-Datei wurde aus ihrem gespeicherten Tag-Ausdruck neu erzeugt." },
        { MessageId::ReindexRegeneratedNoteText, "it", "Nota: il file INX è stato rigenerato dalla sua espressione di tag memorizzata." },
        { MessageId::ReindexCdxRequiresLmdbText, "en-US", "REINDEX CDX requires DOTTALK_INDEX_MODE=LMDB." },
        { MessageId::ReindexCdxRequiresLmdbText, "es", "REINDEX CDX requiere DOTTALK_INDEX_MODE=LMDB." },
        { MessageId::ReindexCdxRequiresLmdbText, "fr", "REINDEX CDX nécessite DOTTALK_INDEX_MODE=LMDB." },
        { MessageId::ReindexCdxRequiresLmdbText, "de", "REINDEX CDX erfordert DOTTALK_INDEX_MODE=LMDB." },
        { MessageId::ReindexCdxRequiresLmdbText, "it", "REINDEX CDX richiede DOTTALK_INDEX_MODE=LMDB." },
        { MessageId::ReindexSixBannerText, "en-US", "REINDEX SIX (student single-tag)" },
        { MessageId::ReindexSixBannerText, "es", "REINDEX SIX (etiqueta única de estudiante)" },
        { MessageId::ReindexSixBannerText, "fr", "REINDEX SIX (tag unique étudiant)" },
        { MessageId::ReindexSixBannerText, "de", "REINDEX SIX (Einzeltag Student)" },
        { MessageId::ReindexSixBannerText, "it", "REINDEX SIX (tag singolo studente)" },
        { MessageId::ReindexScxBannerText, "en-US", "REINDEX SCX (student compound)" },
        { MessageId::ReindexScxBannerText, "es", "REINDEX SCX (compuesto de estudiante)" },
        { MessageId::ReindexScxBannerText, "fr", "REINDEX SCX (composé étudiant)" },
        { MessageId::ReindexScxBannerText, "de", "REINDEX SCX (Student zusammengesetzt)" },
        { MessageId::ReindexScxBannerText, "it", "REINDEX SCX (composto studente)" },
        { MessageId::ReindexTableLineText, "en-US", "  Table : {table}" },
        { MessageId::ReindexTableLineText, "es", "  Tabla : {table}" },
        { MessageId::ReindexTableLineText, "fr", "  Table : {table}" },
        { MessageId::ReindexTableLineText, "de", "  Tabelle : {table}" },
        { MessageId::ReindexTableLineText, "it", "  Tabella : {table}" },
        { MessageId::ReindexArgLineText, "en-US", "  Arg   : {arg}" },
        { MessageId::ReindexArgLineText, "es", "  Arg   : {arg}" },
        { MessageId::ReindexArgLineText, "fr", "  Arg   : {arg}" },
        { MessageId::ReindexArgLineText, "de", "  Arg   : {arg}" },
        { MessageId::ReindexArgLineText, "it", "  Arg   : {arg}" },
        { MessageId::ReindexStubStatusText, "en-US", "  Status: stub (no backend)" },
        { MessageId::ReindexStubStatusText, "es", "  Estado: stub (sin backend)" },
        { MessageId::ReindexStubStatusText, "fr", "  Statut : stub (aucun backend)" },
        { MessageId::ReindexStubStatusText, "de", "  Status: Stub (kein Backend)" },
        { MessageId::ReindexStubStatusText, "it", "  Stato: stub (nessun backend)" },
        { MessageId::ReindexAllCdxText, "en-US", "REINDEX ALL -> CDX (v64-like table)" },
        { MessageId::ReindexAllCdxText, "es", "REINDEX ALL -> CDX (tabla tipo v64)" },
        { MessageId::ReindexAllCdxText, "fr", "REINDEX ALL -> CDX (table de type v64)" },
        { MessageId::ReindexAllCdxText, "de", "REINDEX ALL -> CDX (v64-ähnliche Tabelle)" },
        { MessageId::ReindexAllCdxText, "it", "REINDEX ALL -> CDX (tabella tipo v64)" },
        { MessageId::ReindexAllInxCnxText, "en-US", "REINDEX ALL -> INX + CNX (v32-like table)" },
        { MessageId::ReindexAllInxCnxText, "es", "REINDEX ALL -> INX + CNX (tabla tipo v32)" },
        { MessageId::ReindexAllInxCnxText, "fr", "REINDEX ALL -> INX + CNX (table de type v32)" },
        { MessageId::ReindexAllInxCnxText, "de", "REINDEX ALL -> INX + CNX (v32-ähnliche Tabelle)" },
        { MessageId::ReindexAllInxCnxText, "it", "REINDEX ALL -> INX + CNX (tabella tipo v32)" },
        { MessageId::ReindexCustomText, "en-US", "REINDEX CUSTOM -> SIX + SCX" },
        { MessageId::ReindexCustomText, "es", "REINDEX CUSTOM -> SIX + SCX" },
        { MessageId::ReindexCustomText, "fr", "REINDEX CUSTOM -> SIX + SCX" },
        { MessageId::ReindexCustomText, "de", "REINDEX CUSTOM -> SIX + SCX" },
        { MessageId::ReindexCustomText, "it", "REINDEX CUSTOM -> SIX + SCX" },
        { MessageId::ReindexDefaultCdxText, "en-US", "REINDEX default -> CDX (v64-like table, via BUILDLMDB)" },
        { MessageId::ReindexDefaultCdxText, "es", "REINDEX predeterminado -> CDX (tabla tipo v64, vía BUILDLMDB)" },
        { MessageId::ReindexDefaultCdxText, "fr", "REINDEX par défaut -> CDX (table de type v64, via BUILDLMDB)" },
        { MessageId::ReindexDefaultCdxText, "de", "REINDEX Standard -> CDX (v64-ähnliche Tabelle, über BUILDLMDB)" },
        { MessageId::ReindexDefaultCdxText, "it", "REINDEX predefinito -> CDX (tabella tipo v64, tramite BUILDLMDB)" },
        { MessageId::ReindexDefaultInxText, "en-US", "REINDEX default -> INX (v32-like table)" },
        { MessageId::ReindexDefaultInxText, "es", "REINDEX predeterminado -> INX (tabla tipo v32)" },
        { MessageId::ReindexDefaultInxText, "fr", "REINDEX par défaut -> INX (table de type v32)" },
        { MessageId::ReindexDefaultInxText, "de", "REINDEX Standard -> INX (v32-ähnliche Tabelle)" },
        { MessageId::ReindexDefaultInxText, "it", "REINDEX predefinito -> INX (tabella tipo v32)" },
        { MessageId::ReindexCnxBannerText, "en-US", "REINDEX CNX" },
        { MessageId::ReindexCnxBannerText, "es", "REINDEX CNX" },
        { MessageId::ReindexCnxBannerText, "fr", "REINDEX CNX" },
        { MessageId::ReindexCnxBannerText, "de", "REINDEX CNX" },
        { MessageId::ReindexCnxBannerText, "it", "REINDEX CNX" },
        { MessageId::ReindexCdxBuildlmdbText, "en-US", "REINDEX CDX -> BUILDLMDB" },
        { MessageId::ReindexCdxBuildlmdbText, "es", "REINDEX CDX -> BUILDLMDB" },
        { MessageId::ReindexCdxBuildlmdbText, "fr", "REINDEX CDX -> BUILDLMDB" },
        { MessageId::ReindexCdxBuildlmdbText, "de", "REINDEX CDX -> BUILDLMDB" },
        { MessageId::ReindexCdxBuildlmdbText, "it", "REINDEX CDX -> BUILDLMDB" },
        { MessageId::ExportFunctionsUsageText, "en-US", "Usage:\n  EXPORTFUNCTIONS\n  EXPORTFUNCTIONS USAGE\n  EXPORTFUNCTIONS MD\n  EXPORTFUNCTIONS MD <path>\n  EXPORTFUNCTIONS <path>\n\nDefault output:\n  ./data/docs/functions.md\n" },
        { MessageId::ExportFunctionsUsageText, "es", "Uso:\n  EXPORTFUNCTIONS\n  EXPORTFUNCTIONS USAGE\n  EXPORTFUNCTIONS MD\n  EXPORTFUNCTIONS MD <path>\n  EXPORTFUNCTIONS <path>\n\nSalida predeterminada:\n  ./data/docs/functions.md\n" },
        { MessageId::ExportFunctionsUsageText, "fr", "Utilisation :\n  EXPORTFUNCTIONS\n  EXPORTFUNCTIONS USAGE\n  EXPORTFUNCTIONS MD\n  EXPORTFUNCTIONS MD <path>\n  EXPORTFUNCTIONS <path>\n\nSortie par défaut :\n  ./data/docs/functions.md\n" },
        { MessageId::ExportFunctionsUsageText, "de", "Verwendung:\n  EXPORTFUNCTIONS\n  EXPORTFUNCTIONS USAGE\n  EXPORTFUNCTIONS MD\n  EXPORTFUNCTIONS MD <path>\n  EXPORTFUNCTIONS <path>\n\nStandardausgabe:\n  ./data/docs/functions.md\n" },
        { MessageId::ExportFunctionsUsageText, "it", "Uso:\n  EXPORTFUNCTIONS\n  EXPORTFUNCTIONS USAGE\n  EXPORTFUNCTIONS MD\n  EXPORTFUNCTIONS MD <path>\n  EXPORTFUNCTIONS <path>\n\nOutput predefinito:\n  ./data/docs/functions.md\n" },
        { MessageId::ExportFunctionsUnsupportedFormatText, "en-US", "Unsupported format: {format}" },
        { MessageId::ExportFunctionsUnsupportedFormatText, "es", "Formato no admitido: {format}" },
        { MessageId::ExportFunctionsUnsupportedFormatText, "fr", "Format non pris en charge : {format}" },
        { MessageId::ExportFunctionsUnsupportedFormatText, "de", "Nicht unterstütztes Format: {format}" },
        { MessageId::ExportFunctionsUnsupportedFormatText, "it", "Formato non supportato: {format}" },
        { MessageId::ExportFunctionsFailedText, "en-US", "EXPORTFUNCTIONS failed: {detail}" },
        { MessageId::ExportFunctionsFailedText, "es", "EXPORTFUNCTIONS falló: {detail}" },
        { MessageId::ExportFunctionsFailedText, "fr", "EXPORTFUNCTIONS a échoué : {detail}" },
        { MessageId::ExportFunctionsFailedText, "de", "EXPORTFUNCTIONS fehlgeschlagen: {detail}" },
        { MessageId::ExportFunctionsFailedText, "it", "EXPORTFUNCTIONS non riuscito: {detail}" },
        { MessageId::ExportFunctionsExportedText, "en-US", "Function reference exported to: {path}" },
        { MessageId::ExportFunctionsExportedText, "es", "Referencia de funciones exportada a: {path}" },
        { MessageId::ExportFunctionsExportedText, "fr", "Référence des fonctions exportée vers : {path}" },
        { MessageId::ExportFunctionsExportedText, "de", "Funktionsreferenz exportiert nach: {path}" },
        { MessageId::ExportFunctionsExportedText, "it", "Riferimento delle funzioni esportato in: {path}" },
        { MessageId::IndexseekUsageText, "en-US", "Usage:\n  INDEXSEEK USAGE\n  INDEXSEEK <value>\n  INDEXSEEK <value> SOFT\n  INDEXSEEK <value> TAG <tag-or-path>\n  INDEXSEEK <value> SOFT TAG <tag-or-path>\nExamples:\n  INDEXSEEK \"TAYLOR\"\n  INDEXSEEK \"TAYLOR\" SOFT\n  INDEXSEEK \"TAYLOR\" TAG students.cdx\nNotes:\n  - INDEXSEEK prints INDEXSEEK(): <recno> and restores the cursor best-effort.\n  - INDEXSEEK USAGE works without an open table.\n" },
        { MessageId::IndexseekUsageText, "es", "Uso:\n  INDEXSEEK USAGE\n  INDEXSEEK <value>\n  INDEXSEEK <value> SOFT\n  INDEXSEEK <value> TAG <tag-or-path>\n  INDEXSEEK <value> SOFT TAG <tag-or-path>\nEjemplos:\n  INDEXSEEK \"TAYLOR\"\n  INDEXSEEK \"TAYLOR\" SOFT\n  INDEXSEEK \"TAYLOR\" TAG students.cdx\nNotas:\n  - INDEXSEEK imprime INDEXSEEK(): <recno> y restaura el cursor en la medida de lo posible.\n  - INDEXSEEK USAGE funciona sin una tabla abierta.\n" },
        { MessageId::IndexseekUsageText, "fr", "Utilisation :\n  INDEXSEEK USAGE\n  INDEXSEEK <value>\n  INDEXSEEK <value> SOFT\n  INDEXSEEK <value> TAG <tag-or-path>\n  INDEXSEEK <value> SOFT TAG <tag-or-path>\nExemples :\n  INDEXSEEK \"TAYLOR\"\n  INDEXSEEK \"TAYLOR\" SOFT\n  INDEXSEEK \"TAYLOR\" TAG students.cdx\nRemarques :\n  - INDEXSEEK affiche INDEXSEEK(): <recno> et restaure le curseur au mieux.\n  - INDEXSEEK USAGE fonctionne sans table ouverte.\n" },
        { MessageId::IndexseekUsageText, "de", "Verwendung:\n  INDEXSEEK USAGE\n  INDEXSEEK <value>\n  INDEXSEEK <value> SOFT\n  INDEXSEEK <value> TAG <tag-or-path>\n  INDEXSEEK <value> SOFT TAG <tag-or-path>\nBeispiele:\n  INDEXSEEK \"TAYLOR\"\n  INDEXSEEK \"TAYLOR\" SOFT\n  INDEXSEEK \"TAYLOR\" TAG students.cdx\nHinweise:\n  - INDEXSEEK gibt INDEXSEEK(): <recno> aus und stellt den Cursor bestmöglich wieder her.\n  - INDEXSEEK USAGE funktioniert ohne geöffnete Tabelle.\n" },
        { MessageId::IndexseekUsageText, "it", "Uso:\n  INDEXSEEK USAGE\n  INDEXSEEK <value>\n  INDEXSEEK <value> SOFT\n  INDEXSEEK <value> TAG <tag-or-path>\n  INDEXSEEK <value> SOFT TAG <tag-or-path>\nEsempi:\n  INDEXSEEK \"TAYLOR\"\n  INDEXSEEK \"TAYLOR\" SOFT\n  INDEXSEEK \"TAYLOR\" TAG students.cdx\nNote:\n  - INDEXSEEK stampa INDEXSEEK(): <recno> e ripristina il cursore per quanto possibile.\n  - INDEXSEEK USAGE funziona senza una tabella aperta.\n" },
        { MessageId::ScxUsageText, "en-US", "Usage:\n  SCX USAGE\n  SCX CREATE <file>\n  SCX ADDTAG <file> <name> FIELD <n> [DESC]\n  SCX BUILD <file>\n  SCX TAGS <file>\n  SCX INFO <file>" },
        { MessageId::ScxUsageText, "es", "Uso:\n  SCX USAGE\n  SCX CREATE <file>\n  SCX ADDTAG <file> <name> FIELD <n> [DESC]\n  SCX BUILD <file>\n  SCX TAGS <file>\n  SCX INFO <file>" },
        { MessageId::ScxUsageText, "fr", "Utilisation :\n  SCX USAGE\n  SCX CREATE <file>\n  SCX ADDTAG <file> <name> FIELD <n> [DESC]\n  SCX BUILD <file>\n  SCX TAGS <file>\n  SCX INFO <file>" },
        { MessageId::ScxUsageText, "de", "Verwendung:\n  SCX USAGE\n  SCX CREATE <file>\n  SCX ADDTAG <file> <name> FIELD <n> [DESC]\n  SCX BUILD <file>\n  SCX TAGS <file>\n  SCX INFO <file>" },
        { MessageId::ScxUsageText, "it", "Uso:\n  SCX USAGE\n  SCX CREATE <file>\n  SCX ADDTAG <file> <name> FIELD <n> [DESC]\n  SCX BUILD <file>\n  SCX TAGS <file>\n  SCX INFO <file>" },
        { MessageId::ScxCreateUsageText, "en-US", "Usage: SCX CREATE <file>" },
        { MessageId::ScxCreateUsageText, "es", "Uso: SCX CREATE <file>" },
        { MessageId::ScxCreateUsageText, "fr", "Utilisation : SCX CREATE <file>" },
        { MessageId::ScxCreateUsageText, "de", "Verwendung: SCX CREATE <file>" },
        { MessageId::ScxCreateUsageText, "it", "Uso: SCX CREATE <file>" },
        { MessageId::ScxAddtagUsageText, "en-US", "Usage: SCX ADDTAG <file> <name> FIELD <n> [DESC]" },
        { MessageId::ScxAddtagUsageText, "es", "Uso: SCX ADDTAG <file> <name> FIELD <n> [DESC]" },
        { MessageId::ScxAddtagUsageText, "fr", "Utilisation : SCX ADDTAG <file> <name> FIELD <n> [DESC]" },
        { MessageId::ScxAddtagUsageText, "de", "Verwendung: SCX ADDTAG <file> <name> FIELD <n> [DESC]" },
        { MessageId::ScxAddtagUsageText, "it", "Uso: SCX ADDTAG <file> <name> FIELD <n> [DESC]" },
        { MessageId::ScxBuildUsageText, "en-US", "Usage: SCX BUILD <file>" },
        { MessageId::ScxBuildUsageText, "es", "Uso: SCX BUILD <file>" },
        { MessageId::ScxBuildUsageText, "fr", "Utilisation : SCX BUILD <file>" },
        { MessageId::ScxBuildUsageText, "de", "Verwendung: SCX BUILD <file>" },
        { MessageId::ScxBuildUsageText, "it", "Uso: SCX BUILD <file>" },
        { MessageId::ScxTagsUsageText, "en-US", "Usage: SCX TAGS <file>" },
        { MessageId::ScxTagsUsageText, "es", "Uso: SCX TAGS <file>" },
        { MessageId::ScxTagsUsageText, "fr", "Utilisation : SCX TAGS <file>" },
        { MessageId::ScxTagsUsageText, "de", "Verwendung: SCX TAGS <file>" },
        { MessageId::ScxTagsUsageText, "it", "Uso: SCX TAGS <file>" },
        { MessageId::ScxInfoUsageText, "en-US", "Usage: SCX INFO <file>" },
        { MessageId::ScxInfoUsageText, "es", "Uso: SCX INFO <file>" },
        { MessageId::ScxInfoUsageText, "fr", "Utilisation : SCX INFO <file>" },
        { MessageId::ScxInfoUsageText, "de", "Verwendung: SCX INFO <file>" },
        { MessageId::ScxInfoUsageText, "it", "Uso: SCX INFO <file>" },
        { MessageId::ScxDetailText, "en-US", "{detail}" },
        { MessageId::ScxDetailText, "es", "{detail}" },
        { MessageId::ScxDetailText, "fr", "{detail}" },
        { MessageId::ScxDetailText, "de", "{detail}" },
        { MessageId::ScxDetailText, "it", "{detail}" },
        { MessageId::ScxCreateWroteText, "en-US", "wrote {file}" },
        { MessageId::ScxCreateWroteText, "es", "escrito {file}" },
        { MessageId::ScxCreateWroteText, "fr", "écrit {file}" },
        { MessageId::ScxCreateWroteText, "de", "{file} geschrieben" },
        { MessageId::ScxCreateWroteText, "it", "scritto {file}" },
        { MessageId::ScxAddtagAddedText, "en-US", "added '{name}'" },
        { MessageId::ScxAddtagAddedText, "es", "agregado '{name}'" },
        { MessageId::ScxAddtagAddedText, "fr", "'{name}' ajouté" },
        { MessageId::ScxAddtagAddedText, "de", "'{name}' hinzugefügt" },
        { MessageId::ScxAddtagAddedText, "it", "aggiunto '{name}'" },
        { MessageId::ScxBuildDoneText, "en-US", "done {file}" },
        { MessageId::ScxBuildDoneText, "es", "listo {file}" },
        { MessageId::ScxBuildDoneText, "fr", "terminé {file}" },
        { MessageId::ScxBuildDoneText, "de", "fertig {file}" },
        { MessageId::ScxBuildDoneText, "it", "fatto {file}" },
        { MessageId::ScxUnknownSubText, "en-US", "unknown subcommand: {sub}" },
        { MessageId::ScxUnknownSubText, "es", "subcomando desconocido: {sub}" },
        { MessageId::ScxUnknownSubText, "fr", "sous-commande inconnue : {sub}" },
        { MessageId::ScxUnknownSubText, "de", "unbekannter Unterbefehl: {sub}" },
        { MessageId::ScxUnknownSubText, "it", "sottocomando sconosciuto: {sub}" },
        { MessageId::ReplaceMultiUsageText, "en-US", "Usage:\n  MULTIREP USAGE\n  MULTIREP <field> WITH <value>[, <field> WITH <value>]...\nExamples:\n  MULTIREP LNAME WITH \"Smith\", FNAME WITH \"John\"\n  MULTIREP DOB WITH 20000101, ACTIVE WITH .T.\nNotes:\n  - MULTIREP requires an open table and a current record.\n  - All assignments are validated before the physical write.\n  - MULTIREP uses one record lock and one DBF write.\n  - Memo fields are written through the memo backend.\n  - Direct index maintenance uses before/after snapshots.\n  - Changed fields are marked STALE only if index maintenance fails." },
        { MessageId::ReplaceMultiExpectedFieldAfterFieldText, "en-US", "expected field after FIELD." },
        { MessageId::ReplaceMultiExpectedWithAfterFieldText, "en-US", "expected WITH after field." },
        { MessageId::ReplaceMultiEmptyValueText, "en-US", "empty value." },
        { MessageId::ReplaceMultiInvalidFieldTokenText, "en-US", "invalid field token '{field}'." },
        { MessageId::ReplaceMultiUnknownFieldText, "en-US", "unknown field '{field}'." },
        { MessageId::ReplaceMultiNoAssignmentsText, "en-US", "no assignments." },
        { MessageId::ReplaceMultiNoFileOpenText, "en-US", "no file open." },
        { MessageId::ReplaceMultiNoCurrentRecordText, "en-US", "no current record." },
        { MessageId::ReplaceMultiRecordLockedText, "en-US", "record is locked ({detail})." },
        { MessageId::ReplaceMultiInvalidDateForFieldText, "en-US", "invalid date for field." },
        { MessageId::ReplaceMultiInvalidLogicalForFieldText, "en-US", "invalid logical for field." },
        { MessageId::ReplaceMultiInvalidNumericForFieldText, "en-US", "invalid numeric for field." },
        { MessageId::ReplaceMultiInvalidFloatForFieldText, "en-US", "invalid float for field." },
        { MessageId::ReplaceMultiInvalidInt32ForFieldText, "en-US", "invalid int32 for field." },
        { MessageId::ReplaceMultiInvalidDoubleForFieldText, "en-US", "invalid double for field." },
        { MessageId::ReplaceMultiInvalidCurrencyForFieldText, "en-US", "invalid currency for field." },
        { MessageId::ReplaceMultiDetailText, "en-US", "{detail}" },
        { MessageId::ReplaceMultiMemoBackendNotAttachedText, "en-US", "memo backend not attached." },
        { MessageId::ReplaceMultiMemoWriteFailedText, "en-US", "memo write failed{detail}" },
        { MessageId::ReplaceMultiStoreMemoTokenFailedText, "en-US", "failed to store memo token in DBF field." },
        { MessageId::ReplaceMultiFieldSetFailedText, "en-US", "field set failed." },
        { MessageId::ReplaceMultiExceptionDuringWriteText, "en-US", "exception during write." },
        { MessageId::ReplaceMultiWriteFailedText, "en-US", "write failed." },
        { MessageId::ReplaceMultiUpdatedFieldsText, "en-US", "updated {count} field(s)." },
        { MessageId::UnsupportedMessageLocale, "en-US", "Unsupported message locale: {locale}" },
        { MessageId::UnknownCommand,        "en-US", "Unknown command: {command}" },
        { MessageId::MacroUndefinedVariable, "en-US", "MACRO: undefined variable: {name}" },
        { MessageId::MissingArgument,       "en-US", "Missing required argument." },
        { MessageId::TooManyArguments,      "en-US", "Too many arguments." },
        { MessageId::InvalidSyntax,         "en-US", "Invalid command syntax." },
        { MessageId::InvalidOption,         "en-US", "Invalid option: {option}" },
        { MessageId::CommandNotImplemented, "en-US", "Command is recognized but not implemented: {command}" },
        { MessageId::CommandDeprecated,     "en-US", "Command is deprecated: {command}" },
        { MessageId::GlobalUsageTitle,      "en-US", "Usage:" },
        { MessageId::GlobalSyntaxTitle,     "en-US", "Syntax:" },
        { MessageId::GlobalExamplesTitle,   "en-US", "Examples:" },
        { MessageId::GlobalDirectAliasTitle, "en-US", "Direct alias:" },
        { MessageId::GlobalDefaultsTitle,   "en-US", "Defaults:" },
        { MessageId::GlobalNotesTitle,      "en-US", "Notes:" },
        { MessageId::GlobalWarningsTitle,   "en-US", "Warnings:" },
        { MessageId::GlobalCategoryLine,    "en-US", "Category: {value}" },
        { MessageId::GlobalArgumentsLine,   "en-US", "Arguments: {min}..{max}" },
        { MessageId::GlobalAliasesLine,     "en-US", "Aliases: {value}" },
        { MessageId::GlobalSubcommandsTitle, "en-US", "Subcommands:" },
        { MessageId::GlobalDevTransitionalTitle, "en-US", "Dev / Transitional:" },
        { MessageId::GlobalFunctionFallbackSyntaxLine, "en-US", "  {name}(...)" },
        { MessageId::NoOpenTable,           "en-US", "No table is currently open." },
        { MessageId::NoSelectedArea,        "en-US", "No current work area is selected." },
        { MessageId::NoActiveIndex,         "en-US", "No active index." },
        { MessageId::FindFoundText,         "en-US", "Found." },
        { MessageId::FindNotFoundText,      "en-US", "Not found." },
        { MessageId::SeekEmptyText,         "en-US", "(empty)" },
        { MessageId::SmartlistUsageText,    "en-US", "Usage:\n  SMARTLIST\n  SMARTLIST USAGE\n  SMARTLIST <fields>\n  SMARTLIST ALL\n  SMARTLIST <limit>\n  SMARTLIST NEXT <n>\n  SMARTLIST FIRST <n>\n  SMARTLIST DELETED\n  SMARTLIST DEBUG\n  SMARTLIST TUPLES\n  SMARTLIST FOR <pred>" },
        { MessageId::SmartlistUnknownProjectionFieldText, "en-US", "unknown projection field '{field}'; using full row." },
        { MessageId::SeekTraceStatusText,   "en-US", "SEEK TRACE is {state}." },
        { MessageId::SeekUnknownFieldText,  "en-US", "unknown field: {field}" },
        { MessageId::SeekFoundAtText,       "en-US", "Found at {recno}." },
        { MessageId::SeekNearMatchAtText,   "en-US", "Near match at {recno}." },
        { MessageId::SeekNotFoundText,      "en-US", "Not found." },
        { MessageId::AscendUsageText,       "en-US", "Usage:\n  ASCEND\n  ASCEND USAGE\n" },
        { MessageId::OrderAscendingSet,     "en-US", "Order: ASCENDING." },
        { MessageId::AreaUsageReadOnlyNote, "en-US", "AREA is read-only; it reports the current area slot/file/order state." },
        { MessageId::AreaCurrentAreaLine,   "en-US", "Current area: {index} of {occupied}" },
        { MessageId::AreaCurrentAreaUnknownLine, "en-US", "Current area: (unknown)" },
        { MessageId::AreaNoFileOpenLine,    "en-US", "  (no file open in Area)" },
        { MessageId::AreaFileSummaryLine,   "en-US", "  File: {label}  Recs: {recs}  Recno: {recno}" },
        { MessageId::AreaDbfAbsoluteLine,   "en-US", "  DBF (abs)           : {value}" },
        { MessageId::AreaDbfFlavorLine,     "en-US", "  DBF Flavor          : {value}" },
        { MessageId::AreaRuntimeKindLine,   "en-US", "  Runtime kind        : {value}" },
        { MessageId::AreaLogicalNameLine,   "en-US", "  Logical name        : {value}" },
        { MessageId::AreaLegacyNameLine,    "en-US", "  Legacy name()       : {value}" },
        { MessageId::AreaPathLine,          "en-US", "  Path: {value}" },
        { MessageId::StatusUsageText,       "en-US", "Usage:\n  STATUS                 (Report current work-area status)\n  STATUS USAGE           (Show this usage)\n  STATUS ALL             (Report all open work areas)\n  STATUS VERBOSE         (Include field structure for current area)\n  STATUS ALL VERBOSE     (Report all open areas with field structure)\nNotes:\n  - STATUS is read-only; it reports work-area/index state.\n" },
        { MessageId::StatusAreaHeaderLine,  "en-US", "Area {slot}: {path}  ({base}){current}" },
        { MessageId::StatusWorkspaceLine,   "en-US", "Workspace : {value}" },
        { MessageId::StatusDbfFlavorLine,   "en-US", "  DBF Flavor   : {value}" },
        { MessageId::StatusTagsSummaryLine, "en-US", "  Tags        : {value}" },
        { MessageId::StatusTagsTitle,       "en-US", "  Tags" },
        { MessageId::StatusTagColumnHeaderText, "en-US", "  Field Name    Type    Len   Dec   Dir" },
        { MessageId::StatusTagDividerText,  "en-US", "  ------------ ------- ------ ------ ----" },
        { MessageId::StatusRecordsLine,     "en-US", "  Records     : {value}" },
        { MessageId::StatusLmdbClosedLine,  "en-US", "  LMDB        : (closed)" },
        { MessageId::StatusLmdbEnvLine,     "en-US", "  LMDB        : envdir={envdir}{tag_clause}" },
        { MessageId::StatusFieldsTitle,     "en-US", "Fields ({count})" },
        { MessageId::StatusFieldColumnHeaderText, "en-US", "  #  Name        Type  Len   Dec" },
        { MessageId::StatusOrderPhysicalLine, "en-US", "Order       : PHYSICAL" },
        { MessageId::StructUsageText,       "en-US", "Usage:\n  STRUCT                 (Current area fields + index info)\n  STRUCT USAGE           (Show this usage)\n  STRUCT INDEX           (Explicit index info mode; default)\n  STRUCT FIELDS          (Fields only)\n  STRUCT ALL             (All open areas)\n  STRUCT ALL INDEX       (All open areas + index info)\n  STRUCT ALL VERBOSE     (All open areas + verbose CNX tag info)\nNotes:\n  - STRUCT is read-only; it reports DBF structure/index metadata.\n" },
        { MessageId::StructNoEngineText,    "en-US", "No engine available." },
        { MessageId::StructNoOpenAreasText, "en-US", "No open areas." },
        { MessageId::StructNoFileOpenCurrentAreaText, "en-US", "No file open in current area." },
        { MessageId::StructAreaHeaderLine,  "en-US", "Area {slot}: {path}  ({base})" },
        { MessageId::StructFieldsTitle,     "en-US", "Fields ({count})" },
        { MessageId::StructFieldColumnHeaderText, "en-US", "  #  Name          Type   Len   Dec" },
        { MessageId::StructDbfileLine,      "en-US", "Dbfile      : {path}  ({base})" },
        { MessageId::StructIndexFileLine,   "en-US", "Index file  : {value}" },
        { MessageId::StructTagsSummaryLine, "en-US", "Tags        : {value}" },
        { MessageId::StructActiveTagLine,   "en-US", "Active tag  : {value}" },
        { MessageId::StructCnxTagsVerboseTitle, "en-US", "CNX Tags (verbose)" },
        { MessageId::StructCnxMarksActiveNote, "en-US", "  * marks active" },
        { MessageId::StructVerboseCnxColumnHeaderText, "en-US", "    Tag             Expression" },
        { MessageId::DbareaUsageText,       "en-US", "Usage:\n  DBAREA\n  DBAREA USAGE\nNotes:\n  - DBAREA is read-only; it reports the current work-area summary.\n" },
        { MessageId::DbareaNoTableOpenText, "en-US", "DBAREA: no table open." },
        { MessageId::DbareaBannerTitle,     "en-US", "DBAREA - Current Work Area Summary" },
        { MessageId::DbareaBannerDividerText, "en-US", "============================================================" },
        { MessageId::DbareaAreaSlotLineText, "en-US", "Area (slot)" },
        { MessageId::DbareaDbfAbsoluteLineText, "en-US", "DBF (abs)" },
        { MessageId::DbareaLogicalNameLineText, "en-US", "Logical name" },
        { MessageId::DbareaLegacyNameLineText, "en-US", "Legacy name()" },
        { MessageId::DbareaRecordsLineText, "en-US", "Records" },
        { MessageId::DbareaRecordLengthLineText, "en-US", "Record length" },
        { MessageId::DbareaRecordLengthMethodLineText, "en-US", "recordLength()" },
        { MessageId::DbareaFieldsCountLineText, "en-US", "Fields" },
        { MessageId::DbareaRecnoLineText, "en-US", "Recno" },
        { MessageId::DbareaDeletedFlagLineText, "en-US", "Deleted flag" },
        { MessageId::DbareaIndexOrderTitle, "en-US", "Index / Order" },
        { MessageId::DbareaSectionDividerText, "en-US", "-------------" },
        { MessageId::DbareaIndexFileLineText, "en-US", "Index file" },
        { MessageId::DbareaFieldsTitle,     "en-US", "Fields" },
        { MessageId::DbareaFieldsNoneText,  "en-US", "(none)" },
        { MessageId::DbareaFieldColumnHeaderText, "en-US", "#    Name              Type      Len     Dec" },
        { MessageId::DbareaFieldDividerText, "en-US", "-------------------------------------------------" },
        { MessageId::DbareasUsageText,      "en-US", "Usage:\n  DBAREAS\n  DBAREAS USAGE\n  DBAREAS <n>\n  DBAREAS ALL\n  DBAREAS REL\nNotes:\n  - DBAREAS with no arguments reports the current area by delegating to DBAREA.\n  - DBAREAS <n> reports slot n when that slot is open.\n  - DBAREAS ALL reports all open slots using filename() as the open-area truth.\n  - DBAREAS REL reports the current area and appends relation summary/tree context.\n  - DBAREAS is read-only; it reports session/work-area state and does not mutate table data.\n" },
        { MessageId::DbareasNoOpenWorkAreasText, "en-US", "DBAREAS: no open work areas." },
        { MessageId::DbareasSlotOutOfRangeText, "en-US", "DBAREAS: slot out of range: {slot} (0..{max})" },
        { MessageId::DbareasAreaNotOpenText, "en-US", "DBAREAS: area {slot} is not open." },
        { MessageId::DbareasRelationsModuleMissingText, "en-US", "Relations: (module not present)" },
        { MessageId::DbareasRelationsTitleText, "en-US", "Relations" },
        { MessageId::DbareasRelationsDividerText, "en-US", "---------" },
        { MessageId::DbareasParentAnchorLineText, "en-US", "Parent anchor        : {value}" },
        { MessageId::DbareasChildrenNoneText, "en-US", "Children             : (none configured)" },
        { MessageId::DbareasChildrenDirectTitleText, "en-US", "Children (direct)" },
        { MessageId::DbareasChildMatchLineText, "en-US", "  -> {child}  (matches: {count})" },
        { MessageId::DbareasRelationTreeTitleText, "en-US", "Relation tree" },
        { MessageId::DbareasRelationTreeDividerText, "en-US", "-------------" },
        { MessageId::FieldsUsageText,       "en-US", "Usage:\n  FIELDS\n  FIELDS USAGE\nNotes:\n  - Reports field number, name, type, length, and decimals for the current area.\n  - FIELDS is read-only.\n" },
        { MessageId::FieldsNoFieldsText,    "en-US", "(No fields)" },
        { MessageId::FieldsColumnHeaderText, "en-US", "# Name Type Len Dec" },
        { MessageId::FieldsDividerText,     "en-US", "- ---- ---- --- ---" },
        { MessageId::DescendUsageText,      "en-US", "Usage:\n  DESCEND\n  DESCEND USAGE\n" },
        { MessageId::OrderDescendingSet,    "en-US", "Order: DESCENDING." },
        { MessageId::ColorUsageText,        "en-US", "Usage:\n  COLOR\n  COLOR USAGE\n  COLOR DEFAULT\n  COLOR GREEN\n  COLOR AMBER\n  COLOR TREE ON\n  COLOR TREE OFF\n  COLOR TREECOLOR ON\n  COLOR TREECOLOR OFF\nNotes:\n  - COLOR with no arguments reports current theme and tree palette state.\n  - COLOR TREE/TREECOLOR toggles tree-color behavior.\n" },
        { MessageId::ColorStatusText,       "en-US", "COLOR is {value}" },
        { MessageId::ColorTreeColorStatusText, "en-US", "TREECOLOR is {value}" },
        { MessageId::ColorTreePaletteHeaderText, "en-US", "TREE palette rotates across {count} levels:" },
        { MessageId::ColorTreeLevelLineText, "en-US", "  Level {level}: {value}" },
        { MessageId::ColorTreeSetStatusText, "en-US", "TREECOLOR set to {value}" },
        { MessageId::ColorSetStatusText,    "en-US", "COLOR set to {value}" },
        { MessageId::ValidateUsageText,     "en-US", "Usage:\n  VALIDATE USAGE\n  VALIDATE UNIQUE USAGE\n  VALIDATE UNIQUE FIELD <name> [IGNORE DELETED] [REPAIR] [REPORT TO <path>]\nExamples:\n  VALIDATE UNIQUE FIELD SID\n  VALIDATE UNIQUE FIELD EMAIL IGNORE DELETED\n  VALIDATE UNIQUE FIELD SID REPAIR\n  VALIDATE UNIQUE FIELD SID REPORT TO tmp\\sid_dupes.txt\nNotes:\n  - REPAIR may mutate field values; use it intentionally.\n" },
        { MessageId::ValidateUnknownSubcommandText, "en-US", "VALIDATE: unknown subcommand '{command}'." },
        { MessageId::DotHelpUsageText,      "en-US", "Usage:\n  DOTHELP\n  DOTHELP USAGE\n  DOTHELP <term>\n  HELP /DOT <term>\n" },
        { MessageId::DotHelpTitleText,      "en-US", "DOTTALK REFERENCE" },
        { MessageId::DotHelpSubtitleText,   "en-US", "Project-native commands and subsystems" },
        { MessageId::DotHelpSearchUsageText, "en-US", "Usage:\n  DOTHELP <term>\n  HELP /DOT <term>" },
        { MessageId::DotHelpMatchesTitleText, "en-US", "Matching DotTalk helpers:" },
        { MessageId::DotHelpNoTopicText,    "en-US", "No DotTalk help found for: {command}" },
        { MessageId::DotHelpTryHelpHintText, "en-US", "Try HELP /DOT <term> or plain HELP <term>." },
        { MessageId::DotHelpUnsupportedNoteText, "en-US", "  (documented, but not fully supported yet)" },
        { MessageId::FoxHelpUsageText,      "en-US", "Usage:\n  FOXHELP\n  FOXHELP USAGE\n  FOXHELP <name>\n  FOXHELP <search>\n  FH\n  FH <name>\n  FH <search>\nNotes:\n  - FOXHELP with no arguments lists the FoxPro-style command subset.\n  - FH is a short alias for FOXHELP.\n" },
        { MessageId::FoxHelpSubsetTitleText, "en-US", "FoxPro-style commands (subset):" },
        { MessageId::FoxHelpTipText,        "en-US", "Tip: FOXHELP <NAME> for details, e.g. FOXHELP INDEX" },
        { MessageId::FoxHelpMatchesTitleText, "en-US", "Matches for \"{command}\":" },
        { MessageId::FoxHelpNoTopicText,    "en-US", "No help found for: {command}" },
        { MessageId::FoxHelpTryListHintText, "en-US", "Try FOXHELP (no args) to list commands." },
        { MessageId::FoxHelpUnsupportedSuffixText, "en-US", "[unsupported]" },
        { MessageId::FoxStandardUsageText,  "en-US", "Usage:\n  FOXSTANDARD USAGE\n  FOXSTANDARD <command>\n  FOXSTANDARD ALL\n  FOXSTANDARD TOPICS\n  FOXSTANDARD LIST" },
        { MessageId::PshellUsageText,       "en-US", "Usage:\n  PSHELL\n  PSHELL USAGE\n  PSHELL LIST-CATEGORIES\n  PSHELL <category>\n  PSHELL <term>\nExamples:\n  PSHELL PYTHON\n  PSHELL PY-VENV-CREATE\n  PSHELL CLEAN\nNotes:\n  - PSHELL is a read-only reference command; it does not execute PowerShell.\n" },
        { MessageId::AppendUsageBlankNoArgsNote, "en-US", "APPEND with no arguments appends one blank record." },
        { MessageId::AppendUsageManySmartNote, "en-US", "APPEND MANY uses the smart batch append path." },
        { MessageId::AppendUsageRawNoInlineIndexNote, "en-US", "APPEND RAW uses the raw append path without inline index update." },
        { MessageId::AppendUsageRawManyLine, "en-US", "Usage: APPEND RAW MANY <count>" },
        { MessageId::AppendUsageRawSummaryLine, "en-US", "Usage: APPEND RAW | APPEND RAW MANY <count>" },
        { MessageId::AppendUsageManyLine,   "en-US", "Usage: APPEND MANY <count>" },
        { MessageId::AppendInvalidCount,    "en-US", "invalid count '{value}'" },
        { MessageId::AppendTableLocked,     "en-US", "table locked ({detail})" },
        { MessageId::AppendManyStopped,     "en-US", "MANY stopped after {count} successful append(s)" },
        { MessageId::AppendFailed,          "en-US", "append failed" },
        { MessageId::AppendRawManyStopped,  "en-US", "RAW MANY stopped after {count} successful append(s)" },
        { MessageId::AppendManySuccess,     "en-US", "Appended {count} blank record(s)" },
        { MessageId::AppendRawManySuccess,  "en-US", "Appended {count} raw blank record(s)" },
        { MessageId::AppendBlankSuccess,    "en-US", "Appended blank record {recno}" },
        { MessageId::AppendBlankUsageSharedNote, "en-US", "Appends one blank record through shared append support." },
        { MessageId::SetVarUsageLine,       "en-US", "Usage: SET VAR <name> = <text>" },
        { MessageId::ShowVarUsageLine,      "en-US", "Usage: SHOW VAR [<name>]" },
        { MessageId::ClearVarUsageLine,     "en-US", "Usage: CLEAR VAR <name|ALL>" },
        { MessageId::VarInvalidName,        "en-US", "invalid name: {name}" },
        { MessageId::VarBangEvalError,      "en-US", "{detail}" },
        { MessageId::VarsDefinedCount,      "en-US", "VARS: {count} defined." },
        { MessageId::VarNotDefined,         "en-US", "VAR not defined: {name}" },
        { MessageId::VarCommandUsageLine,   "en-US", "Usage: SET VAR | SHOW VAR | CLEAR VAR" },
        { MessageId::AggsFamilyTitle,       "en-US", "Aggregate verbs owned by AGGS" },
        { MessageId::AggsDirectVerbsTitle,  "en-US", "Direct aggregate verbs:" },
        { MessageId::AggUsageHeading,       "en-US", "usage:" },
        { MessageId::AggErrorDetail,        "en-US", "error: {detail}" },
        { MessageId::AggsOwnerNote,         "en-US", "AGGS owns the usage/help contract for these aggregate verbs." },
        { MessageId::AggsDirectAliasNote,   "en-US", "Direct SUM, AVG, MIN, and MAX are command aliases for normal use." },
        { MessageId::AggsForWhereAcceptedNote, "en-US", "FOR and WHERE are both accepted predicate introducers." },
        { MessageId::AggsDeletedOnlyNote,   "en-US", "DELETED limits the aggregate to deleted records." },
        { MessageId::AggsNotDeletedOnlyNote, "en-US", "NOT DELETED and !DELETED limit the aggregate to visible/non-deleted records." },
        { MessageId::AggsCursorRestoreNote, "en-US", "Aggregate scans restore the cursor best-effort." },
        { MessageId::AggsReadOnlyNote,      "en-US", "Aggregates report values; they do not mutate table data." },
        { MessageId::AggUsageOwnerNote,     "en-US", "AGGS owns this usage contract." },
        { MessageId::AggUsageDirectVerbNote, "en-US", "{verb} is the direct aggregate verb for normal command-line use." },
        { MessageId::AggUsageReadOnlyNote,  "en-US", "This aggregate reports a value and does not mutate table data." },
        { MessageId::AutoDbfUsageLine,      "en-US", "AUTODBF <table> FROM <csvfile> [HEADER|NOHEADER|AUTO] [INFER|TEXTONLY] [OVERWRITE]" },
        { MessageId::AutoDbfUsageX64Line,   "en-US", "AUTODBF X64 <table> FROM <csvfile> [HEADER|NOHEADER|AUTO] [INFER|TEXTONLY] [OVERWRITE]" },
        { MessageId::AutoDbfDefaultFlavorNote, "en-US", "X64 table flavor" },
        { MessageId::AutoDbfDefaultHeaderNote, "en-US", "AUTO header detection, conservative" },
        { MessageId::AutoDbfDefaultInferNote, "en-US", "INFER field types" },
        { MessageId::AutoDbfDefaultOverwriteNote, "en-US", "no overwrite unless OVERWRITE is supplied" },
        { MessageId::AutoDbfCsvParserNote,  "en-US", "CSV parsing uses the existing comma CSV parser." },
        { MessageId::AutoDbfLongTextRejectedNote, "en-US", "Long text is rejected for now rather than auto-promoted to M." },
        { MessageId::AutoDbfHeaderNormalizeNote, "en-US", "Header names are normalized, uniquified, and sent through x64 fallback-name mangling." },
        { MessageId::AutoDbfMissingTableName, "en-US", "missing table name." },
        { MessageId::AutoDbfMissingTableNameAfterX64, "en-US", "missing table name after X64." },
        { MessageId::AutoDbfExpectedFrom,   "en-US", "expected FROM after table name." },
        { MessageId::AutoDbfMissingCsvFile, "en-US", "missing CSV file name after FROM." },
        { MessageId::AutoDbfMaxCharRequiresValue, "en-US", "MAXCHAR requires a value." },
        { MessageId::AutoDbfInvalidMaxCharValue, "en-US", "invalid MAXCHAR value." },
        { MessageId::AutoDbfMaxCharRange,   "en-US", "MAXCHAR must be between 1 and 254." },
        { MessageId::AutoDbfUnknownOption,  "en-US", "unknown option '{option}'." },
        { MessageId::AutoDbfCannotOpenRead, "en-US", "Cannot open {path} for read." },
        { MessageId::AutoDbfEmptyCsv,       "en-US", "Empty CSV." },
        { MessageId::AutoDbfColumnCountMismatch, "en-US", "column count mismatch" },
        { MessageId::AutoDbfTextWidthExceedsLimit, "en-US", "text width {width} exceeds current fixed-field limit {limit}" },
        { MessageId::AutoDbfLongTextRequiresBytes, "en-US", "long text requires {bytes} bytes; AUTODBF does not auto-promote to memo yet" },
        { MessageId::AutoDbfMemoInferenceDisabled, "en-US", "memo inference is disabled for AUTODBF first pass" },
        { MessageId::AutoDbfFieldWidthOutOfRange, "en-US", "field width {width} is outside current fixed-field limits" },
        { MessageId::AutoDbfDecimalCountInvalid, "en-US", "decimal count {decimals} is invalid for width {width}" },
        { MessageId::AutoDbfColumnDetail,   "en-US", "column {index} ({name}): {detail}" },
        { MessageId::AutoDbfCharacterWidthOverflow, "en-US", "character width overflow" },
        { MessageId::AutoDbfInvalidNumericValue, "en-US", "invalid numeric value" },
        { MessageId::AutoDbfNumericWidthOverflow, "en-US", "numeric width overflow" },
        { MessageId::AutoDbfInvalidDateValue, "en-US", "invalid date value; expected YYYY-MM-DD" },
        { MessageId::AutoDbfInvalidLogicalValue, "en-US", "invalid logical value" },
        { MessageId::AutoDbfUnsupportedFieldType, "en-US", "unsupported AUTODBF field type" },
        { MessageId::AutoDbfLineExpectedColumnsFound, "en-US", "line {line}: expected {expected} column(s), found {found}" },
        { MessageId::AutoDbfLineColumnDetail, "en-US", "line {line}, column {column} ({name}): {detail}" },
        { MessageId::AutoDbfAppendBlankFailed, "en-US", "line {line}: appendBlank failed" },
        { MessageId::AutoDbfSetFailed,      "en-US", "line {line}, column {column} ({name}): set failed" },
        { MessageId::AutoDbfWriteCurrentFailed, "en-US", "line {line}: writeCurrent failed" },
        { MessageId::AutoDbfPlanTitle,      "en-US", "AUTODBF plan" },
        { MessageId::AutoDbfPlanCsvLine,    "en-US", "  CSV: {path}" },
        { MessageId::AutoDbfPlanHeaderLine, "en-US", "  Header: {mode}{suffix}" },
        { MessageId::AutoDbfPlanDataRowsLine, "en-US", "  Data rows: {count}" },
        { MessageId::AutoDbfPlanColumnsLine, "en-US", "  Columns: {count}" },
        { MessageId::AutoDbfPlanDescriptorSuffix, "en-US", "  descriptor={name}" },
        { MessageId::AutoDbfPlanSourceSuffix, "en-US", "  source='{name}'" },
        { MessageId::AutoDbfTargetExists,   "en-US", "target exists: {path}" },
        { MessageId::AutoDbfUseOverwriteNote, "en-US", "Use OVERWRITE to replace it." },
        { MessageId::AutoDbfScanFailedAtLine, "en-US", "{detail} at line {line} (expected {expected}, found {found})" },
        { MessageId::AutoDbfNoDataRows,     "en-US", "no data rows found." },
        { MessageId::AutoDbfCreateFailed,   "en-US", "create failed: {detail}" },
        { MessageId::AutoDbfReopenFailedDetail, "en-US", "file written but could not reopen table: {detail}" },
        { MessageId::AutoDbfReopenFailedGeneric, "en-US", "file written but could not reopen table." },
        { MessageId::AutoDbfImportFailed,   "en-US", "failed during import: {detail}" },
        { MessageId::AutoDbfPartialRowsImported, "en-US", "  Partial rows imported: {count}" },
        { MessageId::AutoDbfOkTitle,        "en-US", "AUTODBF OK" },
        { MessageId::AutoDbfCreatedLine,    "en-US", "  Created: {path} [X64]" },
        { MessageId::AutoDbfImportedRowsLine, "en-US", "  Imported rows: {count}" },
        { MessageId::AutoDbfOpenedLine,     "en-US", "  Opened: {path}" },
        { MessageId::AboutUsageLine,        "en-US", "ABOUT" },
        { MessageId::AboutUsageUsageLine,   "en-US", "ABOUT USAGE" },
        { MessageId::AboutPage1Text,        "en-US",
            "ABOUT - Page 1 of 2\n"
            "===================\n"
            "\n"
            "DotTalk++\n"
            "\n"
            "Author\n"
            " Derald Grimwood\n"
            "\n"
            "Dedicated to\n"
            " Kathy Grimwood\n"
            "\n"
            "Project\n"
            " DotTalk++ is a modern C++ xBase-inspired database runtime and command shell.\n"
            "\n"
            "Heritage\n"
            " The DotTalk++ command model draws inspiration from the classic xBase\n"
            " lineage of database languages:\n"
            "\n"
            " dBase - early interactive database shell\n"
            " Clipper - compiled xBase systems\n"
            " FoxPro - relational navigation and index-driven querying\n"
            "\n"
            " DotTalk++ preserves many of the familiar commands and workflows from\n"
            " these systems while extending them with:\n"
            "\n"
            " modern help catalogs\n"
            " relational traversal (REL ENUM)\n"
            " tuple projection\n"
            " scripting and automation\n"
            "\n"
            " DotTalk++ also combines aspects of both the interactive xBase model\n"
            " and the compiled application model. Like dBase and FoxPro, it provides\n"
            " a live command shell for exploring data. Like Clipper, it can be extended\n"
            " through source code and compiled. It is also structured as modular\n"
            " runtime libraries, including xbase and xindex, beneath the shell.\n"
            "\n"
            "History\n"
            " The project traces back to 1993, when Derald Grimwood wrote a small\n"
            " ANSI C database program as a practical and experimental system,\n"
            " including fixed-length record storage and a simple in-memory B-tree.\n"
            "\n"
            " In 2025, that earlier work was revived and used as the conceptual basis\n"
            " for a modern 64-bit rebuild in C++. The result became DotTalk++:\n"
            " not a direct port, but a broader reimplementation and expansion.\n"
            "\n"
            "Current Direction\n"
            " DotTalk++ aims to retain the clarity of the xBase interaction model\n"
            " while making the engine suitable for modern experimentation and\n"
            " education.\n"
            "\n"
            " It is intended to serve as:\n"
            " - a working DBF database runtime\n"
            " - a relational exploration environment\n"
            " - a scripting and automation shell\n"
            " - a teaching system for database concepts\n"
            "\n"
            " Internally, DotTalk++ is also organized as a modular system:\n"
            " - xbase : core DBF/table/runtime library\n"
            " - xindex : indexing library\n"
            " - dottalk : command shell and interactive environment\n"
            "\n"
            " In this sense, DotTalk++ sits between FoxPro and Clipper:\n"
            " - interactive and stateful like FoxPro\n"
            " - extensible and compilable like Clipper\n"
            "\n"
            "Design Philosophy\n"
            " DotTalk++ is intentionally stateful and interactive.\n"
            "\n"
            " It exposes important runtime concepts directly, including:\n"
            " - current work area\n"
            " - current record pointer\n"
            " - active order/index\n"
            " - active filter\n"
            " - relation graph\n"
            " - buffering state\n"
            "\n"
            " The goal is to make database behavior visible and understandable during\n"
            " live operation, rather than hiding it behind abstraction.\n"
            "\n"
            "Working Model\n"
            " DotTalk++ can be understood as four cooperating layers:\n"
            "\n"
            " 1. Command Layer - interactive commands and scripting\n"
            " 2. Data Layer - tables, records, fields, indexes\n"
            " 3. Logic Layer - expressions, predicates, control flow\n"
            " 4. Projection Layer - LIST, SMARTLIST, TUPLE, REL ENUM, browsers\n"
            "\n"
            "Runtime Environment\n"
            " OS family   : {os_family}\n"
            " Architecture: {arch}\n"
            " C++ standard: {cpp_standard}\n"
            " Compiler    : {compiler}\n"
            "\n"
            "Years\n"
            " Origin: 1993 ANSI C\n"
            " Revival / C++ X64 modern rebuild: 2025-\n"
            "\n"
            "Summary\n"
            " DotTalk++ honors the xBase tradition while extending it into a modern,\n"
            " teachable, experiment-friendly database runtime.\n"
            "\n"
            " User interfaces change, languages change, but the underlying database principles remain constant. -- Derald Grimwood" },
        { MessageId::AboutPage2Title,       "en-US", "ABOUT - Page 2 of 2" },
        { MessageId::AboutSectionApplication, "en-US", "Application" },
        { MessageId::AboutSectionOperatingSystem, "en-US", "Operating System" },
        { MessageId::AboutSectionHardware,  "en-US", "Hardware" },
        { MessageId::AboutSectionStorage,   "en-US", "Storage" },
        { MessageId::AboutSectionConsole,   "en-US", "Console" },
        { MessageId::AboutSectionNetwork,   "en-US", "Network" },
        { MessageId::AboutSectionCurrentSession, "en-US", "Current Session" },
        { MessageId::AboutKeyName,          "en-US", "Name" },
        { MessageId::AboutKeyBuildMode,     "en-US", "Build Mode" },
        { MessageId::AboutKeyBuildDate,     "en-US", "Build Date" },
        { MessageId::AboutKeyArchitecture,  "en-US", "Architecture" },
        { MessageId::AboutKeyCompiler,      "en-US", "Compiler" },
        { MessageId::AboutKeyCppStd,        "en-US", "C++ Std" },
        { MessageId::AboutKeyOs,            "en-US", "OS" },
        { MessageId::AboutKeyCpuThreads,    "en-US", "CPU Threads" },
        { MessageId::AboutKeyInstalledRam,  "en-US", "Installed RAM" },
        { MessageId::AboutKeyDiskRoot,      "en-US", "Disk Root" },
        { MessageId::AboutKeyDiskFree,      "en-US", "Disk Free" },
        { MessageId::AboutKeyDiskTotal,     "en-US", "Disk Total" },
        { MessageId::AboutKeySize,          "en-US", "Size" },
        { MessageId::AboutKeyAnsiVt,        "en-US", "ANSI / VT" },
        { MessageId::AboutKeyComputerName,  "en-US", "Computer Name" },
        { MessageId::AboutKeyLocalIpv4,     "en-US", "Local IPv4" },
        { MessageId::AboutKeyFileOpen,      "en-US", "File Open" },
        { MessageId::AboutKeyDbfile,        "en-US", "Dbfile" },
        { MessageId::AboutKeyRecords,       "en-US", "Records" },
        { MessageId::AboutKeyFields,        "en-US", "Fields" },
        { MessageId::AboutYes,              "en-US", "Yes" },
        { MessageId::AboutNo,               "en-US", "No" },
        { MessageId::AboutEnabled,          "en-US", "enabled" },
        { MessageId::AboutDisabled,         "en-US", "disabled" },
        { MessageId::AboutNone,             "en-US", "(none)" },
        { MessageId::AboutUnavailable,      "en-US", "(unavailable)" },
        { MessageId::ShellStartupBannerLine, "en-US", "DotTalk++ type HELP. USE, SELECT <n>, AREA, COLOR <GREEN|AMBER|DEFAULT>, ABOUT, QUIT." },
        { MessageId::ShellStartupDevLine,   "en-US", "Dev: CMDHELPCHK, GPS, WORKSPACE, ERSATZ." },
        { MessageId::ShellStartupHelloLine, "en-US", "Hello World!" },
        { MessageId::ShellBlockCancelled,   "en-US", "BLOCK: cancelled" },
        { MessageId::ShellLoopBlockCancelled, "en-US", "LOOP BLOCK: cancelled" },
        { MessageId::ShellQuitCanceled,     "en-US", "QUIT canceled." },
        { MessageId::BuildLmdbUsageText,    "en-US",
            "Usage: BUILDLMDB [HELP|?] [MAPSIZE <n[K|M|G]> | SIZE <n[K|M|G]> |\n"
            "                  TINY|SMALL|MEDIUM|LARGE|XL|HUGE]\n"
            "                 [YES|AUTO|NOPROMPT] [CLEAN|FORCE] [QUIET]\n"
            "\n"
            "  BUILDLMDB\n"
            "      Rebuild LMDB backing store for the current CDX container.\n"
            "      Default mapsize is 128 MiB.\n"
            "\n"
            "  BUILDLMDB SMALL\n"
            "      Use preset mapsize 64 MiB.\n"
            "\n"
            "  BUILDLMDB MEDIUM\n"
            "      Use preset mapsize 128 MiB.\n"
            "\n"
            "  BUILDLMDB LARGE\n"
            "      Use preset mapsize 256 MiB.\n"
            "\n"
            "  BUILDLMDB MAPSIZE 1G YES\n"
            "      Rebuild using 1 GiB mapsize for empirical/speed testing.\n"
            "\n"
            "  BUILDLMDB CLEAN MAPSIZE 512M YES\n"
            "      Archive existing LMDB env first, then rebuild at 512 MiB.\n"
            "\n"
            "Presets:\n"
            "  TINY=32 MiB  SMALL=64 MiB  MEDIUM=128 MiB\n"
            "  LARGE=256 MiB  XL=512 MiB  HUGE=1 GiB" },
        { MessageId::BuildLmdbEnvPathNotDirectory, "en-US", "env path exists but is not a directory: {path}" },
        { MessageId::BuildLmdbUnableCreateBackupsDir, "en-US", "unable to create backups dir: {path}" },
        { MessageId::BuildLmdbCopyFailed,    "en-US", "copy failed: {detail}" },
        { MessageId::BuildLmdbRemoveAllFailed, "en-US", "remove_all failed after copy: {detail}" },
        { MessageId::BuildLmdbArchivedEnvdir, "en-US", "archived envdir to: {path}" },
        { MessageId::BuildLmdbLmdbStepTagFailed, "en-US", "{step} failed for tag {tag}: {code} ({detail})" },
        { MessageId::BuildLmdbPutFailed,     "en-US", "put failed for tag {tag} rec {recno}: {code} ({detail})" },
        { MessageId::BuildLmdbUnableCreateEnvDir, "en-US", "unable to create env dir: {path}" },
        { MessageId::BuildLmdbLmdbStepFailed, "en-US", "{step} failed: {code} ({detail})" },
        { MessageId::BuildLmdbMapsizeRequiresValue, "en-US", "{keyword} requires a value like 64M, 128M, 1G." },
        { MessageId::BuildLmdbInvalidMapsize, "en-US", "invalid mapsize: {value}" },
        { MessageId::BuildLmdbUnknownOptions, "en-US", "unknown option(s): {options}" },
        { MessageId::BuildLmdbNoTableOpen,  "en-US", "No table open." },
        { MessageId::BuildLmdbTargetContainerLine, "en-US", "target container {path}" },
        { MessageId::BuildLmdbEnvLine,      "en-US", "LMDB env        {path}" },
        { MessageId::BuildLmdbMapsizeInfoLine, "en-US", "mapsize         {value}" },
        { MessageId::BuildLmdbDestructiveWarningText, "en-US",
            "\nWARNING: LMDB environment directory already exists and appears to contain data:\n"
            "  {path}\n"
            "Rebuilding will DROP and recreate all tag databases inside it.\n"
            "This is a destructive operation -- existing index data will be lost.\n"
            "\n"
            "BUILDLMDB: confirmation required. Re-run with YES, AUTO, or NOPROMPT.\n"
            "Examples:\n"
            "  BUILDLMDB YES\n"
            "  BUILDLMDB CLEAN YES\n"
            "  BUILDLMDB MAPSIZE 1G YES" },
        { MessageId::BuildLmdbAutoConfirmed, "en-US", "auto-confirmed rebuild of existing env." },
        { MessageId::BuildLmdbReleasingActiveIndex, "en-US", "releasing active index/order before rebuild." },
        { MessageId::BuildLmdbArchiveFailedAborting, "en-US", "archive failed - aborting." },
        { MessageId::BuildLmdbTagOkLine,    "en-US", " [{index}] {tag} : OK" },
        { MessageId::BuildLmdbDoneTagsRebuilt, "en-US", "done OK={count} tags rebuilt." },
        { MessageId::BuildLmdbCdxContainerLine, "en-US", "CDX container   : {path}" },
        { MessageId::BuildLmdbLmdbEnvironmentLine, "en-US", "LMDB environment: {path}" },
        { MessageId::BuildLmdbMapsizeReportLine, "en-US", "Mapsize         : {value}" },
        { MessageId::BuildLmdbFailedToBuildEnv, "en-US", "failed to build LMDB environment." },
        { MessageId::BBoxUsageText, "en-US",
            "Usage:\n"
            "  BBOX\n"
            "  BBOX USAGE\n"
            "  BBOX MODEL\n"
            "  BBOX LANES\n"
            "  BBOX COMMENTS\n"
            "  BBOX HELP\n"
            "  BBOX MANUALGEN\n"
            "  BBOX DATADICT\n"
            "  BBOX MESSAGING\n"
            "  BBOX MAINT\n"
            "Notes:\n"
            "  - BBOX is read-only and educational.\n"
            "  - BBOX teaches the Blackbox model: data in, processing, information out.\n"
            "  - BBOX does not mutate DBFs, HELP, META, CMDHELPCHK, source, scripts, or publications." },
        { MessageId::BBoxModelText, "en-US",
            "BLACKBOX MODEL\n"
            "  DATA IN\n"
            "    source comments, usage contracts, DBFs, scripts, Markdown, media, source code, catalogs\n"
            "\n"
            "  PROCESSING\n"
            "    scan, harvest, classify, import, build, validate, publish, smoke test\n"
            "\n"
            "  INFORMATION OUT\n"
            "    HELP, CMDHELP, manuals, data dictionary, comments workspace, MAN*/DD*/SRC* catalogs, reports, diagrams\n"
            "\n"
            "  CONTROL\n"
            "    backup, rollback, boundary ledger, runtime smoke, savepoint, next gate" },
        { MessageId::BBoxLanesText, "en-US",
            "BBOX LANES\n"
            "  COMMENTS   source comments and @dottalk.usage -> SRC* evidence catalogs\n"
            "  HELP       registry, DOTREF, usage contracts -> HELP DATA and CMDHELP\n"
            "  MANUALGEN  manual sections/media/manifests -> MAN* catalog and published manuals\n"
            "  DATADICT   repo/schema/help evidence -> DD* catalog and DDICT runtime view\n"
            "  MESSAGING  hard-coded text/message IDs/locales -> typed localized runtime messages\n"
            "  CMDHELPCHK command/help contracts -> validation evidence\n"
            "  MAINT      maintenance lanes, cookbooks, gates, and read-only status" },
        { MessageId::BBoxCommentsLaneText, "en-US",
            "COMMENTS BLACKBOX\n"
            "  DATA IN: source files, header comments, @dottalk.usage v1 blocks\n"
            "  PROCESS: harvest, classify, import, validate, review disposition\n"
            "  OUT: SRCFILE, SRCBLOCK, SRCLINE, SRCUSAGE, SRCCLASS, SRCDISP, SRCALIAS, MEMO_LINES\n"
            "  CURRENT WORKSPACE: dottalkpp/data/workspaces/comments.dtschema" },
        { MessageId::BBoxHelpLaneText, "en-US",
            "HELP BLACKBOX\n"
            "  DATA IN: command registry, dotref.hpp, foxref.hpp, usage contracts, curated rows, source-mined facts\n"
            "  PROCESS: CMDHELP BUILD, HELP DATA generation, validation, runtime smoke\n"
            "  OUT: help_line.dbf, help_topic.dbf, help_artifacts.dbf, commands.dbf, cmd_args.dbf, HELP/CMDHELP output\n"
            "  NOTE: CMDHELP and HELP /DOT are related consumers but not identical proof surfaces." },
        { MessageId::BBoxManualgenLaneText, "en-US",
            "MANUALGEN BLACKBOX\n"
            "  DATA IN: section files, appendices, media anchors, review queues, manifests\n"
            "  PROCESS: assemble, normalize, validate, publish, catalog, runtime smoke\n"
            "  OUT: published manual, MAN* catalog, MANUAL runtime command, regeneration evidence" },
        { MessageId::BBoxDatadictLaneText, "en-US",
            "DATADICT BLACKBOX\n"
            "  DATA IN: data dictionary manifests, DD* candidate rows, x64 DATA_DICTIONARY_* physical tables\n"
            "  PROCESS: stage, import, validate, CDX/LMDB build, runtime smoke\n"
            "  OUT: DD* catalog, DDICT STATUS/TABLES/OBJECTS/FIELDS/TAGS/REL/EVIDENCE\n"
            "  RULE: use bridge policy; report metadata owner and physical artifact." },
        { MessageId::BBoxMessagingLaneText, "en-US",
            "MESSAGING BLACKBOX\n"
            "  DATA IN: hard-coded text, message IDs, message arguments, locale/language rows\n"
            "  PROCESS: extract, catalog, localize, validate placeholders, replace source strings gradually\n"
            "  OUT: x64base message catalog, localized runtime text, typed warnings/errors/status/help messages\n"
            "  CONTROL: SET LANGUAGE / SET LOCALE selects message-rendering locale where supported." },
        { MessageId::BBoxMaintLaneText, "en-US",
            "MAINT BLACKBOX\n"
            "  PURPOSE: developer/SDLC maintenance inspection over documented lanes and cookbooks\n"
            "  PRIMARY APP: native C++ MAINT surface, planned separately\n"
            "  EXTERNAL TOOLS: Python 3.12 for portable report tooling; PowerShell only for temporary scaffolding\n"
            "  RULE: MAINT starts read-only; mutation lanes require explicit guarded packages." },
        { MessageId::BBoxUnknownTopic, "en-US", "unknown topic: {topic}" },
        { MessageId::MaintUsageText, "en-US",
            "Usage:\n"
            "  MAINT\n"
            "  MAINT USAGE\n"
            "  MAINT STATUS\n"
            "  MAINT LANES\n"
            "  MAINT COOKBOOK\n"
            "  MAINT BOUNDARY\n"
            "  MAINT BBOX\n"
            "  MAINT DOCS\n"
            "  MAINT GUI\n"
            "  MAINT AI\n"
            "  MAINT AI USAGE\n"
            "  MAINT AI STATUS\n"
            "  MAINT AI DASHBOARD\n"
            "  MAINT AI ASSIMILATE\n"
            "  MAINT AI BOOK\n"
            "  MAINT AI INTAKE\n"
            "  MAINT AI GATES\n"
            "  MAINT AI VISIBILITY\n"
            "  MAINT CONTRACTS\n"
            "  MAINT CONTRACTS USAGE\n"
            "  MAINT CONTRACTS STATUS\n"
            "  MAINT CONTRACTS SCAN\n"
            "  MAINT CONTRACTS REGISTRY\n"
            "  MAINT CONTRACTS INTAKE\n"
            "  MAINT CONTRACTS DRIFT\n"
            "  MAINT CONTRACTS GATES\n"
            "Notes:\n"
            "  - MAINT is read-only first wave.\n"
            "  - MAINT inspects maintenance lanes, cookbooks, status, and boundaries.\n"
            "  - MAINT AI is a read-only native visibility surface for AI Portal partner onboarding and routing.\n"
            "  - MAINT AI ASSIMILATE points new or second-opinion AI development partners to the repo-local AI Portal.\n"
            "  - The AI Portal is an Alpha Python/registry surface; MAINT AI does not launch it or grant mutation authority.\n"
            "  - MAINT does not run scripts or mutate HELP, CMDHELPCHK, DBFs, source, runtime scripts, or publications." },
        { MessageId::MaintStatusText, "en-US",
            "MAINT STATUS\n"
            "  mode: read-only\n"
            "  purpose: inspect DotTalk++ maintenance/SDLC lanes and boundaries\n"
            "  native app: yes, C++ command surface\n"
            "  executes maintenance scripts: no\n"
            "  mutates protected systems: no\n"
            "  related teaching surface: BBOX" },
        { MessageId::MaintLanesText, "en-US",
            "MAINT LANES\n"
            "  comments    - source comments and @dottalk.usage evidence\n"
            "  help        - HELP, CMDHELP, DOTREF, and help-route evidence\n"
            "  cmdhelpchk  - HELP/registry/source-contract validation\n"
            "  manualgen   - developer manual generation and MAN* catalog evidence\n"
            "  datadict    - DD* / DATA_DICTIONARY_* catalog and DDICT evidence\n"
            "  messaging   - message catalog, language/locale, and output text migration\n"
            "  ai-friendly - AI-assisted work capture, curation, routing, and user visibility\n"
            "  gui         - wx, Python/Tkinter, and TUI synchronization over shared runtime contracts\n"
            "  contracts   - durable rules, usage contracts, registry, intake, and drift review\n"
            "  blackbox    - data in, processing, information out teaching model\n"
            "  maintenance - SDLC cookbooks, gates, boundaries, and closeouts" },
        { MessageId::MaintCookbookText, "en-US",
            "MAINT COOKBOOK\n"
            "  docs root   : docs\\maintenance\n"
            "  script root : dottalkpp\\scripts\\maintenance\n"
            "  runtime scripts stay under dottalkpp\\data\\scripts\n"
            "  native source support is reserved under src\\maintenance when needed\n"
            "  PowerShell is temporary MDO scaffolding; permanent app surface is C++.\n"
            "  Python 3.12 may support portable external helper/report tooling." },
        { MessageId::MaintBoundaryText, "en-US",
            "MAINT BOUNDARY\n"
            "  first-wave MAINT is inspection-only.\n"
            "  It must not mutate:\n"
            "    - source files\n"
            "    - HELP DATA or raw HELP DBFs\n"
            "    - CMDHELPCHK expectations\n"
            "    - metadata catalogs\n"
            "    - DBF/CDX/LMDB artifacts\n"
            "    - runtime scripts\n"
            "    - publications or media\n"
            "  Mutation lanes require separate guarded packages and explicit authorization." },
        { MessageId::MaintBboxRelationText, "en-US",
            "MAINT BBOX\n"
            "  BBOX teaches the Blackbox model: data in, processing, information out.\n"
            "  MAINT inspects the SDLC maintenance controls around those transformations.\n"
            "  Relationship:\n"
            "    BBOX explains the model.\n"
            "    MAINT explains the maintenance process, gates, cookbooks, and boundaries." },
        { MessageId::MaintUnknownTopic, "en-US", "unknown topic: {topic}\nUse MAINT USAGE." },
        { MessageId::DDictUsageText, "en-US",
            "Usage:\n"
            "  DDICT\n"
            "  DDICT HELP\n"
            "  DDICT STATUS\n"
            "  DDICT TABLES\n"
            "  DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]\n"
            "  DDICT FIELDS <table>\n"
            "  DDICT TAGS <table>\n"
            "  DDICT REL <object-id-or-name> [IN|OUT|BOTH]\n"
            "  DDICT EVIDENCE <object-id-or-name>\n"
            "Notes:\n"
            "  DDICT is read-only over the active Data Dictionary catalog." },
        { MessageId::DDictStatusTitle, "en-US", "DDICT STATUS" },
        { MessageId::DDictActiveCatalogLine, "en-US", "  Active catalog: {path}" },
        { MessageId::DDictReadModeLine, "en-US", "  Read mode     : READ-ONLY" },
        { MessageId::DDictDbfTablesLine, "en-US", "  DBF tables    : {present} / {expected}" },
        { MessageId::DDictDtxSidecarsLine, "en-US", "  DTX sidecars  : {present} / {expected}" },
        { MessageId::DDictDbfBytesLine, "en-US", "  DBF bytes     : {bytes}" },
        { MessageId::DDictCatalogStatePresentLine, "en-US", "  Catalog state : ACTIVE_CATALOG_PRESENT" },
        { MessageId::DDictCatalogStateReviewLine, "en-US", "  Catalog state : ACTIVE_CATALOG_REVIEW" },
        { MessageId::DDictTablesTitle, "en-US", "DDICT TABLES" },
        { MessageId::DDictTablesColumnHeader, "en-US", "  Table       DBF  DTX  DBF_BYTES" },
        { MessageId::DDictTablesDivider, "en-US", "  ----------  ---  ---  ---------" },
        { MessageId::DDictFieldsRequiresTableName, "en-US", "FIELDS requires a table name." },
        { MessageId::DDictFieldsTitle, "en-US", "DDICT FIELDS {table}" },
        { MessageId::DDictFieldRowsLine, "en-US", "  Field rows    : {count}" },
        { MessageId::DDictMetadataOwnerLine, "en-US", "  Metadata owner: {owner}" },
        { MessageId::DDictFieldsNoFieldsLine, "en-US", "  Result        : NO_FIELDS_FOUND" },
        { MessageId::DDictFieldsExpectedOwnersNote, "en-US", "  Note          : expected DDOBJECT rows where OBJTYPE=CATALOG_FIELD and OWNER in {owners}" },
        { MessageId::DDictFieldsColumnHeader, "en-US", "  Field       OBJID                     STATUS                    PROFILE       ATTRS" },
        { MessageId::DDictFieldsDivider, "en-US", "  ----------  ------------------------  ------------------------  ------------  -----" },
        { MessageId::DDictTagsRequiresTableName, "en-US", "TAGS requires a table name." },
        { MessageId::DDictTagsTitle, "en-US", "DDICT TAGS {table}" },
        { MessageId::DDictTableDbfLine, "en-US", "  Table DBF     : {value}" },
        { MessageId::DDictCdxArtifactLine, "en-US", "  CDX artifact  : {value}" },
        { MessageId::DDictLmdbMirrorLine, "en-US", "  LMDB mirror   : {value}" },
        { MessageId::DDictCatalogTagsLine, "en-US", "  Catalog tags  : {count}" },
        { MessageId::DDictTagsPhysicalNoCatalogLine, "en-US", "  Result        : PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS" },
        { MessageId::DDictTagsNoCatalogLine, "en-US", "  Result        : NO_CATALOG_TAGS_FOUND" },
        { MessageId::DDictTagsPhysicalArtifactsNote, "en-US", "  Note          : physical DBF/CDX/LMDB artifacts exist, but no DDOBJECT CATALOG_TAG rows were found for OWNER in {owners}" },
        { MessageId::DDictTagsExpectedOwnersNote, "en-US", "  Note          : expected DDOBJECT rows where OBJTYPE=CATALOG_TAG and OWNER in {owners}" },
        { MessageId::DDictTagsColumnHeader, "en-US", "  Tag         OBJID                     STATUS                    PROFILE       ATTRS" },
        { MessageId::DDictTagsDivider, "en-US", "  ----------  ------------------------  ------------------------  ------------  -----" },
        { MessageId::DDictUnknownSubcommand, "en-US", "unknown subcommand '{subcommand}'." },
        { MessageId::DDictRelRequiresObjectToken, "en-US", "REL requires an object id or name." },
        { MessageId::DDictRelInvalidDirection, "en-US", "REL direction must be IN, OUT, or BOTH." },
        { MessageId::DDictRelTitle, "en-US", "DDICT REL {token} {direction}" },
        { MessageId::DDictObjectNotFoundLine, "en-US", "  Result        : OBJECT_NOT_FOUND" },
        { MessageId::DDictObjectLookupNote, "en-US", "  Note          : token was matched against OBJID and DDOBJECT NAME/OWNER." },
        { MessageId::DDictObjectObjidLine, "en-US", "  Object OBJID  : {value}" },
        { MessageId::DDictObjectTypeLine, "en-US", "  Object type   : {value}" },
        { MessageId::DDictObjectOwnerLine, "en-US", "  Object owner  : {value}" },
        { MessageId::DDictObjectNameLine, "en-US", "  Object name   : {value}" },
        { MessageId::DDictIncomingEdgesLine, "en-US", "  Incoming edges: {count}" },
        { MessageId::DDictOutgoingEdgesLine, "en-US", "  Outgoing edges: {count}" },
        { MessageId::DDictRowsShownPerDirectionLine, "en-US", "  Rows shown    : bounded to {count} per direction" },
        { MessageId::DDictRelColumnHeader, "en-US", "  Dir  EdgeType            OtherOBJ                  OtherType          OtherOwner      OtherName       EVID" },
        { MessageId::DDictRelDivider, "en-US", "  ---  ------------------  ------------------------  -----------------  --------------  --------------  --------------------" },
        { MessageId::DDictEvidenceRequiresObjectToken, "en-US", "EVIDENCE requires an object id or name." },
        { MessageId::DDictEvidenceTitle, "en-US", "DDICT EVIDENCE {token}" },
        { MessageId::DDictDirectEvidenceRowsLine, "en-US", "  Direct evidence rows: {count}" },
        { MessageId::DDictAttributeEvidenceRowsLine, "en-US", "  Attribute evidence rows: {count}" },
        { MessageId::DDictRowsShownPerSectionLine, "en-US", "  Rows shown    : bounded to {count} per section" },
        { MessageId::DDictEvidenceRowsTitle, "en-US", "  Evidence rows" },
        { MessageId::DDictEvidenceColumnHeader, "en-US", "  EVID                  KIND                  SRCID                 SOURCE              ARTIFACT" },
        { MessageId::DDictEvidenceDivider, "en-US", "  --------------------  --------------------  --------------------  ------------------  ------------------" },
        { MessageId::DDictNoneLine, "en-US", "  (none)" },
        { MessageId::DDictAttributeEvidenceTitle, "en-US", "  Attribute evidence" },
        { MessageId::DDictAttributeEvidenceColumnHeader, "en-US", "  ATTRNAME            ATTRVAL                         EVID" },
        { MessageId::DDictAttributeEvidenceDivider, "en-US", "  ------------------  ------------------------------  --------------------" },
        { MessageId::DDictObjectsTitle, "en-US", "DDICT OBJECTS" },
        { MessageId::DDictTypeFilterLine, "en-US", "  Type filter   : {value}" },
        { MessageId::DDictProfileFilterLine, "en-US", "  Profile filter: {value}" },
        { MessageId::DDictObjectRowsLine, "en-US", "  Object rows   : {count}" },
        { MessageId::DDictRowsShownBoundedLine, "en-US", "  Rows shown    : bounded to {count}" },
        { MessageId::DDictObjectsColumnHeader, "en-US", "  OBJTYPE             NAME              OWNER             STATUS                    PROFILE       ATTRS" },
        { MessageId::DDictObjectsDivider, "en-US", "  ------------------  ----------------  ----------------  ------------------------  ------------  -----" },
        { MessageId::CmdHelpChkReflectionReportsTitle, "en-US", "=== REFLECTION REPORTS ===" },
        { MessageId::CmdHelpChkArtifactsSummaryTitle,  "en-US", "HELP DATA v2 artifact summary" },
        { MessageId::CmdHelpChkSetFamilyCanonicalizationTitle, "en-US", "SET-family canonicalization" },
        { MessageId::CmdHelpChkMissingV2Columns, "en-US", "Missing expected HELP DATA v2 columns; need at least KIND, SOURCE, CONFID." },
        { MessageId::CmdHelpChkMissingLegacyColumns, "en-US", "Missing expected columns; need at least ID, COMMAND, and one memo (USAGE)." },
        { MessageId::CmdHelpChkArtifactsError, "en-US", "ARTIFACTS error: {detail}" },
        { MessageId::CmdHelpChkRuntimeError,   "en-US", "error: {detail}" },
        { MessageId::CmdHelpChkNoRowsShown,    "en-US", "(no rows shown; try increasing limit)" },
        { MessageId::MsgMgrUsageText, "en-US",
            "Usage:\n"
            "  MSGMGR                 (Show this usage)\n"
            "  MSGMGR USAGE           (Show this usage)\n"
            "  MSGMGR STATUS          (Report Message Manager command-house status)\n"
            "  MSGMGR CHECK           (Read-only command-house check)\n"
            "Notes:\n"
            "  - MSGMGR is read-only in this phase.\n"
            "  - Runtime message catalog proof remains available through SET MESSAGE CATALOG CHECK.\n"
            "  - Locale-spine runtime wiring remains guarded for a later phase." },
        { MessageId::MsgMgrStatusTitle,        "en-US", "MSGMGR STATUS" },
        { MessageId::MsgMgrStatusBodyText, "en-US",
            "  command house        : registered\n"
            "  read mode            : read-only\n"
            "  active message check : SET MESSAGE CATALOG CHECK\n"
            "  active message get   : SET MESSAGE CATALOG GET\n"
            "  provider mode        : active_dbf\n"
            "  message DBF root     : dottalkpp/data/messaging\n"
            "  message index root   : dottalkpp/data/indexes/messaging\n"
            "  message LMDB root    : dottalkpp/data/lmdb/messaging\n"
            "  locale spine         : scaffold present; runtime status wiring held\n"
            "  schema root          : dottalkpp/data/schemas\n"
            "  locale schema        : dottalkpp/data/schemas/locale/locale_spine.dtschema\n"
            "  messaging schema     : dottalkpp/data/schemas/messaging/message_catalog.dtschema\n"
            "  boundary             : no DBF/CDX/LMDB mutation; no runtime writeback" },
        { MessageId::MsgMgrUnknownSubcommand,  "en-US", "Unknown subcommand: {command}" },
        { MessageId::HelpNoFunctionFound,      "en-US", "No function help found for: {command}" },
        { MessageId::HelpNoDotTalkTopicFound,  "en-US", "No DotTalk help found for: {command}" },
        { MessageId::HelpNoEducationalTopicFound, "en-US", "No educational help found for: {command}" },
        { MessageId::HelpNoTopicFound,         "en-US", "No help found for: {command}" },
        { MessageId::HelpTopLevelHint,         "en-US", "Type HELP GIANT, HELP /GIANT, HELP GIANT TOPICS, HELP BETA, HELP PS, HELP SQL, HELP FUNCTION <name>, or HELP <command>" },
        { MessageId::HelpUsageText,            "en-US", "DotTalk++ Help System\n\n  HELP GIANT            - full HELP DATA report\n  HELP GIANT USAGE      - GIANT surface usage\n  HELP GIANT TOPICS     - list current HELP DATA topics\n  HELP GIANT KIND       - group current HELP DATA by kind\n  HELP GIANT SOURCE     - group current HELP DATA by source\n  HELP /GIANT ...       - alias for GIANT help surface\n  HELP BETA             - beta checklist\n  HELP PS / PSHELL      - PowerShell helpers\n  HELP SQL              - SQL reference (SQLite + MSSQL)\n  HELP PREDICATES       - COUNT/LOCATE syntax\n  HELP FUNCTION <name>  - expression function help\n  HELP FUNCTIONS        - list documented expression functions\n  HELP /FOX <topic>     - FoxPro compatibility reference\n  HELP /DOT <topic>     - DotTalk-native command reference\n  HELP /ED <topic>      - educational/system concepts\n  HELP <command>        - default topic lookup\n\n  Paging for long HELP GIANT output follows SET PAGING ON|OFF." },
        { MessageId::CmdHelpCurrentLoadFailed, "en-US", "could not load current HELP DATA lines from \"{dir}\"." },
        { MessageId::CmdHelpBuildTip,          "en-US", "Tip: run CMDHELP BUILD . <source-root>" },
        { MessageId::CmdHelpNoTopicMatched,    "en-US", "no current HELP DATA topic matched \"{topic}\"." },
        { MessageId::CmdHelpSummaryTip,        "en-US", "Tip: run CMDHELP with no arguments for a HELP DATA summary." },
        { MessageId::CmdHelpCurrentBuildWritten, "en-US", "CMDHELP wrote current HELP DATA -> {dir}" },
        { MessageId::CmdHelpArtifactsMinedFrom, "en-US", "Artifacts mined from: {root}" },
        { MessageId::CmdHelpUsageContractsMined, "en-US", "Usage contracts mined directly: {rows} row(s) from {files} file(s)" },
        { MessageId::CmdHelpLegacyBuildWritten, "en-US", "CMDHELP LEGACY wrote: {commands} command rows, {args} arg rows -> {dir}" },
        { MessageId::CmdHelpSwitchesMinedFrom, "en-US", "Switches mined from: {root}" },
        { MessageId::CmdHelpLegacyReadFailed,  "en-US", "LEGACY: could not read commands.dbf/cmd_args.dbf in \"{dir}\"." },
        { MessageId::CmdHelpLegacyBuildTip,    "en-US", "Tip: run: CMDHELP BUILD LEGACY" },
        { MessageId::CmdHelpCurrentReadFailed, "en-US", "could not read current HELP DATA in \"{dir}\"." },
        { MessageId::CmdHelpCurrentExpectedFile, "en-US", "Expected: help_line.dbf" },
        { MessageId::CmdHelpCurrentMissingColumns, "en-US", "help_line.dbf is missing expected columns." },
        { MessageId::CmdHelpCurrentNeedColumns, "en-US", "Need at least TOPICKEY, KIND, SOURCE, TEXT." },
        { MessageId::CmdHelpCurrentReportTitle, "en-US", "CMDHELP Report (current HELP DATA)" },
        { MessageId::CmdHelpPreviewRowsTitle, "en-US", "Preview rows" },
        { MessageId::CmdHelpTopicNoRenderableSections, "en-US", "(topic exists, but no renderable help sections were found)" },
        { MessageId::CmdHelpUsageTitle, "en-US", "CMDHELP usage" },
        { MessageId::CmdHelpNotesTitle, "en-US", "Notes:" },
        { MessageId::CmdHelpUsageNoteBuild, "en-US", "CMDHELP BUILD writes current HELP DATA tables." },
        { MessageId::CmdHelpUsageNoteLegacy, "en-US", "CMDHELP LEGACY reads the old commands.dbf/cmd_args.dbf report." },
        { MessageId::CmdHelpCurrentDirectoryLine, "en-US", "  directory : {dir}" },
        { MessageId::CmdHelpCurrentLineRowsLine, "en-US", "  line rows : {count}" },
        { MessageId::CmdHelpCurrentTopicsLine, "en-US", "  topics    : {count}" },
        { MessageId::CmdHelpByKindTitle, "en-US", "By KIND" },
        { MessageId::CmdHelpBySourceTitle, "en-US", "By SOURCE" },
        { MessageId::CmdHelpMatchedTopicsLabel, "en-US", "Matched topics:" },
        { MessageId::CmdHelpPreviewTopicKeyHeader, "en-US", "TOPICKEY" },
        { MessageId::CmdHelpPreviewKindHeader, "en-US", "KIND" },
        { MessageId::CmdHelpPreviewSourceHeader, "en-US", "SOURCE" },
        { MessageId::CmdHelpPreviewConfidHeader, "en-US", "CONFID" },
        { MessageId::CmdHelpPreviewRoleHeader, "en-US", "ROLE" },
        { MessageId::CmdHelpPreviewTextHeader, "en-US", "TEXT" },
        { MessageId::CmdHelpPreviewDivider, "en-US", "--------------------------------------------------------------------------------" },
        { MessageId::CmdHelpQueryLine, "en-US", "CMDHELP {qualifier}{query}" },
        { MessageId::CmdHelpUsageBodyText, "en-US",
            "  CMDHELP\n"
            "  CMDHELP USAGE\n"
            "  CMDHELP BUILD\n"
            "  CMDHELP BUILD . <source-root>\n"
            "  CMDHELP <topic>\n"
            "  CMDHELP USAGE <topic>\n"
            "  CMDHELP <topic> USAGE\n"
            "  CMDHELP BUILD LEGACY\n"
            "  CMDHELP LEGACY" },
        { MessageId::CmdHelpLegacyReportLine, "en-US", "CMDHELP LEGACY Report: {commands} command rows, {args} arg rows -> {dir}" },
        { MessageId::LmdbUsageText,          "en-US", "Usage:\n  LMDB USAGE\n  LMDB INFO\n  LMDB OPEN <container.cdx>\n  LMDB OPEN <envdir.cdx.d>\n  LMDB OPEN <stem>\n  LMDB USE <tag>\n  LMDB SEEK <key>\n  LMDB DUMP\n  LMDB DUMP <max>\n  LMDB SCAN <low> <high>\n  LMDB CLOSE\nNotes:\n  - LMDB is per-area and uses the current DbArea IndexManager/CDX backend.\n  - Bare stems resolve through the INDEXES path slot.\n  - LMDB_UTIL is deprecated and disabled." },
        { MessageId::LmdbActionNoTableOpenText, "en-US", "{action}: no table open in current area" },
        { MessageId::LmdbInfoNoneText,       "en-US", "(none)" },
        { MessageId::LmdbInfoTitleText,      "en-US", "LMDB INFO" },
        { MessageId::LmdbInfoContainerLineText, "en-US", "  container: {path}" },
        { MessageId::LmdbInfoTagLineText,    "en-US", "  tag      : {tag}" },
        { MessageId::LmdbOpenMissingPathText, "en-US", "missing path" },
        { MessageId::LmdbOpenInvalidPathText, "en-US", "invalid path" },
        { MessageId::LmdbOpenFailedText,     "en-US", "OPEN failed: {detail}" },
        { MessageId::LmdbOpenText,           "en-US", "OPEN: {path}" },
        { MessageId::LmdbUseMissingTagText,  "en-US", "missing TAG" },
        { MessageId::LmdbUseFailedText,      "en-US", "USE failed: {detail}" },
        { MessageId::LmdbUseText,            "en-US", "USE: {tag}" },
        { MessageId::LmdbSeekMissingKeyText, "en-US", "missing key" },
        { MessageId::LmdbSeekFailedText,     "en-US", "SEEK failed: {detail}" },
        { MessageId::LmdbSeekRecnoText,      "en-US", "SEEK: recno={recno}" },
        { MessageId::LmdbDumpNoneText,       "en-US", "DUMP: (none)" },
        { MessageId::LmdbDumpNoTagSelectedText, "en-US", "DUMP: no TAG selected. Try: LMDB USE <TAG>" },
        { MessageId::LmdbDumpCursorOpenFailedText, "en-US", "DUMP: cursor open failed" },
        { MessageId::LmdbDumpPrintedText,    "en-US", "DUMP: printed {count}" },
        { MessageId::LmdbScanUsageText,      "en-US", "SCAN usage: LMDB SCAN <low> <high>" },
        { MessageId::LmdbScanNoneText,       "en-US", "SCAN: (none)" },
        { MessageId::LmdbScanNoTagSelectedText, "en-US", "SCAN: no TAG selected. Try: LMDB USE <TAG>" },
        { MessageId::LmdbScanCursorOpenFailedText, "en-US", "SCAN: cursor open failed" },
        { MessageId::LmdbScanShownText,      "en-US", "SCAN: shown {count}" },
        { MessageId::LmdbCloseText,          "en-US", "CLOSE" },
        { MessageId::LmdbUtilDisabledText,   "en-US", "LMDB_UTIL is deprecated and disabled.\nUse: LMDB (per-area)\nUsage:\n  LMDB_UTIL\n  LMDB_UTIL USAGE\nRelated:\n  LMDB INFO\n  LMDB OPEN <container.cdx>\n  LMDB USE <tag>\n  LMDB SEEK <key>\n  LMDB DUMP\n  LMDB SCAN <low> <high>\n  LMDB CLOSE" },
        { MessageId::ManualCatalogStatusTitle, "en-US", "MANUAL CATALOG STATUS" },
        { MessageId::ManualCatalogTablesTitle, "en-US", "MANUAL CATALOG TABLES" },
        { MessageId::ManualCatalogCountsTitle, "en-US", "MANUAL CATALOG COUNTS" },
        { MessageId::ManualCatalogCountsNote, "en-US", "note: this lightweight native surface reports expected counts and DBF presence; DBF row readback remains in manualgen reports." },
        { MessageId::ManualCatalogResolveTitle, "en-US", "MANUAL CATALOG RESOLVE" },
        { MessageId::ManualResolveUnknownToken, "en-US", "unknown MAN* table token or alias" },
        { MessageId::ManualInternalTableSpecMissing, "en-US", "internal error: table specification missing" },
        { MessageId::ManualUsageTitle, "en-US", "Usage:" },
        { MessageId::ManualNotesTitle, "en-US", "Notes:" },
        { MessageId::ManualReadOnlyNote, "en-US", "MANUAL is read-only." },
        { MessageId::ManualReportsEvidenceNote, "en-US", "MANUAL reports accepted MAN* manualgen catalog evidence." },
        { MessageId::ManualDoesNotMutateNote, "en-US", "MANUAL does not mutate DBFs, HELP, META, CMDHELPCHK, source, or publication artifacts." },
        { MessageId::ManualSectionsTitle, "en-US", "MANUAL SECTIONS" },
        { MessageId::ManualMediaTitle, "en-US", "MANUAL MEDIA" },
        { MessageId::ManualMediaAnchorsTitle, "en-US", "MANUAL MEDIA ANCHORS" },
        { MessageId::ManualReviewTitle, "en-US", "MANUAL REVIEW" },
        { MessageId::ManualStatusModeLine, "en-US", "  mode: read-only" },
        { MessageId::ManualStatusRepoRootLine, "en-US", "  repo_root: {value}" },
        { MessageId::ManualStatusAcceptedDbfDirLine, "en-US", "  accepted_dbf_dir: {value}" },
        { MessageId::ManualStatusAcceptedDbfDirExistsLine, "en-US", "  accepted_dbf_dir_exists: {value}" },
        { MessageId::ManualStatusExpectedTablesLine, "en-US", "  expected_MAN_tables: {value}" },
        { MessageId::ManualStatusPresentTablesLine, "en-US", "  present_MAN_tables: {value}" },
        { MessageId::ManualTableLine, "en-US", "  {compact} alias={alias} expected={expected} exists={exists} purpose=\"{purpose}\"" },
        { MessageId::ManualCountLine, "en-US", "  {compact} expected={expected} dbf_exists={exists}" },
        { MessageId::ManualResolveRequestedTokenLine, "en-US", "  requested_token: {value}" },
        { MessageId::ManualResolveResolvedLine, "en-US", "  resolved: {value}" },
        { MessageId::ManualResolveMessageLine, "en-US", "  message: {value}" },
        { MessageId::ManualResolveCompactNameLine, "en-US", "  compact_name: {value}" },
        { MessageId::ManualResolveAliasCandidateLine, "en-US", "  alias_candidate: {value}" },
        { MessageId::ManualResolvePhysicalTableLine, "en-US", "  physical_table: {value}" },
        { MessageId::ManualResolveDbfExistsLine, "en-US", "  dbf_exists: {value}" },
        { MessageId::ManualFocusCompactNameLine, "en-US", "  compact_name: {value}" },
        { MessageId::ManualFocusAliasCandidateLine, "en-US", "  alias_candidate: {value}" },
        { MessageId::ManualFocusExpectedRecordsLine, "en-US", "  expected_records: {value}" },
        { MessageId::ManualFocusDbfExistsLine, "en-US", "  dbf_exists: {value}" },
        { MessageId::ManualFocusPhysicalTableLine, "en-US", "  physical_table: {value}" },
        { MessageId::ManualFocusDetailFutureNoteLine, "en-US", "  note: detailed row rendering remains a future read-only native enhancement." },
        { MessageId::ManualUnsupportedSubcommand, "en-US", "unsupported read-only subcommand. Use MANUAL USAGE." },

        // Italian. DotScript commands remain English; message prose is localized.
        { MessageId::HelpHintCommand,       "it", "Digitare HELP {command} per ulteriori informazioni." },
        { MessageId::MessageLocaleSet,      "it", "Lingua dei messaggi: {locale}" },
        { MessageId::UnsupportedMessageLocale, "it", "Locale dei messaggi non supportato: {locale}" },
        { MessageId::UnknownCommand,        "it", "Comando sconosciuto: {command}" },
        { MessageId::MissingArgument,       "it", "Argomento obbligatorio mancante." },
        { MessageId::TooManyArguments,      "it", "Troppi argomenti." },
        { MessageId::InvalidSyntax,         "it", "Sintassi del comando non valida." },
        { MessageId::InvalidOption,         "it", "Opzione non valida: {option}" },
        { MessageId::CommandNotImplemented, "it", "Comando riconosciuto ma non implementato: {command}" },
        { MessageId::CommandDeprecated,     "it", "Comando obsoleto: {command}" },
        { MessageId::NoOpenTable,           "it", "Nessuna tabella e' attualmente aperta." },
        { MessageId::NoSelectedArea,        "it", "Nessuna area di lavoro corrente e' selezionata." },
        { MessageId::CmdHelpChkReflectionReportsTitle, "it", "=== RAPPORTI DI RIFLESSIONE ===" },
        { MessageId::CmdHelpChkArtifactsSummaryTitle,  "it", "Riepilogo artefatti HELP DATA v2" },
        { MessageId::CmdHelpChkSetFamilyCanonicalizationTitle, "it", "Canonicalizzazione famiglia SET" },
        { MessageId::CmdHelpChkMissingV2Columns, "it", "Mancano colonne HELP DATA v2 attese; servono almeno KIND, SOURCE e CONFID." },
        { MessageId::CmdHelpChkMissingLegacyColumns, "it", "Mancano colonne attese; servono almeno ID, COMMAND e un memo (USAGE)." },
        { MessageId::CmdHelpChkArtifactsError, "it", "Errore ARTIFACTS: {detail}" },
        { MessageId::CmdHelpChkRuntimeError,   "it", "errore: {detail}" },
        { MessageId::CmdHelpChkNoRowsShown,    "it", "(nessuna riga mostrata; provare ad aumentare il limite)" },
        { MessageId::MsgMgrStatusTitle,        "it", "STATO MSGMGR" },
        { MessageId::MsgMgrUnknownSubcommand,  "it", "Sottocomando sconosciuto: {command}" },
        { MessageId::HelpNoFunctionFound,      "it", "Nessun aiuto funzione trovato per: {command}" },
        { MessageId::HelpNoDotTalkTopicFound,  "it", "Nessun aiuto DotTalk trovato per: {command}" },
        { MessageId::HelpNoEducationalTopicFound, "it", "Nessun aiuto educativo trovato per: {command}" },
        { MessageId::HelpNoTopicFound,         "it", "Nessun aiuto trovato per: {command}" },
        { MessageId::HelpTopLevelHint,         "it", "Digitare HELP GIANT, HELP BETA, HELP PS, HELP SQL, HELP FUNCTION <name> oppure HELP <command>" },
        { MessageId::CmdHelpCurrentLoadFailed, "it", "impossibile caricare le righe HELP DATA correnti da \"{dir}\"." },
        { MessageId::CmdHelpBuildTip,          "it", "Suggerimento: eseguire CMDHELP BUILD . <source-root>" },
        { MessageId::CmdHelpNoTopicMatched,    "it", "nessun argomento HELP DATA corrente corrisponde a \"{topic}\"." },
        { MessageId::CmdHelpSummaryTip,        "it", "Suggerimento: eseguire CMDHELP senza argomenti per un riepilogo HELP DATA." },
        { MessageId::CmdHelpCurrentBuildWritten, "it", "CMDHELP ha scritto HELP DATA corrente -> {dir}" },
        { MessageId::CmdHelpArtifactsMinedFrom, "it", "Artefatti estratti da: {root}" },
        { MessageId::CmdHelpUsageContractsMined, "it", "Contratti di utilizzo estratti direttamente: {rows} riga/e da {files} file" },
        { MessageId::CmdHelpLegacyBuildWritten, "it", "CMDHELP LEGACY ha scritto: {commands} righe comando, {args} righe argomento -> {dir}" },
        { MessageId::CmdHelpSwitchesMinedFrom, "it", "Opzioni estratte da: {root}" },
        { MessageId::CmdHelpLegacyReadFailed,  "it", "LEGACY: impossibile leggere commands.dbf/cmd_args.dbf in \"{dir}\"." },
        { MessageId::CmdHelpLegacyBuildTip,    "it", "Suggerimento: eseguire: CMDHELP BUILD LEGACY" },
        { MessageId::CmdHelpCurrentReadFailed, "it", "impossibile leggere HELP DATA corrente in \"{dir}\"." },
        { MessageId::CmdHelpCurrentExpectedFile, "it", "Atteso: help_line.dbf" },
        { MessageId::CmdHelpCurrentMissingColumns, "it", "help_line.dbf non contiene le colonne attese." },
        { MessageId::CmdHelpCurrentNeedColumns, "it", "Servono almeno TOPICKEY, KIND, SOURCE e TEXT." },
        { MessageId::CmdHelpCurrentReportTitle, "it", "Rapporto CMDHELP (HELP DATA corrente)" },
        { MessageId::CmdHelpPreviewRowsTitle, "it", "Righe di anteprima" },
        { MessageId::CmdHelpTopicNoRenderableSections, "it", "(l'argomento esiste, ma non sono state trovate sezioni di aiuto renderizzabili)" },
        { MessageId::CmdHelpUsageTitle, "it", "Uso CMDHELP" },
        { MessageId::CmdHelpNotesTitle, "it", "Note:" },
        { MessageId::CmdHelpUsageNoteBuild, "it", "CMDHELP BUILD scrive le tabelle HELP DATA correnti." },
        { MessageId::CmdHelpUsageNoteLegacy, "it", "CMDHELP LEGACY legge il vecchio rapporto commands.dbf/cmd_args.dbf." },
        { MessageId::CmdHelpByKindTitle, "it", "Per KIND" },
        { MessageId::CmdHelpBySourceTitle, "it", "Per SOURCE" },
        { MessageId::CmdHelpMatchedTopicsLabel, "it", "Argomenti corrispondenti:" },
        { MessageId::CmdHelpLegacyReportLine, "it", "Rapporto CMDHELP LEGACY: {commands} righe comando, {args} righe argomento -> {dir}" },
        { MessageId::ManualCatalogStatusTitle, "it", "STATO CATALOGO MANUAL" },
        { MessageId::ManualCatalogTablesTitle, "it", "TABELLE CATALOGO MANUAL" },
        { MessageId::ManualCatalogCountsTitle, "it", "CONTEGGI CATALOGO MANUAL" },
        { MessageId::ManualCatalogCountsNote, "it", "nota: questa superficie nativa leggera riporta conteggi attesi e presenza DBF; la rilettura delle righe DBF resta nei rapporti manualgen." },
        { MessageId::ManualCatalogResolveTitle, "it", "RISOLUZIONE CATALOGO MANUAL" },
        { MessageId::ManualResolveUnknownToken, "it", "token o alias tabella MAN* sconosciuto" },
        { MessageId::ManualInternalTableSpecMissing, "it", "errore interno: specifica tabella mancante" },
        { MessageId::ManualUsageTitle, "it", "Uso:" },
        { MessageId::ManualNotesTitle, "it", "Note:" },
        { MessageId::ManualReadOnlyNote, "it", "MANUAL e' in sola lettura." },
        { MessageId::ManualReportsEvidenceNote, "it", "MANUAL riporta l'evidenza del catalogo manualgen MAN* accettata." },
        { MessageId::ManualDoesNotMutateNote, "it", "MANUAL non modifica DBF, HELP, META, CMDHELPCHK, sorgente o artefatti di pubblicazione." },
        { MessageId::ManualUnsupportedSubcommand, "it", "sottocomando di sola lettura non supportato. Usare MANUAL USAGE." },

        // Spanish.
        { MessageId::HelpHintCommand,       "es", "Escriba HELP {command} para obtener mas informacion." },
        { MessageId::MessageLocaleSet,      "es", "Idioma de mensajes: {locale}" },
        { MessageId::UnsupportedMessageLocale, "es", "Configuracion regional de mensajes no admitida: {locale}" },
        { MessageId::UnknownCommand,        "es", "Comando desconocido: {command}" },
        { MessageId::MissingArgument,       "es", "Falta un argumento requerido." },
        { MessageId::TooManyArguments,      "es", "Demasiados argumentos." },
        { MessageId::InvalidSyntax,         "es", "Sintaxis de comando no valida." },
        { MessageId::InvalidOption,         "es", "Opcion no valida: {option}" },
        { MessageId::CommandNotImplemented, "es", "El comando se reconoce, pero no esta implementado: {command}" },
        { MessageId::CommandDeprecated,     "es", "El comando esta obsoleto: {command}" },
        { MessageId::NoOpenTable,           "es", "No hay ninguna tabla abierta actualmente." },
        { MessageId::NoSelectedArea,        "es", "No hay un area de trabajo actual seleccionada." },
        { MessageId::CmdHelpChkReflectionReportsTitle, "es", "=== INFORMES DE REFLEXION ===" },
        { MessageId::CmdHelpChkArtifactsSummaryTitle,  "es", "Resumen de artefactos HELP DATA v2" },
        { MessageId::CmdHelpChkSetFamilyCanonicalizationTitle, "es", "Canonizacion de la familia SET" },
        { MessageId::CmdHelpChkMissingV2Columns, "es", "Faltan columnas esperadas de HELP DATA v2; se necesitan al menos KIND, SOURCE y CONFID." },
        { MessageId::CmdHelpChkMissingLegacyColumns, "es", "Faltan columnas esperadas; se necesitan al menos ID, COMMAND y un memo (USAGE)." },
        { MessageId::CmdHelpChkArtifactsError, "es", "Error de ARTIFACTS: {detail}" },
        { MessageId::CmdHelpChkRuntimeError,   "es", "error: {detail}" },
        { MessageId::CmdHelpChkNoRowsShown,    "es", "(no se mostraron filas; intente aumentar el limite)" },
        { MessageId::MsgMgrStatusTitle,        "es", "ESTADO DE MSGMGR" },
        { MessageId::MsgMgrUnknownSubcommand,  "es", "Subcomando desconocido: {command}" },
        { MessageId::HelpNoFunctionFound,      "es", "No se encontro ayuda de funcion para: {command}" },
        { MessageId::HelpNoDotTalkTopicFound,  "es", "No se encontro ayuda de DotTalk para: {command}" },
        { MessageId::HelpNoEducationalTopicFound, "es", "No se encontro ayuda educativa para: {command}" },
        { MessageId::HelpNoTopicFound,         "es", "No se encontro ayuda para: {command}" },
        { MessageId::HelpTopLevelHint,         "es", "Escriba HELP GIANT, HELP BETA, HELP PS, HELP SQL, HELP FUNCTION <name> o HELP <command>" },
        { MessageId::CmdHelpCurrentLoadFailed, "es", "no se pudieron cargar las lineas actuales de HELP DATA desde \"{dir}\"." },
        { MessageId::CmdHelpBuildTip,          "es", "Sugerencia: ejecute CMDHELP BUILD . <source-root>" },
        { MessageId::CmdHelpNoTopicMatched,    "es", "ningun tema actual de HELP DATA coincide con \"{topic}\"." },
        { MessageId::CmdHelpSummaryTip,        "es", "Sugerencia: ejecute CMDHELP sin argumentos para un resumen de HELP DATA." },
        { MessageId::CmdHelpCurrentBuildWritten, "es", "CMDHELP escribio HELP DATA actual -> {dir}" },
        { MessageId::CmdHelpArtifactsMinedFrom, "es", "Artefactos extraidos de: {root}" },
        { MessageId::CmdHelpUsageContractsMined, "es", "Contratos de uso extraidos directamente: {rows} fila(s) de {files} archivo(s)" },
        { MessageId::CmdHelpLegacyBuildWritten, "es", "CMDHELP LEGACY escribio: {commands} filas de comando, {args} filas de argumento -> {dir}" },
        { MessageId::CmdHelpSwitchesMinedFrom, "es", "Interruptores extraidos de: {root}" },
        { MessageId::CmdHelpLegacyReadFailed,  "es", "LEGACY: no se pudo leer commands.dbf/cmd_args.dbf en \"{dir}\"." },
        { MessageId::CmdHelpLegacyBuildTip,    "es", "Sugerencia: ejecute: CMDHELP BUILD LEGACY" },
        { MessageId::CmdHelpCurrentReadFailed, "es", "no se pudo leer HELP DATA actual en \"{dir}\"." },
        { MessageId::CmdHelpCurrentExpectedFile, "es", "Esperado: help_line.dbf" },
        { MessageId::CmdHelpCurrentMissingColumns, "es", "help_line.dbf no contiene las columnas esperadas." },
        { MessageId::CmdHelpCurrentNeedColumns, "es", "Se necesitan al menos TOPICKEY, KIND, SOURCE y TEXT." },
        { MessageId::CmdHelpCurrentReportTitle, "es", "Informe CMDHELP (HELP DATA actual)" },
        { MessageId::CmdHelpPreviewRowsTitle, "es", "Filas de vista previa" },
        { MessageId::CmdHelpTopicNoRenderableSections, "es", "(el tema existe, pero no se encontraron secciones de ayuda representables)" },
        { MessageId::CmdHelpUsageTitle, "es", "Uso de CMDHELP" },
        { MessageId::CmdHelpNotesTitle, "es", "Notas:" },
        { MessageId::CmdHelpUsageNoteBuild, "es", "CMDHELP BUILD escribe las tablas HELP DATA actuales." },
        { MessageId::CmdHelpUsageNoteLegacy, "es", "CMDHELP LEGACY lee el informe antiguo commands.dbf/cmd_args.dbf." },
        { MessageId::CmdHelpByKindTitle, "es", "Por KIND" },
        { MessageId::CmdHelpBySourceTitle, "es", "Por SOURCE" },
        { MessageId::CmdHelpMatchedTopicsLabel, "es", "Temas coincidentes:" },
        { MessageId::CmdHelpLegacyReportLine, "es", "Informe CMDHELP LEGACY: {commands} filas de comando, {args} filas de argumento -> {dir}" },
        { MessageId::ManualCatalogStatusTitle, "es", "ESTADO DEL CATALOGO MANUAL" },
        { MessageId::ManualCatalogTablesTitle, "es", "TABLAS DEL CATALOGO MANUAL" },
        { MessageId::ManualCatalogCountsTitle, "es", "CONTEOS DEL CATALOGO MANUAL" },
        { MessageId::ManualCatalogCountsNote, "es", "nota: esta superficie nativa ligera informa conteos esperados y presencia de DBF; la lectura de filas DBF sigue en los informes de manualgen." },
        { MessageId::ManualCatalogResolveTitle, "es", "RESOLUCION DEL CATALOGO MANUAL" },
        { MessageId::ManualResolveUnknownToken, "es", "token o alias de tabla MAN* desconocido" },
        { MessageId::ManualInternalTableSpecMissing, "es", "error interno: falta la especificacion de la tabla" },
        { MessageId::ManualUsageTitle, "es", "Uso:" },
        { MessageId::ManualNotesTitle, "es", "Notas:" },
        { MessageId::ManualReadOnlyNote, "es", "MANUAL es de solo lectura." },
        { MessageId::ManualReportsEvidenceNote, "es", "MANUAL informa la evidencia aceptada del catalogo manualgen MAN*." },
        { MessageId::ManualDoesNotMutateNote, "es", "MANUAL no modifica DBF, HELP, META, CMDHELPCHK, origen ni artefactos de publicacion." },
        { MessageId::ManualUnsupportedSubcommand, "es", "subcomando de solo lectura no admitido. Use MANUAL USAGE." },

        // French.
        { MessageId::HelpHintCommand,       "fr", "Tapez HELP {command} pour plus d'informations." },
        { MessageId::MessageLocaleSet,      "fr", "Langue des messages : {locale}" },
        { MessageId::UnsupportedMessageLocale, "fr", "Parametre regional de messages non pris en charge : {locale}" },
        { MessageId::UnknownCommand,        "fr", "Commande inconnue : {command}" },
        { MessageId::MissingArgument,       "fr", "Argument requis manquant." },
        { MessageId::TooManyArguments,      "fr", "Trop d'arguments." },
        { MessageId::InvalidSyntax,         "fr", "Syntaxe de commande non valide." },
        { MessageId::InvalidOption,         "fr", "Option non valide : {option}" },
        { MessageId::CommandNotImplemented, "fr", "La commande est reconnue mais pas implementee : {command}" },
        { MessageId::CommandDeprecated,     "fr", "La commande est obsolete : {command}" },
        { MessageId::NoOpenTable,           "fr", "Aucune table n'est actuellement ouverte." },
        { MessageId::NoSelectedArea,        "fr", "Aucune zone de travail courante n'est selectionnee." },
        { MessageId::CmdHelpChkReflectionReportsTitle, "fr", "=== RAPPORTS DE REFLEXION ===" },
        { MessageId::CmdHelpChkArtifactsSummaryTitle,  "fr", "Resume des artefacts HELP DATA v2" },
        { MessageId::CmdHelpChkSetFamilyCanonicalizationTitle, "fr", "Canonicalisation de la famille SET" },
        { MessageId::CmdHelpChkMissingV2Columns, "fr", "Colonnes HELP DATA v2 attendues manquantes ; il faut au moins KIND, SOURCE et CONFID." },
        { MessageId::CmdHelpChkMissingLegacyColumns, "fr", "Colonnes attendues manquantes ; il faut au moins ID, COMMAND et un memo (USAGE)." },
        { MessageId::CmdHelpChkArtifactsError, "fr", "Erreur ARTIFACTS : {detail}" },
        { MessageId::CmdHelpChkRuntimeError,   "fr", "erreur : {detail}" },
        { MessageId::CmdHelpChkNoRowsShown,    "fr", "(aucune ligne affichee ; essayez d'augmenter la limite)" },
        { MessageId::MsgMgrStatusTitle,        "fr", "ETAT MSGMGR" },
        { MessageId::MsgMgrUnknownSubcommand,  "fr", "Sous-commande inconnue : {command}" },
        { MessageId::HelpNoFunctionFound,      "fr", "Aucune aide de fonction trouvee pour : {command}" },
        { MessageId::HelpNoDotTalkTopicFound,  "fr", "Aucune aide DotTalk trouvee pour : {command}" },
        { MessageId::HelpNoEducationalTopicFound, "fr", "Aucune aide educative trouvee pour : {command}" },
        { MessageId::HelpNoTopicFound,         "fr", "Aucune aide trouvee pour : {command}" },
        { MessageId::HelpTopLevelHint,         "fr", "Tapez HELP GIANT, HELP BETA, HELP PS, HELP SQL, HELP FUNCTION <name> ou HELP <command>" },
        { MessageId::CmdHelpCurrentLoadFailed, "fr", "impossible de charger les lignes HELP DATA actuelles depuis \"{dir}\"." },
        { MessageId::CmdHelpBuildTip,          "fr", "Conseil : executez CMDHELP BUILD . <source-root>" },
        { MessageId::CmdHelpNoTopicMatched,    "fr", "aucun sujet HELP DATA actuel ne correspond a \"{topic}\"." },
        { MessageId::CmdHelpSummaryTip,        "fr", "Conseil : executez CMDHELP sans arguments pour un resume HELP DATA." },
        { MessageId::CmdHelpCurrentBuildWritten, "fr", "CMDHELP a ecrit HELP DATA courant -> {dir}" },
        { MessageId::CmdHelpArtifactsMinedFrom, "fr", "Artefacts extraits de : {root}" },
        { MessageId::CmdHelpUsageContractsMined, "fr", "Contrats d'usage extraits directement : {rows} ligne(s) depuis {files} fichier(s)" },
        { MessageId::CmdHelpLegacyBuildWritten, "fr", "CMDHELP LEGACY a ecrit : {commands} lignes de commande, {args} lignes d'argument -> {dir}" },
        { MessageId::CmdHelpSwitchesMinedFrom, "fr", "Commutateurs extraits de : {root}" },
        { MessageId::CmdHelpLegacyReadFailed,  "fr", "LEGACY : impossible de lire commands.dbf/cmd_args.dbf dans \"{dir}\"." },
        { MessageId::CmdHelpLegacyBuildTip,    "fr", "Conseil : executez : CMDHELP BUILD LEGACY" },
        { MessageId::CmdHelpCurrentReadFailed, "fr", "impossible de lire HELP DATA courant dans \"{dir}\"." },
        { MessageId::CmdHelpCurrentExpectedFile, "fr", "Attendu : help_line.dbf" },
        { MessageId::CmdHelpCurrentMissingColumns, "fr", "help_line.dbf ne contient pas les colonnes attendues." },
        { MessageId::CmdHelpCurrentNeedColumns, "fr", "Il faut au moins TOPICKEY, KIND, SOURCE et TEXT." },
        { MessageId::CmdHelpCurrentReportTitle, "fr", "Rapport CMDHELP (HELP DATA courant)" },
        { MessageId::CmdHelpPreviewRowsTitle, "fr", "Lignes d'aperçu" },
        { MessageId::CmdHelpTopicNoRenderableSections, "fr", "(le sujet existe, mais aucune section d'aide affichable n'a ete trouvee)" },
        { MessageId::CmdHelpUsageTitle, "fr", "Utilisation de CMDHELP" },
        { MessageId::CmdHelpNotesTitle, "fr", "Remarques :" },
        { MessageId::CmdHelpUsageNoteBuild, "fr", "CMDHELP BUILD ecrit les tables HELP DATA courantes." },
        { MessageId::CmdHelpUsageNoteLegacy, "fr", "CMDHELP LEGACY lit l'ancien rapport commands.dbf/cmd_args.dbf." },
        { MessageId::CmdHelpByKindTitle, "fr", "Par KIND" },
        { MessageId::CmdHelpBySourceTitle, "fr", "Par SOURCE" },
        { MessageId::CmdHelpMatchedTopicsLabel, "fr", "Sujets correspondants :" },
        { MessageId::CmdHelpLegacyReportLine, "fr", "Rapport CMDHELP LEGACY : {commands} lignes de commande, {args} lignes d'argument -> {dir}" },
        { MessageId::ManualCatalogStatusTitle, "fr", "ETAT DU CATALOGUE MANUAL" },
        { MessageId::ManualCatalogTablesTitle, "fr", "TABLES DU CATALOGUE MANUAL" },
        { MessageId::ManualCatalogCountsTitle, "fr", "COMPTES DU CATALOGUE MANUAL" },
        { MessageId::ManualCatalogCountsNote, "fr", "note : cette surface native legere rapporte les comptes attendus et la presence DBF ; la relecture des lignes DBF reste dans les rapports manualgen." },
        { MessageId::ManualCatalogResolveTitle, "fr", "RESOLUTION DU CATALOGUE MANUAL" },
        { MessageId::ManualResolveUnknownToken, "fr", "jeton ou alias de table MAN* inconnu" },
        { MessageId::ManualInternalTableSpecMissing, "fr", "erreur interne : specification de table manquante" },
        { MessageId::ManualUsageTitle, "fr", "Utilisation :" },
        { MessageId::ManualNotesTitle, "fr", "Remarques :" },
        { MessageId::ManualReadOnlyNote, "fr", "MANUAL est en lecture seule." },
        { MessageId::ManualReportsEvidenceNote, "fr", "MANUAL rapporte les preuves acceptees du catalogue manualgen MAN*." },
        { MessageId::ManualDoesNotMutateNote, "fr", "MANUAL ne modifie pas les DBF, HELP, META, CMDHELPCHK, la source ni les artefacts de publication." },
        { MessageId::ManualUnsupportedSubcommand, "fr", "sous-commande en lecture seule non prise en charge. Utilisez MANUAL USAGE." },

        // German.
        { MessageId::HelpHintCommand,       "de", "Geben Sie HELP {command} ein, um weitere Informationen zu erhalten." },
        { MessageId::MessageLocaleSet,      "de", "Nachrichten-Sprache: {locale}" },
        { MessageId::UnsupportedMessageLocale, "de", "Nicht unterstuetzte Nachrichten-Locale: {locale}" },
        { MessageId::UnknownCommand,        "de", "Unbekannter Befehl: {command}" },
        { MessageId::MissingArgument,       "de", "Erforderliches Argument fehlt." },
        { MessageId::TooManyArguments,      "de", "Zu viele Argumente." },
        { MessageId::InvalidSyntax,         "de", "Ungueltige Befehlssyntax." },
        { MessageId::InvalidOption,         "de", "Ungueltige Option: {option}" },
        { MessageId::CommandNotImplemented, "de", "Der Befehl ist bekannt, aber nicht implementiert: {command}" },
        { MessageId::CommandDeprecated,     "de", "Der Befehl ist veraltet: {command}" },
        { MessageId::NoOpenTable,           "de", "Derzeit ist keine Tabelle geoeffnet." },
        { MessageId::NoSelectedArea,        "de", "Es ist kein aktueller Arbeitsbereich ausgewaehlt." },
        { MessageId::CmdHelpChkReflectionReportsTitle, "de", "=== REFLEXIONSBERICHTE ===" },
        { MessageId::CmdHelpChkArtifactsSummaryTitle,  "de", "HELP-DATA-v2-Artefaktzusammenfassung" },
        { MessageId::CmdHelpChkSetFamilyCanonicalizationTitle, "de", "SET-Familien-Kanonisierung" },
        { MessageId::CmdHelpChkMissingV2Columns, "de", "Erwartete HELP-DATA-v2-Spalten fehlen; mindestens KIND, SOURCE und CONFID werden benoetigt." },
        { MessageId::CmdHelpChkMissingLegacyColumns, "de", "Erwartete Spalten fehlen; mindestens ID, COMMAND und ein Memo (USAGE) werden benoetigt." },
        { MessageId::CmdHelpChkArtifactsError, "de", "ARTIFACTS-Fehler: {detail}" },
        { MessageId::CmdHelpChkRuntimeError,   "de", "Fehler: {detail}" },
        { MessageId::CmdHelpChkNoRowsShown,    "de", "(keine Zeilen angezeigt; versuchen Sie, das Limit zu erhoehen)" },
        { MessageId::MsgMgrStatusTitle,        "de", "MSGMGR-STATUS" },
        { MessageId::MsgMgrUnknownSubcommand,  "de", "Unbekannter Unterbefehl: {command}" }
        ,{ MessageId::HelpNoFunctionFound,      "de", "Keine Funktionshilfe gefunden fuer: {command}" }
        ,{ MessageId::HelpNoDotTalkTopicFound,  "de", "Keine DotTalk-Hilfe gefunden fuer: {command}" }
        ,{ MessageId::HelpNoEducationalTopicFound, "de", "Keine Lehrhilfe gefunden fuer: {command}" }
        ,{ MessageId::HelpNoTopicFound,         "de", "Keine Hilfe gefunden fuer: {command}" }
        ,{ MessageId::HelpTopLevelHint,         "de", "Geben Sie HELP GIANT, HELP BETA, HELP PS, HELP SQL, HELP FUNCTION <name> oder HELP <command> ein" }
        ,{ MessageId::CmdHelpCurrentLoadFailed, "de", "Aktuelle HELP-DATA-Zeilen aus \"{dir}\" konnten nicht geladen werden." }
        ,{ MessageId::CmdHelpBuildTip,          "de", "Hinweis: Fuehren Sie CMDHELP BUILD . <source-root> aus" }
        ,{ MessageId::CmdHelpNoTopicMatched,    "de", "Kein aktuelles HELP-DATA-Thema stimmt mit \"{topic}\" ueberein." }
        ,{ MessageId::CmdHelpSummaryTip,        "de", "Hinweis: Fuehren Sie CMDHELP ohne Argumente fuer eine HELP-DATA-Zusammenfassung aus." }
        ,{ MessageId::CmdHelpCurrentBuildWritten, "de", "CMDHELP hat aktuelle HELP DATA geschrieben -> {dir}" }
        ,{ MessageId::CmdHelpArtifactsMinedFrom, "de", "Artefakte extrahiert aus: {root}" }
        ,{ MessageId::CmdHelpUsageContractsMined, "de", "Nutzungsvertraege direkt extrahiert: {rows} Zeile(n) aus {files} Datei(en)" }
        ,{ MessageId::CmdHelpLegacyBuildWritten, "de", "CMDHELP LEGACY schrieb: {commands} Befehlszeilen, {args} Argumentzeilen -> {dir}" }
        ,{ MessageId::CmdHelpSwitchesMinedFrom, "de", "Schalter extrahiert aus: {root}" }
        ,{ MessageId::CmdHelpLegacyReadFailed,  "de", "LEGACY: commands.dbf/cmd_args.dbf in \"{dir}\" konnte nicht gelesen werden." }
        ,{ MessageId::CmdHelpLegacyBuildTip,    "de", "Hinweis: Fuehren Sie aus: CMDHELP BUILD LEGACY" }
        ,{ MessageId::CmdHelpCurrentReadFailed, "de", "Aktuelle HELP DATA in \"{dir}\" konnte nicht gelesen werden." }
        ,{ MessageId::CmdHelpCurrentExpectedFile, "de", "Erwartet: help_line.dbf" }
        ,{ MessageId::CmdHelpCurrentMissingColumns, "de", "help_line.dbf enthaelt nicht die erwarteten Spalten." }
        ,{ MessageId::CmdHelpCurrentNeedColumns, "de", "Mindestens TOPICKEY, KIND, SOURCE und TEXT werden benoetigt." }
        ,{ MessageId::CmdHelpCurrentReportTitle, "de", "CMDHELP-Bericht (aktuelle HELP DATA)" }
        ,{ MessageId::CmdHelpPreviewRowsTitle, "de", "Vorschauzeilen" }
        ,{ MessageId::CmdHelpTopicNoRenderableSections, "de", "(Thema existiert, aber es wurden keine darstellbaren Hilfsabschnitte gefunden)" }
        ,{ MessageId::CmdHelpUsageTitle, "de", "CMDHELP-Verwendung" }
        ,{ MessageId::CmdHelpNotesTitle, "de", "Hinweise:" }
        ,{ MessageId::CmdHelpUsageNoteBuild, "de", "CMDHELP BUILD schreibt die aktuellen HELP-DATA-Tabellen." }
        ,{ MessageId::CmdHelpUsageNoteLegacy, "de", "CMDHELP LEGACY liest den alten Bericht commands.dbf/cmd_args.dbf." }
        ,{ MessageId::CmdHelpByKindTitle, "de", "Nach KIND" }
        ,{ MessageId::CmdHelpBySourceTitle, "de", "Nach SOURCE" }
        ,{ MessageId::CmdHelpMatchedTopicsLabel, "de", "Passende Themen:" }
        ,{ MessageId::CmdHelpLegacyReportLine, "de", "CMDHELP-LEGACY-Bericht: {commands} Befehlszeilen, {args} Argumentzeilen -> {dir}" }
        ,{ MessageId::ManualCatalogStatusTitle, "de", "STATUS DES MANUAL-KATALOGS" }
        ,{ MessageId::ManualCatalogTablesTitle, "de", "TABELLEN DES MANUAL-KATALOGS" }
        ,{ MessageId::ManualCatalogCountsTitle, "de", "ANZAHLEN DES MANUAL-KATALOGS" }
        ,{ MessageId::ManualCatalogCountsNote, "de", "Hinweis: Diese leichte native Oberflaeche meldet erwartete Anzahlen und DBF-Praesenz; das Ruecklesen der DBF-Zeilen bleibt in manualgen-Berichten." }
        ,{ MessageId::ManualCatalogResolveTitle, "de", "AUFLOESUNG DES MANUAL-KATALOGS" }
        ,{ MessageId::ManualResolveUnknownToken, "de", "unbekanntes MAN*-Tabellentoken oder Alias" }
        ,{ MessageId::ManualInternalTableSpecMissing, "de", "interner Fehler: Tabellenspezifikation fehlt" }
        ,{ MessageId::ManualUsageTitle, "de", "Verwendung:" }
        ,{ MessageId::ManualNotesTitle, "de", "Hinweise:" }
        ,{ MessageId::ManualReadOnlyNote, "de", "MANUAL ist schreibgeschuetzt." }
        ,{ MessageId::ManualReportsEvidenceNote, "de", "MANUAL meldet anerkannte MAN*-manualgen-Katalogbelege." }
        ,{ MessageId::ManualDoesNotMutateNote, "de", "MANUAL veraendert keine DBFs, HELP, META, CMDHELPCHK, Quelltexte oder Publikationsartefakte." }
        ,{ MessageId::ManualUnsupportedSubcommand, "de", "Nicht unterstuetzter Nur-Lese-Unterbefehl. Verwenden Sie MANUAL USAGE." }
        ,{ MessageId::PrnUsageText, "en-US", "Usage:\n  PRN\n  PRN USAGE\n  PRN STATUS\n  PRN SHOW\n  PRN OFF\n  PRN TO CONSOLE\n  PRN TO SCREEN\n  PRN TO FILE <path>\n  PRN TO PRINTER\n  PRN TO PRINTER <name>\n  PRN TO NULL" }
        ,{ MessageId::PrnStatusLineText, "en-US", "PRN: {dest}" }
        ,{ MessageId::PrnFileLineText, "en-US", "  File       : {path}" }
        ,{ MessageId::PrnPrinterDefaultLineText, "en-US", "  Printer    : (system default)" }
        ,{ MessageId::PrnPrinterNamedLineText, "en-US", "  Printer    : {name}" }
        ,{ MessageId::PrnPrinterJobLineText, "en-US", "  Printer job: staged only (OS handoff disabled)" }
        ,{ MessageId::PrnAlternateLineText, "en-US", "  Alternate  : {value}" }
        ,{ MessageId::PrnPagingLineText, "en-US", "  Paging     : {state}" }
        ,{ MessageId::PrnFileUsageText, "en-US", "Usage: PRN TO FILE <path>" }
        ,{ MessageId::PrnFileOpenFailedText, "en-US", "PRN: failed to open file: {path}" }
        ,{ MessageId::PrnPrinterConfigureFailedText, "en-US", "PRN: failed to configure printer destination." }
        ,{ MessageId::BangUsageText, "en-US", "Usage:\n  BANG\n  BANG USAGE\n  BANG <command>\n  !\n  ! <command>\nNotes:\n  - BANG with no arguments launches an interactive host shell.\n  - BANG <command> executes a host shell command." }
        ,{ MessageId::BellUsageText, "en-US", "Usage:\n  BELL\n  BELL USAGE\n  BELL ON\n  BELL OFF" }
        ,{ MessageId::BellRungText, "en-US", "Bell rung." }
        ,{ MessageId::BellIsOffText, "en-US", "Bell is OFF." }
        ,{ MessageId::BellStatusText, "en-US", "Bell is {state}" }
        ,{ MessageId::CloseUsageText, "en-US", "Usage:\n  CLOSE USAGE\n  CLOSE\n  CLOSE ALL\nNotes:\n  - CLOSE closes the current work area.\n  - CLOSE ALL clears all relations before closing the current work area.\n  - Dirty table-buffer state may prompt or cancel close." }
        ,{ MessageId::CloseCanceledText, "en-US", "CLOSE canceled." }
        ,{ MessageId::CloseCompletedText, "en-US", "Closed." }
        ,{ MessageId::CdxUsageText, "en-US", "Usage:\n  CDX USAGE\n  CDX INFO [<path.cdx>]\n  CDX TAGS [<path.cdx>]\n  CDX CREATE [<path.cdx>]\n  CDX ADDTAG <name> [<path.cdx>]\n  CDX DROPTAG <name> [<path.cdx>]\nNotes:\n  - CDX with no arguments shows usage.\n  - CREATE refuses to overwrite an existing CDX file.\n  - INFO/TAGS inspect metadata; ADDTAG/DROPTAG mutate tag metadata." }
        ,{ MessageId::CdxCreateUnableResolvePathText, "en-US", "unable to resolve path." }
        ,{ MessageId::CdxCreateFileExistsText, "en-US", "file already exists: \"{path}\"" }
        ,{ MessageId::CdxCreateOpenFailedText, "en-US", "open/create failed." }
        ,{ MessageId::CdxCreatedText, "en-US", "created: \"{path}\"" }
        ,{ MessageId::CdxFileNotFoundText, "en-US", "file not found: \"{path}\"" }
        ,{ MessageId::CdxUnableOpenText, "en-US", "unable to open: \"{path}\"" }
        ,{ MessageId::CdxInfoInvalidHeaderText, "en-US", "invalid header." }
        ,{ MessageId::CdxInfoFileLineText, "en-US", "CDX file : {path}" }
        ,{ MessageId::CdxInfoTagsLineText, "en-US", "Tags     : {count}" }
        ,{ MessageId::CdxInfoTagLineText, "en-US", "  [{tag_id}] {name}  root_off={root_off}  recs={recs}" }
        ,{ MessageId::CdxTagsReadFailedText, "en-US", "read failed." }
        ,{ MessageId::CdxNoTagsText, "en-US", "(no tags)" }
        ,{ MessageId::CdxTagLineText, "en-US", "  [{tag_id}] {name}" }
        ,{ MessageId::CdxAddTagMissingNameText, "en-US", "missing <name>." }
        ,{ MessageId::CdxAddTagUnableResolvePathText, "en-US", "unable to resolve path." }
        ,{ MessageId::CdxAddTagOpenFailedText, "en-US", "open failed." }
        ,{ MessageId::CdxAddTagAlreadyExistsText, "en-US", "tag already exists." }
        ,{ MessageId::CdxAddTagAddedText, "en-US", "added '{tag}'." }
        ,{ MessageId::CdxDropTagMissingNameText, "en-US", "missing <name>." }
        ,{ MessageId::CdxDropTagUnableResolvePathText, "en-US", "unable to resolve path." }
        ,{ MessageId::CdxDropTagOpenFailedText, "en-US", "open failed." }
        ,{ MessageId::CdxDropTagNotFoundText, "en-US", "not found." }
        ,{ MessageId::CdxDropTagRemovedText, "en-US", "removed '{tag}'." }
        ,{ MessageId::CdxUnknownSubcommandText, "en-US", "unknown subcommand: {subcommand}" }
        ,{ MessageId::CnxUsageText, "en-US", "Usage:\n  CNX USAGE\n  CNX INFO [<path.cnx>]\n  CNX TAGS [<path.cnx>]\n  CNX CREATE [<path.cnx>]\n  CNX ADDTAG <name> [<path.cnx>]\n  CNX DROPTAG <name> [<path.cnx>]\n  CNX WALK <tag> [<path.cnx>]\n  CNX TRACE <tag> [<path.cnx>]\nNotes:\n  - CNX with no arguments shows usage.\n  - CREATE refuses to overwrite an existing CNX file.\n  - INFO/TAGS/WALK/TRACE inspect metadata; ADDTAG/DROPTAG mutate tag metadata." }
        ,{ MessageId::CnxCreateUnableResolvePathText, "en-US", "unable to resolve path." }
        ,{ MessageId::CnxCreateFileExistsText, "en-US", "file already exists: \"{path}\"" }
        ,{ MessageId::CnxCreateOpenFailedText, "en-US", "open/create failed." }
        ,{ MessageId::CnxCreatedText, "en-US", "created: \"{path}\"" }
        ,{ MessageId::CnxFileNotFoundText, "en-US", "file not found: \"{path}\"" }
        ,{ MessageId::CnxUnableOpenText, "en-US", "unable to open: \"{path}\"" }
        ,{ MessageId::CnxInfoInvalidHeaderText, "en-US", "invalid header." }
        ,{ MessageId::CnxInfoFileLineText, "en-US", "CNX file : {path}" }
        ,{ MessageId::CnxInfoTagsLineText, "en-US", "Tags     : {count}" }
        ,{ MessageId::CnxInfoTagLineText, "en-US", "  [{tag_id}] {name}  root_off={root_off}  recs={recs}" }
        ,{ MessageId::CnxTagsReadFailedText, "en-US", "read failed." }
        ,{ MessageId::CnxNoTagsText, "en-US", "(no tags)" }
        ,{ MessageId::CnxTagLineText, "en-US", "  [{tag_id}] {name}" }
        ,{ MessageId::CnxWalkMissingTagText, "en-US", "missing <tag>." }
        ,{ MessageId::CnxWalkUnableResolvePathText, "en-US", "unable to resolve path." }
        ,{ MessageId::CnxWalkUnableOpenText, "en-US", "unable to open: \"{path}\"" }
        ,{ MessageId::CnxWalkReadTagDirectoryFailedText, "en-US", "failed to read tag directory." }
        ,{ MessageId::CnxWalkTagNotFoundText, "en-US", "tag not found: {tag}" }
        ,{ MessageId::CnxWalkFileSummaryText, "en-US", "file=\"{path}\"  tag={tag}  root_off={root_off}  stats_rec={stats_rec}" }
        ,{ MessageId::CnxWalkPageSizeText, "en-US", "page_size={size}" }
        ,{ MessageId::CnxWalkRootZeroText, "en-US", "root_page_off is 0" }
        ,{ MessageId::CnxAddTagMissingNameText, "en-US", "missing <name>." }
        ,{ MessageId::CnxAddTagUnableResolvePathText, "en-US", "unable to resolve path." }
        ,{ MessageId::CnxAddTagOpenFailedText, "en-US", "open failed." }
        ,{ MessageId::CnxAddTagAlreadyExistsText, "en-US", "tag already exists." }
        ,{ MessageId::CnxAddTagAddedText, "en-US", "added '{tag}'." }
        ,{ MessageId::CnxDropTagMissingNameText, "en-US", "missing <name>." }
        ,{ MessageId::CnxDropTagUnableResolvePathText, "en-US", "unable to resolve path." }
        ,{ MessageId::CnxDropTagOpenFailedText, "en-US", "open failed." }
        ,{ MessageId::CnxDropTagNotFoundText, "en-US", "not found." }
        ,{ MessageId::CnxDropTagRemovedText, "en-US", "removed '{tag}'." }
        ,{ MessageId::CnxUnknownSubcommandText, "en-US", "unknown subcommand: {subcommand}" }
        ,{ MessageId::ClearUsageText, "en-US", "Usage:\n  CLEAR USAGE\n  CLEAR\n  CLS\nNotes:\n  - Clears the console screen only." }
        ,{ MessageId::VersionUsageText, "en-US", "Usage:\n  VERSION\n  VERSION USAGE" }
        ,{ MessageId::VersionBannerLineText, "en-US", "dottalk++ {version}  ({stamp})" }
        ,{ MessageId::VersionBuildLineText, "en-US", "DotTalk++ build {stamp}" }
        ,{ MessageId::SqlverUsageText, "en-US", "Usage:\n  SQLVER\n  SQLVER USAGE" }
        ,{ MessageId::SqlverAvailableLineText, "en-US", "SQLite available: 1, version: {version}" }
        ,{ MessageId::SqlverUnavailableLineText, "en-US", "SQLite available: 0" }
        ,{ MessageId::ShutdownUsageText, "en-US", "Usage:\n  SHUTDOWN\n  SHUTDOWN USAGE\nNotes:\n  - SHUTDOWN with no arguments executes shutdown.ini when present.\n  - SHUTDOWN USAGE prints this usage and does not execute shutdown.ini." }
        ,{ MessageId::ShutdownUnableOpenText, "en-US", "SHUTDOWN: unable to open {path}" }
        ,{ MessageId::ShutdownProcessingText, "en-US", "SHUTDOWN: processing {path}" }
        ,{ MessageId::ShutdownLineFailedText, "en-US", "SHUTDOWN: {file}:{line}: {detail}" }
        ,{ MessageId::ShutdownLineUnknownErrorText, "en-US", "SHUTDOWN: {file}:{line}: unknown error" }
        ,{ MessageId::ShutdownNoIniFoundText, "en-US", "SHUTDOWN: no shutdown.ini found in {path}" }
        ,{ MessageId::ShutdownProcessingFailedText, "en-US", "SHUTDOWN: ini processing failed: {detail}" }
        ,{ MessageId::ShutdownProcessingFailedUnknownText, "en-US", "SHUTDOWN: ini processing failed (unknown error)" }
        ,{ MessageId::SelectUsageText, "en-US", "Usage:\n  SELECT USAGE\n  SELECT <0..{max_slot}>\n  SELECT <name>\n  SELECT <table.dbf>" }
        ,{ MessageId::SelectEngineUnavailableText, "en-US", "SELECT: engine unavailable." }
        ,{ MessageId::SelectOutOfRangeText, "en-US", "SELECT: out of range (valid 0..{max_slot})." }
        ,{ MessageId::SelectNoAreaMatchesText, "en-US", "SELECT: no area matches '{name}'. Use SELECT <0..{max_slot}> or a known name." }
        ,{ MessageId::SelectSelectedAreaText, "en-US", "Selected area {slot}." }
        ,{ MessageId::SelectCurrentAreaText, "en-US", "Current area: {slot}" }
        ,{ MessageId::SelectCurrentAreaFileSummaryText, "en-US", "  File: {path}  Recs: {recs}  Recno: {recno}" }
        ,{ MessageId::QuitUsageText, "en-US", "Usage:\n  QUIT\n  EXIT\nNotes:\n  Requests normal DotTalk++ shutdown." }
        ,{ MessageId::UnlockUsageText, "en-US", "Usage:\n  UNLOCK USAGE\n  UNLOCK\n  UNLOCK <recno>\n  UNLOCK ALL\n  UNLOCK TABLE\nExamples:\n  UNLOCK\n  UNLOCK 10\n  UNLOCK ALL\n  UNLOCK TABLE\nNotes:\n  - UNLOCK USAGE does not require an open table.\n  - UNLOCK with no arguments unlocks the current record." }
        ,{ MessageId::UnlockNoTableOpenText, "en-US", "UNLOCK: no table open." }
        ,{ MessageId::UnlockNoCurrentRecordText, "en-US", "UNLOCK: no current record." }
        ,{ MessageId::UnlockRecordUnlockedText, "en-US", "UNLOCK: record {recno} unlocked." }
        ,{ MessageId::UnlockTableUnlockedText, "en-US", "UNLOCK: table unlocked." }
        ,{ MessageId::RefreshUsageText, "en-US", "Usage:\n  REFRESH\n  REFRESH USAGE" }
        ,{ MessageId::RefreshNoTableOpenText, "en-US", "No table open." }
        ,{ MessageId::RefreshMissingFilenameText, "en-US", "Refresh failed: current table has no filename()." }
        ,{ MessageId::RefreshFileNotFoundText, "en-US", "Refresh failed: file not found: {path}" }
        ,{ MessageId::RefreshOrderRestoreWarningText, "en-US", "REFRESH warning: order restore failed: {detail}" }
        ,{ MessageId::RefreshSuccessText, "en-US", "Refreshed {name} ({count} records)." }
        ,{ MessageId::RefreshFailedText, "en-US", "Refresh failed: {detail}" }
        ,{ MessageId::ErrorClearUsageText, "en-US", "Usage:\n  ERROR_CLEAR\n  ERROR_CLEAR USAGE" }
        ,{ MessageId::ErrorClearStatusText, "en-US", "Last error cleared." }
        ,{ MessageId::ErrorStatusUsageText, "en-US", "Usage:\n  ERROR_STATUS\n  ERROR_STATUS USAGE" }
        ,{ MessageId::ErrorStatusHeaderText, "en-US", "Last Error:" }
        ,{ MessageId::ErrorStatusSeverityLineText, "en-US", "  Severity : {value}" }
        ,{ MessageId::ErrorStatusFacilityLineText, "en-US", "  Facility : {value} ({hex})" }
        ,{ MessageId::ErrorStatusNumberLineText, "en-US", "  Number   : {value}" }
        ,{ MessageId::ErrorStatusHresultLineText, "en-US", "  HRESULT  : {value}" }
        ,{ MessageId::ErrorStatusMessageLineText, "en-US", "  Message  : {value}" }
        ,{ MessageId::ErrorTestUsageText, "en-US", "Usage:\n  ERROR_TEST\n  ERROR_TEST USAGE" }
        ,{ MessageId::ErrorTestHeaderText, "en-US", "ERROR subsystem self-test:" }
        ,{ MessageId::ErrorTestResultLineText, "en-US", "  {name} {result}" }
        ,{ MessageId::ErrorTestPassedText, "en-US", "All tests passed." }
        ,{ MessageId::ErrorTestFailedText, "en-US", "One or more tests FAILED." }
        ,{ MessageId::ErrorTestOkLabel, "en-US", "OK" }
        ,{ MessageId::ErrorTestFailLabel, "en-US", "FAIL" }
        ,{ MessageId::LockUsageText, "en-US", "Usage:\n  LOCK USAGE           - show this usage\n  LOCK                 - lock current record\n  LOCK <n>             - lock record <n>\n  LOCK ALL             - lock entire table\n  LOCK TABLE           - lock entire table\n  LOCK STATUS          - show lock status\n  LOCK WHO <n>         - show owner of record <n>" }
        ,{ MessageId::LockStatusNoTableOpenText, "en-US", "LOCK STATUS: no table open." }
        ,{ MessageId::LockStatusTableLineText, "en-US", "Table: {state}{owner_clause}" }
        ,{ MessageId::LockStatusRecordLineText, "en-US", "Record {recno}: {state}{owner_clause}" }
        ,{ MessageId::LockStateLockedText, "en-US", "LOCKED" }
        ,{ MessageId::LockStateUnlockedText, "en-US", "unlocked" }
        ,{ MessageId::LockOwnerClauseText, "en-US", " (owner {owner})" }
        ,{ MessageId::LockWhoNoneText, "en-US", "LOCK WHO: no lock recorded for {recno}." }
        ,{ MessageId::LockWhoOwnedText, "en-US", "LOCK WHO: record {recno} owned by {owner}" }
        ,{ MessageId::LockNoTableOpenText, "en-US", "LOCK: no table open." }
        ,{ MessageId::LockNoCurrentRecordText, "en-US", "LOCK: no current record." }
        ,{ MessageId::LockRecordLockedText, "en-US", "LOCK: record {recno} locked." }
        ,{ MessageId::LockTableLockedText, "en-US", "LOCK: table locked." }
        ,{ MessageId::LockFailedText, "en-US", "LOCK: failed ({detail})." }
        ,{ MessageId::RecnoUsageText, "en-US", "Usage:\n  RECNO\n  RECNO USAGE\n  RECNO <n>" }
        ,{ MessageId::RecnoOutOfRangeText, "en-US", "Record number out of range (1..{max})." }
        ,{ MessageId::RecnoUnableNavigateText, "en-US", "Unable to navigate to record {recno}." }
        ,{ MessageId::ShowIniUsageText, "en-US", "Usage:\n  SHOWINI\n  SHOWINI USAGE\n  SHOWINI <table-or-ini>\n  SHOWINI PATH <ini-file>\nExamples:\n  SHOWINI\n  SHOWINI students\n  SHOWINI students.ini\n  SHOWINI PATH d:\\data\\students.ini" }
        ,{ MessageId::ShowIniNoTableOpenText, "en-US", "SHOWINI: no table open." }
        ,{ MessageId::ShowIniPathRequiresFilenameText, "en-US", "SHOWINI: PATH requires filename." }
        ,{ MessageId::ShowIniFileNotFoundText, "en-US", "SHOWINI: ini file not found: {path}" }
        ,{ MessageId::ShowIniLoadFailedText, "en-US", "SHOWINI: load failed: {detail}" }
        ,{ MessageId::ShowIniReportTitleText, "en-US", "INI SETTINGS REPORT" }
        ,{ MessageId::ShowIniFileLineText, "en-US", "File: {path}" }
        ,{ MessageId::ShowIniSectionHeaderText, "en-US", "[{name}]" }
        ,{ MessageId::ShowIniSectionDividerText, "en-US", "----------------------------------------" }
        ,{ MessageId::ShowIniKeyValueLineText, "en-US", "{key_padded} = {value}" }
    };
    return texts;
}

const MessageDef* find_message(MessageId id)
{
    for (const auto& message : all_messages()) {
        if (message.id == id) {
            return &message;
        }
    }
    return nullptr;
}

const MessageDef* find_message_by_key(const std::string& key)
{
    for (const auto& message : all_messages()) {
        if (key == message.key) {
            return &message;
        }
    }
    return nullptr;
}

const char* message_key(MessageId id)
{
    const MessageDef* message = find_message(id);
    return message ? message->key : "UNKNOWN_MESSAGE_ID";
}

std::vector<std::string> available_locales()
{
    std::set<std::string> locales;
    for (const auto& text : all_message_texts()) {
        if (text.locale && *text.locale) {
            locales.insert(text.locale);
        }
    }
    return std::vector<std::string>(locales.begin(), locales.end());
}

std::string normalize_locale(const std::string& locale)
{
    std::string s = trim_copy(locale);
    std::replace(s.begin(), s.end(), '_', '-');
    const std::string lower = lower_copy(s);

    if (lower.empty() || lower == "default" || lower == "english" || lower == "en" ||
        lower == "en-us" || lower == "en-us.utf-8" || lower == "en-us.utf8") {
        return "en-US";
    }
    if (lower == "it" || lower == "it-it" || lower == "italian" || lower == "italiano" ||
        lower.rfind("it-", 0) == 0) {
        return "it";
    }
    if (lower == "es" || lower == "es-es" || lower == "spanish" || lower == "espanol" ||
        lower.rfind("es-", 0) == 0) {
        return "es";
    }
    if (lower == "fr" || lower == "fr-fr" || lower == "french" || lower == "francais" ||
        lower.rfind("fr-", 0) == 0) {
        return "fr";
    }
    if (lower == "de" || lower == "de-de" || lower == "german" || lower == "deutsch" ||
        lower.rfind("de-", 0) == 0) {
        return "de";
    }

    return s;
}

bool is_supported_locale(const std::string& locale)
{
    const std::string normalized = normalize_locale(locale);
    for (const auto& supported : available_locales()) {
        if (supported == normalized) {
            return true;
        }
    }
    return false;
}

std::vector<std::string> locale_fallback_chain(const std::string& locale)
{
    std::vector<std::string> chain;
    const std::string requested = normalize_locale(locale);

    if (!requested.empty()) {
        chain.push_back(requested);
        const std::string::size_type dash = requested.find('-');
        if (dash != std::string::npos && dash > 0) {
            const std::string base = requested.substr(0, dash);
            if (base != requested) {
                chain.push_back(base);
            }
        }
    }

    const std::string def = default_locale();
    if (std::find(chain.begin(), chain.end(), def) == chain.end()) {
        chain.push_back(def);
    }

    return chain;
}

const char* find_message_text(MessageId id, const std::string& locale)
{
    for (const auto& candidate : locale_fallback_chain(locale)) {
        for (const auto& text : all_message_texts()) {
            if (text.id == id && candidate == text.locale) {
                return text.text;
            }
        }
    }

    const MessageDef* message = find_message(id);
    return message ? message->text : nullptr;
}

std::string format_message(MessageId id,
                           const std::unordered_map<std::string, std::string>& vars,
                           const std::string& locale)
{
    const char* text = find_message_text(id, locale);
    if (!text) {
        return {};
    }

    return apply_vars(text, vars);
}

std::vector<MessageCatalogIssue> validate_message_catalog()
{
    std::vector<MessageCatalogIssue> issues;
    std::set<MessageId> ids;
    std::set<std::string> keys;
    std::set<std::pair<MessageId, std::string>> text_pairs;

    for (const auto& message : all_messages()) {
        if (!message.key || !*message.key) {
            add_issue(issues, "EMPTY_MESSAGE_KEY", "", "", "MessageDef has an empty key.");
        }

        if (!ids.insert(message.id).second) {
            add_issue(issues, "DUPLICATE_MESSAGE_ID", message.key ? message.key : "", "", "Duplicate MessageId in all_messages().");
        }

        if (message.key && *message.key && !keys.insert(message.key).second) {
            add_issue(issues, "DUPLICATE_MESSAGE_KEY", message.key, "", "Duplicate message key in all_messages().");
        }

        if (!find_message_text(message.id, default_locale())) {
            add_issue(issues, "MISSING_EN_US_TEXT", message.key ? message.key : "", default_locale(), "Message has no default English text.");
        }
    }

    for (const auto& text : all_message_texts()) {
        const MessageDef* message = find_message(text.id);
        const std::string key = message ? message->key : "";
        const std::string locale = text.locale ? text.locale : "";

        if (!message) {
            add_issue(issues, "ORPHAN_MESSAGE_TEXT", "", locale, "MessageTextDef references an unknown MessageId.");
            continue;
        }

        if (locale.empty()) {
            add_issue(issues, "EMPTY_LOCALE", key, locale, "MessageTextDef has an empty locale.");
        }

        if (!text.text || !*text.text) {
            add_issue(issues, "EMPTY_TEXT_TEMPLATE", key, locale, "MessageTextDef has an empty text template.");
        }

        if (!text_pairs.insert(std::make_pair(text.id, locale)).second) {
            add_issue(issues, "DUPLICATE_TEXT_ROW", key, locale, "Duplicate MessageId + locale text row.");
        }
    }

    std::map<MessageId, std::set<std::string>> english_placeholders;
    for (const auto& text : all_message_texts()) {
        if (std::string(text.locale ? text.locale : "") == default_locale()) {
            english_placeholders[text.id] = extract_placeholders(text.text ? text.text : "");
        }
    }

    for (const auto& text : all_message_texts()) {
        const MessageDef* message = find_message(text.id);
        if (!message) {
            continue;
        }
        const std::string locale = text.locale ? text.locale : "";
        if (locale == default_locale()) {
            continue;
        }

        const auto expected_it = english_placeholders.find(text.id);
        if (expected_it == english_placeholders.end()) {
            continue;
        }

        const auto observed = extract_placeholders(text.text ? text.text : "");
        if (observed != expected_it->second) {
            add_issue(issues,
                      "PLACEHOLDER_MISMATCH",
                      message->key,
                      locale,
                      "Expected placeholders {" + join_set(expected_it->second) + "}; observed {" + join_set(observed) + "}.");
        }
    }

    return issues;
}

} // namespace dottalk::helpdata
