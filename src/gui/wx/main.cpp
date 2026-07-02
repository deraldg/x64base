#include "main_frame.hpp"

#include <wx/wx.h>

#include <string>
#include <utility>

namespace {

class DotTalkApp final : public wxApp {
public:
    bool OnInit() override {
        std::filesystem::path initial_table;
        dottalk::gui::LocaleContext locale = dottalk::gui::locale_context_from_environment();

        for (int index = 1; index < argc; ++index) {
            const std::string arg = argv[index].ToStdString();
            if (arg.rfind("--locale=", 0) == 0) {
                locale = dottalk::gui::locale_context_from_message_locale(arg.substr(9));
                continue;
            }
            if (arg == "--locale" && index + 1 < argc) {
                ++index;
                locale = dottalk::gui::locale_context_from_message_locale(argv[index].ToStdString());
                continue;
            }
            if (initial_table.empty()) {
                initial_table = std::filesystem::path(arg);
            }
        }

        auto* frame = new dottalk::gui::wxui::MainFrame(std::move(initial_table), std::move(locale));
        frame->Show(true);
        return true;
    }
};

} // namespace

wxIMPLEMENT_APP(DotTalkApp);
