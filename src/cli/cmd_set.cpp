// src/cli/cmd_set.cpp
// FoxPro-style SET command router for DotTalk++

// @dottalk.usage v1
// owner: DOT|SET
// command: SET
// category: settings
// status: supported
// noargs: usage
// effect: mixed
// mutates: settings output-routing table-buffer order-state filter-state relation-state path-state errorstop-policy
// usage-access: SET USAGE
// summary:
//   General SET dispatcher for session settings, output routing, table buffering,
//   paths, case/near behavior, and index/order/filter/relation subcommands.
//
// usage:
//   SET
//   SET USAGE
//   SET TABLE BUFFER ON
//   SET TABLE BUFFER OFF
//   SET TABLE BUFFER ON ALL
//   SET TABLE BUFFER OFF ALL
//   SET CONSOLE ON
//   SET CONSOLE OFF
//   SET PRINT ON
//   SET PRINT OFF
//   SET PRINT TO <file>
//   SET DEVICE TO SCREEN
//   SET DEVICE TO FILE <path>
//   SET DEVICE TO PRINTER
//   SET DEVICE TO NULL
//   SET ALTERNATE ON
//   SET ALTERNATE OFF
//   SET ALTERNATE TO <file>
//   SET TALK ON
//   SET TALK OFF
//   SET ECHO ON
//   SET ECHO OFF
//   SET PAGING ON
//   SET PAGING OFF
//   SET WRAP ON
//   SET WRAP OFF
//   SET DELETED ON
//   SET DELETED OFF
//   SET CASE ON
//   SET CASE OFF
//   SET NEAR ON
//   SET NEAR OFF
//   SET EDITOR TO <value>
//   SET EDITOR TO DEFAULT
//   SET EDITOR TO OFF
//   SET LANGUAGE
//   SET LANGUAGE TO <locale|DEFAULT>
//   SET LOCALE
//   SET LOCALE TO <locale|DEFAULT>
//   SET LANGUAGE CHECK
//   SET LANGUAGE REPORT
//   SET LOCALE CHECK
//   SET LOCALE REPORT
//   SET PATH <slot> <path>
//   SET INDEX <args>
//   SET ORDER <args>
//   SET FILTER <args>
//   SET RELATION <args>
//   SET CNX <args>
//   SET CDX <args>
//   SET LMDB <args>
//   SET ERRORSTOP
//   SET ERRORSTOP TO OFF | WARNING | ERROR
//
// notes:
//   SET with no arguments shows usage.
//   SET USAGE shows usage without mutating settings.
//   SET PATH, INDEX, ORDER, FILTER, RELATION, CNX, CDX, and LMDB delegate to their command handlers.
//   Output routing settings mutate session output behavior only.
//   TABLE BUFFER toggles table buffering state for the current area or all open areas.
//   SET CASE and SET NEAR mutate expression/search behavior settings.
//   SET may mutate table-buffer, order, path, relation, filter, and output state depending on the option.
//   SET ERRORSTOP [TO] <severity> is the compatibility form of STOP_ON_ERROR; it sets the
//   DotScript stop-on-error threshold (OFF|WARNING|ERROR), mutating errorstop policy only,
//   and with no severity reports the current threshold.
//
// risk:
//   mutates_session_settings: yes
//   mutates_output_routing: CONSOLE PRINT DEVICE ALTERNATE ECHO PAGING WRAP
//   mutates_table_buffer_state: TABLE BUFFER
//   mutates_path_state: PATH
//   mutates_index_order_state: INDEX ORDER CNX CDX LMDB
//   mutates_filter_state: FILTER
//   mutates_relation_state: RELATION RELATIONS
//   mutates_errorstop_policy: ERRORSTOP
//   mutates_table_data: no direct table-data mutation
//
// related:
//   SETPATH
//   SETINDEX
//   SETORDER
//   SETFILTER
//   SET_RELATION
//   SETCASE
//   SETNEAR
//   STOP_ON_ERROR
//

#include "xbase.hpp"

#include <algorithm>
#include <cctype>
#include <iterator>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

#include "cli/command_output.hpp"
#include "cli/output_router.hpp"
#include "cli/settings.hpp"
#include "xbase_error_context.hpp"   // SET ERRORSTOP -> stop_on_error[severity]
#include "cli/table_state.hpp"

#include "help/message_catalog.hpp"
#include "help/helpdata_messages.hpp"

// ---- Forward declarations ---------------------------------------------------
#if DOTTALK_HAS_XINDEX
void cmd_SETINDEX      (xbase::DbArea&, std::istringstream&);
void cmd_SETORDER      (xbase::DbArea&, std::istringstream&);
#endif
void cmd_SETFILTER     (xbase::DbArea&, std::istringstream&);
void cmd_SET_UNIQUE    (xbase::DbArea&, std::istringstream&);
void cmd_SET_RELATION  (xbase::DbArea&, std::istringstream&);
void cmd_SET_RELATIONS (xbase::DbArea&, std::istringstream&);
void cmd_SETCASE       (xbase::DbArea&, std::istringstream&);
void cmd_SETNEAR       (xbase::DbArea&, std::istringstream&);
void cmd_SETPATH       (xbase::DbArea&, std::istringstream&);
void cmd_SETTIMER      (xbase::DbArea&, std::istringstream&);
void cmd_PRN           (xbase::DbArea&, std::istringstream&);

