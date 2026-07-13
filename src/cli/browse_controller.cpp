#include "dli/browse_controller.hpp"
#include "dli/screen.hpp"
#include "dli/replace_api.hpp"
#include "xbase.hpp"                    // Full DbArea definition
#ifdef _WIN32
#include <windows.h>
#endif
#include <iostream>

namespace dli {
namespace {
#ifdef _WIN32
constexpr int key_return = VK_RETURN;
constexpr int key_escape = VK_ESCAPE;
constexpr int key_f2 = VK_F2;
constexpr int key_f3 = VK_F3;
constexpr int key_f4 = VK_F4;
#else
constexpr int key_return = '\n';
constexpr int key_escape = 27;
constexpr int key_f2 = -2;
constexpr int key_f3 = -3;
constexpr int key_f4 = -4;
#endif
} // namespace

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

    while (m_running) {
        redraw();

#ifdef _WIN32
        HANDLE hIn = GetStdHandle(STD_INPUT_HANDLE);
        INPUT_RECORD rec;
        DWORD n = 0;
        if (!ReadConsoleInput(hIn, &rec, 1, &n)) break;

        if (rec.EventType == KEY_EVENT && rec.Event.KeyEvent.bKeyDown) {
            handle_key(rec.Event.KeyEvent.wVirtualKeyCode);
        }
#else
        const int key = std::cin.get();
        if (key == std::char_traits<char>::eof()) break;
        handle_key(key);
#endif
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
        if (vk == key_return)      commit_edit();
        else if (vk == key_escape) cancel_edit();
        return;
    }

    switch (vk) {
        case key_f2:
            if (m_currentFields.size() > 1) {
                start_edit(m_currentFields[1].first);
            }
            break;

        case key_f3:   // Next record
            break;

        case key_f4:   // Previous record
            break;

        case 'G':
            switch_mode(BrowseMode::Grid);
            break;

        case 'F':
            switch_mode(BrowseMode::Form);
            break;

        case key_escape:
        case 'Q':
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
