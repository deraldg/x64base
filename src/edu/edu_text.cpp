// ==============================
// File: src/cli/cmd_text.cpp
// TEXT command.
//
// Current scope:
// - TEXT                    -> open editor with empty buffer
// - TEXT <literal text>     -> open editor preloaded with literal text
// - TEXT FILE <path>        -> edit file contents in-place
// - TEXT MEMO <field>       -> validate memo target, leave stub for later wiring
//
// Notes:
// - FILE mode now reads the full remaining path, so paths with spaces work.
// - MEMO mode remains a deliberate integration stub until memo editor wiring
//   is finished.
// - Engine truth remains in xbase.hpp / DbArea; this command stays in CLI layer.
// ==============================

// @dottalk.usage v1
// owner: EDU|TEXT
// command: TEXT
// category: utility-editor
// status: supported
// noargs: launch-editor-empty-buffer
// effect: launch-editor
// mutates: filesystem-or-memo-stub depending-on-mode
// usage-access: TEXT USAGE
// summary:
//   Open the text editor with an empty buffer, literal text, a file, or a memo
//   field target stub.
//
// usage:
//   TEXT USAGE
//   TEXT
//   TEXT <literal text>
//   TEXT FILE <path>
//   TEXT MEMO <field>
//
// examples:
//   TEXT
//   TEXT hello world
//   TEXT FILE notes.txt
//   TEXT MEMO NOTES
//
// notes:
//   TEXT USAGE/HELP/? returns before entering editor mode.
//   TEXT with no arguments preserves the existing empty-buffer editor behavior.
//   TEXT MEMO remains an integration stub until memo editor wiring is complete.
//
// risk:
//   launches_editor: yes except usage
//   mutates_filesystem: TEXT FILE through editor
//   mutates_table_data: no direct mutation in current implementation
//

#include "cli/cmd_text.hpp"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

#include "cli/text_editor.hpp"
#include "xbase.hpp"

using text_editor::edit_text_via_editor;

namespace
{
    std::string to_upper_copy(std::string s)
    {
        std::transform(s.begin(), s.end(), s.begin(),
            [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
        return s;
    }

    std::string read_rest(std::istringstream& iss)
    {
        std::string rest;
        std::getline(iss >> std::ws, rest);

        while (!rest.empty() &&
               (rest.back() == '\r' || rest.back() == '\n' ||
                rest.back() == ' '  || rest.back() == '\t'))
        {
            rest.pop_back();
        }

        return rest;
    }

    int find_field_ci(const xbase::DbArea& area, const std::string& field_name)
    {
        const std::string needle = to_upper_copy(field_name);
        const auto& fields = area.fields();

        for (int i = 0; i < static_cast<int>(fields.size()); ++i)
        {
            if (to_upper_copy(fields[i].name) == needle)
                return i + 1; // 1-based
        }

        return -1;
    }

    void run_plain_text_mode(const std::string& initial_text)
    {
        std::string text = initial_text;
        std::string err;

        if (!edit_text_via_editor(text, &err))
        {
            std::cout << "TEXT: FAILED\n";
            if (!err.empty())
                std::cout << "  " << err << "\n";
            return;
        }

        std::cout << "\n";
        std::cout << "TEXT RESULT\n";
        std::cout << "-----------\n";
        std::cout << text << "\n";
    }

    void run_file_mode(const std::string& path)
    {
        if (path.empty())
        {
            std::cout << "TEXT FILE requires a path\n";
            return;
        }

        std::string text;

        {
            std::ifstream in(path, std::ios::in | std::ios::binary);
            if (in)
            {
                std::stringstream buffer;
                buffer << in.rdbuf();
                text = buffer.str();
            }
        }

        std::string err;
        if (!edit_text_via_editor(text, &err))
        {
            std::cout << "TEXT FILE: FAILED\n";
            if (!err.empty())
                std::cout << "  " << err << "\n";
            return;
        }

        {
            std::ofstream out(path, std::ios::out | std::ios::binary | std::ios::trunc);
            if (!out)
            {
                std::cout << "TEXT FILE: FAILED\n";
                std::cout << "  Unable to write file\n";
                return;
            }

            out << text;
        }

        std::cout << "\n";
        std::cout << "TEXT FILE: OK\n";
        std::cout << "  " << path << "\n";
    }

    void run_memo_mode(xbase::DbArea& area, const std::string& field_name)
    {
        if (field_name.empty())
        {
            std::cout << "TEXT MEMO requires a field name\n";
            return;
        }

        if (!area.isOpen())
        {
            std::cout << "TEXT MEMO requires an open table\n";
            return;
        }

        const int field1 = find_field_ci(area, field_name);
        if (field1 < 1)
        {
            std::cout << "TEXT MEMO: unknown field: " << field_name << "\n";
            return;
        }

        const auto& fd = area.fields()[field1 - 1];
        if (fd.type != 'M')
        {
            std::cout << "TEXT MEMO: field is not memo: " << field_name << "\n";
            return;
        }

        if (area.recno() == 0)
        {
            std::cout << "TEXT MEMO: no current record\n";
            return;
        }

        // ------------------------------------------------------------
        // MEMO STUB / INTEGRATION POINT
        //
        // When memo wiring is finished:
        //   1) load current memo text from area.get(field1)
        //   2) launch edit_text_via_editor(text, &err)
        //   3) write back through area.replaceFieldStored(field1, text, &err)
        //
        // That path preserves table buffering, locks, indexing, and events.
        // ------------------------------------------------------------
        std::cout << "TEXT MEMO: stub\n";
        std::cout << "  Field: " << field_name << "\n";
        std::cout << "  Memo editor integration pending\n";
    }

    void print_usage()
    {
        std::cout << "Usage:\n";
        std::cout << "  TEXT USAGE\n";
        std::cout << "  TEXT\n";
        std::cout << "  TEXT <literal text>\n";
        std::cout << "  TEXT FILE <path>\n";
        std::cout << "  TEXT MEMO <field>\n";
        std::cout << "Examples:\n";
        std::cout << "  TEXT\n";
        std::cout << "  TEXT hello world\n";
        std::cout << "  TEXT FILE notes.txt\n";
        std::cout << "  TEXT MEMO NOTES\n";
        std::cout << "Notes:\n";
        std::cout << "  - TEXT USAGE does not enter editor mode.\n";
    }
}

void cmd_TEXT(xbase::DbArea& area, std::istringstream& iss)
{
    std::string first;
    iss >> first;

    if (first.empty())
    {
        run_plain_text_mode("");
        return;
    }

    const std::string mode = to_upper_copy(first);

    if (mode == "FILE")
    {
        const std::string path = read_rest(iss);
        run_file_mode(path);
        return;
    }

    if (mode == "MEMO")
    {
        std::string field_name;
        iss >> field_name;
        run_memo_mode(area, field_name);
        return;
    }

    if (mode == "USAGE" || mode == "HELP" || mode == "?")
    {
        print_usage();
        return;
    }

    std::string text = first;
    const std::string rest = read_rest(iss);
    if (!rest.empty())
    {
        text += " ";
        text += rest;
    }

    run_plain_text_mode(text);
}