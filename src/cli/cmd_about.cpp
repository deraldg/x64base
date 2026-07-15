// src/cli/cmd_about.cpp
//
// ABOUT
// Print project identity, lineage, author, history, and runtime environment.

// @dottalk.usage v1
// owner: DOT|ABOUT
// command: ABOUT
// category: report
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: ABOUT USAGE
// summary:
//   Print DotTalk++ project identity, lineage, author, runtime environment, and
//   current session summary.
//
// usage:
//   ABOUT
//   ABOUT USAGE
//
// notes:
//   ABOUT with no arguments prints the full project/runtime report.
//   ABOUT USAGE prints command usage only.
//   ABOUT is read-only and does not mutate table data or session state.
//
// risk:
//   mutates_table_data: no
//   mutates_session: no
//
// related:
//   VERSION
//   SQLVER
//

#include "cli/cmd_about.hpp"
#include "cli/command_output.hpp"
#include "xbase/about_info.hpp"
#include "xbase.hpp"

#include <cctype>
#include <iomanip>
#include <sstream>
#include <string>

#if defined(_WIN32) || defined(_WIN64) || defined(__WIN32__) || defined(__WINDOWS__)
    #define DT_OS_FAMILY "Windows"
    #ifdef _WIN64
        #define DT_ARCH "x64"
    #else
        #define DT_ARCH "x86"
    #endif
#elif defined(__linux__) || defined(__linux) || defined(linux)
    #define DT_OS_FAMILY "Linux"
    #ifdef __x86_64__
        #define DT_ARCH "x86_64"
    #elif defined(__i386__) || defined(__i486__) || defined(__i586__) || defined(__i686__)
        #define DT_ARCH "x86"
    #elif defined(__aarch64__)
        #define DT_ARCH "ARM64"
    #else
        #define DT_ARCH "unknown"
    #endif
#elif defined(__APPLE__) || defined(__MACH__)
    #include <TargetConditionals.h>
    #define DT_OS_FAMILY "macOS"
    #if TARGET_CPU_ARM64
        #define DT_ARCH "Apple Silicon (arm64)"
    #else
        #define DT_ARCH "x86_64 (Intel)"
    #endif
#elif defined(__FreeBSD__) || defined(__FreeBSD_kernel__)
    #define DT_OS_FAMILY "FreeBSD"
    #define DT_ARCH "unknown"
#else
    #define DT_OS_FAMILY "Unknown platform"
    #define DT_ARCH "unknown"
#endif

namespace
{
    using dottalk::helpdata::MessageId;

