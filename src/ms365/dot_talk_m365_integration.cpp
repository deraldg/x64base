#include "xbase.hpp"
#include "dot_talk_m365_integration.hpp"

#include <algorithm>
#include <cctype>
#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <system_error>
#include <vector>

namespace fs = std::filesystem;

namespace dottalk::m365
{
    namespace
    {
        std::string g_oneDriveRoot;
        bool        g_oneDriveInitialized = false;

        bool ensure_folder(const fs::path& p)
        {
            std::error_code ec;
            if (fs::exists(p, ec))
                return fs::is_directory(p, ec);

            return fs::create_directories(p, ec) && !ec;
        }

        std::string get_env(const char* name)
        {
            const char* v = std::getenv(name);
            return v ? std::string(v) : std::string{};
        }

        bool detect_onedrive_root()
        {
            if (g_oneDriveInitialized)
                return !g_oneDriveRoot.empty();

            std::string overrideRoot = get_env("DOTTALK_ONEDRIVE_ROOT");
            if (!overrideRoot.empty() && fs::exists(overrideRoot))
            {
                g_oneDriveRoot = overrideRoot;
                g_oneDriveInitialized = true;
                return true;
            }

            std::vector<std::string> candidates;
            for (auto name : { "ONEDRIVE", "ONEDRIVE_COMMERCIAL", "ONEDRIVE_CONSUMER" })
            {
                auto v = get_env(name);
                if (!v.empty())
                    candidates.push_back(v);
            }

#ifdef _WIN32
            auto userProfile = get_env("USERPROFILE");
            if (!userProfile.empty())
                candidates.push_back(userProfile + "\\OneDrive");
#endif

            for (const auto& c : candidates)
            {
                std::error_code ec;
                if (!c.empty() && fs::exists(c, ec) && fs::is_directory(c, ec))
                {
                    g_oneDriveRoot = c;
                    g_oneDriveInitialized = true;
                    return true;
                }
            }

            g_oneDriveInitialized = true;
            g_oneDriveRoot.clear();
            return false;
        }

        fs::path root_path()
        {
            if (!detect_onedrive_root())
                return fs::path();
            return fs::path(g_oneDriveRoot);
        }

        fs::path exchange_root()
        {
            auto r = root_path();
            if (r.empty())
                return fs::path();
            return r / Paths::Root;
        }

        fs::path subfolder_path(const char* subfolder)
        {
            auto r = root_path();
            if (r.empty())
                return fs::path();
            return r / subfolder;
        }

        std::string make_filename_timestamp()
        {
            using clock = std::chrono::system_clock;
            auto now = clock::now();
            auto t   = clock::to_time_t(now);
            std::tm tm{};
#ifdef _WIN32
            gmtime_s(&tm, &t);
#else
            gmtime_r(&t, &tm);
#endif
            std::ostringstream oss;
            oss << std::put_time(&tm, "%Y%m%d_%H%M%S");
            return oss.str();
        }

        Timestamp make_iso_timestamp()
        {
            using clock = std::chrono::system_clock;
            auto now = clock::now();
            auto t   = clock::to_time_t(now);
            std::tm tm{};
#ifdef _WIN32
            gmtime_s(&tm, &t);
#else
            gmtime_r(&t, &tm);
#endif
            std::ostringstream oss;
            oss << std::put_time(&tm, "%Y-%m-%dT%H:%M:%SZ");
            return Timestamp{ oss.str() };
        }

        FileKind classify_kind(const std::string& name)
        {
            if (name.rfind(Naming::TablePrefixOutbound, 0) == 0 ||
                name.rfind(Naming::TablePrefixInbound, 0) == 0)
            {
                if (name.size() >= 4 &&
                    name.compare(name.size() - 4, 4, Naming::ExtCSV) == 0)
                    return FileKind::TableCSV;
            }

            if (name.rfind(Naming::RecordPrefixOutbound, 0) == 0 ||
                name.rfind(Naming::RecordPrefixInbound, 0) == 0)
            {
                if (name.size() >= 5 &&
                    name.compare(name.size() - 5, 5, Naming::ExtJSON) == 0)
                    return FileKind::RecordJSON;
            }

            if (name.rfind(Naming::NotesPrefixOutbound, 0) == 0 ||
                name.rfind(Naming::NotesPrefixInbound, 0) == 0)
            {
                if (name.size() >= 4 &&
                    name.compare(name.size() - 4, 4, Naming::ExtTXT) == 0)
                    return FileKind::NotesTXT;
            }

            return FileKind::Unknown;
        }

