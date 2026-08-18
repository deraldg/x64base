// @dottalk.file v1
// subsystem: cli
// layer: command
// owns:
// project: project.x64base.runtime
// lane:
// owner: member.derald
// status: review-needed

// src/cli/cmd_smtp.cpp
// SMTP command -- a thin wrapper over tools/notify/smtp_probe.py.
//
// This command does NOT speak SMTP. It stages the body to a temp file and
// invokes the Python probe, exactly as cmd_sftp.cpp stages a batch file and
// invokes the system sftp client. Implementing the protocol here would mean new
// protocol code, a TLS dependency, and a second credential path competing with
// a working one.
//
// CREDENTIALS ARE NEVER SEEN BY THIS COMMAND. SMTP_USER / SMTP_PASS reach the
// probe through the environment, set by a platform wrapper (DPAPI clixml on
// Windows, a chmod-600 env file on POSIX). Nothing here reads, stores, prompts
// for, or logs them.
//
// SCRIPT LOCATION: the TOOLS path slot, <root>/tools, with DOTTALK_SMTP_PROBE
// as an explicit override.
//
// TOOLS is root-relative rather than data-relative on purpose. SCRIPTS (under
// data) holds scripts a USER runs; TOOLS holds helpers the RUNTIME invokes. A
// command that shells out to a helper is broken the moment the helper is not
// beside the product, so the helper has to ship with the product rather than
// live in the development tree.
//
// CONSEQUENCE, and it is a real one: smtp_probe.py currently sits at the
// REPOSITORY tools directory, which is a different tree from <root>/tools. For
// a deployed dottalkpp to send mail the probe must be under the product's TOOLS
// slot. Until it is moved or staged there, set DOTTALK_SMTP_PROBE.
//
// STATUS: NOT COMPILED. Written against the cmd_sftp.cpp pattern in a sandbox
// with no toolchain. First build is the first test.

// @dottalk.usage v1
// owner: DOT|SMTP
// command: SMTP
// category: network
// status: review-needed
// noargs: usage
// effect: network
// mutates: nothing-local
// usage-access: SMTP USAGE
// summary:
//   Send mail through the tools/notify/smtp_probe.py helper, or probe the
//   configured server without sending.
//
// usage:
//   SMTP USAGE
//   SMTP STATUS
//   SMTP PROBE
//   SMTP SEND FROM <body-file> [TO <address>] SUBJECT <text to end of line>
//
// examples:
//   SMTP STATUS
//   SMTP PROBE
//   SMTP SEND FROM report.txt SUBJECT Nightly regression summary
//   SMTP SEND FROM report.txt TO ops@example.com SUBJECT Nightly summary
//
// notes:
//   SMTP with no arguments shows usage.
//   Keywords come first and SUBJECT is last, reading to end of line, so a
//   subject containing spaces needs no quoting and cannot be confused with a
//   keyword.
//   TO defaults to SMTP_USER, matching the probe's own default.
//   STATUS reports host, port and user, and NEVER the password.
//   Credentials come from the environment; this command cannot read them.
//   Set DOTTALK_ALLOW_HOST_COMMANDS=1 and DOTTALK_ALLOW_NETWORK=1 to enable.
//   Requires identity permission host.shell, as SFTP does.
//   --debug is deliberately not exposed: the probe's debug mode prints the
//   base64 AUTH exchange, and a CLI that can be scripted into a log file must
//   not offer that as a flag.
//
// risk:
//   network_access: PROBE SEND
//   launches_external_process: python + tools/notify/smtp_probe.py
//   sends_outbound_mail: SEND
//   reads_local_filesystem: SEND reads the body file
//   writes_local_filesystem: SEND stages a temp copy of the body
//   mutates_table_data: no
//   stores_credentials: no
//
// related:
//   SFTP
//   NET
//   PSHELL
//

#include <cctype>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "cli/external_process_policy.hpp"
#include "common/path_state.hpp"
#include "identity/identity_admin.hpp"

namespace fs = std::filesystem;

