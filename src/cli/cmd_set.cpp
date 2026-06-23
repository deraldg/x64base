// src/cli/cmd_set.cpp
// FoxPro-style SET command router for DotTalk++

// @dottalk.usage v1
// owner: DOT|SET
// command: SET
// category: settings
// status: supported
// noargs: usage
// effect: mixed
// mutates: settings output-routing table-buffer order-state filter-state relation-state path-state
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
//
// notes:
//   SET with no arguments shows usage.
//   SET USAGE shows usage without mutating settings.
//   SET PATH, INDEX, ORDER, FILTER, RELATION, CNX, CDX, and LMDB delegate to their command handlers.
//   Output routing settings mutate session output behavior only.
//   TABLE BUFFER toggles table buffering state for the current area or all open areas.
//   SET CASE and SET NEAR mutate expression/search behavior settings.
//   SET may mutate table-buffer, order, path, relation, filter, and output state depending on the option.
//
// risk:
//   mutates_session_settings: yes
//   mutates_output_routing: CONSOLE PRINT DEVICE ALTERNATE ECHO PAGING WRAP
//   mutates_table_buffer_state: TABLE BUFFER
//   mutates_path_state: PATH
//   mutates_index_order_state: INDEX ORDER CNX CDX LMDB
//   mutates_filter_state: FILTER
//   mutates_relation_state: RELATION RELATIONS
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
//

#include "xbase.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <iterator>
#include <sstream>
#include <string>
#include <vector>
#include <unordered_map>

#include "cli/output_router.hpp"
#include "cli/settings.hpp"
#include "cli/table_state.hpp"

#include "help/message_catalog.hpp"
#include "help/helpdata_messages.hpp"

// ---- Forward declarations ---------------------------------------------------
void cmd_SETINDEX      (xbase::DbArea&, std::istringstream&);
void cmd_SETORDER      (xbase::DbArea&, std::istringstream&);
void cmd_SETFILTER     (xbase::DbArea&, std::istringstream&);
void cmd_SET_UNIQUE    (xbase::DbArea&, std::istringstream&);
void cmd_SET_RELATION  (xbase::DbArea&, std::istringstream&);
void cmd_SET_RELATIONS (xbase::DbArea&, std::istringstream&);
void cmd_SETCASE       (xbase::DbArea&, std::istringstream&);
void cmd_SETNEAR       (xbase::DbArea&, std::istringstream&);
void cmd_SETPATH       (xbase::DbArea&, std::istringstream&);
void cmd_SETTIMER      (xbase::DbArea&, std::istringstream&);
void cmd_PRN           (xbase::DbArea&, std::istringstream&);

#if DOTTALK_WITH_DEV
void cmd_SETCNX        (xbase::DbArea&, std::istringstream&);
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

static void print_message_catalog_status() {
    auto& out = cli::OutputRouter::instance().out();

    const auto issues = dottalk::helpdata::validate_message_catalog();
    const auto locales = dottalk::helpdata::available_locales();

    out << "Message catalog validation: " << (issues.empty() ? "green" : "issues found") << "\n"
        << "  messages: " << dottalk::helpdata::all_messages().size() << "\n"
        << "  text rows: " << dottalk::helpdata::all_message_texts().size() << "\n"
        << "  locales: " << join_strings(locales) << "\n"
        << "  issues: " << issues.size() << "\n";

    for (const auto& issue : issues) {
        out << "  " << issue.code
            << " key=" << issue.message_key
            << " locale=" << issue.locale
            << " detail=" << issue.detail
            << "\n";
    }

    out << "  boundary: report-only; no DBF, HELP DATA, CMDHELPCHK, source-mining, or catalog mutation.\n";
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

    out << "Message catalog report: report-only\n"
        << "  schema intent: SYSTEM_MESSAGES + SYSTEM_MESSAGE_TEXT\n"
        << "  messages: " << messages.size() << "\n"
        << "  text rows: " << texts.size() << "\n"
        << "  locales: " << join_strings(locales) << "\n"
        << "  validation issues: " << issues.size() << "\n";

    if (!normalized_filter.empty()) {
        out << "  locale filter: " << normalized_filter << "\n";
    }

    out << "\nSYSTEM_MESSAGES preview:\n";
    for (const auto& message : messages) {
        out << "  " << (message.key ? message.key : "")
            << " | owner=" << (message.owner ? message.owner : "")
            << " | category=" << (message.category ? message.category : "")
            << " | severity=" << (message.severity ? message.severity : "")
            << "\n";
    }

    out << "\nSYSTEM_MESSAGE_TEXT preview:\n";
    for (const auto& message : messages) {
        out << "  " << (message.key ? message.key : "") << ":";
        bool any = false;
        for (const auto& text : texts) {
            if (text.id != message.id) {
                continue;
            }
            const std::string locale = text.locale ? text.locale : "";
            if (!normalized_filter.empty() && locale != normalized_filter) {
                continue;
            }
            out << (any ? ", " : " ") << locale;
            any = true;
        }
        if (!any) {
            out << " <no matching text rows>";
        }
        out << "\n";
    }

    out << "\n  boundary: report-only console report; no DBF, HELP DATA, CMDHELPCHK, source-mining, file, or catalog mutation.\n";
}

