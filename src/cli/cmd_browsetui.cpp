// src/cli/cmd_browsetui.cpp
// COMPLETE + TARGETED CLEAR VERSION - No more "declared but not defined" errors

// @dottalk.usage v1
// owner: DOT|BROWSETUI
// command: BROWSETUI
// category: ui
// status: supported
// noargs: interactive
// effect: interactive
// mutates: delegates create append delete goto replace-like staged edits
// usage-access: BROWSETUI USAGE
// summary:
//   Enter the full-screen Turbo/console browse UI with create, read, update,
//   delete, append, navigation, and staged edit support.
//
// usage:
//   BROWSETUI USAGE
//   BROWSETUI
//
// notes:
//   BROWSETUI with no arguments enters the interactive TUI browser.
//   The TUI uses function keys and single-key commands for create, read/list, update/edit, delete, append, goto, help, and quit.
//   Edits may be staged and then saved or discarded when navigating or exiting.
//   BROWSETUI delegates to existing command handlers for create, append, delete, list/display, goto, and update-like operations.
//   BROWSETUI is interactive and may mutate table data or session state depending on user actions.
//
// risk:
//   interactive: yes
//   mutates_table_data: create append delete update actions
//   mutates_record_pointer: navigation actions
//   staged_edits: yes
//   delegates_to_create: yes
//   delegates_to_append: yes
//   delegates_to_delete: yes
//
// related:
//   BROWSE
//   BROWSER
//   CREATE
//   APPEND
//   DELETE
//   GOTO
//

#include <string>
#include <vector>
#include <sstream>
#include <iostream>
#include <algorithm>
#include <cctype>
#include <memory>
#include <unordered_map>
#include <cstdlib>
#include <cstdio>

#include "xbase.hpp"
#include "cli/console.hpp"
#include "dli/browsetui.hpp"
#include "memo/memo_display.hpp"
#include "cli/replace_multi.hpp"

// External commands
extern void cmd_LIST    (xbase::DbArea&, std::istringstream&);
extern void cmd_DISPLAY (xbase::DbArea&, std::istringstream&);
extern void cmd_GOTO    (xbase::DbArea&, std::istringstream&);
extern void cmd_TOP     (xbase::DbArea&, std::istringstream&);
extern void cmd_BOTTOM  (xbase::DbArea&, std::istringstream&);
extern void cmd_CREATE  (xbase::DbArea&, std::istringstream&);
extern void cmd_APPEND  (xbase::DbArea&, std::istringstream&);
extern void cmd_DELETE  (xbase::DbArea&, std::istringstream&);

extern std::vector<std::string>
build_browse_lines(int inner_w, int inner_h, int recno, const std::vector<FieldView>& fields);

// ==================================================================
// Targeted Clear Helper
// ==================================================================
static void clear_content_area(Console& con, int x, int y, int width, int height) {
    std::string blank(width, ' ');
    for (int i = 0; i < height; ++i) {
        con.draw_text(x, y + i, blank);
    }
}

// ==================================================================
// Small helpers
// ==================================================================
static inline void rtrim_inplace(std::string& s) {
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back())))
        s.pop_back();
}


