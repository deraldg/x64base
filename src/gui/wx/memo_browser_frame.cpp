// @dottalk.file v1
// subsystem: gui
// layer: window
// owns: 
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: supported

#include "memo_browser_frame.hpp"

#include "main_frame.hpp"

#include "gui/core/gui_runtime_adapter.hpp"
#include "gui/core/gui_workspace_format.hpp"

#include <wx/button.h>
#include <wx/font.h>
#include <wx/stattext.h>
#include <wx/listctrl.h>
#include <wx/sizer.h>
#include <wx/splitter.h>
#include <wx/statusbr.h>
#include <wx/textctrl.h>

#include <cctype>
#include <cstdint>
#include <string>
#include <vector>

namespace dottalk::gui::wxui {

namespace {

wxString to_wx(const std::string& s) { return wxString::FromUTF8(s.c_str()); }

std::string group_digits(std::uint64_t v) {
    std::string s = std::to_string(v);
    for (int i = static_cast<int>(s.size()) - 3; i > 0; i -= 3) s.insert(static_cast<std::size_t>(i), ",");
    return s;
}

std::vector<MemoWorkspaceRow>& rows() {
    static std::vector<MemoWorkspaceRow> r;
    return r;
}

} // namespace

MemoBrowserFrame::MemoBrowserFrame(wxWindow* parent)
    : wxFrame(parent, wxID_ANY, "Memo workspaces -- what is inside the memo",
              wxDefaultPosition, wxSize(1080, 640)) {
    CreateStatusBar(1);

    auto* split = new wxSplitterWindow(this, wxID_ANY, wxDefaultPosition, wxDefaultSize,
                                       wxSP_LIVE_UPDATE | wxSP_3D);

    list_ = new wxListView(split, wxID_ANY, wxDefaultPosition, wxDefaultSize,
                           wxLC_REPORT | wxLC_SINGLE_SEL);
    list_->AppendColumn("WS_ID",      wxLIST_FORMAT_RIGHT,  60);
    list_->AppendColumn("Name",       wxLIST_FORMAT_LEFT,  190);
    list_->AppendColumn("FMT",        wxLIST_FORMAT_LEFT,  100);
    list_->AppendColumn("SIZE_B",     wxLIST_FORMAT_RIGHT, 100);
    list_->AppendColumn("EST_HYD_B",  wxLIST_FORMAT_RIGHT, 110);
    list_->AppendColumn("Saved",      wxLIST_FORMAT_LEFT,  160);
    list_->AppendColumn("State",      wxLIST_FORMAT_LEFT,   90);

    detail_ = new wxTextCtrl(split, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize,
                             wxTE_MULTILINE | wxTE_READONLY | wxTE_DONTWRAP | wxTE_RICH2);
    detail_->SetFont(wxFont(wxFontInfo(9).Family(wxFONTFAMILY_TELETYPE)));

    split->SplitHorizontally(list_, detail_, 240);
    split->SetMinimumPaneSize(120);

    open_ = new wxButton(this, wxID_ANY, "Open in Workbench");
    plan_ = new wxStaticText(this, wxID_ANY, wxEmptyString);

    auto* bar = new wxBoxSizer(wxHORIZONTAL);
    bar->Add(open_, 0, wxALL, 4);
    bar->Add(plan_, 1, wxALIGN_CENTER_VERTICAL | wxLEFT, 8);

    auto* sizer = new wxBoxSizer(wxVERTICAL);
    sizer->Add(bar, 0, wxEXPAND);
    sizer->Add(split, 1, wxEXPAND);
    SetSizer(sizer);

    open_->Enable(false);   // nothing is selected yet
    open_->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) { OnOpenInWorkbench(); });
    list_->Bind(wxEVT_LIST_ITEM_ACTIVATED, [this](wxListEvent&) { OnOpenInWorkbench(); });

    list_->Bind(wxEVT_LIST_ITEM_SELECTED, [this](wxListEvent&) { ShowSelected(); });

    ReloadCatalog();
}

