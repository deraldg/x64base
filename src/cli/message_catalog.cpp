#include "message_catalog.hpp"

#include "cli/settings.hpp"
#include "help/helpdata_messages.hpp"

#include <set>
#include <string>
#include <vector>

namespace dottalk::msg {

namespace {

struct CodeTextDef {
    Code        code;
    const char* locale;
    const char* text;
};

const std::vector<CodeTextDef>& all_code_texts()
{
    static const std::vector<CodeTextDef> texts = {
        { Code::UnknownCommand,               "en-US", "Unknown command" },
        { Code::MissingArgument,              "en-US", "Missing required argument" },
        { Code::InvalidSyntax,                "en-US", "Invalid command syntax" },
        { Code::NotFound,                     "en-US", "Not found" },
        { Code::IndexNotSet,                  "en-US", "No active index" },
        { Code::InternalError,                "en-US", "Internal error" },
        { Code::ExpectedPositiveRecordNumber, "en-US", "expected a positive record number" },
        { Code::AreaQualifierNotSupportedYet, "en-US", "'IN <alias>' not supported yet (SELECT the area, then GO ...)" },
        { Code::UnrecognizedCommandForm,      "en-US", "unrecognized form" },

        { Code::UnknownCommand,               "it", "Comando sconosciuto" },
        { Code::MissingArgument,              "it", "Argomento obbligatorio mancante" },
        { Code::InvalidSyntax,                "it", "Sintassi del comando non valida" },
        { Code::NotFound,                     "it", "Non trovato" },
        { Code::IndexNotSet,                  "it", "Nessun indice attivo" },
        { Code::InternalError,                "it", "Errore interno" },
        { Code::ExpectedPositiveRecordNumber, "it", "era previsto un numero di record positivo" },
        { Code::AreaQualifierNotSupportedYet, "it", "'IN <alias>' non e' ancora supportato (usare SELECT per scegliere l'area, poi GO ...)" },
        { Code::UnrecognizedCommandForm,      "it", "forma non riconosciuta" },

        { Code::UnknownCommand,               "es", "Comando desconocido" },
        { Code::MissingArgument,              "es", "Falta un argumento requerido" },
        { Code::InvalidSyntax,                "es", "Sintaxis de comando no valida" },
        { Code::NotFound,                     "es", "No encontrado" },
        { Code::IndexNotSet,                  "es", "No hay indice activo" },
        { Code::InternalError,                "es", "Error interno" },
        { Code::ExpectedPositiveRecordNumber, "es", "se esperaba un numero de registro positivo" },
        { Code::AreaQualifierNotSupportedYet, "es", "'IN <alias>' todavia no esta admitido (use SELECT para elegir el area, luego GO ...)" },
        { Code::UnrecognizedCommandForm,      "es", "forma no reconocida" },

        { Code::UnknownCommand,               "fr", "Commande inconnue" },
        { Code::MissingArgument,              "fr", "Argument requis manquant" },
        { Code::InvalidSyntax,                "fr", "Syntaxe de commande non valide" },
        { Code::NotFound,                     "fr", "Introuvable" },
        { Code::IndexNotSet,                  "fr", "Aucun index actif" },
        { Code::InternalError,                "fr", "Erreur interne" },
        { Code::ExpectedPositiveRecordNumber, "fr", "un numero d'enregistrement positif etait attendu" },
        { Code::AreaQualifierNotSupportedYet, "fr", "'IN <alias>' n'est pas encore pris en charge (utilisez SELECT pour choisir la zone, puis GO ...)" },
        { Code::UnrecognizedCommandForm,      "fr", "forme non reconnue" },

        { Code::UnknownCommand,               "de", "Unbekannter Befehl" },
        { Code::MissingArgument,              "de", "Erforderliches Argument fehlt" },
        { Code::InvalidSyntax,                "de", "Ungueltige Befehlssyntax" },
        { Code::NotFound,                     "de", "Nicht gefunden" },
        { Code::IndexNotSet,                  "de", "Kein aktiver Index" },
        { Code::InternalError,                "de", "Interner Fehler" },
        { Code::ExpectedPositiveRecordNumber, "de", "eine positive Datensatznummer wurde erwartet" },
        { Code::AreaQualifierNotSupportedYet, "de", "'IN <alias>' wird noch nicht unterstuetzt (waehlen Sie den Bereich mit SELECT aus, dann GO ...)" },
        { Code::UnrecognizedCommandForm,      "de", "nicht erkannte Form" }
    };
    return texts;
}

} // anonymous namespace

std::string normalize_locale(const std::string& locale)
{
    return dottalk::helpdata::normalize_locale(locale);
}

std::vector<std::string> available_locales()
{
    std::set<std::string> locales;
    for (const auto& text : all_code_texts()) {
        if (text.locale && *text.locale) {
            locales.insert(text.locale);
        }
    }
    for (const auto& locale : dottalk::helpdata::available_locales()) {
        locales.insert(locale);
    }
    return std::vector<std::string>(locales.begin(), locales.end());
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

std::string text(Code code)
{
    return text(code, cli::Settings::instance().message_locale);
}

std::string text(Code code, const std::string& locale)
{
    for (const auto& candidate : dottalk::helpdata::locale_fallback_chain(locale)) {
        for (const auto& item : all_code_texts()) {
            if (item.code == code && candidate == item.locale) {
                return item.text;
            }
        }
    }

    return "Unknown message";
}

} // namespace dottalk::msg
