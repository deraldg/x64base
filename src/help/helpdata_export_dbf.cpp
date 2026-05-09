// ============================================================================
// File: src/help/helpdata_export_dbf.cpp
// Purpose: Export HELP DATA v2 artifacts as both memo-backed artifacts and
//          browse-friendly fixed-width help_line rows.
// ============================================================================
#include "helpdata_export_dbf.hpp"

#include <algorithm>
#include <cstdint>
#include <cstring>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace dottalk::helpdata {
namespace {

#pragma pack(push,1)
struct DbfHeader {
    uint8_t  version { 0x03 };
    uint8_t  y { 0 };
    uint8_t  m { 0 };
    uint8_t  d { 0 };
    uint32_t nrecs { 0 };
    uint16_t header_len { 0 };
    uint16_t rec_len { 0 };
    uint8_t  reserved[20] {};
};

struct DbfField {
    char     name[11] {};
    char     type { 'C' };
    uint32_t data_addr { 0 };
    uint8_t  length { 0 };
    uint8_t  decimals { 0 };
    uint8_t  reserved[14] {};
};
#pragma pack(pop)

static void put_name(char dst[11], const std::string& name)
{
    std::memset(dst, 0, 11);
    std::strncpy(dst, name.c_str(), 10);
}

static DbfField field_c(const std::string& name, uint8_t len)
{
    DbfField field;
    put_name(field.name, name);
    field.type = 'C';
    field.length = len;
    return field;
}

static DbfField field_n(const std::string& name, uint8_t len)
{
    DbfField field;
    put_name(field.name, name);
    field.type = 'N';
    field.length = len;
    return field;
}

static DbfField field_m(const std::string& name)
{
    DbfField field;
    put_name(field.name, name);
    field.type = 'M';
    field.length = 10;
    return field;
}

static DbfField field_l(const std::string& name)
{
    DbfField field;
    put_name(field.name, name);
    field.type = 'L';
    field.length = 1;
    return field;
}

class DbtWriter {
public:
    explicit DbtWriter(const fs::path& path)
        : path_(path)
    {
        out_.open(path_, std::ios::binary | std::ios::trunc);
        if (!out_) {
            throw std::runtime_error("cannot open " + path_.string());
        }
        flush_header();
    }

    uint32_t append(const std::string& text)
    {
        if (text.empty()) {
            return 0;
        }

        const uint32_t start = next_block_;
        std::string payload;
        payload.resize(4);

        const uint32_t len = static_cast<uint32_t>(text.size());
        payload[0] = static_cast<char>((len >> 0) & 0xff);
        payload[1] = static_cast<char>((len >> 8) & 0xff);
        payload[2] = static_cast<char>((len >> 16) & 0xff);
        payload[3] = static_cast<char>((len >> 24) & 0xff);
        payload += text;
        payload.push_back(static_cast<char>(0x1a));

        const size_t blocks = (payload.size() + block_size_ - 1) / block_size_;
        payload.resize(blocks * block_size_, 0x00);

        out_.seekp(static_cast<std::streamoff>(start) * static_cast<std::streamoff>(block_size_), std::ios::beg);
        out_.write(payload.data(), static_cast<std::streamsize>(payload.size()));
        if (!out_) {
            throw std::runtime_error("write failed " + path_.string());
        }

        next_block_ += static_cast<uint32_t>(blocks);
        flush_header();
        return start;
    }

    void close()
    {
        if (out_.is_open()) {
            flush_header();
            out_.flush();
            out_.close();
        }
    }

    ~DbtWriter()
    {
        try {
            close();
        } catch (...) {
        }
    }

private:
    void flush_header()
    {
        std::string header(block_size_, 0x00);
        header[0] = static_cast<char>((next_block_ >> 0) & 0xff);
        header[1] = static_cast<char>((next_block_ >> 8) & 0xff);
        header[2] = static_cast<char>((next_block_ >> 16) & 0xff);
        header[3] = static_cast<char>((next_block_ >> 24) & 0xff);
        out_.seekp(0, std::ios::beg);
        out_.write(header.data(), static_cast<std::streamsize>(header.size()));
        if (!out_) {
            throw std::runtime_error("write failed " + path_.string());
        }
    }

