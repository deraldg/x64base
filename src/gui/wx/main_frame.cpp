#include "main_frame.hpp"

#include "gui/core/gui_command_catalog.hpp"
#include "gui/core/gui_workspace_format.hpp"

#include <wx/checkbox.h>
#include <wx/choice.h>
#include <wx/dirdlg.h>
#include <wx/filedlg.h>
#include <wx/grid.h>
#include <wx/listbox.h>
#include <wx/menu.h>
#include <wx/msgdlg.h>
#include <wx/notebook.h>
#include <wx/panel.h>
#include <wx/sizer.h>
#include <wx/splitter.h>
#include <wx/stattext.h>
#include <wx/statusbr.h>
#include <wx/textctrl.h>
#include <wx/button.h>
#include <wx/dialog.h>
#include <wx/scrolwin.h>
#include <wx/utils.h>

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace dottalk::gui::wxui {

wxDEFINE_EVENT(wxEVT_DOTTALK_CORE, DotTalkCoreEvent);

namespace {

enum : int {
    IdRefresh = wxID_HIGHEST + 100,
    IdRunCommand,
    IdAreas,
    IdCloseArea,
    IdWorkspaceOpenDirectory,
    IdWorkspaceLoadRuntime,
    IdWorkspaceClose,
    IdOpenWorkspace,
    IdSaveWorkspace,
    IdSaveWorkspaceAs,
    IdOpenWorkspaceRoot,
    IdPathRoots,
    IdSetDbfSkeleton,
    IdSetIndexSkeleton,
    IdRunScan,
    IdLanguageEnUs,
    IdLanguageEs,
    IdLanguageFr,
    IdLanguageDe,
    IdLanguageIt,
    IdAbout,
    IdCatalogCommandBase = wxID_HIGHEST + 1000
};

struct LanguageMenuItem {
    int id;
    const char* locale;
    GuiTextId label;
};

constexpr LanguageMenuItem kLanguageMenuItems[] = {
    {IdLanguageEnUs, "en-US", GuiTextId::LocaleEnUs},
    {IdLanguageEs, "es", GuiTextId::LocaleEs},
    {IdLanguageFr, "fr", GuiTextId::LocaleFr},
    {IdLanguageDe, "de", GuiTextId::LocaleDe},
    {IdLanguageIt, "it", GuiTextId::LocaleIt},
};

std::string visible_area_id(AreaId id) {
    return id == 0 ? std::string("none") : std::to_string(id - 1);
}

std::string join_labels(const std::vector<std::string>& labels) {
    std::ostringstream out;
    for (std::size_t i = 0; i < labels.size(); ++i) {
        if (i != 0) {
            out << ", ";
        }
        out << labels[i];
    }
    return out.str();
}

std::string trim_ascii(std::string value) {
    auto is_space = [](unsigned char ch) { return std::isspace(ch) != 0; };
    value.erase(value.begin(), std::find_if(value.begin(), value.end(), [&](char ch) {
        return !is_space(static_cast<unsigned char>(ch));
    }));
    value.erase(std::find_if(value.rbegin(), value.rend(), [&](char ch) {
        return !is_space(static_cast<unsigned char>(ch));
    }).base(), value.end());
    return value;
}

std::string upper_ascii(std::string value) {
    for (auto& ch : value) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return value;
}

bool is_record_view_command(const std::string& command) {
    const std::string token = upper_ascii(trim_ascii(command));
    return token == "RECORDVIEW" || token == "RECORD VIEW";
}

int record_view_column_count(const std::vector<TableColumn>& columns) {
    bool has_long_field = false;
    for (const auto& column : columns) {
        if (column.type == 'M' || column.width > 40) {
            has_long_field = true;
            break;
        }
    }
    if (has_long_field) {
        return 1;
    }
    if (columns.size() >= 12) {
        return 3;
    }
    if (columns.size() >= 6) {
        return 2;
    }
    return 1;
}

wxSize record_view_size(const std::vector<TableColumn>& columns) {
    int total_width = 0;
    for (const auto& column : columns) {
        total_width += std::max(8, column.width);
    }
    if (total_width > 180 || columns.size() > 16) {
        return wxSize(980, 720);
    }
    if (total_width > 90 || columns.size() > 8) {
        return wxSize(820, 640);
    }
    return wxSize(640, 520);
}

std::string column_label(const TableColumn& column) {
    std::ostringstream out;
    out << column.name << " " << column.type << "(" << column.width << "," << column.decimals << ")";
    return out.str();
}

void configure_readonly_grid(wxGrid* grid, int label_size = 64) {
    if (!grid) {
        return;
    }
    grid->EnableEditing(false);
    grid->SetRowLabelSize(label_size);
}

void reset_grid(wxGrid* grid, int rows, int cols) {
    if (!grid) {
        return;
    }
    if (grid->GetNumberRows() > 0 && grid->GetNumberCols() > 0) {
        grid->ClearGrid();
    }
    if (grid->GetNumberCols() > 0) {
        grid->DeleteCols(0, grid->GetNumberCols());
    }
    if (grid->GetNumberRows() > 0) {
        grid->DeleteRows(0, grid->GetNumberRows());
    }
    if (cols > 0) {
        grid->AppendCols(cols);
    }
    if (rows > 0) {
        grid->AppendRows(rows);
    }
}

} // namespace

DotTalkCoreEvent::DotTalkCoreEvent(wxEventType event_type, int winid, GuiEvent payload)
    : wxCommandEvent(event_type, winid),
      payload_(std::move(payload)) {
}

wxEvent* DotTalkCoreEvent::Clone() const {
    return new DotTalkCoreEvent(*this);
}

const GuiEvent& DotTalkCoreEvent::payload() const noexcept {
    return payload_;
}

MainFrame::MainFrame(std::filesystem::path initial_table, LocaleContext locale)
    : wxFrame(nullptr, wxID_ANY, gui_text(GuiTextId::AppTitle, locale), wxDefaultPosition, wxSize(1100, 720)),
      locale_(std::move(locale)) {
    BuildMenu();
    BuildLayout();
    CreateStatusBar(3);
    SetStatusText(gui_text(GuiTextId::Ready, locale_), 0);
    SetStatusText(gui_text(GuiTextId::NoOpenAreas, locale_), 1);
    SetStatusText("0 rows", 2);

    session_ = std::make_unique<AsyncSession>([this](GuiEvent event) {
        wxQueueEvent(this, new DotTalkCoreEvent(wxEVT_DOTTALK_CORE, GetId(), std::move(event)));
    });

    Bind(wxEVT_MENU, &MainFrame::OnOpen, this, wxID_OPEN);
    Bind(wxEVT_MENU, &MainFrame::OnRefresh, this, IdRefresh);
    Bind(wxEVT_MENU, &MainFrame::OnCloseArea, this, IdCloseArea);
    Bind(wxEVT_MENU, &MainFrame::OnWorkspaceOpenDirectory, this, IdWorkspaceOpenDirectory);
    Bind(wxEVT_MENU, &MainFrame::OnWorkspaceLoadRuntime, this, IdWorkspaceLoadRuntime);
    Bind(wxEVT_MENU, &MainFrame::OnWorkspaceClose, this, IdWorkspaceClose);
    Bind(wxEVT_MENU, &MainFrame::OnOpenWorkspace, this, IdOpenWorkspace);
    Bind(wxEVT_MENU, &MainFrame::OnSaveWorkspace, this, IdSaveWorkspace);
    Bind(wxEVT_MENU, &MainFrame::OnSaveWorkspaceAs, this, IdSaveWorkspaceAs);
    Bind(wxEVT_MENU, &MainFrame::OnOpenWorkspaceRoot, this, IdOpenWorkspaceRoot);
    Bind(wxEVT_MENU, &MainFrame::OnPathRoots, this, IdPathRoots);
    Bind(wxEVT_MENU, &MainFrame::OnSetSkeleton, this, IdSetDbfSkeleton);
    Bind(wxEVT_MENU, &MainFrame::OnSetSkeleton, this, IdSetIndexSkeleton);
    Bind(wxEVT_MENU, &MainFrame::OnScan, this, IdRunScan);
    Bind(wxEVT_MENU, &MainFrame::OnAbout, this, IdAbout);
    Bind(wxEVT_MENU, &MainFrame::OnExit, this, wxID_EXIT);
    for (const auto& item : kLanguageMenuItems) {
        Bind(wxEVT_MENU, &MainFrame::OnLanguage, this, item.id);
    }
    Bind(wxEVT_BUTTON, &MainFrame::OnOpen, this, wxID_OPEN);
    Bind(wxEVT_BUTTON, &MainFrame::OnRefresh, this, IdRefresh);
    Bind(wxEVT_BUTTON, &MainFrame::OnCloseArea, this, IdCloseArea);
    Bind(wxEVT_BUTTON, &MainFrame::OnRunCommand, this, IdRunCommand);
    Bind(wxEVT_TEXT_ENTER, &MainFrame::OnRunCommand, this, IdRunCommand);
    Bind(wxEVT_LISTBOX, &MainFrame::OnAreaSelected, this, IdAreas);
    if (grid_) {
        grid_->Bind(wxEVT_GRID_SELECT_CELL, &MainFrame::OnBrowseCellSelected, this);
        grid_->Bind(wxEVT_CHAR_HOOK, &MainFrame::OnRecordViewKeyDown, this);
    }
    Bind(wxEVT_DOTTALK_CORE, &MainFrame::OnCoreEvent, this);

    if (!initial_table.empty()) {
        OpenTable(std::move(initial_table));
    } else {
        session_->submit_list_areas();
    }
    AppendLog("startup: init.ini, dottalkpp.ini, and dotscript.ini searched by GUI session.");
}

MainFrame::~MainFrame() {
    session_.reset();
}

void MainFrame::BuildMenu() {
    catalog_menu_ids_.clear();

    auto* file = new wxMenu();
    file->Append(wxID_OPEN, "&" + gui_text(GuiTextId::OpenTable, locale_) + "...\tCtrl+O");
    file->AppendSeparator();
    file->Append(wxID_EXIT, gui_text(GuiTextId::Exit, locale_) + "\tAlt+F4");

    auto* workspace = new wxMenu();
    workspace->Append(IdWorkspaceOpenDirectory, "WORKSPACE OPEN Directory...");
    workspace->Append(IdWorkspaceLoadRuntime, "WORKSPACE LOAD Schema...");
    workspace->Append(IdWorkspaceClose, "WORKSPACE CLOSE");
    workspace->AppendSeparator();
    workspace->Append(IdOpenWorkspace, "Load Bootstrap Workspace File...");
    workspace->Append(IdSaveWorkspace, gui_text(GuiTextId::SaveWorkspace, locale_));
    workspace->Append(IdSaveWorkspaceAs, gui_text(GuiTextId::SaveWorkspaceAs, locale_) + "...");
    workspace->AppendSeparator();
    workspace->Append(IdOpenWorkspaceRoot, "Open Workspace Root...");
    workspace->Append(IdPathRoots, "Path Roots...");
    workspace->AppendSeparator();
    workspace->Append(IdSetDbfSkeleton, "SET DBF...");
    workspace->Append(IdSetIndexSkeleton, "SET INDEX...");

    auto* area = new wxMenu();
    area->Append(IdRefresh, "&" + gui_text(GuiTextId::RefreshSnapshot, locale_) + "\tF5");
    area->Append(IdCloseArea, "&" + gui_text(GuiTextId::CloseArea, locale_) + "\tCtrl+W");

    auto* run = new wxMenu();
    run->Append(IdRunScan, "SCAN...ENDSCAN...");

    auto append_catalog_category = [this](wxMenuBar* menu_bar, const std::string& category, const std::string& title) {
        auto* menu = new wxMenu();
        int count = 0;
        const auto& catalog = gui_command_catalog();
        for (std::size_t index = 0; index < catalog.size(); ++index) {
            const auto& action = catalog[index];
            if (action.category != category) {
                continue;
            }
            const int id = IdCatalogCommandBase + static_cast<int>(catalog_menu_ids_.size());
            catalog_menu_ids_[id] = index;
            menu->Append(id, action.label);
            Bind(wxEVT_MENU, &MainFrame::OnCatalogCommand, this, id);
            ++count;
        }
        if (count > 0) {
            menu_bar->Append(menu, title);
        } else {
            delete menu;
        }
    };

    auto* language = new wxMenu();
    for (const auto& item : kLanguageMenuItems) {
        language->AppendRadioItem(item.id, gui_text(item.label, locale_));
        if (locale_.message_locale == item.locale) {
            language->Check(item.id, true);
        }
    }

    auto* help = new wxMenu();
    help->Append(IdAbout, gui_text(GuiTextId::About, locale_));

    auto* menu_bar = new wxMenuBar();
    menu_bar->Append(file, "&" + gui_text(GuiTextId::File, locale_));
    menu_bar->Append(workspace, gui_text(GuiTextId::Workspace, locale_));
    menu_bar->Append(area, "&" + gui_text(GuiTextId::Area, locale_));
    menu_bar->Append(run, "Run");
    append_catalog_category(menu_bar, "Table", "Table");
    append_catalog_category(menu_bar, "Record", "Record");
    append_catalog_category(menu_bar, "Index", "Index");
    append_catalog_category(menu_bar, "Lists", "Lists");
    append_catalog_category(menu_bar, "Browse", "Browse");
    append_catalog_category(menu_bar, "Rel", "Rel");
    append_catalog_category(menu_bar, "Tuple", "Tuple");
    append_catalog_category(menu_bar, "Cmd", "Cmd");
    menu_bar->Append(language, gui_text(GuiTextId::Language, locale_));
    menu_bar->Append(help, gui_text(GuiTextId::Help, locale_));
    SetMenuBar(menu_bar);
}

void MainFrame::BuildLayout() {
    auto* root = new wxPanel(this, wxID_ANY);
    auto* root_sizer = new wxBoxSizer(wxVERTICAL);

    auto* toolbar = new wxBoxSizer(wxHORIZONTAL);
    open_button_ = new wxButton(root, wxID_OPEN, gui_text(GuiTextId::OpenTable, locale_));
    refresh_button_ = new wxButton(root, IdRefresh, gui_text(GuiTextId::Refresh, locale_));
    close_area_button_ = new wxButton(root, IdCloseArea, gui_text(GuiTextId::CloseArea, locale_));
    command_label_ = new wxStaticText(root, wxID_ANY, gui_text(GuiTextId::Command, locale_));
    command_ = new wxTextCtrl(root, IdRunCommand, "", wxDefaultPosition, wxDefaultSize, wxTE_PROCESS_ENTER);
    run_button_ = new wxButton(root, IdRunCommand, gui_text(GuiTextId::Run, locale_));

    toolbar->Add(open_button_, 0, wxRIGHT, 6);
    toolbar->Add(refresh_button_, 0, wxRIGHT, 6);
    toolbar->Add(close_area_button_, 0, wxRIGHT, 12);
    toolbar->Add(command_label_, 0, wxALIGN_CENTER_VERTICAL | wxRIGHT, 6);
    toolbar->Add(command_, 1, wxRIGHT, 6);
    toolbar->Add(run_button_, 0);
    root_sizer->Add(toolbar, 0, wxEXPAND | wxALL, 8);

    auto* work_splitter = new wxSplitterWindow(root, wxID_ANY);
    auto* area_panel = new wxPanel(work_splitter, wxID_ANY);
    auto* area_sizer = new wxBoxSizer(wxVERTICAL);
    area_label_ = new wxStaticText(area_panel, wxID_ANY, gui_text(GuiTextId::Areas, locale_));
    areas_ = new wxListBox(area_panel, IdAreas);
    areas_->Append(gui_text(GuiTextId::NoOpenAreas, locale_));
    area_sizer->Add(area_label_, 0, wxEXPAND | wxLEFT | wxRIGHT | wxTOP, 8);
    area_sizer->Add(areas_, 1, wxEXPAND | wxALL, 8);
    area_panel->SetSizer(area_sizer);

    auto* splitter = new wxSplitterWindow(work_splitter, wxID_ANY);

    notebook_ = new wxNotebook(splitter, wxID_ANY);

    tables_grid_ = new wxGrid(notebook_, wxID_ANY);
    tables_grid_->CreateGrid(0, 0);
    configure_readonly_grid(tables_grid_);

    indexes_grid_ = new wxGrid(notebook_, wxID_ANY);
    indexes_grid_->CreateGrid(0, 0);
    configure_readonly_grid(indexes_grid_);

    relations_grid_ = new wxGrid(notebook_, wxID_ANY);
    relations_grid_->CreateGrid(0, 0);
    configure_readonly_grid(relations_grid_);

    grid_ = new wxGrid(notebook_, wxID_ANY);
    grid_->CreateGrid(0, 0);
    configure_readonly_grid(grid_, 72);

    structure_grid_ = new wxGrid(notebook_, wxID_ANY);
    structure_grid_->CreateGrid(0, 4);
    configure_readonly_grid(structure_grid_, 48);
    structure_grid_->SetColLabelValue(0, "Name");
    structure_grid_->SetColLabelValue(1, "Type");
    structure_grid_->SetColLabelValue(2, "Width");
    structure_grid_->SetColLabelValue(3, "Decimals");

    workspace_graph_ = new wxTextCtrl(notebook_, wxID_ANY, "", wxDefaultPosition, wxDefaultSize,
                                      wxTE_MULTILINE | wxTE_READONLY | wxTE_RICH2);
    notebook_->AddPage(tables_grid_, "Tables");
    notebook_->AddPage(indexes_grid_, "Indexes");
    notebook_->AddPage(relations_grid_, "Relations");
    notebook_->AddPage(workspace_graph_, gui_text(GuiTextId::WorkspaceGraph, locale_));
    notebook_->AddPage(grid_, gui_text(GuiTextId::Browse, locale_));
    notebook_->AddPage(structure_grid_, gui_text(GuiTextId::Structure, locale_));
    UpdateWorkspaceGraph();
    SelectWorkbenchPage(WorkbenchPage::Tables);

    log_ = new wxTextCtrl(splitter, wxID_ANY, "", wxDefaultPosition, wxDefaultSize,
                          wxTE_MULTILINE | wxTE_READONLY | wxTE_RICH2);

    splitter->SplitHorizontally(notebook_, log_, 500);
    splitter->SetMinimumPaneSize(120);

    work_splitter->SplitVertically(area_panel, splitter, 220);
    work_splitter->SetMinimumPaneSize(120);

    root_sizer->Add(work_splitter, 1, wxEXPAND | wxLEFT | wxRIGHT | wxBOTTOM, 8);
    root->SetSizer(root_sizer);

    auto* frame_sizer = new wxBoxSizer(wxVERTICAL);
    frame_sizer->Add(root, 1, wxEXPAND);
    SetSizer(frame_sizer);
    if (command_) {
        command_->SetFocus();
    }
}

void MainFrame::OnOpen(wxCommandEvent&) {
    wxFileDialog dialog(this, "Open DBF table", "", "", "DBF files (*.dbf)|*.dbf|All files (*.*)|*.*",
                        wxFD_OPEN | wxFD_FILE_MUST_EXIST);
    if (dialog.ShowModal() != wxID_OK) {
        return;
    }

    OpenTable(std::filesystem::path(dialog.GetPath().ToStdString()));
}

void MainFrame::OnRefresh(wxCommandEvent&) {
    if (current_area_id_ == 0) {
        StatusMessage message;
        message.severity = Severity::warning;
        message.code = gui_text_key(GuiTextId::NoTableOpen);
        message.text = gui_text(GuiTextId::NoTableOpen, locale_);
        AppendLog(render_status_line(message, locale_));
        SetStatusText(render_status_text(message, locale_), 0);
        return;
    }
    SetStatusText(gui_text(GuiTextId::RefreshingSnapshot, locale_), 0);
    session_->submit_table_snapshot(TableSnapshotRequest{current_area_id_, 0, 200});
}

void MainFrame::OnCloseArea(wxCommandEvent&) {
    if (current_area_id_ == 0) {
        StatusMessage message;
        message.severity = Severity::warning;
        message.code = gui_text_key(GuiTextId::NoAreaSelected);
        message.text = gui_text(GuiTextId::NoAreaSelected, locale_);
        AppendLog(render_status_line(message, locale_));
        SetStatusText(render_status_text(message, locale_), 0);
        return;
    }
    SetStatusText(gui_text(GuiTextId::ClosingArea, locale_), 0);
    session_->submit_close_area(CloseAreaRequest{current_area_id_});
}

void MainFrame::OnWorkspaceOpenDirectory(wxCommandEvent&) {
    wxDirDialog dialog(this,
                       "WORKSPACE OPEN <dir>",
                       "",
                       wxDD_DEFAULT_STYLE | wxDD_DIR_MUST_EXIST);
    if (dialog.ShowModal() != wxID_OK) {
        return;
    }

    const std::filesystem::path dir(dialog.GetPath().ToStdString());
    wxDialog options(this, wxID_ANY, "WORKSPACE OPEN Options", wxDefaultPosition, wxSize(420, 260));
    auto* sizer = new wxBoxSizer(wxVERTICAL);
    auto* index_label = new wxStaticText(&options, wxID_ANY, "Index/key attachment");
    auto* index_mode = new wxChoice(&options, wxID_ANY);
    index_mode->Append("No indexes");
    index_mode->Append("CDX indexes");
    index_mode->Append("CNX indexes");
    index_mode->Append("INX indexes");
    index_mode->SetSelection(0);
    auto* fallback = new wxCheckBox(&options, wxID_ANY, "FALLBACK if requested indexes are missing");
    auto* recursive = new wxCheckBox(&options, wxID_ANY, "recursive directory scan");
    auto* table_state = new wxCheckBox(&options, wxID_ANY, "TABLE state for opened areas");
    sizer->Add(index_label, 0, wxEXPAND | wxLEFT | wxRIGHT | wxTOP, 10);
    sizer->Add(index_mode, 0, wxEXPAND | wxLEFT | wxRIGHT | wxTOP, 10);
    sizer->Add(fallback, 0, wxEXPAND | wxLEFT | wxRIGHT | wxTOP, 10);
    sizer->Add(recursive, 0, wxEXPAND | wxLEFT | wxRIGHT | wxTOP, 10);
    sizer->Add(table_state, 0, wxEXPAND | wxLEFT | wxRIGHT | wxTOP, 10);
    sizer->Add(options.CreateSeparatedButtonSizer(wxOK | wxCANCEL), 0, wxEXPAND | wxALL, 10);
    options.SetSizer(sizer);
    if (options.ShowModal() != wxID_OK) {
        return;
    }

    std::string command = "workspace open " + dir.string();
    switch (index_mode->GetSelection()) {
    case 1:
        command += " CDX";
        break;
    case 2:
        command += " CNX";
        break;
    case 3:
        command += " INX";
        break;
    default:
        break;
    }
    if (fallback->GetValue()) {
        command += " FALLBACK";
    }
    if (recursive->GetValue()) {
        command += " recursive";
    }
    if (table_state->GetValue()) {
        command += " TABLE";
    }
    AppendLog("> " + command);
    session_->submit_command(CommandRequest{command});
}

void MainFrame::OnWorkspaceLoadRuntime(wxCommandEvent&) {
    wxFileDialog dialog(this,
                        "WORKSPACE LOAD name.dtschemas",
                        "",
                        "",
                        "DotTalk++ workspace schemas (*.dtschemas;*.dtschema)|*.dtschemas;*.dtschema|All files (*.*)|*.*",
                        wxFD_OPEN | wxFD_FILE_MUST_EXIST);
    if (dialog.ShowModal() != wxID_OK) {
        return;
    }

    const std::filesystem::path path(dialog.GetPath().ToStdString());
    const std::string command = "workspace load " + path.string();
    AppendLog("> " + command);
    session_->submit_command(CommandRequest{command});
}

void MainFrame::OnWorkspaceClose(wxCommandEvent&) {
    const std::string command = "workspace close";
    AppendLog("> " + command);
    SetStatusText(gui_text(GuiTextId::RunningCommand, locale_), 0);
    session_->submit_command(CommandRequest{command});
}

void MainFrame::OnOpenWorkspace(wxCommandEvent&) {
    wxFileDialog dialog(this,
                        "Load bootstrap workspace file",
                        "",
                        "",
                        "DotTalk++ schema (*.dtschema;*.dtschemas)|*.dtschema;*.dtschemas|All files (*.*)|*.*",
                        wxFD_OPEN | wxFD_FILE_MUST_EXIST);
    if (dialog.ShowModal() != wxID_OK) {
        return;
    }
    LoadWorkspaceFile(std::filesystem::path(dialog.GetPath().ToStdString()));
}

void MainFrame::OnSaveWorkspace(wxCommandEvent& event) {
    if (current_workspace_path_.empty()) {
        OnSaveWorkspaceAs(event);
        return;
    }
    SaveWorkspaceFile(current_workspace_path_);
}

void MainFrame::OnSaveWorkspaceAs(wxCommandEvent&) {
    wxFileDialog dialog(this,
                        "Save workspace",
                        "",
                        "workspace.dtschema",
                        "DotTalk++ schema (*.dtschema)|*.dtschema|All files (*.*)|*.*",
                        wxFD_SAVE | wxFD_OVERWRITE_PROMPT);
    if (dialog.ShowModal() != wxID_OK) {
        return;
    }
    SaveWorkspaceFile(std::filesystem::path(dialog.GetPath().ToStdString()));
}

void MainFrame::OnOpenWorkspaceRoot(wxCommandEvent&) {
    const auto root = std::filesystem::current_path() / "workspaces";
    if (!wxLaunchDefaultApplication(root.string())) {
        ShowTextWindow("Workspace Root", root.string());
    }
}

void MainFrame::OnPathRoots(wxCommandEvent&) {
    AppendLog("> paths");
    session_->submit_command(CommandRequest{"paths"});
}

void MainFrame::OnSetSkeleton(wxCommandEvent& event) {
    if (event.GetId() == IdSetDbfSkeleton) {
        AppendLog("> set dbf");
        session_->submit_command(CommandRequest{"set dbf"});
    } else {
        AppendLog("> set index");
        session_->submit_command(CommandRequest{"set index"});
    }
}

void MainFrame::OnScan(wxCommandEvent&) {
    wxDialog dialog(this, wxID_ANY, "SCAN...ENDSCAN", wxDefaultPosition, wxSize(680, 420));
    auto* sizer = new wxBoxSizer(wxVERTICAL);
    auto* editor = new wxTextCtrl(&dialog,
                                  wxID_ANY,
                                  "DO X64\nUSE STUDENTS\nSCAN\n  TUPLE\n  SKIP\nENDSCAN\n",
                                  wxDefaultPosition,
                                  wxDefaultSize,
                                  wxTE_MULTILINE | wxTE_RICH2);
    sizer->Add(editor, 1, wxEXPAND | wxALL, 8);
    sizer->Add(dialog.CreateSeparatedButtonSizer(wxOK | wxCANCEL), 0, wxEXPAND | wxLEFT | wxRIGHT | wxBOTTOM, 8);
    dialog.SetSizer(sizer);
    if (dialog.ShowModal() != wxID_OK) {
        return;
    }
    const std::string scan_text = editor->GetValue().ToStdString();
    AppendLog("> SCAN...ENDSCAN");
    const TaskId task = session_->submit_command(CommandRequest{scan_text});
    if (task != 0) {
        scan_task_ids_.insert(task);
    }
}

void MainFrame::OnCatalogCommand(wxCommandEvent& event) {
    const auto found = catalog_menu_ids_.find(event.GetId());
    if (found == catalog_menu_ids_.end()) {
        return;
    }

    const auto& catalog = gui_command_catalog();
    if (found->second >= catalog.size()) {
        return;
    }

    const auto& action = catalog[found->second];
    if (action.kind == GuiCommandActionKind::info) {
        wxMessageBox(action.note.empty() ? action.label : action.note,
                     action.label,
                     wxOK | wxICON_INFORMATION,
                     this);
        return;
    }

    if (action.kind == GuiCommandActionKind::prefill) {
        if (command_) {
            command_->SetValue(action.command);
            command_->SetInsertionPointEnd();
            command_->SetFocus();
        }
        SetStatusText("Ready: " + action.command, 0);
        return;
    }

    if (is_record_view_command(action.command)) {
        ShowRecordView();
        return;
    }

    AppendLog("> " + action.command);
    SetStatusText(gui_text(GuiTextId::RunningCommand, locale_), 0);
    session_->submit_command(CommandRequest{action.command});
}

void MainFrame::OnRunCommand(wxCommandEvent&) {
    if (!command_) {
        return;
    }
    const std::string text = command_->GetValue().ToStdString();
    if (text.empty()) {
        return;
    }
    if (is_record_view_command(text)) {
        command_->Clear();
        ShowRecordView();
        return;
    }
    AppendLog("> " + text);
    SetStatusText(gui_text(GuiTextId::RunningCommand, locale_), 0);
    command_->Clear();
    session_->submit_command(CommandRequest{text});
}

void MainFrame::OnAreaSelected(wxCommandEvent& event) {
    const int selection = event.GetSelection();
    if (selection < 0 || static_cast<std::size_t>(selection) >= area_ids_.size()) {
        return;
    }

    const AreaId area_id = area_ids_[static_cast<std::size_t>(selection)];
    current_area_id_ = area_id;
    SetStatusText(gui_text(GuiTextId::SelectingArea, locale_), 0);
    session_->submit_select_area(SelectAreaRequest{area_id});
}

void MainFrame::OnBrowseCellSelected(wxGridEvent& event) {
    if (applying_snapshot_ || current_area_id_ == 0 || !session_) {
        event.Skip();
        return;
    }

    const int row = event.GetRow();
    if (row < 0 || row >= grid_->GetNumberRows()) {
        event.Skip();
        return;
    }

    const std::string label = grid_->GetRowLabelValue(row).ToStdString();
    try {
        std::size_t used = 0;
        const auto recno = std::stoull(label, &used, 10);
        if (used == 0 || recno == 0) {
            event.Skip();
            return;
        }
        session_->submit_move_cursor(MoveCursorRequest{current_area_id_, recno});
    } catch (...) {
    }
    event.Skip();
}

void MainFrame::OnLanguage(wxCommandEvent& event) {
    for (const auto& item : kLanguageMenuItems) {
        if (event.GetId() == item.id) {
            locale_ = locale_context_from_message_locale(item.locale);
            UpdateLocalizedText();
            return;
        }
    }
}

void MainFrame::OnAbout(wxCommandEvent&) {
    wxMessageBox(gui_text(GuiTextId::AboutBody, locale_),
                 gui_text(GuiTextId::AboutTitle, locale_),
                 wxOK | wxICON_INFORMATION,
                 this);
}

void MainFrame::OnExit(wxCommandEvent&) {
    Close(true);
}

void MainFrame::OpenTable(std::filesystem::path path) {
    if (path.empty()) {
        return;
    }
    current_table_ = path;
    SetStatusText(gui_text(GuiTextId::OpeningTable, locale_), 0);
    AppendLog("open " + path.string());
    session_->submit_open_table(OpenTableRequest{std::move(path)});
}

void MainFrame::AddArea(const OpenTableResult& result) {
    if (!areas_ || result.area_id == 0) {
        return;
    }

    const auto existing = std::find(area_ids_.begin(), area_ids_.end(), result.area_id);
    if (existing != area_ids_.end()) {
        const auto index = static_cast<int>(std::distance(area_ids_.begin(), existing));
        areas_->SetSelection(index);
        current_area_id_ = result.area_id;
        for (auto& area : area_infos_) {
            area.active = area.area_id == result.area_id;
        }
        UpdateWorkspaceGraph();
        return;
    }

    if (area_ids_.empty() && areas_->GetCount() == 1 &&
        areas_->GetString(0) == gui_text(GuiTextId::NoOpenAreas, locale_)) {
        areas_->Clear();
    }

    area_ids_.push_back(result.area_id);
    area_infos_.push_back(AreaInfo{result.area_id, true, result.path, result.display_name, result.record_count});
    workspace_model_.active_area_id = result.area_id;
    workspace_model_.tables = area_infos_;
    std::ostringstream label;
    label << visible_area_id(result.area_id) << "  " << result.display_name << "  (" << result.record_count << ")";
    areas_->Append(label.str());
    areas_->SetSelection(static_cast<int>(area_ids_.size() - 1));
    current_area_id_ = result.area_id;
    ApplyTables(workspace_model_);
    UpdateWorkspaceGraph();
}

void MainFrame::RebuildAreas(const ListAreasResult& result) {
    area_ids_.clear();
    area_infos_.clear();
    current_area_id_ = result.active_area_id;
    workspace_model_.active_area_id = result.active_area_id;
    workspace_model_.tables = result.areas;

    if (!areas_) {
        return;
    }

    areas_->Clear();
    if (result.areas.empty()) {
        areas_->Append(gui_text(GuiTextId::NoOpenAreas, locale_));
        ApplyTables(workspace_model_);
        UpdateWorkspaceGraph();
        return;
    }

    int active_selection = wxNOT_FOUND;
    for (const auto& area : result.areas) {
        area_ids_.push_back(area.area_id);
        area_infos_.push_back(area);
        std::ostringstream label;
        label << visible_area_id(area.area_id) << "  " << area.display_name << "  (" << area.record_count << ")";
        areas_->Append(label.str());
        if (area.active) {
            active_selection = static_cast<int>(area_ids_.size() - 1);
        }
    }

    if (active_selection != wxNOT_FOUND) {
        areas_->SetSelection(active_selection);
    }
    ApplyTables(workspace_model_);
    UpdateWorkspaceGraph();
}

void MainFrame::ApplyWorkspaceModel(const WorkspaceModel& model) {
    workspace_model_ = model;
    area_infos_ = model.tables;
    current_area_id_ = model.active_area_id;
    ApplyTables(model);
    ApplyIndexes(model);
    ApplyRelations(model);
    UpdateWorkspaceGraph();
}

void MainFrame::ApplyTables(const WorkspaceModel& model) {
    if (!tables_grid_) {
        return;
    }

    reset_grid(tables_grid_, static_cast<int>(model.tables.size()), 6);
    tables_grid_->SetColLabelValue(0, "Area");
    tables_grid_->SetColLabelValue(1, "Table");
    tables_grid_->SetColLabelValue(2, "Records");
    tables_grid_->SetColLabelValue(3, "Fields");
    tables_grid_->SetColLabelValue(4, "Active");
    tables_grid_->SetColLabelValue(5, "Path");

    for (std::size_t row = 0; row < model.tables.size(); ++row) {
        const auto& area = model.tables[row];
        const int grid_row = static_cast<int>(row);
        tables_grid_->SetRowLabelValue(grid_row, std::to_string(row + 1));
        tables_grid_->SetCellValue(grid_row, 0, visible_area_id(area.area_id));
        tables_grid_->SetCellValue(grid_row, 1, area.display_name);
        tables_grid_->SetCellValue(grid_row, 2, std::to_string(area.record_count));
        tables_grid_->SetCellValue(grid_row, 3, std::to_string(area.field_count));
        tables_grid_->SetCellValue(grid_row, 4, area.active ? "yes" : "");
        tables_grid_->SetCellValue(grid_row, 5, area.path.string());
    }
    tables_grid_->AutoSizeColumns(false);
}

void MainFrame::ApplyIndexes(const WorkspaceModel& model) {
    if (!indexes_grid_) {
        return;
    }

    reset_grid(indexes_grid_, static_cast<int>(model.indexes.size()), 9);
    indexes_grid_->SetColLabelValue(0, "Area");
    indexes_grid_->SetColLabelValue(1, "Table");
    indexes_grid_->SetColLabelValue(2, "Kind");
    indexes_grid_->SetColLabelValue(3, "Active");
    indexes_grid_->SetColLabelValue(4, "Direction");
    indexes_grid_->SetColLabelValue(5, "Active Tag");
    indexes_grid_->SetColLabelValue(6, "Tags");
    indexes_grid_->SetColLabelValue(7, "Backend");
    indexes_grid_->SetColLabelValue(8, "Container");

    for (std::size_t row = 0; row < model.indexes.size(); ++row) {
        const auto& index = model.indexes[row];
        const int grid_row = static_cast<int>(row);
        indexes_grid_->SetRowLabelValue(grid_row, std::to_string(row + 1));
        indexes_grid_->SetCellValue(grid_row, 0, visible_area_id(index.area_id));
        indexes_grid_->SetCellValue(grid_row, 1, index.area_name);
        indexes_grid_->SetCellValue(grid_row, 2, index.kind);
        indexes_grid_->SetCellValue(grid_row, 3, index.active ? "yes" : "");
        indexes_grid_->SetCellValue(grid_row, 4, index.ascending ? "ASC" : "DESC");
        indexes_grid_->SetCellValue(grid_row, 5, index.tag);
        indexes_grid_->SetCellValue(grid_row, 6, join_labels(index.tags));
        indexes_grid_->SetCellValue(grid_row, 7, index.backend);
        indexes_grid_->SetCellValue(grid_row, 8, index.container.string());
    }
    indexes_grid_->AutoSizeColumns(false);
}

void MainFrame::ApplyRelations(const WorkspaceModel& model) {
    if (!relations_grid_) {
        return;
    }

    reset_grid(relations_grid_, static_cast<int>(model.relations.size()), 6);
    relations_grid_->SetColLabelValue(0, "Parent");
    relations_grid_->SetColLabelValue(1, "Child");
    relations_grid_->SetColLabelValue(2, "Parent Key");
    relations_grid_->SetColLabelValue(3, "Child Key");
    relations_grid_->SetColLabelValue(4, "Matches");
    relations_grid_->SetColLabelValue(5, "Source");

    for (std::size_t row = 0; row < model.relations.size(); ++row) {
        const auto& relation = model.relations[row];
        const int grid_row = static_cast<int>(row);
        relations_grid_->SetRowLabelValue(grid_row, std::to_string(row + 1));
        relations_grid_->SetCellValue(grid_row, 0, relation.parent);
        relations_grid_->SetCellValue(grid_row, 1, relation.child);
        relations_grid_->SetCellValue(grid_row, 2, relation.parent_key);
        relations_grid_->SetCellValue(grid_row, 3, relation.child_key);
        relations_grid_->SetCellValue(grid_row, 4, std::to_string(relation.match_count));
        relations_grid_->SetCellValue(grid_row, 5, relation.source);
    }
    relations_grid_->AutoSizeColumns(false);
}

void MainFrame::OnCoreEvent(DotTalkCoreEvent& event) {
    const auto& payload = event.payload();
    if (!payload.label.empty()) {
        SetStatusText(render_label(payload.label_code, payload.label, locale_), 0);
    }

    for (const auto& message : payload.messages) {
        AppendLog(render_status_line(message, locale_));
    }

    switch (payload.kind) {
    case GuiEventKind::open_table_finished:
        if (payload.open_table && payload.open_table->ok) {
            AddArea(*payload.open_table);
            SetStatusText(payload.open_table->display_name, 1);
            session_->submit_table_snapshot(TableSnapshotRequest{payload.open_table->area_id, 0, 200});
            session_->submit_list_areas();
        }
        break;
    case GuiEventKind::area_selected:
        if (payload.select_area && payload.select_area->ok) {
            SetStatusText(payload.select_area->display_name, 1);
            session_->submit_table_snapshot(TableSnapshotRequest{payload.select_area->area_id, 0, 200});
        }
        break;
    case GuiEventKind::area_closed:
        if (payload.close_area && payload.close_area->ok) {
            current_area_id_ = payload.close_area->active_area_id;
            session_->submit_list_areas();
            if (current_area_id_ != 0) {
                session_->submit_table_snapshot(TableSnapshotRequest{current_area_id_, 0, 200});
            } else {
                ApplySnapshot(TableSnapshot{});
                SetStatusText(gui_text(GuiTextId::NoOpenAreas, locale_), 1);
            }
        }
        break;
    case GuiEventKind::areas_listed:
        if (payload.list_areas) {
            RebuildAreas(*payload.list_areas);
        }
        break;
    case GuiEventKind::workspace_model_ready:
        if (payload.workspace_model) {
            ApplyWorkspaceModel(*payload.workspace_model);
        }
        break;
    case GuiEventKind::table_snapshot_ready:
        if (payload.table_snapshot) {
            ApplySnapshot(*payload.table_snapshot);
        }
        break;
    case GuiEventKind::command_finished:
        if (payload.command && !payload.command->output.empty()) {
            AppendLog(payload.command->output);
            if (scan_task_ids_.erase(payload.task_id) > 0) {
                ShowTextWindow("SCAN Results", payload.command->output);
            }
        }
        break;
    case GuiEventKind::task_progress:
    case GuiEventKind::log_line:
        break;
    }
}

void MainFrame::ApplySnapshot(const TableSnapshot& snapshot) {
    applying_snapshot_ = true;
    current_snapshot_ = snapshot;
    if (grid_->GetNumberRows() > 0 && grid_->GetNumberCols() > 0) {
        grid_->ClearGrid();
    }

    if (grid_->GetNumberCols() > 0) {
        grid_->DeleteCols(0, grid_->GetNumberCols());
    }
    if (grid_->GetNumberRows() > 0) {
        grid_->DeleteRows(0, grid_->GetNumberRows());
    }

    if (!snapshot.columns.empty()) {
        grid_->AppendCols(static_cast<int>(snapshot.columns.size()));
        for (std::size_t col = 0; col < snapshot.columns.size(); ++col) {
            const auto& column = snapshot.columns[col];
            std::ostringstream label;
            label << column.name << " " << column.type << "(" << column.width << ")";
            grid_->SetColLabelValue(static_cast<int>(col), label.str());
        }
    }

    if (!snapshot.rows.empty()) {
        grid_->AppendRows(static_cast<int>(snapshot.rows.size()));
        int current_row = wxNOT_FOUND;
        for (std::size_t row = 0; row < snapshot.rows.size(); ++row) {
            const auto& source = snapshot.rows[row];
            grid_->SetRowLabelValue(static_cast<int>(row), std::to_string(source.record_number));
            if (source.record_number == snapshot.current_record_number) {
                current_row = static_cast<int>(row);
            }
            for (std::size_t col = 0; col < source.values.size() && col < snapshot.columns.size(); ++col) {
                grid_->SetCellValue(static_cast<int>(row), static_cast<int>(col), source.values[col]);
            }
        }
        if (current_row != wxNOT_FOUND && grid_->GetNumberCols() > 0) {
            grid_->SetGridCursor(current_row, 0);
            grid_->SelectRow(current_row);
            grid_->MakeCellVisible(current_row, 0);
        }
    }

    grid_->AutoSizeColumns(false);
    ApplyStructure(snapshot);

    const std::string area_name = snapshot.display_name.empty()
        ? gui_text(GuiTextId::NoOpenAreas, locale_)
        : snapshot.display_name;
    SetStatusText(area_name, 1);
    SetStatusText(std::to_string(snapshot.rows.size()) + " " +
                      gui_text(GuiTextId::RowsShownOf, locale_) + " " +
                      std::to_string(snapshot.total_records),
                  2);
    SetTitle(snapshot.display_name.empty()
                 ? gui_text(GuiTextId::AppTitle, locale_)
                 : gui_text(GuiTextId::AppTitle, locale_) + " - " + snapshot.display_name);
    UpdateWorkspaceGraph();
    applying_snapshot_ = false;
    RefreshRecordView();
}

void MainFrame::ApplyStructure(const TableSnapshot& snapshot) {
    if (!structure_grid_) {
        return;
    }

    reset_grid(structure_grid_, 0, 4);
    structure_grid_->SetColLabelValue(0, "Name");
    structure_grid_->SetColLabelValue(1, "Type");
    structure_grid_->SetColLabelValue(2, "Width");
    structure_grid_->SetColLabelValue(3, "Decimals");

    if (snapshot.columns.empty()) {
        structure_grid_->AutoSizeColumns(false);
        return;
    }

    structure_grid_->AppendRows(static_cast<int>(snapshot.columns.size()));
    for (std::size_t row = 0; row < snapshot.columns.size(); ++row) {
        const auto& column = snapshot.columns[row];
        const int grid_row = static_cast<int>(row);
        structure_grid_->SetRowLabelValue(grid_row, std::to_string(row + 1));
        structure_grid_->SetCellValue(grid_row, 0, column.name);
        structure_grid_->SetCellValue(grid_row, 1, std::string(1, column.type));
        structure_grid_->SetCellValue(grid_row, 2, std::to_string(column.width));
        structure_grid_->SetCellValue(grid_row, 3, std::to_string(column.decimals));
    }

    structure_grid_->AutoSizeColumns(false);
}

void MainFrame::ShowRecordView() {
    if (current_area_id_ == 0) {
        StatusMessage message;
        message.severity = Severity::warning;
        message.code = gui_text_key(GuiTextId::NoAreaSelected);
        message.text = gui_text(GuiTextId::NoAreaSelected, locale_);
        AppendLog(render_status_line(message, locale_));
        SetStatusText(render_status_text(message, locale_), 0);
        return;
    }

    if (!record_view_frame_) {
        record_view_frame_ = new wxFrame(this,
                                         wxID_ANY,
                                         "Record View",
                                         wxDefaultPosition,
                                         record_view_size(current_snapshot_.columns));
        record_view_panel_ = new wxPanel(record_view_frame_, wxID_ANY);
        record_view_frame_->Bind(wxEVT_CHAR_HOOK, &MainFrame::OnRecordViewKeyDown, this);
        record_view_panel_->Bind(wxEVT_CHAR_HOOK, &MainFrame::OnRecordViewKeyDown, this);
        record_view_frame_->Bind(wxEVT_DESTROY, [this](wxWindowDestroyEvent& event) {
            if (event.GetEventObject() == record_view_frame_) {
                record_view_frame_ = nullptr;
                record_view_panel_ = nullptr;
            }
            event.Skip();
        });
        record_view_frame_->Show();
    }

    RefreshRecordView();
    if (record_view_frame_) {
        record_view_frame_->Raise();
        record_view_frame_->SetFocus();
    }
}

void MainFrame::RefreshRecordView() {
    if (!record_view_frame_ || !record_view_panel_) {
        return;
    }

    if (current_area_id_ == 0 || current_snapshot_.area_id != current_area_id_ ||
        current_snapshot_.columns.empty()) {
        record_view_frame_->SetTitle("Record View");
        if (record_view_panel_->GetSizer()) {
            record_view_panel_->SetSizer(nullptr, true);
        }
        record_view_panel_->DestroyChildren();
        auto* root = new wxBoxSizer(wxVERTICAL);
        root->Add(new wxStaticText(record_view_panel_,
                                   wxID_ANY,
                                   "No active table snapshot. Select an area or refresh the workspace."),
                  0,
                  wxALL,
                  10);
        record_view_panel_->SetSizer(root);
        record_view_panel_->Layout();
        return;
    }

    std::uint64_t recno = current_snapshot_.current_record_number;
    if (recno == 0) {
        recno = 1;
    }

    const TableRow* selected_row = nullptr;
    for (const auto& row : current_snapshot_.rows) {
        if (row.record_number == recno) {
            selected_row = &row;
            break;
        }
    }

    if (!selected_row) {
        session_->submit_table_snapshot(TableSnapshotRequest{current_area_id_, recno, 200});
        return;
    }

    record_view_frame_->SetTitle("Record View - " + current_snapshot_.display_name + " #" +
                                 std::to_string(recno));
    record_view_frame_->SetMinSize(record_view_size(current_snapshot_.columns));
    if (record_view_panel_->GetSizer()) {
        record_view_panel_->SetSizer(nullptr, true);
    }
    record_view_panel_->DestroyChildren();
    record_view_panel_->Bind(wxEVT_CHAR_HOOK, &MainFrame::OnRecordViewKeyDown, this);

    auto* root = new wxBoxSizer(wxVERTICAL);

    auto* header = new wxBoxSizer(wxHORIZONTAL);
    header->Add(new wxStaticText(record_view_panel_, wxID_ANY, current_snapshot_.display_name),
                1,
                wxALIGN_CENTER_VERTICAL | wxRIGHT,
                8);
    std::ostringstream rec_label;
    rec_label << "Record " << recno << " of " << current_snapshot_.total_records;
    if (selected_row->deleted) {
        rec_label << " (deleted)";
    }
    header->Add(new wxStaticText(record_view_panel_, wxID_ANY, rec_label.str()), 0, wxALIGN_CENTER_VERTICAL);
    root->Add(header, 0, wxEXPAND | wxALL, 10);

    auto* scroll = new wxScrolledWindow(record_view_panel_, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxVSCROLL);
    scroll->Bind(wxEVT_CHAR_HOOK, &MainFrame::OnRecordViewKeyDown, this);
    scroll->SetScrollRate(8, 8);
    const int columns = record_view_column_count(current_snapshot_.columns);
    auto* fields = new wxFlexGridSizer(0, columns, 8, 8);
    for (int col = 0; col < columns; ++col) {
        fields->AddGrowableCol(col, 1);
    }

    for (std::size_t index = 0; index < current_snapshot_.columns.size(); ++index) {
        const auto& column = current_snapshot_.columns[index];
        const std::string value = index < selected_row->values.size() ? selected_row->values[index] : std::string{};
        auto* box = new wxStaticBoxSizer(wxVERTICAL, scroll, column_label(column));

        const bool multiline = column.type == 'M' || column.width > 60 || value.size() > 80;
        const long style = wxTE_READONLY | (multiline ? wxTE_MULTILINE : 0);
        const int height = multiline ? std::min(140, std::max(70, static_cast<int>(value.size() / 2 + 50))) : -1;
        auto* field = new wxTextCtrl(scroll,
                                     wxID_ANY,
                                     value,
                                     wxDefaultPosition,
                                     wxSize(-1, height),
                                     style);
        field->Bind(wxEVT_CHAR_HOOK, &MainFrame::OnRecordViewKeyDown, this);
        box->Add(field, 1, wxEXPAND | wxALL, 4);
        fields->Add(box, 1, wxEXPAND);
    }

    scroll->SetSizer(fields);
    root->Add(scroll, 1, wxEXPAND | wxLEFT | wxRIGHT, 10);

    auto* footer = new wxBoxSizer(wxHORIZONTAL);
    footer->Add(new wxStaticText(record_view_panel_,
                                 wxID_ANY,
                                 "Home/End/Page/Arrow keys move the active database record."),
                1,
                wxALIGN_CENTER_VERTICAL | wxRIGHT,
                8);
    auto* close = new wxButton(record_view_panel_, wxID_CLOSE, "Close");
    close->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
        if (record_view_frame_) {
            record_view_frame_->Close();
        }
    });
    footer->Add(close, 0);
    root->Add(footer, 0, wxEXPAND | wxALL, 10);

    record_view_panel_->SetSizer(root);
    record_view_panel_->Layout();
    record_view_frame_->Layout();
}

