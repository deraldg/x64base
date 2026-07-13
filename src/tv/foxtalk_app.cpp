// ---- TVision uses ----
#define Uses_TApplication
#define Uses_TDeskTop
#define Uses_TEvent
#define Uses_TMenuBar
#define Uses_TStatusLine
#define Uses_TBackground
#define Uses_TProgram
#define Uses_TScreen
#define Uses_TKeys
#define Uses_MsgBox
#define Uses_TEditWindow
#define Uses_TEditor
#define Uses_TFileDialog
#define Uses_TDialog
#define Uses_TObject

#if DOTTALK_TV_AVAILABLE
#include <tvision/tv.h>
#endif

#include "tv/foxtalk_app.hpp"

#include <algorithm>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <cstring>
#include <sstream>
#include <string>

#include "cli/command_registry.hpp"
#include "cli/shell_exit_request.hpp"
#include "tv/foxtalk_cmd_input.hpp"
#include "tv/foxtalk_command_window.hpp"
#include "tv/foxtalk_ids.hpp"
#include "tv/foxtalk_layout.hpp"
#include "tv/foxtalk_log_view.hpp"
#include "tv/foxtalk_menu.hpp"
#include "tv/foxtalk_output_window.hpp"
#include "tv/foxtalk_pro_menu_ids.hpp"
#include "tv/foxtalk_status.hpp"
#include "tv/foxtalk_util.hpp"
#include "tv/foxtalk_workspace_window.hpp"
#include "xbase.hpp"

// externs from your shell
extern "C" xbase::XBaseEngine* shell_engine();
extern "C" void register_shell_commands(xbase::XBaseEngine& eng, bool include_ui_cmds);

