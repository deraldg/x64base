// @dottalk.usage v1
// owner: DOT|IMAGE
// command: IMAGE
// category: shell
// status: supported
// noargs: usage
// effect: mixed
// mutates: external-viewer
// usage-access: IMAGE USAGE
// summary:
//   Inspect image file metadata or open a supported image file in the operating
//   system viewer.
//
// usage:
//   IMAGE USAGE
//   IMAGE DEFAULT
//   IMAGE <file>
//   IMAGE INFO DEFAULT
//   IMAGE INFO <file>
//
// notes:
//   IMAGE with no arguments prints usage.
//   IMAGE USAGE prints usage and does not open a viewer.
//   IMAGE DEFAULT opens "arctic fox.png" beside the running executable.
//   IMAGE INFO DEFAULT reports metadata for the default image.
//   IMAGE INFO <file> prints file extension, size, and recognized-image status.
//   IMAGE <file> opens the OS viewer on Windows.
//   Non-Windows viewer launch is currently not implemented.
//   IMAGE does not mutate table data.
//
// risk:
//   launches_external_viewer: IMAGE DEFAULT or IMAGE <file> on Windows
//   reads_filesystem_metadata: yes
//   mutates_table_data: no
//
// related:
//   WEB
//   BANG
//

#include "cmd_image_display.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"

#ifdef _WIN32
#include <windows.h>
#include <shellapi.h>
#endif

namespace fs = std::filesystem;
using xbase::DbArea;

namespace {

constexpr const char* kDefaultImageName = "arctic fox.png";

static std::string upcopy(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static std::string trim(std::string s)
{
    auto issp = [](unsigned char c) {
        return c == ' ' || c == '\t' || c == '\r' || c == '\n';
    };

    while (!s.empty() && issp(static_cast<unsigned char>(s.front()))) {
        s.erase(s.begin());
    }
    while (!s.empty() && issp(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
    return s;
}

static std::string read_pathish(std::istringstream& iss)
{
    iss >> std::ws;
    if (!iss.good()) return {};

    if (iss.peek() == '"' || iss.peek() == '\'') {
        const char q = static_cast<char>(iss.get());
        std::string out;
        char c = '\0';
        while (iss.get(c)) {
            if (c == q) break;
            out.push_back(c);
        }
        return out;
    }

    std::string s;
    iss >> s;
    return s;
}

static bool file_exists_regular(const fs::path& p)
{
    std::error_code ec;
    return fs::exists(p, ec) && fs::is_regular_file(p, ec);
}

static fs::path executable_directory()
{
#ifdef _WIN32
    // Use the running executable, not the process working directory.
    // A large dynamic buffer avoids the legacy MAX_PATH limit.
    std::wstring buffer(32768, L'\0');
    const DWORD length = ::GetModuleFileNameW(
        nullptr,
        buffer.data(),
        static_cast<DWORD>(buffer.size()));

    if (length > 0 && length < buffer.size()) {
        buffer.resize(length);
        return fs::path(buffer).parent_path();
    }
#endif

    std::error_code ec;
    const fs::path current = fs::current_path(ec);
    return ec ? fs::path(".") : current;
}

static fs::path default_image_path()
{
    return executable_directory() / kDefaultImageName;
}

static fs::path resolve_image_operand(const std::string& operand)
{
    return upcopy(operand) == "DEFAULT"
        ? default_image_path()
        : fs::path(operand);
}

static bool supported_image_ext(const std::string& extUpper)
{
    return extUpper == ".BMP"  ||
           extUpper == ".PNG"  ||
           extUpper == ".JPG"  ||
           extUpper == ".JPEG" ||
           extUpper == ".GIF"  ||
           extUpper == ".TIF"  ||
           extUpper == ".TIFF" ||
           extUpper == ".WEBP" ||
           extUpper == ".ICO";
}

static void usage()
{
    std::cout
        << "Usage:\n"
        << "  IMAGE USAGE\n"
        << "  IMAGE DEFAULT\n"
        << "  IMAGE <file>\n"
        << "  IMAGE INFO DEFAULT\n"
        << "  IMAGE INFO <file>\n"
        << "Default image:\n"
        << "  " << kDefaultImageName << " (beside the executable)\n";
}

static void print_info(const fs::path& p)
{
    std::error_code ec;
    const auto sz = fs::file_size(p, ec);
    const std::string ext = upcopy(p.extension().string());

    std::cout << "IMAGE INFO\n";
    std::cout << "  File : " << p.string() << "\n";
    std::cout << "  Ext  : " << (ext.empty() ? "(none)" : ext) << "\n";
    if (!ec) {
        std::cout << "  Size : " << sz << " byte(s)\n";
    } else {
        std::cout << "  Size : (unavailable)\n";
    }
    std::cout << "  Type : "
              << (supported_image_ext(ext) ? "recognized image extension" : "unknown/unsupported extension")
              << "\n";
}

#ifdef _WIN32
static std::intptr_t open_external_viewer_rc(const fs::path& p)
{
    HINSTANCE rc = ::ShellExecuteW(
        nullptr,
        L"open",
        p.c_str(),
        nullptr,
        nullptr,
        SW_SHOWNORMAL);

    return reinterpret_cast<std::intptr_t>(rc);
}
#endif

} // namespace

void cmd_IMAGE_DISPLAY(DbArea&, std::istringstream& iss)
{
    std::string tok;
    if (!(iss >> tok)) {
        usage();
        return;
    }

    const std::string tokU = upcopy(tok);


    if (tokU == "USAGE" || tokU == "HELP" || tokU == "?") {
        usage();
        return;
    }
    if (tokU == "INFO") {
        const std::string raw = trim(read_pathish(iss));
        if (raw.empty()) {
            usage();
            return;
        }

        const fs::path p = resolve_image_operand(raw);
        if (!file_exists_regular(p)) {
            std::cout << "IMAGE INFO: file not found: " << p.string() << "\n";
            return;
        }

        print_info(p);
        return;
    }

    // IMAGE DEFAULT or existing IMAGE <file> form.
    const fs::path p = resolve_image_operand(tok);

    if (!file_exists_regular(p)) {
        std::cout << "IMAGE: file not found: " << p.string() << "\n";
        return;
    }

    const std::string ext = upcopy(p.extension().string());
    if (!supported_image_ext(ext)) {
        std::cout << "IMAGE: warning: unrecognized image extension: "
                  << (ext.empty() ? "(none)" : ext) << "\n";
    }

#ifdef _WIN32
    const std::intptr_t rc = open_external_viewer_rc(p);
    if (rc <= 32) {
        std::cout << "IMAGE: failed to open viewer for "
                  << p.string()
                  << " (ShellExecute rc=" << rc << ")\n";
        return;
    }

    std::cout << "IMAGE: opening " << p.string() << "\n";
#else
    std::cout << "IMAGE: OS viewer not implemented on this platform\n";
#endif
}