bool MainFrame::NavigateActiveRecordTo(std::uint64_t record_number) {
    if (current_area_id_ == 0 || !session_ || current_snapshot_.total_records == 0) {
        return false;
    }
    record_number = std::max<std::uint64_t>(1, record_number);
    record_number = std::min<std::uint64_t>(record_number, current_snapshot_.total_records);
    session_->submit_move_cursor(MoveCursorRequest{current_area_id_, record_number});
    return true;
}

bool MainFrame::NavigateActiveRecordBy(long long delta) {
    if (current_area_id_ == 0 || current_snapshot_.total_records == 0) {
        return false;
    }
    const auto current = current_snapshot_.current_record_number == 0
        ? std::uint64_t{1}
        : current_snapshot_.current_record_number;
    long long target = static_cast<long long>(current) + delta;
    if (target < 1) {
        target = 1;
    }
    const auto max_record = static_cast<long long>(current_snapshot_.total_records);
    if (target > max_record) {
        target = max_record;
    }
    return NavigateActiveRecordTo(static_cast<std::uint64_t>(target));
}

void MainFrame::OnRecordViewKeyDown(wxKeyEvent& event) {
    const long page_delta = std::max<long>(10, grid_ ? grid_->GetNumberRows() / 4 : 10);
    bool handled = false;
    switch (event.GetKeyCode()) {
    case WXK_UP:
    case WXK_LEFT:
        handled = NavigateActiveRecordBy(-1);
        break;
    case WXK_DOWN:
    case WXK_RIGHT:
        handled = NavigateActiveRecordBy(1);
        break;
    case WXK_PAGEUP:
        handled = NavigateActiveRecordBy(-page_delta);
        break;
    case WXK_PAGEDOWN:
        handled = NavigateActiveRecordBy(page_delta);
        break;
    case WXK_HOME:
        handled = NavigateActiveRecordTo(1);
        break;
    case WXK_END:
        handled = NavigateActiveRecordTo(current_snapshot_.total_records);
        break;
    default:
        break;
    }

    if (!handled) {
        event.Skip();
    }
}

