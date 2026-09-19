# ArcticTalk Workbench

The Workbench begins with your saved workspace catalog and its database images.
Its layout is authored as a UIDEF DBF and compiled to native wx/C++. Database
inspection uses x64base's own DBF, DTX and MINIDB readers. The Live session tab
hosts one engine on one worker, using the prompt's canonical command executor.

Development follows [M1 through M7](../../docs/maintenance/AIF120_WORKBENCH_MILESTONES_V1.md).
The working foundation is the baseline; M1 covers native menus and modal workflow.

## Launch

From PowerShell, after building:

```powershell
& D:\code\ccode\build\uidef-native\Release\arctictalk_workbench_m3.exe
```

Or double-click the executable. It locates installation DATA from the executable
location (including this development build), initializes native path defaults,
and runs the native INIT flow using BIN/dottalkpp.ini followed by BIN/init.ini.
Saved catalogs opens WORKSPACES/WORKSPACES.dbf automatically. Here that is
D:\code\ccode\dottalkpp\data\workspaces\WORKSPACES.dbf.

Use `--data-root <directory>` for another installation or **Choose catalog** /
`--catalog <file>` for an inspection override. The catalog filename is plural:
WORKSPACES.dbf. No duplicate workspace.dbf is created. `--private-session` keeps
the earlier isolated test environment; it does not run installation INI files.

To build, run its native tests, and launch:

```powershell
& D:\code\ccode\.venv312\Scripts\python.exe -B D:\code\ccode\gui\uidef\build_workbench.py --output-name arctictalk_workbench_m3 --launch
```

The Windows build uses installed Visual Studio 2022, CMake, Python and
`VCPKG_ROOT`. Packages live in `build/uidef-deps`, independently of the root
engine build's optional features. Add `--install-deps` on first build to install
wxWidgets, libsodium, LMDB, nlohmann-json and SQLite there; `--deps-dir` selects
an existing installation. The root CMake option is
`DOTTALK_BUILD_UIDEF_WORKBENCH=ON`. It reuses the CLI's source inventory and
libraries, including LMDB indexing. The smaller samples retain their standalone
build. The Workbench does not use `DOTTALK_WITH_WX` or replace APPGUI.

Add `--output-name arctictalk_workbench_catalogflow` to the build and verification
commands to build a separate executable while an earlier preview is running.
The currently running process keeps its own session and code until closed.

## Command loads and their views

Saved catalogs also offers **Hydrate to RAM...** for a selected MINIDB and
**Load definition...** for a selected DTSHEMA. Both use that exact saved version,
including a superseded one. The RAM dialog names the new workspace and offers
the current workspace as parent; the definition dialog names the current
destination and exposes table/index directories. Birth-only records cannot load.
See [catalog workflow and verification](../../docs/maintenance/AIF120_WORKBENCH_CATALOG_FLOW_V1.md).

After hydration, Live session shows the open tables and Database images contains
the inspected payload. RAM tables/indexes and disk memo sidecars are distinguished.
Definition loads reopen external files; create or SWITCH workspace first to change
their destination. Loads refuse pending table edits until Commit or Rollback.

The native menu bar provides **File, Workspace, Table, View, Tools, Help**.
Menus and buttons share the same host actions and engine session. Ctrl+N opens
New, Ctrl+O Open, Ctrl+L Load, Ctrl+S Save, Ctrl+R Run script, Ctrl+K the command input, and F1 help.

**New workspace**, **Open...**, **Load...**, **Save image...** and **Run script...** use generated
modal forms. Each shows its target, accepts Enter, and cancels with Escape,
Cancel or window close. New creates and enters a root workspace; New child
shows the selected parent. Invalid input stays in the form with an explanation.
Cancel submits no engine operation. A changed workspace or missing parent is
refused before acting on another target. Native errors appear in Engine response.

