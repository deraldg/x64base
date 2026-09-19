// @dottalk.file v1
// subsystem: gui
// layer: adapter
// owns: generated Workbench host capabilities
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#include "uidef_rt.h"
#include "workbench_catalog.hpp"
#include "workbench_session.hpp"
#include "gui/core/localization.hpp"
#include <wx/listctrl.h>
#include <wx/filedlg.h>
#include <wx/dcclient.h>
#include <wx/dcmemory.h>
#include <wx/filename.h>
#include <wx/textdlg.h>
#include <wx/notebook.h>
#include <wx/dialog.h>
#include <wx/sizer.h>
#include <wx/button.h>
#include <wx/stdpaths.h>
#include <wx/dirdlg.h>
#include <wx/weakref.h>
#include <wx/treectrl.h>
#include <set>
#include <fstream>
#include <future>
#include <map>
#include <sstream>

extern uidef::Runtime* g_rt;
extern std::shared_ptr<uidef::Scope> g_scope;
extern std::map<std::string, int> g_menu_ids;
wxDialog* uidef_create_dialog(const std::string&, wxWindow*);

namespace {
using dottalk::workbench::CatalogSnapshot;
using dottalk::workbench::SavedWorkspace;
using dottalk::workbench::Request;
using dottalk::workbench::Action;
using NavKey = std::pair<std::uint64_t, std::uint64_t>; // workspace, area (0 for workspace)
struct NavData : wxTreeItemData {
    NavKey key;
    explicit NavData(NavKey value) : key(value) {}
};
namespace fs = std::filesystem;
dottalk::workbench::SessionOptions startup_options() {
    dottalk::workbench::SessionOptions options; options.private_session = false;
    for (int i = 1; i < wxTheApp->argc; ++i) {
        const wxString arg(wxTheApp->argv[i]);
        if (arg == "--private-session") options.private_session = true;
        else if (arg == "--data-root" && i + 1 < wxTheApp->argc)
            options.data_root = wxString(wxTheApp->argv[++i]).ToStdWstring();
    }
    if (!options.private_session && options.data_root.empty())
        options.data_root = dottalk::workbench::find_workbench_data_root(
            fs::path(wxStandardPaths::Get().GetExecutablePath().ToStdWstring()), fs::current_path());
    return options;
}
wxString wstr(const std::string& s) { return wxString::FromUTF8(s.data(), s.size()); }
const auto locale = dottalk::gui::locale_context_from_environment();
wxString text(const char* key, const char* fallback) {
    return wstr(dottalk::gui::render_label(key, fallback, locale));
}
template<class T> T* control(wxWindow* root, const char* panel) {
    auto* container = wxWindow::FindWindowByName(panel, root);
    if (auto* value = dynamic_cast<T*>(container)) return value;
    if (container) for (auto* child : container->GetChildren())
        if (auto* value = dynamic_cast<T*>(child)) return value;
    throw std::runtime_error(std::string("Generated document has no control in ") + panel);
}
void columns(wxListCtrl* grid, const std::vector<wxString>& names) {
    grid->ClearAll();
    for (std::size_t i = 0; i < names.size(); ++i)
        grid->InsertColumn(static_cast<long>(i), names[i], wxLIST_FORMAT_LEFT, i ? 260 : 220);
}
void row(wxListCtrl* grid, const std::vector<std::string>& values) {
    if (values.empty()) return;
    const auto n = grid->InsertItem(grid->GetItemCount(), wstr(values.front()));
    for (std::size_t i = 1; i < values.size(); ++i) grid->SetItem(n, static_cast<int>(i), wstr(values[i]));
}
class Workbench : public wxEvtHandler {
    wxFrame* frame_;
    wxTextCtrl* path_;
    wxTextCtrl* filter_;
    wxCheckBox* history_;
    wxListBox* list_;
    wxListCtrl *identity_, *members_, *posture_;
    wxStaticText* status_;
    wxListCtrl* paths_grid_{};
    wxStaticText* paths_note_{};
    bool follow_catalog_{true}, catalog_refresh_queued_{}, paths_smoke_{}, paths_ok_{true};
    unsigned paths_step_{};
    fs::path paths_original_catalog_;
    wxTimer timer_{this};
    std::future<CatalogSnapshot> pending_;
    dottalk::workbench::WorkbenchSession session_;
    std::future<dottalk::workbench::SessionSnapshot> live_pending_;
    dottalk::workbench::SessionSnapshot live_;
    wxTreeCtrl* live_tree_{};
    wxTextCtrl* nav_query_{};
    wxStaticText* nav_note_{};
    std::map<NavKey, wxTreeItemId> nav_items_;
    std::set<std::uint64_t> nav_known_, nav_expanded_;
    std::uint64_t nav_area_{};
    bool rendering_nav_{};
    unsigned navigation_failed_at_{};
    NavKey navigation_stale_{};
    std::unique_ptr<wxMenu> navigation_old_menu_;
    wxListCtrl *live_ws_{}, *live_areas_{}, *live_log_{};
    wxCheckBox *area_all_{}, *area_nested_{};
    wxTextCtrl* area_query_{};
    wxStaticText* area_note_{};
    std::vector<std::size_t> area_visible_;
    std::uint64_t area_highlighted_{};
    bool rendering_areas_{}, navigation_smoke_{}, navigation_ok_{true};
    unsigned navigation_step_{};
    wxListCtrl *table_rows_{}, *table_fields_{};
    wxStaticText* table_note_{};
    std::future<dottalk::workbench::FieldValue> field_pending_;
    std::future<dottalk::workbench::MemoTarget> memo_target_pending_;
    bool store_smoke_{}, store_smoke_ok_{true};
    unsigned store_smoke_step_{};
    fs::path store_image_source_;
    Request edit_request_;
    bool edit_requested_{}, edit_smoke_{}, edit_smoke_ok_{true};
    unsigned edit_smoke_step_{};
    bool null_requested_{}, m3_smoke_{}, m3_ok_{true};
    unsigned m3_step_{};
    std::string m3_error_;
    bool browse_smoke_{}, browse_smoke_ok_{true};
    unsigned browse_smoke_step_{};
    fs::path table_source_;
    fs::path edited_path_;
    bool save_smoke_{}, save_smoke_ok_{true};
    unsigned save_smoke_step_{};
    fs::path saved_path_;
    bool memo_image_smoke_{}, memo_image_ok_{true};
    unsigned memo_image_step_{};
    std::uint64_t memo_parent_{};
    wxStaticText* live_current_{};
    wxCheckBox* recursion_{};
    std::vector<wxString> command_history_;
    std::size_t history_cursor_{};
    wxString command_draft_;
    std::uint64_t live_selected_{};
    bool live_smoke_{};
    unsigned live_smoke_step_{};
    bool live_smoke_ok_{true};
    std::future<dottalk::workbench::ImageTree> image_pending_;
    dottalk::workbench::ImageTree image_tree_;
    wxListBox* image_list_{};
    wxListCtrl* image_info_{};
    std::string image_provenance_;
    std::map<std::string, fs::path> image_exports_;
    std::string exporting_location_;
    bool image_exporting_{}, export_smoke_{}, export_smoke_ok_{true};
    fs::path export_smoke_path_;
    bool image_smoke_{}, image_loading_{}, nested_smoke_{};
    std::string catalog_image_payload_, catalog_image_provenance_;
    bool catalog_flow_smoke_{}, catalog_flow_ok_{true};
    unsigned catalog_flow_step_{};
    std::string catalog_flow_error_;
    std::uint64_t catalog_flow_parent_{};
    bool loadview_smoke_{}, loadview_ok_{true};
    unsigned loadview_step_{};
    bool openload_smoke_{}, openload_ok_{true};
    unsigned openload_step_{};
    std::stop_source stop_;
    CatalogSnapshot snapshot_;
    std::vector<std::size_t> visible_;
    std::uint64_t selected_{};
    fs::path smoke_, capture_;
    bool closing_{}, smoke_done_{};
    unsigned capture_delay_{};
    unsigned ticks_{};
    bool close_while_reading_{};
    bool history_ok_{}, filter_ok_{};
    wxDialog* workflow_dialog_{}; // borrowed only while ShowModal is on the stack
    std::string workflow_prefix_;
    std::function<void(wxDialog*, const std::string&)> modal_probe_;
    bool m1_smoke_{}, m1_ok_{true};
    unsigned m1_step_{}, m1_dialogs_{};
    std::string m1_error_;
    fs::path m1_single_, m1_nested_;
public:
    explicit Workbench(wxFrame* frame) : frame_(frame),
        path_(control<wxTextCtrl>(frame, "PATH_BOX")),
        filter_(control<wxTextCtrl>(frame, "FILTER_BOX")),
        history_(control<wxCheckBox>(frame, "HISTORY_BOX")),
        list_(control<wxListBox>(frame, "LIST_BOX")),
        identity_(control<wxListCtrl>(frame, "IDENTITY")),
        members_(control<wxListCtrl>(frame, "MEMBERS")),
        posture_(control<wxListCtrl>(frame, "POSTURE")),
        status_(control<wxStaticText>(frame, "FOOTER")), session_(startup_options()) {
        frame_->SetMinSize(wxSize(900, 540));
        wxInitAllImageHandlers();
        for (const auto& [id, native_id] : g_menu_ids) {
            frame_->Bind(wxEVT_UPDATE_UI, [this, id](wxUpdateUIEvent& e) {
                bool enabled = !closing_ && !workflow_dialog_ && !live_pending_.valid() && !field_pending_.valid() && !memo_target_pending_.valid();
                if (id.starts_with("MI2_") && id != "MI2_0") enabled = enabled && !live_.areas.empty();
                e.Enable(enabled);
            }, native_id);
        }
        paths_grid_ = control<wxListCtrl>(frame, "PATHS_GRID");
        paths_note_ = control<wxStaticText>(frame, "PATHS_NOTE");
        paths_note_->SetWindowStyleFlag(paths_note_->GetWindowStyleFlag() | wxST_ELLIPSIZE_END | wxST_NO_AUTORESIZE);
        paths_note_->SetMinSize(wxSize(1, -1));
        columns(paths_grid_, {"Path slot", "Directory", "Status"});
        paths_grid_->SetColumnWidth(0, 170); paths_grid_->SetColumnWidth(1, 790); paths_grid_->SetColumnWidth(2, 170);
        paths_grid_->Bind(wxEVT_LIST_ITEM_ACTIVATED, [this](wxListEvent&) { paths_action("edit"); });
        path_->Bind(wxEVT_TEXT, [this](wxCommandEvent&) { follow_catalog_ = false; render_paths(); });
        path_->SetHint(text("gui.catalog.path_hint", "Path to WORKSPACES.dbf"));
        filter_->SetHint(text("gui.catalog.filter_hint", "Filter workspace names or IDs"));
        list_->SetName("Saved workspaces");
        history_->SetLabel(text("gui.catalog.include_history", "Include superseded records"));
        columns(identity_, {text("gui.catalog.property", "Property"), text("gui.catalog.value", "Value")});
        columns(members_, {text("gui.catalog.member", "Member"), text("gui.catalog.bytes", "Bytes"),
                           text("gui.catalog.destination", "Hydration destination")});
        columns(posture_, {text("gui.catalog.line", "Line"), text("gui.catalog.definition", "Saved definition")});
        posture_->SetColumnWidth(0, 70);
        posture_->SetColumnWidth(1, 640);
        members_->SetColumnWidth(0, 330);
        members_->SetColumnWidth(1, 100);
        image_list_ = control<wxListBox>(frame, "IMAGE_LIST");
        image_info_ = control<wxListCtrl>(frame, "IMAGE_INFO");
        columns(image_info_, {"Property / member", "Value"});
        image_list_->Bind(wxEVT_LISTBOX, [this](wxCommandEvent&) { image_selection(); });
        wxWindow::FindWindowByName("IMAGE_TOOLS", frame_)->Disable();
        live_tree_ = control<wxTreeCtrl>(frame, "NAV_TREEBOX");
        live_tree_->SetWindowStyleFlag(wxTR_DEFAULT_STYLE | wxTR_HIDE_ROOT | wxTR_FULL_ROW_HIGHLIGHT);
        nav_query_ = control<wxTextCtrl>(frame, "NAV_FIND");
        nav_query_->SetHint("Find workspace or table");
        nav_note_ = dynamic_cast<wxStaticText*>(wxWindow::FindWindowByName("NAV_NOTE", frame));
        nav_note_->SetMinSize(wxSize(1, -1));
        nav_note_->SetWindowStyleFlag(nav_note_->GetWindowStyleFlag() | wxST_ELLIPSIZE_END | wxST_NO_AUTORESIZE);
        nav_query_->Bind(wxEVT_TEXT, [this](wxCommandEvent&) { if (!closing_) render_navigator(); });
        nav_query_->Bind(wxEVT_CHAR_HOOK, [this](wxKeyEvent& e) {
            if (e.GetKeyCode() == WXK_ESCAPE) nav_query_->SetValue(wxEmptyString);
            else if (e.GetKeyCode() == WXK_DOWN) {
                live_tree_->SetFocus();
                if (!live_tree_->GetSelection().IsOk() && !nav_items_.empty())
                    live_tree_->SelectItem(nav_items_.begin()->second);
            } else e.Skip();
        });
        live_ws_ = control<wxListCtrl>(frame, "LIVE_WS");
        live_areas_ = control<wxListCtrl>(frame, "AREA_GRID");
        area_all_ = control<wxCheckBox>(frame, "AREA_ALLBOX");
        area_nested_ = control<wxCheckBox>(frame, "AREA_NESTBOX"); area_nested_->SetValue(true);
        area_query_ = control<wxTextCtrl>(frame, "AREA_FIND");
        area_query_->SetHint("Find table or workspace name");
        area_note_ = control<wxStaticText>(frame, "AREA_NOTE");
        area_note_->SetWindowStyleFlag(area_note_->GetWindowStyleFlag() | wxST_ELLIPSIZE_END | wxST_NO_AUTORESIZE);
        area_note_->SetMinSize(wxSize(1, -1));
        area_all_->Bind(wxEVT_CHECKBOX, [this](wxCommandEvent&) { render_areas(); });
        area_nested_->Bind(wxEVT_CHECKBOX, [this](wxCommandEvent&) { render_areas(); });
        area_query_->Bind(wxEVT_TEXT, [this](wxCommandEvent&) { render_areas(); });
        live_log_ = control<wxListCtrl>(frame, "LIVE_LOG");
        live_current_ = control<wxStaticText>(frame, "LIVE_CURRENT");
        table_rows_ = control<wxListCtrl>(frame, "TABLE_ROWS");
        table_fields_ = control<wxListCtrl>(frame, "TABLE_FIELDS");
        table_note_ = control<wxStaticText>(frame, "TABLE_NOTE");
        table_note_->SetWindowStyleFlag(table_note_->GetWindowStyleFlag() | wxST_ELLIPSIZE_END | wxST_NO_AUTORESIZE);
        table_note_->SetMinSize(wxSize(1, -1));
        table_fields_->SetMinSize(wxSize(1, 110));
        columns(table_fields_, {"Field", "Type", "Value preview"});
        table_fields_->SetColumnWidth(0, 100); table_fields_->SetColumnWidth(1, 60);
        table_fields_->SetColumnWidth(2, 220);
        table_fields_->SetToolTip("Select a field; F2 edits it. Ctrl+Left/Right changes record; Ctrl+Home/End goes first/last.");
        table_rows_->Bind(wxEVT_LIST_ITEM_SELECTED, [this](wxListEvent&) { table_selection(); });
        table_rows_->Bind(wxEVT_LIST_ITEM_ACTIVATED, [this](wxListEvent&) { table_action("select"); });
        table_fields_->Bind(wxEVT_LIST_ITEM_ACTIVATED, [this](wxListEvent&) { table_action("value"); });
        for (auto* grid : {table_rows_, table_fields_}) grid->Bind(wxEVT_CHAR_HOOK, [this](wxKeyEvent& event) {
            const auto key = event.GetKeyCode();
            if (key == WXK_F2) table_action("edit");
            else if (event.ControlDown() && key == WXK_LEFT) table_action("back");
            else if (event.ControlDown() && key == WXK_RIGHT) table_action("forward");
            else if (event.ControlDown() && key == WXK_HOME) table_action("first");
            else if (event.ControlDown() && key == WXK_END) table_action("last");
            else event.Skip();
        });
        auto* details = dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("LIVE_DETAILS", frame));
        details->Bind(wxEVT_NOTEBOOK_PAGE_CHANGED, [this, details](wxBookCtrlEvent& e) {
            if (e.GetEventObject() == details && details->GetSelection() == 3) table_action("refresh");
            e.Skip();
        });
        recursion_ = control<wxCheckBox>(frame, "RECURSE_BOX");
        auto* command_input = control<wxTextCtrl>(frame, "COMMAND_BOX");
        command_input->SetHint("x64base command or expression - Enter to run (Up/Down: history)");
        command_input->Bind(wxEVT_CHAR_HOOK, [this](wxKeyEvent& e) {
            if ((e.GetKeyCode() == WXK_RETURN || e.GetKeyCode() == WXK_NUMPAD_ENTER) && !e.AltDown() && !e.ControlDown())
                live_action("command");
            else if ((e.GetKeyCode() == WXK_UP || e.GetKeyCode() == WXK_DOWN) && !command_history_.empty()) {
                auto* input = control<wxTextCtrl>(frame_, "COMMAND_BOX");
                if (history_cursor_ == command_history_.size()) command_draft_ = input->GetValue();
                if (e.GetKeyCode() == WXK_UP && history_cursor_) --history_cursor_;
                if (e.GetKeyCode() == WXK_DOWN && history_cursor_ < command_history_.size()) ++history_cursor_;
                input->ChangeValue(history_cursor_ < command_history_.size() ? command_history_[history_cursor_] : command_draft_);
                input->SetInsertionPointEnd();
            }
            else e.Skip();
        });
        columns(live_ws_, {"Property", "Value"});
        columns(live_areas_, {"Workspace", "Table", "Area", "Records"});
        const int area_widths[] = {150, 280, 70, 95};
        for (int column = 0; column < 4; ++column) live_areas_->SetColumnWidth(column, area_widths[column]);
        columns(live_log_, {"Line", "Engine response"});
        live_log_->SetFont(wxFontInfo(10).Family(wxFONTFAMILY_TELETYPE));
        live_log_->SetColumnWidth(0, 55); live_log_->SetColumnWidth(1, 670);
        live_tree_->SetToolTip("Click to browse. Enter or double-click: SWITCH workspace or SELECT table. Right-click for actions. Area numbers are global and zero-based.");
        live_tree_->Bind(wxEVT_TREE_SEL_CHANGED, [this](wxTreeEvent& e) {
            if (rendering_nav_) return;
            const auto key = nav_key(e.GetItem());
            if (!key.first) return;
            live_selected_ = key.first; nav_area_ = key.second;
            if (nav_area_) area_highlighted_ = nav_area_;
            live_selection(); nav_note();
            dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("LIVE_DETAILS", frame_))->ChangeSelection(1);
        });
        live_tree_->Bind(wxEVT_TREE_ITEM_ACTIVATED, [this](wxTreeEvent& e) { nav_activate(nav_key(e.GetItem())); });
        live_tree_->Bind(wxEVT_TREE_ITEM_EXPANDED, [this](wxTreeEvent& e) {
            if (!rendering_nav_ && nav_query_->IsEmpty()) nav_expanded_.insert(nav_key(e.GetItem()).first);
        });
        live_tree_->Bind(wxEVT_TREE_ITEM_COLLAPSED, [this](wxTreeEvent& e) {
            if (!rendering_nav_ && nav_query_->IsEmpty()) nav_expanded_.erase(nav_key(e.GetItem()).first);
        });
        live_tree_->Bind(wxEVT_TREE_ITEM_MENU, [this](wxTreeEvent& e) {
            const auto item = e.GetItem().IsOk() ? e.GetItem() : live_tree_->GetSelection();
            const auto key = nav_key(item);
            if (!key.first) return;
            live_tree_->SelectItem(item);
            auto menu = nav_menu(key); live_tree_->PopupMenu(menu.get());
        });
        live_tree_->Bind(wxEVT_CHAR_HOOK, [this](wxKeyEvent& e) {
            if (e.GetKeyCode() == WXK_RETURN || e.GetKeyCode() == WXK_NUMPAD_ENTER)
                nav_activate(nav_key(live_tree_->GetSelection()));
            else if (e.GetKeyCode() == WXK_F5) live_action("refresh");
            else if ((e.GetKeyCode() == 'F' || e.GetKeyCode() == 'f') && e.ControlDown()) nav_query_->SetFocus();
            else e.Skip(); // native arrows, Home/End and type-ahead
        });
        live_areas_->Bind(wxEVT_LIST_ITEM_SELECTED, [this](wxListEvent& event) {
            const auto index = event.GetIndex();
            if (!rendering_areas_ && index >= 0 && static_cast<std::size_t>(index) < area_visible_.size())
                area_highlighted_ = live_.areas[area_visible_[index]].handle;
        });
        live_areas_->Bind(wxEVT_LIST_ITEM_ACTIVATED, [this](wxListEvent&) { live_action("area"); });
        recursion_->Bind(wxEVT_CHECKBOX, [this](wxCommandEvent&) {
            Request r; r.action = Action::Recursion; r.enabled = recursion_->GetValue(); submit_live(r);
        });
        auto* main_pages = dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame));
        if (main_pages) main_pages->Bind(wxEVT_NOTEBOOK_PAGE_CHANGED, [this, main_pages](wxBookCtrlEvent& e) {
            if (e.GetEventObject() == main_pages) {
                if (main_pages->GetSelection() == 0) selection();
                else if (main_pages->GetSelection() == 2) image_selection(); else live_status();
            }
            e.Skip();
        });
        Bind(wxEVT_TIMER, [this](wxTimerEvent&) { poll(); });
        list_->Bind(wxEVT_LISTBOX, [this](wxCommandEvent&) { selection(); });
        filter_->Bind(wxEVT_TEXT, [this](wxCommandEvent&) { rebuild(); });
        history_->Bind(wxEVT_CHECKBOX, [this](wxCommandEvent&) { rebuild(); });
        frame_->Bind(wxEVT_CLOSE_WINDOW, [this](wxCloseEvent& e) {
            if (workflow_dialog_) { workflow_dialog_->EndModal(wxID_CANCEL); e.Veto(); return; }
            if (!closing_ && e.CanVeto() && (live_pending_.valid() || field_pending_.valid() || memo_target_pending_.valid() || live_.dirty_areas)) {
                live_current_->SetLabel(live_pending_.valid() || field_pending_.valid() || memo_target_pending_.valid() ? "Wait for the running command before closing." :
                    "Commit or roll back buffered table edits before closing.");
                e.Veto(); return;
            }
            shutdown(); e.Skip();
        });
        for (int i = 1; i < wxTheApp->argc; ++i) {
            const wxString arg(wxTheApp->argv[i]);
            if (arg == "--catalog" && i + 1 < wxTheApp->argc) { follow_catalog_ = false; path_->ChangeValue(wxTheApp->argv[++i]); }
            else if (arg == "--smoke" && i + 1 < wxTheApp->argc) smoke_ = wxString(wxTheApp->argv[++i]).ToStdWstring();
            else if (arg == "--capture" && i + 1 < wxTheApp->argc) capture_ = wxString(wxTheApp->argv[++i]).ToStdWstring();
            else if (arg == "--close-during-read") close_while_reading_ = true;
            else if (arg == "--live-smoke") live_smoke_ = true;
            else if (arg == "--browse-smoke") browse_smoke_ = true;
            else if (arg == "--edit-smoke") edit_smoke_ = true;
            else if (arg == "--save-smoke") save_smoke_ = true;
            else if (arg == "--memo-image-smoke") memo_image_smoke_ = true;
            else if (arg == "--export-image-smoke") export_smoke_ = true;
            else if (arg == "--store-image-smoke") store_smoke_ = true;
            else if (arg == "--paths-smoke") paths_smoke_ = true;
            else if (arg == "--loadview-smoke") loadview_smoke_ = true;
            else if (arg == "--openload-smoke") openload_smoke_ = true;
            else if (arg == "--m1-smoke") m1_smoke_ = true;
            else if (arg == "--m3-smoke") m3_smoke_ = true;
            else if (arg == "--catalog-flow-smoke") catalog_flow_smoke_ = true;
            else if (arg == "--navigation-smoke") navigation_smoke_ = true;
            else if (arg == "--image-source" && i + 1 < wxTheApp->argc) store_image_source_ = wxString(wxTheApp->argv[++i]).ToStdWstring();
            else if (arg == "--table-source" && i + 1 < wxTheApp->argc) table_source_ = wxString(wxTheApp->argv[++i]).ToStdWstring();
            else if (arg == "--image-smoke") image_smoke_ = true;
            else if (arg == "--nested-smoke") { nested_smoke_ = true; image_smoke_ = true; }
        }
        timer_.Start(50);
        submit_live({});
        if (!path_->IsEmpty()) refresh();
    }
    ~Workbench() override { shutdown(); }
    void shutdown() {
        if (closing_) return;
        closing_ = true;
        // wxTreeCtrl emits selection/collapse notifications as its items die.
        // Sibling controls may already be gone; none may refresh the browser.
        rendering_nav_ = true;
        timer_.Stop();
        stop_.request_stop();
        session_.shutdown();
        // Worker touches only its owned copies and result. No callback into widgets.
        if (pending_.valid()) pending_.wait();
        if (g_scope) g_scope->destroy();
        delete g_rt;
        g_rt = nullptr;
    }
    fs::path live_path(const std::string& name) const {
        for (const auto& entry : live_.paths) if (entry.slot == name) return entry.value;
        return {};
    }
    void sync_catalog() {
        if (!follow_catalog_ || live_.default_catalog.empty()) return;
        const fs::path shown(path_->GetValue().ToStdWstring());
        if (shown == live_.default_catalog) return;
        path_->ChangeValue(wstr(live_.default_catalog.string()));
        if (pending_.valid()) catalog_refresh_queued_ = true; else refresh();
    }
    void render_paths() {
        if (auto* button = wxWindow::FindWindowByName("OPEN_WS", frame_)) button->SetToolTip(wstr(
            "WORKSPACE OPEN dbf: open tables in the current workspace from " + live_path("DBF").string()));
        if (auto* button = wxWindow::FindWindowByName("LOAD_WS", frame_)) button->SetToolTip(wstr(
            "WORKSPACE LOAD: choose a saved definition from " + live_path("WORKSPACES").string()));
        if (auto* button = wxWindow::FindWindowByName("SCRIPT_RUN", frame_)) button->SetToolTip(wstr(
            "DO: choose an exact script from " + live_path("SCRIPTS").string()));
        const auto selected = paths_grid_->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
        const auto selected_name = selected < 0 ? wxString{} : paths_grid_->GetItemText(selected);
        paths_grid_->Freeze(); paths_grid_->DeleteAllItems();
        for (const auto& entry : live_.paths) {
            row(paths_grid_, {entry.slot, entry.value.string(), entry.exists ? "Available" : "Not a directory"});
            if (wstr(entry.slot) == selected_name)
                paths_grid_->SetItemState(paths_grid_->GetItemCount() - 1, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED);
        }
        paths_grid_->Thaw();
        const auto note = "Default catalog: " + live_.default_catalog.string() +
            (follow_catalog_ ? " | Saved catalogs follows this path" : " | Saved catalogs uses your chosen file");
        paths_note_->SetLabel(wstr(note)); paths_note_->SetToolTip(wstr(note));
    }
    void paths_action(const std::string& action) {
        if (closing_ || live_pending_.valid() || field_pending_.valid() || memo_target_pending_.valid()) return;
        auto* pages = dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_));
        if (action == "show") { pages->SetSelection(3); return; }
        if (action == "catalog") {
            follow_catalog_ = true; sync_catalog(); render_paths();
            pages->SetSelection(0); return;
        }
        Request r;
        if (action == "edit") {
            const auto selected = paths_grid_->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
            if (selected < 0 || static_cast<std::size_t>(selected) >= live_.paths.size()) {
                status_->SetLabel("Select a path slot to change."); return;
            }
            const auto& entry = live_.paths[selected];
            wxTextEntryDialog dialog(frame_, "Directory (relative paths follow native SET PATH rules)",
                wstr("SET PATH " + entry.slot), wstr(entry.value.string()));
            if (dialog.ShowModal() != wxID_OK) return;
            r.action = Action::SetPath; r.name = entry.slot; r.path = fs::path(dialog.GetValue().ToStdWstring());
        } else if (action == "reset" || action == "init") {
            r.action = Action::Command; r.name = action == "reset" ? "SET PATH RESET" : "INIT";
        }
        submit_live(std::move(r));
    }
    void choose() {
        wxFileDialog dialog(frame_, text("gui.catalog.choose", "Choose workspace catalog"),
            wstr(live_path("WORKSPACES").string()), "WORKSPACES.dbf", "DBF catalogs (*.dbf)|*.dbf", wxFD_OPEN | wxFD_FILE_MUST_EXIST);
        if (dialog.ShowModal() == wxID_OK) { follow_catalog_ = false; path_->ChangeValue(dialog.GetPath()); render_paths(); refresh(); }
    }
    void refresh() {
        if (closing_ || pending_.valid()) return;
        if (path_->IsEmpty()) { choose(); return; }
        stop_ = std::stop_source{};
        const fs::path input(path_->GetValue().ToStdWstring());
        const auto token = stop_.get_token();
        status_->SetLabel(text("gui.catalog.reading", "Reading a private catalog snapshot..."));
        path_->Disable();
        pending_ = session_.inspect(input, token);
        if (close_while_reading_) {
            shutdown();
            std::ofstream out(smoke_);
            out << "PASS close during read: cancellation requested, worker joined\n";
            frame_->CallAfter([frame = frame_] { frame->Close(); });
        }
    }
    void view_action(const std::string& action) {
        if (closing_ || workflow_dialog_) return;
        auto* main = dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_));
        if (action == "exit") { frame_->Close(); return; }
        if (action == "about" || action == "help") {
            wxMessageBox(action == "about" ? "ArcticTalk Workbench\nGenerated UIDEF / native x64base session" :
                "New creates and enters a workspace. Open loads a directory of tables.\n"
                "Load restores a saved definition. Save writes a new database image.\n\n"
                "SWITCH changes workspace; SELECT 0 or SELECT students selects a table.\n"
                "Areas are numbered from zero across the session.\n\n"
                "Use Paths and defaults for native directories. Commit or roll back\n"
                "table edits before saving. Ctrl+K focuses the command input.",
                action == "about" ? "About ArcticTalk" : "Workbench help", wxOK | wxICON_INFORMATION, frame_);
            return;
        }
        main->SetSelection(action == "catalogs" ? 0 : action == "images" ? 2 : 1);
        if (action == "command") control<wxTextCtrl>(frame_, "COMMAND_BOX")->SetFocus();
    }
    void workflow_browse(const std::string& kind = {}) {
        if (!workflow_dialog_) return;
        if (kind == "tables" || kind == "indexes") {
            auto* root = dynamic_cast<wxTextCtrl*>(wxWindow::FindWindowByName(kind == "tables" ? "LD_DBF" : "LD_IDX", workflow_dialog_));
            if (!root) return;
            wxDirDialog picker(workflow_dialog_, kind == "tables" ? "Choose table directory" : "Choose index directory",
                               root->GetValue(), wxDD_DEFAULT_STYLE | wxDD_DIR_MUST_EXIST);
            if (picker.ShowModal() == wxID_OK) root->ChangeValue(picker.GetPath());
            root->SetFocus(); return;
        }
        auto* value = dynamic_cast<wxTextCtrl*>(wxWindow::FindWindowByName(wstr(workflow_prefix_ + "_VALUE"), workflow_dialog_));
        if (workflow_prefix_ == "OPEN") {
            wxDirDialog picker(workflow_dialog_, "Choose table directory", value->GetValue(), wxDD_DEFAULT_STYLE | wxDD_DIR_MUST_EXIST);
            if (picker.ShowModal() == wxID_OK) value->ChangeValue(picker.GetPath());
        } else {
            const bool save = workflow_prefix_ == "SAVE";
            const bool script = workflow_prefix_ == "RUN";
            const fs::path path(value->GetValue().ToStdWstring());
            const bool directory = fs::is_directory(path);
            wxFileDialog picker(workflow_dialog_, save ? "Choose a new image file" : script ? "Choose script" : "Choose workspace definition",
                wstr(directory ? path.string() : path.parent_path().string()), directory ? wxString{} : wstr(path.filename().string()),
                save ? "MINIDB images (*.minidb)|*.minidb" : script ? "DotTalk scripts (*.dts)|*.dts" : "Workspace definitions (*.dtschema;*.dtschemas)|*.dtschema;*.dtschemas",
                save ? wxFD_SAVE : wxFD_OPEN | wxFD_FILE_MUST_EXIST);
            if (picker.ShowModal() == wxID_OK) value->ChangeValue(picker.GetPath());
        }
        value->SetFocus();
    }
    bool workflow(const std::string& action, Request& request) {
        const auto prefix = action == "hydrate" ? "HYD" : action == "new" || action == "child" ? "NEW" : action == "open_workspace" ? "OPEN" : action == "load_workspace" ? "LOAD" : action == "run_script" ? "RUN" : "SAVE";
        request.expected_workspace = live_.desk.current_handle;
        request.workspace = action == "child" ? live_selected_ : (action == "save" ? live_.desk.current_handle : 0);
        request.action = action == "hydrate" ? Action::Hydrate : prefix == std::string("NEW") ? Action::NewWorkspace : prefix == std::string("OPEN") ? Action::OpenWorkspace : prefix == std::string("LOAD") ? Action::LoadWorkspace : prefix == std::string("RUN") ? Action::RunScript : Action::SaveImage;
        wxWeakRef<wxWindow> focus(wxWindow::FindFocus());
        auto dialog = std::unique_ptr<wxDialog>(uidef_create_dialog(std::string(prefix) + "_FORM", frame_));
        workflow_dialog_ = dialog.get(); workflow_prefix_ = prefix;
        auto find = [&](const char* suffix) { return wxWindow::FindWindowByName(wstr(workflow_prefix_ + suffix), dialog.get()); };
        auto* value = dynamic_cast<wxTextCtrl*>(find("_VALUE"));
        auto* error = dynamic_cast<wxStaticText*>(find("_ERROR"));
        auto* dest = dynamic_cast<wxStaticText*>(find("_DEST"));
        std::string name;
        const auto target = action == "child" ? live_selected_ : live_.desk.current_handle;
        for (const auto& ws : live_.desk.workspaces) if (ws.handle == target) name = ws.name;
        dest->SetLabel(wstr(action == "new" ? "Destination: new root workspace" : action == "child" ? "Parent workspace: " + name : "Current workspace: " + name));
        error->SetForegroundColour(wxColour(160, 25, 25));
        if (request.action == Action::Hydrate) {
            value->ChangeValue(wstr(request.name));
            auto* note = dynamic_cast<wxStaticText*>(find("_NOTE"));
            note->SetLabel(wstr(request.provenance + "\nTables and indexes go into RAM; memo sidecars remain on disk.")); note->Wrap(650);
            auto* child = dynamic_cast<wxCheckBox*>(find("_CHILD"));
            auto destination = [=, this] {
                dest->SetLabel(wstr(child->GetValue() ? "Parent workspace: " + name : "Destination: new root workspace"));
            };
            destination(); child->Bind(wxEVT_CHECKBOX, [destination](wxCommandEvent&) { destination(); });
        }
        if (request.action == Action::OpenWorkspace) value->ChangeValue(wstr(live_path("DBF").string()));
        if (request.action == Action::LoadWorkspace) {
            value->ChangeValue(wstr((live_path("WORKSPACES") / "workspace.dtschema").string()));
            dynamic_cast<wxTextCtrl*>(wxWindow::FindWindowByName("LD_DBF", dialog.get()))->ChangeValue(wstr(live_path("DBF").string()));
            dynamic_cast<wxTextCtrl*>(wxWindow::FindWindowByName("LD_IDX", dialog.get()))->ChangeValue(wstr(live_path("INDEXES").string()));
            if (!request.payload.empty()) {
                value->ChangeValue(wstr(request.provenance)); value->SetEditable(false);
                find("_PICK")->Hide();
                dynamic_cast<wxStaticText*>(find("_LABEL"))->SetLabel("Selected saved snapshot (exact version)");
            }
        }
        if (request.action == Action::RunScript) value->ChangeValue(wstr(live_path("SCRIPTS").string()));
        if (request.action == Action::SaveImage) {
            value->ChangeValue(wstr((live_path("WORKSPACES") / (name + ".minidb")).string()));
            dynamic_cast<wxCheckBox*>(find("_NESTED"))->SetValue(recursion_->GetValue());
            dest->SetLabel(wstr("Source workspace: " + name));
        }
        bool accepted = false;
        dialog->Bind(wxEVT_BUTTON, [&](wxCommandEvent&) {
            if (accepted) return;
            try {
                if (live_.desk.current_handle != request.expected_workspace) throw std::runtime_error("Workspace changed. Cancel and reopen this form.");
                const auto input = value->GetValue().Strip(wxString::both);
                if (input.empty()) throw std::runtime_error("Enter a value before continuing.");
                if (request.action == Action::NewWorkspace || request.action == Action::Hydrate) {
                    request.name = input.ToStdString();
                    if (request.name.size() > 32 || !std::isalpha(static_cast<unsigned char>(request.name.front())) ||
                        request.name.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_") != std::string::npos)
                        throw std::runtime_error("Start with a letter; use letters, digits or underscore (up to 32).");
                    for (const auto& ws : live_.desk.workspaces)
                        if (wstr(ws.name).CmpNoCase(input) == 0) throw std::runtime_error("A workspace with that name already exists.");
                    if (request.action == Action::Hydrate)
                        request.workspace = dynamic_cast<wxCheckBox*>(find("_CHILD"))->GetValue() ? request.expected_workspace : 0;
                } else {
                    if (request.payload.empty()) request.path = fs::path(input.ToStdWstring());
                    if (request.payload.empty() && !request.path.is_absolute()) throw std::runtime_error("Choose a full path, starting from the native default directory.");
                    if (request.action == Action::OpenWorkspace && !fs::is_directory(request.path)) throw std::runtime_error("Choose an existing table directory.");
                    if (request.action == Action::LoadWorkspace) {
                        const auto extension = wstr(request.path.extension().string()).Lower();
                        if (request.payload.empty() && (!fs::is_regular_file(request.path) || (extension != ".dtschema" && extension != ".dtschemas")))
                            throw std::runtime_error("Choose an existing .dtschema or .dtschemas file.");
                        request.table_root = fs::path(dynamic_cast<wxTextCtrl*>(wxWindow::FindWindowByName("LD_DBF", dialog.get()))->GetValue().Strip().ToStdWstring());
                        request.index_root = fs::path(dynamic_cast<wxTextCtrl*>(wxWindow::FindWindowByName("LD_IDX", dialog.get()))->GetValue().Strip().ToStdWstring());
                        if (!request.table_root.is_absolute() || !request.index_root.is_absolute())
                            throw std::runtime_error("Choose full table and index directory paths.");
                        const auto check = session_.check_workspace(request.path, request.table_root, request.payload).get();
                        if (!check.error.empty()) throw std::runtime_error(check.error);
                        if (!check.missing.empty()) throw std::runtime_error(std::to_string(check.missing.size()) + " of " +
                            std::to_string(check.declared) + " tables are missing. Choose their table directory.\nFirst: " + check.missing.front());
                    }
                    if (request.action == Action::RunScript && (!fs::is_regular_file(request.path) ||
                        wstr(request.path.extension().string()).Lower() != ".dts"))
                        throw std::runtime_error("Choose an existing .dts script.");
                    if (request.action == Action::SaveImage) {
                        if (fs::exists(request.path)) throw std::runtime_error("That file exists. Choose a new image filename.");
                        if (!fs::is_directory(request.path.parent_path())) throw std::runtime_error("Choose an existing destination directory.");
                        if (wstr(request.path.extension().string()).Lower() != ".minidb") throw std::runtime_error("Use the .minidb extension for an image.");
                        request.include_nested = dynamic_cast<wxCheckBox*>(find("_NESTED"))->GetValue();
                    }
                }
                accepted = true; dialog->EndModal(wxID_OK);
            } catch (const std::exception& e) { error->SetLabel(wstr(e.what())); error->Wrap(650); dialog->Fit(); dialog->Layout(); value->SetFocus(); }
        }, wxID_OK);
        dialog->Layout(); value->SetFocus();
        // Verification drives the actual generated dialog inside its modal loop.
        if (modal_probe_) dialog->CallAfter([this] { modal_probe_(workflow_dialog_, workflow_prefix_); });
        else if (openload_smoke_) dialog->CallAfter([&, this] {
            if (request.action == Action::LoadWorkspace) value->ChangeValue(wstr((live_path("WORKSPACES") / "Button load & sample.dtschema").string()));
            wxCommandEvent event(wxEVT_BUTTON, wxID_OK); dialog->GetEventHandler()->ProcessEvent(event);
        });
        const int result = dialog->ShowModal();
        workflow_dialog_ = nullptr; workflow_prefix_.clear();
        dialog.reset(); // scopes die here, after the nested event loop has exited
        if (focus && focus->IsEnabled() && focus->IsShownOnScreen()) focus->SetFocus();
        if (result != wxID_OK || !accepted) { status_->SetLabel("Cancelled. Workspace and tables unchanged."); return false; }
        return true;
    }
    void catalog_action(const std::string& action) {
        if (closing_ || workflow_dialog_ || pending_.valid() || live_pending_.valid() || image_pending_.valid() ||
            field_pending_.valid() || memo_target_pending_.valid()) return;
        const auto selected = list_->GetSelection();
        if (selected < 0 || static_cast<std::size_t>(selected) >= visible_.size()) return;
        const auto saved = snapshot_.entries[visible_[selected]];
        const bool hydrate = action == "hydrate";
        if (saved.action() != (hydrate ? dottalk::workbench::CatalogAction::Hydrate : dottalk::workbench::CatalogAction::LoadDefinition)) {
            status_->SetLabel(wstr(saved.action_note())); return;
        }
        Request request;
        request.payload = saved.payload;
        request.provenance = snapshot_.path.string() + " / saved ID " + std::to_string(saved.id) + " / " +
            saved.value("WS_NAME") + (saved.superseded ? " (historical version)" : "");
        request.name = saved.value("WS_NAME").substr(0, 24) + "_ram";
        if (!workflow(hydrate ? "hydrate" : "load_workspace", request)) return;
        image_loading_ = hydrate;
        if (hydrate) { catalog_image_payload_ = request.payload; catalog_image_provenance_ = request.provenance; }
        dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_))->SetSelection(1);
        dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("LIVE_DETAILS", frame_))->SetSelection(2);
        submit_live(std::move(request));
    }
    void live_action(const std::string& action) {
        if (closing_ || workflow_dialog_ || live_pending_.valid() || field_pending_.valid() || memo_target_pending_.valid()) return;
        Request r;
        if (action == "new" || action == "child" || action == "open_workspace" || action == "load_workspace" || action == "save" || action == "run_script") {
            if (action == "child" && !live_selected_) return;
            if (!workflow(action, r)) return;
            dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_))->SetSelection(1);
            dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("LIVE_DETAILS", frame_))->SetSelection(2);
        } else if (action == "switch") {
            r.action = Action::SwitchWorkspace; r.workspace = live_selected_;
        } else if (action == "open") {
            wxFileDialog dialog(frame_, "Open a private copy in the current workspace", wstr(live_path("DBF").string()),
                wxEmptyString, "DBF tables (*.dbf)|*.dbf", wxFD_OPEN | wxFD_FILE_MUST_EXIST);
            if (dialog.ShowModal() != wxID_OK) return;
            r.action = Action::OpenCopy; r.path = fs::path(dialog.GetPath().ToStdWstring());
        } else if (action == "close") r.action = Action::CloseWorkspace;
        else if (action == "command") {
            r.action = Action::Command; r.name = control<wxTextCtrl>(frame_, "COMMAND_BOX")->GetValue().ToStdString();
            if (r.name.empty()) return;
            const auto line = wstr(r.name);
            if (command_history_.empty() || command_history_.back() != line) command_history_.push_back(line);
            if (command_history_.size() > 200) command_history_.erase(command_history_.begin());
            history_cursor_ = command_history_.size(); command_draft_.clear();
            auto* pages = dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("LIVE_DETAILS", frame_));
            if (pages) pages->SetSelection(2);
        }
        else if (action == "area") {
            const auto item = live_areas_->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
            if (item < 0 || static_cast<std::size_t>(item) >= area_visible_.size()) {
                auto* pages = dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("LIVE_DETAILS", frame_));
                if (pages) pages->SetSelection(1);
                live_current_->SetLabel("Select a row in Tables, then choose SELECT area."); return;
            }
            const auto& area = live_.areas[area_visible_[item]];
            r.action = Action::SelectArea; r.slot = area.slot; r.area_handle = area.handle;
        }
        submit_live(std::move(r));
    }
    void image_action(const std::string& action) {
        if (closing_ || image_pending_.valid() || live_pending_.valid() || field_pending_.valid() || memo_target_pending_.valid()) return;
        if (action == "tables") { show_live_tables(); return; }
        if (action == "saved") {
            dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_))->SetSelection(0);
            status_->SetLabel("Select a saved MINIDB, then choose Inspect image."); return;
        }
        if (action == "open") {
            wxFileDialog dialog(frame_, "Open a MINIDB image", wstr(live_path("WORKSPACES").string()), wxEmptyString,
                "MINIDB images (*.minidb)|*.minidb|All files (*.*)|*.*", wxFD_OPEN | wxFD_FILE_MUST_EXIST);
            if (dialog.ShowModal() == wxID_OK) open_image(fs::path(dialog.GetPath().ToStdWstring()));
            return;
        }
        if (action == "inspect") {
            const auto selected = list_->GetSelection();
            if (selected < 0 || static_cast<std::size_t>(selected) >= visible_.size()) return;
            const auto& saved = snapshot_.entries[visible_[selected]];
            if (!saved.container.ok) { status_->SetLabel("Select a valid MINIDB image in Saved catalogs."); return; }
            image_provenance_ = snapshot_.path.string() + " / saved ID " + std::to_string(saved.id) + " / " + saved.value("WS_NAME");
            image_list_->Clear(); image_info_->DeleteAllItems(); image_tree_ = {}; image_exports_.clear();
            wxWindow::FindWindowByName("IMAGE_TOOLS", frame_)->Disable();
            image_pending_ = session_.inspect_image(saved.payload, stop_.get_token());
            dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_))->SetSelection(2);
            status_->SetLabel("Inspecting nested DTX objects in private copies...");
            return;
        }
        const auto selected = image_list_->GetSelection();
        if (selected < 0 || static_cast<std::size_t>(selected) >= image_tree_.nodes.size()) {
            status_->SetLabel(wstr(image_tree_.error.empty() ? "Select a saved MINIDB and choose Inspect image." : image_tree_.error));
            return;
        }
        const auto& image = image_tree_.nodes[selected];
        if (!image.scan.ok) return;
        if (action == "export") {
            fs::path destination;
            if (export_smoke_) destination = export_smoke_path_ = live_.home / "GUI exported child.minidb";
            else {
                wxFileDialog dialog(frame_, "Export selected image to a new file", wxEmptyString,
                    image.depth ? "nested-image.minidb" : "database-image.minidb",
                    "MINIDB images (*.minidb)|*.minidb|All files (*.*)|*.*", wxFD_SAVE);
                if (dialog.ShowModal() != wxID_OK) return;
                destination = fs::path(dialog.GetPath().ToStdWstring());
            }
            Request r; r.action = Action::ExportImage; r.path = std::move(destination); r.payload = image.payload;
            r.provenance = image_provenance_ + " / " + image.location;
            exporting_location_ = image.location; image_exporting_ = true;
            wxWindow::FindWindowByName("IMAGE_TOOLS", frame_)->Disable();
            status_->SetLabel("Exporting the selected image's exact bytes...");
            submit_live(std::move(r)); return;
        }
        std::string name;
        if (image_smoke_ || save_smoke_ || memo_image_smoke_) name = "LoadedImage";
        else {
            wxTextEntryDialog dialog(frame_, "Name for the new workspace", "Hydrate selected image");
            if (dialog.ShowModal() != wxID_OK) return;
            name = dialog.GetValue().ToStdString();
        }
        Request r; r.action = Action::Hydrate; r.name = name; r.payload = image.payload;
        r.provenance = image_provenance_ + " / " + image.location;
        if (action == "child") r.workspace = live_.desk.current_handle;
        image_loading_ = true;
        wxWindow::FindWindowByName("IMAGE_TOOLS", frame_)->Disable();
        status_->SetLabel("Hydrating selected image in the Workbench process...");
        submit_live(std::move(r));
    }