    fs::path path_;
    std::ofstream out_;
    const uint32_t block_size_ { 512 };
    uint32_t next_block_ { 1 };
};

static void write_fixed(std::ofstream& out, std::string value, uint8_t len)
{
    if (value.size() < len) {
        value.append(len - value.size(), ' ');
    } else if (value.size() > len) {
        value.resize(len);
    }
    out.write(value.data(), len);
}

static void write_number(std::ofstream& out, std::string value, uint8_t len)
{
    if (value.size() < len) {
        value.insert(value.begin(), len - value.size(), ' ');
    } else if (value.size() > len) {
        value = value.substr(value.size() - len);
    }
    out.write(value.data(), len);
}

static void write_logical(std::ofstream& out, bool value)
{
    const char ch = value ? 'T' : 'F';
    out.write(&ch, 1);
}

static void write_memo_ptr(std::ofstream& out, uint32_t block)
{
    std::string ptr = std::to_string(block);
    if (ptr.size() < 10) {
        ptr.append(10 - ptr.size(), ' ');
    } else if (ptr.size() > 10) {
        ptr.resize(10);
    }
    out.write(ptr.data(), 10);
}

static void set_today(DbfHeader& header)
{
    std::time_t now = std::time(nullptr);
    std::tm tm_buf {};
#if defined(_WIN32)
    localtime_s(&tm_buf, &now);
#else
    localtime_r(&now, &tm_buf);
#endif
    header.y = static_cast<uint8_t>((tm_buf.tm_year + 1900) % 100);
    header.m = static_cast<uint8_t>(tm_buf.tm_mon + 1);
    header.d = static_cast<uint8_t>(tm_buf.tm_mday);
}

static uint16_t record_length_for(const std::vector<DbfField>& fields)
{
    uint16_t rec_len = 1; // deletion flag
    for (const auto& field : fields) {
        rec_len = static_cast<uint16_t>(rec_len + field.length);
    }
    return rec_len;
}

static DbfHeader make_header(size_t record_count, const std::vector<DbfField>& fields)
{
    DbfHeader header;
    set_today(header);
    header.nrecs = static_cast<uint32_t>(record_count);
    header.header_len = static_cast<uint16_t>(sizeof(DbfHeader) + fields.size() * sizeof(DbfField) + 1);
    header.rec_len = record_length_for(fields);
    return header;
}

static void write_dbf_header(std::ofstream& out, const DbfHeader& header, const std::vector<DbfField>& fields)
{
    out.write(reinterpret_cast<const char*>(&header), sizeof(header));
    for (const auto& field : fields) {
        out.write(reinterpret_cast<const char*>(&field), sizeof(field));
    }
    const char terminator = 0x0d;
    out.write(&terminator, 1);
}


struct HelpTopicRow {
    int topic_id { 0 };
    std::string topickey;
    std::string catalog;
    std::string topic;
    std::string topic_type;
    std::string status;
    bool implemented { false };
    bool supported { false };
    std::string primary_source;
    std::string confid;
    std::string title;
    std::string summary;
    int sections { 0 };
    int lines { 0 };
};

struct HelpSectionRow {
    int sect_id { 0 };
    int art_id { 0 };
    int topic_id { 0 };
    std::string topickey;
    std::string kind;
    std::string source;
    std::string confid;
    std::string severity;
    std::string name;
    int ordinal { 0 };
    int nlines { 0 };
};

static std::string topic_key_for(const Artifact& artifact)
{
    if (!artifact.cmdkey.empty()) {
        return artifact.cmdkey;
    }
    if (!artifact.catalog.empty() && !artifact.command.empty()) {
        return artifact.catalog + "|" + artifact.command;
    }
    if (!artifact.command.empty()) {
        return artifact.command;
    }
    return owner_to_string(artifact.owner);
}

static std::string topic_type_for(const Artifact& artifact)
{
    if (artifact.catalog == "FOX" || artifact.catalog == "DOT") {
        return "COMMAND";
    }
    if (artifact.catalog == "ED") {
        return "EDUCATION";
    }
    if (artifact.catalog == "FUNC" || artifact.catalog == "FUNCTION") {
        return "FUNCTION";
    }
    return "TOPIC";
}

static bool contains_token(const std::string& text, const std::string& token)
{
    return text.find(token) != std::string::npos;
}

static int logical_line_count(const std::string& payload)
{
    if (payload.empty()) {
        return 0;
    }

    int count = 1;
    for (char ch : payload) {
        if (ch == '\n') {
            ++count;
        }
    }
    return count;
}

static std::vector<HelpTopicRow> make_help_topic_rows(const std::vector<Artifact>& artifacts)
{
    std::vector<HelpTopicRow> rows;
    std::map<std::string, int> index_by_key;

    int next_topic_id = 1;
    for (const auto& artifact : artifacts) {
        const std::string key = topic_key_for(artifact);
        if (key.empty()) {
            continue;
        }

        auto it = index_by_key.find(key);
        if (it == index_by_key.end()) {
            HelpTopicRow row;
            row.topic_id = next_topic_id++;
            row.topickey = key;
            row.catalog = artifact.catalog;
            row.topic = artifact.command;
            row.topic_type = topic_type_for(artifact);
            row.status = "pending";
            row.primary_source = to_string(artifact.source);
            row.confid = to_string(artifact.confidence);
            row.title = !artifact.command.empty() ? artifact.command : key;
            rows.push_back(std::move(row));
            index_by_key[key] = static_cast<int>(rows.size()) - 1;
            it = index_by_key.find(key);
        }

        HelpTopicRow& row = rows[static_cast<size_t>(it->second)];
        ++row.sections;
        row.lines += logical_line_count(artifact.text);
        row.lines += logical_line_count(artifact.detail);
        row.lines += logical_line_count(artifact.evidence);

        if (artifact.kind == ArtifactKind::Status) {
            if (contains_token(artifact.text, "implemented=yes")) {
                row.implemented = true;
            }
            if (contains_token(artifact.text, "supported=yes")) {
                row.supported = true;
                row.status = "supported";
            } else if (contains_token(artifact.text, "supported=no") && row.status == "pending") {
                row.status = "partial";
            }
        }

        if (artifact.kind == ArtifactKind::Summary && row.summary.empty()) {
            row.summary = artifact.text;
            row.primary_source = to_string(artifact.source);
            row.confid = to_string(artifact.confidence);
        } else if ((artifact.kind == ArtifactKind::Usage || artifact.kind == ArtifactKind::Syntax) && row.summary.empty()) {
            row.summary = artifact.text;
            row.primary_source = to_string(artifact.source);
            row.confid = to_string(artifact.confidence);
        }
    }

    return rows;
}

static std::map<std::string, int> make_topic_id_by_key(const std::vector<HelpTopicRow>& topics)
{
    std::map<std::string, int> result;
    for (const auto& topic : topics) {
        result[topic.topickey] = topic.topic_id;
    }
    return result;
}

static std::vector<HelpSectionRow> make_help_section_rows(const std::vector<Artifact>& artifacts,
                                                          const std::map<std::string, int>& topic_id_by_key)
{
    std::vector<HelpSectionRow> rows;
    rows.reserve(artifacts.size());

    int fallback_art_id = 1;
    int next_sect_id = 1;
    for (const auto& artifact : artifacts) {
        const int art_id = artifact.id > 0 ? artifact.id : fallback_art_id;
        const std::string key = topic_key_for(artifact);

        HelpSectionRow row;
        row.sect_id = next_sect_id++;
        row.art_id = art_id;
        row.topickey = key;
        const auto topic_it = topic_id_by_key.find(key);
        row.topic_id = topic_it != topic_id_by_key.end() ? topic_it->second : 0;
        row.kind = to_string(artifact.kind);
        row.source = to_string(artifact.source);
        row.confid = to_string(artifact.confidence);
        row.severity = to_string(artifact.severity);
        row.name = artifact.name;
        row.ordinal = artifact.ordinal;
        row.nlines = logical_line_count(artifact.text)
                   + logical_line_count(artifact.detail)
                   + logical_line_count(artifact.evidence);
        rows.push_back(std::move(row));
        ++fallback_art_id;
    }

    return rows;
}

static int write_help_topic_dbf(const std::string& out_dir, const std::vector<HelpTopicRow>& rows)
{
    const fs::path dbf_path = fs::path(out_dir) / "help_topic.dbf";

    std::vector<DbfField> fields = {
        field_n("TOPICID",    10),
        field_c("TOPICKEY",   48),
        field_c("CATALOG",     8),
        field_c("TOPIC",      40),
        field_c("TOPICTYPE",  12),
        field_c("STATUS",     16),
        field_l("IMPLEMENT"),
        field_l("SUPPORTED"),
        field_c("PRIMARY",    16),
        field_c("CONFID",     16),
        field_c("TITLE",      80),
        field_c("SUMMARY",   200),
        field_n("SECTIONS",    6),
        field_n("LINES",       8)
    };

    const DbfHeader header = make_header(rows.size(), fields);
    std::ofstream out(dbf_path, std::ios::binary | std::ios::trunc);
    if (!out) {
        throw std::runtime_error("cannot open " + dbf_path.string());
    }

    write_dbf_header(out, header, fields);
    for (const auto& row : rows) {
        const char not_deleted = ' ';
        out.write(&not_deleted, 1);
        write_number(out, std::to_string(row.topic_id), 10);
        write_fixed(out, row.topickey, 48);
        write_fixed(out, row.catalog, 8);
        write_fixed(out, row.topic, 40);
        write_fixed(out, row.topic_type, 12);
        write_fixed(out, row.status, 16);
        write_logical(out, row.implemented);
        write_logical(out, row.supported);
        write_fixed(out, row.primary_source, 16);
        write_fixed(out, row.confid, 16);
        write_fixed(out, row.title, 80);
        write_fixed(out, row.summary, 200);
        write_number(out, std::to_string(row.sections), 6);
        write_number(out, std::to_string(row.lines), 8);
    }

    const char eof = 0x1a;
    out.write(&eof, 1);
    out.flush();
    if (!out) {
        throw std::runtime_error("write failed " + dbf_path.string());
    }
    return static_cast<int>(rows.size());
}

static int write_help_section_dbf(const std::string& out_dir, const std::vector<HelpSectionRow>& rows)
{
    const fs::path dbf_path = fs::path(out_dir) / "help_section.dbf";

    std::vector<DbfField> fields = {
        field_n("SECTID",   10),
        field_n("ARTID",    10),
        field_n("TOPICID",  10),
        field_c("TOPICKEY", 48),
        field_c("KIND",     16),
        field_c("SOURCE",   16),
        field_c("CONFID",   16),
        field_c("SEVERITY",  8),
        field_c("NAME",     40),
        field_n("ORD",       6),
        field_n("NLINES",    6)
    };

    const DbfHeader header = make_header(rows.size(), fields);
    std::ofstream out(dbf_path, std::ios::binary | std::ios::trunc);
    if (!out) {
        throw std::runtime_error("cannot open " + dbf_path.string());
    }

    write_dbf_header(out, header, fields);
    for (const auto& row : rows) {
        const char not_deleted = ' ';
        out.write(&not_deleted, 1);
        write_number(out, std::to_string(row.sect_id), 10);
        write_number(out, std::to_string(row.art_id), 10);
        write_number(out, std::to_string(row.topic_id), 10);
        write_fixed(out, row.topickey, 48);
        write_fixed(out, row.kind, 16);
        write_fixed(out, row.source, 16);
        write_fixed(out, row.confid, 16);
        write_fixed(out, row.severity, 8);
        write_fixed(out, row.name, 40);
        write_number(out, std::to_string(row.ordinal), 6);
        write_number(out, std::to_string(row.nlines), 6);
    }

    const char eof = 0x1a;
    out.write(&eof, 1);
    out.flush();
    if (!out) {
        throw std::runtime_error("write failed " + dbf_path.string());
    }
    return static_cast<int>(rows.size());
}

struct HelpLineRow {
    int line_id { 0 };
    int art_id { 0 };
    std::string topickey;
    std::string catalog;
    std::string topic;
    std::string kind;
    std::string source;
    std::string confid;
    std::string severity;
    std::string name;
    std::string role;
    int line_no { 0 };
    int part_no { 0 };
    std::string text;
};

static std::vector<std::string> split_logical_lines(const std::string& text)
{
    std::vector<std::string> lines;
    std::string current;

    for (char ch : text) {
        if (ch == '\r') {
            continue;
        }
        if (ch == '\n') {
            lines.push_back(current);
            current.clear();
            continue;
        }
        current.push_back(ch);
    }

    if (!current.empty() || (!text.empty() && text.back() == '\n')) {
        lines.push_back(current);
    }

    return lines;
}

static std::vector<std::string> split_parts(const std::string& line, size_t max_len)
{
    std::vector<std::string> parts;
    if (max_len == 0) {
        parts.push_back(line);
        return parts;
    }

    if (line.empty()) {
        parts.push_back({});
        return parts;
    }

    for (size_t pos = 0; pos < line.size(); pos += max_len) {
        parts.push_back(line.substr(pos, std::min(max_len, line.size() - pos)));
    }
    return parts;
}

static void append_line_rows_for_role(const Artifact& artifact,
                                      int art_id,
                                      const std::string& role,
                                      const std::string& payload,
                                      std::vector<HelpLineRow>& rows,
                                      int& next_line_id)
{
    if (payload.empty()) {
        return;
    }

    const std::vector<std::string> logical_lines = split_logical_lines(payload);
    int line_no = 1;

    for (const auto& logical_line : logical_lines) {
        const std::vector<std::string> parts = split_parts(logical_line, 240);
        int part_no = 1;
        for (const auto& part : parts) {
            HelpLineRow row;
            row.line_id = next_line_id++;
            row.art_id = art_id;
            row.topickey = artifact.cmdkey;
            row.catalog = artifact.catalog;
            row.topic = artifact.command;
            row.kind = to_string(artifact.kind);
            row.source = to_string(artifact.source);
            row.confid = to_string(artifact.confidence);
            row.severity = to_string(artifact.severity);
            row.name = artifact.name;
            row.role = role;
            row.line_no = line_no;
            row.part_no = part_no;
            row.text = part;
            rows.push_back(std::move(row));
            ++part_no;
        }
        ++line_no;
    }
}

static std::vector<HelpLineRow> make_help_line_rows(const std::vector<Artifact>& artifacts)
{
    std::vector<HelpLineRow> rows;
    rows.reserve(artifacts.size() * 2);

    int next_line_id = 1;
    int fallback_art_id = 1;
    for (const auto& artifact : artifacts) {
        const int art_id = artifact.id > 0 ? artifact.id : fallback_art_id;
        append_line_rows_for_role(artifact, art_id, "TEXT", artifact.text, rows, next_line_id);
        append_line_rows_for_role(artifact, art_id, "DETAIL", artifact.detail, rows, next_line_id);
        append_line_rows_for_role(artifact, art_id, "EVIDENCE", artifact.evidence, rows, next_line_id);
        ++fallback_art_id;
    }

    return rows;
}

static int write_help_line_dbf(const std::string& out_dir, const std::vector<Artifact>& artifacts)
{
    const fs::path dbf_path = fs::path(out_dir) / "help_line.dbf";
    const std::vector<HelpLineRow> rows = make_help_line_rows(artifacts);

    std::vector<DbfField> fields = {
        field_n("LINEID",   10),
        field_n("ARTID",    10),
        field_c("TOPICKEY", 48),
        field_c("CATALOG",   8),
        field_c("TOPIC",    40),
        field_c("KIND",     16),
        field_c("SOURCE",   16),
        field_c("CONFID",   16),
        field_c("SEVERITY",  8),
        field_c("NAME",     40),
        field_c("ROLE",     12),
        field_n("LINE_NO",   6),
        field_n("PART_NO",   4),
        field_c("TEXT",    240)
    };

    const DbfHeader header = make_header(rows.size(), fields);
    std::ofstream out(dbf_path, std::ios::binary | std::ios::trunc);
    if (!out) {
        throw std::runtime_error("cannot open " + dbf_path.string());
    }

    write_dbf_header(out, header, fields);

    for (const auto& row : rows) {
        const char not_deleted = ' ';
        out.write(&not_deleted, 1);
        write_number(out, std::to_string(row.line_id), 10);
        write_number(out, std::to_string(row.art_id), 10);
        write_fixed(out, row.topickey, 48);
        write_fixed(out, row.catalog, 8);
        write_fixed(out, row.topic, 40);
        write_fixed(out, row.kind, 16);
        write_fixed(out, row.source, 16);
        write_fixed(out, row.confid, 16);
        write_fixed(out, row.severity, 8);
        write_fixed(out, row.name, 40);
        write_fixed(out, row.role, 12);
        write_number(out, std::to_string(row.line_no), 6);
        write_number(out, std::to_string(row.part_no), 4);
        write_fixed(out, row.text, 240);
    }

    const char eof = 0x1a;
    out.write(&eof, 1);
    out.flush();
    if (!out) {
        throw std::runtime_error("write failed " + dbf_path.string());
    }

    return static_cast<int>(rows.size());
}

static void write_help_artifacts_dbf(const std::string& out_dir,
                                     const std::vector<Artifact>& artifacts)
{
    const fs::path dbf_path = fs::path(out_dir) / "help_artifacts.dbf";
    const fs::path dbt_path = fs::path(out_dir) / "help_artifacts.dbt";

    std::vector<DbfField> fields = {
        field_n("ID",       10),
        field_c("CATALOG",   8),
        field_c("COMMAND",  24),
        field_c("CMDKEY",   40),
        field_c("OWNER",    40),
        field_c("KIND",     16),
        field_c("SOURCE",   16),
        field_c("CONFID",   16),
        field_c("SEVERITY",  8),
        field_c("NAME",     40),
        field_n("ORD",       6),
        field_m("TEXT"),
        field_m("DETAIL"),
        field_m("EVIDENCE")
    };

    const DbfHeader header = make_header(artifacts.size(), fields);
    DbtWriter dbt(dbt_path);
    std::ofstream out(dbf_path, std::ios::binary | std::ios::trunc);
    if (!out) {
        throw std::runtime_error("cannot open " + dbf_path.string());
    }

    write_dbf_header(out, header, fields);

    int next_id = 1;
    for (const auto& artifact : artifacts) {
        const char not_deleted = ' ';
        out.write(&not_deleted, 1);

        const int id = artifact.id > 0 ? artifact.id : next_id;
        write_number(out, std::to_string(id), 10);
        write_fixed(out, artifact.catalog, 8);
        write_fixed(out, artifact.command, 24);
        write_fixed(out, artifact.cmdkey, 40);
        write_fixed(out, owner_to_string(artifact.owner), 40);
        write_fixed(out, to_string(artifact.kind), 16);
        write_fixed(out, to_string(artifact.source), 16);
        write_fixed(out, to_string(artifact.confidence), 16);
        write_fixed(out, to_string(artifact.severity), 8);
        write_fixed(out, artifact.name, 40);
        write_number(out, std::to_string(artifact.ordinal), 6);
        write_memo_ptr(out, dbt.append(artifact.text));
        write_memo_ptr(out, dbt.append(artifact.detail));
        write_memo_ptr(out, dbt.append(artifact.evidence));

        ++next_id;
    }

    const char eof = 0x1a;
    out.write(&eof, 1);
    out.flush();
    dbt.close();

    if (!out) {
        throw std::runtime_error("write failed " + dbf_path.string());
    }
}

} // namespace

ExportCounts export_artifacts_dbf(const std::string& out_dir,
                                  const std::vector<Artifact>& artifacts)
{
    fs::create_directories(out_dir);

    const std::vector<HelpTopicRow> topics = make_help_topic_rows(artifacts);
    const std::map<std::string, int> topic_id_by_key = make_topic_id_by_key(topics);
    const std::vector<HelpSectionRow> sections = make_help_section_rows(artifacts, topic_id_by_key);

    write_help_artifacts_dbf(out_dir, artifacts);
    const int topics_written = write_help_topic_dbf(out_dir, topics);
    const int sections_written = write_help_section_dbf(out_dir, sections);
    const int lines = write_help_line_dbf(out_dir, artifacts);

    return { static_cast<int>(artifacts.size()), lines, topics_written, sections_written };
}

} // namespace dottalk::helpdata
