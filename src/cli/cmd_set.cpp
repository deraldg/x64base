// src/cli/cmd_set.cpp
// FoxPro-style SET command router for DotTalk++

#include "xbase.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <iterator>
#include <sstream>
#include <string>

#include "cli/output_router.hpp"
#include "cli/settings.hpp"
#include "cli/table_state.hpp"

// ---- Forward declarations ---------------------------------------------------
void cmd_SETINDEX      (xbase::DbArea&, std::istringstream&);
void cmd_SETORDER      (xbase::DbArea&, std::istringstream&);
void cmd_SETFILTER     (xbase::DbArea&, std::istringstream&);
void cmd_SET_UNIQUE    (xbase::DbArea&, std::istringstream&);
void cmd_SET_RELATION  (xbase::DbArea&, std::istringstream&);
void cmd_SET_RELATIONS (xbase::DbArea&, std::istringstream&);
void cmd_SETCASE       (xbase::DbArea&, std::istringstream&);
void cmd_SETNEAR       (xbase::DbArea&, std::istringstream&);
void cmd_SETPATH       (xbase::DbArea&, std::istringstream&);
void cmd_SETTIMER      (xbase::DbArea&, std::istringstream&);
void cmd_PRN           (xbase::DbArea&, std::istringstream&);

#if DOTTALK_WITH_DEV
void cmd_SETCNX        (xbase::DbArea&, std::istringstream&);
void cmd_SETCDX        (xbase::DbArea&, std::istringstream&);
void cmd_SETLMDB       (xbase::DbArea&, std::istringstream&);
#endif

extern "C" xbase::XBaseEngine* shell_engine();

namespace {

static inline std::string up_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static inline std::string ltrim_copy(std::string s) {
    std::size_t i = 0;
    while (i < s.size() && std::isspace(static_cast<unsigned char>(s[i]))) ++i;
    return s.substr(i);
}

static inline std::string rest(std::istringstream& iss) {
    return std::string(std::istreambuf_iterator<char>(iss),
                       std::istreambuf_iterator<char>());
}

static inline bool parse_on_off(const std::string& tok, bool& out) {
    const std::string u = up_copy(tok);
    if (u == "ON")  { out = true;  return true; }
    if (u == "OFF") { out = false; return true; }
    return false;
}

static void print_set_usage() {
    auto& out = cli::OutputRouter::instance().out();

    out
        << "Usage: SET <option> [args]\n"
        << "Public options:\n"
        << "  SET TABLE BUFFER ON|OFF [ALL]\n"
        << "  SET CONSOLE ON|OFF\n"
        << "  SET PRINT ON|OFF\n"
        << "  SET PRINT TO <file>\n"
        << "  SET DEVICE TO SCREEN|FILE <path>|PRINTER [name]|NULL\n"
        << "  SET ALTERNATE ON|OFF\n"
        << "  SET ALTERNATE TO <file>\n"
        << "  SET TALK ON|OFF\n"
        << "  SET ECHO ON|OFF\n"
        << "  SET PAGING ON|OFF\n"
        << "  SET WRAP ON|OFF\n"
        << "  SET DELETED ON|OFF\n"
        << "  SET CASE ON|OFF\n"
        << "  SET NEAR ON|OFF\n"
        << "  SET EDITOR TO <value|DEFAULT|OFF>\n"
        << "  SET PATH <slot> <path>\n"
        << "  SET TIMER ON|OFF\n"
        << "  SET POLLING ON|OFF\n"
        << "  SET INDEX TO <file>\n"
        << "  SET ORDER TO <tag|0>\n";

#if DOTTALK_WITH_DEV
    out
        << "\n"
        << "Developer / transitional:\n"
        << "  SET FILTER TO <expr>\n"
        << "  SET RELATION <args...>\n"
        << "  SET RELATIONS <args...>\n"
        << "  SET CNX [TO] <container.cnx>\n"
        << "  SET CDX [TO] <container.cdx>\n"
        << "  SET LMDB <args...>\n";
#endif
}

} // namespace