static std::string browsetui_trim(std::string s) {
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string browsetui_upper(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool is_browsetui_usage_request(std::string raw) {
    std::string t = browsetui_upper(browsetui_trim(std::move(raw)));
    if (t.rfind("BROWSETUI ", 0) == 0) t = browsetui_trim(t.substr(10));
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_browsetui_usage() {
    std::cout
        << "Usage:\n"
        << "  BROWSETUI USAGE\n"
        << "  BROWSETUI\n"
        << "Notes:\n"
        << "  - Enters the full-screen interactive browse TUI.\n"
        << "  - F1 create, F2 read/list, F3 update/edit, F4 delete, F5 append.\n"
        << "  - G goto, L list/read, D display, E edit, H/? help, Q/Esc quit.\n";
}

// ==================================================================
// Key decoding
// ==================================================================
enum class Key {
    Other, Esc, Quit, Enter, Up, Down, Home, End, G, L, D, E, Help, CtrlS,
    PageUp, PageDown, F1, F2, F3, F4, F5, F6
};

static Key read_key(Console& con) {
    int c = con.get_key();
    if (c == 27) {
        int c2 = con.get_key();
        if (c2 == '[') {
            int c3 = con.get_key();
            switch (c3) {
                case 'A': return Key::Up;
                case 'B': return Key::Down;
                case 'H': return Key::Home;
                case 'F': return Key::End;
                case '5': con.get_key(); return Key::PageUp;
                case '6': con.get_key(); return Key::PageDown;
                default:  return Key::Other;
            }
        }
        return Key::Esc;
    }
#ifdef _WIN32
    if (c == 224 || c == 0) {
        int c2 = con.get_key();
        switch (c2) {
            case 72: return Key::Up;
            case 80: return Key::Down;
            case 71: return Key::Home;
            case 79: return Key::End;
            case 73: return Key::PageUp;
            case 81: return Key::PageDown;
            case 59: return Key::F1;
            case 60: return Key::F2;
            case 61: return Key::F3;
            case 62: return Key::F4;
            case 63: return Key::F5;
            case 64: return Key::F6;
            default: return Key::Other;
        }
    }
#endif
    if (c == '\r' || c == '\n') return Key::Enter;
    if (c == 19) return Key::CtrlS;
    if (c == 'q' || c == 'Q') return Key::Quit;
    if (c == 'g' || c == 'G') return Key::G;
    if (c == 'l' || c == 'L') return Key::L;
    if (c == 'd' || c == 'D') return Key::D;
    if (c == 'e' || c == 'E') return Key::E;
    if (c == '?' || c == 'h' || c == 'H') return Key::Help;
    return Key::Other;
}

// ==================================================================
// UI Bars
// ==================================================================
static const char* SGR_RESET      = "\x1b[0m";
static const char* SGR_HEADER_BAR = "\x1b[1;37;42m";
static const char* SGR_FOOTER_BAR = "\x1b[30;43m";
static const char* SGR_MENU_BAR   = "\x1b[47;30m";

static void draw_color_bar(Console& con, int y, int width,
                           const std::string& left, const std::string& right,
                           const char* style_sgr) {
    std::string line;
    line.reserve(static_cast<size_t>(width));
    const int rlen = static_cast<int>(right.size());
    int space_for_left = std::max(0, width - rlen);

    std::string L = left;
    if (static_cast<int>(L.size()) > space_for_left) L.resize(static_cast<size_t>(space_for_left));
    line += L;
    line.append(static_cast<size_t>(space_for_left - static_cast<int>(L.size())), ' ');

    std::string R = right;
    if (static_cast<int>(R.size()) > width) R.resize(static_cast<size_t>(width));
    line += R;

    if (static_cast<int>(line.size()) < width)
        line.append(static_cast<size_t>(width - static_cast<int>(line.size())), ' ');

    con.draw_text(0, y, std::string(style_sgr) + line + SGR_RESET);
}

static void draw_header_menu(Console& con, int y, int width) {
    std::string menu = " F1:Create | F2:Read | F3:Update | F4:Delete | F5:Append ";
    std::string line;
    line.reserve(static_cast<size_t>(width));
    int padding = std::max(0, width - static_cast<int>(menu.size()));
    line.append(static_cast<size_t>(padding/2), ' ');
    line += menu;
    line.append(static_cast<size_t>(padding - padding/2), ' ');
    con.draw_text(0, y, std::string(SGR_MENU_BAR) + line + SGR_RESET);
}

// ==================================================================
// All Prompt Functions - FULL DEFINITIONS
// ==================================================================
static bool prompt_yes_no(Console& con, int footer_y, int term_cols, const std::string& question, bool& out_yes) {
    std::string s = question + " (Y/N, Esc=cancel)";
    if (static_cast<int>(s.size()) < term_cols) s.append(static_cast<size_t>(term_cols - static_cast<int>(s.size())), ' ');
    con.draw_text(0, footer_y, std::string(SGR_FOOTER_BAR) + s + SGR_RESET);
    std::cout.flush();
    for (;;) {
        int ch = con.get_key();
#ifdef _WIN32
        if (ch == 224 || ch == 0) { (void)con.get_key(); continue; }
#endif
        if (ch == 27) return false;
        if (ch == 'y' || ch == 'Y') { out_yes = true;  return true; }
        if (ch == 'n' || ch == 'N') { out_yes = false; return true; }
    }
}

static bool prompt_goto(Console& con, int footer_y, int term_cols, int& out_recno) {
    std::string buf;
    auto paint = [&](const std::string& pre) {
        std::string s = pre + buf;
        if (static_cast<int>(s.size()) < term_cols) s.append(static_cast<size_t>(term_cols - static_cast<int>(s.size())), ' ');
        con.draw_text(0, footer_y, std::string(SGR_FOOTER_BAR) + s + SGR_RESET);
        std::cout.flush();
    };
    paint("Goto rec: ");
    for (;;) {
        int ch = con.get_key();
#ifdef _WIN32
        if (ch == 224 || ch == 0) { (void)con.get_key(); continue; }
#endif
        if (ch == 27) return false;
        if (ch == '\r' || ch == '\n') break;
        if (ch == 8 || ch == 127) { if (!buf.empty()) { buf.pop_back(); paint("Goto rec: "); } continue; }
        if (std::isdigit(ch)) { buf.push_back(static_cast<char>(ch)); paint("Goto rec: "); continue; }
    }
    if (buf.empty()) return false;
    out_recno = std::max(1, std::stoi(buf));
    return true;
}

static bool prompt_for_create_string(Console& con, int footer_y, int term_cols, const std::string& question, std::string& out) {
    std::string buf;
    auto paint = [&](const std::string& pre) {
        std::string s = pre + buf;
        if (static_cast<int>(s.size()) < term_cols) s.append(static_cast<size_t>(term_cols - static_cast<int>(s.size())), ' ');
        con.draw_text(0, footer_y, std::string(SGR_FOOTER_BAR) + s + SGR_RESET);
        std::cout.flush();
    };
    paint(question);
    for (;;) {
        int ch = con.get_key();
        if (ch == 27) return false;
        if (ch == '\r' || ch == '\n') break;
        if (ch == 8 || ch == 127) { if (!buf.empty()) buf.pop_back(); paint(question); continue; }
        if (ch >= 32 && ch <= 126) { buf.push_back(static_cast<char>(ch)); paint(question); continue; }
    }
    out = buf;
    return true;
}

// ==================================================================
// Type-aware editing helpers
// ==================================================================
static std::string normalize_date_YYYYMMDD(const std::string& in_raw) {
    std::string digits;
    for (char c : in_raw) if (std::isdigit(static_cast<unsigned char>(c))) digits.push_back(c);
    if (digits.size() == 8) {
        int y = std::atoi(digits.substr(0,4).c_str());
        int m = std::atoi(digits.substr(4,2).c_str());
        int d = std::atoi(digits.substr(6,2).c_str());
        if (y > 0 && m >= 1 && m <= 12 && d >= 1 && d <= 31) return digits;
    }
    return "";
}

static std::string normalize_numeric(const std::string& in, int length, int decimals) {
    std::string s; s.reserve(in.size());
    bool seen_dot = false;
    for (char c : in) {
        if ((c == '-' && s.empty()) || std::isdigit(static_cast<unsigned char>(c))) { s.push_back(c); continue; }
        if (decimals > 0 && c == '.' && !seen_dot) { seen_dot = true; s.push_back(c); continue; }
        if (std::isspace(static_cast<unsigned char>(c))) continue;
        return "";
    }
    if (s.empty() || s == "-" || s == ".") return "";
    if (decimals == 0) {
        size_t dot = s.find('.');
        if (dot != std::string::npos) s.erase(dot);
    }
    if (static_cast<int>(s.size()) > length) return "";
    return s;
}

static std::string normalize_logical_from_key(int ch, const std::string& currentTF) {
    auto toTF = [](char c)->std::string {
        switch (std::toupper(static_cast<unsigned char>(c))) {
            case 'T': case 'Y': case '1': return "T";
            case 'F': case 'N': case '0': return "F";
            default: return "";
        }
    };
    if (ch == ' ') return (currentTF == "T" ? "F" : "T");
    return toTF(static_cast<char>(ch));
}

static bool prompt_value_for_field(Console& con, int footer_y, int term_cols,
                                   xbase::DbArea& area, int fieldIndex,
                                   const std::string& fieldName, char fieldType,
                                   int fieldLen, int fieldDec, std::string& outNormalized) {
    (void)area.readCurrent();
    std::string current = area.get(fieldIndex + 1);
    rtrim_inplace(current);
    char typeCh = static_cast<char>(std::toupper(static_cast<unsigned char>(fieldType)));
    std::string base = "Set " + fieldName + " (" + std::string(1, typeCh) + "): ";

    if (typeCh == 'L') {
        std::string curTF = (!current.empty() && (current[0]=='T' || current[0]=='t')) ? "T" : "F";
        std::string msg = base + "[ " + curTF + " ] <Space toggle, Enter accept, Esc cancel>";
        std::string s = msg; 
        if (static_cast<int>(s.size()) < term_cols) s.append(static_cast<size_t>(term_cols - static_cast<int>(s.size())), ' ');
        con.draw_text(0, footer_y, std::string(SGR_FOOTER_BAR) + s + SGR_RESET);
        std::cout.flush();

        std::string nextTF = curTF;
        for (;;) {
            int ch = con.get_key();
#ifdef _WIN32
            if (ch == 224 || ch == 0) { (void)con.get_key(); continue; }
#endif
            if (ch == 27) return false;
            if (ch == '\r' || ch == '\n') { outNormalized = nextTF; return true; }
            std::string set = normalize_logical_from_key(ch, nextTF);
            if (!set.empty()) {
                nextTF = set;
                std::string s2 = base + "[ " + nextTF + " ] <Space toggle, Enter accept, Esc cancel>";
                if (static_cast<int>(s2.size()) < term_cols) s2.append(static_cast<size_t>(term_cols - static_cast<int>(s2.size())), ' ');
                con.draw_text(0, footer_y, std::string(SGR_FOOTER_BAR) + s2 + SGR_RESET);
                std::cout.flush();
            }
        }
    } else {
        std::string buf;
        auto paint = [&]() {
            std::string s = base + "[" + current + "] : " + buf;
            if (static_cast<int>(s.size()) < term_cols) s.append(static_cast<size_t>(term_cols - static_cast<int>(s.size())), ' ');
            con.draw_text(0, footer_y, std::string(SGR_FOOTER_BAR) + s + SGR_RESET);
            std::cout.flush();
        };
        paint();
        for (;;) {
            int ch = con.get_key();
#ifdef _WIN32
            if (ch == 224 || ch == 0) { (void)con.get_key(); continue; }
#endif
            if (ch == 27) return false;
            if (ch == '\r' || ch == '\n') {
                std::string entered = buf.empty() ? current : buf;
                if (typeCh == 'D') outNormalized = normalize_date_YYYYMMDD(entered);
                else if (typeCh == 'N') outNormalized = normalize_numeric(entered, fieldLen, fieldDec);
                else outNormalized = entered;
                return true;
            }
            if (ch == 8 || ch == 127) { if (!buf.empty()) { buf.pop_back(); paint(); } continue; }
            if (ch >= 32 && ch <= 126) { buf.push_back(static_cast<char>(ch)); paint(); continue; }
        }
    }
}

// ==================================================================
// Staging
// ==================================================================
struct PendingEdits {
    std::unordered_map<std::string, std::string> by_name;
    void clear() { by_name.clear(); }
    bool empty() const { return by_name.empty(); }
    size_t count() const { return by_name.size(); }
};

static bool save_staged_transactional(Console& con, xbase::DbArea& area, const PendingEdits& staged) {
    if (staged.empty()) return true;
    std::vector<FieldUpdate> updates;
    updates.reserve(staged.by_name.size());
    for (const auto& kv : staged.by_name)
        updates.push_back(FieldUpdate{kv.first, kv.second});

    std::string err;
    bool ok = cmd_REPLACE_MULTI(area, updates, &err);
    if (!ok) {
        int y = con.size().rows - 1;
        con.draw_text(0, y, "Error: " + err + " (press any key)", -1);
        (void)con.get_key();
    }
    return ok;
}

// ==================================================================
// Editor
// ==================================================================
struct EditorState { int selected = 0; int scroll = 0; };

static void render_editor(Console& con, const Size& term, int frame_l, int frame_t, int frame_w, int frame_h,
                          xbase::DbArea& area, const EditorState& st, const PendingEdits& staged, const std::string& status) {
    const int inner_w = frame_w - 2;
    const int inner_h = frame_h - 2;

    con.clear(); // editor can keep full clear for simplicity
    draw_color_bar(con, 0, term.cols, "EDIT RECORD", "ESC:Back ↑↓:Move Enter:Edit Ctrl+S:Save", SGR_HEADER_BAR);
    con.draw_frame(frame_l, frame_t, frame_w, frame_h);

    (void)area.readCurrent();
    const auto& F = area.fields();
    int total = static_cast<int>(F.size());
    int y = frame_t + 1;
    int start = std::clamp(st.scroll, 0, std::max(0, total - inner_h));
    int end = std::min(total, start + inner_h);

    for (int i = start; i < end; ++i, ++y) {
        const std::string& name = F[static_cast<size_t>(i)].name;
        std::string val = area.get(i + 1);
        rtrim_inplace(val);
        auto it = staged.by_name.find(name);
        if (it != staged.by_name.end()) val = it->second;

        std::string line = name + ": " + val;
        if (static_cast<int>(line.size()) > inner_w) line.resize(static_cast<size_t>(inner_w));

        if (i == st.selected)
            con.draw_text(frame_l + 1, y, std::string("\x1b[7m") + line + SGR_RESET, inner_w);
        else
            con.draw_text(frame_l + 1, y, line, inner_w);
    }

    std::string foot = status;
    if (!staged.empty()) foot += "  [staged: " + std::to_string(staged.count()) + "]";
    if (static_cast<int>(foot.size()) < term.cols)
        foot.append(static_cast<size_t>(term.cols - static_cast<int>(foot.size())), ' ');
    con.draw_text(0, term.rows - 1, std::string(SGR_FOOTER_BAR) + foot + SGR_RESET);
    std::cout.flush();
}

static void run_editor(Console& con, xbase::DbArea& area, PendingEdits& staged) {
    std::string status = "Enter to stage value, Ctrl+S to save, ESC to return.";
    EditorState st{0, 0};

    for (;;) {
        const Size term = con.size();
        const int margin = 1, header_h = 2, footer_h = 1;
        const int frame_l = margin;
        const int frame_t = header_h + margin;
        const int frame_w = std::max(40, term.cols - 2*margin);
        const int frame_h = std::max(8, term.rows - header_h - footer_h - 2*margin);

        const auto& F = area.fields();
        int total = static_cast<int>(F.size());

        st.selected = std::clamp(st.selected, 0, std::max(0, total - 1));
        int inner_h = frame_h - 2;
        if (st.selected < st.scroll) st.scroll = st.selected;
        if (st.selected >= st.scroll + inner_h) st.scroll = st.selected - inner_h + 1;

        render_editor(con, term, frame_l, frame_t, frame_w, frame_h, area, st, staged, status);

        Key k = read_key(con);
        if (k == Key::Esc || k == Key::Quit) {
            if (!staged.empty()) {
                bool yes = false;
                if (prompt_yes_no(con, term.rows-1, term.cols, "Save changes?", yes)) {
                    if (yes) save_staged_transactional(con, area, staged);
                }
                staged.clear();
            }
            break;
        }

        switch (k) {
            case Key::Up:    if (st.selected > 0) st.selected--; break;
            case Key::Down:  if (st.selected + 1 < total) st.selected++; break;
            case Key::Home:  st.selected = 0; st.scroll = 0; break;
            case Key::End:   st.selected = std::max(0, total-1); st.scroll = std::max(0, total-inner_h); break;
            case Key::CtrlS:
                if (!staged.empty() && save_staged_transactional(con, area, staged)) {
                    staged.clear();
                    status = "Saved.";
                }
                break;
            case Key::Enter:
                if (st.selected >= 0 && st.selected < total) {
                    const auto& fd = F[static_cast<size_t>(st.selected)];
                    std::string norm;
                    if (prompt_value_for_field(con, term.rows-1, term.cols, area,
                                               st.selected, fd.name, fd.type,
                                               static_cast<int>(fd.length),
                                               static_cast<int>(fd.decimals), norm)) {
                        staged.by_name[fd.name] = norm;
                        status = "Staged " + fd.name;
                    }
                }
                break;
            default: break;
        }
    }
}

static void show_modal(Console& con, const std::string& title,
                       xbase::DbArea& area,
                       void(*handler)(xbase::DbArea&, std::istringstream&),
                       std::istringstream& args) {
    con.clear();
    const Size term = con.size();
    draw_color_bar(con, 0, term.cols, title, "", SGR_HEADER_BAR);
    handler(area, args);
    con.draw_text(0, term.rows - 1, std::string(SGR_FOOTER_BAR) + "Press any key to return." + SGR_RESET);
    std::cout.flush();
    (void)con.get_key();
}

// ==================================================================
// MAIN COMMAND
// ==================================================================
void cmd_BROWSETUI(xbase::DbArea& area, std::istringstream& iss) {
    const std::string raw_args = iss.str();
    if (is_browsetui_usage_request(raw_args)) {
        print_browsetui_usage();
        return;
    }

    std::unique_ptr<Console> con(make_console());
    std::string status = "Ready.";
    bool isFullScreen = false;
    PendingEdits staged;

    auto get_recno    = [&]() -> long long { return area.isOpen() ? area.recno() : 0LL; };
    auto get_reccount = [&]() -> long long { return area.isOpen() ? area.recCount() : 0LL; };

    auto collect_fields = [&]() -> std::vector<FieldView> {
        std::vector<FieldView> out;
        if (!area.isOpen()) return out;
        (void)area.readCurrent();
        const auto& F = area.fields();
        out.reserve(F.size());
        for (size_t i = 0; i < F.size(); ++i) {
            std::string value = area.get(static_cast<int>(i) + 1);
            rtrim_inplace(value);
            auto it = staged.by_name.find(F[i].name);
            if (it != staged.by_name.end()) value = it->second;
            out.push_back(FieldView{F[i].name, value});
        }
        return out;
    };

    auto render = [&](const std::string& footer_msg) {
        const Size term = con->size();
        const bool isFull = isFullScreen;
        const int header_h = isFull ? 1 : 3;
        const int footer_h = 1;

        int frame_l = 0, frame_t = 0, frame_w = 0, frame_h = 0;
        if (isFull) {
            frame_l = 0; frame_t = header_h; frame_w = term.cols; frame_h = term.rows - header_h - footer_h;
        } else {
            const int min_w = 60, min_h = 12;
            frame_w = std::clamp(static_cast<int>(term.cols * 0.75), min_w, term.cols - 4);
            frame_h = std::clamp(static_cast<int>(term.rows * 0.75), min_h, term.rows - header_h - footer_h - 2);
            frame_l = std::max(0, (term.cols - frame_w) / 2);
            frame_t = header_h + std::max(1, (term.rows - header_h - footer_h - frame_h) / 2);
        }

        const int inner_w = frame_w - 2;
        const int inner_h = frame_h - 2;

        // TARGETED CLEAR
        clear_content_area(*con, 0, 0, term.cols, header_h);
        if (!isFull) clear_content_area(*con, 0, 1, term.cols, 1);
        clear_content_area(*con, frame_l, frame_t, frame_w, frame_h);
        clear_content_area(*con, 0, term.rows - 1, term.cols, 1);

        // Redraw
        draw_color_bar(*con, 0, term.cols, "DotTalk++", "A TUI Database Shell", SGR_HEADER_BAR);
        if (!isFull) draw_header_menu(*con, 1, term.cols);
        con->draw_frame(frame_l, frame_t, frame_w, frame_h);

        if (area.isOpen() && get_reccount() > 0) {
            int recno_int = static_cast<int>(std::clamp(get_recno(), 1LL, 2147483647LL));
            auto fields = collect_fields();
            auto lines = build_browse_lines(inner_w, inner_h, recno_int, fields);
            for (int i = 0; i < inner_h && i < static_cast<int>(lines.size()); ++i) {
                con->draw_text(frame_l + 1, frame_t + 1 + i, lines[static_cast<size_t>(i)], inner_w);
            }
        } else if (!area.isOpen()) {
            con->draw_text(frame_l + 1, frame_t + 1, "No table is open.", inner_w);
        } else {
            con->draw_text(frame_l + 1, frame_t + 1, "Table is empty.", inner_w);
        }

        std::string foot = footer_msg;
        if (!staged.empty()) foot += "  [modified]";
        if (static_cast<int>(foot.size()) < term.cols)
            foot.append(static_cast<size_t>(term.cols - static_cast<int>(foot.size())), ' ');
        con->draw_text(0, term.rows - 1, std::string(SGR_FOOTER_BAR) + foot + SGR_RESET);

        std::cout.flush();
    };

    auto maybe_save_staged = [&](bool navigating) -> bool {
        if (staged.empty()) return true;
        const Size term = con->size();
        bool yes = false;
        std::string q = navigating ? "Save changes before navigating?" : "Save changes before exiting?";
        if (!prompt_yes_no(*con, term.rows - 1, term.cols, q, yes)) return false;
        if (yes) {
            if (save_staged_transactional(*con, area, staged)) {
                staged.clear();
                return true;
            }
            return false;
        } else {
            staged.clear();
            return true;
        }
    };

    render(status);

    for (;;) {
        Key k = read_key(*con);

        if (k == Key::Esc || k == Key::Quit) {
            if (!maybe_save_staged(false)) { render(status); continue; }
            status = "Leaving BROWSE.";
            render(status);
            std::cout << "\n";
            std::system("cls");
            break;
        }

        const long long total = get_reccount();
        const long long cur   = get_recno();

        switch (k) {
            case Key::F6: isFullScreen = !isFullScreen; break;

            case Key::G:
                if (total > 0 && maybe_save_staged(true)) {
                    const Size term = con->size();
                    int target = 0;
                    if (prompt_goto(*con, term.rows - 1, term.cols, target)) {
                        const long long bounded = std::clamp<long long>(target, 1LL, total);
                        std::istringstream s(std::to_string(bounded));
                        cmd_GOTO(area, s);
                        staged.clear();
                        status = "REC " + std::to_string(get_recno()) + " / " + std::to_string(total);
                    } else {
                        status = "Goto cancelled.";
                    }
                } else if (total <= 0) {
                    status = "No records to goto.";
                }
                break;

            case Key::F1:
                if (!maybe_save_staged(true)) { render(status); continue; }
                {
                    const Size term = con->size();
                    std::string create_args;
                    if (prompt_for_create_string(*con, term.rows - 1, term.cols,
                                                 "CREATE arguments: ", create_args)) {
                        create_args = std::string(create_args.begin(),
                                                  std::find_if(create_args.rbegin(), create_args.rend(),
                                                               [](unsigned char ch) { return !std::isspace(ch); }).base());
                        create_args.erase(create_args.begin(),
                                          std::find_if(create_args.begin(), create_args.end(),
                                                       [](unsigned char ch) { return !std::isspace(ch); }));
                        if (!create_args.empty()) {
                            std::istringstream s(create_args);
                            show_modal(*con, "CREATE", area, cmd_CREATE, s);
                            status = "Returned from CREATE.";
                        } else {
                            status = "CREATE cancelled: no arguments.";
                        }
                    } else {
                        status = "CREATE cancelled.";
                    }
                }
                break;

            case Key::F2: case Key::D: case Key::L:
                if (!maybe_save_staged(true)) { render(status); continue; }
                {
                    std::istringstream noargs;
                    show_modal(*con, "LIST / DISPLAY", area, cmd_LIST, noargs);
                    status = "Returned from LIST.";
                }
                break;

            case Key::F3: case Key::E:
                if (!maybe_save_staged(true)) { render(status); continue; }
                if (area.isOpen()) run_editor(*con, area, staged);
                else status = "No table open.";
                break;

            case Key::F4:
                if (!maybe_save_staged(true)) { render(status); continue; }
                if (area.isOpen()) {
                    std::istringstream s("DELETE");
                    cmd_DELETE(area, s);
                }
                break;

            case Key::F5:
                if (!maybe_save_staged(true)) { render(status); continue; }
                if (area.isOpen()) {
                    std::istringstream s("APPEND BLANK");
                    cmd_APPEND(area, s);
                }
                break;

            case Key::CtrlS:
                if (!staged.empty() && save_staged_transactional(*con, area, staged)) {
                    staged.clear();
                    status = "Changes saved.";
                }
                break;

            case Key::Up:
                if (total > 0 && maybe_save_staged(true)) {
                    long long target = std::max(1LL, cur - 1);
                    if (target != cur) {
                        std::istringstream s(std::to_string(target));
                        cmd_GOTO(area, s);
                        staged.clear();
                    }
                }
                status = "REC " + std::to_string(get_recno()) + " / " + std::to_string(total);
                break;

            case Key::Down:
                if (total > 0 && maybe_save_staged(true)) {
                    long long target = std::min(total, cur + 1);
                    if (target != cur) {
                        std::istringstream s(std::to_string(target));
                        cmd_GOTO(area, s);
                        staged.clear();
                    }
                }
                status = "REC " + std::to_string(get_recno()) + " / " + std::to_string(total);
                break;

            case Key::Help:
                status = "↑↓ PgUp/PgDn Home/End: Navigate | G: Goto | E/F3: Edit | Ctrl+S: Save | F6: Fullscreen | Esc: Quit";
                break;

            default: break;
        }
        render(status);
    }
}