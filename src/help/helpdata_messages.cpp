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
            MessageId::ReplaceMultiUsageText,
            "REPLACE_MULTI_USAGE_TEXT",
            "COMMAND:REPLACE_MULTI",
            "USAGE",
            "INFO",
            "Usage:\n  REPLACE_MULTI USAGE\n  MULTIREP USAGE\n  REPLACE_MULTI <field> WITH <value>[, <field> WITH <value>]...\n  MULTIREP <field> WITH <value>[, <field> WITH <value>]...\nExamples:\n  MULTIREP LNAME WITH \"Smith\", FNAME WITH \"John\"\n  MULTIREP DOB WITH 20000101, ACTIVE WITH .T.\nNotes:\n  - REPLACE_MULTI requires an open table and a current record.\n  - All assignments are validated before the physical write.\n  - REPLACE_MULTI uses one record lock and one DBF write.\n  - Memo fields are written through the memo backend.\n  - Direct index maintenance uses before/after snapshots.\n  - Changed fields are marked STALE only if index maintenance fails."
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
            "  MAINT AI ASSIMILATE\n"
            "  MAINT CONTRACTS\n"
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
        { MessageId::ReplaceMultiUsageText, "en-US", "Usage:\n  REPLACE_MULTI USAGE\n  MULTIREP USAGE\n  REPLACE_MULTI <field> WITH <value>[, <field> WITH <value>]...\n  MULTIREP <field> WITH <value>[, <field> WITH <value>]...\nExamples:\n  MULTIREP LNAME WITH \"Smith\", FNAME WITH \"John\"\n  MULTIREP DOB WITH 20000101, ACTIVE WITH .T.\nNotes:\n  - REPLACE_MULTI requires an open table and a current record.\n  - All assignments are validated before the physical write.\n  - REPLACE_MULTI uses one record lock and one DBF write.\n  - Memo fields are written through the memo backend.\n  - Direct index maintenance uses before/after snapshots.\n  - Changed fields are marked STALE only if index maintenance fails." },
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
            "  MAINT AI ASSIMILATE\n"
            "  MAINT CONTRACTS\n"
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