private:
    void show_live_tables() {
        live_selected_ = live_.desk.current_handle; nav_area_ = 0;
        area_all_->SetValue(true); area_query_->ChangeValue(wxEmptyString);
        render_live();
        dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_))->SetSelection(1);
        dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("LIVE_DETAILS", frame_))->SetSelection(1);
        live_status();
    }
    void show_command_images() {
        image_tree_ = {}; image_exports_.clear(); image_list_->Clear();
        image_provenance_ = live_.command_images.size() == 1 ? live_.command_images.front().tree.provenance :
            "Workbench command | " + std::to_string(live_.command_images.size()) + " materialized MINIDB images";
        std::size_t opened = 0;
        for (auto& loaded : live_.command_images) {
            if (!loaded.tree.error.empty()) image_tree_.error += loaded.tree.error + " ";
            opened += loaded.opened_areas.size();
            for (auto& node : loaded.tree.nodes) {
                node.location = loaded.name + " / " + node.location;
                image_tree_.nodes.push_back(std::move(node));
            }
        }
        image_tree_.source_label = std::to_string(opened) + " tables opened at load time; View live tables shows current state";
        for (const auto& node : image_tree_.nodes) image_list_->Append(wstr(std::string(node.depth * 2, ' ') + node.location));
        if (!image_tree_.nodes.empty()) image_list_->SetSelection(0);
        dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_))->SetSelection(2);
        image_selection();
    }
    void save_image(fs::path path) {
        Request r; r.action = Action::SaveImage; r.workspace = live_.desk.current_handle; r.path = std::move(path);
        dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("LIVE_DETAILS", frame_))->ChangeSelection(2);
        submit_live(std::move(r));
    }
    void open_image(fs::path path) {
        if (closing_ || image_pending_.valid() || live_pending_.valid() || field_pending_.valid() || memo_target_pending_.valid()) return;
        image_provenance_ = path.string(); image_tree_ = {}; image_exports_.clear();
        image_list_->Clear(); image_info_->DeleteAllItems();
        wxWindow::FindWindowByName("IMAGE_TOOLS", frame_)->Disable();
        image_pending_ = session_.inspect_image_file(std::move(path), stop_.get_token());
        dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_))->SetSelection(2);
        status_->SetLabel("Opening image and inspecting nested DTX objects...");
    }
    void image_selection() {
        image_info_->DeleteAllItems();
        control<wxStaticText>(frame_, "IMAGE_HEAD")->SetLabel(wstr(
            std::to_string(live_.areas.size()) + " open tables in this session | Images are saved payloads; View live tables opens current data."));
        const auto selected = image_list_->GetSelection();
        if (selected < 0 || static_cast<std::size_t>(selected) >= image_tree_.nodes.size()) {
            wxWindow::FindWindowByName("IMAGE_TOOLS", frame_)->Disable();
            row(image_info_, {"Image", "No image selected"});
            row(image_info_, {"Live tables", std::to_string(live_.areas.size()) + " open; choose View live tables"});
            row(image_info_, {"Directory loads", "WORKSPACE OPEN dbf opens tables in Live session"});
            row(image_info_, {"Saved images", "Choose saved image, then Inspect image; or open an image file"});
            image_info_->SetColumnWidth(1, std::max(300, image_info_->GetClientSize().GetWidth() - 230));
            status_->SetLabel(wstr(image_tree_.error.empty() ? "No image selected. Open tables are available through View live tables." : image_tree_.error));
            return;
        }
        const auto& image = image_tree_.nodes[selected];
        row(image_info_, {"Source", image_provenance_});
        image_info_->SetToolTip(wstr(image_provenance_));
        if (!image_tree_.source_label.empty()) row(image_info_, {"Load / source", image_tree_.source_label});
        row(image_info_, {"Location", image.location});
        row(image_info_, {"Nested depth", std::to_string(image.depth)});
        row(image_info_, {"Payload bytes", std::to_string(image.payload.size())});
        if (const auto it = image_exports_.find(image.location); it != image_exports_.end()) {
            row(image_info_, {"Last export", it->second.filename().string()});
            row(image_info_, {"Export folder", it->second.parent_path().string()});
            image_info_->SetToolTip(wstr(image_provenance_ + "\nExport: " + it->second.string()));
        }
        row(image_info_, {"RAM member bytes", std::to_string(image.scan.ram_file_bytes)});
        row(image_info_, {"Disk memo bytes", std::to_string(image.scan.sidecar_file_bytes)});
        row(image_info_, {"Scope", "Live DTX objects; DBF row references are not inferred"});
        row(image_info_, {"Hydrate buttons", "Load another copy in a new workspace"});
        if (!image.error.empty()) row(image_info_, {"Inspection note", image.error});
        for (const auto& file : image.scan.files)
            row(image_info_, {file.relpath, std::to_string(file.length) +
                (dottalk::minidb::is_memo_sidecar(file.relpath) ? " bytes / disk memo" : " bytes / RAM")});
        image_info_->SetColumnWidth(0, 185);
        image_info_->SetColumnWidth(1, std::max(300, image_info_->GetClientSize().GetWidth() - 195));
        wxWindow::FindWindowByName("IMAGE_TOOLS", frame_)->Enable(image.scan.ok && !live_pending_.valid());
        status_->SetLabel(wstr(image_tree_.error.empty() ? std::to_string(image_tree_.nodes.size()) +
            " images inspected | Limits: 8 nested levels, 128 images, 128 MiB" : "Partial inspection: " + image_tree_.error));
    }
    void live_status() {
        auto* pages = dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_));
        if (pages && pages->GetSelection() == 3) {
            status_->SetLabel(wstr("Paths and defaults | " + std::to_string(live_.paths.size()) + " native path slots | Changes apply to this session"));
        }
        if (pages && pages->GetSelection() == 1)
            status_->SetLabel(wstr("Live session | " + std::to_string(live_.desk.workspace_count) +
                " workspaces | " + std::to_string(live_.areas.size()) + " open areas | " +
                std::to_string(live_.registered_commands) + " registered commands | " +
                std::to_string(live_.dirty_areas) + " tables with buffered edits"));
    }
    void submit_live(Request request) {
        if (closing_ || live_pending_.valid() || field_pending_.valid() || memo_target_pending_.valid()) return;
        wxWindow::FindWindowByName("LIVE_TOOLS", frame_)->Disable(); recursion_->Disable();
        wxWindow::FindWindowByName("COMMAND_ROW", frame_)->Disable();
        wxWindow::FindWindowByName("TABLE_TOOLS", frame_)->Disable();
        wxWindow::FindWindowByName("EDIT_TOOLS", frame_)->Disable();
        wxWindow::FindWindowByName("PATHS_TOOLS", frame_)->Disable();
        live_pending_ = session_.submit(std::move(request));
    }
    void table_selection() {
        const auto prior_field = table_fields_->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
        const auto prior_name = prior_field < 0 ? wxString{} : table_fields_->GetItemText(prior_field);
        table_fields_->DeleteAllItems();
        const auto selected = table_rows_->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
        if (selected < 0 || static_cast<std::size_t>(selected) >= live_.table.rows.size()) return;
        const auto& values = live_.table.rows[selected].values;
        for (std::size_t i = 0; i < live_.table.fields.size(); ++i) {
            const auto& field = live_.table.fields[i];
            row(table_fields_, {field.name, std::string(1, field.type) + "(" + std::to_string(field.length) + ")", values[i]});
            if (wstr(field.name) == prior_name) table_fields_->SetItemState(static_cast<long>(i), wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED);
        }
    }
    bool table_workflow(const std::string& action, Request& r) {
        const bool immediate = action == "append" || action == "recall" || action == "null";
        if (immediate && (live_.table.buffered || live_.table.pending_records)) {
            table_note_->SetLabel("TABLE ON prevents this write. Native buffering is unavailable for this operation. Finish edits and explicitly use TABLE OFF first.");
            return false;
        }
        wxWeakRef<wxWindow> focus(wxWindow::FindFocus());
        auto dialog = std::unique_ptr<wxDialog>(uidef_create_dialog("OP_FORM", frame_));
        workflow_dialog_ = dialog.get(); workflow_prefix_ = "OP";
        auto* input = control<wxTextCtrl>(dialog.get(), "OP_VALUE");
        auto* error = control<wxStaticText>(dialog.get(), "OP_ERROR");
        auto* tag = control<wxTextCtrl>(dialog.get(), "OP_TAG");
        auto* desc = control<wxCheckBox>(dialog.get(), "OP_DESC");
        const bool has_input = action == "filter" || action == "order" || action == "seek" || action == "go";
        wxWindow::FindWindowByName("OP_ROW", dialog.get())->Show(has_input);
        wxWindow::FindWindowByName("OP_LABEL", dialog.get())->Show(has_input);
        wxWindow::FindWindowByName("OP_ORDER", dialog.get())->Show(action == "order");
        auto* pick = control<wxButton>(dialog.get(), "OP_PICK"); pick->Show(action == "order");
        pick->Bind(wxEVT_BUTTON, [&, this](wxCommandEvent&) {
            wxFileDialog file(dialog.get(), "Choose index", wstr(live_path("INDEXES").string()), wxEmptyString,
                "Indexes (*.cdx;*.cnx;*.inx)|*.cdx;*.cnx;*.inx|All files (*.*)|*.*", wxFD_OPEN | wxFD_FILE_MUST_EXIST);
            if (file.ShowModal() == wxID_OK) input->ChangeValue(file.GetPath());
        });
        const std::map<std::string, std::string> titles{{"filter", "Filter records"}, {"order", "Index order"},
            {"seek", "Seek key"}, {"go", "Go to record"}, {"append", "Append blank record"},
            {"delete", "Buffer record deletion"}, {"recall", "Recall record"}, {"null", "Set field NULL"}};
        dialog->SetTitle(wstr(titles.at(action)));
        std::string note = immediate ? "TABLE OFF: this writes immediately. Rollback cannot undo it." :
            action == "delete" ? "Mark this record for deletion in the table buffer. Commit writes it; Rollback cancels it." :
            action == "filter" ? "Use an x64base filter expression. Leave empty to clear the filter." :
            action == "order" ? "Choose an index and optional tag. Leave the index empty for natural (physical) order." :
            action == "seek" ? "Enter a key for the current index order, for example 'Smith' or 42. Native SEEK does not support spaces in a key; use Filter for those values." :
            "Enter a physical record number (records start at 1; areas start at 0).";
        control<wxStaticText>(dialog.get(), "OP_NOTE")->SetLabel(wstr(note));
        control<wxStaticText>(dialog.get(), "OP_NOTE")->Wrap(650);
        control<wxStaticText>(dialog.get(), "OP_DEST")->SetLabel(wstr(live_.table.name + " / area " +
            std::to_string(r.slot) + (r.record ? " / record " + std::to_string(r.record) : "") +
            (action == "null" ? " / " + r.edit.field_name : "")));
        control<wxStaticText>(dialog.get(), "OP_LABEL")->SetLabel(action == "order" ? "Index file" : action == "go" ? "Record number" : "Expression");
        if (action == "go") input->ChangeValue(wstr(std::to_string(live_.table.current_record)));
        control<wxButton>(dialog.get(), "OP_OK")->SetLabel(immediate ? "Write now" : action == "delete" ? "Buffer deletion" : "Apply");
        bool accepted = false;
        dialog->Bind(wxEVT_BUTTON, [&](wxCommandEvent&) {
            try {
                r.payload = input->GetValue().ToStdString(wxConvUTF8);
                if (r.payload.find_first_of("\r\n") != std::string::npos) throw std::runtime_error("Enter one line.");
                if (action == "go") {
                    if (r.payload.empty() || r.payload.find_first_not_of("0123456789") != std::string::npos)
                        throw std::runtime_error("Enter a positive record number.");
                    r.record = std::stoull(r.payload);
                    if (!r.record || r.record > live_.table.records) throw std::runtime_error("Record is outside this table.");
                }
                if (action == "seek" && r.payload.empty()) throw std::runtime_error("Enter a key expression.");
                if (action == "seek" && r.payload.find_first_of(" \t") != std::string::npos)
                    throw std::runtime_error("Use Filter for a key containing spaces.");
                if (action == "order" && !r.payload.empty()) {
                    const auto tag_text = tag->GetValue().ToStdString(wxConvUTF8);
                    if (r.payload.find('"') != std::string::npos || tag_text.find_first_of("\r\n\"") != std::string::npos)
                        throw std::runtime_error("Index and tag must not contain quotes or newlines.");
                    r.payload = "\"" + r.payload + "\"" + (tag_text.empty() ? "" : " " + tag_text) + (desc->GetValue() ? " DESC" : " ASC");
                }
                accepted = true; dialog->EndModal(wxID_OK);
            } catch (const std::exception& e) { error->SetLabel(wstr(e.what())); dialog->Fit(); }
        }, wxID_OK);
        dialog->Fit(); if (has_input) input->SetFocus();
        if (modal_probe_) dialog->CallAfter([this] { modal_probe_(workflow_dialog_, "OP"); });
        const auto result = dialog->ShowModal();
        workflow_dialog_ = nullptr; workflow_prefix_.clear(); dialog.reset();
        if (focus && focus->IsEnabled() && focus->IsShownOnScreen()) focus->SetFocus();
        return result == wxID_OK && accepted;
    }
