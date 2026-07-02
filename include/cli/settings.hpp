#pragma once
#include <atomic>
#include <cstdlib>
#include <string>
#include <cstdint>

namespace cli {

namespace detail {

inline bool default_passive_dev_diagnostics_enabled() {
#if DOTTALK_EXTRA_DIAGNOSTICS
    const char* v = std::getenv("DOTTALK_DEV_DIAGNOSTICS");
    if (!v || !*v) return false;
    const char c = static_cast<char>(*v);
    return !(c == '0' || c == 'n' || c == 'N' || c == 'f' || c == 'F');
#else
    return false;
#endif
}

} // namespace detail

enum class EditorMode {
    Default,
    Custom,
    Off
};

struct EditorSettings {
    EditorMode mode{EditorMode::Default};
    std::string command;
};

// Process-wide runtime settings for CLI / shell behavior.
// Defaults are FoxPro-ish where it makes sense.
struct Settings {
    // ---- Display / Console ----
    std::atomic<bool> talk_on{true};          // SET TALK
    std::atomic<bool> status_on{false};       // SET STATUS
    std::atomic<bool> time_on{false};         // SET TIME
    std::atomic<bool> passive_dev_diagnostics_on{detail::default_passive_dev_diagnostics_enabled()}; // SET DEVDIAG
    std::atomic<bool> timer_on{false};        // SET TIMER
    std::atomic<bool> polling_on{false};      // SET POLLING
    std::atomic<bool> clock_on{false};        // SET CLOCK

    std::atomic<bool> console_on{true};       // SET CONSOLE
    std::atomic<bool> bell_on{false};         // SET BELL

    // ---- Data handling ----
    std::atomic<bool> safety_on{true};        // SET SAFETY
    std::atomic<bool> deleted_on{true};       // SET DELETED (ON => hide deleted)
    std::atomic<bool> exact_on{false};        // SET EXACT
    std::atomic<bool> escape_on{true};        // SET ESCAPE
    std::atomic<bool> carry_on{false};        // SET CARRY
    std::atomic<bool> confirm_on{false};      // SET CONFIRM
    std::atomic<bool> exclusive_on{false};    // SET EXCLUSIVE
    std::atomic<bool> multilocks_on{false};   // SET MULTILOCKS

    // ---- Formatting ----
    std::atomic<bool> century_on{false};      // SET CENTURY
    std::string       date_format = "MDY";    // SET DATE TO ...
    std::uint32_t     decimals{2};            // SET DECIMALS TO n
    std::atomic<bool> fixed_on{false};        // SET FIXED
    std::uint32_t     memo_width{50};         // SET MEMOWIDTH TO n
    std::atomic<bool> memo_error_on{true};    // SET MEMOERROR

    // ---- Search / Relations (stubs for now) ----
    std::string       filter_expr;            // SET FILTER TO <expr>

    // ---- File / Pathing ----
    std::string       default_dir;            // SET DEFAULT TO ...
    std::string       path_list;              // SET PATH TO dir1;dir2;...

    // ---- Printing / Device (stubs) ----
    std::atomic<bool> print_on{false};        // SET PRINT
    std::string       printer_target;         // SET PRINTER TO ...
    std::string       device_target = "SCREEN"; // SET DEVICE TO SCREEN|PRINTER
    std::string       format_file;            // SET FORMAT TO ...
    int               report_behavior{90};    // SET REPORTBEHAVIOR 80|90

    // ---- External editor ----
    EditorSettings    editor;                 // SET EDITOR TO ...

    // ---- Message presentation ----
    std::string       message_locale = "en-US"; // SET LANGUAGE / SET LOCALE

    // ---- Misc ----
    std::uint32_t     typeahead{128};         // SET TYPEAHEAD TO n
    std::uint32_t     reprocess_ms{0};        // SET REPROCESS TO n (ms) or 0=AUTOMATIC

    // Singleton
    static Settings& instance() {
        static Settings s;
        return s;
    }

    static constexpr bool extraDiagnosticsBuiltIn() {
#if DOTTALK_EXTRA_DIAGNOSTICS
        return true;
#else
        return false;
#endif
    }

    static bool devDiagnosticsEnabled() {
        return extraDiagnosticsBuiltIn();
    }

    static bool passiveDevDiagnosticsEnabled() {
        return instance().passive_dev_diagnostics_on.load();
    }

    static void setPassiveDevDiagnostics(bool on) {
        instance().passive_dev_diagnostics_on.store(on);
    }

    // Convenience used elsewhere
    static bool deletedOn() { return instance().deleted_on.load(); }
    static void setDeleted(bool on) { instance().deleted_on.store(on); }
};

} // namespace cli