        Direction classify_direction(const std::string& name)
        {
            if (name.rfind("import_", 0) == 0)
                return Direction::Inbound;
            return Direction::Outbound;
        }

        Timestamp file_timestamp_from_fs(const fs::path& p)
        {
            std::error_code ec;
            auto ftime = fs::last_write_time(p, ec);
            if (ec)
                return make_iso_timestamp();

            auto sctp = std::chrono::time_point_cast<std::chrono::system_clock::duration>(
                ftime - fs::file_time_type::clock::now()
                + std::chrono::system_clock::now());

            auto t = std::chrono::system_clock::to_time_t(sctp);
            std::tm tm{};
#ifdef _WIN32
            gmtime_s(&tm, &t);
#else
            gmtime_r(&t, &tm);
#endif
            std::ostringstream oss;
            oss << std::put_time(&tm, "%Y-%m-%dT%H:%M:%SZ");
            return Timestamp{ oss.str() };
        }
    }

    Timestamp make_current_timestamp_utc()
    {
        return make_iso_timestamp();
    }

    bool is_onedrive_available()
    {
        return detect_onedrive_root();
    }

    std::string get_onedrive_root()
    {
        auto p = root_path();
        return p.empty() ? std::string{} : p.string();
    }

    std::string get_exchange_root()
    {
        auto p = exchange_root();
        return p.empty() ? std::string{} : p.string();
    }

    std::string get_inbound_folder()
    {
        auto p = subfolder_path(Paths::Inbound);
        return p.empty() ? std::string{} : p.string();
    }

    std::string get_outbound_folder()
    {
        auto p = subfolder_path(Paths::Outbound);
        return p.empty() ? std::string{} : p.string();
    }

    std::string get_archive_folder()
    {
        auto p = subfolder_path(Paths::Archive);
        return p.empty() ? std::string{} : p.string();
    }

    std::string build_path(const std::string& subfolder, const std::string& file_name)
    {
        auto r = root_path();
        if (r.empty())
            return {};

        fs::path p = r / subfolder / file_name;
        return p.string();
    }

    FileDescriptor classify_file(const std::string& full_path, const std::string& file_name)
    {
        FileDescriptor fd;
        fd.full_path = full_path;
        fd.file_name = file_name;
        fd.kind      = classify_kind(file_name);
        fd.direction = classify_direction(file_name);
        fd.created   = file_timestamp_from_fs(fs::path(full_path));
        return fd;
    }

    bool export_table_to_csv(
        const std::string& table_name,
        const Timestamp&,
        std::string& out_full_path)
    {
        auto outDir = subfolder_path(Paths::Outbound);
        if (outDir.empty() || !ensure_folder(outDir))
            return false;

        std::string fname = std::string(Naming::TablePrefixOutbound)
                          + table_name + "_" + make_filename_timestamp()
                          + Naming::ExtCSV;

        fs::path full = outDir / fname;

        std::ofstream ofs(full, std::ios::binary);
        if (!ofs)
            return false;

        ofs << "placeholder_column\n";
        ofs << "placeholder_value\n";

        ofs.close();
        out_full_path = full.string();
        return true;
    }

    bool export_record_to_json(
        const std::string& table_name,
        std::int64_t       record_id,
        const Timestamp&   ts,
        std::string&       out_full_path)
    {
        auto outDir = subfolder_path(Paths::Outbound);
        if (outDir.empty() || !ensure_folder(outDir))
            return false;

        std::ostringstream idss;
        idss << record_id;

        std::string fname = std::string(Naming::RecordPrefixOutbound)
                          + table_name + "_" + idss.str()
                          + Naming::ExtJSON;

        fs::path full = outDir / fname;

        std::ofstream ofs(full, std::ios::binary);
        if (!ofs)
            return false;

        ofs << "{\n";
        ofs << "  \"table\": \"" << table_name << "\",\n";
        ofs << "  \"id\": " << record_id << ",\n";
        ofs << "  \"metadata\": {\n";
        ofs << "    \"last_update\": \"" << ts.iso_8601 << "\",\n";
        ofs << "    \"source\": \"dottalk\"\n";
        ofs << "  }\n";
        ofs << "}\n";

        ofs.close();
        out_full_path = full.string();
        return true;
    }