void MainFrame::UpdateLocalizedText() {
    BuildMenu();
    if (open_button_) {
        open_button_->SetLabel(gui_text(GuiTextId::OpenTable, locale_));
    }
    if (refresh_button_) {
        refresh_button_->SetLabel(gui_text(GuiTextId::Refresh, locale_));
    }
    if (close_area_button_) {
        close_area_button_->SetLabel(gui_text(GuiTextId::CloseArea, locale_));
    }
    if (command_label_) {
        command_label_->SetLabel(gui_text(GuiTextId::Command, locale_));
    }
    if (run_button_) {
        run_button_->SetLabel(gui_text(GuiTextId::Run, locale_));
    }
    if (area_label_) {
        area_label_->SetLabel(gui_text(GuiTextId::Areas, locale_));
    }
    UpdateWorkbenchPageText();
    if (areas_ && area_ids_.empty() && areas_->GetCount() == 1) {
        areas_->SetString(0, gui_text(GuiTextId::NoOpenAreas, locale_));
    }
    if (current_area_id_ == 0) {
        SetStatusText(gui_text(GuiTextId::Ready, locale_), 0);
        SetStatusText(gui_text(GuiTextId::NoOpenAreas, locale_), 1);
        SetTitle(gui_text(GuiTextId::AppTitle, locale_));
    } else {
        SetTitle(gui_text(GuiTextId::AppTitle, locale_));
    }
    Layout();
    UpdateWorkspaceGraph();
}