#if DOTTALK_HAS_XINDEX
void cmd_SETCNX        (xbase::DbArea&, std::istringstream&);
#endif
#if DOTTALK_WITH_INDEX
void cmd_SETCDX        (xbase::DbArea&, std::istringstream&);
void cmd_SETLMDB       (xbase::DbArea&, std::istringstream&);
#endif

extern "C" xbase::XBaseEngine* shell_engine();

namespace {

static inline std::string up_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static inline std::string ltrim_copy(std::string s) {
    std::size_t i = 0;
    while (i < s.size() && std::isspace(static_cast<unsigned char>(s[i]))) ++i;
    return s.substr(i);
}

static inline std::string rtrim_copy(std::string s) {
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
    return s;
}

static inline std::string trim_copy(std::string s) {
    return rtrim_copy(ltrim_copy(std::move(s)));
}

static inline bool normalize_message_locale(std::string value, std::string& out_locale) {
    value = trim_copy(std::move(value));
    std::replace(value.begin(), value.end(), '_', '-');

    const std::string u = up_copy(value);

    if (u.empty() || u == "DEFAULT") {
        out_locale = "en-US";
        return true;
    }

    if (u == "EN" || u == "EN-US") {
        out_locale = "en-US";
        return true;
    }

    if (u == "ES" || u == "ES-ES") {
        out_locale = "es";
        return true;
    }

    if (u == "FR" || u == "FR-FR") {
        out_locale = "fr";
        return true;
    }

    if (u == "DE" || u == "DE-DE") {
        out_locale = "de";
        return true;
    }

    if (u == "IT" || u == "IT-IT") {
        out_locale = "it";
        return true;
    }

    return false;
}

static std::string join_strings(const std::vector<std::string>& values) {
    std::ostringstream oss;
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i) {
            oss << ", ";
        }
        oss << values[i];
    }
    return oss.str();
}

static std::string localized_yes_no(bool value) {
    return cli::cmdout::message_text(
        value ? dottalk::helpdata::MessageId::AboutYes
              : dottalk::helpdata::MessageId::AboutNo);
}

static std::string localized_none() {
    return cli::cmdout::message_text(dottalk::helpdata::MessageId::AboutNone);
}

static std::string display_or_none(const std::string& value) {
    return value.empty() ? localized_none() : value;
}

static std::string localized_validation_status(bool ok) {
    return cli::cmdout::message_text(
        ok ? dottalk::helpdata::MessageId::SetMessageCatalogValidationGreenLabel
           : dottalk::helpdata::MessageId::SetMessageCatalogValidationIssuesFoundLabel);
}

static void print_message_catalog_status() {
    const auto issues = dottalk::helpdata::validate_message_catalog();
    const auto locales = dottalk::helpdata::available_locales();

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::SetMessageCatalogValidationStatusText,
        {
            {"status", localized_validation_status(issues.empty())},
            {"message_count", std::to_string(dottalk::helpdata::all_messages().size())},
            {"text_row_count", std::to_string(dottalk::helpdata::all_message_texts().size())},
            {"locales", join_strings(locales)},
            {"issue_count", std::to_string(issues.size())}
        });

    for (const auto& issue : issues) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SetMessageCatalogValidationIssueRowText,
            {
                {"code", issue.code},
                {"key", issue.message_key},
                {"locale", issue.locale},
                {"detail", issue.detail}
            });
    }
}

static void print_message_catalog_report(const std::string& locale_filter = std::string()) {
    auto& out = cli::OutputRouter::instance().out();

    const auto& messages = dottalk::helpdata::all_messages();
    const auto& texts = dottalk::helpdata::all_message_texts();
    const auto locales = dottalk::helpdata::available_locales();
    const auto issues = dottalk::helpdata::validate_message_catalog();

    std::string normalized_filter;
    if (!trim_copy(locale_filter).empty()) {
        normalized_filter = dottalk::helpdata::normalize_locale(locale_filter);
    }

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::SetMessageCatalogReportHeaderText,
        {
            {"message_count", std::to_string(messages.size())},
            {"text_row_count", std::to_string(texts.size())},
            {"locales", join_strings(locales)},
            {"issue_count", std::to_string(issues.size())}
        });

    if (!normalized_filter.empty()) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SetMessageCatalogReportLocaleFilterLine,
            {{"locale", normalized_filter}});
    }

    out << "\n";
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::SetMessageCatalogReportSystemMessagesTitle);
    for (const auto& message : messages) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SetMessageCatalogReportMessageRow,
            {
                {"key", message.key ? message.key : ""},
                {"owner", message.owner ? message.owner : ""},
                {"category", message.category ? message.category : ""},
                {"severity", message.severity ? message.severity : ""}
            });
    }

    out << "\n";
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::SetMessageCatalogReportSystemMessageTextTitle);
    for (const auto& message : messages) {
        std::string rendered_locales;
        bool any = false;
        for (const auto& text : texts) {
            if (text.id != message.id) {
                continue;
            }
            const std::string locale = text.locale ? text.locale : "";
            if (!normalized_filter.empty() && locale != normalized_filter) {
                continue;
            }
            rendered_locales += any ? ", " : " ";
            rendered_locales += locale;
            any = true;
        }
        if (!any) {
            rendered_locales = " ";
            rendered_locales += cli::cmdout::message_text(
                dottalk::helpdata::MessageId::SetMessageCatalogReportNoMatchingTextRows);
        }
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SetMessageCatalogReportTextRow,
            {
                {"key", message.key ? message.key : ""},
                {"value", rendered_locales}
            });
    }
}

