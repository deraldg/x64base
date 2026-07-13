#pragma once

#include "gui/core/async_session.hpp"
#include "gui/core/localization.hpp"
#include "datadict/ddict_dbf_reader.hpp"

#include <wx/event.h>
#include <wx/frame.h>

#include <filesystem>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <vector>

class wxGrid;
class wxGridEvent;
class wxKeyEvent;
class wxChoice;
class wxListBox;
class wxNotebook;
class wxPanel;
class wxButton;
class wxStaticText;
class wxTextCtrl;

namespace dottalk::gui::wxui {

enum class WorkbenchPage {
    Tables,
    Indexes,
    Relations,
    DDict,
    Workspace,
    Browse,
    Structure
};

class DotTalkCoreEvent final : public wxCommandEvent {
public:
    DotTalkCoreEvent(wxEventType event_type, int winid, GuiEvent payload);
    DotTalkCoreEvent(const DotTalkCoreEvent&) = default;

    wxEvent* Clone() const override;
    const GuiEvent& payload() const noexcept;

private:
    GuiEvent payload_;
};

wxDECLARE_EVENT(wxEVT_DOTTALK_CORE, DotTalkCoreEvent);

class MainFrame final : public wxFrame {
public:
    explicit MainFrame(std::filesystem::path initial_table = {},
                       LocaleContext locale = {});
    ~MainFrame() override;

private:
    void BuildMenu();
    void BuildLayout();
    void OnOpen(wxCommandEvent& event);
    void OnRefresh(wxCommandEvent& event);
    void OnCloseArea(wxCommandEvent& event);
    void OnWorkspaceOpenDirectory(wxCommandEvent& event);
    void OnWorkspaceLoadRuntime(wxCommandEvent& event);
    void OnWorkspaceClose(wxCommandEvent& event);
    void OnOpenWorkspace(wxCommandEvent& event);
    void OnSaveWorkspace(wxCommandEvent& event);
    void OnSaveWorkspaceAs(wxCommandEvent& event);
    void OnOpenWorkspaceRoot(wxCommandEvent& event);
    void OnPathRoots(wxCommandEvent& event);
    void OnSetSkeleton(wxCommandEvent& event);
    void OnScan(wxCommandEvent& event);
    void OnCatalogCommand(wxCommandEvent& event);
    void OnRunCommand(wxCommandEvent& event);
    void OnCommandKeyDown(wxKeyEvent& event);
    void OnAreaSelected(wxCommandEvent& event);
    void OnBrowseCellSelected(wxGridEvent& event);
    void OnDDictRefresh(wxCommandEvent& event);
    void OnDDictFilterChanged(wxCommandEvent& event);
    void OnDDictObjectSelected(wxGridEvent& event);
    void OnDDictDetailSelected(wxGridEvent& event);
    void OnRecordViewKeyDown(wxKeyEvent& event);
    void OnLanguage(wxCommandEvent& event);
    void OnAbout(wxCommandEvent& event);
    void OnExit(wxCommandEvent& event);
    void OnCoreEvent(DotTalkCoreEvent& event);
    void OpenTable(std::filesystem::path path);
    void AddArea(const OpenTableResult& result);
    void RebuildAreas(const ListAreasResult& result);
    void ApplyWorkspaceModel(const WorkspaceModel& model);
    void ApplyTables(const WorkspaceModel& model);
    void ApplyIndexes(const WorkspaceModel& model);
    void ApplyRelations(const WorkspaceModel& model);
    void LoadDDictCatalog();
    void ApplyDDictObjects();
    void ApplyDDictSelection(const std::string& token);
    void ApplyDDictDetails(const dottalk::datadict::DDictRow* object);
    void ApplyDDictSource(const std::string& source_id);
    void SelectDDictObject(const std::string& token);
    void ApplySnapshot(const TableSnapshot& snapshot);
    void ApplyStructure(const TableSnapshot& snapshot);
    void ShowRecordView();
    void RefreshRecordView();
    bool NavigateActiveRecordTo(std::uint64_t record_number);
    bool NavigateActiveRecordBy(long long delta);
    void UpdateLocalizedText();
    void UpdateWorkspaceGraph();
    void AppendLog(const std::string& text);
    void AddCommandHistory(const std::string& text);
    bool RecallCommandHistory(int direction);
    void LoadWorkspaceFile(const std::filesystem::path& path);
    void SaveWorkspaceFile(const std::filesystem::path& path);
    void ShowTextWindow(const std::string& title, const std::string& body);
    void ShowErsatzResultsWindow(const std::string& output);
    int PageIndex(WorkbenchPage page) const;
    void SelectWorkbenchPage(WorkbenchPage page);
    void UpdateWorkbenchPageText();

    wxListBox* areas_ {nullptr};
    wxNotebook* notebook_ {nullptr};
    wxGrid* tables_grid_ {nullptr};
    wxGrid* indexes_grid_ {nullptr};
    wxGrid* relations_grid_ {nullptr};
    wxChoice* ddict_filter_ {nullptr};
    wxButton* ddict_refresh_button_ {nullptr};
    wxStaticText* ddict_status_ {nullptr};
    wxGrid* ddict_objects_grid_ {nullptr};
    wxNotebook* ddict_detail_notebook_ {nullptr};
    wxGrid* ddict_fields_grid_ {nullptr};
    wxGrid* ddict_tags_grid_ {nullptr};
    wxGrid* ddict_relations_grid_ {nullptr};
    wxGrid* ddict_evidence_grid_ {nullptr};
    wxGrid* ddict_source_grid_ {nullptr};
    wxTextCtrl* ddict_source_text_ {nullptr};
    wxGrid* grid_ {nullptr};
    wxGrid* structure_grid_ {nullptr};
    wxTextCtrl* workspace_graph_ {nullptr};
    wxTextCtrl* log_ {nullptr};
    wxFrame* record_view_frame_ {nullptr};
    wxPanel* record_view_panel_ {nullptr};
    wxTextCtrl* command_ {nullptr};
    wxButton* open_button_ {nullptr};
    wxButton* refresh_button_ {nullptr};
    wxButton* close_area_button_ {nullptr};
    wxButton* run_button_ {nullptr};
    wxStaticText* command_label_ {nullptr};
    wxStaticText* area_label_ {nullptr};
    std::filesystem::path current_table_;
    std::filesystem::path current_workspace_path_;
    AreaId current_area_id_ {0};
    LocaleContext locale_;
    std::vector<AreaId> area_ids_;
    std::vector<AreaInfo> area_infos_;
    WorkspaceModel workspace_model_;
    TableSnapshot current_snapshot_;
    std::filesystem::path ddict_catalog_dir_;
    std::vector<dottalk::datadict::DDictRow> ddict_objects_;
    std::vector<dottalk::datadict::DDictRow> ddict_attributes_;
    std::vector<dottalk::datadict::DDictRow> ddict_edges_;
    std::vector<dottalk::datadict::DDictRow> ddict_evidence_;
    std::vector<dottalk::datadict::DDictRow> ddict_sources_;
    std::vector<std::size_t> ddict_visible_object_rows_;
    std::string ddict_selected_objid_;
    std::map<int, std::size_t> catalog_menu_ids_;
    std::set<TaskId> scan_task_ids_;
    std::vector<std::string> command_history_;
    std::string command_history_draft_;
    int command_history_index_ {-1};
    bool applying_snapshot_ {false};
    std::unique_ptr<AsyncSession> session_;
};

} // namespace dottalk::gui::wxui