void MemoBrowserFrame::ReloadCatalog() {
    std::string error;
    rows() = gui_list_memo_workspaces(error);

    list_->DeleteAllItems();
    if (!error.empty()) {
        detail_->SetValue(to_wx(error));
        SetStatusText("catalog unavailable");
        return;
    }

    long i = 0;
    std::uint64_t live = 0;
    for (const auto& r : rows()) {
        list_->InsertItem(i, to_wx(std::to_string(r.ws_id)));
        list_->SetItem(i, 1, to_wx(r.name));
        list_->SetItem(i, 2, to_wx(r.fmt));
        list_->SetItem(i, 3, to_wx(group_digits(r.size_b)));
        // EST_HYD_B reads back 0 when the column is blank. Blank is a real
        // state -- a posture-only payload has no RAM hydration path at all --
        // so it is shown as "--" rather than as a measured zero.
        list_->SetItem(i, 4, r.est_hyd_b ? to_wx(group_digits(r.est_hyd_b))
                                           : wxString("--"));
        list_->SetItem(i, 5, to_wx(r.saved_at));
        list_->SetItem(i, 6, r.superseded ? "superseded" : "live");
        if (!r.superseded) ++live;
        ++i;
    }

    SetStatusText(to_wx(std::to_string(rows().size()) + " row(s), " +
                        std::to_string(live) + " live -- nothing hydrated"));
    if (!rows().empty()) {
        list_->Select(0);
        list_->Focus(0);
    }
}

void MemoBrowserFrame::ShowSelected() {
    const long sel = list_->GetFirstSelected();
    if (sel < 0 || static_cast<std::size_t>(sel) >= rows().size()) return;
    const auto& r = rows()[static_cast<std::size_t>(sel)];

    std::string error;
    const std::string payload = gui_read_memo_payload(r.snapshot, error);
    if (!error.empty()) {
        detail_->SetValue(to_wx("Could not read the memo for '" + r.name + "'.\n\n" + error));
        SetStatusText("memo read failed");
        return;
    }

    const std::string title =
        "WS_ID " + std::to_string(r.ws_id) + " -- " + r.name +
        "   [" + r.fmt + (r.superseded ? ", superseded]" : "]");
    detail_->SetValue(to_wx(format_minidb_container_text(payload, title)));
    {
        std::string why_not;
        const std::string cmd = PlannedCommand(why_not);
        plan_->SetLabel(to_wx(cmd.empty() ? why_not : cmd));
        open_->Enable(!cmd.empty());
    }
    detail_->ShowPosition(0);
    SetStatusText(to_wx(group_digits(payload.size()) + " byte(s) read from the memo -- "
                        "nothing hydrated"));
}

std::string MemoBrowserFrame::PlannedCommand(std::string& why_not) const {
    why_not.clear();
    const long sel = list_ ? list_->GetFirstSelected() : -1;
    if (sel < 0 || static_cast<std::size_t>(sel) >= rows().size()) {
        why_not = "Select a row.";
        return {};
    }
    const auto& r = rows()[static_cast<std::size_t>(sel)];

    // A superseded row cannot be opened, and pretending otherwise would be
    // worse than refusing. fetch_memo_payload resolves by WS_NAME and skips
    // rows where SUPERSEDED = 1, so "WORKSPACE LOAD <name> MEMO" on a
    // superseded row silently loads the LIVE row of the same name -- a
    // different snapshot than the one selected, with no indication.
    if (r.superseded) {
        why_not = "'" + r.name + "' is superseded. WORKSPACE LOAD resolves by name to "
                  "the live row, so this would open a different snapshot than the one "
                  "selected. Opening a superseded snapshot needs a by-WS_ID path that "
                  "does not exist yet.";
        return {};
    }
    if (r.name.empty()) {
        why_not = "This row has no WS_NAME to load by.";
        return {};
    }

    std::string fmt;
    for (char ch : r.fmt) fmt.push_back(static_cast<char>(std::toupper(static_cast<unsigned char>(ch))));

    // MINIDB carries the tables themselves, so it hydrates into the RAM disk.
    // A posture-only payload names tables that must already be on disk; plain
    // MEMO refuses a MINIDB payload by design, which is why the two differ.
    if (fmt.rfind("MINIDB", 0) == 0) {
        return "WORKSPACE LOAD " + r.name + " MEMO RAM";
    }
    return "WORKSPACE LOAD " + r.name + " MEMO";
}

void MemoBrowserFrame::OnOpenInWorkbench() {
    std::string why_not;
    const std::string cmd = PlannedCommand(why_not);
    if (cmd.empty()) {
        if (!why_not.empty()) {
            detail_->SetValue(to_wx(why_not));
            SetStatusText("cannot open this row");
        }
        return;
    }
    auto* owner = dynamic_cast<MainFrame*>(GetParent());
    if (!owner) {
        SetStatusText("no Workbench to open into");
        return;
    }
    owner->SubmitCommandText(cmd);
    owner->Raise();
    SetStatusText(to_wx("sent: " + cmd));
}

} // namespace dottalk::gui::wxui