namespace foxtalk {

std::filesystem::path iniPath();

namespace {

const char* commandKeyHint();

static bool probeHasOpenTable(xbase::DbArea& area)
{
    return area.isOpen();
}

static std::string probeAlias(xbase::DbArea& area)
{
    return area.logicalName();
}

static std::string probeFileName(xbase::DbArea& area)
{
    return area.filename();
}

static long long probeRecno(xbase::DbArea& area)
{
    return static_cast<long long>(area.recno64());
}

static long long probeRecCount(xbase::DbArea& area)
{
    return static_cast<long long>(area.recCount64());
}

static bool probeDeleted(xbase::DbArea& area)
{
    return area.isDeleted();
}

static std::string probeOrderName(xbase::DbArea& area)
{
    (void)area;
    return {};
}

static std::string probeFilterText(xbase::DbArea& area)
{
    (void)area;
    return {};
}

static WindowGeometry makeWindowGeometry(int x, int y, int w, int h)
{
    WindowGeometry g;
    g.x = x;
    g.y = y;
    g.w = w;
    g.h = h;
    g.zoomed = false;
    return g;
}

struct FoxtalkZones
{
    WindowGeometry output;     // Persistent upper log pane.
    WindowGeometry workbench;  // Visible gray desktop band; not a window.
    WindowGeometry command;    // Persistent bottom command surface.
    WindowGeometry workspace;  // Small floating inspector.
};

static int desktopWidth()
{
    if (TProgram::deskTop)
        return std::max<int>(1, TProgram::deskTop->size.x);
    return std::max<int>(1, TScreen::screenWidth);
}

static int desktopHeight()
{
    if (TProgram::deskTop)
        return std::max<int>(1, TProgram::deskTop->size.y);
    return std::max<int>(1, TScreen::screenHeight);
}

static FoxtalkZones canonicalZones()
{
    const int dw = desktopWidth();
    const int dh = desktopHeight();

    const int commandH = std::min(4, std::max(3, dh - 2));
    const int commandY = std::max(0, dh - commandH);
    const int paneX = 1;
    const int paneW = std::max(20, dw - 2);

    const int outputY = 1;
    const int availableAboveCommand = std::max(0, commandY - outputY);

    // The gray desktop is an intentional workbench, not wasted space.
    // Keep a modest band visible on normal terminals, but give it up
    // before starving the output pane on small screens.
    const int desiredWorkbenchH = std::min(8, std::max(4, dh / 7));
    const int minOutputH = 6;
    const int workbenchH = std::max(0,
        std::min(desiredWorkbenchH, availableAboveCommand - minOutputH));
    const int outputH = std::max(minOutputH, availableAboveCommand - workbenchH);

    FoxtalkZones z;
    z.output = makeWindowGeometry(paneX, outputY, paneW, outputH);
    z.workbench = makeWindowGeometry(paneX, outputY + outputH, paneW,
                                     std::max(0, commandY - (outputY + outputH)));
    z.command = makeWindowGeometry(paneX, commandY, paneW, commandH);
    z.workspace = makeWindowGeometry(2, 1,
                                     std::min(32, std::max(20, dw - 4)),
                                     std::min(10, std::max(6, dh - 4)));
    return z;
}

static WindowGeometry canonicalCommandGeometry()
{
    return canonicalZones().command;
}

static WindowGeometry canonicalOutputGeometry()
{
    return canonicalZones().output;
}

static WindowGeometry canonicalWorkspaceGeometry()
{
    return canonicalZones().workspace;
}

static void clampGeometryToDesktop(WindowGeometry& g,
                                   const WindowGeometry& defaults,
                                   int minW,
                                   int minH)
{
    clampGeometryToScreen(
        g,
        desktopWidth(), desktopHeight(),
        defaults.x, defaults.y, defaults.w, defaults.h,
        minW, minH
    );
}

static TRect rectFromGeometry(const WindowGeometry& g)
{
    return TRect(
        S(g.x),
        S(g.y),
        S(g.x + g.w),
        S(g.y + g.h)
    );
}

struct SavedDesktopSize
{
    int w = 0;
    int h = 0;
};

static SavedDesktopSize readSavedDesktopSize()
{
    SavedDesktopSize s;

    std::ifstream in(iniPath());
    if (!in)
        return s;

    std::string line;
    while (std::getline(in, line)) {
        const auto pos = line.find('=');
        if (pos == std::string::npos)
            continue;

        const std::string k = trim(line.substr(0, pos));
        const std::string v = trim(line.substr(pos + 1));

        try {
            if (k == "desk.w" || k == "screen.w")
                s.w = std::stoi(v);
            else if (k == "desk.h" || k == "screen.h")
                s.h = std::stoi(v);
        }
        catch (...) {
            // Ignore malformed portability markers.
        }
    }

    return s;
}

static SavedDesktopSize gLoadedDesktopSize;

static bool savedGeometryMatchesDesktop()
{
    if (gLoadedDesktopSize.w <= 0 || gLoadedDesktopSize.h <= 0)
        return false;

    const int dw = desktopWidth();
    const int dh = desktopHeight();

    // Terminal resize can be off by a cell or two depending on host chrome.
    // Treat small drift as the same physical layout, but reflow portrait
    // vs. landscape and other material size changes.
    return std::abs(gLoadedDesktopSize.w - dw) <= 2
        && std::abs(gLoadedDesktopSize.h - dh) <= 1;
}

static void useCanonicalGeometry(LayoutState& state)
{
    const FoxtalkZones z = canonicalZones();
    state.output = z.output;
    state.command = z.command;
    state.output.zoomed = false;
    state.command.zoomed = false;
}

static void stampCurrentDesktopSize()
{
    gLoadedDesktopSize.w = desktopWidth();
    gLoadedDesktopSize.h = desktopHeight();
}

static void prepareLayoutForCurrentDesktop(LayoutState& state)
{
    if (!savedGeometryMatchesDesktop())
        useCanonicalGeometry(state);

    stampCurrentDesktopSize();
}

static bool saveLayoutStateForCurrentDesktop(const LayoutState& state)
{
    const bool ok = saveLayoutState(state);
    if (!ok)
        return false;

    std::ofstream out(iniPath(), std::ios::app);
    if (!out)
        return false;

    out << "desk.w=" << desktopWidth() << "\n";
    out << "desk.h=" << desktopHeight() << "\n";
    return true;
}

static unsigned short execEditorDialog(TDialog* d, void* data)
{
    if (!TProgram::application || !TProgram::deskTop || !d)
        return cmCancel;

    TView* p = TProgram::application->validView(d);
    if (!p)
        return cmCancel;

    if (data)
        p->setData(data);

    const unsigned short result = TProgram::deskTop->execView(p);
    if (result != cmCancel && data)
        p->getData(data);

    TObject::destroy(p);
    return result;
}

static unsigned short editorFileError(const char* prefix, const char* fileName)
{
    std::string msg = std::string(prefix) + (fileName ? fileName : "(unknown)") + ".";
    return messageBox(msg.c_str(), mfError | mfOKButton);
}

static unsigned short turboEditorDialog(int dialog, ...)
{
    va_list args;

    switch (dialog) {
    case edOutOfMemory:
        return messageBox("Not enough memory for this editor operation.", mfError | mfOKButton);

    case edReadError: {
        va_start(args, dialog);
        char* fileName = va_arg(args, char*);
        va_end(args);
        return editorFileError("Error reading file ", fileName);
    }

    case edWriteError: {
        va_start(args, dialog);
        char* fileName = va_arg(args, char*);
        va_end(args);
        return editorFileError("Error writing file ", fileName);
    }

    case edCreateError: {
        va_start(args, dialog);
        char* fileName = va_arg(args, char*);
        va_end(args);
        return editorFileError("Error creating file ", fileName);
    }

    case edSaveModify: {
        va_start(args, dialog);
        char* fileName = va_arg(args, char*);
        va_end(args);
        std::string msg = std::string(fileName ? fileName : "Untitled") + " has been modified. Save?";
        return messageBox(msg.c_str(), mfInformation | mfYesNoCancel);
    }

    case edSaveUntitled:
        return messageBox("Save untitled file?", mfInformation | mfYesNoCancel);

    case edSaveAs: {
        va_start(args, dialog);
        char* fileName = va_arg(args, char*);
        va_end(args);
        return execEditorDialog(
            new TFileDialog("*.*", "Save text file as", "~N~ame", fdOKButton, 101),
            fileName
        );
    }

    case edFind:
    case edReplace:
        return messageBox("Find/replace dialogs are not wired into ArcticTalk yet.",
                          mfInformation | mfOKButton);

    case edSearchFailed:
        return messageBox("Search string not found.", mfError | mfOKButton);

    case edReplacePrompt:
        return messageBox("Replace this occurrence?", mfInformation | mfYesNoCancel);
    }

    return cmCancel;
}

static TRect canonicalEditorRect()
{
    const int dw = desktopWidth();
    const int dh = desktopHeight();
    const FoxtalkZones z = canonicalZones();

    const int left = std::min(3, std::max(0, dw - 20));
    const int top = std::min(2, std::max(0, dh - 8));
    const int right = std::max(left + 40, dw - 3);
    const int bottomLimit = std::max(top + 10, z.command.y - 1);
    const int bottom = std::min(std::max(top + 10, dh - 5), bottomLimit);

    return TRect(S(left), S(top), S(std::min(dw, right)), S(std::min(dh, bottom)));
}

static bool openTextEditor(const std::string& fileName)
{
    if (!TProgram::application || !TProgram::deskTop)
        return false;

    TEditor::editorDialog = turboEditorDialog;

    TRect r = canonicalEditorRect();
    const char* path = fileName.empty() ? nullptr : fileName.c_str();
    TView* view = TProgram::application->validView(new TEditWindow(r, path, wnNoNumber));
    if (!view) {
        messageBox("Could not create editor window.", mfError | mfOKButton);
        return false;
    }

    TProgram::deskTop->insert(view);
    view->show();
    view->select();
    return true;
}

static bool openTextEditorDialog()
{
    char fileName[MAXPATH] = "*.dts";
    const unsigned short result = execEditorDialog(
        new TFileDialog("*.dts", "Open text / DotScript file", "~N~ame", fdOpenButton, 100),
        fileName
    );

    if (result == cmCancel)
        return false;

    return openTextEditor(fileName);
}

} // anonymous namespace

TFoxtalkApp::TFoxtalkApp()
    : TProgInit(&TFoxtalkApp::initStatusLine,
                &TFoxtalkApp::initMenuBar,
                &TFoxtalkApp::initDeskTop),
      redirect_(this)
{
    loadState();
    prepareLayoutForCurrentDesktop(layout_);

    createBackground();
    createOutputWindow();
    createCommandWindow();
    createWorkspaceWindow();

    static bool registered = false;
    if (!registered) {
        if (auto* eng = shell_engine())
            register_shell_commands(*eng, false);
        registered = true;
    }

    redirect_.install(OutputMode::ToWindow);
    redirect_.setMode(OutputMode::ToWindow);

    applyStateToWindows();
    refreshWorkspaceWindow();

    if (cmdWin_) {
        cmdWin_->show();
        cmdWin_->select();
        cmdWin_->focusInput();
    }

    showMessage(commandKeyHint());
}

TFoxtalkApp::~TFoxtalkApp()
{
    saveStateFromWindows();
    saveLayoutStateForCurrentDesktop(layout_);
}

TMenuBar* TFoxtalkApp::initMenuBar(TRect bounds)
{
    return buildMenuBar(bounds);
}

TStatusLine* TFoxtalkApp::initStatusLine(TRect bounds)
{
    return buildStatusLine(bounds);
}

TDeskTop* TFoxtalkApp::initDeskTop(TRect bounds)
{
    return new TDeskTop(bounds);
}

void TFoxtalkApp::idle()
{
    TApplication::idle();
    std::cout.flush();
    std::cerr.flush();
    flushPending();
}

void TFoxtalkApp::enqueueChunk(const std::string& s)
{
    std::lock_guard<std::mutex> lk(qMutex_);
    pending_.push_back(s);

    if (!flushPosted_) {
        flushPosted_ = true;
        TEvent ev{};
        ev.what = evCommand;
        ev.message.command = cmFlushLog;
        putEvent(ev);
    }
}

void TFoxtalkApp::flushPending()
{
    std::vector<std::string> chunks;

    {
        std::lock_guard<std::mutex> lk(qMutex_);
        if (pending_.empty())
            return;
        chunks.swap(pending_);
        flushPosted_ = false;
    }

    if (outWin_ && outWin_->logView())
        outWin_->logView()->appendBatch(chunks);
}

void TFoxtalkApp::createBackground()
{
    if (!deskTop)
        return;

    deskTop->insert(new TBackground(deskTop->getExtent(), 0x20));
}

void TFoxtalkApp::createOutputWindow()
{
    clampGeometryToDesktop(layout_.output, canonicalOutputGeometry(), 20, 6);

    outWin_ = new FoxtalkOutputWindow(rectFromGeometry(layout_.output), "ArcticTalk Output", 0);
    deskTop->insert(outWin_);
}

void TFoxtalkApp::createCommandWindow()
{
    clampGeometryToDesktop(layout_.command, canonicalCommandGeometry(), 20, 3);

    cmdWin_ = new FoxtalkCommandWindow(rectFromGeometry(layout_.command), "Command", 0);

    if (!layout_.lastInput.empty())
        cmdWin_->setInputText(layout_.lastInput);

    deskTop->insert(cmdWin_);
}

void TFoxtalkApp::createWorkspaceWindow()
{
    const WindowGeometry ws = canonicalWorkspaceGeometry();
    wsWin_ = new FoxtalkWorkspaceWindow(rectFromGeometry(ws), "Workspace", 0);
    deskTop->insert(wsWin_);
    refreshWorkspaceWindow();
}

void TFoxtalkApp::showOutputWindow()
{
    if (outWin_) {
        outWin_->show();
        outWin_->select();
        if (outWin_->logView()) {
            outWin_->logView()->select();
            outWin_->logView()->focus();
        }
    }
}

void TFoxtalkApp::showWorkspaceWindow()
{
    if (!wsWin_)
        return;

    refreshWorkspaceWindow();
    wsWin_->show();
    wsWin_->select();

    if (wsWin_->workspaceView()) {
        wsWin_->workspaceView()->select();
        wsWin_->workspaceView()->focus();
    }
}

void TFoxtalkApp::showMessage(const std::string& m)
{
    if (cmdWin_)
        cmdWin_->setMessage(m);
}

namespace {

bool isNestedTvCommand(const std::string& cmd)
{
    return cmd == "ARCTICTALK" ||
           cmd == "FOXTALK" ||
           cmd == "TVISION" ||
           cmd == "BROWSETV" ||
           cmd == "BROWSETUI";
}

bool isSubappExitCommand(const std::string& cmd)
{
    return cmd == "EXIT" ||
           cmd == "QUIT" ||
           cmd == "CANCEL" ||
           cmd == "ABORT";
}

const char* commandKeyHint()
{
    return "Enter/Run | Up/Dn History | Ctrl-Q Cmd | F2 Out | F3 Rec | F4 Work | Alt-X Close";
}

} // namespace

void TFoxtalkApp::runImmediate(const std::string& line)
{
    if (!cmdWin_)
        return;

    cmdWin_->setInputText(line);

    TEvent ev{};
    ev.what = evCommand;
    ev.message.command = cmRunCmd;
    putEvent(ev);
}

void TFoxtalkApp::runFromInput()
{
    if (!cmdWin_)
        return;

    const std::string s = trim(cmdWin_->getInputText());
    if (!s.empty()) {
        executeCommandLine(s);
        cmdWin_->setInputText("");
    }

    cmdWin_->focusInput();
}

void TFoxtalkApp::executeCommandLine(const std::string& line)
{
    const std::string trimmed = trim(line);
    if (trimmed.empty())
        return;

    pushHistory(trimmed);
    layout_.lastInput = trimmed;

    const std::string resolved = shell_.resolveShortcuts(trimmed);
    std::cout << "> " << resolved << "\n";

    {
        std::istringstream tok(resolved);
        std::string cmd;
        tok >> cmd;
        cmd = upcopy(cmd);

        std::string rest;
        std::getline(tok, rest);
        rest = trim(rest);
        const std::string restUpper = upcopy(rest);

        if (isSubappExitCommand(cmd) && restUpper.empty()) {
            xbase::clear_shell_exit_request();
            std::cout << "Leaving ArcticTalk; returning to DotTalk++ shell.\n";
            showMessage("Returning to DotTalk++ shell.");
            TEvent quit{};
            quit.what = evCommand;
            quit.message.command = cmQuit;
            putEvent(quit);
            return;
        }

        if ((cmd == "CLEAR" && (restUpper.empty() || restUpper == "OUTPUT" || restUpper == "SCREEN")) ||
            cmd == "CLS") {
            if (outWin_ && outWin_->logView()) {
                outWin_->logView()->clearAll();
                showMessage("Output cleared.");
            }
            return;
        }

        if (cmd == "HISTORY") {
            if (restUpper.empty() || restUpper == "STATUS") {
                std::cout << "ArcticTalk history: "
                          << (layout_.persistHistory ? "persistent" : "fresh per session")
                          << ", entries: " << layout_.history.size() << "\n";
                std::cout << "Usage: HISTORY STATUS | CLEAR | FRESH | KEEP\n";
                showMessage(layout_.persistHistory ? "History persists across sessions." : "History is session-only.");
                return;
            }

            if (restUpper == "CLEAR") {
                layout_.history.clear();
                layout_.lastInput.clear();
                histPos_ = 0;
                if (cmdWin_)
                    cmdWin_->setInputText("");
                saveStateFromWindows();
                saveLayoutStateForCurrentDesktop(layout_);
                std::cout << "ArcticTalk command history cleared.\n";
                showMessage("History cleared.");
                return;
            }

            if (restUpper == "FRESH" || restUpper == "OFF" || restUpper == "SESSION") {
                layout_.persistHistory = false;
                layout_.history.clear();
                layout_.lastInput.clear();
                histPos_ = 0;
                if (cmdWin_)
                    cmdWin_->setInputText("");
                saveStateFromWindows();
                saveLayoutStateForCurrentDesktop(layout_);
                std::cout << "ArcticTalk command history is now fresh per session.\n";
                showMessage("History persistence off.");
                return;
            }

            if (restUpper == "KEEP" || restUpper == "ON" || restUpper == "PERSIST") {
                layout_.persistHistory = true;
                saveStateFromWindows();
                saveLayoutStateForCurrentDesktop(layout_);
                std::cout << "ArcticTalk command history will persist across sessions.\n";
                showMessage("History persistence on.");
                return;
            }

            std::cout << "Usage: HISTORY STATUS | CLEAR | FRESH | KEEP\n";
            showMessage("HISTORY usage shown.");
            return;
        }

        if (isNestedTvCommand(cmd)) {
            std::cout << cmd << " is not launched from inside ArcticTalk. Use the outer CLI unless this app is explicitly integrated.\n";
            showMessage("Nested TVision app blocked inside ArcticTalk.");
            return;
        }

        if (cmd == "TED" || cmd == "TEDIT" || cmd == "TURBOEDIT") {
            const bool opened = rest.empty() ? openTextEditorDialog() : openTextEditor(rest);
            if (opened) {
                const std::string openedMsg = rest.empty() ? std::string(".") : (std::string(": ") + rest);
                std::cout << "ArcticTalk editor opened" << openedMsg << "\n";
                showMessage(rest.empty() ? "Editor opened." : ("Editor: " + rest));
            }
            else {
                showMessage("Editor canceled or unavailable.");
            }
            return;
        }

        if (cmd == "WIN") {
            std::string sub;
            std::istringstream subtok(rest);
            subtok >> sub;
            sub = upcopy(trim(sub));

            if (sub == "SAVE") {
                saveStateFromWindows();
                saveLayoutStateForCurrentDesktop(layout_);
                std::cout << "Window layout saved.\n";
                showMessage("WIN SAVE done.");
                refreshWorkspaceWindow();
                return;
            }

            if (sub == "RESTORE") {
                loadState();
                applyStateToWindows();
                std::cout << "Window layout restored.\n";
                showMessage("WIN RESTORE done.");
                refreshWorkspaceWindow();
                return;
            }

            if (sub == "DEFAULTS" || sub == "RESET") {
                resetOutputWindow();
                resetCommandWindow();
                saveStateFromWindows();
                saveLayoutStateForCurrentDesktop(layout_);
                std::cout << "Window layout reset to defaults.\n";
                showMessage("WIN DEFAULTS done.");
                refreshWorkspaceWindow();
                return;
            }

            std::cout << "Usage: WIN SAVE | WIN RESTORE | WIN DEFAULTS\n";
            showMessage("WIN usage shown.");
            refreshWorkspaceWindow();
            return;
        }
    }

    const ShellRunResult result = shell_.runLine(curArea(), trimmed);
    if (!result.statusMessage.empty()) {
        if (result.success)
            showMessage(commandKeyHint());
        else
            showMessage(result.statusMessage);
    }

    refreshWorkspaceWindow();
}

void TFoxtalkApp::pushHistory(const std::string& s)
{
    if (layout_.history.empty() || layout_.history.back() != s)
        layout_.history.push_back(s);

    if (static_cast<int>(layout_.history.size()) > kMaxHistory) {
        layout_.history.erase(
            layout_.history.begin(),
            layout_.history.begin() + (static_cast<int>(layout_.history.size()) - kMaxHistory)
        );
    }

    histPos_ = static_cast<int>(layout_.history.size());
}

void TFoxtalkApp::historyPrev()
{
    if (layout_.history.empty())
        return;

    if (histPos_ > 0)
        --histPos_;

    setInputFromHistory();
}

void TFoxtalkApp::historyNext()
{
    if (layout_.history.empty())
        return;

    if (histPos_ < static_cast<int>(layout_.history.size()))
        ++histPos_;

    setInputFromHistory();
}

void TFoxtalkApp::setInputFromHistory()
{
    if (!cmdWin_)
        return;

    std::string txt;
    if (histPos_ >= 0 && histPos_ < static_cast<int>(layout_.history.size()))
        txt = layout_.history[static_cast<std::size_t>(histPos_)];

    cmdWin_->setInputText(txt);
    cmdWin_->focusInput();

    if (histPos_ >= 0 && histPos_ < static_cast<int>(layout_.history.size()))
        showMessage("History: " + txt);
    else
        showMessage("History end.");
}

void TFoxtalkApp::loadState()
{
    loadLayoutState(layout_, kMaxHistory);
    gLoadedDesktopSize = readSavedDesktopSize();
    histPos_ = static_cast<int>(layout_.history.size());
}

void TFoxtalkApp::saveStateFromWindows()
{
    if (outWin_) {
        layout_.output.x = outWin_->origin.x;
        layout_.output.y = outWin_->origin.y;
        layout_.output.w = outWin_->size.x;
        layout_.output.h = outWin_->size.y;
        layout_.output.zoomed = false;
    }

    if (cmdWin_) {
        layout_.command.x = cmdWin_->origin.x;
        layout_.command.y = cmdWin_->origin.y;
        layout_.command.w = cmdWin_->size.x;
        layout_.command.h = cmdWin_->size.y;
        layout_.command.zoomed = false;
    }
}

void TFoxtalkApp::applyStateToWindows()
{
    prepareLayoutForCurrentDesktop(layout_);

    clampGeometryToDesktop(layout_.output, canonicalOutputGeometry(), 20, 6);
    clampGeometryToDesktop(layout_.command, canonicalCommandGeometry(), 20, 3);

    if (outWin_) {
        TRect r = rectFromGeometry(layout_.output);
        outWin_->locate(r);
    }

    if (cmdWin_) {
        TRect r = rectFromGeometry(layout_.command);
        cmdWin_->locate(r);
        cmdWin_->focusInput();
    }
}

void TFoxtalkApp::toggleZoomCommandWindow()
{
    if (!cmdWin_)
        return;

    message(cmdWin_, evCommand, cmZoom, cmdWin_);
    cmdWin_->focusInput();
}

void TFoxtalkApp::resetCommandWindow()
{
    if (!cmdWin_)
        return;

    layout_.command = canonicalCommandGeometry();
    TRect r = rectFromGeometry(layout_.command);
    cmdWin_->locate(r);
    cmdWin_->flags |= (wfMove | wfGrow | wfZoom);
    cmdWin_->select();
    cmdWin_->focusInput();
    showMessage("Command window restored.");
}

void TFoxtalkApp::toggleZoomOutputWindow()
{
    if (!outWin_)
        return;

    message(outWin_, evCommand, cmZoom, outWin_);
    if (outWin_->logView()) {
        outWin_->logView()->select();
        outWin_->logView()->focus();
    }
}

void TFoxtalkApp::resetOutputWindow()
{
    if (!outWin_)
        return;

    layout_.output = canonicalOutputGeometry();
    TRect r = rectFromGeometry(layout_.output);
    outWin_->locate(r);
    outWin_->flags |= (wfMove | wfGrow | wfZoom);
    outWin_->select();

    if (outWin_->logView()) {
        outWin_->logView()->select();
        outWin_->logView()->focus();
    }

    showMessage("Output window restored.");
}

void TFoxtalkApp::refreshWorkspaceWindow()
{
    if (!wsWin_)
        return;

    wsWin_->setSnapshot(makeWorkspaceSnapshot());
}

WorkspaceSnapshot TFoxtalkApp::makeWorkspaceSnapshot()
{
    WorkspaceSnapshot s;

    auto* eng = shell_engine();
    if (!eng)
        return s;

    s.areaNumber = eng->currentArea();

    xbase::DbArea& area = eng->area(s.areaNumber);

    s.hasOpenTable = probeHasOpenTable(area);
    if (!s.hasOpenTable)
        return s;

    s.alias      = probeAlias(area);
    s.fileName   = probeFileName(area);
    s.recno      = probeRecno(area);
    s.recCount   = probeRecCount(area);
    s.deleted    = probeDeleted(area);
    s.orderName  = probeOrderName(area);
    s.filterText = probeFilterText(area);

    return s;
}

bool TFoxtalkApp::dispatchMenu(int id)
{
    auto run = [this](const char* line) -> bool {
        runImmediate(line);
        return true;
    };

    auto prefill = [this](const char* line) -> bool {
        if (cmdWin_) {
            cmdWin_->setInputText(line);
            cmdWin_->show();
            cmdWin_->select();
            cmdWin_->focusInput();
            showMessage(std::string("Ready: ") + line);
        }
        return true;
    };

    auto info = [](const char* message) -> bool {
        messageBox(message, mfInformation);
        return true;
    };

    auto editFile = [this](const char* path) -> bool {
        if (openTextEditor(path ? path : ""))
            showMessage(std::string("Editor: ") + (path ? path : "untitled"));
        else
            showMessage("Editor unavailable.");
        return true;
    };

    auto editDialog = [this]() -> bool {
        if (openTextEditorDialog())
            showMessage("Editor opened.");
        else
            showMessage("Editor canceled.");
        return true;
    };

    switch (id) {
        // Existing prototype menu ids: preserved for compatibility with any
        // stale events, saved status bindings, or local experiments.
        case cmFileOpen:       return prefill("USE ");
        case cmFileClose:      return run("CLOSE");
        case cmAreaSelect:     return prefill("AREA ");
        case cmIndexOpen:      return prefill("SET INDEX TO ");
        case cmIndexClose:     return run("SET INDEX TO");
        case cmWinSave:        return run("WIN SAVE");
        case cmWinRestore:     return run("WIN RESTORE");
        case cmWinDefaults:    return run("WIN DEFAULTS");

        case cmBrowse:         return run("BROWSE");
        case cmRecordView:     return run("RECORDVIEW");
        case cmList:           return run("LIST");
        case cmSmartList:      return run("SMARTLIST");
        case cmCount:          return run("COUNT");
        case cmFind:           return prefill("FIND ");
        case cmLocate:         return prefill("LOCATE FOR ");
        case cmWhere:          return prefill("WHERE ");
        case cmWhereClear:     return run("SET FILTER TO");

        case cmWorkspace:
            showWorkspaceWindow();
            return true;

        case cmShowDeletedStub: return info("Use command line: SET DELETED ON | SET DELETED OFF");
        case cmStatusStub:      return run("STATUS");
        case cmSeek:            return prefill("SEEK ");
        case cmSetOrder:        return prefill("SET ORDER TO ");
        case cmReindex:         return run("REINDEX");
        case cmTagManagerStub:  return info("Tag Manager will become a real dialog after menu validation.");
        case cmOrderInfoStub:   return run("STATUS");
        case cmSetRelation:     return prefill("SET RELATION TO ");
        case cmRelRefresh:      return run("REL REFRESH");
        case cmRelClear:        return run("SET RELATION OFF ALL");
        case cmRelBrowserStub:  return prefill("REL ENUM LIMIT 10 ");
        case cmAppend:          return run("APPEND");
        case cmEdit:            return run("EDIT");
        case cmDelete:          return run("DELETE");
        case cmRecall:          return run("RECALL");
        case cmPack:            return run("PACK");
        case cmTurboPack:       return run("TURBOPACK");
        case cmZapStub:         return info("ZAP is intentionally not run from this menu yet. Type ZAP manually when you mean it.");
        case cmBlankStub:       return run("APPEND_BLANK");
        case cmCalc:            return prefill("CALC ");
        case cmEval:            return prefill("EVAL ");
        case cmHelp:            return run("HELP");
        case cmSelfTest:        return run("/SELFTEST 300");
        case cmHistorySizeStub: return info("History sizing remains fixed for now.");
        case cmVerbosityStub:   return info("Message verbosity is a future ArcticTalk preference.");
        case cmOutputModeStub:  return info("Output routing remains command-driven for now.");
        case cmPaletteColor:    return prefill("COLOR ");
        case cmKeysStub:        return info("Keys: Enter/Run executes | Up/Down history | F10 Menu | Ctrl-Q Command | F2 Output | F3 Record | F4 Workspace | Alt-Z/Ctrl-F5 Command | Alt-O/Ctrl-F6 Output | Alt-X closes ArcticTalk");
        case cmAboutStub:       return info("ArcticTalk (DotTalk++) - Turbo Vision / MagicBLOT command desktop.");

        // System.
        case cmFtSysAbout:       return run("ABOUT");
        case cmFtSysVersion:     return run("VERSION");
        case cmFtSysStatus:      return run("STATUS");
        case cmFtSysPaths:       return run("SET PATH");
        case cmFtSysColorDefault:return run("COLOR DEFAULT");
        case cmFtSysColorGreen:  return run("COLOR GREEN");
        case cmFtSysColorAmber:  return run("COLOR AMBER");
        case cmFtSysShell:       return prefill("! ");
        case cmFtSysDotScriptX32: return run("DOTSCRIPT x32");
        case cmFtSysDotScriptX64: return run("DOTSCRIPT x64");
        case cmFtSysDotScriptSandbox: return run("DOTSCRIPT sandbox");
        case cmFtSysDotScriptInit: return prefill("DOTSCRIPT init.ini");
        case cmFtSysDotScriptShutdown: return prefill("DOTSCRIPT shutdown.ini");
        case cmFtSysShowDottalkIni: return run("SHOWINI");
        case cmFtSysEditDottalkIni: return editFile("dottalkpp.ini");
        case cmFtSysEditInitIni: return editFile("init.ini");
        case cmFtSysEditShutdownIni: return editFile("shutdown.ini");
        case cmFtSysEditDotScript: return editDialog();
        case cmFtSysEditScratch: return editFile("");

        // File.
        case cmFtFileUse:        return prefill("USE ");
        case cmFtFileClose:      return run("CLOSE");
        case cmFtFileCloseAll:   return run("WORKSPACE CLOSE");
        case cmFtFileSelect:     return prefill("SELECT ");
        case cmFtFileDir:        return prefill("DIR ");
        case cmFtFileImport:     return prefill("IMPORT ");
        case cmFtFileExport:     return prefill("EXPORT ");
        case cmFtFileDotScript:  return prefill("DOTSCRIPT ");

        // Workspace.
        case cmFtWorkSummary:    return run("WORKSPACE");
        case cmFtWorkOpenDbf:    return run("WORKSPACE OPEN DBF");
        case cmFtWorkOpenDir:    return prefill("WORKSPACE OPEN ");
        case cmFtWorkSave:       return prefill("WORKSPACE SAVE ");
        case cmFtWorkLoad:       return prefill("WORKSPACE LOAD ");
        case cmFtWorkClose:      return run("WORKSPACE CLOSE");
        case cmFtWorkArea:       return run("AREA");
        case cmFtWorkDbarea:     return run("DBAREA");
        case cmFtWorkDbareas:    return run("DBAREAS");
        case cmFtWorkReport:     return run("WSREPORT");
        case cmFtWorkRefresh:    return run("REFRESH");

        // Ersatz/demo workflows.
        case cmFtErsatzMcc:      return run("ERSATZ MCC");
        case cmFtErsatzPrompt:   return prefill("ERSATZ ");
        case cmFtErsatzWorkspace:return run("WORKSPACE");
        case cmFtErsatzRelAll:   return run("REL LIST ALL");
        case cmFtErsatzRecord:   return run("RECORDVIEW");

        // Table/schema/state.
        case cmFtTableStruct:    return run("STRUCT");
        case cmFtTableFields:    return run("FIELDS");
        case cmFtTableStatus:    return run("STATUS");
        case cmFtTableMeta:      return run("TABLEMETA");
        case cmFtTableValidate:  return run("VALIDATE");
        case cmFtTableDDL:       return prefill("DDL ");
        case cmFtTableShow:      return run("SHOW");
        case cmFtTableBufferOn:  return run("TABLE ON");
        case cmFtTableBufferOff: return run("TABLE OFF");
        case cmFtTableStale:     return run("TABLE STALE");
        case cmFtTableFresh:     return prefill("TABLE FRESH ");
        case cmFtTableCommit:    return run("COMMIT");
        case cmFtTableRollback:  return info("ROLLBACK is listed but not confirmed in current shakedowns. Type it manually if you are testing it.");

        // Record/navigation/editing.
        case cmFtRecView:        return run("RECORDVIEW");
        case cmFtRecDisplay:     return run("DISPLAY");
        case cmFtRecContext:     return run("RECORD");
        case cmFtRecGoto:        return prefill("GOTO ");
        case cmFtRecTop:         return run("TOP");
        case cmFtRecBottom:      return run("BOTTOM");
        case cmFtRecSkipForward: return run("SKIP 1");
        case cmFtRecSkipBack:    return run("SKIP -1");
        case cmFtRecAppend:      return run("APPEND");
        case cmFtRecAppendBlank: return run("APPEND_BLANK");
        case cmFtRecEdit:        return run("EDIT");
        case cmFtRecReplace:     return prefill("REPLACE ");
        case cmFtRecDelete:      return run("DELETE");
        case cmFtRecRecall:      return run("RECALL");
        case cmFtRecPack:        return run("PACK");
        case cmFtRecZapSafe:     return info("ZAP is destructive. For now ArcticTalk only reminds you; type ZAP manually if intentional.");
        case cmFtRecLock:        return run("LOCK");
        case cmFtRecUnlock:      return run("UNLOCK");

        // Index/order/search.
        case cmFtIdxSetIndex:    return prefill("SET INDEX TO ");
        case cmFtIdxSetOrder:    return prefill("SET ORDER TO ");
        case cmFtIdxPhysical:    return run("SET ORDER TO 0");
        case cmFtIdxSeek:        return prefill("SEEK ");
        case cmFtIdxFind:        return prefill("FIND ");
        case cmFtIdxIndexSeek:   return prefill("INDEXSEEK ");
        case cmFtIdxAscend:      return run("ASCEND");
        case cmFtIdxDescend:     return run("DESCEND");
        case cmFtIdxReindex:     return run("REINDEX");
        case cmFtIdxBuildLmdb:   return run("BUILDLMDB");
        case cmFtIdxCnx:         return prefill("CNX ");
        case cmFtIdxCdx:         return prefill("CDX ");
        case cmFtIdxLmdb:        return prefill("LMDB ");

        // Lists/filtering/projection.
        case cmFtListList:       return run("LIST");
        case cmFtListList10:     return run("LIST 10");
        case cmFtListSmart:      return run("SMARTLIST");
        case cmFtListSmartFilter:return prefill("SMARTLIST 20 FOR ");
        case cmFtListDisplay:    return run("DISPLAY");
        case cmFtListCount:      return prefill("COUNT FOR ");
        case cmFtListSum:        return prefill("SUM ");
        case cmFtListAverage:    return prefill("AVERAGE ");
        case cmFtListWhere:      return prefill("WHERE ");
        case cmFtListSetFilter:  return prefill("SET FILTER TO ");
        case cmFtListClearFilter:return run("SET FILTER TO");
        case cmFtListPredHelp:   return run("PREDHELP");
        case cmFtListPredicates: return run("PREDICATES");

        // Browsers.
        case cmFtBrowseCurrent:  return run("BROWSE");
        case cmFtBrowseSimple:   return prefill("SIMPLEBROWSER ");
        case cmFtBrowseSmart:    return prefill("SMARTBROWSER ");
        case cmFtBrowseText:     return info("BROWSETUI is not launched inside ArcticTalk yet. Use the outer CLI until it is integrated.");
        case cmFtBrowseTv:       return info("BROWSETV is not launched inside ArcticTalk yet. Use the outer CLI until it is integrated.");
        case cmFtBrowseDev:      return run("BROWSER");
        case cmFtBrowseRecord:   return run("RECORDVIEW");
        case cmFtBrowseChildren: return prefill("SIMPLEBROWSER SHOW CHILDREN LIMIT 20");
        case cmFtBrowseFor:      return prefill("SIMPLEBROWSER FOR ");
        case cmFtBrowseOrder:    return prefill("SIMPLEBROWSER ORDER ");

        // Relations.
        case cmFtRelSet:         return prefill("SET RELATION TO ");
        case cmFtRelSetAdd:      return prefill("SET RELATION ADDITIVE TO ");
        case cmFtRelOffInto:     return prefill("SET RELATION OFF INTO ");
        case cmFtRelOffAll:      return run("SET RELATION OFF ALL");
        case cmFtRelList:        return run("REL LIST");
        case cmFtRelListAll:     return run("REL LIST ALL");
        case cmFtRelRefresh:     return run("REL REFRESH");
        case cmFtRelAdd:         return prefill("REL ADD ");
        case cmFtRelClear:       return prefill("REL CLEAR ");
        case cmFtRelSave:        return prefill("REL SAVE ");
        case cmFtRelLoad:        return prefill("REL LOAD ");
        case cmFtRelEnum:        return prefill("REL ENUM LIMIT 10 ");

        // Tuples.
        case cmFtTupleAll:       return run("TUPLE *");
        case cmFtTupleFields:    return prefill("TUPLE ");
        case cmFtTupleArea:      return prefill("TUPLE #");
        case cmFtTupleMixed:     return prefill("TUPLE #9.*,#11.LNAME");
        case cmFtTupleTuptalk:   return prefill("TUPTALK ");
        case cmFtTupleExport:    return prefill("TUPEXPORT ");
        case cmFtTupleValidate:  return run("TUPVALIDATE");
        case cmFtTupleRelEnum:   return prefill("REL ENUM LIMIT 10 ");

        // Functions/expressions.
        case cmFtFuncCalc:       return prefill("CALC ");
        case cmFtFuncEval:       return prefill("EVAL ");
        case cmFtFuncCatalog:    return run("EXPFUNCS");
        case cmFtFuncPredHelp:   return run("PREDHELP");
        case cmFtFuncPredicates: return run("PREDICATES");
        case cmFtFuncUpper:      return prefill("CALC UPPER(\"\")");
        case cmFtFuncDate:       return prefill("CALC DATE()");
        case cmFtFuncNumericHelp:return prefill("HELP ABS");
        case cmFtFuncStringHelp: return prefill("HELP UPPER");

        // Command/help/test surface.
        case cmFtCmdHelp:        return run("HELP");
        case cmFtCmdFoxHelp:     return run("FOXHELP");
        case cmFtCmdCatalog:     return run("CMDHELP");
        case cmFtCmdBuildCatalog:return run("CMDHELP BUILD");
        case cmFtCmdValidateCatalog:return run("CMDHELPCHK");
        case cmFtCmdArgCheck:    return run("CMDARGCHK");
        case cmFtCmdCommandsHelp:return run("COMMANDSHELP");
        case cmFtCmdDotScript:   return prefill("DOTSCRIPT ");
        case cmFtCmdTest:        return prefill("TEST ");
        case cmFtCmdShow:        return run("SHOW");
        case cmFtCmdDump:        return run("DUMP");
        case cmFtCmdSetVar:      return prefill("SET VAR ");
        case cmFtCmdSetVarBang:  return prefill("SET VAR! ");
        case cmFtCmdSqlVersion:  return run("SQLVER");
        case cmFtCmdSqlite:      return run("SQLITE");
        case cmFtCmdSqlExec:     return prefill("SQL ");
        case cmFtCmdSqlSelect:   return prefill("SQLSEL ");

        // Help.
        case cmFtHelpMain:       return run("HELP");
        case cmFtHelpCommand:    return prefill("HELP ");
        case cmFtHelpFox:        return run("FOXHELP");
        case cmFtHelpPred:       return run("PREDHELP");
        case cmFtHelpWorkspace:  return run("HELP WORKSPACE");
        case cmFtHelpRelations:  return run("HELP REL");
        case cmFtHelpTuple:      return run("HELP TUPLE");
        case cmFtHelpBrowser:    return run("HELP SIMPLEBROWSER");
        case cmFtHelpKeys:       return info("Keys: Enter/Run executes | Up/Down history | F10 Menu | Ctrl-Q Command | F2 Output | F3 Record | F4 Workspace | Alt-Z/Ctrl-F5 Command | Alt-O/Ctrl-F6 Output | Alt-X closes ArcticTalk");
        case cmFtWinClearOutput: if (outWin_ && outWin_->logView()) { outWin_->logView()->clearAll(); showMessage("Output cleared."); } return true;

        case cmFtHelpAbout:      return info("ArcticTalk is the Turbo Vision / MagicBLOT command desktop for DotTalk++.");
    }

    return false;
}

void TFoxtalkApp::handleEvent(TEvent& event)
{
    if (event.what == evCommand && event.message.command == cmFlushLog) {
        flushPending();
        clearEvent(event);
        return;
    }

    if (event.what == evCommand && event.message.command == cmRunCmd) {
        runFromInput();
        clearEvent(event);
        return;
    }

    if (event.what == evCommand && event.message.command == cmTalkExit) {
        xbase::clear_shell_exit_request();
        TEvent quit{};
        quit.what = evCommand;
        quit.message.command = cmQuit;
        putEvent(quit);
        clearEvent(event);
        return;
    }

    TApplication::handleEvent(event);

    if (event.what == evKeyDown) {
        if (event.keyDown.keyCode == kbCtrlQ) {
            if (cmdWin_) {
                cmdWin_->show();
                cmdWin_->select();
                cmdWin_->focusInput();
            }
            clearEvent(event);
            return;
        }

        if (event.keyDown.keyCode == kbF2) {
            showOutputWindow();
            clearEvent(event);
            return;
        }

        if (event.keyDown.keyCode == kbF3) {
            runImmediate("RECORDVIEW");
            clearEvent(event);
            return;
        }

        if (event.keyDown.keyCode == kbF4) {
            showWorkspaceWindow();
            clearEvent(event);
            return;
        }

        if (event.keyDown.keyCode == kbAltX) {
            event.what = evCommand;
            event.message.command = cmTalkExit;
        }

        if (event.keyDown.keyCode == kbAltZ) {
            event.what = evCommand;
            event.message.command = cmZoomCmd;
        }

        if (event.keyDown.keyCode == kbCtrlF5) {
            event.what = evCommand;
            event.message.command = cmResetCmdWin;
        }

        if (event.keyDown.keyCode == kbAltO) {
            event.what = evCommand;
            event.message.command = cmZoomOut;
        }

        if (event.keyDown.keyCode == kbCtrlF6) {
            event.what = evCommand;
            event.message.command = cmResetOutWin;
        }

        if (cmdWin_ && cmdWin_->input() && cmdWin_->input()->getState(sfFocused)) {
            if (event.keyDown.keyCode == kbUp) {
                historyPrev();
                clearEvent(event);
                return;
            }
            if (event.keyDown.keyCode == kbDown) {
                historyNext();
                clearEvent(event);
                return;
            }
        }
    }

    if (event.what == evCommand) {
        const int id = event.message.command;

        if (id == cmShowOutput) {
            showOutputWindow();
            clearEvent(event);
            return;
        }

        if (id == cmWorkspace) {
            showWorkspaceWindow();
            clearEvent(event);
            return;
        }

        if (id == cmFocusCmd) {
            if (cmdWin_) {
                cmdWin_->show();
                cmdWin_->select();
                cmdWin_->focusInput();
            }
            clearEvent(event);
            return;
        }

        if (id == cmZoomCmd) {
            toggleZoomCommandWindow();
            clearEvent(event);
            return;
        }

        if (id == cmResetCmdWin) {
            resetCommandWindow();
            clearEvent(event);
            return;
        }

        if (id == cmZoomOut) {
            toggleZoomOutputWindow();
            clearEvent(event);
            return;
        }

        if (id == cmResetOutWin) {
            resetOutputWindow();
            clearEvent(event);
            return;
        }

        if (dispatchMenu(id)) {
            clearEvent(event);
            return;
        }
    }
}

xbase::DbArea& TFoxtalkApp::curArea()
{
    auto* e = shell_engine();
    return e->area(e->currentArea());
}

} // namespace foxtalk