static void print_language_status(const std::string& current_locale) {
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::SetLanguageStatusText,
        {{"locale", current_locale}});
}

static inline std::string rest(std::istringstream& iss) {
    return std::string(std::istreambuf_iterator<char>(iss),
                       std::istreambuf_iterator<char>());
}

static inline bool parse_on_off(const std::string& tok, bool& out) {
    const std::string u = up_copy(tok);
    if (u == "ON")  { out = true;  return true; }
    if (u == "OFF") { out = false; return true; }
    return false;
}


// MSG-022E BEGIN message catalog provider status helper
static const char* message_catalog_mode_name(dottalk::helpdata::MessageCatalogMode mode) {
    switch (mode) {
        case dottalk::helpdata::MessageCatalogMode::ActiveDbf:
            return "active_dbf";
        case dottalk::helpdata::MessageCatalogMode::Auto:
            return "auto";
        case dottalk::helpdata::MessageCatalogMode::CompiledFallback:
        default:
            return "compiled_fallback";
    }
}

static void print_message_catalog_provider_status() {
    const auto status = dottalk::helpdata::active_message_catalog_status();

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::SetMessageCatalogProviderStatusText,
        {
            {"mode", message_catalog_mode_name(status.mode)},
            {"present", localized_yes_no(status.active_catalog_present)},
            {"loaded", localized_yes_no(status.active_catalog_loaded)},
            {"message_count", std::to_string(status.message_count)},
            {"text_row_count", std::to_string(status.text_row_count)},
            {"dbf_dir", display_or_none(status.active_dbf_dir)},
            {"indexes_dir", display_or_none(status.active_indexes_dir)},
            {"lmdb_dir", display_or_none(status.active_lmdb_dir)},
            {"detail", display_or_none(status.detail)}
        });
}
// MSG-022E END message catalog provider status helper

// MSG-022H BEGIN SET LANGUAGE active message emission helper
static void print_language_active_message_emission_check(const std::string& current_locale) {
    const auto status = dottalk::helpdata::active_message_catalog_status();
    const std::string text =
        dottalk::helpdata::format_message_catalog(current_locale, "HELP_HINT_COMMAND");

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::SetLanguageActiveMessageEmissionText,
        {
            {"locale", current_locale},
            {"mode", message_catalog_mode_name(status.mode)},
            {"loaded", localized_yes_no(status.active_catalog_loaded)},
            {"text", text.empty() ? localized_none() : text}
        });
}
// MSG-022H END SET LANGUAGE active message emission helper


// MSG-022O BEGIN routing proof mode helper
static bool message_routing_proof_enabled() {
    return dottalk::helpdata::message_routing_proof_enabled();
}

static void set_message_routing_proof_enabled(bool enabled) {
    dottalk::helpdata::set_message_routing_proof_enabled(enabled);
}


// MSG-022Y BEGIN SET MESSAGE PROOF status text catalog routing helpers
static bool msg22y_unresolved_message_text(const std::string& text, const std::string& symbol) {
    return text.empty() || text == symbol;
}

static std::string msg22y_current_message_locale() {
    const std::string locale = cli::Settings::instance().message_locale;
    return locale.empty() ? std::string("en-US") : locale;
}

static std::string msg22y_message_proof_mode_status(const std::string& mode) {
    const std::string symbol = "MESSAGE_PROOF_MODE_STATUS";
    const std::string locale = msg22y_current_message_locale();
    std::unordered_map<std::string, std::string> args;
    args["mode"] = mode;
    const std::string routed = dottalk::helpdata::format_message_catalog(symbol, locale, args);
    if (!msg22y_unresolved_message_text(routed, symbol)) {
        return routed;
    }

    // Preserve the English invariant prefix so existing regression checks and
    // scripts can continue to recognize proof-mode transitions after this seam
    // is routed. Localized suffixes make the active locale visible without
    // breaking the long-lived diagnostic contract.
    if (locale == "es") {
        return std::string("Message routing proof mode: ") + mode +
               " / Modo de prueba de enrutamiento de mensajes: " + mode;
    }
    if (locale == "fr") {
        return std::string("Message routing proof mode: ") + mode +
               " / Mode de preuve du routage des messages : " + mode;
    }
    if (locale == "de") {
        return std::string("Message routing proof mode: ") + mode +
               " / Nachrichten-Routing-Pruefmodus: " + mode;
    }
    if (locale == "it") {
        return std::string("Message routing proof mode: ") + mode +
               " / Modalita prova instradamento messaggi: " + mode;
    }
    return std::string("Message routing proof mode: ") + mode;
}

static std::string msg22y_message_proof_boundary_note() {
    const std::string symbol = "MESSAGE_PROOF_BOUNDARY_NOTE";
    const std::string locale = msg22y_current_message_locale();
    const std::unordered_map<std::string, std::string> args;
    const std::string routed = dottalk::helpdata::format_message_catalog(symbol, locale, args);
    if (!msg22y_unresolved_message_text(routed, symbol)) {
        return routed;
    }

    // Preserve the no-writeback tokens exactly; the regression pack depends on
    // them and they are also the safety contract users should see.
    const std::string invariant =
        "boundary: proof mode changes runtime diagnostic state only; "
        "no DBF/CDX/LMDB mutation; no runtime writeback";

    if (locale == "es") {
        return invariant + " / limite: el modo de prueba solo cambia el estado diagnostico";
    }
    if (locale == "fr") {
        return invariant + " / limite : le mode de preuve ne change que l'etat diagnostique";
    }
    if (locale == "de") {
        return invariant + " / Grenze: Der Pruefmodus aendert nur den Diagnosestatus";
    }
    if (locale == "it") {
        return invariant + " / confine: la modalita prova cambia solo lo stato diagnostico";
    }
    return invariant;
}
// MSG-022Y END SET MESSAGE PROOF status text catalog routing helpers