static void print_language_status(const std::string& current_locale) {
    auto& out = cli::OutputRouter::instance().out();

    out << "Message locale: " << current_locale << "\n"
        << "Supported message locales: en-US, es, fr, de, it\n"
        << "Usage: SET LANGUAGE [TO] <en-US|es|fr|de|it|DEFAULT>\n"
        << "       SET LOCALE   [TO] <en-US|es|fr|de|it|DEFAULT>\n"
        << "       SET LANGUAGE CHECK\n"
        << "       SET LOCALE CHECK\n"
        << "       SET LANGUAGE REPORT [locale]\n"
        << "       SET LOCALE REPORT [locale]\n";
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
    auto& out = cli::OutputRouter::instance().out();
    const auto status = dottalk::helpdata::active_message_catalog_status();

    out << "Message catalog provider status:\n";
    out << "  mode: " << message_catalog_mode_name(status.mode) << "\n";
    out << "  active catalog present: " << (status.active_catalog_present ? "yes" : "no") << "\n";
    out << "  active catalog loaded: " << (status.active_catalog_loaded ? "yes" : "no") << "\n";
    out << "  message count: " << status.message_count << "\n";
    out << "  text row count: " << status.text_row_count << "\n";
    out << "  active dbf dir: " << status.active_dbf_dir << "\n";
    out << "  active indexes dir: " << status.active_indexes_dir << "\n";
    out << "  active lmdb dir: " << status.active_lmdb_dir << "\n";
    out << "  detail: " << status.detail << "\n";
    out << "  boundary: read-only status/load; no DBF/CDX/LMDB mutation; no runtime writeback\n";
}
// MSG-022E END message catalog provider status helper

// MSG-022H BEGIN SET LANGUAGE active message emission helper
static void print_language_active_message_emission_check(const std::string& current_locale) {
    auto& out = cli::OutputRouter::instance().out();
    const auto status = dottalk::helpdata::active_message_catalog_status();
    const std::string text =
        dottalk::helpdata::format_message_catalog(current_locale, "HELP_HINT_COMMAND");

    out << "SET LANGUAGE active message emission:\n";
    out << "  current locale: " << current_locale << "\n";
    out << "  provider mode: " << message_catalog_mode_name(status.mode) << "\n";
    out << "  active catalog loaded: " << (status.active_catalog_loaded ? "yes" : "no") << "\n";
    out << "  symbol: HELP_HINT_COMMAND\n";
    out << "  fallback locale: en-US\n";
    out << "  text: " << (text.empty() ? "<missing>" : text) << "\n";
    out << "  boundary: read-only emission; no DBF/CDX/LMDB mutation; no runtime writeback\n";
}
// MSG-022H END SET LANGUAGE active message emission helper


// MSG-022G BEGIN SET LANGUAGE active catalog lookup helper
static std::string& message_catalog_current_locale() {
    static std::string locale = "en-US";
    return locale;
}

static void print_message_catalog_language_check() {
    auto& out = cli::OutputRouter::instance().out();
    const auto status = dottalk::helpdata::active_message_catalog_status();
    const std::string locale = message_catalog_current_locale();
    const std::string sample = dottalk::helpdata::format_message_catalog(locale, "MESSAGE_LOCALE_SET");

    out << "SET LANGUAGE active catalog check:\n";
    out << "  current language: " << locale << "\n";
    out << "  message catalog mode: " << message_catalog_mode_name(status.mode) << "\n";
    out << "  active catalog present: " << (status.active_catalog_present ? "yes" : "no") << "\n";
    out << "  active catalog loaded: " << (status.active_catalog_loaded ? "yes" : "no") << "\n";
    out << "  message count: " << status.message_count << "\n";
    out << "  text row count: " << status.text_row_count << "\n";
    out << "  lookup symbol: MESSAGE_LOCALE_SET\n";
    out << "  lookup locale: " << locale << "\n";
    out << "  lookup text: " << (sample.empty() ? "<empty>" : sample) << "\n";
    out << "  runtime active catalog lookup proof: "
        << ((status.active_catalog_loaded && !sample.empty()) ? "yes" : "no") << "\n";
    out << "  boundary: read-only lookup; no DBF/CDX/LMDB mutation; no runtime writeback\n";
}