    std::string about_trim(std::string s)
    {
        while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) {
            s.erase(s.begin());
        }
        while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) {
            s.pop_back();
        }
        return s;
    }

    std::string about_upper(std::string s)
    {
        for (char& ch : s) {
            ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
        }
        return s;
    }

    bool is_about_usage_request(const std::string& raw)
    {
        std::string t = about_upper(about_trim(raw));
        if (t.rfind("ABOUT ", 0) == 0) {
            t = about_upper(about_trim(t.substr(6)));
        }
        return t == "USAGE" || t == "HELP" || t == "?";
    }

    std::string about_text(MessageId id,
                           const std::unordered_map<std::string, std::string>& vars = {})
    {
        return cli::cmdout::message_text(id, vars);
    }

    void print_about_usage()
    {
        cli::cmdout::print_message(MessageId::GlobalUsageTitle);
        cli::cmdout::print_line("  " + about_text(MessageId::AboutUsageLine));
        cli::cmdout::print_line("  " + about_text(MessageId::AboutUsageUsageLine));
    }

    void print_section(const std::string& title)
    {
        cli::cmdout::print_line("");
        cli::cmdout::print_line(title);
        cli::cmdout::print_line(std::string(title.size(), '-'));
    }

    void print_kv(const std::string& key, const std::string& value)
    {
        std::ostringstream oss;
        oss << std::left << std::setw(16) << key << ": " << value;
        cli::cmdout::print_line(oss.str());
    }

    void print_kv(MessageId key_id, const std::string& value)
    {
        print_kv(about_text(key_id), value);
    }

    std::string yes_no(bool v)
    {
        return about_text(v ? MessageId::AboutYes : MessageId::AboutNo);
    }

    std::string enabled_disabled(bool v)
    {
        return about_text(v ? MessageId::AboutEnabled : MessageId::AboutDisabled);
    }

    std::string safe_filename(const xbase::DbArea& db)
    {
        try
        {
            const std::string s = db.filename();
            return s.empty() ? about_text(MessageId::AboutNone) : s;
        }
        catch (...)
        {
            return about_text(MessageId::AboutNone);
        }
    }

    std::string safe_record_count(const xbase::DbArea& db)
    {
        try
        {
            std::ostringstream oss;
            oss << db.recCount();
            return oss.str();
        }
        catch (...)
        {
            return about_text(MessageId::AboutUnavailable);
        }
    }

    std::string safe_field_count(const xbase::DbArea& db)
    {
        try
        {
            std::ostringstream oss;
            oss << db.fields().size();
            return oss.str();
        }
        catch (...)
        {
            return about_text(MessageId::AboutUnavailable);
        }
    }

    std::string compiler_line()
    {
    #if defined(__GNUC__)
        std::ostringstream oss;
        oss << "GCC " << __GNUC__ << "." << __GNUC_MINOR__ << "." << __GNUC_PATCHLEVEL__;
        return oss.str();
    #elif defined(_MSC_VER)
        std::ostringstream oss;
        oss << "MSVC " << _MSC_VER;
        return oss.str();
    #elif defined(__clang__)
        std::ostringstream oss;
        oss << "Clang " << __clang_major__ << "." << __clang_minor__ << "." << __clang_patchlevel__;
        return oss.str();
    #else
        return "Unknown";
    #endif
    }

    void print_page_1()
    {
        cli::cmdout::print_message(
            MessageId::AboutPage1Text,
            {{"os_family", DT_OS_FAMILY},
             {"arch", DT_ARCH},
             {"cpp_standard", "C++" + std::to_string(__cplusplus / 100)},
             {"compiler", compiler_line()}});
    }

    void print_page_2(xbase::DbArea& db)
    {
        const std::string file_name = safe_filename(db);
        const std::string root = about_info::path_root_of(file_name);
        const about_info::DiskInfo dsk = about_info::disk_info(root);
        const about_info::ConsoleInfo con = about_info::console_size();
        const std::string page_title = about_text(MessageId::AboutPage2Title);

        cli::cmdout::print_line("");
        cli::cmdout::print_line(page_title);
        cli::cmdout::print_line(std::string(page_title.size(), '='));

        print_section(about_text(MessageId::AboutSectionApplication));
        print_kv(MessageId::AboutKeyName, about_info::app_name());
        print_kv(MessageId::AboutKeyBuildMode, about_info::build_mode());
        print_kv(MessageId::AboutKeyBuildDate, about_info::build_date_time());
        print_kv(MessageId::AboutKeyArchitecture, about_info::architecture());
        print_kv(MessageId::AboutKeyCompiler, about_info::compiler_string());
        print_kv(MessageId::AboutKeyCppStd, about_info::cpp_standard_string());

        print_section(about_text(MessageId::AboutSectionOperatingSystem));
        print_kv(MessageId::AboutKeyOs, about_info::windows_version());

        print_section(about_text(MessageId::AboutSectionHardware));
        {
            std::ostringstream oss;
            oss << about_info::cpu_logical_count();
            print_kv(MessageId::AboutKeyCpuThreads, oss.str());
        }
        print_kv(MessageId::AboutKeyInstalledRam, about_info::format_bytes(about_info::installed_ram_bytes()));

        print_section(about_text(MessageId::AboutSectionStorage));
        print_kv(MessageId::AboutKeyDiskRoot, dsk.root_path);
        print_kv(MessageId::AboutKeyDiskFree, about_info::format_bytes(dsk.free_bytes));
        print_kv(MessageId::AboutKeyDiskTotal, about_info::format_bytes(dsk.total_bytes));

        print_section(about_text(MessageId::AboutSectionConsole));
        {
            std::ostringstream oss;
            oss << con.width << " x " << con.height;
            print_kv(MessageId::AboutKeySize, oss.str());
        }
        print_kv(MessageId::AboutKeyAnsiVt, enabled_disabled(about_info::vt_enabled()));

        print_section(about_text(MessageId::AboutSectionNetwork));
        print_kv(MessageId::AboutKeyComputerName, about_info::computer_name_str());
        print_kv(MessageId::AboutKeyLocalIpv4, about_info::local_ipv4());

        print_section(about_text(MessageId::AboutSectionCurrentSession));
        print_kv(MessageId::AboutKeyFileOpen, yes_no(db.isOpen()));
        print_kv(MessageId::AboutKeyDbfile, file_name);
        print_kv(MessageId::AboutKeyRecords, safe_record_count(db));
        print_kv(MessageId::AboutKeyFields, safe_field_count(db));

        cli::cmdout::print_line("");
    }
}

void cmd_ABOUT(xbase::DbArea& db, std::istringstream& in)
{
    if (is_about_usage_request(in.str())) {
        print_about_usage();
        return;
    }

    print_page_1();
    print_page_2(db);
}