int MainFrame::PageIndex(WorkbenchPage page) const {
    switch (page) {
    case WorkbenchPage::Tables:
        return 0;
    case WorkbenchPage::Indexes:
        return 1;
    case WorkbenchPage::Relations:
        return 2;
    case WorkbenchPage::Workspace:
        return 3;
    case WorkbenchPage::Browse:
        return 4;
    case WorkbenchPage::Structure:
        return 5;
    }
    return 0;
}

void MainFrame::SelectWorkbenchPage(WorkbenchPage page) {
    if (notebook_) {
        notebook_->SetSelection(PageIndex(page));
    }
}

void MainFrame::UpdateWorkbenchPageText() {
    if (!notebook_) {
        return;
    }
    notebook_->SetPageText(PageIndex(WorkbenchPage::Tables), "Tables");
    notebook_->SetPageText(PageIndex(WorkbenchPage::Indexes), "Indexes");
    notebook_->SetPageText(PageIndex(WorkbenchPage::Relations), "Relations");
    notebook_->SetPageText(PageIndex(WorkbenchPage::Workspace), gui_text(GuiTextId::WorkspaceGraph, locale_));
    notebook_->SetPageText(PageIndex(WorkbenchPage::Browse), gui_text(GuiTextId::Browse, locale_));
    notebook_->SetPageText(PageIndex(WorkbenchPage::Structure), gui_text(GuiTextId::Structure, locale_));
}