public:
    void table_action(const std::string& action) {
        if (closing_ || workflow_dialog_ || live_pending_.valid() || field_pending_.valid() || memo_target_pending_.valid() || image_pending_.valid()) return;
        const auto& table = live_.table;
        Request r; r.action = Action::Browse;
        r.slot = table.slot; r.area_handle = table.area_handle; r.offset = table.offset;
        r.expected_workspace = live_.desk.current_handle;
        static const std::set<std::string> operations{"first", "last", "back", "forward", "go", "filter", "order", "seek", "deleted", "append", "delete", "recall"};
        if (operations.count(action)) {
            if (!table.open) { table_note_->SetLabel("Open and select a table first."); return; }
            r.action = Action::TableCommand; r.name = action; r.enabled = table.deleted_hidden;
            if (action == "delete" || action == "recall") {
                const auto selected = table_rows_->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
                if (selected < 0 || static_cast<std::size_t>(selected) >= table.rows.size()) { table_note_->SetLabel("Select a record first."); return; }
                r.record = table.rows[selected].recno;
            }
            if (action != "first" && action != "last" && action != "back" && action != "forward" && action != "deleted")
                if (!table_workflow(action, r)) return;
            submit_live(std::move(r)); return;
        }
        if (action == "top") r.offset = 0;
        if (action == "previous") r.offset = table.offset >= 100 ? table.offset - 100 : 0;
        if (action == "next") { if (!table.more) return; r.offset += table.rows.size(); }
        if (action == "commit") r.action = Action::CommitTable;
        if (action == "rollback") r.action = Action::RollbackTable;
        if (action == "select" || action == "value" || action == "edit" || action == "null" || action == "image" || action == "store_image") {
            const auto selected = table_rows_->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
            if (selected < 0 || static_cast<std::size_t>(selected) >= table.rows.size()) {
                table_note_->SetLabel("Select a table row first."); return;
            }
            r.record = table.rows[selected].recno;
            if (action == "select") r.action = Action::SelectRecord;
            else {
                const auto field = table_fields_->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
                if (field < 0 || static_cast<std::size_t>(field) >= table.fields.size()) {
                    table_note_->SetLabel("Select a field to open its value or memo."); return;
                }
                if (action == "image") {
                    image_provenance_.clear(); image_tree_ = {}; image_exports_.clear();
                    image_list_->Clear(); image_info_->DeleteAllItems();
                    wxWindow::FindWindowByName("IMAGE_TOOLS", frame_)->Disable();
                    image_pending_ = session_.inspect_field_image(table.slot, table.area_handle, r.record,
                        static_cast<int>(field) + 1, table.fields[field].name, stop_.get_token());
                    dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_))->SetSelection(2);
                    status_->SetLabel("Reading the selected memo as a database image...");
                    return;
                }
                wxWindow::FindWindowByName("TABLE_TOOLS", frame_)->Disable();
                wxWindow::FindWindowByName("EDIT_TOOLS", frame_)->Disable();
                wxWindow::FindWindowByName("COMMAND_ROW", frame_)->Disable();
                wxWindow::FindWindowByName("LIVE_TOOLS", frame_)->Disable(); recursion_->Disable();
                if (action == "store_image") {
                    dottalk::workbench::FieldEdit target;
                    target.slot = table.slot; target.handle = table.area_handle; target.record = r.record;
                    target.field1 = static_cast<int>(field) + 1; target.field_name = table.fields[field].name;
                    memo_target_pending_ = session_.inspect_memo_target(std::move(target));
                    table_note_->SetLabel("Checking the selected memo field..."); return;
                }
                field_pending_ = session_.inspect_field(table.slot, table.area_handle, r.record,
                    static_cast<int>(field) + 1, table.fields[field].name);
                edit_requested_ = action == "edit";
                null_requested_ = action == "null";
                edit_request_ = {}; edit_request_.action = Action::EditField;
                edit_request_.edit.slot = table.slot; edit_request_.edit.handle = table.area_handle;
                edit_request_.edit.record = r.record; edit_request_.edit.field1 = static_cast<int>(field) + 1;
                edit_request_.edit.field_name = table.fields[field].name;
                return;
            }
        }
        submit_live(std::move(r));
    }
