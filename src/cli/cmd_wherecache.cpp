// ===============================================
// src/cli/cmd_wherecache.cpp
// Developer command: WHERECACHE STATS | CLEAR | CAP <n>
// ===============================================
// @dottalk.usage v1
// owner: DOT|WHERECACHE
// command: WHERECACHE
// category: diagnostics
// status: supported
// noargs: report
// effect: mixed
// mutates: where-cache
// usage-access: WHERECACHE USAGE
// summary:
//   Inspect or tune the shared WHERE expression evaluation cache.
//
// usage:
//   WHERECACHE
//   WHERECACHE USAGE
//   WHERECACHE STATS
//   WHERECACHE CLEAR
//   WHERECACHE CAP <n>
//
// examples:
//   WHERECACHE
//   WHERECACHE STATS
//   WHERECACHE CAP 256
//   WHERECACHE CLEAR
//
// notes:
//   WHERECACHE with no arguments reports cache stats and usage.
//   WHERECACHE USAGE prints usage and does not clear or resize the cache.
//   CLEAR empties the cache; CAP changes the cache capacity.
//   WHERECACHE does not mutate table data.
//
// risk:
//   mutates_where_cache: CLEAR, CAP
//   mutates_table_data: no
//
// related:
//   WHERE
//   SET FILTER
//

#include <string>
#include <sstream>
#include <iostream>
#include <cctype>

#include "cli/where_eval_shared.hpp"


static void print_wherecache_usage()
{
    std::cout
        << "Usage:\n"
        << "  WHERECACHE\n"
        << "  WHERECACHE USAGE\n"
        << "  WHERECACHE STATS\n"
        << "  WHERECACHE CLEAR\n"
        << "  WHERECACHE CAP <n>\n"
        << "Examples:\n"
        << "  WHERECACHE STATS\n"
        << "  WHERECACHE CAP 256\n"
        << "  WHERECACHE CLEAR\n"
        << "Notes:\n"
        << "  - CLEAR empties the WHERE expression cache.\n"
        << "  - CAP changes the cache capacity.\n";
}

static inline std::string up(std::string s){
    for(char& c: s) c = (char)std::toupper((unsigned char)c);
    return s;
}

void cmd_WHERECACHE(std::istringstream& args)
{
    std::string tok;
    if (!(args >> tok)) {
        auto st = where_eval::cache_stats();
        std::cout << "; WHERECACHE ? size=" << st.size << " capacity=" << st.capacity << "\n";
        print_wherecache_usage();
        return;
    }
    std::string T = up(tok);
    if (T == "USAGE" || T == "HELP" || T == "?") {
        print_wherecache_usage();
        return;
    }

    if (T == "STATS") {
        auto st = where_eval::cache_stats();
        std::cout << "; WHERECACHE ? size=" << st.size << " capacity=" << st.capacity << "\n";
    } else if (T == "CLEAR") {
        where_eval::cache_clear();
        auto st = where_eval::cache_stats();
        std::cout << "; WHERECACHE ? cleared (size=" << st.size << ")\n";
    } else if (T == "CAP") {
        size_t n = 0;
        if (!(args >> n)) {
            std::cout << "; WHERECACHE ? CAP requires a positive integer\n";
            return;
        }
        where_eval::cache_set_capacity(n);
        auto st = where_eval::cache_stats();
        std::cout << "; WHERECACHE ? capacity set to " << st.capacity << "\n";
    } else {
        std::cout << "; WHERECACHE ? unknown action '" << tok << "'\n";
        print_wherecache_usage();
    }
}