    bool export_notes_to_txt(
        const std::string& topic,
        const Timestamp&   ts,
        std::string&       out_full_path)
    {
        auto outDir = subfolder_path(Paths::Outbound);
        if (outDir.empty() || !ensure_folder(outDir))
            return false;

        std::string fname = std::string(Naming::NotesPrefixOutbound)
                          + topic + "_" + make_filename_timestamp()
                          + Naming::ExtTXT;

        fs::path full = outDir / fname;

        std::ofstream ofs(full, std::ios::binary);
        if (!ofs)
            return false;

        ofs << "Notes topic: " << topic << "\n";
        ofs << "Created: " << ts.iso_8601 << "\n";
        ofs << "\n";
        ofs << "This is placeholder content generated by DotTalk++.\n";

        ofs.close();
        out_full_path = full.string();
        return true;
    }

    InboundScanResult scan_inbound_folder()
    {
        InboundScanResult result;

        auto inDir = subfolder_path(Paths::Inbound);
        if (inDir.empty())
        {
            result.ok = false;
            result.error_message = "OneDrive root not found.";
            return result;
        }

        if (!ensure_folder(inDir))
        {
            result.ok = false;
            result.error_message = "Failed to create or access inbound folder.";
            return result;
        }

        std::error_code ec;
        for (auto& entry : fs::directory_iterator(inDir, ec))
        {
            if (ec)
                break;

            if (!entry.is_regular_file())
                continue;

            auto p  = entry.path();
            auto fn = p.filename().string();

            FileDescriptor fd = classify_file(p.string(), fn);
            if (fd.kind == FileKind::Unknown)
                continue;

            fd.direction = Direction::Inbound;
            result.files.push_back(std::move(fd));
        }

        if (ec)
        {
            result.ok = false;
            result.error_message = "Error scanning inbound folder.";
            return result;
        }

        result.ok = true;
        return result;
    }

    bool import_table_from_csv(
        const FileDescriptor& file,
        std::string&          out_table_name)
    {
        fs::path p(file.full_path);
        if (!fs::exists(p))
            return false;

        std::string name = file.file_name;
        std::string prefix = Naming::TablePrefixInbound;
        auto pos = name.find(prefix);
        if (pos == std::string::npos)
            prefix = Naming::TablePrefixOutbound;

        pos = name.find(prefix);
        if (pos != std::string::npos)
        {
            auto start = pos + prefix.size();
            auto end   = name.find('_', start);
            if (end == std::string::npos)
                end = name.find('.', start);
            if (end != std::string::npos)
                out_table_name = name.substr(start, end - start);
        }

        return true;
    }

    bool import_record_from_json(
        const FileDescriptor& file,
        std::string&          out_table_name,
        std::int64_t&         out_record_id)
    {
        fs::path p(file.full_path);
        if (!fs::exists(p))
            return false;

        std::string name = file.file_name;
        std::string prefix = Naming::RecordPrefixInbound;
        auto pos = name.find(prefix);
        if (pos == std::string::npos)
            prefix = Naming::RecordPrefixOutbound;

        pos = name.find(prefix);
        if (pos != std::string::npos)
        {
            auto start = pos + prefix.size();
            auto mid   = name.find('_', start);
            auto end   = name.find('.', mid + 1);

            if (mid != std::string::npos && end != std::string::npos)
            {
                out_table_name = name.substr(start, mid - start);
                auto idStr = name.substr(mid + 1, end - (mid + 1));
                try
                {
                    out_record_id = std::stoll(idStr);
                }
                catch (...)
                {
                    out_record_id = 0;
                }
            }
        }

        return true;
    }

    bool import_notes_from_txt(
        const FileDescriptor& file,
        std::string&          out_topic)
    {
        fs::path p(file.full_path);
        if (!fs::exists(p))
            return false;

        std::string name = file.file_name;
        std::string prefix = Naming::NotesPrefixInbound;
        auto pos = name.find(prefix);
        if (pos == std::string::npos)
            prefix = Naming::NotesPrefixOutbound;

        pos = name.find(prefix);
        if (pos != std::string::npos)
        {
            auto start = pos + prefix.size();
            auto end   = name.find('_', start);
            if (end == std::string::npos)
                end = name.find('.', start);
            if (end != std::string::npos)
                out_topic = name.substr(start, end - start);
        }

        return true;
    }