private:
    void render_table() {
        const auto& table = live_.table;
        table_rows_->Freeze();
        std::vector<wxString> names{"Record", "State"};
        for (const auto& field : table.fields) names.push_back(wstr(field.name));
        columns(table_rows_, names);
        table_rows_->SetColumnWidth(0, 100); table_rows_->SetColumnWidth(1, 155);
        for (std::size_t i = 2; i < names.size(); ++i) table_rows_->SetColumnWidth(static_cast<int>(i), 180);
        long selected = 0;
        for (const auto& value : table.rows) {
            if (value.recno == table.current_record) selected = table_rows_->GetItemCount();
            std::string state = value.recno == table.current_record ? "Current" : "";
            if (value.deleted) state += " Deleted";
            if (value.delete_pending) state += " Delete pending";
            if (value.pending) state += " Buffered";
            std::vector<std::string> values{std::to_string(value.recno), state};
            values.insert(values.end(), value.values.begin(), value.values.end()); row(table_rows_, values);
        }
        if (!table.rows.empty()) {
            table_rows_->SetItemState(selected, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED);
            table_rows_->EnsureVisible(selected);
        }
        table_rows_->Thaw(); table_selection();
        std::string note = "No table selected. Open a table, then type BROWSE.";
        if (table.open) note = table.name + " | " + std::to_string(table.records) + " records | " + table.order +
            (table.expression_filter ? " | Filter on" : "") + (table.deleted_hidden ? " | Deleted hidden" : " | Deleted shown") + " | " + std::to_string(table.rows.size()) +
            " rows from offset " + std::to_string(table.offset) + " | Current record " + std::to_string(table.current_record);
        if (table.limited) note += " | Scan limit reached; narrow the filter or order scope.";
        if (table.open) note += (table.buffered ? " | TABLE ON | " : " | TABLE OFF | ") + std::to_string(table.pending_records) + " buffered records";
        if (!table.error.empty()) note = table.error;
        table_note_->SetLabel(wstr(note)); table_note_->SetToolTip(wstr(note));
        frame_->Layout();
    }
    NavKey nav_key(wxTreeItemId item) const {
        const auto* data = item.IsOk() ? dynamic_cast<NavData*>(live_tree_->GetItemData(item)) : nullptr;
        return data ? data->key : NavKey{};
    }
    bool nav_exists(NavKey key) const {
        if (!key.first || std::none_of(live_.desk.workspaces.begin(), live_.desk.workspaces.end(),
            [&](const auto& ws) { return ws.handle == key.first; })) return false;
        return !key.second || std::any_of(live_.areas.begin(), live_.areas.end(), [&](const auto& area) {
            return area.handle == key.second && area.workspace == key.first;
        });
    }
    bool nav_busy() const {
        return closing_ || workflow_dialog_ || live_pending_.valid() || field_pending_.valid() || memo_target_pending_.valid();
    }
    void nav_activate(NavKey key) {
        if (nav_busy()) return;
        if (!nav_exists(key)) { status_->SetLabel("That navigator target is no longer open. Refresh and choose again."); return; }
        Request r;
        live_selected_ = key.first; nav_area_ = key.second;
        if (!key.second) { r.action = Action::SwitchWorkspace; r.workspace = key.first; }
        else for (const auto& area : live_.areas) if (area.handle == key.second) {
            r.action = Action::SelectArea; r.slot = area.slot; r.area_handle = area.handle;
            area_highlighted_ = area.handle;
        }
        submit_live(std::move(r));
    }
    std::unique_ptr<wxMenu> nav_menu(NavKey key) {
        auto menu = std::make_unique<wxMenu>();
        auto add = [&](const wxString& label, std::function<void()> action, bool allowed = true) {
            const auto id = wxWindow::NewControlId();
            menu->Append(id, label)->Enable(allowed && nav_exists(key) && !nav_busy());
            menu->Bind(wxEVT_MENU, [this, key, action](wxCommandEvent&) {
                if (nav_busy()) return;
                if (!nav_exists(key)) { status_->SetLabel("That navigator target is no longer open. Refresh and choose again."); return; }
                action();
            }, id);
        };
        add(key.second ? "SELECT this table" : "SWITCH to this workspace", [this, key] { nav_activate(key); });
        if (!key.second) {
            add("New child workspace...", [this, key] {
                live_selected_ = key.first; nav_area_ = 0; live_action("child");
            }, std::any_of(live_.desk.workspaces.begin(), live_.desk.workspaces.end(),
                [&](const auto& ws) { return ws.handle == key.first && ws.ws_id != 0; }));
            add("Close tables in this workspace", [this, key] {
                Request r; r.action = Action::CloseWorkspace; r.expected_workspace = key.first; submit_live(r);
            }, key.first == live_.desk.current_handle);
            menu->AppendSeparator();
            add("Expand branch", [this, key] { if (nav_items_.count(key)) live_tree_->ExpandAllChildren(nav_items_.at(key)); });
            add("Collapse branch", [this, key] { if (nav_items_.count(key)) live_tree_->CollapseAllChildren(nav_items_.at(key)); });
        }
        menu->AppendSeparator();
        add("Refresh", [this] { live_action("refresh"); });
        return menu;
    }
    void nav_note() {
        const auto key = NavKey{live_selected_, nav_area_};
        const std::string note = nav_items_.empty() ? "No matches. Clear the search to see all workspaces." :
            !nav_items_.count(key) ? "Browsed selection is outside this search." :
            nav_area_ ? "Browsing table. Enter to SELECT its area." : "Browsing workspace. Enter to SWITCH.";
        nav_note_->SetLabel(wstr(note)); nav_note_->SetToolTip(wstr(note));
    }
    void render_navigator() {
        if (!nav_exists({live_selected_, 0})) { live_selected_ = live_.desk.current_handle; nav_area_ = 0; }
        if (nav_area_ && !nav_exists({live_selected_, nav_area_})) nav_area_ = 0;
        std::set<std::uint64_t> present;
        for (const auto& ws : live_.desk.workspaces) {
            present.insert(ws.handle);
            if (nav_known_.insert(ws.handle).second) nav_expanded_.insert(ws.handle);
        }
        nav_known_ = present;
        std::erase_if(nav_expanded_, [&](auto id) { return !present.count(id); });
        const auto view = dottalk::workbench::navigator_view(live_, nav_query_->GetValue().ToStdString(wxConvUTF8));
        const std::set<std::uint64_t> visible(view.workspaces.begin(), view.workspaces.end());
        rendering_nav_ = true; live_tree_->Freeze(); live_tree_->DeleteAllItems(); nav_items_.clear();
        const auto root = live_tree_->AddRoot("Live session");
        std::set<std::uint64_t> visiting;
        std::function<wxTreeItemId(std::uint64_t)> add = [&](std::uint64_t id) -> wxTreeItemId {
            const NavKey key{id, 0};
            if (nav_items_.count(key)) return nav_items_.at(key);
            if (!visible.count(id) || !visiting.insert(id).second) return root;
            for (const auto& ws : live_.desk.workspaces) if (ws.handle == id) {
                const auto parent = add(ws.parent);
                const auto label = ws.name + " [" + std::to_string(ws.open_areas) + " tables]" + (ws.current ? " [current]" : "");
                const auto item = live_tree_->AppendItem(parent, wstr(label), -1, -1, new NavData(key));
                nav_items_[key] = item; live_tree_->SetItemBold(item, ws.current); return item;
            }
            return root;
        };
        for (auto id : view.workspaces) add(id);
        for (auto index : view.areas) {
            const auto& area = live_.areas[index];
            const NavKey key{area.workspace, area.handle};
            const bool selected = area.slot == live_.desk.current_engine_area;
            const auto label = std::to_string(area.slot) + ": " + area.name + (area.ram ? " [RAM]" : "") + (selected ? " [selected]" : "");
            const auto item = live_tree_->AppendItem(nav_items_.at({area.workspace, 0}), wstr(label), -1, -1, new NavData(key));
            nav_items_[key] = item; live_tree_->SetItemBold(item, selected);
        }
        for (const auto& [key, item] : nav_items_)
            if (!key.second && (!nav_query_->IsEmpty() || nav_expanded_.count(key.first))) live_tree_->Expand(item);
        const NavKey selected{live_selected_, nav_area_};
        if (nav_items_.count(selected)) live_tree_->SelectItem(nav_items_.at(selected));
        live_tree_->Thaw(); rendering_nav_ = false; nav_note();
    }
    void live_selection() {
        live_ws_->DeleteAllItems();
        if (nav_area_) for (const auto& area : live_.areas) if (area.handle == nav_area_) {
            row(live_ws_, {"Browsing table", area.name}); row(live_ws_, {"Area", std::to_string(area.slot)});
            row(live_ws_, {"Table path", area.path}); row(live_ws_, {"Records", std::to_string(area.records)});
        }
        for (const auto& ws : live_.desk.workspaces) if (ws.handle == live_selected_) {
            row(live_ws_, {"Name", ws.name});
            row(live_ws_, {"Runtime workspace handle", std::to_string(ws.handle)});
            row(live_ws_, {"Durable ID in session catalog", ws.ws_id ? std::to_string(ws.ws_id) : "Not allocated (DEFAULT)"});
            row(live_ws_, {"Parent runtime handle", ws.parent ? std::to_string(ws.parent) : "Root"});
            row(live_ws_, {"Nesting depth", std::to_string(ws.depth)});
            row(live_ws_, {"Open areas", std::to_string(ws.open_areas)});
            row(live_ws_, {"Current workspace", ws.current ? "Yes" : "No"});
            row(live_ws_, {"DBF root", ws.dbf_root}); row(live_ws_, {"Index root", ws.idx_root});
            row(live_ws_, {"LMDB root", ws.lmdb_root});
            row(live_ws_, {"Session data retained at", live_.home.string()});
            row(live_ws_, {"Active workspace catalog", live_.default_catalog.string()});
            row(live_ws_, {"Catalog identity", "Live handles and durable WS_ID are separate; catalog path is part of durable identity"});
            for (const auto& image : live_.images) if (image.workspace == ws.handle) {
                row(live_ws_, {"Hydrated from", image.provenance});
                row(live_ws_, {"Image RAM bytes (retained until exit)", std::to_string(image.ram_bytes)});
                row(live_ws_, {"Image disk memo bytes", std::to_string(image.disk_bytes)});
                row(live_ws_, {"Private mount", image.root.string()});
            }
        }
        live_ws_->SetColumnWidth(1, std::max(300, live_ws_->GetClientSize().GetWidth() - 230));
        render_areas();
    }
    void render_areas() {
        const auto scope = dottalk::workbench::scope_areas(live_, live_selected_, area_all_->GetValue(),
            area_nested_->GetValue(), area_query_->GetValue().ToStdString(wxConvUTF8));
        if (area_highlighted_ && std::none_of(live_.areas.begin(), live_.areas.end(),
            [this](const auto& area) { return area.handle == area_highlighted_; })) area_highlighted_ = 0;
        rendering_areas_ = true; live_areas_->Freeze(); live_areas_->DeleteAllItems();
        area_visible_ = scope.indices;
        long match = -1;
        std::string scope_name;
        for (const auto& ws : live_.desk.workspaces) if (ws.handle == live_selected_) scope_name = ws.name;
        for (std::size_t i = 0; i < area_visible_.size(); ++i) {
            const auto& area = live_.areas[area_visible_[i]];
            std::string workspace;
            for (const auto& ws : live_.desk.workspaces) if (ws.handle == area.workspace) workspace = ws.name;
            const bool active = area.slot == live_.desk.current_engine_area;
            row(live_areas_, {workspace, (active ? "* " : "") + area.name + (area.ram ? " [RAM]" : ""),
                std::to_string(area.slot), std::to_string(area.records)});
            if (area.handle == area_highlighted_ || (!area_highlighted_ && active)) match = static_cast<long>(i);
        }
        if (match >= 0) {
            live_areas_->SetItemState(match, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED);
            live_areas_->EnsureVisible(match);
        }
        live_areas_->Thaw(); rendering_areas_ = false;
        area_nested_->Enable(!area_all_->GetValue());
        const auto label = !scope.error.empty() ? scope.error :
            (area_all_->GetValue() ? "All workspaces" : scope_name + (area_nested_->GetValue() ? " and nested workspaces" : " only")) +
            " | " + std::to_string(area_visible_.size()) + " of " + std::to_string(live_.areas.size()) +
            " open tables | Double-click a table to SELECT it";
        area_note_->SetLabel(wstr(label)); area_note_->SetToolTip(wstr(label));
    }
    void render_live() {
        render_navigator(); live_selection();
        recursion_->SetValue(live_.desk.recursion_enabled);
        std::string current = "Current workspace: ", selected = "none", owner;
        for (const auto& ws : live_.desk.workspaces) if (ws.current) current += ws.name;
        for (const auto& area : live_.areas) {
            std::string workspace;
            for (const auto& ws : live_.desk.workspaces) if (ws.handle == area.workspace) workspace = ws.name;
            const bool active = area.slot == live_.desk.current_engine_area;
            if (active) { selected = area.name + " (area " + std::to_string(area.slot) + ")"; owner = workspace; }
        }
        current += " | Selected table: " + selected + (owner.empty() ? "" : " in " + owner);
        live_current_->SetLabel(wstr(!live_.error.empty() ? "Refused: " + live_.error :
            live_.saved_image.empty() ? current : "Saved image verified: " + live_.saved_image.string()));
        live_current_->SetToolTip(wstr(current));
        if (!live_.transcript.empty() || !live_.error.empty()) {
            live_log_->DeleteAllItems(); std::istringstream lines(live_.transcript);
            std::string line; unsigned number = 0; int width = 670;
            while (number < 5000 && std::getline(lines, line)) {
                row(live_log_, {std::to_string(++number), line});
                width = std::max(width, live_log_->GetTextExtent(wstr(line.substr(0, 4096))).GetWidth() + 16);
            }
            if (std::getline(lines, line)) row(live_log_, {"...", "Display limited to 5000 lines; narrow the query or use SET ALTERNATE."});
            if (!live_.error.empty()) row(live_log_, {"Error", live_.error});
            live_log_->SetColumnWidth(1, width);
        }
        render_table(); live_status();
    }
    void advance_live_smoke() {
        live_smoke_ok_ = live_smoke_ok_ && live_.ok() && live_.desk.healthy();
        auto handle = [&](const char* name) {
            for (const auto& ws : live_.desk.workspaces) if (ws.name == name) return ws.handle;
            return std::uint64_t{};
        };
        Request r;
        switch (live_smoke_step_++) {
        case 0: r.action = Action::NewWorkspace; r.name = "WorkbenchParent"; break;
        case 1: r.action = Action::NewWorkspace; r.name = "WorkbenchChild"; r.workspace = handle("WorkbenchParent"); break;
        case 2: r.action = Action::SwitchWorkspace; r.workspace = handle("WorkbenchChild"); break;
        case 3: r.action = Action::OpenCopy; r.path = fs::path(path_->GetValue().ToStdWstring()); break;
        case 4: r.action = Action::NewWorkspace; r.name = "WorkbenchPeer"; break;
        case 5: r.action = Action::SwitchWorkspace; r.workspace = handle("WorkbenchPeer"); break;
        case 6: r.action = Action::OpenCopy; r.path = fs::path(path_->GetValue().ToStdWstring()); break;
        case 7: r.action = Action::SwitchWorkspace; r.workspace = handle("WorkbenchParent"); break;
        case 8:
            control<wxTextCtrl>(frame_, "COMMAND_BOX")->ChangeValue("SELECT WorkbenchChild:WORKSPACES");
            live_action("command"); return;
        case 9: {
            auto* input = control<wxTextCtrl>(frame_, "COMMAND_BOX");
            input->ChangeValue("list top 1");
            wxKeyEvent enter(wxEVT_CHAR_HOOK); enter.m_keyCode = WXK_RETURN; enter.SetEventObject(input);
            live_smoke_ok_ = live_smoke_ok_ && input->GetEventHandler()->ProcessEvent(enter);
            return;
        }
        case 10: {
            live_smoke_ok_ = live_smoke_ok_ && live_.transcript.find("listed") != std::string::npos;
            auto* input = control<wxTextCtrl>(frame_, "COMMAND_BOX");
            for (const auto key : {WXK_UP, WXK_UP, WXK_DOWN}) {
                wxKeyEvent event(wxEVT_CHAR_HOOK); event.m_keyCode = key; event.SetEventObject(input);
                live_smoke_ok_ = live_smoke_ok_ && input->GetEventHandler()->ProcessEvent(event);
            }
            live_smoke_ok_ = live_smoke_ok_ && input->GetValue() == "list top 1";
            r.action = Action::Command; r.name = "TABLE ON"; break;
        }
        case 11: r.action = Action::Command; r.name = "GO TOP"; break;
        case 12: r.action = Action::Command; r.name = "REPLACE WS_NAME WITH 'WB_BUFFERED_TEST'"; break;
        case 13:
            live_smoke_ok_ = live_smoke_ok_ && live_.dirty_areas == 1;
            frame_->Close();
            live_smoke_ok_ = live_smoke_ok_ && !closing_ && live_current_->GetLabel().Contains("buffered");
            r.action = Action::Command; r.name = "ROLLBACK"; break;
        case 14:
            live_smoke_ok_ = live_smoke_ok_ && live_.dirty_areas == 0;
            r.action = Action::Command; r.name = "TABLE OFF"; break;
        case 15:
            control<wxTextCtrl>(frame_, "COMMAND_BOX")->ChangeValue("list top 1");
            live_action("command"); return;
        default: {
            live_selected_ = handle("WorkbenchChild"); render_live();
            auto* pages = dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_));
            if (pages) pages->SetSelection(1); else live_smoke_ok_ = false;
            auto* detail_pages = dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("LIVE_DETAILS", frame_));
            if (detail_pages) detail_pages->SetSelection(2);
            live_smoke_ok_ = live_smoke_ok_ && live_.desk.workspace_count == 4 && live_.areas.size() == 2 &&
                live_.desk.current_handle == handle("WorkbenchParent") &&
                live_current_->GetLabel().Contains("in WorkbenchChild") &&
                live_log_->GetItemCount() > 1 && live_.transcript.find("WS_NAME") != std::string::npos &&
                live_.transcript.find("listed") != std::string::npos;
            capture_delay_ = 6; return;
        }
        }
        submit_live(std::move(r));
    }
    void advance_m3_smoke() {
        auto check = [&](bool ok, const std::string& why) { if (!ok) throw std::runtime_error(why); };
        auto probe = [this](std::string input, bool cancel = false, bool invalid_first = false) {
            modal_probe_ = [this, input, cancel, invalid_first](wxDialog* dialog, const std::string&) {
                if (cancel) { dialog->EndModal(wxID_CANCEL); return; }
                auto* value = control<wxTextCtrl>(dialog, "OP_VALUE");
                if (invalid_first) {
                    value->ChangeValue("-1");
                    wxCommandEvent invalid(wxEVT_BUTTON, wxID_OK); dialog->GetEventHandler()->ProcessEvent(invalid);
                    m3_ok_ = m3_ok_ && dialog->IsModal() && !control<wxStaticText>(dialog, "OP_ERROR")->GetLabel().empty();
                }
                value->ChangeValue(wstr(input));
                wxCommandEvent accept(wxEVT_BUTTON, wxID_OK); dialog->GetEventHandler()->ProcessEvent(accept);
            };
        };
        auto row_field = [&] {
            for (long i = 0; i < table_rows_->GetItemCount(); ++i) table_rows_->SetItemState(i, 0, wxLIST_STATE_SELECTED);
            table_rows_->SetItemState(0, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED); table_selection();
            table_fields_->SetItemState(1, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED);
        };
        try {
            check(live_.ok(), live_.error);
            switch (m3_step_++) {
            case 0: { Request r; r.action = Action::OpenCopy; r.path = table_source_; submit_live(r); return; }
            case 1:
                if (!live_.table.open) {
                    --m3_step_;
                    dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_))->ChangeSelection(1);
                    dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("LIVE_DETAILS", frame_))->ChangeSelection(3);
                    table_action("refresh"); return;
                }
                table_action("last"); return;
            case 2: check(live_.table.current_record == 205 && live_.table.offset == 200, "Last record follows cursor across pages"); table_action("first"); return;
            case 3: check(live_.table.current_record == 1, "First record"); {
                wxKeyEvent key(wxEVT_CHAR_HOOK); key.m_keyCode = WXK_RIGHT; key.m_controlDown = true;
                table_rows_->GetEventHandler()->ProcessEvent(key); return;
            }
            case 4: check(live_.table.current_record == 2, "Keyboard next record"); table_action("back"); return;
            case 5: check(live_.table.current_record == 1, "Previous record"); probe("NUMBER > 200"); table_action("filter"); return;
            case 6: check(live_.table.rows.size() == 5 && live_.table.rows[0].recno == 201, "Filter dialog");
                probe("", true); table_action("order"); check(!workflow_dialog_, "Cancel releases modal"); submit_live({}); return;
            case 7: probe("201", false, true); table_action("go"); return;
            case 8: check(live_.table.current_record == 201, "Go validation and readback"); probe(""); table_action("filter"); return;
            case 9: check(!live_.table.expression_filter, "Clear expression filter while retaining deleted visibility"); table_action("first"); return;
            case 10: row_field(); table_action("edit"); return;
            case 11: check(live_.table.pending_records == 1 && session_.inspect_field(live_.table.slot, live_.table.area_handle, 1, 2, "NOTE").get().text ==
                    "M3 memo text\nSecond line 'quoted' & literal", "Memo editor stages literal text"); table_action("rollback"); return;
            case 12: check(live_.table.pending_records == 0, "Memo rollback"); row_field(); table_action("edit"); return;
            case 13: table_action("commit"); return;
            case 14: check(live_.table.pending_records == 0 && session_.inspect_field(live_.table.slot, live_.table.area_handle, 1, 2, "NOTE").get().text ==
                    "M3 memo text\nSecond line 'quoted' & literal", "Memo commit readback");
                table_action("append"); check(table_note_->GetLabel().Contains("TABLE ON prevents"), "Append refuses TABLE ON");
                probe(""); table_action("delete"); return;
            case 15: check(live_.table.rows[0].delete_pending && live_.table.pending_records == 1, "Delete flag visibly buffered"); table_action("rollback"); return;
            case 16: check(!live_.table.rows[0].delete_pending && live_.table.pending_records == 0, "Delete rollback");
                table_action("deleted"); return;
            default: check(!live_.table.deleted_hidden, "Deleted visibility control"); modal_probe_ = {}; capture_delay_ = 6; return;
            }
        } catch (const std::exception& e) { m3_ok_ = false; m3_error_ = e.what(); modal_probe_ = {}; capture_delay_ = 6; }
    }
    void advance_browse_smoke() {
        browse_smoke_ok_ = browse_smoke_ok_ && live_.ok() && live_.table.error.empty();
        switch (browse_smoke_step_++) {
        case 0: {
            Request r; r.action = Action::OpenCopy; r.path = table_source_; submit_live(r); return;
        }
        case 1: {
            auto* input = control<wxTextCtrl>(frame_, "COMMAND_BOX"); input->ChangeValue("BROWSE");
            wxKeyEvent enter(wxEVT_CHAR_HOOK); enter.m_keyCode = WXK_RETURN; enter.SetEventObject(input);
            browse_smoke_ok_ = browse_smoke_ok_ && input->GetEventHandler()->ProcessEvent(enter); return;
        }
        case 2:
            browse_smoke_ok_ = browse_smoke_ok_ && live_.browse_requested && table_rows_->GetItemCount() == 100 &&
                dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("LIVE_DETAILS", frame_))->GetSelection() == 3;
            table_action("next"); return;
        case 3:
            browse_smoke_ok_ = browse_smoke_ok_ && live_.table.offset == 100 && table_rows_->GetItemText(0) == "101";
            table_action("previous"); return;
        case 4:
            browse_smoke_ok_ = browse_smoke_ok_ && live_.table.offset == 0 && table_rows_->GetItemCount() == 100;
            table_rows_->SetItemState(-1, 0, wxLIST_STATE_SELECTED);
            table_rows_->SetItemState(6, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED);
            table_action("select"); return;
        case 5:
            browse_smoke_ok_ = browse_smoke_ok_ && live_.table.current_record == 7 && table_fields_->GetItemCount() == 3;
            table_fields_->SetItemState(1, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED);
            table_action("value"); return;
        default: browse_smoke_ok_ = false; capture_delay_ = 6; return;
        }
    }
    void advance_edit_smoke() {
        edit_smoke_ok_ = edit_smoke_ok_ && live_.ok() && live_.table.error.empty();
        auto edit_first = [this] {
            table_rows_->SetItemState(-1, 0, wxLIST_STATE_SELECTED);
            table_rows_->SetItemState(0, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED);
            table_selection(); table_fields_->SetItemState(0, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED);
            table_action("edit");
        };
        Request r;
        switch (edit_smoke_step_++) {
        case 0: r.action = Action::OpenCopy; r.path = table_source_; break;
        case 1: r.action = Action::Command; r.name = "BROWSE"; break;
        case 2: edit_first(); return;
        case 3:
            edit_smoke_ok_ = edit_smoke_ok_ && live_.table.pending_records == 1 && live_.table.rows[0].values[0] == "GUI buffered value";
            table_action("rollback"); return;
        case 4:
            edit_smoke_ok_ = edit_smoke_ok_ && live_.table.pending_records == 0 && live_.table.rows[0].values[0] == "Person 1";
            edit_first(); return;
        case 5:
            edit_smoke_ok_ = edit_smoke_ok_ && live_.table.pending_records == 1 && live_.table.rows[0].values[0] == "GUI committed value";
            table_action("commit"); return;
        case 6:
            edit_smoke_ok_ = edit_smoke_ok_ && live_.table.pending_records == 0 && live_.dirty_areas == 0;
            for (const auto& area : live_.areas) if (area.slot == live_.table.slot) edited_path_ = area.path;
            r.action = Action::Command; r.name = "CLOSE"; break;
        case 7: r.action = Action::Command; r.name = "USE " + edited_path_.string(); break;
        default:
            edit_smoke_ok_ = edit_smoke_ok_ && !live_.table.rows.empty() &&
                live_.table.rows[0].values[0] == "GUI committed value" && live_.table.pending_records == 0;
            dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("LIVE_DETAILS", frame_))->ChangeSelection(3);
            capture_delay_ = 6; return;
        }
        submit_live(r);
    }
    void advance_save_smoke() {
        save_smoke_ok_ = save_smoke_ok_ && live_.ok() && live_.desk.healthy();
        Request r;
        switch (save_smoke_step_++) {
        case 0: r.action = Action::OpenCopy; r.path = table_source_; break;
        case 1: r.action = Action::Command; r.name = "GO TOP"; break;
        case 2: r.action = Action::Command; r.name = "REPLACE NAME WITH 'Saved from Workbench'"; break;
        case 3:
            saved_path_ = live_.home / "GUI saved image.minidb";
            save_image(saved_path_); return;
        case 4:
            save_smoke_ok_ = save_smoke_ok_ && live_.saved_image == saved_path_;
            open_image(saved_path_); return;
        case 5: r.action = Action::Command; r.name = "BROWSE"; break;
        default:
            save_smoke_ok_ = save_smoke_ok_ && live_.areas.size() == 2 && live_.images.size() == 1 &&
                live_.table.records == 205 && !live_.table.rows.empty() && live_.table.rows[0].values[0] == "Saved from Workbench";
            capture_delay_ = 6; return;
        }
        submit_live(std::move(r));
    }
    void advance_memo_image_smoke() {
        memo_image_ok_ = memo_image_ok_ && live_.ok() && live_.desk.healthy();
        Request r;
        switch (memo_image_step_++) {
        case 0: r.action = Action::NewWorkspace; r.name = "MemoLibrary"; break;
        case 1:
            for (const auto& ws : live_.desk.workspaces) if (ws.name == "MemoLibrary") memo_parent_ = ws.handle;
            r.action = Action::SwitchWorkspace; r.workspace = memo_parent_; break;
        case 2: r.action = Action::OpenCopy; r.path = fs::path(path_->GetValue().ToStdWstring()); break;
        case 3: r.action = Action::Command; r.name = "BROWSE"; break;
        case 4: {
            table_rows_->SetItemState(0, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED); table_selection();
            auto field = std::find_if(live_.table.fields.begin(), live_.table.fields.end(),
                [](const auto& f) { return f.name == "SNAPSHOT"; });
            if (field == live_.table.fields.end()) { memo_image_ok_ = false; capture_delay_ = 6; return; }
            table_fields_->SetItemState(static_cast<long>(field - live_.table.fields.begin()), wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED);
            table_action("image"); return;
        }
        case 5: r.action = Action::Command; r.name = "BROWSE"; break;
        default:
            memo_image_ok_ = memo_image_ok_ && live_.areas.size() == 2 && live_.images.size() == 1 &&
                live_.table.records == 2 && live_.table.rows.size() == 2 && live_.table.rows[0].values[0] == "Ada";
            for (const auto& ws : live_.desk.workspaces) if (ws.current)
                memo_image_ok_ = memo_image_ok_ && ws.parent == memo_parent_;
            dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_))->ChangeSelection(2);
            image_selection();
            capture_delay_ = 6; return;
        }
        submit_live(std::move(r));
    }
    void advance_openload_smoke() {
        openload_ok_ = openload_ok_ && live_.ok();
        auto* main = dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_));
        auto* details = dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("LIVE_DETAILS", frame_));
        auto click = [&](const char* id) {
            auto* button = dynamic_cast<wxButton*>(wxWindow::FindWindowByName(id, frame_));
            if (!button || !button->IsEnabled()) { openload_ok_ = false; capture_delay_ = 6; return; }
            wxCommandEvent event(wxEVT_BUTTON, button->GetId()); event.SetEventObject(button);
            button->GetEventHandler()->ProcessEvent(event);
        };
        switch (openload_step_++) {
        case 0:
            frame_->SetSize(1000, 850); main->SetSelection(1); click("OPEN_WS"); return;
        case 1:
            openload_ok_ = openload_ok_ && live_.desk.workspace_count == 1 && live_.areas.size() == 1 &&
                live_.command_opened_tables == 1 && main->GetSelection() == 1 && details->GetSelection() == 1 && live_areas_->GetItemCount() == 1;
            click("LOAD_WS"); return;
        case 2:
            openload_ok_ = openload_ok_ && live_.areas.size() == 2 && live_.desk.workspace_count == 1 &&
                live_.command_opened_tables == 1 && details->GetSelection() == 1 && live_areas_->GetItemCount() == 2 &&
                live_areas_->GetColumnCount() == 4 && live_areas_->GetItemText(0, 2) == "0" && live_areas_->GetItemText(1, 2) == "1" &&
                live_current_->GetLabel().Contains("(area 1)") &&
                live_.transcript.find("Button load & sample.dtschema") != std::string::npos;
            submit_live({}); return;
        default:
            for (const char* id : {"NEW_ROOT", "OPEN_WS", "LOAD_WS", "NEW_CHILD", "SWITCH_WS", "OPEN_COPY", "LIVE_REFRESH"}) {
                auto* button = wxWindow::FindWindowByName(id, frame_);
                const auto rect = button->GetScreenRect(), parent = button->GetParent()->GetScreenRect();
                openload_ok_ = openload_ok_ && button->IsShownOnScreen() && button->IsEnabled() && parent.Contains(rect);
            }
            openload_ok_ = openload_ok_ && live_areas_->GetItemCount() == 2 && details->GetSelection() == 1;
            capture_delay_ = 6; return;
        }
    }
    void advance_catalog_flow_smoke() {
        auto check = [](bool good, const std::string& why) { if (!good) throw std::runtime_error(why); };
        auto choose = [&](std::uint64_t id) {
            history_->SetValue(true); rebuild();
            for (std::size_t i = 0; i < visible_.size(); ++i) if (snapshot_.entries[visible_[i]].id == id) {
                list_->SetSelection(static_cast<int>(i)); selection();
                dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_))->SetSelection(0); return;
            }
            throw std::runtime_error("Fixture saved ID missing");
        };
        auto click = [&](const char* id) {
            auto* button = control<wxButton>(frame_, id); check(button->IsEnabled(), "Catalog action disabled");
            wxCommandEvent event(wxEVT_BUTTON, button->GetId()); event.SetEventObject(button);
            check(button->GetEventHandler()->ProcessEvent(event), "Catalog button dispatch");
        };
        auto probe = [&](bool cancel, bool child = false) {
            modal_probe_ = [this, check, cancel, child](wxDialog* dialog, const std::string& prefix) {
                try {
                    check(dialog->IsModal() && dialog->GetParent() == frame_, "Catalog modal ownership");
                    auto* value = dynamic_cast<wxTextCtrl*>(wxWindow::FindWindowByName(wstr(prefix + "_VALUE"), dialog));
                    auto* error = dynamic_cast<wxStaticText*>(wxWindow::FindWindowByName(wstr(prefix + "_ERROR"), dialog));
                    wxCommandEvent accept(wxEVT_BUTTON, wxID_OK);
                    if (prefix == "HYD") {
                        check(dynamic_cast<wxStaticText*>(wxWindow::FindWindowByName("HYD_NOTE", dialog))->GetLabel().Contains("saved ID 21"), "Exact image identity shown");
                        value->ChangeValue("invalid name!"); dialog->GetEventHandler()->ProcessEvent(accept);
                        check(dialog->IsModal() && !error->GetLabel().Strip().empty(), "Invalid hydration name stays in form");
                        value->ChangeValue(child ? "GuiChildRam" : "GuiHistoricalRam");
                        auto* under = dynamic_cast<wxCheckBox*>(wxWindow::FindWindowByName("HYD_CHILD", dialog));
                        under->SetValue(child); wxCommandEvent changed(wxEVT_CHECKBOX, under->GetId()); under->GetEventHandler()->ProcessEvent(changed);
                        check(dynamic_cast<wxStaticText*>(wxWindow::FindWindowByName("HYD_DEST", dialog))->GetLabel().Contains(child ? "Parent workspace:" : "new root"), "Hydration destination label");
                    } else {
                        check(prefix == "LOAD" && !value->IsEditable() && value->GetValue().Contains("saved ID 11") &&
                              !wxWindow::FindWindowByName("LOAD_PICK", dialog)->IsShown(), "Saved definition identity cannot redirect by name");
                        auto* tables = dynamic_cast<wxTextCtrl*>(wxWindow::FindWindowByName("LD_DBF", dialog));
                        tables->ChangeValue(wstr(live_.home.string())); dialog->GetEventHandler()->ProcessEvent(accept);
                        check(dialog->IsModal() && error->GetLabel().Contains("missing"), "Missing member correction in modal");
                        tables->ChangeValue(wstr(table_source_.parent_path().string()));
                    }
                    if (!capture_.empty()) {
                        dialog->Update(); wxClientDC source(dialog); const auto size = dialog->GetClientSize();
                        wxBitmap bitmap(size.x, size.y); wxMemoryDC target(bitmap);
                        check(target.Blit(0, 0, size.x, size.y, &source, 0, 0), "Catalog modal capture"); target.SelectObject(wxNullBitmap);
                        check(bitmap.SaveFile(wstr((capture_.parent_path() / (capture_.stem().string() + "-catalog-" + prefix + ".png")).string()), wxBITMAP_TYPE_PNG), "Catalog modal capture write");
                    }
                    wxKeyEvent key(wxEVT_CHAR_HOOK); key.m_keyCode = cancel ? WXK_ESCAPE : WXK_RETURN;
                    key.SetEventObject(value); dialog->GetEventHandler()->ProcessEvent(key);
                    check(dialog->GetReturnCode() == (cancel ? wxID_CANCEL : wxID_OK), "Catalog Enter/Escape result");
                } catch (const std::exception& e) {
                    catalog_flow_ok_ = false; catalog_flow_error_ = e.what(); dialog->EndModal(wxID_CANCEL);
                }
            };
        };
        auto verify_table = [&](bool ram) {
            const auto area = std::find_if(live_.areas.begin(), live_.areas.end(), [&](const auto& a) { return a.slot == live_.desk.current_engine_area; });
            check(area != live_.areas.end() && area->workspace == live_.desk.current_handle && area->ram == ram && area->name == "HISTORICAL", "Selected exact historical table and storage");
            const auto field = session_.inspect_field(area->slot, area->handle, 1, 1, "NAME").get();
            check(field.error.empty() && field.text == "Ada", "Catalog UI loaded actual Ada value");
        };
        try {
            check(catalog_flow_ok_, catalog_flow_error_); check(live_.ok(), live_.error);
            switch (catalog_flow_step_++) {
            case 0:
                choose(31); check(!control<wxButton>(frame_, "CAT_LOAD")->IsEnabled() && !control<wxButton>(frame_, "CAT_HYDRATE")->IsEnabled() &&
                    control<wxStaticText>(frame_, "CAT_NOTE")->GetLabel().Contains("Birth record"), "Birth row disabled with explanation");
                choose(32); check(!control<wxButton>(frame_, "CAT_HYDRATE")->IsEnabled(), "Corrupt image disabled");
                choose(21); check(!control<wxButton>(frame_, "CAT_LOAD")->IsEnabled(), "Image action only");
                probe(true); click("CAT_HYDRATE"); check(!live_pending_.valid() && live_.areas.empty() && live_.desk.workspace_count == 1, "Cancelled hydration changes no live state");
                probe(false); click("CAT_HYDRATE"); return;
            case 1: {
                verify_table(true); check(!image_tree_.nodes.empty() && image_provenance_.find("saved ID 21") != std::string::npos, "Direct hydration fills Database images with source identity");
                Request next; next.action = Action::NewWorkspace; next.name = "GuiDefinitionTarget"; submit_live(next); return;
            }
            case 2:
                catalog_flow_parent_ = live_.desk.current_handle;
                choose(11); check(!control<wxButton>(frame_, "CAT_HYDRATE")->IsEnabled(), "Definition action only");
                probe(true); click("CAT_LOAD"); check(!live_pending_.valid() && live_.areas.size() == 1, "Cancelled definition leaves RAM peer intact");
                probe(false); click("CAT_LOAD"); return;
            case 3:
                verify_table(false); check(live_.areas.size() == 2 && live_.desk.current_handle == catalog_flow_parent_, "Definition loads into shown destination and retains peer");
                choose(21); probe(false, true); click("CAT_HYDRATE"); return;
            default:
                verify_table(true);
                check(live_.areas.size() == 3 && live_.images.size() == 2 && !image_tree_.nodes.empty(), "Both RAM imports and disk definition remain visible");
                for (const auto& ws : live_.desk.workspaces) if (ws.current) check(ws.parent == catalog_flow_parent_, "Hydrated child parent identity");
                modal_probe_ = {}; choose(21); capture_delay_ = 6; return;
            }
        } catch (const std::exception& e) {
            catalog_flow_ok_ = false; catalog_flow_error_ = e.what(); modal_probe_ = {}; capture_delay_ = 6;
        }
    }
    void advance_m1_smoke() {
        auto check = [](bool good, const std::string& message) { if (!good) throw std::runtime_error(message); };
        auto table_count = [&](const dottalk::workbench::ImageTree& image) {
            check(image.error.empty() && image.nodes.size() == 1, "Saved image inspection");
            const auto admitted = dottalk::workbench::admit_image(image.nodes[0].payload, live_.home / "m1-admit");
            check(admitted.ok(), admitted.error); return admitted.tables;
        };
        auto menu = [&](const char* id) {
            check(g_menu_ids.contains(id), std::string("Generated menu missing: ") + id);
            wxCommandEvent event(wxEVT_MENU, g_menu_ids.at(id));
            check(frame_->GetEventHandler()->ProcessEvent(event), "Generated menu did not dispatch");
        };
        auto probe = [&](std::string input, int mode = 0, bool nested = false) {
            modal_probe_ = [this, input, mode, nested, check](wxDialog* dialog, const std::string& prefix) {
                try {
                    ++m1_dialogs_;
                    check(dialog && dialog->IsModal() && dialog->GetParent() == frame_, "Modal ownership");
                    auto* value = dynamic_cast<wxTextCtrl*>(wxWindow::FindWindowByName(wstr(prefix + "_VALUE"), dialog));
                    check(value && dialog->GetAffirmativeId() == wxID_OK && dialog->GetEscapeId() == wxID_CANCEL,
                          "Generated input and default/escape identities");
                    check(dialog->GetDefaultItem() && dialog->GetDefaultItem()->GetId() == wxID_OK, "Enter default button");
                    if (prefix == "RUN") check(fs::path(value->GetValue().ToStdWstring()) == live_path("SCRIPTS"), "Script form starts in SCRIPTS");
                    if (!input.empty()) value->ChangeValue(wstr(input));
                    if (prefix == "SAVE") dynamic_cast<wxCheckBox*>(wxWindow::FindWindowByName("SAVE_NESTED", dialog))->SetValue(nested);
                    if (mode == 1) {
                        value->ChangeValue(prefix == "NEW" ? "bad name!" : "missing-relative-path");
                        wxCommandEvent invalid(wxEVT_BUTTON, wxID_OK); dialog->GetEventHandler()->ProcessEvent(invalid);
                        check(dialog->IsModal(), "Invalid input closed the form");
                        auto* error = dynamic_cast<wxStaticText*>(wxWindow::FindWindowByName(wstr(prefix + "_ERROR"), dialog));
                        check(error && error->GetLabel().Strip().length() > 0, "Invalid input did not explain refusal");
                    }
                    if (mode == 4) {
                        auto* tables = dynamic_cast<wxTextCtrl*>(wxWindow::FindWindowByName("LD_DBF", dialog));
                        auto* indexes = dynamic_cast<wxTextCtrl*>(wxWindow::FindWindowByName("LD_IDX", dialog));
                        check(tables && indexes, "Load exposes both directory defaults");
                        tables->ChangeValue(wstr(live_path("WORKSPACES").string()));
                        wxCommandEvent invalid(wxEVT_BUTTON, wxID_OK); dialog->GetEventHandler()->ProcessEvent(invalid);
                        auto* error = dynamic_cast<wxStaticText*>(wxWindow::FindWindowByName("LOAD_ERROR", dialog));
                        check(dialog->IsModal() && !live_pending_.valid() && error && error->GetLabel().Contains("missing"),
                              "Missing schema tables must keep the modal open");
                        tables->ChangeValue(wstr((live_path("DATA") / "dbf/button load").string()));
                        indexes->ChangeValue(wstr(live_path("INDEXES").string()));
                    }
                    if (!capture_.empty()) {
                        dialog->Update(); wxClientDC source(dialog); const auto size = dialog->GetClientSize();
                        wxBitmap bitmap(size.x, size.y); wxMemoryDC target(bitmap);
                        check(target.Blit(0, 0, size.x, size.y, &source, 0, 0), "Dialog capture"); target.SelectObject(wxNullBitmap);
                        const auto path = capture_.parent_path() / (capture_.stem().string() + "-modal-" + prefix + ".png");
                        check(bitmap.SaveFile(wstr(path.string()), wxBITMAP_TYPE_PNG), "Dialog capture write");
                    }
                    if (mode == 2 || mode == 0 || mode == 4) {
                        value->SetFocus();
                        wxKeyEvent key(wxEVT_CHAR_HOOK); key.m_keyCode = mode == 2 ? WXK_ESCAPE : WXK_RETURN;
                        key.SetEventObject(value); dialog->GetEventHandler()->ProcessEvent(key);
                        // wx/MSW retains IsModal until ShowModal unwinds. The
                        // return code proves EndModal ran inside this callback.
                        check(dialog->GetReturnCode() == (mode == 2 ? wxID_CANCEL : wxID_OK),
                              mode == 2 ? "Escape did not cancel" : "Enter did not accept");
                    } else if (mode == 3) dialog->Close();
                    else {
                        wxCommandEvent event(wxEVT_BUTTON, mode == 1 ? wxID_CANCEL : wxID_OK);
                        dialog->GetEventHandler()->ProcessEvent(event);
                    }
                } catch (const std::exception& e) {
                    m1_ok_ = false; m1_error_ = e.what();
                    if (dialog->IsModal()) dialog->EndModal(wxID_CANCEL);
                }
            };
        };
        auto command = [&](const std::string& line) {
            control<wxTextCtrl>(frame_, "COMMAND_BOX")->ChangeValue(wstr(line)); live_action("command");
        };
        try {
            check(m1_ok_, m1_error_);
            check(live_.ok(), live_.error);
            switch (m1_step_++) {
            case 0: {
                auto* bar = frame_->GetMenuBar();
                check(bar && bar->GetMenuCount() == 7, "Seven native menu headings including Record");
                const std::vector<wxString> labels{"File", "Workspace", "Table", "View", "Tools", "Help"};
                for (unsigned i = 0; i < labels.size(); ++i) check(bar->GetMenuLabelText(i) == labels[i], "Native menu order");
                menu("MI3_1");
                auto* focus = control<wxTextCtrl>(frame_, "COMMAND_BOX"); focus->SetFocus();
                for (int mode : {1, 2, 3}) for (const auto* id : {"MI0_0", "MI0_1", "MI0_2", "MI0_3", "MI4_2"}) {
                    probe({}, mode); menu(id);
                    check(!live_pending_.valid() && !workflow_dialog_ && wxWindow::FindFocus() == focus,
                          "Cancel changed state, left modal lifetime or lost focus");
                }
                check(m1_ok_, m1_error_); submit_live({}); return;
            }
            case 1:
                check(live_.areas.empty() && live_.desk.workspace_count == 1, "Cancel mutated native state");
                probe("M1_ROOT"); menu("MI0_0"); return;
            case 2:
                check(live_.desk.workspace_count == 2 && live_.areas.empty(), "New root");
                probe({}); menu("MI0_1"); return;
            case 3:
                check(live_.areas.size() == 1 && live_.command_opened_tables == 1, "Open current root directory");
                probe("M1_CHILD"); menu("MI1_0"); return;
            case 4:
                check(live_.desk.workspace_count == 3 && live_.areas.size() == 1 && live_.areas[0].workspace != live_.desk.current_handle,
                      "New empty child activation");
                probe((live_path("WORKSPACES") / "Legacy load.dtschema").string(), 4); menu("MI0_2"); return;
            case 5:
                check(live_.areas.size() == 2 && live_.command_opened_tables == 1, "Load child schema");
                table_action("refresh"); return;
            case 6:
                check(!live_.table.rows.empty() && live_.table.rows[0].values[0] == "Ada", "Modal Load actual row readback");
                command("SWITCH M1_ROOT"); return;
            case 7:
                m1_single_ = live_.home / "M1 single image.minidb";
                probe(m1_single_.string()); menu("MI0_3"); return;
            case 8: {
                check(live_.saved_image == m1_single_, "Save completion result");
                auto image = session_.inspect_image_file(m1_single_).get();
                check(table_count(image) == 1, "Save excludes nested tables");
                m1_nested_ = live_.home / "M1 nested image.minidb";
                probe(m1_nested_.string(), 0, true); menu("MI0_3"); return;
            }
            case 9: {
                auto image = session_.inspect_image_file(m1_nested_).get();
                check(live_.saved_image == m1_nested_ && table_count(image) == 2, "Save includes child tables");
                probe("M1_PEER"); menu("MI0_0"); return;
            }
            case 10:
                check(live_.desk.workspace_count == 4 && live_.areas.size() == 2, "Peer workspace preserves root and child");
                command("SWITCH M1_CHILD"); return;
            case 11:
                probe((live_path("SCRIPTS") / "modal & script.dts").string()); menu("MI4_2"); return;
            default:
                check(live_.areas.size() == 2 && live_path("DBF") == live_path("DATA") / "dbf/peer" &&
                      live_.transcript.find("modal & script.dts") != std::string::npos, "Modal script executed the chosen path");
                modal_probe_ = {}; check(m1_dialogs_ == 23, "All repeated modal lifetimes exercised");
                show_live_tables(); capture_delay_ = 6; return;
            }
        } catch (const std::exception& e) {
            m1_ok_ = false; m1_error_ = e.what(); modal_probe_ = {}; capture_delay_ = 6;
        }
    }
    void advance_loadview_smoke() {
        loadview_ok_ = loadview_ok_ && live_.ok();
        auto* main = dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_));
        auto* details = dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("LIVE_DETAILS", frame_));
        std::string line;
        switch (loadview_step_++) {
        case 0: line = "DO x64"; break;
        case 1: line = "WORKSPACE OPEN dbf"; break;
        case 2:
            loadview_ok_ = loadview_ok_ && live_.areas.size() == 1 && live_.command_images.empty() &&
                main->GetSelection() == 1 && details->GetSelection() == 1 && live_areas_->GetItemCount() == 1;
            main->SetSelection(2); image_selection();
            loadview_ok_ = loadview_ok_ && image_tree_.nodes.empty() && image_info_->GetItemCount() >= 4 &&
                wxWindow::FindWindowByName("IMAGE_ENTRY", frame_)->IsEnabled();
            line = "SET PATH BIN " + (live_.home / "bin").string(); break;
        case 3: line = "VDISK MOUNT"; break;
        case 4: line = "WORKSPACE LOAD PathImage MEMO RAM"; break;
        case 5:
            loadview_ok_ = loadview_ok_ && main->GetSelection() == 2 && image_tree_.nodes.size() == 1 &&
                image_tree_.nodes[0].scan.ok && image_info_->GetItemCount() > 8 && live_.areas.size() == 2 &&
                live_.command_images.size() == 1 && live_.command_images[0].opened_areas.size() == 1;
            image_action("tables");
            loadview_ok_ = loadview_ok_ && main->GetSelection() == 1 && details->GetSelection() == 1 && live_areas_->GetItemCount() == 2;
            main->SetSelection(0); main->SetSelection(2);
            submit_live({}); return;
        case 6:
            loadview_ok_ = loadview_ok_ && live_.command_images.empty() && image_tree_.nodes.size() == 1;
            line = "WORKSPACE LOAD DoesNotExist MEMO RAM"; break;
        case 7:
            loadview_ok_ = loadview_ok_ && live_.command_images.empty() && live_.command_opened_tables == 0 && image_tree_.nodes.size() == 1;
            image_action("tables"); main->SetSelection(2); submit_live({}); return;
        default:
            loadview_ok_ = loadview_ok_ && main->GetSelection() == 2 && image_tree_.nodes.size() == 1 && image_info_->GetItemCount() > 8;
            capture_delay_ = 6; return;
        }
        control<wxTextCtrl>(frame_, "COMMAND_BOX")->ChangeValue(wstr(line));
        live_action("command");
    }
    void advance_paths_smoke() {
        paths_ok_ = paths_ok_ && live_.ok();
        Request r; r.action = Action::Command;
        switch (paths_step_++) {
        case 0:
            paths_original_catalog_ = live_path("DATA") / "workspaces/WORKSPACES.dbf";
            paths_ok_ = paths_ok_ && follow_catalog_ && snapshot_.path == paths_original_catalog_ &&
                live_.default_catalog == paths_original_catalog_ && live_path("DBF") == live_path("DATA") / "dbf/lesson space" &&
                paths_grid_->GetItemCount() == static_cast<long>(live_.paths.size());
            control<wxTextCtrl>(frame_, "COMMAND_BOX")->ChangeValue("SET PATH WORKSPACES alternate workspaces");
            live_action("command"); return;
        case 1:
            paths_ok_ = paths_ok_ && snapshot_.path == live_.default_catalog && snapshot_.path != paths_original_catalog_;
            path_->SetValue(wstr(paths_original_catalog_.string())); refresh(); return;
        case 2:
            paths_ok_ = paths_ok_ && !follow_catalog_ && snapshot_.path == paths_original_catalog_;
            r.name = "SET PATH WORKSPACES missing catalog"; break;
        case 3:
            paths_ok_ = paths_ok_ && snapshot_.path == paths_original_catalog_ &&
                live_.default_catalog == live_path("DATA") / "missing catalog/WORKSPACES.dbf";
            paths_action("reset"); return;
        case 4:
            paths_ok_ = paths_ok_ && live_path("DBF") == live_path("DATA") / "dbf" && live_.default_catalog == paths_original_catalog_;
            paths_action("init"); return;
        default:
            paths_ok_ = paths_ok_ && live_path("DBF") == live_path("DATA") / "dbf/lesson space" &&
                live_.transcript.find("dottalkpp.ini") != std::string::npos;
            paths_action("catalog"); paths_action("show");
            paths_ok_ = paths_ok_ && follow_catalog_ && fs::path(path_->GetValue().ToStdWstring()) == paths_original_catalog_;
            capture_delay_ = 6; return;
        }
        submit_live(std::move(r));
    }
    void advance_navigation_smoke() {
        if (!navigation_ok_ && !navigation_failed_at_) navigation_failed_at_ = navigation_step_;
        navigation_ok_ = navigation_ok_ && live_.ok() && live_.desk.healthy();
        auto handle = [&](const char* name) {
            for (const auto& ws : live_.desk.workspaces) if (ws.name == name) return ws.handle;
            return std::uint64_t{};
        };
        auto area_slot = [&](const char* name) {
            for (const auto& area : live_.areas) if (area.workspace == handle(name)) return area.slot;
            return -1;
        };
        auto check = [&](wxCheckBox* box, bool value) {
            box->SetValue(value); wxCommandEvent event(wxEVT_CHECKBOX, box->GetId()); event.SetEventObject(box);
            navigation_ok_ = box->GetEventHandler()->ProcessEvent(event) && navigation_ok_;
        };
        auto browse_workspace = [&](const char* name, bool activate = false) {
            const NavKey key{handle(name), 0};
            if (!nav_items_.count(key)) { navigation_ok_ = false; return; }
            live_tree_->SelectItem(nav_items_.at(key));
            if (activate) {
                wxTreeEvent event(wxEVT_TREE_ITEM_ACTIVATED, live_tree_, nav_items_.at(key));
                navigation_ok_ = live_tree_->GetEventHandler()->ProcessEvent(event) && navigation_ok_;
            }
        };
        auto activate_first = [&] {
            if (area_visible_.empty()) { navigation_ok_ = false; capture_delay_ = 6; return; }
            live_areas_->SetItemState(0, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED);
            wxListEvent event(wxEVT_LIST_ITEM_ACTIVATED, live_areas_->GetId()); event.SetIndex(0); event.SetEventObject(live_areas_);
            navigation_ok_ = live_areas_->GetEventHandler()->ProcessEvent(event) && navigation_ok_;
        };
        Request r;
        switch (navigation_step_++) {
        case 0: r.action = Action::NewWorkspace; r.name = "NavParent"; break;
        case 1: r.action = Action::NewWorkspace; r.name = "NavChild"; r.workspace = handle("NavParent"); break;
        case 2: r.action = Action::NewWorkspace; r.name = "NavPeer"; break;
        case 3: r.action = Action::SwitchWorkspace; r.workspace = handle("NavParent"); break;
        case 4: case 6: case 8: r.action = Action::OpenCopy; r.path = table_source_; break;
        case 5: r.action = Action::SwitchWorkspace; r.workspace = handle("NavChild"); break;
        case 7: r.action = Action::SwitchWorkspace; r.workspace = handle("NavPeer"); break;
        case 9: r.action = Action::Recursion; r.enabled = false; break;
        case 10:
            browse_workspace("NavParent");
            navigation_ok_ = navigation_ok_ && live_selected_ == handle("NavParent") && area_visible_.size() == 2 &&
                live_.desk.current_handle == handle("NavPeer") && !live_.desk.recursion_enabled;
            check(area_nested_, false); navigation_ok_ = navigation_ok_ && area_visible_.size() == 1;
            area_query_->SetValue("child"); navigation_ok_ = navigation_ok_ && area_visible_.empty();
            check(area_nested_, true);
            navigation_ok_ = navigation_ok_ && area_visible_.size() == 1 &&
                live_.areas[area_visible_[0]].workspace == handle("NavChild") && area_visible_[0] != 0;
            activate_first(); return;
        case 11:
            navigation_ok_ = navigation_ok_ && live_.desk.current_handle == handle("NavPeer") &&
                live_.desk.current_engine_area == area_slot("NavChild");
            area_query_->SetValue("parent"); area_query_->SetValue("child");
            navigation_ok_ = navigation_ok_ && live_areas_->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED) == 0;
            check(area_all_, true); area_query_->SetValue("peer");
            navigation_ok_ = navigation_ok_ && area_visible_.size() == 1 &&
                live_.areas[area_visible_[0]].workspace == handle("NavPeer") && !area_nested_->IsEnabled();
            activate_first(); return;
        case 12:
            navigation_ok_ = navigation_ok_ && live_.desk.current_engine_area == area_slot("NavPeer");
            browse_workspace("NavChild", true); return;
        case 13:
            navigation_ok_ = navigation_ok_ && live_.desk.current_handle == handle("NavChild") && live_selected_ == handle("NavChild");
            check(area_all_, false); area_query_->SetValue(wxEmptyString); browse_workspace("NavParent");
            navigation_ok_ = navigation_ok_ && area_visible_.size() == 2 && live_.areas.size() == 3 &&
                live_.desk.workspace_count == 4 && !live_.desk.recursion_enabled &&
                live_areas_->GetItemText(1, 2) == wstr(std::to_string(area_slot("NavChild")));
            r.action = Action::NewWorkspace; r.name = "NavGrandchild"; r.workspace = handle("NavChild"); break;
        case 14: r.action = Action::NewWorkspace; r.name = "NavEmpty"; break;
        case 15: {
            navigation_ok_ = navigation_ok_ && live_.desk.current_handle == handle("NavEmpty") &&
                live_current_->GetLabel().Contains("Selected table: none") &&
                live_tree_->GetItemParent(nav_items_.at({handle("NavGrandchild"), 0})) == nav_items_.at({handle("NavChild"), 0});
            browse_workspace("NavGrandchild");
            wxKeyEvent enter(wxEVT_CHAR_HOOK); enter.m_keyCode = WXK_RETURN;
            navigation_ok_ = live_tree_->GetEventHandler()->ProcessEvent(enter) && navigation_ok_; return;
        }
        case 16:
            navigation_ok_ = navigation_ok_ && live_.desk.current_handle == handle("NavGrandchild") && live_current_->GetLabel().Contains("Selected table: none");
            r.action = Action::OpenCopy; r.path = table_source_; break;
        case 17: {
            dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_))->SetSelection(1);
            wxKeyEvent find(wxEVT_CHAR_HOOK); find.m_keyCode = 'F'; find.m_controlDown = true;
            live_tree_->GetEventHandler()->ProcessEvent(find);
            navigation_ok_ = navigation_ok_ && wxWindow::FindFocus() == nav_query_;
            for (const auto& area : live_.areas) if (area.workspace == handle("NavChild")) navigation_stale_ = {area.workspace, area.handle};
            live_tree_->SelectItem(nav_items_.at(navigation_stale_));
            navigation_ok_ = navigation_ok_ && live_selected_ == handle("NavChild") && nav_area_ == navigation_stale_.second &&
                live_.desk.current_handle == handle("NavGrandchild") && live_.desk.current_engine_area == area_slot("NavGrandchild");
            nav_query_->SetValue("nothing matches this");
            navigation_ok_ = navigation_ok_ && nav_items_.empty() && nav_area_ == navigation_stale_.second &&
                !live_tree_->GetSelection().IsOk();
            wxKeyEvent escape(wxEVT_CHAR_HOOK); escape.m_keyCode = WXK_ESCAPE;
            nav_query_->GetEventHandler()->ProcessEvent(escape);
            navigation_ok_ = navigation_ok_ && nav_key(live_tree_->GetSelection()) == navigation_stale_;
            live_tree_->Collapse(nav_items_.at({handle("NavPeer"), 0}));
            break; // observe/refresh
        }
        case 18: {
            navigation_ok_ = navigation_ok_ && nav_key(live_tree_->GetSelection()) == navigation_stale_ &&
                !live_tree_->IsExpanded(nav_items_.at({handle("NavPeer"), 0}));
            nav_query_->SetValue(live_.areas.front().name);
            navigation_ok_ = navigation_ok_ && nav_key(live_tree_->GetSelection()) == navigation_stale_;
            nav_query_->SetValue(wxEmptyString);
            wxKeyEvent enter(wxEVT_CHAR_HOOK); enter.m_keyCode = WXK_RETURN;
            navigation_ok_ = live_tree_->GetEventHandler()->ProcessEvent(enter) && navigation_ok_; return;
        }
        case 19: {
            navigation_ok_ = navigation_ok_ && live_.desk.current_handle == handle("NavGrandchild") &&
                live_.desk.current_engine_area == area_slot("NavChild") &&
                live_tree_->GetItemText(nav_items_.at(navigation_stale_)).Contains("[selected]") &&
                live_current_->GetLabel().Contains("in NavChild");
            auto menu = nav_menu({handle("NavParent"), 0});
            wxCommandEvent event(wxEVT_MENU, menu->FindItemByPosition(0)->GetId());
            navigation_ok_ = menu->ProcessEvent(event) && navigation_ok_; return;
        }
        case 20: {
            navigation_ok_ = navigation_ok_ && live_.desk.current_handle == handle("NavParent");
            navigation_old_menu_ = nav_menu(navigation_stale_);
            wxCommandEvent event(wxEVT_MENU, navigation_old_menu_->FindItemByPosition(0)->GetId());
            navigation_ok_ = navigation_old_menu_->ProcessEvent(event) && navigation_ok_; return;
        }
        case 21:
            navigation_ok_ = navigation_ok_ && live_.desk.current_handle == handle("NavParent") && live_.desk.current_engine_area == area_slot("NavChild");
            r.action = Action::Command; r.name = "SWITCH NavChild"; break;
        case 22: r.action = Action::Command; r.name = "CLOSE"; break;
        case 23: {
            navigation_ok_ = navigation_ok_ && !nav_exists(navigation_stale_) && !nav_items_.count(navigation_stale_) &&
                nav_area_ == 0 && area_slot("NavGrandchild") >= 0;
            wxCommandEvent event(wxEVT_MENU, navigation_old_menu_->FindItemByPosition(0)->GetId());
            navigation_old_menu_->ProcessEvent(event);
            navigation_ok_ = navigation_ok_ && !live_pending_.valid() && status_->GetLabel().Contains("no longer open");
            r.action = Action::OpenCopy; r.path = table_source_; break;
        }
        case 24: {
            navigation_ok_ = navigation_ok_ && !nav_exists(navigation_stale_) && area_slot("NavChild") >= 0;
            wxCommandEvent event(wxEVT_MENU, navigation_old_menu_->FindItemByPosition(0)->GetId());
            navigation_old_menu_->ProcessEvent(event);
            navigation_ok_ = navigation_ok_ && !live_pending_.valid() && status_->GetLabel().Contains("no longer open");
            r.action = Action::Command; r.name = "WORKDESK"; break;
        }
        case 25:
            navigation_ok_ = navigation_ok_ && live_.transcript.find("NavGrandchild") != std::string::npos && live_.desk.healthy();
            r.action = Action::Command; r.name = "GPS"; break;
        default:
            navigation_ok_ = navigation_ok_ && live_.transcript.find(live_.areas.front().name) != std::string::npos &&
                live_.desk.current_handle == handle("NavChild") && live_.desk.current_engine_area == area_slot("NavChild");
            browse_workspace("NavParent");
            navigation_ok_ = navigation_ok_ && area_visible_.size() == 3 && live_.areas.size() == 4 && live_.desk.workspace_count == 6;
            dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_))->SetSelection(1);
            dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("LIVE_DETAILS", frame_))->ChangeSelection(1);
            navigation_ok_ = navigation_ok_ && status_->GetLabel().StartsWith("Live session |");
            capture_delay_ = 6; return;
        }
        submit_live(std::move(r));
    }
    void advance_store_smoke() {
        store_smoke_ok_ = store_smoke_ok_ && live_.ok();
        Request r;
        switch (store_smoke_step_++) {
        case 0: r.action = Action::OpenCopy; r.path = table_source_; break;
        case 1: r.action = Action::Command; r.name = "BROWSE"; break;
        case 2:
        case 4:
            table_rows_->SetItemState(0, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED); table_selection();
            table_fields_->SetItemState(0, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED);
            table_action("store_image"); return;
        case 3:
            store_smoke_ok_ = store_smoke_ok_ && live_.table.pending_records == 1;
            table_action("rollback"); return;
        case 5:
            store_smoke_ok_ = store_smoke_ok_ && live_.table.pending_records == 1;
            table_action("commit"); return;
        default:
            store_smoke_ok_ = store_smoke_ok_ && live_.table.pending_records == 0;
            table_rows_->SetItemState(0, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED); table_selection();
            table_fields_->SetItemState(0, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED);
            table_action("image"); return;
        }
        submit_live(std::move(r));
    }
    void poll() {
        if (workflow_dialog_) return;
        ++ticks_;
        if (live_pending_.valid() && live_pending_.wait_for(std::chrono::milliseconds(0)) == std::future_status::ready) {
            const auto previous_workspace = live_.desk.current_handle;
            live_ = live_pending_.get();
            if (live_.ok() && live_.desk.current_handle != previous_workspace) {
                live_selected_ = live_.desk.current_handle; nav_area_ = 0;
            }
            render_live(); render_paths(); sync_catalog();
            if (live_.exit_requested) { frame_->Close(); return; }
            wxWindow::FindWindowByName("LIVE_TOOLS", frame_)->Enable(); recursion_->Enable();
            wxWindow::FindWindowByName("COMMAND_ROW", frame_)->Enable();
            wxWindow::FindWindowByName("TABLE_TOOLS", frame_)->Enable();
            wxWindow::FindWindowByName("EDIT_TOOLS", frame_)->Enable();
            wxWindow::FindWindowByName("PATHS_TOOLS", frame_)->Enable();
            if (live_.command_opened_tables) show_live_tables();
            if (!live_.command_images.empty()) show_command_images();
            if (dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_))->GetSelection() == 2) image_selection();
            if (image_exporting_) {
                image_exporting_ = false;
                if (live_.ok()) image_exports_[exporting_location_] = live_.exported_image;
                image_selection();
                const auto message = live_.ok() ? "Export verified: " + live_.exported_image.filename().string() :
                    "Export refused: " + live_.error;
                status_->SetLabel(wstr(message)); status_->SetToolTip(wstr(live_.ok() ? live_.exported_image.string() : live_.error));
                if (export_smoke_) {
                    std::ifstream file(export_smoke_path_, std::ios::binary);
                    const std::string back{std::istreambuf_iterator<char>(file), {}};
                    export_smoke_ok_ = export_smoke_ok_ && live_.ok() && live_.exported_image == export_smoke_path_ &&
                        live_.areas.empty() && live_.images.empty() && image_list_->GetSelection() == 1 &&
                        image_tree_.nodes.size() == 2 && back == image_tree_.nodes[1].payload &&
                        image_exports_.count(exporting_location_) == 1;
                    capture_delay_ = 6;
                }
            }
            if (live_.browse_requested) {
                dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_))->ChangeSelection(1);
                dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("LIVE_DETAILS", frame_))->ChangeSelection(3);
            }
            if (live_smoke_) advance_live_smoke();
            if (browse_smoke_) advance_browse_smoke();
            if (edit_smoke_) advance_edit_smoke();
            if (image_loading_) {
                image_loading_ = false;
                image_selection();
                if (!catalog_image_payload_.empty()) {
                    if (live_.ok()) {
                        image_tree_ = {}; image_exports_.clear(); image_list_->Clear(); image_info_->DeleteAllItems();
                        image_provenance_ = catalog_image_provenance_;
                        image_pending_ = session_.inspect_image(std::move(catalog_image_payload_));
                        show_live_tables();
                    }
                    catalog_image_payload_.clear(); catalog_image_provenance_.clear();
                }
                if (live_.ok()) {
                    live_selected_ = live_.desk.current_handle; nav_area_ = 0; render_live();
                    dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_))->SetSelection(1);
                    if (nested_smoke_)
                        dynamic_cast<wxNotebook*>(wxWindow::FindWindowByName("MAIN", frame_))->SetSelection(2);
                } else status_->SetLabel(wstr("Hydration refused: " + live_.error));
                if (image_smoke_) capture_delay_ = 6;
            }
            if (save_smoke_) advance_save_smoke();
            if (memo_image_smoke_) advance_memo_image_smoke();
            if (store_smoke_) advance_store_smoke();
            if (navigation_smoke_) advance_navigation_smoke();
        }
        if (memo_target_pending_.valid() && memo_target_pending_.wait_for(std::chrono::milliseconds(0)) == std::future_status::ready) {
            auto target = memo_target_pending_.get();
            wxWindow::FindWindowByName("LIVE_TOOLS", frame_)->Enable(); recursion_->Enable();
            wxWindow::FindWindowByName("COMMAND_ROW", frame_)->Enable();
            wxWindow::FindWindowByName("TABLE_TOOLS", frame_)->Enable();
            wxWindow::FindWindowByName("EDIT_TOOLS", frame_)->Enable();
            if (!target.error.empty()) {
                table_note_->SetLabel(wstr(target.error));
                if (store_smoke_) { store_smoke_ok_ = false; capture_delay_ = 6; }
            } else {
                fs::path path;
                if (store_smoke_) path = store_image_source_;
                else {
                    wxFileDialog dialog(frame_, wstr("Buffer image in " + target.title), wxEmptyString, wxEmptyString,
                        "MINIDB images (*.minidb)|*.minidb|All files (*.*)|*.*", wxFD_OPEN | wxFD_FILE_MUST_EXIST);
                    if (dialog.ShowModal() == wxID_OK) path = fs::path(dialog.GetPath().ToStdWstring());
                }
                if (!path.empty()) {
                    Request r; r.action = Action::StoreImage; r.path = std::move(path); r.edit = std::move(target.edit);
                    submit_live(std::move(r));
                } else table_note_->SetLabel("Image storage cancelled; field unchanged.");
            }
        }
        if (field_pending_.valid() && field_pending_.wait_for(std::chrono::milliseconds(0)) == std::future_status::ready) {
            auto value = field_pending_.get();
            if (!value.text.empty() && wstr(value.text).empty()) {
                value.editable = false; value.edit_reason = "Text encoding cannot be displayed; use the command console.";
            }
            wxWindow::FindWindowByName("LIVE_TOOLS", frame_)->Enable(); recursion_->Enable();
            wxWindow::FindWindowByName("COMMAND_ROW", frame_)->Enable();
            wxWindow::FindWindowByName("TABLE_TOOLS", frame_)->Enable();
            wxWindow::FindWindowByName("EDIT_TOOLS", frame_)->Enable();
            if (null_requested_) {
                null_requested_ = false;
                if (!value.error.empty()) { table_note_->SetLabel(wstr(value.error)); return; }
                edit_request_.action = Action::SetNullField;
                edit_request_.slot = edit_request_.edit.slot;
                edit_request_.record = edit_request_.edit.record;
                edit_request_.edit.expected_value = value.text;
                if (table_workflow("null", edit_request_)) submit_live(edit_request_);
                return;
            }
            if (edit_requested_ && value.error.empty() && value.editable) {
                edit_requested_ = false;
                wxTextEntryDialog edit(frame_, "Literal value. Buffer value stages the edit; Commit table writes it.",
                    wstr(value.title), wstr(value.text), wxOK | wxCANCEL | wxTE_MULTILINE | wxRESIZE_BORDER);
                edit.SetSize(wxSize(720, 420));
                if (auto* button = dynamic_cast<wxButton*>(edit.FindWindow(wxID_OK))) button->SetLabel("Buffer value");
                if (edit_smoke_) {
                    edit.SetValue(edit_smoke_step_ <= 3 ? "GUI buffered value" : "GUI committed value");
                    edit.CallAfter([&edit] { edit.EndModal(wxID_OK); });
                }
                if (m3_smoke_) {
                    edit.SetValue("M3 memo text\nSecond line 'quoted' & literal");
                    edit.CallAfter([&edit] { edit.EndModal(wxID_OK); });
                }
                if (edit.ShowModal() == wxID_OK) {
                    edit_request_.edit.expected_value = value.text;
                    edit_request_.edit.value = edit.GetValue().ToStdString(wxConvUTF8);
                    submit_live(edit_request_);
                }
                return;
            }
            wxDialog dialog(frame_, wxID_ANY, wstr(value.title), wxDefaultPosition, wxSize(800, 550),
                wxDEFAULT_DIALOG_STYLE | wxRESIZE_BORDER);
            auto* layout = new wxBoxSizer(wxVERTICAL);
            auto* note = new wxStaticText(&dialog, wxID_ANY, wstr(value.error.empty() ?
                std::to_string(value.bytes) + " bytes | Read only" + (value.pending ? " | Buffered value" : "") +
                    (edit_requested_ ? " | " + value.edit_reason : "") : value.error));
            auto* content = new wxTextCtrl(&dialog, wxID_ANY, wstr(value.text), wxDefaultPosition, wxDefaultSize,
                wxTE_MULTILINE | wxTE_READONLY | wxHSCROLL);
            content->SetFont(wxFontInfo(10).Family(wxFONTFAMILY_TELETYPE));
            layout->Add(note, 0, wxEXPAND | wxALL, 10); layout->Add(content, 1, wxEXPAND | wxALL, 10);
            layout->Add(dialog.CreateButtonSizer(wxOK), 0, wxALIGN_RIGHT | wxALL, 10); dialog.SetSizer(layout);
            if (browse_smoke_) {
                browse_smoke_ok_ = browse_smoke_ok_ && value.error.empty() && value.memo &&
                    content->GetValue().Contains("Workbench memo record 7") && !content->IsEditable();
                dialog.CallAfter([&dialog] { dialog.EndModal(wxID_OK); });
            }
            dialog.ShowModal();
            edit_requested_ = false;
            if (browse_smoke_) capture_delay_ = 6;
        }
        if (image_pending_.valid() && image_pending_.wait_for(std::chrono::milliseconds(0)) == std::future_status::ready) {
            image_tree_ = image_pending_.get();
            if (!image_tree_.provenance.empty()) image_provenance_ = image_tree_.provenance;
            for (const auto& image : image_tree_.nodes)
                image_list_->Append(wstr(std::string(image.depth * 2, ' ') + image.location));
            if (!image_tree_.nodes.empty()) image_list_->SetSelection(0);
            if (nested_smoke_ && image_tree_.nodes.size() > 1) image_list_->SetSelection(1);
            image_selection();
            if (store_smoke_) {
                std::ifstream file(store_image_source_, std::ios::binary);
                const std::string bytes{std::istreambuf_iterator<char>(file), {}};
                store_smoke_ok_ = store_smoke_ok_ && image_tree_.error.empty() && !image_tree_.nodes.empty() &&
                    image_tree_.nodes[0].payload == bytes && image_provenance_.find("record 1 / field IMAGE") != std::string::npos;
                capture_delay_ = 6;
            }
            if (export_smoke_) {
                export_smoke_ok_ = export_smoke_ok_ && image_tree_.error.empty() && image_tree_.nodes.size() == 2 &&
                    image_tree_.nodes[1].depth == 1;
                if (!export_smoke_ok_) capture_delay_ = 6;
                else { image_list_->SetSelection(1); image_selection(); image_action("export"); }
            }
            if (image_smoke_) image_action("hydrate");
            if (save_smoke_) image_action("hydrate");
            if (memo_image_smoke_) {
                memo_image_ok_ = memo_image_ok_ && image_tree_.error.empty() && image_tree_.nodes.size() == 2 &&
                    image_provenance_.find(" / record 1 / field SNAPSHOT / committed memo") != std::string::npos;
                if (image_tree_.nodes.size() != 2) { capture_delay_ = 6; }
                else { image_list_->SetSelection(1); image_selection(); image_action("child"); }
            }
        }
        if (pending_.valid() && pending_.wait_for(std::chrono::milliseconds(0)) == std::future_status::ready) {
            snapshot_ = pending_.get();
            path_->Enable();
            rebuild();
            if (!snapshot_.ok()) status_->SetLabel(wstr(snapshot_.code + ": " + snapshot_.error));
            if (!smoke_.empty()) {
                const auto current_count = visible_.size();
                history_->SetValue(true);
                rebuild();
                history_ok_ = visible_.size() == snapshot_.entries.size() && visible_.size() >= current_count;
                if (!visible_.empty()) {
                    const auto& first = snapshot_.entries[visible_.front()];
                    filter_->ChangeValue(wstr("#" + std::to_string(first.id) + " "));
                    rebuild();
                    filter_ok_ = visible_.size() == 1 && selected_ == first.id;
                    filter_->ChangeValue(wxEmptyString);
                }
                history_->SetValue(false);
                rebuild();
                for (std::size_t i = 0; i < visible_.size(); ++i)
                    if (snapshot_.entries[visible_[i]].container.ok) {
                        list_->SetSelection(static_cast<int>(i)); selection(); break;
                    }
                if (image_smoke_ || export_smoke_) image_action("inspect");
                else if (!live_smoke_ && !browse_smoke_ && !edit_smoke_ && !save_smoke_ && !memo_image_smoke_ && !store_smoke_ && !navigation_smoke_ && !paths_smoke_ && !loadview_smoke_ && !openload_smoke_ && !m1_smoke_ && !catalog_flow_smoke_ && !m3_smoke_) capture_delay_ = 6;
            }
        }
        if (catalog_refresh_queued_ && !pending_.valid()) { catalog_refresh_queued_ = false; refresh(); }
        if (paths_smoke_ && !live_pending_.valid() && !pending_.valid() && !catalog_refresh_queued_ && !capture_delay_)
            advance_paths_smoke();
        if (loadview_smoke_ && !live_pending_.valid() && !pending_.valid() && !catalog_refresh_queued_ && !capture_delay_)
            advance_loadview_smoke();
        if (openload_smoke_ && !live_pending_.valid() && !pending_.valid() && !catalog_refresh_queued_ && !capture_delay_)
            advance_openload_smoke();
        if (m1_smoke_ && !live_pending_.valid() && !pending_.valid() && !catalog_refresh_queued_ && !capture_delay_)
            advance_m1_smoke();
        if (catalog_flow_smoke_ && !live_pending_.valid() && !image_pending_.valid() && !pending_.valid() && !catalog_refresh_queued_ && !capture_delay_)
            advance_catalog_flow_smoke();
        if (m3_smoke_ && !live_pending_.valid() && !field_pending_.valid() && !pending_.valid() && !catalog_refresh_queued_ && !capture_delay_)
            advance_m3_smoke();
        if (capture_delay_ && --capture_delay_ == 0) finish_smoke();
        if (!smoke_.empty() && ticks_ > 600 && !smoke_done_) {
            std::ofstream out(smoke_); out << "FAIL inspection timeout\n";
            frame_->Close();
        }
    }
    void rebuild() {
        list_->Freeze();
        list_->Clear(); visible_.clear();
        const auto filter = filter_->GetValue().Lower();
        int match = wxNOT_FOUND;
        for (const auto [i, depth] : dottalk::workbench::catalog_order(snapshot_)) {
            const auto& e = snapshot_.entries[i];
            if (!history_->GetValue() && e.superseded) continue;
            const auto label = e.value("WS_NAME") + "  #" + std::to_string(e.id) +
                "  [" + e.value("FMT") + "]" + (e.superseded ? "  (superseded)" : "");
            if (!filter.empty() && !wstr(label).Lower().Contains(filter)) continue;
            if (e.id == selected_) match = static_cast<int>(visible_.size());
            visible_.push_back(i);
            list_->Append(wstr(std::string(depth * 3, ' ') + label));
        }
        list_->Thaw();
        if (match == wxNOT_FOUND && !visible_.empty()) match = 0;
        list_->SetSelection(match);
        selection();
    }
    void selection() {
        identity_->DeleteAllItems(); members_->DeleteAllItems(); posture_->DeleteAllItems();
        control<wxButton>(frame_, "CAT_HYDRATE")->Disable(); control<wxButton>(frame_, "CAT_LOAD")->Disable();
        control<wxStaticText>(frame_, "CAT_NOTE")->SetLabel("Select a saved workspace.");
        const auto n = list_->GetSelection();
        if (n == wxNOT_FOUND || static_cast<std::size_t>(n) >= visible_.size()) {
            status_->SetLabel(snapshot_.ok() ? text("gui.catalog.no_match", "No saved workspaces match this view.")
                                           : wstr(snapshot_.code + ": " + snapshot_.error));
            return;
        }
        const auto& e = snapshot_.entries[visible_[static_cast<std::size_t>(n)]];
        control<wxButton>(frame_, "CAT_HYDRATE")->Enable(e.action() == dottalk::workbench::CatalogAction::Hydrate);
        control<wxButton>(frame_, "CAT_LOAD")->Enable(e.action() == dottalk::workbench::CatalogAction::LoadDefinition);
        control<wxStaticText>(frame_, "CAT_NOTE")->SetLabel(wstr(e.action_note()));
        selected_ = e.id;
        row(identity_, {"View", "Saved catalog record; not a live workspace"});
        row(identity_, {"Durable workspace ID", std::to_string(e.id)});
        row(identity_, {"Parent workspace ID", e.parent_id ? std::to_string(e.parent_id) : "Not recorded"});
        row(identity_, {"Previous saved version ID", e.previous_id ? std::to_string(e.previous_id) : "None recorded"});
        row(identity_, {"Catalog record", std::to_string(e.record)});
        if (e.parent_id) {
            const auto parent = std::find_if(snapshot_.entries.begin(), snapshot_.entries.end(),
                [&](const auto& p) { return p.id == e.parent_id; });
            row(identity_, {"Parent record", parent == snapshot_.entries.end() ? "Not present in this snapshot"
                               : parent->value("WS_NAME") + (parent->superseded ? " (superseded)" : "")});
        }
        for (const auto* field : {"WS_NAME", "FMT", "FLAVOR", "SAVED_AT", "AUTHOR", "SIZE_B",
                                  "EST_HYD_B", "DBF_ROOT", "IDX_ROOT", "TREE_DEPTH", "DEPTH", "SELF_REF"})
            row(identity_, {field, e.value(field)});
        const auto& container = e.container;
        if (container.ok) {
            row(identity_, {"Measured RAM file bytes", std::to_string(container.ram_file_bytes)});
            row(identity_, {"Measured disk memo bytes", std::to_string(container.sidecar_file_bytes)});
            row(identity_, {"Live data", "View Live session for currently open tables"});
            row(identity_, {"Nested memo payloads", "Use Inspect image to follow live DTX objects"});
            for (const auto& member : container.files)
                row(members_, {member.relpath, std::to_string(member.length),
                    dottalk::minidb::is_memo_sidecar(member.relpath) ? "Disk memo sidecar" : "RAM file"});
        }
        const auto& definition = container.ok ? container.posture : e.payload;
        // Only text postures are previewed. Malformed binary containers are never
        // passed to a text widget as if they were a valid definition.
        if (e.error.empty()) {
            std::istringstream lines(definition);
            std::string line; unsigned index = 0;
            while (index < 1000 && std::getline(lines, line)) row(posture_, {std::to_string(++index), line});
            if (lines.peek() != EOF) row(posture_, {"...", "Preview limited to 1000 lines"});
        }
        const auto info = std::to_string(visible_.size()) + " visible / " + std::to_string(snapshot_.entries.size()) +
            " saved records | " + std::to_string(snapshot_.deleted) + " deleted records excluded | " +
            (e.error.empty() ? "Read-only snapshot" : "Payload error: " + e.error);
        status_->SetLabel(wstr(info));
        live_status();
        identity_->SetColumnWidth(1, std::max(300, identity_->GetClientSize().GetWidth() - 230));
    }
    void finish_smoke() {
        smoke_done_ = true;
        const auto projected = dottalk::workbench::navigator_view(live_, nav_query_->GetValue().ToStdString(wxConvUTF8));
        bool navigator_ok = nav_items_.size() == projected.workspaces.size() + projected.areas.size();
        for (const auto& ws : live_.desk.workspaces) if (nav_items_.count({ws.handle, 0})) {
            const auto item = nav_items_.at({ws.handle, 0});
            navigator_ok = navigator_ok && nav_key(item) == NavKey{ws.handle, 0} &&
                live_tree_->GetItemText(item).Contains("[current]") == ws.current &&
                nav_key(live_tree_->GetItemParent(item)).first == ws.parent;
        }
        for (auto index : projected.areas) {
            const auto& area = live_.areas[index]; const NavKey key{area.workspace, area.handle};
            if (!nav_items_.count(key)) { navigator_ok = false; continue; }
            const auto item = nav_items_.at(key);
            navigator_ok = navigator_ok && nav_key(item) == key &&
                nav_key(live_tree_->GetItemParent(item)) == NavKey{area.workspace, 0} &&
                live_tree_->GetItemText(item).StartsWith(wstr(std::to_string(area.slot) + ": ")) &&
                live_tree_->GetItemText(item).Contains("[selected]") == (area.slot == live_.desk.current_engine_area);
        }
        bool image_ok = true;
        if (!capture_.empty()) {
            const auto size = frame_->GetClientSize();
            wxBitmap bitmap(size.x, size.y);
            wxMemoryDC target(bitmap);
            wxClientDC source(frame_);
            image_ok = target.Blit(0, 0, size.x, size.y, &source, 0, 0);
            target.SelectObject(wxNullBitmap);
            image_ok = image_ok && bitmap.SaveFile(wxString(capture_.wstring()), wxBITMAP_TYPE_PNG);
            if (m1_smoke_) {
                const auto outer = frame_->GetSize(); wxBitmap full(outer.x, outer.y);
                wxMemoryDC dest(full); wxWindowDC window(frame_);
                image_ok = dest.Blit(0, 0, outer.x, outer.y, &window, 0, 0) && image_ok;
                dest.SelectObject(wxNullBitmap);
                const auto path = capture_.parent_path() / (capture_.stem().string() + "-menus.png");
                image_ok = full.SaveFile(wstr(path.string()), wxBITMAP_TYPE_PNG) && image_ok;
            }
            // A hidden desktop can return a successful blit of an all-black
            // surface. Such an artifact does not establish visible rendering.
            const auto pixels = bitmap.ConvertToImage();
            if (pixels.IsOk()) {
                const auto* data = pixels.GetData();
                const auto count = static_cast<std::size_t>(pixels.GetWidth()) * pixels.GetHeight() * 3;
                image_ok = image_ok && std::any_of(data, data + count, [](unsigned char p) { return p != 0; });
            } else image_ok = false;
        }
        std::ofstream out(smoke_);
        const auto size = identity_->GetSize();
        const bool layout_ok = size.x >= 400 && size.y >= 250;
        const bool ok = navigator_ok && snapshot_.ok() && !snapshot_.entries.empty() && selected_ &&
            identity_->GetItemCount() > 0 && image_ok && layout_ok && history_ok_ && filter_ok_ &&
            live_.ok() && (!live_smoke_ || live_smoke_ok_) && (!browse_smoke_ || browse_smoke_ok_) && (!edit_smoke_ || edit_smoke_ok_) &&
            (!save_smoke_ || save_smoke_ok_) &&
            (!memo_image_smoke_ || memo_image_ok_) &&
            (!export_smoke_ || (export_smoke_ok_ && !live_.exported_image.empty())) &&
            (!store_smoke_ || (store_smoke_ok_ && store_smoke_step_ >= 7 && live_.table.pending_records == 0)) &&
            (!paths_smoke_ || (paths_ok_ && paths_step_ >= 6)) &&
            (!loadview_smoke_ || (loadview_ok_ && loadview_step_ >= 9 && !image_tree_.nodes.empty())) &&
            (!openload_smoke_ || (openload_ok_ && openload_step_ >= 4)) &&
            (!m1_smoke_ || (m1_ok_ && m1_step_ >= 13)) &&
            (!m3_smoke_ || (m3_ok_ && m3_step_ >= 18)) &&
            (!catalog_flow_smoke_ || (catalog_flow_ok_ && catalog_flow_step_ >= 5)) &&
            (!navigation_smoke_ || (navigation_ok_ && navigation_step_ >= 27 && live_areas_->GetItemCount() == 3)) &&
            (!image_smoke_ || (!image_tree_.nodes.empty() && live_.images.size() == 1 && !live_.areas.empty() &&
                std::all_of(live_.areas.begin(), live_.areas.end(), [](const auto& area) { return area.ram; }))) &&
            (!nested_smoke_ || (image_tree_.nodes.size() == 2 && image_list_->GetSelection() == 1 &&
                image_tree_.nodes[1].depth == 1 && live_.areas.size() == 1 && live_.areas[0].records == 2 &&
                image_info_->GetItemCount() > 8 && image_info_->GetSize().x >= 350 && image_info_->GetSize().y >= 250));
        out << (ok ? "PASS" : "FAIL") << " generated native Workbench\n"
            << "catalog=" << snapshot_.path.string() << "\nrecords=" << snapshot_.entries.size()
            << "\ndeleted=" << snapshot_.deleted << "\nselected_ws_id=" << selected_
            << "\nidentity_rows=" << identity_->GetItemCount() << "\nmember_rows=" << members_->GetItemCount()
            << "\ngrid_width=" << size.x << "\ngrid_height=" << size.y
            << "\nhistory_ok=" << history_ok_ << "\nfilter_ok=" << filter_ok_
            << "\nui_timer_ticks=" << ticks_ << "\nerror=" << snapshot_.error
            << "\nlive_smoke=" << live_smoke_ << "\nlive_workspaces=" << live_.desk.workspace_count
            << "\nlive_areas=" << live_.areas.size() << "\nlive_error=" << live_.error
            << "\nbrowse_smoke=" << browse_smoke_ << "\nbrowse_ok=" << browse_smoke_ok_
            << "\nedit_smoke=" << edit_smoke_ << "\nedit_ok=" << edit_smoke_ok_
            << "\nsave_smoke=" << save_smoke_ << "\nsave_ok=" << save_smoke_ok_ << "\nsaved_image=" << saved_path_.string()
            << "\nmemo_image_smoke=" << memo_image_smoke_ << "\nmemo_image_ok=" << memo_image_ok_
            << "\nexport_smoke=" << export_smoke_ << "\nexport_ok=" << export_smoke_ok_
            << "\nexported_image=" << export_smoke_path_.string()
            << "\nstore_smoke=" << store_smoke_ << "\nstore_ok=" << store_smoke_ok_
            << "\nnavigation_smoke=" << navigation_smoke_ << "\nnavigation_ok=" << navigation_ok_
            << "\nnavigation_steps=" << navigation_step_ << "\nnavigator_nodes=" << nav_items_.size()
            << "\nnavigator_ok=" << navigator_ok << "\nnavigation_failed_at=" << navigation_failed_at_
            << "\npaths_smoke=" << paths_smoke_ << "\npaths_ok=" << paths_ok_ << "\npath_rows=" << paths_grid_->GetItemCount()
            << "\nloadview_smoke=" << loadview_smoke_ << "\nloadview_ok=" << loadview_ok_
            << "\nopenload_smoke=" << openload_smoke_ << "\nopenload_ok=" << openload_ok_
            << "\nm1_smoke=" << m1_smoke_ << "\nm1_ok=" << m1_ok_ << "\nm1_dialogs=" << m1_dialogs_ << "\nm1_error=" << m1_error_
            << "\nm3_smoke=" << m3_smoke_ << "\nm3_ok=" << m3_ok_ << "\nm3_steps=" << m3_step_ << "\nm3_error=" << m3_error_
            << "\ncatalog_flow=" << catalog_flow_smoke_ << "\ncatalog_flow_ok=" << catalog_flow_ok_ << "\ncatalog_flow_steps=" << catalog_flow_step_ << "\ncatalog_flow_error=" << catalog_flow_error_
            << "\ndefault_catalog=" << live_.default_catalog.string()
            << "\nvisible_area_rows=" << live_areas_->GetItemCount()
            << "\nimage_provenance=" << image_provenance_
            << "\ntable_rows=" << table_rows_->GetItemCount() << "\nfield_rows=" << table_fields_->GetItemCount()
            << "\nimage_smoke=" << image_smoke_ << "\nnested_smoke=" << nested_smoke_ << "\ninspected_image_nodes=" << image_tree_.nodes.size()
            << "\nhydrated_images=" << live_.images.size()
            << "\nsession_home=" << live_.home.string() << "\n";
        out.close();
        frame_->Close();
    }
};
std::weak_ptr<Workbench> active;
}
void uidef_register(uidef::Runtime& runtime) {
    runtime.host("workflow.browse", [] { if (auto p = active.lock()) p->workflow_browse(); });
    for (const std::string kind : {"tables", "indexes"})
        runtime.host("workflow." + kind, [kind] { if (auto p = active.lock()) p->workflow_browse(kind); });
    for (const std::string action : {"catalogs", "live", "images", "command", "exit", "help", "about"})
        runtime.host("view." + action, [action] { if (auto p = active.lock()) p->view_action(action); });
    runtime.host("catalog.choose", [] { if (auto p = active.lock()) p->choose(); });
    runtime.host("catalog.refresh", [] { if (auto p = active.lock()) p->refresh(); });
    for (const std::string action : {"hydrate", "load"})
        runtime.host("catalog." + action, [action] { if (auto p = active.lock()) p->catalog_action(action); });
    for (const std::string action : {"show", "edit", "reset", "init", "refresh", "catalog"})
        runtime.host("paths." + action, [action] { if (auto p = active.lock()) p->paths_action(action); });
    for (const std::string action : {"inspect", "hydrate", "child", "open", "export", "saved", "tables"})
        runtime.host("image." + action, [action] { if (auto p = active.lock()) p->image_action(action); });
    for (const std::string action : {"new", "child", "switch", "open", "close", "area", "refresh", "command", "save", "open_workspace", "load_workspace", "run_script"})
        runtime.host("session." + action, [action] { if (auto p = active.lock()) p->live_action(action); });
    for (const std::string action : {"top", "previous", "next", "refresh", "select", "value", "edit", "commit", "rollback", "image", "store_image",
        "first", "last", "back", "forward", "go", "filter", "order", "seek", "deleted", "append", "delete", "recall", "null"})
        runtime.host("table." + action, [action] { if (auto p = active.lock()) p->table_action(action); });
}
void uidef_after_init(wxWindow* window) {
    auto* frame = dynamic_cast<wxFrame*>(window);
    auto controller = std::make_shared<Workbench>(frame);
    active = controller;
    frame->Bind(wxEVT_DESTROY, [controller, frame](wxWindowDestroyEvent& e) {
        if (e.GetWindow() == frame) controller->shutdown();
        e.Skip();
    });
}
