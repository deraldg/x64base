#include "dli/browse_controller.hpp"
#include "dli/screen.hpp"
#include "dli/replace_api.hpp"
#include "xbase.hpp"                    // Full DbArea definition
#include <iostream>
#include <cstdio>

#ifdef _WIN32
#include <windows.h>
#else
#include <termios.h>
#include <unistd.h>
#endif

namespace {

constexpr int kKeyReturn = 13;
constexpr int kKeyEscape = 27;
constexpr int kKeyF2 = 0x1001;
constexpr int kKeyF3 = 0x1002;
constexpr int kKeyF4 = 0x1003;

#ifdef _WIN32
int read_browse_key() {
    HANDLE hIn = GetStdHandle(STD_INPUT_HANDLE);
    INPUT_RECORD rec;
    DWORD n = 0;
    if (!ReadConsoleInput(hIn, &rec, 1, &n)) {
        return -1;
    }
    if (rec.EventType == KEY_EVENT && rec.Event.KeyEvent.bKeyDown) {
        return static_cast<int>(rec.Event.KeyEvent.wVirtualKeyCode);
    }
    return 0;
}
#else
class ScopedRawMode {
public:
    ScopedRawMode() {
        if (::tcgetattr(STDIN_FILENO, &old_) == 0) {
            termios raw = old_;
            raw.c_lflag &= static_cast<unsigned long>(~(ICANON | ECHO));
            raw.c_cc[VMIN] = 1;
            raw.c_cc[VTIME] = 0;
            enabled_ = (::tcsetattr(STDIN_FILENO, TCSANOW, &raw) == 0);
        }
    }

    ~ScopedRawMode() {
        if (enabled_) {
            ::tcsetattr(STDIN_FILENO, TCSANOW, &old_);
        }
    }

private:
    termios old_{};
    bool enabled_ = false;
};

int read_browse_key() {
    int ch = std::getchar();
    if (ch == EOF) {
        return -1;
    }

    if (ch != kKeyEscape) {
        return ch;
    }

    int ch2 = std::getchar();
    if (ch2 == EOF) {
        return kKeyEscape;
    }

    if (ch2 == 'O') {
        int ch3 = std::getchar();
        if (ch3 == 'Q') return kKeyF2;
        if (ch3 == 'R') return kKeyF3;
        if (ch3 == 'S') return kKeyF4;
        return kKeyEscape;
    }

    if (ch2 == '[') {
        int ch3 = std::getchar();
        if (ch3 == '1') {
            int ch4 = std::getchar();
            if (ch4 == '2') {
                int ch5 = std::getchar();
                if (ch5 == '~') return kKeyF2;
            } else if (ch4 == '3') {
                int ch5 = std::getchar();
                if (ch5 == '~') return kKeyF3;
            } else if (ch4 == '4') {
                int ch5 = std::getchar();
                if (ch5 == '~') return kKeyF4;
            }
        }
        return kKeyEscape;
    }

    return kKeyEscape;
}
#endif

} // namespace

namespace dli {

BrowseController::BrowseController(xbase::DbArea& db)
    : m_db(db)
    , m_gridPaint({10, 35}, screen_width(), screen_height() - 4, true)
    , m_mode(BrowseMode::Form)
{
    m_editSession = begin_edit(db);
    refresh_current_record_form();
}

void BrowseController::run() {
    screen_clear(true);
    screen_enable_vt(true);

#ifndef _WIN32
    ScopedRawMode raw_mode;
#endif

    while (m_running) {
        redraw();
        const int key = read_browse_key();
        if (key < 0) {
            break;
        }
        if (key != 0) {
            handle_key(key);
        }
    }

    screen_clear(true);
    screen_set_cursor(0, screen_height() - 1, true);
}

void BrowseController::switch_mode(BrowseMode newMode) {
    m_mode = newMode;
    screen_clear(true);
}

void BrowseController::redraw() {
    if (m_mode == BrowseMode::Form) {
        draw_form_view();
    } else {
        draw_grid_view();
    }
}

// ====================== FORM VIEW ======================
void BrowseController::draw_form_view() {
    draw_form_border();

    int y = 3;
    for (const auto& [fname, fvalue] : m_currentFields) {
        if (y >= screen_height() - 3) break;

        std::string line = " " + fname;
        line.resize(18, ' ');
        line += " : " + fvalue;

        if (m_inEdit && fname == m_currentEditingField) {
            line = vt_fg(line, 226, true, true);   // bright yellow
        }

        screen_write_line(y++, line);
    }

    std::string status = " REC " + std::to_string(m_currentRecno) +
                         "   F2=Edit  F3=Next  F4=Prev  G=Grid  Esc=Quit";
    screen_write_line(screen_height() - 1, status);
}

void BrowseController::draw_form_border() {
    int W = screen_width();
    if (W < 4) return;

    std::string top    = "+" + std::string(W - 2, '-') + "+";
    std::string middle = "|" + std::string(W - 2, ' ') + "|";

    screen_write_line(1, top);
    for (int y = 2; y < screen_height() - 2; ++y) {
        screen_write_line(y, middle);
    }
    screen_write_line(screen_height() - 2, top);
}


void BrowseController::refresh_current_record_form() {
    m_currentRecno = m_db.recno64();

    // Placeholder - replace with real data later
    m_currentFields = {
        {"REC",     std::to_string(m_currentRecno)},
        {"SID",     "50000002"},
        {"LNAME",   "Ramirez"},
        {"FNAME",   "Skyler"},
        {"DOB",     "19890329"},
        {"GENDER",  "X"},
        {"MAJOR",   "HIST"},
        {"GPA",     "2.58"},
        {"EMAIL",   "skyler.ramirez2@student.mcc.edu"}
    };
}

// ====================== GRID VIEW ======================
void BrowseController::draw_grid_view() {
    screen_write_line(1, vt_fg("=== GRID / BROWSE VIEW ===", 10, true, true));
    m_gridPaint.redraw_all();
}

// ====================== KEY HANDLING ======================
void BrowseController::handle_key(int vk) {
    if (m_inEdit) {
        if (vk == kKeyReturn)      commit_edit();
        else if (vk == kKeyEscape) cancel_edit();
        return;
    }

    switch (vk) {
        case kKeyF2:
            if (m_currentFields.size() > 1) {
                start_edit(m_currentFields[1].first);
            }
            break;

        case kKeyF3:   // Next record
            break;

        case kKeyF4:   // Previous record
            break;

        case 'G':
        case 'g':
            switch_mode(BrowseMode::Grid);
            break;

        case 'F':
        case 'f':
            switch_mode(BrowseMode::Form);
            break;

        case kKeyEscape:
        case 'Q':
        case 'q':
            m_running = false;
            break;

        default:
            break;
    }
}

void BrowseController::start_edit(const std::string& fieldName) {
    m_currentEditingField = fieldName;
    m_inEdit = true;
    m_editSession = begin_edit(m_db);
    std::cout << "\n>>> Editing field: " << fieldName << " (real input soon)\n";
}

void BrowseController::commit_edit() {
    std::string err;
    if (commit(m_editSession, err)) {
        screen_write_line(screen_height()-2, vt_fg(" Saved successfully ", 82, true, true));
        refresh_current_record_form();
    } else {
        screen_write_line(screen_height()-2, vt_fg(" Error: " + err, 196, true, true));
    }
    m_inEdit = false;
    m_currentEditingField.clear();
}

void BrowseController::cancel_edit() {
    cancel(m_editSession);
    m_inEdit = false;
    m_currentEditingField.clear();
}

} // namespace dli