    bool archive_file(
        const FileDescriptor& file,
        std::string&          out_archived_path)
    {
        auto archRoot = subfolder_path(Paths::Archive);
        if (archRoot.empty() || !ensure_folder(archRoot))
            return false;

        if (file.created.iso_8601.size() < 7)
            return false;

        std::string year  = file.created.iso_8601.substr(0, 4);
        std::string month = file.created.iso_8601.substr(5, 2);

        fs::path yearDir  = fs::path(archRoot) / year;
        fs::path monthDir = yearDir / month;

        if (!ensure_folder(yearDir) || !ensure_folder(monthDir))
            return false;

        fs::path src = file.full_path;
        fs::path dst = monthDir / file.file_name;

        std::error_code ec;
        fs::rename(src, dst, ec);
        if (ec)
        {
            fs::copy_file(src, dst, fs::copy_options::overwrite_existing, ec);
            if (ec)
                return false;
            fs::remove(src, ec);
            if (ec)
                return false;
        }

        out_archived_path = dst.string();
        return true;
    }
}

namespace
{
    std::string trim(const std::string& s)
    {
        std::size_t a = 0;
        while (a < s.size() && std::isspace(static_cast<unsigned char>(s[a])))
            ++a;

        std::size_t b = s.size();
        while (b > a && std::isspace(static_cast<unsigned char>(s[b - 1])))
            --b;

        return s.substr(a, b - a);
    }