void MainFrame::UpdateWorkspaceGraph() {
    if (!workspace_graph_) {
        return;
    }

    workspace_model_.active_area_id = current_area_id_;
    if (workspace_model_.tables.empty() || workspace_model_.tables.size() != area_infos_.size()) {
        workspace_model_.tables = area_infos_;
    }
    workspace_graph_->SetValue(format_workspace_graph_text(workspace_model_,
                                                           gui_text(GuiTextId::WorkspaceGraph, locale_),
                                                           gui_text(GuiTextId::NoOpenAreas, locale_)));
}

void MainFrame::LoadWorkspaceFile(const std::filesystem::path& path) {
    std::ifstream in(path);
    if (!in.is_open()) {
        wxMessageBox("Unable to open workspace file: " + path.string(), "Workspace", wxOK | wxICON_ERROR, this);
        return;
    }

    current_workspace_path_ = path;
    std::vector<std::filesystem::path> tables;
    std::string line;
    while (std::getline(in, line)) {
        if (line.rfind("table=", 0) == 0) {
            tables.emplace_back(line.substr(6));
        }
    }

    for (const auto area_id : area_ids_) {
        session_->submit_close_area(CloseAreaRequest{area_id});
    }
    for (const auto& table : tables) {
        OpenTable(table);
    }
    AppendLog("workspace loaded: " + path.string());
}

