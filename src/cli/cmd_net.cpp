// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: DOT|NET
// project: project.x64base.runtime
// lane: AIF-053
// owner: member.derald
// status: supported

// @dottalk.usage v1
// owner: DOT|NET
// command: NET
// category: diagnostics
// status: supported
// noargs: usage
// effect: mixed
// mutates: host-network-policy
// usage-access: NET USAGE
// summary:
//   NET EGRESS (M2): read and toggle the WSL/AFB egress isolation as a permissioned,
//   audited capability. OPEN/CLOSE require RBAC permission host.network.egress (Critical,
//   requires_approval) AND DOTTALK_ALLOW_HOST_COMMANDS. Owner (role.maintainer) is exempt;
//   AI members are denied. Windows/mirrored-mode only.
//
// usage:
//   NET USAGE
//   NET EGRESS STATUS                      report Hyper-V DefaultOutboundAction (read-only)
//   NET EGRESS OPEN  [MINUTES <n>] [reason] allow outbound (host.network.egress)  -- UAC prompt
//   NET EGRESS CLOSE                        block outbound (host.network.egress)  -- UAC prompt
//
// examples:
//   NET EGRESS STATUS
//   NET EGRESS OPEN MINUTES 10 pull qwen2.5-coder
//   NET EGRESS CLOSE
//
// notes:
//   The block is a Hyper-V firewall per-VM DefaultOutboundAction on the WSL VM id; loopback
//   stays allowed so local Ollama is unaffected. This is "verified revocable egress isolation,"
//   NOT an air-gap. OPEN/CLOSE shell an ELEVATED PowerShell (Start-Process -Verb RunAs) => a
//   UAC prompt, unless the engine already runs elevated. MINUTES is recorded in the audit
//   transcript; scheduled auto-close is a documented follow-up (schtasks), not run inline.
//   Every OPEN/CLOSE writes an audit transcript under data/metadata/bbs/egress_audit/.
//
// risk:
//   mutates_table_data: no
//   mutates_host_network_policy: OPEN, CLOSE
//   requires_elevation: OPEN, CLOSE (UAC)
//
// related:
//   USER
//   BBS
//
// @dottalk.end

#include "identity/identity_admin.hpp"        // agent_permitted, acting_member_key
#include "cli/external_process_policy.hpp"    // cli::security::authorize_external_process
#include "cli/command_output.hpp"             // cli::cmdout::print_line / print_info
#include "common/path_state.hpp"              // dottalk::paths::get_slot
#include "selfdoc/event_record.hpp"           // M5: runtime->doc intake
#include "xbase.hpp"                           // xbase::DbArea (command signature)

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

namespace fs = std::filesystem;