    std::string upper(std::string s)
    {
        std::transform(
            s.begin(), s.end(), s.begin(),
            [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
        return s;
    }

    std::string remainder_trimmed(std::istringstream& iss)
    {
        std::string rest;
        std::getline(iss, rest);
        return trim(rest);
    }

    bool iequals(const std::string& a, const std::string& b)
    {
        return upper(a) == upper(b);
    }

    const char* kind_name(dottalk::m365::FileKind k)
    {
        using dottalk::m365::FileKind;
        switch (k)
        {
        case FileKind::TableCSV:   return "TABLE";
        case FileKind::RecordJSON: return "RECORD";
        case FileKind::NotesTXT:   return "NOTES";
        default:                   return "UNKNOWN";
        }
    }

    const char* dir_name(dottalk::m365::Direction d)
    {
        using dottalk::m365::Direction;
        switch (d)
        {
        case Direction::Inbound:  return "INBOUND";
        case Direction::Outbound: return "OUTBOUND";
        default:                  return "UNKNOWN";
        }
    }

    void print_file_row(const dottalk::m365::FileDescriptor& f)
    {
        std::cout
            << kind_name(f.kind)
            << "  "
            << dir_name(f.direction)
            << "  "
            << f.file_name;

        if (!f.created.iso_8601.empty())
            std::cout << "  [" << f.created.iso_8601 << "]";

        std::cout << "\n";
    }

    void print_usage()
    {
        std::cout
            << "MS365 STATUS\n"
            << "MS365 SCAN\n"
            << "MS365 LIST INBOUND\n"
            << "MS365 LIST OUTBOUND\n"
            << "MS365 EXPORT TABLE <table>\n"
            << "MS365 EXPORT RECORD <table> <recno>\n"
            << "MS365 EXPORT NOTES <topic>\n"
            << "MS365 IMPORT <file>\n"
            << "MS365 IMPORT ALL\n"
            << "MS365 ARCHIVE <file>\n"
            << "MS365 ARCHIVE ALL\n";
    }

    bool find_inbound_file_by_name(
        const std::string& file_name,
        dottalk::m365::FileDescriptor& out_file,
        std::string& out_error)
    {
        auto scan = dottalk::m365::scan_inbound_folder();
        if (!scan.ok)
        {
            out_error = scan.error_message;
            return false;
        }

        for (const auto& f : scan.files)
        {
            if (iequals(f.file_name, file_name))
            {
                out_file = f;
                return true;
            }
        }

        out_error = "File not found in inbound folder.";
        return false;
    }

    bool classify_arbitrary_file(
        const std::string& path_or_name,
        dottalk::m365::FileDescriptor& out_file)
    {
        std::string full = path_or_name;
        std::string name = path_or_name;

        auto slash = path_or_name.find_last_of("/\\");
        if (slash != std::string::npos)
            name = path_or_name.substr(slash + 1);

        out_file = dottalk::m365::classify_file(full, name);
        return out_file.kind != dottalk::m365::FileKind::Unknown;
    }

    void do_status()
    {
        using namespace dottalk::m365;

        std::cout << "MS365 STATUS\n";

        if (!is_onedrive_available())
        {
            std::cout << "  OneDrive : not detected\n";
            std::cout << "  Hint     : set DOTTALK_ONEDRIVE_ROOT or ONEDRIVE\n";
            return;
        }

        std::cout << "  OneDrive : detected\n";
        std::cout << "  Root     : " << get_onedrive_root() << "\n";
        std::cout << "  Exchange : " << get_exchange_root() << "\n";
        std::cout << "  Inbound  : " << get_inbound_folder() << "\n";
        std::cout << "  Outbound : " << get_outbound_folder() << "\n";
        std::cout << "  Archive  : " << get_archive_folder() << "\n";
    }

    void do_scan()
    {
        using namespace dottalk::m365;

        auto res = scan_inbound_folder();
        if (!res.ok)
        {
            std::cout << "MS365 SCAN failed: " << res.error_message << "\n";
            return;
        }

        std::cout << "Inbound files: " << res.files.size() << "\n";
        for (const auto& f : res.files)
            print_file_row(f);
    }

    void do_list(const std::string& which)
    {
        using namespace dottalk::m365;

        const std::string u = upper(which);

        if (u == "INBOUND")
        {
            do_scan();
            return;
        }

        if (u == "OUTBOUND")
        {
            if (!is_onedrive_available())
            {
                std::cout << "MS365 LIST OUTBOUND failed: OneDrive not detected.\n";
                return;
            }

            std::cout << "Outbound folder: " << get_outbound_folder() << "\n";
            std::cout << "Listing outbound files is not yet implemented in backend.\n";
            return;
        }

        std::cout << "Usage: MS365 LIST INBOUND|OUTBOUND\n";
    }

    void do_export_table(const std::string& table_name)
    {
        using namespace dottalk::m365;

        if (table_name.empty())
        {
            std::cout << "Usage: MS365 EXPORT TABLE <table>\n";
            return;
        }

        std::string out_path;
        if (!export_table_to_csv(table_name, make_current_timestamp_utc(), out_path))
        {
            std::cout << "MS365 EXPORT TABLE failed.\n";
            return;
        }

        std::cout << "Exported table: " << table_name << "\n";
        std::cout << "Path: " << out_path << "\n";
    }

    void do_export_record(const std::string& table_name, const std::string& recno_text)
    {
        using namespace dottalk::m365;

        if (table_name.empty() || recno_text.empty())
        {
            std::cout << "Usage: MS365 EXPORT RECORD <table> <recno>\n";
            return;
        }

        std::int64_t recno = 0;
        try
        {
            recno = std::stoll(recno_text);
        }
        catch (...)
        {
            std::cout << "Invalid record number: " << recno_text << "\n";
            return;
        }

        std::string out_path;
        if (!export_record_to_json(table_name, recno, make_current_timestamp_utc(), out_path))
        {
            std::cout << "MS365 EXPORT RECORD failed.\n";
            return;
        }

        std::cout << "Exported record: " << table_name << " #" << recno << "\n";
        std::cout << "Path: " << out_path << "\n";
    }

    void do_export_notes(const std::string& topic)
    {
        using namespace dottalk::m365;

        if (topic.empty())
        {
            std::cout << "Usage: MS365 EXPORT NOTES <topic>\n";
            return;
        }

        std::string out_path;
        if (!export_notes_to_txt(topic, make_current_timestamp_utc(), out_path))
        {
            std::cout << "MS365 EXPORT NOTES failed.\n";
            return;
        }

        std::cout << "Exported notes: " << topic << "\n";
        std::cout << "Path: " << out_path << "\n";
    }

    void do_import_one(const dottalk::m365::FileDescriptor& f)
    {
        using namespace dottalk::m365;

        switch (f.kind)
        {
        case FileKind::TableCSV:
        {
            std::string table_name;
            if (!import_table_from_csv(f, table_name))
            {
                std::cout << "Import failed: " << f.file_name << "\n";
                return;
            }

            std::cout << "Imported TABLE file: " << f.file_name;
            if (!table_name.empty())
                std::cout << "  -> table=" << table_name;
            std::cout << "\n";
            return;
        }

        case FileKind::RecordJSON:
        {
            std::string table_name;
            std::int64_t record_id = 0;
            if (!import_record_from_json(f, table_name, record_id))
            {
                std::cout << "Import failed: " << f.file_name << "\n";
                return;
            }

            std::cout << "Imported RECORD file: " << f.file_name;
            if (!table_name.empty())
                std::cout << "  -> table=" << table_name;
            if (record_id != 0)
                std::cout << " id=" << record_id;
            std::cout << "\n";
            return;
        }

        case FileKind::NotesTXT:
        {
            std::string topic;
            if (!import_notes_from_txt(f, topic))
            {
                std::cout << "Import failed: " << f.file_name << "\n";
                return;
            }

            std::cout << "Imported NOTES file: " << f.file_name;
            if (!topic.empty())
                std::cout << "  -> topic=" << topic;
            std::cout << "\n";
            return;
        }

        default:
            std::cout << "Unsupported file kind: " << f.file_name << "\n";
            return;
        }
    }

    void do_import(const std::string& arg)
    {
        using namespace dottalk::m365;

        if (arg.empty())
        {
            std::cout << "Usage: MS365 IMPORT <file>|ALL\n";
            return;
        }

        if (iequals(arg, "ALL"))
        {
            auto scan = scan_inbound_folder();
            if (!scan.ok)
            {
                std::cout << "MS365 IMPORT ALL failed: " << scan.error_message << "\n";
                return;
            }

            if (scan.files.empty())
            {
                std::cout << "No inbound files.\n";
                return;
            }

            std::cout << "Importing " << scan.files.size() << " inbound file(s)...\n";
            for (const auto& f : scan.files)
                do_import_one(f);

            return;
        }

        FileDescriptor f;
        std::string err;

        if (!find_inbound_file_by_name(arg, f, err))
        {
            if (classify_arbitrary_file(arg, f))
            {
                do_import_one(f);
                return;
            }

            std::cout << "MS365 IMPORT failed: " << err << "\n";
            return;
        }

        do_import_one(f);
    }

    void do_archive_one(const dottalk::m365::FileDescriptor& f)
    {
        std::string archived_path;
        if (!dottalk::m365::archive_file(f, archived_path))
        {
            std::cout << "Archive failed: " << f.file_name << "\n";
            return;
        }

        std::cout << "Archived: " << f.file_name << "\n";
        std::cout << "Path: " << archived_path << "\n";
    }

    void do_archive(const std::string& arg)
    {
        using namespace dottalk::m365;

        if (arg.empty())
        {
            std::cout << "Usage: MS365 ARCHIVE <file>|ALL\n";
            return;
        }

        if (iequals(arg, "ALL"))
        {
            auto scan = scan_inbound_folder();
            if (!scan.ok)
            {
                std::cout << "MS365 ARCHIVE ALL failed: " << scan.error_message << "\n";
                return;
            }

            if (scan.files.empty())
            {
                std::cout << "No inbound files.\n";
                return;
            }

            std::cout << "Archiving " << scan.files.size() << " inbound file(s)...\n";
            for (const auto& f : scan.files)
                do_archive_one(f);

            return;
        }

        dottalk::m365::FileDescriptor f;
        std::string err;

        if (!find_inbound_file_by_name(arg, f, err))
        {
            if (classify_arbitrary_file(arg, f))
            {
                do_archive_one(f);
                return;
            }

            std::cout << "MS365 ARCHIVE failed: " << err << "\n";
            return;
        }

        do_archive_one(f);
    }
}

void cmd_MS365(xbase::DbArea&, std::istringstream& iss)
{
    std::string sub;
    iss >> sub;

    if (sub.empty())
    {
        print_usage();
        return;
    }

    sub = upper(sub);

    if (sub == "STATUS")
    {
        do_status();
        return;
    }

    if (sub == "SCAN")
    {
        do_scan();
        return;
    }

    if (sub == "LIST")
    {
        std::string which;
        iss >> which;
        do_list(which);
        return;
    }

    if (sub == "EXPORT")
    {
        std::string kind;
        iss >> kind;
        kind = upper(kind);

        if (kind == "TABLE")
        {
            std::string table;
            iss >> table;
            do_export_table(table);
            return;
        }

        if (kind == "RECORD")
        {
            std::string table;
            std::string recno;
            iss >> table >> recno;
            do_export_record(table, recno);
            return;
        }

        if (kind == "NOTES")
        {
            std::string topic = remainder_trimmed(iss);
            do_export_notes(topic);
            return;
        }

        std::cout << "Usage: MS365 EXPORT TABLE|RECORD|NOTES ...\n";
        return;
    }

    if (sub == "IMPORT")
    {
        std::string arg = remainder_trimmed(iss);
        do_import(arg);
        return;
    }

    if (sub == "ARCHIVE")
    {
        std::string arg = remainder_trimmed(iss);
        do_archive(arg);
        return;
    }

    print_usage();
}