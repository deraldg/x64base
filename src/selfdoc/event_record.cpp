// @dottalk.file v1
// subsystem: selfdoc
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: AIF-050
// owner: member.derald
// status: supported

// event_record.cpp — runtime -> documentation intake seam (M5).
#include "selfdoc/event_record.hpp"
#include "common/path_state.hpp"      // dottalk::paths::get_slot

#include <ctime>
#include <filesystem>
#include <fstream>
#include <system_error>

namespace fs = std::filesystem;

namespace dottalk::selfdoc {

std::string record_event(const std::string& kind,
                         const std::string& slug,
                         const std::string& actor,
                         const std::string& summary,
                         const std::vector<std::string>& lines) {
    try {
        const fs::path dir = dottalk::paths::get_slot(dottalk::paths::Slot::DATA) / "metadata" / "bbs" / "proofs";
        std::error_code ec; fs::create_directories(dir, ec);
        std::time_t t = std::time(nullptr);
        char ts[32]; std::strftime(ts, sizeof ts, "%Y%m%d_%H%M%S", std::localtime(&t));
        const std::string name = std::string(ts) + "_" + kind + "_" + slug + ".txt";
        const fs::path path = dir / name;
        std::ofstream out(path.string());
        if (!out) return {};
        out << "# proof transcript (runtime intake, M5)\n";
        out << "kind    : " << kind    << "\n";
        out << "slug    : " << slug    << "\n";
        out << "actor   : " << actor   << "\n";
        out << "at      : " << ts      << "\n";
        out << "summary : " << summary << "\n";
        out << "----\n";
        for (const auto& l : lines) out << l << "\n";
        return path.string();
    } catch (...) {
        return {};   // best-effort; a logging failure must never break the command
    }
}

} // namespace dottalk::selfdoc
