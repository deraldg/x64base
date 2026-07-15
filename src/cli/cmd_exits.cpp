// @dottalk.usage v1
// owner: DOT|EXITS
// command: EXITS
// category: extension-control
// status: document-control-readonly
// noargs: list-summary
// effect: report
// mutates: none
// usage-access: EXITS USAGE; EXITS HELP; EXITS ?
// summary:
//   Inspect and validate the reviewed DotTalk++ extension-exit manifest.
//
// usage:
//   EXITS
//   EXITS USAGE
//   EXITS LIST
//   EXITS SHOW <id>
//   EXITS VALIDATE
//   EXITS WHERE
//
// examples:
//   EXITS LIST
//   EXITS SHOW Z_AUDIT_COMMAND
//   EXITS VALIDATE
//   EXITS WHERE
//
// notes:
//   This phase is read-only document control.
//   EXITS does not load DLLs, execute processes, enable exits, or disable exits.
//   Non-C++ extension artifacts are manifest-controlled and not source-mined in v1.
//
// risk:
//   mutates_table_data: no
//   mutates_manifest: no
//   executes_external_process: no
//

#include <iostream>
#include <sstream>
#include <string>

#include "extension_manifest.hpp"
#include "textio.hpp"
#include "xbase.hpp"

namespace {

static std::string upper(std::string value)
{
    return textio::up(textio::trim(std::move(value)));
}

static void print_usage()
{
    std::cout
        << "Usage:\n"
        << "  EXITS\n"
        << "  EXITS USAGE\n"
        << "  EXITS LIST\n"
        << "  EXITS SHOW <id>\n"
        << "  EXITS VALIDATE\n"
        << "  EXITS WHERE\n"
        << "Notes:\n"
        << "  - Read-only document-control surface.\n"
        << "  - No extension code is executed by this command.\n";
}

static void print_diagnostics(const dottalk::extensions::Manifest& manifest)
{
    for (const auto& diag : manifest.diagnostics) {
        std::cout << "  [" << dottalk::extensions::to_string(diag.severity)
                  << "] " << diag.message << "\n";
    }
}

static void print_entry(const dottalk::extensions::ManifestEntry& entry)
{
    std::cout
        << entry.id
        << "  point=" << entry.point
        << "  kind=" << entry.kind
        << "  state=" << (entry.state.empty() ? "(none)" : entry.state)
        << "  enabled=" << (entry.enabled ? "true" : "false")
        << "\n";
}

static void print_entry_detail(const dottalk::extensions::ManifestEntry& entry)
{
    std::cout
        << "id              : " << entry.id << "\n"
        << "point           : " << entry.point << "\n"
        << "kind            : " << entry.kind << "\n"
        << "language        : " << (entry.language.empty() ? "(none)" : entry.language) << "\n"
        << "entry           : " << entry.entry << "\n"
        << "enabled         : " << (entry.enabled ? "true" : "false") << "\n"
        << "timeout_ms      : " << (entry.timeout_ms ? std::to_string(*entry.timeout_ms) : "(none)") << "\n"
        << "owner           : " << (entry.owner.empty() ? "(none)" : entry.owner) << "\n"
        << "state           : " << (entry.state.empty() ? "(none)" : entry.state) << "\n"
        << "usage_contract  : " << (entry.usage_contract.empty() ? "(none)" : entry.usage_contract) << "\n"
        << "evidence        : " << (entry.evidence.empty() ? "(none)" : entry.evidence) << "\n";
}

} // namespace

void cmd_EXITS(xbase::DbArea&, std::istringstream& in)
{
    std::string sub;
    in >> sub;
    const std::string mode = upper(sub.empty() ? "LIST" : sub);

    if (mode == "USAGE" || mode == "HELP" || mode == "?") {
        print_usage();
        return;
    }

    const auto manifest_path = dottalk::extensions::default_manifest_path();

    if (mode == "WHERE") {
        std::cout << "Exit manifest: " << manifest_path.string() << "\n";
        std::cout << "Exit root    : " << dottalk::extensions::default_exit_root().string() << "\n";
        return;
    }

    auto manifest = dottalk::extensions::load_manifest(manifest_path);

    if (mode == "VALIDATE") {
        std::cout << "EXITS VALIDATE\n";
        std::cout << "manifest: " << manifest_path.string() << "\n";
        std::cout << "entries : " << manifest.entries.size() << "\n";
        std::cout << "errors  : " << manifest.error_count() << "\n";
        std::cout << "warnings: " << manifest.warning_count() << "\n";
        print_diagnostics(manifest);
        return;
    }

    if (mode == "SHOW") {
        std::string id;
        in >> id;
        if (id.empty()) {
            std::cout << "EXITS SHOW requires an id.\n";
            return;
        }
        const auto* entry = dottalk::extensions::find_entry(manifest, id);
        if (!entry) {
            std::cout << "No exit entry found for: " << id << "\n";
            print_diagnostics(manifest);
            return;
        }
        print_entry_detail(*entry);
        return;
    }

    if (mode != "LIST") {
        std::cout << "Unknown EXITS subcommand: " << sub << "\n";
        print_usage();
        return;
    }

    std::cout << "EXITS\n";
    std::cout << "manifest: " << manifest_path.string() << "\n";
    std::cout << "entries : " << manifest.entries.size() << "\n";
    for (const auto& entry : manifest.entries) {
        print_entry(entry);
    }
    print_diagnostics(manifest);
}
