// ============================================================================
// File: src/help/helpdata_messages.hpp
// Purpose: Shared, compiled, reusable HELP/system message registry.
//
// DotTalk++ message localization boundary:
//   - DotScript / xBase command verbs remain English and canonical.
//   - Runtime messages, HELP prose, instructions, and lessons may be localized.
//
// This compiled registry is the phase-two analogue of the approved catalog
// model:
//   SYSTEM_MESSAGES      -> stable message identity / owner / category / severity
//   SYSTEM_MESSAGE_TEXT  -> message id + locale + localized template
// ============================================================================
#pragma once

#include <string>
#include <unordered_map>
#include <vector>

namespace dottalk::helpdata {

enum class MessageId {
    HelpHintCommand,
    MessageLocaleSet,
    UnsupportedMessageLocale,
    UnknownCommand,
    MissingArgument,
    TooManyArguments,
    InvalidSyntax,
    InvalidOption,
    CommandNotImplemented,
    CommandDeprecated,
    NoOpenTable,
    NoSelectedArea
};

struct MessageDef {
    MessageId   id;
    const char* key;      // Stable symbolic id, future SYSTEM_MESSAGES.SYMBOL.
    const char* owner;    // GLOBAL, COMMAND:<name>, SUBSYSTEM:<name>.
    const char* category; // HINT, ERROR, WARNING, STATUS, etc.
    const char* severity; // INFO, WARNING, ERROR, FATAL.
    const char* text;     // Default/fallback text. May contain {placeholders}.
};

struct MessageTextDef {
    MessageId   id;
    const char* locale;   // Normalized locale key: en-US, it, es, fr, de.
    const char* text;     // Localized template. May contain {placeholders}.
};

struct MessageCatalogIssue {
    std::string code;        // e.g. MISSING_EN_US_TEXT, PLACEHOLDER_MISMATCH.
    std::string message_key; // MessageDef::key when available.
    std::string locale;      // Locale involved, if any.
    std::string detail;      // Human-readable diagnostic.
};

const char* default_locale();

const std::vector<MessageDef>& all_messages();
const std::vector<MessageTextDef>& all_message_texts();

const MessageDef* find_message(MessageId id);
const MessageDef* find_message_by_key(const std::string& key);
const char* message_key(MessageId id);

std::vector<std::string> available_locales();
std::string normalize_locale(const std::string& locale);
bool is_supported_locale(const std::string& locale);
std::vector<std::string> locale_fallback_chain(const std::string& locale);

const char* find_message_text(MessageId id, const std::string& locale = "en-US");

std::string format_message(MessageId id,
                           const std::unordered_map<std::string, std::string>& vars = {},
                           const std::string& locale = "en-US");

// Report-only validation hook for CMDHELPCHK / MAINT / metadata promotion.
// This does not mutate HELP DATA, DBFs, catalogs, source, or runtime state.
std::vector<MessageCatalogIssue> validate_message_catalog();

} // namespace dottalk::helpdata
