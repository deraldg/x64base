// @dottalk.file v1
// subsystem: gui
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: supported

#pragma once

// AIF-120. A window that shows what is inside the memo fields of the
// WORKSPACES catalog, WITHOUT hydrating any of it.
//
// It is a window, not an application: an ordinary wxFrame owned by the running
// Workbench, opened from the Workspace menu and closed like any other. It adds
// no executable and no second process.
//
// Everything it renders comes from two read-only calls in gui/core --
// gui_list_memo_workspaces() and gui_read_memo_payload() -- plus
// format_minidb_container_text(). Nothing here writes, hydrates, or mounts.

#include <wx/frame.h>

class wxListView;
class wxTextCtrl;
class wxStatusBar;

namespace dottalk::gui::wxui {

class MemoBrowserFrame final : public wxFrame {
public:
    explicit MemoBrowserFrame(wxWindow* parent);

private:
    void ReloadCatalog();
    void ShowSelected();

    wxListView* list_ = nullptr;
    wxTextCtrl* detail_ = nullptr;
};

} // namespace dottalk::gui::wxui