static void handle_set_language_or_locale(std::istringstream& args, const std::string& command_name) {
    auto& out = cli::OutputRouter::instance().out();

    std::string tok;
    args >> tok;
    tok = up_copy(tok);

    if (tok.empty()) {
        out << command_name << ": " << message_catalog_current_locale() << "\n";
        return;
    }

    if (tok == "CHECK" || tok == "STATUS") {
        print_message_catalog_language_check();
        return;
    }

    std::string locale;
    if (tok == "TO") {
        args >> locale;
    } else {
        locale = tok;
    }

    if (locale.empty()) {
        out << "Usage: SET " << command_name << " <locale>|CHECK\n";
        return;
    }

    message_catalog_current_locale() = locale;
    out << command_name << ": " << message_catalog_current_locale() << "\n";
    print_message_catalog_language_check();
}
// MSG-022G END SET LANGUAGE active catalog lookup helper



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
    std::cout << msg22y_message_proof_mode_status(mode) << "\n";
    std::cout << msg22y_message_proof_boundary_note() << "\n";
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

    auto& out = cli::OutputRouter::instance().out();
    out << "Usage:\n";
    out << "  SET MESSAGE PROOF ON\n";
    out << "  SET MESSAGE PROOF OFF\n";
    out << "  SET MESSAGE PROOF CHECK\n";
}
// MSG-022O END routing proof mode helper


// MSG-022I-B BEGIN controlled message emit helper
static void print_message_emit_usage() {
    auto& out = cli::OutputRouter::instance().out();
    out << "Usage:\n";
    out << "  SET MESSAGE CATALOG CHECK\n";
    out << "  SET MESSAGE PROOF ON|OFF|CHECK\n";
    out << "  SET MESSAGE EMIT <symbol> [LOCALE <locale>] [ARG <name> <value>]\n";
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
    auto& out = cli::OutputRouter::instance().out();

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

    out << "SET MESSAGE EMIT:\n";
    out << "  current locale: " << locale << "\n";
    out << "  provider mode: " << message_catalog_mode_name(status.mode) << "\n";
    out << "  active catalog present: " << (status.active_catalog_present ? "yes" : "no") << "\n";
    out << "  active catalog loaded: " << (status.active_catalog_loaded ? "yes" : "no") << "\n";
    out << "  message count: " << status.message_count << "\n";
    out << "  text row count: " << status.text_row_count << "\n";
    out << "  symbol: " << symbol << "\n";
    out << "  locale: " << locale << "\n";
    out << "  placeholder arg supplied: "
        << (arg_name.empty() ? "<none>" : (arg_name + "=" + arg_value)) << "\n";
    out << "  placeholder substitution proof: " << (substituted ? "yes" : "no") << "\n";
    out << "  text: " << (text.empty() ? "<empty>" : text) << "\n";
    out << "  runtime controlled emission proof: "
        << ((status.active_catalog_loaded && !text.empty()) ? "yes" : "no") << "\n";
    out << "  boundary: explicit diagnostic emission; no DBF/CDX/LMDB mutation; no runtime writeback\n";
}
// MSG-022I-B END controlled message emit helper