void cmd_SET(xbase::DbArea& A, std::istringstream& args) {
    using cli::Settings;

    auto& S   = Settings::instance();
    auto& R   = cli::OutputRouter::instance();
    auto& out = R.out();

    std::string opt;
    if (!(args >> opt)) {
        print_set_usage();
        return;
    }
    opt = up_copy(opt);

    // ─────────────────────────────────────────────────────────────
    // SET TABLE BUFFER
    // ─────────────────────────────────────────────────────────────
    if (opt == "TABLE") {
        std::string sub;
        args >> sub;
        sub = up_copy(sub);

        if (sub == "BUFFER") {
            std::string tok;
            args >> tok;

            bool on = false;
            if (!parse_on_off(tok, on)) {
                out << "Usage: SET TABLE BUFFER ON|OFF [ALL]\n";
                return;
            }

            std::string scope;
            args >> scope;
            const bool all = (up_copy(scope) == "ALL");

            auto* eng = shell_engine();
            if (!eng) {
                out << "TABLE BUFFER: engine not available.\n";
                return;
            }

            int changed = 0;

            if (all) {
                for (int i = 0; i < xbase::MAX_AREA; ++i) {
                    xbase::DbArea& area = eng->area(i);
                    if (area.filename().empty()) continue;

                    dottalk::table::set_enabled(i, on);
                    ++changed;
                }
                out << "TABLE BUFFER: " << (on ? "ON" : "OFF")
                    << " for " << changed << " open area(s).\n";
                return;
            }

            int area0 = -1;
            for (int i = 0; i < xbase::MAX_AREA; ++i) {
                if (&eng->area(i) == &A) {
                    area0 = i;
                    break;
                }
            }

            if (area0 < 0) {
                out << "TABLE BUFFER: cannot determine current area.\n";
                return;
            }

            dottalk::table::set_enabled(area0, on);

            out << "TABLE BUFFER: " << (on ? "ON" : "OFF")
                << " (area " << area0 << ")\n";
            return;
        }

        out << "Usage: SET TABLE BUFFER ON|OFF [ALL]\n";
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET CONSOLE
    // Fox-style alias for PRN TO CONSOLE / PRN TO NULL
    // ─────────────────────────────────────────────────────────────
    if (opt == "CONSOLE") {
        std::string tok;
        args >> tok;

        bool on = (R.dest() == cli::OutputDest::Console);
        if (!parse_on_off(tok, on)) {
            out << "Usage: SET CONSOLE ON|OFF\n";
            return;
        }

        if (on) {
            R.set_dest_console();
            R.console_note("PRN: CONSOLE");
        } else {
            R.console_note("PRN: NULL");
            R.set_dest_null();
        }
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET PRINT
    // Fox-style alias for PRN TO FILE / PRN OFF
    // ─────────────────────────────────────────────────────────────
    if (opt == "PRINT") {
        std::string tok;
        args >> tok;

        if (tok.empty()) {
            out << "Usage: SET PRINT ON|OFF | SET PRINT TO <file>\n";
            return;
        }

        const std::string u = up_copy(tok);

        if (u == "TO") {
            std::string tail = ltrim_copy(rest(args));
            if (tail.empty()) {
                out << "Usage: SET PRINT TO <file>\n";
                return;
            }

            if (!R.set_dest_file(tail)) {
                out << "PRINT TO failed: " << tail << "\n";
                return;
            }

            R.console_note("PRN: FILE -> " + R.prn_file_path());
            return;
        }

        bool on = (R.dest() == cli::OutputDest::File);
        if (!parse_on_off(tok, on)) {
            out << "Usage: SET PRINT ON|OFF | SET PRINT TO <file>\n";
            return;
        }

        if (on) {
            if (!R.prn_file_path().empty()) {
                (void)R.set_dest_file(R.prn_file_path());
                R.console_note("PRN: FILE -> " + R.prn_file_path());
            } else {
                out << "SET PRINT ON requires a file. Use: SET PRINT TO <file>\n";
            }
        } else {
            R.console_note("PRN: NULL");
            R.set_dest_null();
        }
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET ALTERNATE
    // ─────────────────────────────────────────────────────────────
    if (opt == "ALTERNATE") {
        std::string tok;
        args >> tok;

        if (tok.empty()) {
            out << "Usage: SET ALTERNATE ON|OFF | SET ALTERNATE TO <file>\n";
            return;
        }

        const std::string u = up_copy(tok);

        if (u == "TO") {
            std::string tail = ltrim_copy(rest(args));
            if (tail.empty()) {
                out << "Usage: SET ALTERNATE TO <file>\n";
                return;
            }

            if (!R.set_alternate_to(tail)) {
                out << "ALTERNATE TO failed: " << tail << "\n";
                return;
            }

            out << "ALTERNATE TO: " << R.alternate_to_path() << "\n";
            return;
        }

        bool on = R.alternate_on();
        if (!parse_on_off(tok, on)) {
            out << "Usage: SET ALTERNATE ON|OFF | SET ALTERNATE TO <file>\n";
            return;
        }

        R.set_alternate(on);
        out << "Alternate is " << (on ? "ON" : "OFF") << "\n";
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET TALK
    // ─────────────────────────────────────────────────────────────
    if (opt == "TALK") {
        std::string tok;
        args >> tok;

        bool on = S.talk_on.load();
        if (!parse_on_off(tok, on)) {
            out << "Usage: SET TALK ON|OFF\n";
            return;
        }

        S.talk_on.store(on);
        out << "Talk is " << (on ? "ON" : "OFF") << "\n";
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET ECHO
    // ─────────────────────────────────────────────────────────────
    if (opt == "ECHO") {
        std::string tok;
        args >> tok;

        bool on = R.echo_on();
        if (!parse_on_off(tok, on)) {
            out << "Usage: SET ECHO ON|OFF\n";
            return;
        }

        R.set_echo(on);
        out << "Echo is " << (on ? "ON" : "OFF") << "\n";
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET PAGING
    // ─────────────────────────────────────────────────────────────
    if (opt == "PAGING") {
        std::string tok;
        args >> tok;

        bool on = R.paging_on();
        if (!parse_on_off(tok, on)) {
            out << "Usage: SET PAGING ON|OFF\n";
            return;
        }

        R.set_paging(on);
        out << "Paging is " << (on ? "ON" : "OFF") << "\n";
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET WRAP
    // ─────────────────────────────────────────────────────────────
    if (opt == "WRAP") {
        std::string tok;
        args >> tok;

        bool on = R.wrap_on();
        if (!parse_on_off(tok, on)) {
            out << "Usage: SET WRAP ON|OFF\n";
            return;
        }

        R.set_wrap(on);
        out << "Wrap is " << (on ? "ON" : "OFF") << "\n";
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET TIMER
    // ─────────────────────────────────────────────────────────────
    if (opt == "TIMER") {
        std::string tok;
        args >> tok;

        bool on = S.timer_on.load();
        if (!parse_on_off(tok, on)) {
            out << "Usage: SET TIMER ON|OFF\n";
            return;
        }

        S.timer_on.store(on);
        out << "Timer is " << (on ? "ON" : "OFF") << "\n";
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET POLLING
    // ─────────────────────────────────────────────────────────────
    if (opt == "POLLING") {
        std::string tok;
        args >> tok;

        bool on = S.polling_on.load();
        if (!parse_on_off(tok, on)) {
            out << "Usage: SET POLLING ON|OFF\n";
            return;
        }

        S.polling_on.store(on);
        out << "Polling is " << (on ? "ON" : "OFF") << "\n";
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET DELETED
    // ─────────────────────────────────────────────────────────────
    if (opt == "DELETED") {
        std::string tok;
        args >> tok;

        bool on = S.deleted_on.load();
        if (!parse_on_off(tok, on)) {
            out << "Usage: SET DELETED ON|OFF\n";
            return;
        }

        S.deleted_on.store(on);
        out << "Deleted visibility: " << (on ? "HIDE (ON)" : "SHOW (OFF)") << "\n";
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET CASE
    // Routes Fox-style SET CASE ON|OFF through the SETCASE handler.
    // Direct SETCASE remains available through the command registry.
    // ─────────────────────────────────────────────────────────────
    if (opt == "CASE" || opt == "SETCASE") {
        std::istringstream r(rest(args));
        cmd_SETCASE(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET NEAR
    // SEEK remains exact while NEAR is OFF. When NEAR is ON, SEEK/FIND
    // may later use nearest greater/equal ordered-key behavior.
    // ─────────────────────────────────────────────────────────────
    if (opt == "NEAR" || opt == "SETNEAR") {
        std::istringstream r(rest(args));
        cmd_SETNEAR(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET EDITOR TO <value|DEFAULT|OFF>
    // ─────────────────────────────────────────────────────────────
    if (opt == "EDITOR") {
        std::string sub;
        args >> sub;

        if (sub.empty()) {
            out << "Usage: SET EDITOR TO <value|DEFAULT|OFF>\n";
            return;
        }

        sub = up_copy(sub);
        if (sub != "TO") {
            out << "Usage: SET EDITOR TO <value|DEFAULT|OFF>\n";
            return;
        }

        std::string tail = ltrim_copy(rest(args));
        if (tail.empty()) {
            out << "Usage: SET EDITOR TO <value|DEFAULT|OFF>\n";
            return;
        }

        const std::string tail_up = up_copy(tail);

        if (tail_up == "OFF") {
            S.editor.mode = cli::EditorMode::Off;
            S.editor.command.clear();
            out << "EDITOR is OFF\n";
            return;
        }

        if (tail_up == "DEFAULT") {
            S.editor.mode = cli::EditorMode::Default;
            S.editor.command.clear();
            out << "EDITOR set to DEFAULT\n";
            return;
        }

        S.editor.mode = cli::EditorMode::Custom;
        S.editor.command = tail;

        out << "EDITOR set to: " << S.editor.command << "\n";
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET DEVICE TO SCREEN|FILE <path>|PRINTER [name]|NULL
    // Fox-style alias for PRN
    // ─────────────────────────────────────────────────────────────
    if (opt == "DEVICE") {
        std::string sub;
        args >> sub;

        if (up_copy(sub) != "TO") {
            out << "Usage: SET DEVICE TO SCREEN|FILE <path>|PRINTER [name]|NULL\n";
            return;
        }

        std::string mode;
        args >> mode;
        mode = up_copy(mode);

        if (mode == "SCREEN" || mode == "CONSOLE") {
            R.set_dest_console();
            R.console_note("PRN: CONSOLE");
            return;
        }

        if (mode == "NULL" || mode == "OFF") {
            R.console_note("PRN: NULL");
            R.set_dest_null();
            return;
        }

        if (mode == "FILE") {
            std::string path = ltrim_copy(rest(args));
            if (path.empty()) {
                out << "Usage: SET DEVICE TO FILE <path>\n";
                return;
            }
            if (!R.set_dest_file(path)) {
                out << "SET DEVICE TO FILE failed: " << path << "\n";
                return;
            }
            R.console_note("PRN: FILE -> " + R.prn_file_path());
            return;
        }

        if (mode == "PRINTER") {
            std::string printer_name = ltrim_copy(rest(args));
            if (!R.set_dest_printer(printer_name)) {
                out << "SET DEVICE TO PRINTER failed.\n";
                return;
            }
            if (R.prn_uses_default_printer()) {
                R.console_note("PRN: PRINTER -> (system default) [staged only]");
            } else {
                R.console_note("PRN: PRINTER -> " + R.prn_printer_name() + " [staged only]");
            }
            return;
        }

        out << "Usage: SET DEVICE TO SCREEN|FILE <path>|PRINTER [name]|NULL\n";
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET PATH
    // ─────────────────────────────────────────────────────────────
    if (opt == "PATH") {
        std::istringstream r(rest(args));
        cmd_SETPATH(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET INDEX
    // ─────────────────────────────────────────────────────────────
    if (opt == "INDEX") {
        std::istringstream r(rest(args));
        cmd_SETINDEX(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET ORDER
    // ─────────────────────────────────────────────────────────────
    if (opt == "ORDER") {
        std::istringstream r(rest(args));
        cmd_SETORDER(A, r);
        return;
    }

#if DOTTALK_WITH_DEV
    // ─────────────────────────────────────────────────────────────
    // SET FILTER
    // ─────────────────────────────────────────────────────────────
    if (opt == "FILTER") {
        std::istringstream r(rest(args));
        cmd_SETFILTER(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET RELATION
    // ─────────────────────────────────────────────────────────────
    if (opt == "RELATION") {
        std::istringstream r(rest(args));
        cmd_SET_RELATION(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET RELATIONS
    // ─────────────────────────────────────────────────────────────
    if (opt == "RELATIONS") {
        std::istringstream r(rest(args));
        cmd_SET_RELATIONS(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET CNX
    // ─────────────────────────────────────────────────────────────
    if (opt == "CNX") {
        std::istringstream r(rest(args));
        cmd_SETCNX(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET CDX
    // ─────────────────────────────────────────────────────────────
    if (opt == "CDX") {
        std::istringstream r(rest(args));
        cmd_SETCDX(A, r);
        return;
    }

    // ─────────────────────────────────────────────────────────────
    // SET LMDB
    // ─────────────────────────────────────────────────────────────
    if (opt == "LMDB") {
        std::istringstream r(rest(args));
        cmd_SETLMDB(A, r);
        return;
    }
#endif

    print_set_usage();
}