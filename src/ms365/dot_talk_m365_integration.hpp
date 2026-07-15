#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace dottalk::m365
{
    struct Timestamp
    {
        std::string iso_8601;
    };

    enum class FileKind
    {
        Unknown = 0,
        TableCSV,
        RecordJSON,
        NotesTXT
    };

    enum class Direction
    {
        Outbound = 0,
        Inbound
    };

    struct FileDescriptor
    {
        std::string full_path;
        std::string file_name;
        FileKind    kind = FileKind::Unknown;
        Direction   direction = Direction::Outbound;
        Timestamp   created;
    };

    struct InboundScanResult
    {
        bool ok = false;
        std::string error_message;
        std::vector<FileDescriptor> files;
    };

    namespace Paths
    {
        inline constexpr const char* Root     = "DotTalk_Exchange";
        inline constexpr const char* Outbound = "DotTalk_Exchange/outbound";
        inline constexpr const char* Inbound  = "DotTalk_Exchange/inbound";
        inline constexpr const char* Archive  = "DotTalk_Exchange/archive";
    }

    namespace Naming
    {
        inline constexpr const char* TablePrefixOutbound  = "table_";
        inline constexpr const char* TablePrefixInbound   = "import_table_";

        inline constexpr const char* RecordPrefixOutbound = "record_";
        inline constexpr const char* RecordPrefixInbound  = "import_record_";

        inline constexpr const char* NotesPrefixOutbound  = "notes_";
        inline constexpr const char* NotesPrefixInbound   = "import_notes_";

        inline constexpr const char* ExtCSV  = ".csv";
        inline constexpr const char* ExtJSON = ".json";
        inline constexpr const char* ExtTXT  = ".txt";
    }

    // Time/status helpers
    Timestamp make_current_timestamp_utc();

    bool is_onedrive_available();
    std::string get_onedrive_root();
    std::string get_exchange_root();
    std::string get_inbound_folder();
    std::string get_outbound_folder();
    std::string get_archive_folder();

    // General helpers
    std::string build_path(const std::string& subfolder, const std::string& file_name);
    FileDescriptor classify_file(const std::string& full_path, const std::string& file_name);

    // Export
    bool export_table_to_csv(
        const std::string& table_name,
        const Timestamp&   ts,
        std::string&       out_full_path);

    bool export_record_to_json(
        const std::string& table_name,
        std::int64_t       record_id,
        const Timestamp&   ts,
        std::string&       out_full_path);

    bool export_notes_to_txt(
        const std::string& topic,
        const Timestamp&   ts,
        std::string&       out_full_path);

    // Scan/import
    InboundScanResult scan_inbound_folder();

    bool import_table_from_csv(
        const FileDescriptor& file,
        std::string&          out_table_name);

    bool import_record_from_json(
        const FileDescriptor& file,
        std::string&          out_table_name,
        std::int64_t&         out_record_id);

    bool import_notes_from_txt(
        const FileDescriptor& file,
        std::string&          out_topic);

    // Archive
    bool archive_file(
        const FileDescriptor& file,
        std::string&          out_archived_path);
}