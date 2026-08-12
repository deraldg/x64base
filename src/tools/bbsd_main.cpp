// @dottalk.file v1
// subsystem: tools
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: AIF-054
// owner: member.derald
// status: supported

// bbsd_main.cpp -- standalone DotTalk++ BBS agent-server daemon (M6).
//
// Runs dottalk::bbs::serve() as a long-lived process, independent of the interactive CLI, so the
// server can be left up for stretches without tying up a dottalkpp shell. It shares the SAME data
// root as dottalkpp (identity catalog + board tables), so a token issued in the shell via
// `USER TOKEN <member>` authenticates here.
//
// Usage: dottalk_bbsd [--data <dir>] [--port <n>] [--model <name>] [--operator <member.key>]
//   --data      DATA root (default: <cwd>/dottalkpp/data). MUST match the CLI's data root.
//   --port      listen port (default 8765)
//   --model     Ollama model for CHAT (default qwen2.5-coder:7b)
//   --operator  operator/owner identity for save-restore + SHUTDOWN (default member.derald)

#include "bbs/bbs_server.hpp"
#include "identity/identity_admin.hpp"
#include "common/path_state.hpp"

#include <cstdint>
#include <filesystem>
#include <iostream>
#include <string>

namespace fs = std::filesystem;

int main(int argc, char** argv) {
    fs::path      data_root;
    std::uint16_t port  = 8765;
    std::string   model = "qwen2.5-coder:7b";
    std::string   op    = "member.derald";

    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        auto next = [&](const char* def) -> std::string { return (i + 1 < argc) ? std::string(argv[++i]) : std::string(def); };
        if      (a == "--data")     data_root = next("");
        else if (a == "--port")     { try { int p = std::stoi(next("8765")); if (p > 0 && p < 65536) port = static_cast<std::uint16_t>(p); } catch (...) {} }
        else if (a == "--model")    model = next("qwen2.5-coder:7b");
        else if (a == "--operator") op = next("member.derald");
        else if (a == "--help" || a == "-h") {
            std::cerr << "usage: dottalk_bbsd [--data <dir>] [--port <n>] [--model <name>] [--operator <member.key>]\n";
            return 0;
        }
    }
    if (data_root.empty()) data_root = fs::current_path() / "dottalkpp" / "data";

    std::error_code ec;
    if (!fs::exists(data_root / "metadata" / "identity", ec)) {
        std::cerr << "dottalk_bbsd: WARNING: " << (data_root / "metadata" / "identity").string()
                  << " not found. Pass --data <dir> pointing at dottalkpp/data so the identity "
                     "catalog + board tables match the CLI.\n";
    }

    // 1) DATA slot MUST be set before any identity/bbs access -- identity_store() caches its
    //    directory on first touch. identity_dir/bbs_dir both derive from Slot::DATA.
    dottalk::paths::set_slot(dottalk::paths::Slot::DATA, data_root);
    std::cerr << "dottalk_bbsd: data root = "
              << dottalk::paths::get_slot(dottalk::paths::Slot::DATA).string() << "\n";

    // 2) operator identity (owner) so serve() can save/restore it and honor SHUTDOWN.
    dottalk::identity::set_acting_member(op);

    // 3) serve -- blocks on the accept loop until an owner SHUTDOWN or a fatal socket error.
    //    (libsodium self-inits lazily inside token_crypto on first verify.)
    std::string err;
    std::cerr << "dottalk_bbsd: starting on 127.0.0.1:" << port << "  model=" << model
              << "  operator=" << op << "\n";
    const bool ok = dottalk::bbs::serve(port, model, err);
    if (!ok) { std::cerr << "dottalk_bbsd: serve failed: " << err << "\n"; return 1; }
    std::cerr << "dottalk_bbsd: stopped\n";
    return 0;
}
