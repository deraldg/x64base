// @dottalk.usage v1
// owner: DOT|ZIP
// command: ZIP
// category: archive
// status: supported
// noargs: usage
// effect: archive-file-operation
// mutates: filesystem
// usage-access: ZIP USAGE
// summary:
//   List, create, or extract ZIP archives through the configured ZIP backend.
//
// usage:
//   ZIP USAGE
//   ZIP LIST <archive.zip>
//   ZIP CREATE <archive.zip> <path>
//   ZIP EXTRACT <archive.zip> [target_dir]
//
// examples:
//   ZIP LIST backups.zip
//   ZIP CREATE source_bundle.zip src
//   ZIP EXTRACT source_bundle.zip tmp\source_bundle
//
// notes:
//   ZIP USAGE prints usage and does not touch archive files.
//   ZIP LIST reads an archive and prints entries.
//   ZIP CREATE writes an archive, adding .zip when needed.
//   ZIP EXTRACT writes files under the target directory or current directory.
//
// risk:
//   reads_filesystem: ZIP LIST, ZIP CREATE source
//   writes_filesystem: ZIP CREATE, ZIP EXTRACT
//   overwrites_files: backend-dependent on ZIP CREATE/EXTRACT
//   mutates_table_data: no
//
// related:
//   COPY
//   EXPORT
//
#include "cli/zip_service.hpp"
#include "xbase.hpp"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace {

using namespace dottalk::zip;

static std::string trim_copy(std::string s)
{
    auto is_space = [](unsigned char c){ return std::isspace(c) != 0; };

    s.erase(s.begin(), std::find_if(s.begin(), s.end(),
        [&](unsigned char c){ return !is_space(c); }));

    s.erase(std::find_if(s.rbegin(), s.rend(),
        [&](unsigned char c){ return !is_space(c); }).base(), s.end());

    return s;
}

static std::string upper_copy(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}

static std::vector<std::string> split_tokens(const std::string& s)
{
    std::istringstream iss(s);
    std::vector<std::string> out;
    std::string tok;

    while (iss >> tok)
        out.push_back(tok);

    return out;
}

static void print_usage()
{
    std::cout
        << "Usage:\n"
        << "  ZIP USAGE\n"
        << "  ZIP LIST <archive.zip>\n"
        << "  ZIP CREATE <archive.zip> <path>\n"
        << "  ZIP EXTRACT <archive.zip> [target_dir]\n"
        << "Examples:\n"
        << "  ZIP LIST backups.zip\n"
        << "  ZIP CREATE source_bundle.zip src\n"
        << "  ZIP EXTRACT source_bundle.zip tmp\\source_bundle\n"
        << "Notes:\n"
        << "  - ZIP USAGE does not touch archive files.\n"
        << "  - ZIP LIST reads an archive and prints entries.\n"
        << "  - ZIP CREATE writes an archive and adds .zip when needed.\n"
        << "  - ZIP EXTRACT writes files under the target directory or current directory.\n";
}

static void do_list(const std::vector<std::string>& toks)
{
    if (toks.size() < 2) {
        print_usage();
        return;
    }

    fs::path archive = toks[1];

    Listing listing;
    Result r = list_archive(archive, &listing);

    if (!r.success) {
        std::cout << "ZIP LIST: failed\n";
        std::cout << "  archive: " << archive.string() << "\n";
        std::cout << "  backend: " << backend_name(r.backend) << "\n";
        if (!r.message.empty())
            std::cout << "  error  : " << r.message << "\n";
        return;
    }

    std::cout << "ZIP LIST: " << archive.string() << "\n";

    if (listing.entries.empty()) {
        std::cout << "  (empty)\n";
        return;
    }

    for (const auto& e : listing.entries) {
        std::cout << "  " << e << "\n";
    }
}

static void do_create(const std::vector<std::string>& toks)
{
    if (toks.size() < 3) {
        print_usage();
        return;
    }

    fs::path archive = toks[1];
    fs::path source  = toks[2];

    archive = ensure_zip_extension(archive);

    Result r = create_archive(archive, source);

    if (!r.success) {
        std::cout << "ZIP CREATE: failed\n";
        std::cout << "  archive: " << archive.string() << "\n";
        std::cout << "  source : " << source.string() << "\n";
        std::cout << "  backend: " << backend_name(r.backend) << "\n";
        if (!r.message.empty())
            std::cout << "  error  : " << r.message << "\n";
        return;
    }

    std::cout << "ZIP CREATE: created archive.\n";
    std::cout << "  archive: " << archive.string() << "\n";
    std::cout << "  source : " << source.string() << "\n";
}

static void do_extract(const std::vector<std::string>& toks)
{
    if (toks.size() < 2) {
        print_usage();
        return;
    }

    fs::path archive = toks[1];
    fs::path target;

    if (toks.size() >= 3)
        target = toks[2];
    else
        target = fs::current_path();

    Result r = extract_archive(archive, target);

    if (!r.success) {
        std::cout << "ZIP EXTRACT: failed\n";
        std::cout << "  archive: " << archive.string() << "\n";
        std::cout << "  target : " << target.string() << "\n";
        std::cout << "  backend: " << backend_name(r.backend) << "\n";
        if (!r.message.empty())
            std::cout << "  error  : " << r.message << "\n";
        return;
    }

    std::cout << "ZIP EXTRACT: archive extracted.\n";
    std::cout << "  archive: " << archive.string() << "\n";
    std::cout << "  target : " << target.string() << "\n";
}

} // namespace

void cmd_ZIP(xbase::DbArea&, std::istringstream& iss)
{
    std::string rest;
    std::getline(iss, rest);
    rest = trim_copy(rest);

    const std::vector<std::string> toks = split_tokens(rest);

    if (toks.empty()) {
        print_usage();
        return;
    }

    const std::string cmd = upper_copy(toks[0]);
    if (cmd == "USAGE" || cmd == "HELP" || cmd == "?") {
        print_usage();
        return;
    }

    if (cmd == "LIST") {
        do_list(toks);
        return;
    }

    if (cmd == "CREATE") {
        do_create(toks);
        return;
    }

    if (cmd == "EXTRACT") {
        do_extract(toks);
        return;
    }

    print_usage();
}