namespace {

using cli::cmdout::print_line;
using cli::cmdout::print_info;

// WSL's well-known Hyper-V VM id (same id AFB tooling uses).
constexpr const char* kVmId = "{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}";
constexpr const char* kPerm = "host.network.egress";

std::string upcase(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}
std::string trim(const std::string& s) {
    std::size_t b = 0, e = s.size();
    while (b < e && std::isspace(static_cast<unsigned char>(s[b]))) ++b;
    while (e > b && std::isspace(static_cast<unsigned char>(s[e-1]))) --e;
    return s.substr(b, e - b);
}

void net_usage() {
    print_line("NET USAGE");
    print_line("  NET EGRESS STATUS");
    print_line("  NET EGRESS OPEN  [MINUTES <n>] [reason]");
    print_line("  NET EGRESS CLOSE");
}

// Append an audit transcript row for an OPEN/CLOSE (best-effort; M5 wires proofs.yaml/ai_runs).
void write_audit(const std::string& action, const std::string& reason, int minutes, const std::string& result) {
    try {
        const fs::path dir = dottalk::paths::get_slot(dottalk::paths::Slot::DATA) / "metadata" / "bbs" / "egress_audit";
        std::error_code ec; fs::create_directories(dir, ec);
        const std::time_t t = std::time(nullptr);
        char ts[32]; std::strftime(ts, sizeof ts, "%Y%m%d_%H%M%S", std::localtime(&t));
        std::ofstream out((dir / (std::string("egress_") + ts + ".txt")).string(), std::ios::app);
        out << "action="  << action
            << " actor="  << dottalk::identity::acting_member_key()
            << " minutes=" << minutes
            << " result=" << result
            << " reason=\"" << reason << "\""
            << " at="     << ts << "\n";
    } catch (...) { /* audit is best-effort; never abort the command on a log failure */ }
}

// Build + run the platform command. Returns std::system rc (or -1 if unsupported/blocked path).
int run_egress(bool allow) {
#ifdef _WIN32
    const std::string act = allow ? "Allow" : "Block";
    // Elevated: outer powershell spawns an elevated one (UAC) that sets the Hyper-V default action.
    // Doubled '' inside the single-quoted arg yields a literal ' around the {GUID}.
    const std::string inner = std::string("Set-NetFirewallHyperVVMSetting -Name ''") + kVmId +
                              "'' -DefaultOutboundAction " + act;
    const std::string cmd = std::string(
        "powershell -NoProfile -Command \"Start-Process powershell -Verb RunAs -Wait "
        "-ArgumentList '-NoProfile','-Command','") + inner + "'\"";
    return std::system(cmd.c_str());
#else
    (void)allow;
    print_info("NET EGRESS", "unsupported on this platform (Windows + WSL mirrored mode only)");
    return -1;
#endif
}

void do_status() {
#ifdef _WIN32
    const std::string cmd = std::string(
        "powershell -NoProfile -Command \"(Get-NetFirewallHyperVVMSetting -Name '") + kVmId +
        "').DefaultOutboundAction\"";
    print_line("NET EGRESS STATUS (Hyper-V DefaultOutboundAction):");
    std::system(cmd.c_str());   // prints Allow/Block to the console
#else
    print_info("NET EGRESS", "unsupported on this platform (Windows + WSL mirrored mode only)");
#endif
}

void do_toggle(bool allow, std::istringstream& iss) {
    // 1) RBAC: owner exempt; ai_partner denied; host.* also folds in DOTTALK_ALLOW_HOST_COMMANDS.
    const dottalk::identity::Decision d = dottalk::identity::agent_permitted(kPerm);
    if (!d.allowed()) {
        print_info("NET EGRESS", "refused for " + dottalk::identity::acting_member_key() + " -- " + d.reason);
        return;
    }
    // 2) Host + network policy gate (env: DOTTALK_ALLOW_HOST_COMMANDS / DOTTALK_ALLOW_NETWORK).
    if (!cli::security::authorize_external_process("NET EGRESS", true)) return;

    // 3) Optional MINUTES + free-text reason (OPEN only).
    int minutes = 0;
    std::string reason;
    if (allow) {
        std::string tok;
        if (iss >> tok) {
            if (upcase(tok) == "MINUTES") { iss >> minutes; std::string rest; std::getline(iss, rest); reason = trim(rest); }
            else { std::string rest; std::getline(iss, rest); reason = trim(tok + rest); }
        }
    }

    const int rc = run_egress(allow);
    const std::string action = allow ? "OPEN" : "CLOSE";
    const std::string result = (rc == 0) ? "ok" : ("rc=" + std::to_string(rc));
    write_audit(action, reason, minutes, result);
    dottalk::selfdoc::record_event("runtime", "net_egress",
        dottalk::identity::acting_member_key(), action + " egress",
        { "result=" + result, "minutes=" + std::to_string(minutes), "reason=" + reason });

    if (rc == 0) {
        print_info("NET EGRESS", action + std::string(" applied (DefaultOutboundAction ") + (allow ? "Allow)" : "Block)"));
        if (allow && minutes > 0)
            print_info("NET EGRESS", "window recorded for " + std::to_string(minutes) +
                       " min -- run NET EGRESS CLOSE when done (scheduled auto-close is a follow-up).");
    } else if (rc != -1) {
        print_info("NET EGRESS", action + " failed (rc=" + std::to_string(rc) + "); needs elevation? check the UAC prompt.");
    }
}

} // namespace

// Registered in shell_commands.cpp:  registry().add("NET", ...cmd_NET...);
// Forward declaration in shell_commands.hpp:  void cmd_NET(DbArea&, std::istringstream&);
void cmd_NET(xbase::DbArea&, std::istringstream& iss) {
    std::string sub;
    if (!(iss >> sub)) { net_usage(); return; }
    const std::string u = upcase(sub);
    if (u == "USAGE" || u == "HELP" || u == "?") { net_usage(); return; }
    if (u == "EGRESS") {
        std::string op; iss >> op; const std::string o = upcase(op);
        if (o == "STATUS") { do_status(); return; }
        if (o == "OPEN")   { do_toggle(true,  iss); return; }
        if (o == "CLOSE")  { do_toggle(false, iss); return; }
        net_usage(); return;
    }
    net_usage();
}