static void print_set_usage() {
    auto& out = cli::OutputRouter::instance().out();

    out
        << "Usage:\n"
        << "  SET\n"
        << "  SET USAGE\n"
        << "  SET <option> [args]\n"
        << "Public options:\n"
        << "  SET TABLE BUFFER ON|OFF [ALL]\n"
        << "  SET CONSOLE ON|OFF\n"
        << "  SET PRINT ON|OFF\n"
        << "  SET PRINT TO <file>\n"
        << "  SET DEVICE TO SCREEN|FILE <path>|PRINTER [name]|NULL\n"
        << "  SET ALTERNATE ON|OFF\n"
        << "  SET ALTERNATE TO <file>\n"
        << "  SET TALK ON|OFF\n"
        << "  SET ECHO ON|OFF\n"
        << "  SET PAGING ON|OFF\n"
        << "  SET WRAP ON|OFF\n"
        << "  SET DELETED ON|OFF\n"
        << "  SET CASE ON|OFF\n"
        << "  SET NEAR ON|OFF\n"
        << "  SET EDITOR TO <value|DEFAULT|OFF>\n"
        << "  SET LANGUAGE [TO] <en-US|es|fr|de|it|DEFAULT>\n"
        << "  SET LOCALE [TO] <en-US|es|fr|de|it|DEFAULT>\n"
        << "  SET LANGUAGE CHECK\n"
        << "  SET LOCALE CHECK\n"
        << "  SET LANGUAGE REPORT [locale]\n"
        << "  SET LOCALE REPORT [locale]\n"
        << "  SET PATH <slot> <path>\n"
        << "  SET MESSAGE CATALOG CHECK\n"
        << "  SET MESSAGE EMIT <symbol> [LOCALE <locale>]\n"
        << "  SET LANGUAGE <locale>|CHECK\n"
        << "  SET LOCALE <locale>|CHECK\n"
        << "  SET UNIQUE FIELD <name> ON|OFF\n"
        << "  SET TIMER ON|OFF\n"
        << "  SET POLLING ON|OFF\n"
        << "  SET INDEX TO <file>\n"
        << "  SET ORDER TO <tag|0>\n";

#if DOTTALK_WITH_DEV
    out
        << "\n"
        << "Developer / transitional:\n"
        << "  SET FILTER TO <expr>\n"
        << "  SET RELATION <args...>\n"
        << "  SET RELATIONS <args...>\n"
        << "  SET CNX [TO] <container.cnx>\n"
        << "  SET CDX [TO] <container.cdx>\n"
        << "  SET LMDB <args...>\n";
#endif
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
                        out << "Message routing proof: active_dbf UNSUPPORTED_MESSAGE_LOCALE\n";
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
                route_out << "Message routing proof: active_dbf MESSAGE_LOCALE_SET\n";
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


    // MSG-022G BEGIN SET LANGUAGE active catalog lookup
    if (opt == "LANGUAGE" || opt == "LOCALE") {
        handle_set_language_or_locale(args, opt);
        return;
    }
    // MSG-022G END SET LANGUAGE active catalog lookup

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
                out << "Usage: SET TABLE BUFFER ON|OFF [ALL]\n";
                return;
            }

            std::string scope;
            args >> scope;
            const bool all = (up_copy(scope) == "ALL");

            auto* eng = shell_engine();
            if (!eng) {
                out << "TABLE BUFFER: engine not available.\n";
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
                out << "TABLE BUFFER: " << (on ? "ON" : "OFF")
                    << " for " << changed << " open area(s).\n";
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
                out << "TABLE BUFFER: cannot determine current area.\n";
                return;
            }

            dottalk::table::set_enabled(area0, on);

            out << "TABLE BUFFER: " << (on ? "ON" : "OFF")
                << " (area " << area0 << ")\n";
            return;
        }

        out << "Usage: SET TABLE BUFFER ON|OFF [ALL]\n";
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
            out << "Usage: SET CONSOLE ON|OFF\n";
            return;
        }

        if (on) {
            R.set_dest_console();
            R.console_note("PRN: CONSOLE");
        } else {
            R.console_note("PRN: NULL");
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
            out << "Usage: SET PRINT ON|OFF | SET PRINT TO <file>\n";
            return;
        }

        const std::string u = up_copy(tok);

        if (u == "TO") {
            std::string tail = ltrim_copy(rest(args));
            if (tail.empty()) {
                out << "Usage: SET PRINT TO <file>\n";
                return;
            }

            if (!R.set_dest_file(tail)) {
                out << "PRINT TO failed: " << tail << "\n";
                return;
            }

            R.console_note("PRN: FILE -> " + R.prn_file_path());
            return;
        }

        bool on = (R.dest() == cli::OutputDest::File);
        if (!parse_on_off(tok, on)) {
            out << "Usage: SET PRINT ON|OFF | SET PRINT TO <file>\n";
            return;
        }

        if (on) {
            if (!R.prn_file_path().empty()) {
                (void)R.set_dest_file(R.prn_file_path());
                R.console_note("PRN: FILE -> " + R.prn_file_path());
            } else {
                out << "SET PRINT ON requires a file. Use: SET PRINT TO <file>\n";
            }
        } else {
            R.console_note("PRN: NULL");
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
            out << "Usage: SET ALTERNATE ON|OFF | SET ALTERNATE TO <file>\n";
            return;
        }

        const std::string u = up_copy(tok);

        if (u == "TO") {
            std::string tail = ltrim_copy(rest(args));
            if (tail.empty()) {
                out << "Usage: SET ALTERNATE TO <file>\n";
                return;
            }

            if (!R.set_alternate_to(tail)) {
                out << "ALTERNATE TO failed: " << tail << "\n";
                return;
            }

            out << "ALTERNATE TO: " << R.alternate_to_path() << "\n";
            return;
        }

        bool on = R.alternate_on();
        if (!parse_on_off(tok, on)) {
            out << "Usage: SET ALTERNATE ON|OFF | SET ALTERNATE TO <file>\n";
            return;
        }

        R.set_alternate(on);
        out << "Alternate is " << (on ? "ON" : "OFF") << "\n";
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
            out << "Usage: SET TALK ON|OFF\n";
            return;
        }

        S.talk_on.store(on);
        out << "Talk is " << (on ? "ON" : "OFF") << "\n";
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
            out << "Usage: SET ECHO ON|OFF\n";
            return;
        }

        R.set_echo(on);
        out << "Echo is " << (on ? "ON" : "OFF") << "\n";
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
            out << "Usage: SET PAGING ON|OFF\n";
            return;
        }

        R.set_paging(on);
        out << "Paging is " << (on ? "ON" : "OFF") << "\n";
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
            out << "Usage: SET WRAP ON|OFF\n";
            return;
        }

        R.set_wrap(on);
        out << "Wrap is " << (on ? "ON" : "OFF") << "\n";
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
            out << "Usage: SET TIMER ON|OFF\n";
            return;
        }

        S.timer_on.store(on);
        out << "Timer is " << (on ? "ON" : "OFF") << "\n";
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
            out << "Usage: SET POLLING ON|OFF\n";
            return;
        }

        S.polling_on.store(on);
        out << "Polling is " << (on ? "ON" : "OFF") << "\n";
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
            out << "Usage: SET DELETED ON|OFF\n";
            return;
        }

        S.deleted_on.store(on);
        out << "Deleted visibility: " << (on ? "HIDE (ON)" : "SHOW (OFF)") << "\n";
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
            out << "Usage: SET EDITOR TO <value|DEFAULT|OFF>\n";
            return;
        }

        sub = up_copy(sub);
        if (sub != "TO") {
            out << "Usage: SET EDITOR TO <value|DEFAULT|OFF>\n";
            return;
        }

        std::string tail = ltrim_copy(rest(args));
        if (tail.empty()) {
            out << "Usage: SET EDITOR TO <value|DEFAULT|OFF>\n";
            return;
        }

        const std::string tail_up = up_copy(tail);

        if (tail_up == "OFF") {
            S.editor.mode = cli::EditorMode::Off;
            S.editor.command.clear();
            out << "EDITOR is OFF\n";
            return;
        }

        if (tail_up == "DEFAULT") {
            S.editor.mode = cli::EditorMode::Default;
            S.editor.command.clear();
            out << "EDITOR set to DEFAULT\n";
            return;
        }

        S.editor.mode = cli::EditorMode::Custom;
        S.editor.command = tail;

        out << "EDITOR set to: " << S.editor.command << "\n";
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
            out << "Usage: SET DEVICE TO SCREEN|FILE <path>|PRINTER [name]|NULL\n";
            return;
        }

        std::string mode;
        args >> mode;
        mode = up_copy(mode);

        if (mode == "SCREEN" || mode == "CONSOLE") {
            R.set_dest_console();
            R.console_note("PRN: CONSOLE");
            return;
        }

        if (mode == "NULL" || mode == "OFF") {
            R.console_note("PRN: NULL");
            R.set_dest_null();
            return;
        }

        if (mode == "FILE") {
            std::string path = ltrim_copy(rest(args));
            if (path.empty()) {
                out << "Usage: SET DEVICE TO FILE <path>\n";
                return;
            }
            if (!R.set_dest_file(path)) {
                out << "SET DEVICE TO FILE failed: " << path << "\n";
                return;
            }
            R.console_note("PRN: FILE -> " + R.prn_file_path());
            return;
        }

        if (mode == "PRINTER") {
            std::string printer_name = ltrim_copy(rest(args));
            if (!R.set_dest_printer(printer_name)) {
                out << "SET DEVICE TO PRINTER failed.\n";
                return;
            }
            if (R.prn_uses_default_printer()) {
                R.console_note("PRN: PRINTER -> (system default) [staged only]");
            } else {
                R.console_note("PRN: PRINTER -> " + R.prn_printer_name() + " [staged only]");
            }
            return;
        }

        out << "Usage: SET DEVICE TO SCREEN|FILE <path>|PRINTER [name]|NULL\n";
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

    // ─────────────────────────────────────────────────────────────
    // SET CNX
    // ─────────────────────────────────────────────────────────────
    if (opt == "CNX") {
        std::istringstream r(rest(args));
        cmd_SETCNX(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET CDX
    // ─────────────────────────────────────────────────────────────
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