void MainFrame::SaveWorkspaceFile(const std::filesystem::path& path) {
    std::ofstream out(path, std::ios::trunc);
    if (!out.is_open()) {
        wxMessageBox("Unable to save workspace file: " + path.string(), "Workspace", wxOK | wxICON_ERROR, this);
        return;
    }

    out << "# dottalkpp gui workspace v1\n";
    out << "kind=dtschema\n";
    for (const auto& area : area_infos_) {
        if (!area.path.empty()) {
            out << "table=" << area.path.string() << "\n";
        }
    }
    current_workspace_path_ = path;
    AppendLog("workspace saved: " + path.string());
}

void MainFrame::ShowTextWindow(const std::string& title, const std::string& body) {
    auto* dialog = new wxDialog(this, wxID_ANY, title, wxDefaultPosition, wxSize(820, 520));
    auto* sizer = new wxBoxSizer(wxVERTICAL);
    auto* text = new wxTextCtrl(dialog,
                                wxID_ANY,
                                body,
                                wxDefaultPosition,
                                wxDefaultSize,
                                wxTE_MULTILINE | wxTE_READONLY | wxTE_RICH2);
    sizer->Add(text, 1, wxEXPAND | wxALL, 8);
    sizer->Add(dialog->CreateSeparatedButtonSizer(wxOK), 0, wxEXPAND | wxLEFT | wxRIGHT | wxBOTTOM, 8);
    dialog->SetSizer(sizer);
    dialog->Show();
}

void MainFrame::AppendLog(const std::string& text) {
    if (log_) {
        log_->AppendText(text + "\n");
    }
}

} // namespace dottalk::gui::wxui