using xbase::DbArea;

namespace {

std::string uppercase_copy(std::string s)
{
    for (char& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

// Same blacklist as cmd_sftp.cpp, plus '%'. On Windows std::system() goes
// through cmd.exe, which expands %NAME% INSIDE double quotes -- so a subject
// containing %PATH% would leak the path into an outbound mail. SFTP never hit
// this because its arguments are temp paths and user@host targets; a mail
// subject is free text typed by a person.
bool contains_forbidden_chars(const std::string& s)
{
    for (char c : s) {
        switch (c) {
        case '"':
        case '%':
        case '\r':
        case '\n':
            return true;
        default:
            break;
        }
    }
    return false;
}

// Recipients get an ALLOW-list rather than the blacklist above. An address has
// a narrow legal shape, so permitting only what is legal is strictly stronger
// than forbidding what is known to be dangerous -- and the failure mode of a
// wrong recipient is mail delivered to a stranger.
bool valid_recipient(const std::string& s)
{
    if (s.empty() || s.size() > 320) return false;

    std::size_t at_count = 0;
    for (char c : s) {
        const unsigned char u = static_cast<unsigned char>(c);
        if (std::isalnum(u)) continue;
        switch (c) {
        case '@': ++at_count; continue;
        case '.': case '_': case '-': case '+': case ',': continue;
        default:  return false;
        }
    }

    // At least one address, and a comma list needs one '@' per entry. Counting
    // is enough here: the probe and the server both parse properly, and this
    // gate exists to keep shell metacharacters out, not to validate RFC 5322.
    return at_count >= 1;
}

std::string quote_for_shell(const std::string& s)
{
#ifdef _WIN32
    return "\"" + s + "\"";
#else
    std::string out = "'";
    for (char c : s) {
        if (c == '\'') {
            out += "'\\''";
        } else {
            out += c;
        }
    }
    out += "'";
    return out;
#endif
}

fs::path make_temp_body_path()
{
    std::error_code ec;
    fs::path dir = fs::temp_directory_path(ec);
    if (ec) dir = fs::current_path();

    static unsigned counter = 0;
    const std::string name =
        "dottalk_smtp_body_" + std::to_string(++counter) + ".txt";
    return dir / name;
}

// Resolve the probe script. Order is deliberate: an explicit setting always
// wins, and the fallback is a convenience for the development tree only.
bool resolve_probe_script(fs::path& out, std::string& err)
{
    if (const char* env = std::getenv("DOTTALK_SMTP_PROBE")) {
        if (env[0] != '\0') {
            fs::path p(env);
            std::error_code ec;
            if (!fs::exists(p, ec)) {
                err = "DOTTALK_SMTP_PROBE is set but does not exist: " + p.string();
                return false;
            }
            out = p;
            return true;
        }
    }

    // The supported location: the TOOLS slot. No cwd arithmetic, no assumption
    // about where the binary was launched from. get_slot can throw, and every
    // other CLI consumer guards it, so this does too.
    fs::path slotted;
    try {
        slotted = dottalk::paths::get_slot(dottalk::paths::Slot::TOOLS)
                  / "notify" / "smtp_probe.py";
    } catch (...) {
        err = "TOOLS path slot is not available. "
              "Set DOTTALK_SMTP_PROBE to the full path of smtp_probe.py.";
        return false;
    }

    std::error_code ec;
    if (fs::exists(slotted, ec)) {
        out = slotted;
        return true;
    }

    err = "smtp_probe.py not found at " + slotted.string() +
          ". Put it under the TOOLS slot, or set DOTTALK_SMTP_PROBE to its full path.";
    return false;
}

std::string python_exe()
{
    if (const char* env = std::getenv("DOTTALK_SMTP_PYTHON")) {
        if (env[0] != '\0') return std::string(env);
    }
    return "python";
}

void smtp_usage()
{
    std::cout
        << "Usage:\n"
        << "  SMTP USAGE\n"
        << "  SMTP STATUS\n"
        << "  SMTP PROBE\n"
        << "  SMTP SEND FROM <body-file> [TO <address>] SUBJECT <text>\n"
        << "\n"
        << "Examples:\n"
        << "  SMTP STATUS\n"
        << "  SMTP PROBE\n"
        << "  SMTP SEND FROM report.txt SUBJECT Nightly regression summary\n"
        << "  SMTP SEND FROM report.txt TO ops@example.com SUBJECT Nightly summary\n"
        << "\n"
        << "Notes:\n"
        << "  Credentials come from SMTP_USER / SMTP_PASS in the environment.\n"
        << "  This command never reads, stores or prints the password.\n"
        << "  SUBJECT reads to end of line and needs no quoting.\n"
        << "  TO defaults to SMTP_USER.\n"
        << "  Set DOTTALK_SMTP_PROBE to the full path of smtp_probe.py.\n"
        << "  Set DOTTALK_ALLOW_HOST_COMMANDS=1 and DOTTALK_ALLOW_NETWORK=1.\n";
}

std::string env_or(const char* name, const char* fallback)
{
    const char* v = std::getenv(name);
    return (v && v[0] != '\0') ? std::string(v) : std::string(fallback);
}

void smtp_status()
{
    const std::string user = env_or("SMTP_USER", "");
    const std::string host = env_or("SMTP_HOST", "smtp.gmail.com");
    const std::string port = env_or("SMTP_PORT", "587");
    const bool has_pass = !env_or("SMTP_PASS", "").empty();

    std::cout << "SMTP configuration:\n"
              << "  user     : " << (user.empty() ? "(SMTP_USER not set)" : user) << "\n"
              << "  server   : " << host << ":" << port << " (STARTTLS)\n"
              // Presence only. The value is never printed, and its length is not
              // reported either: length is a real hint about a secret.
              << "  password : " << (has_pass ? "set" : "NOT SET") << "\n";

    fs::path script;
    std::string err;
    if (resolve_probe_script(script, err)) {
        std::cout << "  probe    : " << script.string() << "\n";
    } else {
        std::cout << "  probe    : " << err << "\n";
    }
}

// Build and run the probe. `bodyPath` empty means no stdin redirect (PROBE).
int run_probe(const std::vector<std::string>& args,
              const fs::path& bodyPath,
              std::string& err)
{
    fs::path script;
    if (!resolve_probe_script(script, err)) {
        return -1;
    }

    std::string command = quote_for_shell(python_exe());
    command += " " + quote_for_shell(script.string());
    for (const std::string& a : args) {
        command += " " + quote_for_shell(a);
    }
    if (!bodyPath.empty()) {
        command += " < " + quote_for_shell(bodyPath.string());
    }

    return std::system(command.c_str());
}

// Map the probe's exit codes back to the operator. The probe already
// distinguishes an authentication failure from every other failure; collapsing
// both into "SMTP failed" would discard a diagnosis it had already made.
void report_exit(int rc)
{
    switch (rc) {
    case 0:  std::cout << "SMTP: OK\n"; break;
    case 2:  std::cout << "SMTP: credentials not set (SMTP_USER / SMTP_PASS)\n"; break;
    case 3:  std::cout << "SMTP: AUTHENTICATION FAILED -- the server rejected the login\n"; break;
    case 4:  std::cout << "SMTP: failed -- see the message above\n"; break;
    default: std::cout << "SMTP: probe exited " << rc << "\n"; break;
    }
}

void cmd_smtp_probe()
{
    std::string err;
    const int rc = run_probe({"--probe"}, fs::path(), err);
    if (rc < 0) {
        std::cout << "SMTP: " << err << "\n";
        return;
    }
    report_exit(rc);
}

void cmd_smtp_send(std::istringstream& S)
{
    std::string bodyFile;
    std::string to;
    std::string subject;

    // Keyword-led parse. SUBJECT is last and reads to end of line, so a subject
    // containing spaces needs no quoting and can never be mistaken for a
    // keyword. Anything after SUBJECT belongs to the subject.
    std::string tok;
    while (S >> tok) {
        const std::string key = uppercase_copy(tok);

        if (key == "FROM") {
            if (!(S >> bodyFile)) {
                std::cout << "SMTP: FROM expects a file path\n";
                return;
            }
            continue;
        }
        if (key == "TO") {
            if (!(S >> to)) {
                std::cout << "SMTP: TO expects an address\n";
                return;
            }
            continue;
        }
        if (key == "SUBJECT") {
            std::getline(S, subject);
            // Trim one leading space left by the stream.
            if (!subject.empty() && subject.front() == ' ') subject.erase(0, 1);
            break;
        }

        std::cout << "SMTP: unexpected token '" << tok << "'\n";
        smtp_usage();
        return;
    }

    if (bodyFile.empty()) {
        std::cout << "SMTP: SEND requires FROM <body-file>\n";
        return;
    }
    if (subject.empty()) {
        std::cout << "SMTP: SEND requires SUBJECT <text>\n";
        return;
    }
    if (contains_forbidden_chars(subject)) {
        std::cout << "SMTP: subject contains an unsupported character "
                     "(double quote, percent, or newline)\n";
        return;
    }
    if (!to.empty() && !valid_recipient(to)) {
        std::cout << "SMTP: recipient is not a plausible address: " << to << "\n";
        return;
    }

    std::error_code ec;
    if (!fs::exists(bodyFile, ec)) {
        std::cout << "SMTP: body file not found: " << bodyFile << "\n";
        return;
    }

    // Stage a copy rather than redirecting the original. The probe reads stdin
    // to EOF, and staging keeps a caller from discovering that SMTP holds a
    // read handle on a file they are still writing.
    const fs::path staged = make_temp_body_path();
    {
        std::ifstream in(bodyFile, std::ios::binary);
        if (!in) {
            std::cout << "SMTP: cannot read body file: " << bodyFile << "\n";
            return;
        }
        std::ofstream out(staged, std::ios::binary | std::ios::trunc);
        if (!out) {
            std::cout << "SMTP: cannot stage body in the temp directory\n";
            return;
        }
        out << in.rdbuf();
    }

    std::vector<std::string> args{"--send", subject};
    if (!to.empty()) {
        args.push_back("--to");
        args.push_back(to);
    }

    std::string err;
    const int rc = run_probe(args, staged, err);

    fs::remove(staged, ec);

    if (rc < 0) {
        std::cout << "SMTP: " << err << "\n";
        return;
    }
    report_exit(rc);
}

} // namespace

void cmd_SMTP(DbArea&, std::istringstream& S)
{
    std::string sub;

    if (!(S >> sub)) {
        smtp_usage();
        return;
    }

    sub = uppercase_copy(sub);

    if (sub == "USAGE" || sub == "HELP" || sub == "?") {
        smtp_usage();
        return;
    }

    // STATUS is read-only and reports no secret, so it sits BEFORE the gates:
    // "is mail configured" must be answerable without permission to send any.
    if (sub == "STATUS") {
        smtp_status();
        return;
    }

    // Identity enforcement, mirroring cmd_sftp.cpp: SMTP launches a process and
    // reaches a remote host, so the acting member must hold host.shell. A
    // separate mail permission was considered and rejected -- anyone with
    // host.shell can already run the probe script through the shell escape, so
    // a distinct capability would be the appearance of control rather than
    // control. See SMTP_COMMAND_PROPOSAL_V1.md.
    {
        const dottalk::identity::Decision d = dottalk::identity::agent_permitted("host.shell");
        if (!d.allowed()) {
            std::cout << "SMTP: refused for " << dottalk::identity::acting_member_key()
                      << " -- " << d.reason << "\n";
            return;
        }
    }

    if (!cli::security::authorize_external_process("SMTP", true)) {
        return;
    }

    if (sub == "PROBE") {
        cmd_smtp_probe();
        return;
    }

    if (sub == "SEND") {
        cmd_smtp_send(S);
        return;
    }

    smtp_usage();
}