Open starts with the current DBF directory; Browse can choose another directory.
It invokes native `WORKSPACE OPEN dbf` using that directory for the operation,
then restores the native path default. Load chooses a `.dtschema`/`.dtschemas`
file starting at WORKSPACES and invokes native `WORKSPACE LOAD`.
The Load form also shows **Table directory** and **Index directory**, initialized
from DBF and INDEXES. They apply only to this load; each has its own Browse
button. Definitions with saved roots use those roots first. Older V1/V2
definitions often contain only filenames, so these directory choices matter.
The native preflight checks for every table before the modal accepts; missing
tables leave an explanation in the form so you can correct the directory.

For the existing `mcc.dtschema` CNX definition, use
`D:\code\ccode\dottalkpp\data\dbf\x32` and
`D:\code\ccode\dottalkpp\data\indexes\x32` (also the mcc.erz preset's setup).
For `help.dtschemas`, use `D:\code\ccode\dottalkpp\data\help` as the table
directory; that definition has no indexes. Choose the intended family explicitly
when a table exists in multiple locations. No recursive table search is used.
Both operate in the current workspace;
use SWITCH first when you want a different destination. Load keeps native
posture roots, cursor and index behavior. Posture roots locate tables for that
load; native LOAD leaves SET PATH settings unchanged. The worker rechecks before
loading; later native errors appear in Engine response. **Open table copy** remains a separate
action for copying a single table family. Tables shows one **Area** column with
the actual zero-based number used by SELECT. Internal stable identities stay
inside the selection checks; they are not displayed as area numbers.

Save writes a new `.minidb` file, with an explicit **Include nested workspaces**
option for this save. It preserves the session recursion default, refuses an
existing destination, and requires committed tables in the selected scope.
Dialog layout, buttons and menus are in the generated UIDEF document; directory
and file pickers are native host services. Modal forms currently have a wx
implementation; Tk, HTML and text renderers explicitly refuse them.

The M1 verification mode briefly opens real windows to check focus and keyboard
flow even without `--capture`. See the [M1 record](../../docs/maintenance/AIF120_WORKBENCH_M1_V1.md)
for evidence and limits.

**Run script...** (also Tools / Run script, Ctrl+R) starts in SET PATH SCRIPTS,
normally DATA/scripts, and filters for `.dts`. The form shows the current
workspace and full selected filename. Run sends that exact file to the native
DO/DOTSCRIPT runner; spaces and ampersands in the filename stay literal.
The engine response names the executed file. Script commands have their usual
effects, including any workspace switches written in the script.

File defaults are per kind, not a recursive search of DATA:

| Operation | Native default directory |
| --- | --- |
| DO / Run script (.dts) | SCRIPTS |
| Open table / directory (.dbf) | DBF |
| Load workspace definition (.dtschema, .dtschemas) | WORKSPACES |
| Open / save image (.minidb) | WORKSPACES |
| Default saved catalog (WORKSPACES.dbf) | WORKSPACES |

For top-level DO and WORKSPACE file LOAD/SAVE, a bare name uses its configured
slot; a qualified relative path such as `scripts/mcc/example.dts` starts at DATA;
an absolute path is exact. Missing files do not trigger a cwd, tests, or
user/public search. Subscripts use their calling script's directory, also
without fallback. WORKSPACE keeps its .dtschema-before-.dtschemas preference
within the one chosen directory. SCHEMAS remains the native table-schema
directory; it is not the workspace-definition directory.

Existing user/public directories can be chosen explicitly or assigned with
SET PATH; nothing is relocated. ERSATZ's separate user/public/default policy is
outside this follow-up. See the [file-location record](../../docs/maintenance/AIF120_WORKBENCH_FILEPATHS_V1.md).

`DO x64` followed by `WORKSPACE OPEN dbf` opens the directory's tables and brings
**Live session / Tables** forward. **Database images** displays inspected MINIDB
payloads. `WORKSPACE LOAD name MEMO RAM` also populates that page, including
nested DTX images, whether entered directly or run through a script. It retains
the inspected image when you switch tabs or refresh; its load-time table count
is historical. **View live tables** shows what is open now.

The image page offers **Choose saved image**, **Open image file**, and
**View live tables** even when no image is selected. Its empty state reports
the actual open-table count. Native loading retains its usual path, VDISK and
error behavior. Materialized bytes alone do not prove every table opened;
the image notification reports the actual newly opened table handles.

## Paths and defaults

**Paths and defaults** displays native slots and directory availability. Select
a slot and **Set selected path**, or type `SET PATH DBF dbf/x64`. Relative values
follow native DATA-root rules; DBF, INDEXES and LMDB bind the current workspace
and follow SWITCH. `SET PATH ... IN workspace` remains available at the prompt.
The directory editor refuses a value that could be mistaken for that IN clause.

**Reset paths** runs SET PATH RESET against the current DATA root and binds the
reset roots to the current workspace. **Run INIT** repeats native initialization
and the two INI scripts from the current BIN. Script commands have their usual
effects. Changes are session settings; these controls do not rewrite INI files.

Saved catalogs follows WORKSPACES/WORKSPACES.dbf when the slot changes. Choosing
or typing a catalog pins inspection to that file; **Use default catalog** resumes
following the slot. Inspection choices do not retarget native workspace writes.
Table pickers start in DBF and image pickers in WORKSPACES. Available scripts,
help, indexes and other locations come from the same native path state.

## Use

- The left list shows current saved records. **Include superseded records**
  adds retained history; deleted records remain excluded.
- Filter by name, format, or `#ID`. Indentation follows recorded `PARENT_ID`.
- **Workspace** shows durable identity, parent, previous saved version,
  recorded roots and depth fields. Parentage and version lineage are separate.
- **MINIDB contents** lists carried files, exact byte counts and whether the
  existing hydrator would place each in RAM or on disk as a memo sidecar.
- **Saved definition** shows the stored posture, limited to 1,000 lines.
- **Refresh** reads a new snapshot. A missing or invalid catalog clears the
  old view and reports the error.

Saved catalogs and the live session have separate identities. Equal numeric IDs
in two different catalogs do not identify the same workspace.

In **Live session**:

- The navigator is a tree of workspaces, child workspaces and their tables.
  Tables show their global zero-based area before the name. **[current]** marks
  the current workspace; **[selected]** marks the engine's selected table.
  A single click browses without changing either engine cursor. Enter or
  double-click runs SWITCH for a workspace or SELECT for a table. SELECT keeps
  the current workspace unchanged, and the table's owner remains visible.
  Arrow keys navigate/expand branches; Ctrl+F focuses search, Escape clears
  search, and F5 refreshes. Right-click offers the matching actions, New child,
  branch expansion and refresh. Closing tables is enabled only for the current
  workspace and uses the existing Include nested setting.
- Search matches workspace or table names, retaining ancestors. A matching
  workspace includes its descendants. Search and refresh retain the browsed
  identity and unfiltered expansion state; a hidden selection is restored when
  the filter clears. A closed table loses its selection and cannot receive
  actions, even if another table reuses its area number. New/SWITCH and loads
  follow their destination workspace. See the [M2 record](../../docs/maintenance/AIF120_WORKBENCH_M2_V1.md).
- **New workspace** creates a root through WORKSPACE NEW, including its durable
  birth row in the active WORKSPACES catalog, and makes it current. **New child**
  uses the selected parent and enters the new child.
  DEFAULT has no durable identity at startup; create a named parent first.
- **SWITCH workspace** changes the current workspace and selects its first open
  area (lowest global number). An empty workspace selects an unused area and
  shows no table open; NEW uses the same empty-workspace flow. If every area is
  occupied, entering an empty workspace is refused without moving either cursor.
  **SELECT area** selects a row in **Tables** without changing the workspace.
  These are separate states, shown together above the panes.
  Clicking a workspace browses its tables; double-clicking it runs SWITCH.
  The browser follows the current workspace after a typed SWITCH as well.
- **Tables** shows the highlighted workspace's open tables. **Include nested**
  adds its descendants; **All workspaces** shows the full desk. These view
  controls do not change the engine's save/close recursion setting. Search by
  table or workspace name, then double-click a row or choose **SELECT area**.
  The **Area** column gives the actual zero-based global number for `SELECT n`.
  SELECT retains the current workspace, including when selecting a peer's table.
  Internal area identities are not displayed. Filtering preserves a highlighted
  row by area identity; a hidden row cannot receive a selection action.
- The command box runs ordinary x64base commands and expressions through the
  same executor as the prompt: `SWITCH name`, `SELECT 4`, `SELECT students`,
  `SELECT other:students`, `LIST`, `COUNT`, `GO TOP`, `SKIP 1`, `DISPLAY`,
  `SET FILTER`, `SQLSEL`, `APPEND`, `REPLACE`, `DELETE`, `RECALL`, `COMMIT`,
  `ROLLBACK`, `WORKDESK`, `DOTSCRIPT`, and the rest of this build's registry.
  `SET VAR amount = 9` followed by `? &amount + 1` uses the normal macro path.
  Press Enter or **Run command**; Up/Down recalls command history.
  Read engine output and errors in **Engine response**. The status bar reports
  the measured registry size, which includes aliases and function commands.
- Commands operate on the selected area and chosen paths. **Open table copy**
  protects its source by copying; a typed `USE` opens the path you specify.
  Edits through commands are real. `TABLE ON` buffers changes until `COMMIT`
  or `ROLLBACK`; closing is refused while buffered edits remain.
- `QUIT`/`EXIT` close the Workbench through its normal shutdown. Terminal
  browsers (`BROWSER`, `BROWSETUI`, `RBROWSE`, `ERSATZ`,
  `SIMPLEBROWSER`, `SMARTBROWSER`), other in-process UI owners, `!`, `CLEAR`,
  and the blocking `BBS SERVE` require the terminal/separate frontend.
  These exceptions also apply inside macros and scripts. Commands that normally
  request console input receive end-of-input; use their explicit argument forms.
  Interactive multiline block capture is not exposed; run complete DOTSCRIPT files.
  Output is capped at 4 MiB and the grid at 5,000 lines, with a visible notice.
  Use narrower queries or the engine's `SET ALTERNATE` for larger reports.
- **Open table copy** copies a DBF and its memo sidecars, then uses WORKSPACE ADD
  with NOINDEX in the current workspace. The same table may be inspected in
  multiple workspaces; identities and area slots are shown in **Tables**.
- **Close current** closes that workspace's areas. The checkbox controls whether
  close also descends into children. Peer workspaces remain open; workspace
  identities remain after closing their areas.

In the live **Table** page:

- Type `BROWSE`, or select the Table page, to inspect the selected area. Pages
  contain up to 100 visible rows in the engine's display order. Top, Previous,
  Next and Refresh leave the engine's current record unchanged.
- The header shows table identity, record count, order, filter state and current
  record. The record column retains 64-bit record numbers. Deleted rows follow
  `SET DELETED`; row membership follows the same filter/order path as LIST.
- Select a row to inspect its fields. **Select record**, or double-clicking the
  row, runs GOTO on that record in the same live session.
- Double-click a field, or choose **Open value**, for a read-only value/memo
  window. Memo objects are read only when requested. Binary values appear in
  hexadecimal. Text previews show up to 64 KiB, binary previews 4 KiB; memo
  objects larger than 1 MiB are refused before loading.
- For a memo that carries a database, select its row and field, then choose
  **Inspect image**. The Database images page shows that MINIDB and its nested
  images, with the source table, record and field recorded. Choose an image and
  hydrate it into a new workspace, or under the current workspace. This also
  works when the source table is in RAM and its memo sidecar is on disk.
  Inspection leaves the table's current record and workspace selection alone.
  Commit or roll back changes to that memo first. Ordinary text, empty/deleted
  memo objects and stale selections report a reason instead of opening an image.
  Explicit image inspection allows up to 128 MiB; ordinary value previews keep
  their smaller limits. Nested inspection still uses the aggregate image budget.
- To put a database into a memo, select a row and memo field, then choose
  **Store image** and select a `.minidb` file. The file dialog names the target
  table, record and field. The image reference stays buffered until **Commit
  table**; **Rollback table** keeps the previous reference. Commit/Rollback
  still apply to all pending edits in that table. After committing, choose
  **Inspect image** to open the stored database and hydrate it as a workspace.
  This works with DTX memos using 16-byte tokens or fixed x64 references,
  including RAM tables with disk memo sidecars. The input file is unchanged.
- Store image validates the image and compares its memo readback byte-for-byte.
  It allocates a new object so other fields pointing to the previous object
  retain their contents. Rollback/failure can leave an unreferenced allocated
  object in the DTX; this action does not reclaim memo objects. The row reference
  is buffered, but allocation of the memo bytes happens immediately. Files are
  limited to 128 MiB. Pending edits to the selected memo, deleted/NULL records,
  unsupported memo layouts/backends, stale selections and active SQL transactions
  refuse with an explanation. The old reference is rechecked before storage;
  this is not a lock held across the file dialog or a crash-atomic DBF/DTX update.
- `TABLE ON` edits appear as buffered values before COMMIT. Commands refresh
  the view and reset it to the first page. Filtering and index membership use
  persisted engine values until commit; buffered cells are overlaid afterward.
- Select a row and field, then choose **Edit value**. Enter literal text and
  choose **Buffer value**. The engine validates the type and width, enables
  TABLE buffering if needed, and stages the change. Quotes, macros and command
  names entered here are stored as text. The current record stays unchanged.
- **Commit table** applies all buffered changes in the selected table.
  **Rollback table** discards all its buffered changes, including changes made
  in the command console. Other areas and workspaces retain their buffers.
  The Table header counts buffered records; closing still requires resolving
  pending edits. Read **Engine response** if a commit is refused or incomplete.
- The value editor supports ordinary character, numeric, logical, date and
  datetime fields. Primary keys, NULL, memo, binary and truncated previews
  remain inspect-only in the scalar editor. Use Store image for MINIDB memos
  and commands for other memo/NULL operations. Edits and
  native Commit/Rollback refuse an active SQL transaction; finish it through
  the command console first. The original field value is rechecked when
  staging; this is not a lock held across the editing dialog.

Each page scans at most 100,000 ordered entries, including skipped rows; a
limit notice means the view is incomplete. Use a narrower filter or order scope.
The engine streams natural/CNX/LMDB-CDX traversal; INX/ISX/CSX fallback can still
materialize an index vector. These are Workbench preview limits, not engine
capacity limits. BROWSE arguments for terminal editing are not supported by
this host; `BROWSE USAGE` explains its native behavior.

In **Database images**:

- Choose **Export selected image** to write that image's exact bytes to a new
  `.minidb` file. A selected child exports as its own database, without its
  surrounding carrier. This works for images inspected from catalogs, files
  and live memo fields. The export preserves nested contents inside the chosen
  image, leaves the live workspace and buffered edits alone, and never replaces
  an existing file. **Last export** and **Export folder** show the destination;
  its full path is also in the details tooltip and Engine response.
- Export copies the inspected snapshot. Changes made later to its source are
  included only after inspecting that source again. Export checks the MINIDB
  structure, compares the written bytes and syncs the file; hydration performs
  the separate table/path admission checks. A write/readback/sync failure can
  leave private staging data or a partial destination and is reported explicitly.
- **Open image file** reads a standalone `.minidb` file for inspection. Choose
  **Hydrate in new workspace** to reopen its tables in this session, or hydrate
  an individual nested image. File paths with spaces are supported.
- Select a MINIDB record in Saved catalogs and choose **Inspect image**.
  The image tree follows live MINIDB objects in carried DTX memo files. It excludes
  tombstones and ordinary text. Live objects are not a claim of DBF row reachability.
- Select the root or a nested image and choose **Hydrate in new workspace**.
  **Hydrate under current workspace** creates an explicit child of the current
  live workspace; that parent must have a durable identity.
- Hydration uses VDISK MOUNT and WORKSPACE LOAD MEMO RAM inside this process.
  The imported image gets a new identity and payload in the active WORKSPACES catalog. Foreign
  saved IDs are provenance only. Every materialized member is read back against
  the input bytes before success is reported.
- The Live session then shows the new current workspace, its source location,
  RAM and disk byte counts, private mount, and open tables marked `[RAM]`.
  DBF/index members reside in memory; DTX/DBT/FPT memo sidecars reside on disk.
- Close releases areas, while image RAM files remain until exit. Exit closes all
  areas and releases only this session's mounts. Disk copies remain for review.

In **Live session**, choose **Save image** to write the current workspace's
committed tables, attached memos and active indexes into a new `.minidb` file.
The checkbox controls whether child workspace tables are included. Peer
workspaces are excluded, even when SELECT has selected a peer table. Resolve
buffered changes in the scope being saved first. Active SQL transactions also
refuse saving. Choose a new filename each time; existing files are not replaced.
The engine writes a snapshot into the private catalog, verifies the exported
bytes, and syncs the image file before reporting success. A failed export can
leave a private snapshot or partial destination; inspect Engine response.

Use **Open image file** on a later launch to inspect and hydrate the saved
image. Restoring creates fresh identities. The image carries its table posture,
not the original ownership tree: included child tables reopen together in one
workspace. It does not resume the entire Workbench, command history or buffers.
Concurrent external writes are not captured as a transactional snapshot.

Copied tables and imported RAM mounts/memo sidecars use the temporary path shown in **Workspace**. Native commands use the selected paths; normal workspace births use the active WORKSPACES catalog.
Each launch creates a fresh session. Save an image somewhere durable before
closing if you want to keep RAM tables. Copies are limited to 256 MiB per table family. Table edits and
file operations are exposed through commands. This build includes the normal
LMDB index support; Open table copy starts with indexes detached (`NOINDEX`).

Image admission is limited to 128 MiB per payload and 128 MiB of resident RAM
across the session. Nested inspection is bounded to 8 levels, 128 images and
128 MiB aggregate payload bytes; FPT/DBT nested expansion is not implemented.
Partial inspection and limit failures are reported. Member paths must stay under
their mount and posture table/index paths must name members carried in the image.
Unsafe manifests are refused before writing. An I/O or table-opening failure can
leave a birth row in the active catalog and private disk residue; its new areas and RAM are released,
and the previous current workspace and selected area are restored.

The catalog family is copied to private temporary files before engine readers
open it. This matters because the DTX backend writes its header on close.
Within this catalog inspector, only owned copies are opened by write-capable
engine APIs and removed after inspection. File size and modification-time checks detect changes while
copying; this is not a transactional snapshot across concurrent writers.
Current inspection limits are 64 MiB for the catalog, 256 MiB for its memo file,
and 128 MiB of loaded payload previews. These are inspector limits, not engine
capacity claims.

## Verify

```powershell
& D:\code\ccode\.venv312\Scripts\python.exe -B D:\code\ccode\gui\uidef\verify_workbench.py
```

Add `--capture <path.png>` for a brief visible window and a screenshot. The
verifier uses fresh result files, checks process completion and native test
markers, exercises live commands and closing during a read, and compares input hashes. A black
capture is a failure, not visual evidence.
Capture also writes sibling `-live.png`, `-browse.png`, `-edit.png`, `-save.png`,
`-image.png`, `-nested.png`, `-memo-image.png`, `-export.png`, `-store.png`
and `-navigation.png`, `-paths.png`, `-loadview.png`, `-openload.png` images. Verification
hydrates every MINIDB found in the chosen catalog, including nested live DTX
images, exclusively into private session storage.

The source and local evidence are uncommitted. The existing handwritten wx
Workbench, Python samples, and APPGUI launcher are preserved. This executable
is separate so it can be reviewed before launcher integration.

The table and memo views share the live command session and also inspect hydrated
RAM tables. Scalar value editing shares the engine's table buffer. Portable
images preserve working data; complete workspace-tree session restoration
remains future work.

Owner direction for the next workflow pass: task-focused modal New/Open/Load/Save
dialogs showing the destination workspace, validation and Apply/Cancel. A native
cross-platform menu bar remains planned alongside common-action buttons and the
command box. These additions are not implemented by the current slice.