static void print_message_proof_status() {
    // MSG-022Y ROUTED SET MESSAGE PROOF status text
    const std::string mode = dottalk::helpdata::message_routing_proof_enabled() ? "on" : "off";
    cli::cmdout::print_line(msg22y_message_proof_mode_status(mode));
    cli::cmdout::print_line(msg22y_message_proof_boundary_note());
}

static void handle_set_message_proof(std::istringstream& args) {
    std::string mode;
    args >> mode;
    const std::string up = up_copy(mode);

    if (up == "ON") {
        set_message_routing_proof_enabled(true);
        print_message_proof_status();
        return;
    }

    if (up == "OFF") {
        set_message_routing_proof_enabled(false);
        print_message_proof_status();
        return;
    }

    if (up == "CHECK" || up == "STATUS" || up.empty()) {
        print_message_proof_status();
        return;
    }

    cli::cmdout::print_message(dottalk::helpdata::MessageId::SetMessageProofUsageText);
}
// MSG-022O END routing proof mode helper


// MSG-022I-B BEGIN controlled message emit helper
static void print_message_emit_usage() {
    cli::cmdout::print_message(dottalk::helpdata::MessageId::SetMessageEmitUsageText);
}

static void message_replace_all(std::string& text, const std::string& needle, const std::string& value) {
    if (needle.empty()) {
        return;
    }

    std::string::size_type pos = 0;
    while ((pos = text.find(needle, pos)) != std::string::npos) {
        text.replace(pos, needle.size(), value);
        pos += value.size();
    }
}

static bool message_apply_single_placeholder_arg(std::string& text,
                                                 const std::string& arg_name,
                                                 const std::string& arg_value) {
    if (arg_name.empty()) {
        return false;
    }

    const std::string lower_token = "{" + arg_name + "}";
    std::string upper_name = arg_name;
    for (char& ch : upper_name) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    const std::string upper_token = "{" + upper_name + "}";

    const bool had_lower = text.find(lower_token) != std::string::npos;
    const bool had_upper = text.find(upper_token) != std::string::npos;

    message_replace_all(text, lower_token, arg_value);
    message_replace_all(text, upper_token, arg_value);

    return had_lower || had_upper;
}

static void handle_set_message_emit(std::istringstream& args, const std::string& default_locale) {
    std::string symbol;
    args >> symbol;
    if (symbol.empty()) {
        print_message_emit_usage();
        return;
    }

    std::string locale = default_locale.empty()
        ? std::string("en-US")
        : default_locale;

    std::string arg_name;
    std::string arg_value;

    std::string tok;
    while (args >> tok) {
        const std::string up = up_copy(tok);
        if (up == "LOCALE" || up == "LANGUAGE" || up == "TO") {
            std::string value;
            args >> value;
            if (!value.empty()) {
                locale = value;
            }
            continue;
        }

        if (up == "ARG") {
            std::string name;
            std::string value;
            args >> name;
            args >> value;
            if (!name.empty() && !value.empty()) {
                arg_name = name;
                arg_value = value;
            }
            continue;
        }
    }

    const auto status = dottalk::helpdata::active_message_catalog_status();
    const std::string raw_text = dottalk::helpdata::format_message_catalog(locale, symbol);
    std::string text = raw_text;
    bool substituted = false;

    if (!arg_name.empty()) {
        substituted = message_apply_single_placeholder_arg(text, arg_name, arg_value);
    }

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::SetMessageEmitStatusText,
        {
            {"current_locale", locale},
            {"mode", message_catalog_mode_name(status.mode)},
            {"present", localized_yes_no(status.active_catalog_present)},
            {"loaded", localized_yes_no(status.active_catalog_loaded)},
            {"message_count", std::to_string(status.message_count)},
            {"text_row_count", std::to_string(status.text_row_count)},
            {"symbol", symbol},
            {"locale", locale},
            {"placeholder_arg", arg_name.empty() ? localized_none() : (arg_name + "=" + arg_value)},
            {"substituted", localized_yes_no(substituted)},
            {"text", text.empty() ? localized_none() : text},
            {"proof", localized_yes_no(status.active_catalog_loaded && !text.empty())}
        });
}
// MSG-022I-B END controlled message emit helper

static void print_set_usage() {
    cli::cmdout::print_message(dottalk::helpdata::MessageId::SetUsageText);
}

} // namespace

