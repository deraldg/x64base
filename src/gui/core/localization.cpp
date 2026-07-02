#include "gui/core/localization.hpp"

#include "gui/core/generated_gui_messages.hpp"

#include <cctype>
#include <cstdlib>
#include <sstream>

namespace dottalk::gui {
namespace {

std::string lower_ascii(std::string value) {
    for (char& ch : value) {
        if (ch == '_') {
            ch = '-';
            continue;
        }
        ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
    }
    return value;
}

const generated::GuiMessageSeed* find_text(GuiTextId id) {
    for (const auto& row : generated::k_gui_message_seed) {
        if (row.id == id) {
            return &row;
        }
    }
    return nullptr;
}

const generated::GuiMessageSeed* find_text(std::string_view key) {
    for (const auto& row : generated::k_gui_message_seed) {
        if (key == row.key) {
            return &row;
        }
    }
    return nullptr;
}

std::string row_text(const generated::GuiMessageSeed& row, std::string_view locale) {
    const std::string normalized = normalize_locale(locale);
    if (normalized == "es") {
        return row.es;
    }
    if (normalized == "fr") {
        return row.fr;
    }
    if (normalized == "de") {
        return row.de;
    }
    if (normalized == "it") {
        return row.it;
    }
    return row.en_us;
}

GuiTextId severity_id(Severity severity) {
    switch (severity) {
    case Severity::info:
        return GuiTextId::SeverityInfo;
    case Severity::warning:
        return GuiTextId::SeverityWarning;
    case Severity::error:
        return GuiTextId::SeverityError;
    }
    return GuiTextId::SeverityInfo;
}

} // namespace

std::string normalize_locale(std::string_view locale) {
    std::string lowered = lower_ascii(std::string(locale));
    const auto dot = lowered.find('.');
    if (dot != std::string::npos) {
        lowered.resize(dot);
    }
    if (lowered == "default" || lowered.empty()) {
        return "en-US";
    }
    if (lowered == "en" || lowered == "en-us" || lowered == "enus") {
        return "en-US";
    }
    if (lowered == "es" || lowered == "es-es" || lowered == "es-mx") {
        return "es";
    }
    if (lowered == "fr" || lowered == "fr-fr" || lowered == "fr-ca") {
        return "fr";
    }
    if (lowered == "de" || lowered == "de-de") {
        return "de";
    }
    if (lowered == "it" || lowered == "it-it") {
        return "it";
    }
    return "en-US";
}

std::vector<std::string> available_gui_message_locales() {
    std::vector<std::string> locales;
    for (const auto* locale : generated::k_gui_message_locales) {
        locales.emplace_back(locale);
    }
    return locales;
}

bool is_gui_message_locale_supported(std::string_view locale) {
    const std::string normalized = normalize_locale(locale);
    for (const auto& supported : available_gui_message_locales()) {
        if (normalized == supported) {
            return true;
        }
    }
    return false;
}

LocaleContext locale_context_from_message_locale(std::string_view locale) {
    LocaleContext context;
    context.message_locale = normalize_locale(locale);
    context.display_locale = context.message_locale;
    context.parse_locale = context.message_locale;
    return context;
}

LocaleContext locale_context_from_environment() {
    const char* value = std::getenv("DOTTALK_GUI_LOCALE");
    if (!value || !*value) {
        value = std::getenv("DOTTALK_LOCALE");
    }
    if (!value || !*value) {
        value = std::getenv("LANG");
    }
    return locale_context_from_message_locale(value ? value : "en-US");
}

std::string gui_text_key(GuiTextId id) {
    const auto* row = find_text(id);
    return row ? row->key : std::string {};
}

std::string gui_text(GuiTextId id, const LocaleContext& locale) {
    const auto* row = find_text(id);
    return row ? row_text(*row, locale.message_locale) : std::string {};
}

std::string gui_text(std::string_view key, const LocaleContext& locale) {
    const auto* row = find_text(key);
    return row ? row_text(*row, locale.message_locale) : std::string {};
}

std::string render_label(std::string_view label_code,
                         std::string_view fallback,
                         const LocaleContext& locale) {
    if (!label_code.empty()) {
        const std::string resolved = gui_text(label_code, locale);
        if (!resolved.empty()) {
            return resolved;
        }
    }
    return std::string(fallback);
}

std::string render_status_text(const StatusMessage& message, const LocaleContext& locale) {
    const std::string resolved = gui_text(message.code, locale);
    if (!resolved.empty()) {
        return resolved;
    }
    return message.text;
}

std::string render_status_line(const StatusMessage& message, const LocaleContext& locale) {
    std::ostringstream line;
    line << gui_text(severity_id(message.severity), locale) << ": ";
    if (!message.code.empty()) {
        line << '[' << message.code << "] ";
    }
    line << render_status_text(message, locale);
    if (!message.detail.empty()) {
        line << ' ' << message.detail;
    }
    return line.str();
}

} // namespace dottalk::gui
