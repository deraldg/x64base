// cmd_showini.cpp
// DotTalk++ SHOWINI command
// Displays table.ini contents

// @dottalk.usage v1
// owner: DOT|SHOWINI
// command: SHOWINI
// category: diagnostics
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: SHOWINI USAGE
// summary:
//   Display a table-specific .ini file, either derived from the current table or
//   from an explicit file/path.
//
// usage:
//   SHOWINI
//   SHOWINI USAGE
//   SHOWINI <table-or-ini>
//   SHOWINI PATH <ini-file>
//
// examples:
//   SHOWINI
//   SHOWINI students
//   SHOWINI students.ini
//   SHOWINI PATH d:\data\students.ini
//
// notes:
//   SHOWINI with no arguments derives the .ini path from the current table.
//   SHOWINI USAGE prints usage before open-table checks or file reads.
//   SHOWINI reads .ini files and prints parsed sections/keys; it does not write files.
//
// risk:
//   reads_filesystem: yes except usage
//   writes_filesystem: no
//   mutates_table_data: no
//
// related:
//   SHOWINI
//   SETPATH
//   STATUS
//

#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <filesystem>
#include <algorithm>
#include <iomanip>
#include <cctype>

#include "xbase.hpp"
#include "textio.hpp"
#include "cli/command_registry.hpp"

using namespace std;
namespace fs = std::filesystem;

extern "C" xbase::XBaseEngine* shell_engine();

struct IniEntry
{
    string key;
    string value;
};

struct IniSection
{
    string name;
    vector<IniEntry> entries;
};

static string trim(const string& s)
{
    return textio::trim(s);
}

static bool load_ini(const fs::path& path,
                     vector<IniSection>& sections,
                     string& error)
{
    sections.clear();
    error.clear();

    ifstream in(path.string());
    if (!in)
    {
        error = "cannot open file";
        return false;
    }

    string line;
    string current;

    while (getline(in, line))
    {
        if (!line.empty() && line.back() == '\r')
            line.pop_back();

        string t = trim(line);

        if (t.empty()) continue;
        if (t[0] == ';' || t[0] == '#') continue;

        if (t.front() == '[')
        {
            if (t.back() != ']')
            {
                error = "malformed section";
                return false;
            }

            current = trim(t.substr(1, t.size()-2));
            sections.push_back({current,{}});
            continue;
        }

        auto pos = t.find('=');
        if (pos == string::npos)
            continue;

        string key = trim(t.substr(0,pos));
        string val = trim(t.substr(pos+1));

        if (sections.empty())
            sections.push_back({"global",{}});

        sections.back().entries.push_back({key,val});
    }

    return true;
}

static void print_ini(const fs::path& path,
                      const vector<IniSection>& sections)
{
    cout << "INI SETTINGS REPORT\n";
    cout << "File: " << path.string() << "\n\n";

    for (const auto& sec : sections)
    {
        cout << "[" << sec.name << "]\n";
        cout << "----------------------------------------\n";

        for (const auto& e : sec.entries)
        {
            cout << left << setw(24) << e.key
                 << " = " << e.value << "\n";
        }

        cout << "\n";
    }
}

static fs::path derive_ini_from_dbf(const fs::path& dbf)
{
    fs::path p = dbf;
    p.replace_extension(".ini");
    return p;
}

static std::string showini_usage_upper_hotfix(std::string s)
{
    for (char& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

static bool showini_usage_request_hotfix(std::istringstream& iss)
{
    std::string tok;
    if (!(iss >> tok)) {
        iss.clear();
        iss.seekg(0, std::ios::beg);
        return false;
    }

    const std::string u = showini_usage_upper_hotfix(tok);
    iss.clear();
    iss.seekg(0, std::ios::beg);

    return u == "USAGE" || u == "HELP" || u == "?";
}

static void print_showini_usage_hotfix()
{
    std::cout
        << "Usage:\n"
        << "  SHOWINI\n"
        << "  SHOWINI USAGE\n"
        << "  SHOWINI <table-or-ini>\n"
        << "  SHOWINI PATH <ini-file>\n"
        << "Examples:\n"
        << "  SHOWINI\n"
        << "  SHOWINI students\n"
        << "  SHOWINI students.ini\n"
        << "  SHOWINI PATH d:\\data\\students.ini\n";
}
void cmd_SHOWINI(xbase::DbArea& area, std::istringstream& iss)
{
    if (showini_usage_request_hotfix(iss)) {
        print_showini_usage_hotfix();
        return;
    }
    string arg;
    iss >> arg;

    fs::path iniPath;

    if (arg.empty())
    {
        string fn = area.filename();
        if (fn.empty())
        {
            cout << "SHOWINI: no table open.\n";
            return;
        }

        iniPath = derive_ini_from_dbf(fn);
    }
    else
    {
        string up = arg;
        transform(up.begin(), up.end(), up.begin(), ::toupper);

        if (up == "PATH")
        {
            iss >> arg;
            if (arg.empty())
            {
                cout << "SHOWINI: PATH requires filename.\n";
                return;
            }

            iniPath = arg;
        }
        else
        {
            fs::path p = arg;

            if (p.extension() == ".ini")
                iniPath = p;
            else
                iniPath = derive_ini_from_dbf(p);
        }
    }

    if (!fs::exists(iniPath))
    {
        cout << "SHOWINI: ini file not found: "
             << iniPath.string() << "\n";
        return;
    }

    vector<IniSection> sections;
    string error;

    if (!load_ini(iniPath, sections, error))
    {
        cout << "SHOWINI: load failed: " << error << "\n";
        return;
    }

    print_ini(iniPath, sections);
}