void cmd_SET(xbase::DbArea& A, std::istringstream& args) {
    using cli::Settings;

    auto& S   = Settings::instance();
    auto& R   = cli::OutputRouter::instance();
    auto& out = R.out();

    std::string opt;
    if (!(args >> opt)) {
        print_set_usage();
        return;
    }
    opt = up_copy(opt);

    if (opt == "USAGE" || opt == "HELP" || opt == "?") {
        print_set_usage();
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET LANGUAGE / SET LOCALE
    // Selects the active message-rendering locale. This does not
    // localize command keywords; it selects message text templates.
    // ─────────────────────────────────────────────────────────────
    if (opt == "LANGUAGE" || opt == "LOCALE") {
        std::string tok;
        if (!(args >> tok)) {
            print_language_status(S.message_locale);
            return;
        }

        const std::string tok_up = up_copy(tok);
        if (tok_up == "CHECK" || tok_up == "VALIDATE" || tok_up == "CATALOG") {
            print_message_catalog_status();
            print_language_active_message_emission_check(S.message_locale);
            return;
        }
        if (tok_up == "REPORT" || tok_up == "EXPORT") {
            print_message_catalog_report(ltrim_copy(rest(args)));
            return;
        }
        if (tok_up == "STATUS") {
            print_language_status(S.message_locale);
            return;
        }

        std::string value;
        if (tok_up == "TO") {
            value = ltrim_copy(rest(args));
        } else {
            value = tok;
            const std::string tail = ltrim_copy(rest(args));
            if (!tail.empty()) {
                value += " ";
                value += tail;
            }
        }

        std::string normalized;
        if (!normalize_message_locale(value, normalized)) {
            // MSG-022Q BEGIN unsupported locale active provider routing
            {
                const auto msg_status = dottalk::helpdata::active_message_catalog_status();
                std::string routed_text;

                if (msg_status.active_catalog_loaded) {
                    routed_text = dottalk::helpdata::format_message_catalog(S.message_locale, "UNSUPPORTED_MESSAGE_LOCALE");
                    message_apply_single_placeholder_arg(routed_text, "locale", value);
                    message_apply_single_placeholder_arg(routed_text, "language", value);
                }

                if (!routed_text.empty()) {
                    out << routed_text << "\n";
                    if (message_routing_proof_enabled()) {
                        cli::cmdout::print_message(
                            dottalk::helpdata::MessageId::MessageRoutingProofLine,
                            {{"provider", "active_dbf"}, {"symbol", "UNSUPPORTED_MESSAGE_LOCALE"}});
                    }
                    print_language_status(S.message_locale);
                    return;
                }
            }
            // MSG-022Q END unsupported locale active provider routing
            out << dottalk::helpdata::format_message(
                       dottalk::helpdata::MessageId::UnsupportedMessageLocale,
                       {{"locale", value}},
                       S.message_locale)
                << "\n";
            print_language_status(S.message_locale);
            return;
        }

        S.message_locale = normalized;
    // MSG-022M BEGIN SET LANGUAGE active provider routing
    {
        const auto msg_status = dottalk::helpdata::active_message_catalog_status();
        std::string routed_text;

        if (msg_status.active_catalog_loaded) {
            routed_text = dottalk::helpdata::format_message_catalog(S.message_locale, "MESSAGE_LOCALE_SET");
            message_apply_single_placeholder_arg(routed_text, "locale", S.message_locale);
            message_apply_single_placeholder_arg(routed_text, "language", S.message_locale);
        }

        if (!routed_text.empty()) {
            auto& route_out = cli::OutputRouter::instance().out();
            route_out << routed_text << "\n";
            if (message_routing_proof_enabled()) {
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::MessageRoutingProofLine,
                    {{"provider", "active_dbf"}, {"symbol", "MESSAGE_LOCALE_SET"}});
            }
            return;
        }
    }
    // MSG-022M END SET LANGUAGE active provider routing
        out << dottalk::helpdata::format_message(
                   dottalk::helpdata::MessageId::MessageLocaleSet,
                   {{"locale", S.message_locale}},
                   S.message_locale)
            << "\n";
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET TABLE BUFFER
    // ─────────────────────────────────────────────────────────────


// MSG-022E BEGIN SET MESSAGE CATALOG CHECK
    if (opt == "MESSAGE") {
        std::string sub1;
        args >> sub1;
        sub1 = up_copy(sub1);

        if (sub1 == "CATALOG") {
            std::string sub2;
            args >> sub2;
            sub2 = up_copy(sub2);

            if (sub2 == "CHECK" || sub2 == "STATUS") {
                print_message_catalog_provider_status();
                return;
            }

            print_message_emit_usage();
            return;
        }

        if (sub1 == "PROOF") {
            handle_set_message_proof(args);
            return;
        }

        if (sub1 == "EMIT") {
            handle_set_message_emit(args, S.message_locale);
            return;
        }

        print_message_emit_usage();
        return;
    }
    // MSG-022E END SET MESSAGE CATALOG CHECK



    if (opt == "TABLE") {
        std::string sub;
        args >> sub;
        sub = up_copy(sub);

        if (sub == "BUFFER") {
            std::string tok;
            args >> tok;

            bool on = false;
            if (!parse_on_off(tok, on)) {
                cli::cmdout::print_message(dottalk::helpdata::MessageId::SetTableBufferUsageText);
                return;
            }

            std::string scope;
            args >> scope;
            const bool all = (up_copy(scope) == "ALL");

            auto* eng = shell_engine();
            if (!eng) {
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::SetTableBufferEngineUnavailableText);
                return;
            }

            int changed = 0;

            if (all) {
                for (int i = 0; i < xbase::MAX_AREA; ++i) {
                    xbase::DbArea& area = eng->area(i);
                    if (area.filename().empty()) continue;

                    dottalk::table::set_enabled(i, on);
                    ++changed;
                }
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::SetTableBufferAllStatusText,
                    {
                        {"state", on ? "ON" : "OFF"},
                        {"count", std::to_string(changed)}
                    });
                return;
            }

            int area0 = -1;
            for (int i = 0; i < xbase::MAX_AREA; ++i) {
                if (&eng->area(i) == &A) {
                    area0 = i;
                    break;
                }
            }

            if (area0 < 0) {
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::SetTableBufferCannotDetermineCurrentAreaText);
                return;
            }

            dottalk::table::set_enabled(area0, on);

            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::SetTableBufferAreaStatusText,
                {
                    {"state", on ? "ON" : "OFF"},
                    {"area", std::to_string(area0)}
                });
            return;
        }

        cli::cmdout::print_message(dottalk::helpdata::MessageId::SetTableBufferUsageText);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET CONSOLE
    // Fox-style alias for PRN TO CONSOLE / PRN TO NULL
    // ─────────────────────────────────────────────────────────────
    if (opt == "CONSOLE") {
        std::string tok;
        args >> tok;

        bool on = (R.dest() == cli::OutputDest::Console);
        if (!parse_on_off(tok, on)) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetConsoleUsageText);
            return;
        }

        if (on) {
            R.set_dest_console();
            R.console_note(cli::cmdout::message_text(
                dottalk::helpdata::MessageId::SetPrnConsoleNoteText));
        } else {
            R.console_note(cli::cmdout::message_text(
                dottalk::helpdata::MessageId::SetPrnNullNoteText));
            R.set_dest_null();
        }
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET PRINT
    // Fox-style alias for PRN TO FILE / PRN OFF
    // ─────────────────────────────────────────────────────────────
    if (opt == "PRINT") {
        std::string tok;
        args >> tok;

        if (tok.empty()) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetPrintUsageText);
            return;
        }

        const std::string u = up_copy(tok);

        if (u == "TO") {
            std::string tail = ltrim_copy(rest(args));
            if (tail.empty()) {
                cli::cmdout::print_message(dottalk::helpdata::MessageId::SetPrintToUsageText);
                return;
            }

            if (!R.set_dest_file(tail)) {
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::SetPrintToFailedText,
                    {{"path", tail}});
                return;
            }

            R.console_note(cli::cmdout::message_text(
                dottalk::helpdata::MessageId::SetPrnFileNoteText,
                {{"path", R.prn_file_path()}}));
            return;
        }

        bool on = (R.dest() == cli::OutputDest::File);
        if (!parse_on_off(tok, on)) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetPrintUsageText);
            return;
        }

        if (on) {
            if (!R.prn_file_path().empty()) {
                (void)R.set_dest_file(R.prn_file_path());
                R.console_note(cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::SetPrnFileNoteText,
                    {{"path", R.prn_file_path()}}));
            } else {
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::SetPrintOnRequiresFileText);
            }
        } else {
            R.console_note(cli::cmdout::message_text(
                dottalk::helpdata::MessageId::SetPrnNullNoteText));
            R.set_dest_null();
        }
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET ALTERNATE
    // ─────────────────────────────────────────────────────────────
    if (opt == "ALTERNATE") {
        std::string tok;
        args >> tok;

        if (tok.empty()) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetAlternateUsageText);
            return;
        }

        const std::string u = up_copy(tok);

        if (u == "TO") {
            std::string tail = ltrim_copy(rest(args));
            if (tail.empty()) {
                cli::cmdout::print_message(dottalk::helpdata::MessageId::SetAlternateToUsageText);
                return;
            }

            if (!R.set_alternate_to(tail)) {
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::SetAlternateToFailedText,
                    {{"path", tail}});
                return;
            }

            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::SetAlternateToStatusText,
                {{"path", R.alternate_to_path()}});
            return;
        }

        bool on = R.alternate_on();
        if (!parse_on_off(tok, on)) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetAlternateUsageText);
            return;
        }

        R.set_alternate(on);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SetAlternateStatusText,
            {{"state", on ? "ON" : "OFF"}});
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET TALK
    // ─────────────────────────────────────────────────────────────
    if (opt == "TALK") {
        std::string tok;
        args >> tok;

        bool on = S.talk_on.load();
        if (!parse_on_off(tok, on)) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetTalkUsageText);
            return;
        }

        R.set_talk(on);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SetTalkStatusText,
            {{"state", on ? "ON" : "OFF"}});
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET ECHO
    // ─────────────────────────────────────────────────────────────
    if (opt == "ECHO") {
        std::string tok;
        args >> tok;

        bool on = R.echo_on();
        if (!parse_on_off(tok, on)) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetEchoUsageText);
            return;
        }

        R.set_echo(on);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SetEchoStatusText,
            {{"state", on ? "ON" : "OFF"}});
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET PAGING
    // ─────────────────────────────────────────────────────────────
    if (opt == "PAGING") {
        std::string tok;
        args >> tok;

        bool on = R.paging_on();
        if (!parse_on_off(tok, on)) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetPagingUsageText);
            return;
        }

        R.set_paging(on);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SetPagingStatusText,
            {{"state", on ? "ON" : "OFF"}});
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET WRAP
    // ─────────────────────────────────────────────────────────────
    if (opt == "WRAP") {
        std::string tok;
        args >> tok;

        bool on = R.wrap_on();
        if (!parse_on_off(tok, on)) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetWrapUsageText);
            return;
        }

        R.set_wrap(on);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SetWrapStatusText,
            {{"state", on ? "ON" : "OFF"}});
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET DEVDIAG
    // Controls passive startup/shutdown/relation diagnostics in dev builds.
    // Explicit command traces remain under their own command surfaces.
    // ─────────────────────────────────────────────────────────────
    if (opt == "DEVDIAG") {
        std::string tok;
        if (!(args >> tok)) {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::SetDevdiagStatusText,
                {{"state", cli::Settings::passiveDevDiagnosticsEnabled() ? "ON" : "OFF"}});
            return;
        }

        const std::string up = up_copy(tok);
        if (up == "STATUS" || up == "CHECK") {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::SetDevdiagStatusText,
                {{"state", cli::Settings::passiveDevDiagnosticsEnabled() ? "ON" : "OFF"}});
            return;
        }

        bool on = cli::Settings::passiveDevDiagnosticsEnabled();
        if (!parse_on_off(tok, on)) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetDevdiagUsageText);
            return;
        }

        cli::Settings::setPassiveDevDiagnostics(on);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SetDevdiagStatusText,
            {{"state", on ? "ON" : "OFF"}});
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET TIMER
    // ─────────────────────────────────────────────────────────────
    if (opt == "TIMER") {
        std::string tok;
        args >> tok;

        bool on = S.timer_on.load();
        if (!parse_on_off(tok, on)) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetTimerUsageText);
            return;
        }

        S.timer_on.store(on);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SetTimerStatusText,
            {{"state", on ? "ON" : "OFF"}});
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET POLLING
    // ─────────────────────────────────────────────────────────────
    if (opt == "POLLING") {
        std::string tok;
        args >> tok;

        bool on = S.polling_on.load();
        if (!parse_on_off(tok, on)) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetPollingUsageText);
            return;
        }

        S.polling_on.store(on);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SetPollingStatusText,
            {{"state", on ? "ON" : "OFF"}});
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET DELETED
    // ─────────────────────────────────────────────────────────────
    if (opt == "DELETED") {
        std::string tok;
        args >> tok;

        bool on = S.deleted_on.load();
        if (!parse_on_off(tok, on)) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetDeletedUsageText);
            return;
        }

        S.deleted_on.store(on);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SetDeletedStatusText,
            {{"state", on ? "HIDE (ON)" : "SHOW (OFF)"}});
        return;
    }

    // SET INDEXTXN ON|OFF  (transactional in-COMMIT index maintenance)
    // Default OFF: COMMIT keeps the legacy batch behavior (BUILDLMDB / REBUILD /
    // REINDEX). ON enables incremental maintenance inside COMMIT for the active
    // transactional (CDX/LMDB) backend. print_line keeps it message-catalog-free.
    if (opt == "INDEXTXN") {
        std::string tok;
        if (!(args >> tok)) {
            cli::cmdout::print_line(std::string("SET INDEXTXN: ") +
                (S.index_txn_on.load() ? "ON" : "OFF"));
            return;
        }
        const std::string up = up_copy(tok);
        if (up == "STATUS" || up == "CHECK") {
            cli::cmdout::print_line(std::string("SET INDEXTXN: ") +
                (S.index_txn_on.load() ? "ON" : "OFF"));
            return;
        }
        if (up == "USAGE" || up == "HELP" || up == "?") {
            cli::cmdout::print_line("Usage: SET INDEXTXN ON|OFF   (default OFF = legacy batch rebuild)");
            return;
        }
        bool on = S.index_txn_on.load();
        if (!parse_on_off(tok, on)) {
            cli::cmdout::print_line("Usage: SET INDEXTXN ON|OFF");
            return;
        }
        S.index_txn_on.store(on);
        cli::cmdout::print_line(std::string("SET INDEXTXN: ") + (on ? "ON" : "OFF"));
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET ERRORSTOP [TO] OFF|WARNING|ERROR
    // Compatibility form of the native STOP_ON_ERROR command. Sets the severity
    // at which a running DotScript aborts. Errors derive from messaging: the
    // threshold is compared against the severity carried by the recorded
    // canonical error code.
    // ─────────────────────────────────────────────────────────────
    if (opt == "ERRORSTOP") {
        std::string tail = ltrim_copy(rest(args));
        {
            // Accept an optional leading TO (SET ERRORSTOP TO ERROR).
            std::istringstream ts(tail);
            std::string first;
            ts >> first;
            if (up_copy(first) == "TO") {
                tail = ltrim_copy(rest(ts));
            }
        }

        // Drop an inline "&&" comment and keep the first token as the severity.
        {
            const std::string::size_type amp = tail.find("&&");
            if (amp != std::string::npos) tail.erase(amp);
        }
        std::string sev;
        {
            std::istringstream sev_toks(tail);
            sev_toks >> sev;
        }

        if (sev.empty()) {
            cli::cmdout::print_info(
                "SET ERRORSTOP",
                std::string("threshold is ") +
                    xbase::error::errorstop_level_name(xbase::error::get_errorstop()));
            return;
        }

        bool ok = false;
        const xbase::error::errorstop_level lvl =
            xbase::error::parse_errorstop_level(sev, &ok);
        if (!ok) {
            xbase::error::set_last_error(xbase::error::e_invalid_argument());
            cli::cmdout::print_info(
                "SET ERRORSTOP",
                std::string("invalid severity '") + sev + "'; use OFF, WARNING, or ERROR.");
            return;
        }

        xbase::error::set_errorstop(lvl);
        cli::cmdout::print_info(
            "SET ERRORSTOP",
            std::string("threshold set to ") + xbase::error::errorstop_level_name(lvl));
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET CASE
    // Routes Fox-style SET CASE ON|OFF through the SETCASE handler.
    // Direct SETCASE remains available through the command registry.
    // ─────────────────────────────────────────────────────────────
    if (opt == "CASE" || opt == "SETCASE") {
        std::istringstream r(rest(args));
        cmd_SETCASE(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET NEAR
    // SEEK remains exact while NEAR is OFF. When NEAR is ON, SEEK/FIND
    // may later use nearest greater/equal ordered-key behavior.
    // ─────────────────────────────────────────────────────────────
    if (opt == "NEAR" || opt == "SETNEAR") {
        std::istringstream r(rest(args));
        cmd_SETNEAR(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET EDITOR TO <value|DEFAULT|OFF>
    // ─────────────────────────────────────────────────────────────
    if (opt == "EDITOR") {
        std::string sub;
        args >> sub;

        if (sub.empty()) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetEditorUsageText);
            return;
        }

        sub = up_copy(sub);
        if (sub != "TO") {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetEditorUsageText);
            return;
        }

        std::string tail = ltrim_copy(rest(args));
        if (tail.empty()) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetEditorUsageText);
            return;
        }

        const std::string tail_up = up_copy(tail);

        if (tail_up == "OFF") {
            S.editor.mode = cli::EditorMode::Off;
            S.editor.command.clear();
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetEditorOffStatusText);
            return;
        }

        if (tail_up == "DEFAULT") {
            S.editor.mode = cli::EditorMode::Default;
            S.editor.command.clear();
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetEditorDefaultStatusText);
            return;
        }

        S.editor.mode = cli::EditorMode::Custom;
        S.editor.command = tail;

        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::SetEditorCustomStatusText,
            {{"value", S.editor.command}});
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET DEVICE TO SCREEN|FILE <path>|PRINTER [name]|NULL
    // Fox-style alias for PRN
    // ─────────────────────────────────────────────────────────────
    if (opt == "DEVICE") {
        std::string sub;
        args >> sub;

        if (up_copy(sub) != "TO") {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::SetDeviceUsageText);
            return;
        }

        std::string mode;
        args >> mode;
        mode = up_copy(mode);

        if (mode == "SCREEN" || mode == "CONSOLE") {
            R.set_dest_console();
            R.console_note(cli::cmdout::message_text(
                dottalk::helpdata::MessageId::SetPrnConsoleNoteText));
            return;
        }

        if (mode == "NULL" || mode == "OFF") {
            R.console_note(cli::cmdout::message_text(
                dottalk::helpdata::MessageId::SetPrnNullNoteText));
            R.set_dest_null();
            return;
        }

        if (mode == "FILE") {
            std::string path = ltrim_copy(rest(args));
            if (path.empty()) {
                cli::cmdout::print_message(dottalk::helpdata::MessageId::SetDeviceFileUsageText);
                return;
            }
            if (!R.set_dest_file(path)) {
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::SetDeviceFileFailedText,
                    {{"path", path}});
                return;
            }
            R.console_note(cli::cmdout::message_text(
                dottalk::helpdata::MessageId::SetPrnFileNoteText,
                {{"path", R.prn_file_path()}}));
            return;
        }

        if (mode == "PRINTER") {
            std::string printer_name = ltrim_copy(rest(args));
            if (!R.set_dest_printer(printer_name)) {
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::SetDevicePrinterFailedText);
                return;
            }
            if (R.prn_uses_default_printer()) {
                R.console_note(cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::SetPrnPrinterDefaultStagedNoteText));
            } else {
                R.console_note(cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::SetPrnPrinterNamedStagedNoteText,
                    {{"name", R.prn_printer_name()}}));
            }
            return;
        }

        cli::cmdout::print_message(dottalk::helpdata::MessageId::SetDeviceUsageText);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET UNIQUE
    // ─────────────────────────────────────────────────────────────
    if (opt == "UNIQUE") {
        std::istringstream r(rest(args));
        cmd_SET_UNIQUE(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET PATH
    // ─────────────────────────────────────────────────────────────
    if (opt == "PATH") {
        std::istringstream r(rest(args));
        cmd_SETPATH(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET INDEX
    // ─────────────────────────────────────────────────────────────
#if DOTTALK_HAS_XINDEX
    if (opt == "INDEX") {
        std::istringstream r(rest(args));
        cmd_SETINDEX(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET ORDER
    // ─────────────────────────────────────────────────────────────
    if (opt == "ORDER") {
        std::istringstream r(rest(args));
        cmd_SETORDER(A, r);
        return;
    }
#endif

#if DOTTALK_WITH_DEV
    // ─────────────────────────────────────────────────────────────
    // SET FILTER
    // ─────────────────────────────────────────────────────────────
    if (opt == "FILTER") {
        std::istringstream r(rest(args));
        cmd_SETFILTER(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET RELATION
    // ─────────────────────────────────────────────────────────────
    if (opt == "RELATION") {
        std::istringstream r(rest(args));
        cmd_SET_RELATION(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET RELATIONS
    // ─────────────────────────────────────────────────────────────
    if (opt == "RELATIONS") {
        std::istringstream r(rest(args));
        cmd_SET_RELATIONS(A, r);
        return;
    }

#endif

#if DOTTALK_HAS_XINDEX
    // SET CNX is available in both legacy and LMDB index profiles.
    if (opt == "CNX") {
        std::istringstream r(rest(args));
        cmd_SETCNX(A, r);
        return;
    }
#endif

#if DOTTALK_WITH_INDEX
    // SET CDX / LMDB are LMDB-index profile commands.
    if (opt == "CDX") {
        std::istringstream r(rest(args));
        cmd_SETCDX(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET LMDB
    // ─────────────────────────────────────────────────────────────
    if (opt == "LMDB") {
        std::istringstream r(rest(args));
        cmd_SETLMDB(A, r);
        return;
    }
#endif

    print_set_usage();
}
