// src/cli/cmd_append.cpp — APPEND
//
// Supported forms:
//   APPEND
//   APPEND RAW
//   APPEND MANY <count>
//   APPEND RAW MANY <count>
//   APPEND <count>
//
// Behavior:
//   APPEND              -> smart append (keys + inline active index update)
//   APPEND RAW          -> raw one-record append (keys, no inline index update)
//   APPEND MANY <n>     -> smart batch append under one lock
//   APPEND RAW MANY <n> -> raw batch append under one lock
//   APPEND <n>          -> shorthand for APPEND MANY <n>

// @dottalk.usage v1
// owner: DOT|APPEND
// command: APPEND
// category: data
// status: supported
// noargs: mutate
// effect: mutate
// mutates: table-data index memo record-pointer
// usage-access: APPEND USAGE
// summary:
//   Append one or more blank records to the current table, using smart append
//   paths that maintain keys and active indexes, or raw append paths when requested.
//
// usage:
//   APPEND USAGE
//   APPEND
//   APPEND <count>
//   APPEND MANY <count>
//   APPEND RAW
//   APPEND RAW MANY <count>
//
// notes:
//   APPEND with no arguments appends one blank record through the shared smart append path.
//   APPEND <count> is shorthand for APPEND MANY <count>.
//   APPEND MANY <count> performs smart batch append under one lock.
//   APPEND RAW appends one record without inline index update.
//   APPEND RAW MANY <count> performs raw batch append under one lock.
//   Count values must be positive integers.
//   APPEND is a table-data mutation command; do not classify it as read-only.
//
// risk:
//   writes_dbf_records: yes
//   appends_records: yes
//   updates_indexes: smart append paths
//   raw_path_skips_inline_index_update: yes
//   one_lock_batch: MANY forms
//   requires_open_table: yes
//
// related:
//   APPEND_BLANK
//   REPLACE
//   MULTIREP
//   TABLE
//   COMMIT
//

#include <cctype>
#include <cstdint>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "cli/append_support.hpp"

namespace
{
    static std::string upcase_copy(std::string s)
    {
        for (char& ch : s)
            ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
        return s;
    }


    static bool is_append_usage_request(const std::string& raw)
    {
        std::string t = upcase_copy(raw);
        while (!t.empty() && std::isspace(static_cast<unsigned char>(t.front()))) t.erase(t.begin());
        while (!t.empty() && std::isspace(static_cast<unsigned char>(t.back()))) t.pop_back();

        if (t.rfind("APPEND ", 0) == 0) {
            t = t.substr(7);
            while (!t.empty() && std::isspace(static_cast<unsigned char>(t.front()))) t.erase(t.begin());
        }

        return t == "USAGE" || t == "HELP" || t == "?";
    }

    static void print_append_usage()
    {
        std::cout
            << "Usage:\n"
            << "  APPEND USAGE\n"
            << "  APPEND\n"
            << "  APPEND <count>\n"
            << "  APPEND MANY <count>\n"
            << "  APPEND RAW\n"
            << "  APPEND RAW MANY <count>\n"
            << "Notes:\n"
            << "  - APPEND with no arguments appends one blank record.\n"
            << "  - APPEND MANY uses the smart batch append path.\n"
            << "  - APPEND RAW uses the raw append path without inline index update.\n";
    }

    static bool parse_count_token(const std::string& s, std::size_t& out)
    {
        if (s.empty()) return false;

        for (unsigned char ch : s)
            if (!std::isdigit(ch)) return false;

        try
        {
            const unsigned long long v = std::stoull(s);
            if (v == 0) return false;
            if (v > static_cast<unsigned long long>(std::numeric_limits<std::size_t>::max()))
                return false;

            out = static_cast<std::size_t>(v);
            return true;
        }
        catch (...)
        {
            return false;
        }
    }
}

void cmd_APPEND(xbase::DbArea& A, std::istringstream& iss)
{
    const std::string raw_args = iss.str();
    if (is_append_usage_request(raw_args))
    {
        print_append_usage();
        return;
    }

    std::string tok1;
    if (!(iss >> tok1))
    {
        std::istringstream none;
        (void)dottalk_append_blank_core(A, none);
        return;
    }

    std::size_t count = 0;
    if (parse_count_token(tok1, count))
    {
        (void)dottalk_append_many_core(A, count);
        return;
    }

    const std::string u1 = upcase_copy(tok1);

    if (u1 == "RAW")
    {
        std::string tok2;
        if (!(iss >> tok2))
        {
            std::uint32_t rn = 0;
            (void)dottalk_append_blank_raw(A, rn);
            return;
        }

        const std::string u2 = upcase_copy(tok2);

        if (u2 == "MANY")
        {
            std::string tok3;
            if (!(iss >> tok3))
            {
                std::cout << "Usage: APPEND RAW MANY <count>\n";
                return;
            }

            if (!parse_count_token(tok3, count))
            {
                std::cout << "APPEND: invalid count '" << tok3 << "'\n";
                return;
            }

            (void)dottalk_append_many_raw(A, count);
            return;
        }

        std::cout << "Usage: APPEND RAW | APPEND RAW MANY <count>\n";
        return;
    }

    if (u1 == "MANY")
    {
        std::string tok2;
        if (!(iss >> tok2))
        {
            std::cout << "Usage: APPEND MANY <count>\n";
            return;
        }

        if (!parse_count_token(tok2, count))
        {
            std::cout << "APPEND: invalid count '" << tok2 << "'\n";
            return;
        }

        (void)dottalk_append_many_core(A, count);
        return;
    }

    print_append_usage();
}