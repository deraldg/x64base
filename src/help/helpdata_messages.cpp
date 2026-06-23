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
            MessageId::MessageLocaleSet,
            "MESSAGE_LOCALE_SET",
            "SUBSYSTEM:MESSAGING",
            "STATUS",
            "INFO",
            "Message locale is {locale}"
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
        }
    };
    return messages;
}

const std::vector<MessageTextDef>& all_message_texts()
{
    static const std::vector<MessageTextDef> texts = {
        // en-US is explicit even though MessageDef::text remains the final fallback.
        { MessageId::HelpHintCommand,       "en-US", "Type HELP {command} for more information." },
        { MessageId::MessageLocaleSet,      "en-US", "Message locale is {locale}" },
        { MessageId::UnsupportedMessageLocale, "en-US", "Unsupported message locale: {locale}" },
        { MessageId::UnknownCommand,        "en-US", "Unknown command: {command}" },
        { MessageId::MissingArgument,       "en-US", "Missing required argument." },
        { MessageId::TooManyArguments,      "en-US", "Too many arguments." },
        { MessageId::InvalidSyntax,         "en-US", "Invalid command syntax." },
        { MessageId::InvalidOption,         "en-US", "Invalid option: {option}" },
        { MessageId::CommandNotImplemented, "en-US", "Command is recognized but not implemented: {command}" },
        { MessageId::CommandDeprecated,     "en-US", "Command is deprecated: {command}" },
        { MessageId::NoOpenTable,           "en-US", "No table is currently open." },
        { MessageId::NoSelectedArea,        "en-US", "No current work area is selected." },

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
        { MessageId::NoSelectedArea,        "de", "Es ist kein aktueller Arbeitsbereich ausgewaehlt." }
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
