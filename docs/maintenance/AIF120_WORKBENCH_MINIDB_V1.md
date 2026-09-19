# AIF-120 Workbench: MINIDB hydration and nested inspection

Status: implemented and locally verified on Windows; source and evidence are
uncommitted. Registry evidence remains source_defined until versioned.
Owner authorization: continue the commissioned Workbench; dogfood x64base using
SWITCH and SELECT. Run: CODEX-20260917-UIDEF-MINIDB.

## Source mutation preflight

Targets: gui/uidef session/catalog services, new image service and native test,
generated document author, wx adapter, standalone CMake, build/verification and
guide; include/dottalk/minidb_hydrate.hpp and, if required by malformed-length
tests, minidb.hpp; this report and owned registry/evidence fragments.
Subsystem: generated frontend plus shared container admission (C3).

Expected behavior: inspect live MINIDB objects in carried DTX sidecars; hydrate a
selected image into a private live workspace through existing WORKSPACE MEMO RAM
loading. Durable identity belongs to the private session catalog. Sources remain
read-only. No writeback or editing UI in this slice.

The shared materializer currently joins member names without containment checks.
Before exposing hydration, validate all destination paths and ranges before any
write, reject duplicate destinations and unsafe paths, and check stream failures.
Reuse the existing scanner, DTX reader, RAM filesystem and command lifecycle.
Do not substitute a second engine or a frontend hydration implementation.

Proof: malformed/traversing/absolute/duplicate members leave the mount unchanged;
real command hydration of a generated MINIDB; nested DTX-contained MINIDB readback;
correct RAM versus real memo placement; additive loads with independent identities;
expected areas and records; close/shutdown; actual catalog input hashes unchanged;
native generated-window smoke and image capture. Existing samples are preserved.

Authorities: canonical Tier 1 seed, x64base skill, GUI/threading/database/UIDEF
contracts read for prior slices, minidb.hpp/minidb_hydrate.hpp/ramfs.hpp,
WORKSPACE implementation, and RAM_MINIDB_MEMO_WORKSPACE_OPERATIONS_V1.md.
The operations manual predates additive loads; runtime source governs this work.

## Delivered behavior

The UIDEF author now produces 70 rows / 69 widgets. Saved catalogs has an
Inspect image action; Database images shows the root and MINIDB objects found
inside carried DTX sidecars. The existing MemoStore live-object API excludes
tombstones. Ordinary memo text is skipped. This is object discovery, not proof
that each object is referenced by a DBF row.

Hydrate creates a named root or explicit child workspace through WORKSPACE NEW,
attaches the selected bytes to its canonical birth row in the private session
catalog, then uses VDISK MOUNT and WORKSPACE LOAD <name> MEMO RAM. All of this
runs on the same joined engine worker as the live session. No subprocess owns
the hydrated RAM and no second workspace allocator or loader was introduced.

Each load has a unique private mount. Foreign catalog IDs remain provenance;
private workspace IDs are allocated by the existing command. The session's
private BIN slot owns vdisk.ini, so an unrelated launch directory cannot redirect
the mount. Admission checks carried posture paths, free area capacity and the
128 MiB resident RAM budget before creating the workspace.

Success requires actual open areas and byte-for-byte readback of every carried
member, not the void command's output. DBF/index members use ramfs; DTX/DBT/FPT
sidecars use physical files. A failed load closes only the new workspace's areas,
releases its RAM, and restores the prior current workspace, selected area and
path slots. A private birth row and disk residue can remain for review.

Open table copy temporarily supplies its private DBF root to WORKSPACE ADD, then
restores the live roots. This fixes a real integration hazard after hydration
changes the current workspace's roots. Close retains image RAM until exit;
shutdown closes areas first, then erases and unmounts only owned RAM roots.

The shared materializer now plans the complete destination manifest before
writing. It rejects traversal, absolute/drive/stream paths, reserved Windows
devices, malformed components, case-folded duplicate destinations and out-of-range
payload spans. Canonical destinations must remain under the supplied roots.
Non-memo files require mounted destinations; stream failures are checked.
The scanner parses full unsigned lengths and uses subtraction bounds to avoid
overflow. This is admission before writes, not transactional rollback of disk
I/O failures, and it is not a defense against a concurrent hostile filesystem
replacement after the check.

## Measured verification

- Three native test executables passed. Tests cover unsafe manifests before any
  write, malformed/overflowing lengths, live/deleted/ordinary nested DTX objects,
  explicit child workspaces, additive repeated loads, source/member readback,
  RAM/disk placement, copy-after-hydration, failed DBF recovery, recursive close,
  owned mount teardown, cancellation, and existing SWITCH/SELECT behavior.
- The real WORKSPACES catalog has 134 retained records, 148 excluded deleted
  records, seven scanned MINIDBs and no payload errors. All seven hydrated into
  97 simultaneously open tables in independent private workspaces. No nested
  MINIDB objects were found in that catalog's carried DTX files.
- Nested behavior was therefore proved using a generated native DBF/DTX fixture:
  one live child image, one deleted child image and ordinary memo text. Native
  traversal found exactly root plus live child. The generated window selected
  the child and hydrated its two-record STUDENTS table.
- Generated window checks passed for saved catalog, live session, actual-image
  hydration, nested-image selection/hydration, and close during a read. The new
  Database images page and the loaded live workspace were visually inspected.
- Original catalog DBF and DTX SHA-256 values stayed unchanged. The exact hashes,
  tested executable hash, counts, UI markers and private session paths are in
  evidence/AIF120_workbench_minidb_20260917.txt. Review images are the
  evidence/AIF120_workbench_20260917_v3*.png family.
- Source diff whitespace and new-content ASCII checks passed. cmd_area.cpp has
  no diff. SELECT remains the command for numbered or named areas.

Build recovery: wxWidgets disappeared from the shared build/vcpkg_installed
installation during work (its package status became not-installed). Required
packages were restored from the existing vcpkg binary cache into build/uidef-deps.
build_workbench.py now uses that isolated directory, supports --install-deps and
--deps-dir, and refreshes stale wxWidgets/WX_ library hints. The root engine's
package installation was not modified by the recovery. The existing preview
held the executable open; the user closed it before the successful relink.

## Limits and next work

Windows native was tested; Linux/macOS were not. Nested inspection is bounded
to 8 levels, 128 images and 128 MiB aggregate payload bytes. FPT/DBT nested
expansion is reported as unsupported. Hydration has a 128 MiB per-image limit and
128 MiB total resident RAM budget. Limits are host policy, not engine capacities.

No index attachment, table editing or writeback UI is exposed. Carried indexes
are materialized, with command limitations visible in Engine response. Detailed
relation/index semantics across every stored posture were not independently
proved. Private catalogs and disk sidecars survive exit for review, but resuming
a retained session is not implemented. The next useful slice is read-only table
and memo browsing, then an explicit edit/writeback workflow.

## Housekeeping and handoff

The full measured dirty-path and retained-session inventory is
evidence/AIF120_workbench_housekeeping_20260917.txt. It separates this Workbench's
owned paths (including prior slices) from untouched shared work. Shared authors
were not inferred. Among those untouched files are PROMOTION_CHECKLIST.md,
PSEUDO_CHAT_BOARD.md, the AIF-136 retention plan, other maintenance/manual reports,
and existing untracked trees. No broad cleanup or staging was performed.

The tree remains development. HEAD advanced independently from the run baseline
6123842098f8e4d9cc3f8010865709cce899730f to
b63606ec113edca7b7fc2986074b390cfb645817 (launcher work); that commit has no
changes under src, include or gui/uidef. This work made no git mutation.

Build/generated residue is confined to build/uidef-workbench and build/uidef-deps,
plus the package tool's existing cache and private temporary session directories
listed in the inventory. Successful fixture tests remove their source DBFs/DTX.
The private session catalogs and disk memo copies are intentionally retained.
Windows SDK build and visible-window verification used approved elevated tool
runs; those are not a portable clean-clone dependency. A clean clone needs the
toolchain and the documented --install-deps step. No environment-only product
configuration is required beyond the existing VCPKG_ROOT tool locator.

No staging, commit, push, promotion, publication, APPGUI replacement, or lane
closure was performed. Existing handwritten and Python samples remain available.

RE: AIF-120 and runtime container owners -- for maintainer transcription

WHAT_CHANGED: gui/uidef generated Workbench image inspection/hydration, tests,
build helper and guide; shared include/dottalk/minidb.hpp length validation and
minidb_hydrate.hpp destination admission; owned registry and evidence fragments.

WHOSE_AREA: AIF-120 generated frontend and shared MINIDB hydration; owner
member.derald, steward member.ai.claude.cowork.

AUTHORIZATION: Owner commissioned the Workbench, requested continued development
and extensive x64base dogfooding, and specified SWITCH plus SELECT semantics.

VERIFY_OR_UNDO: From D:\code\ccode run
.venv312\Scripts\python.exe -B gui\uidef\build_workbench.py, then
.venv312\Scripts\python.exe -B gui\uidef\verify_workbench.py.
Undo only the named third-slice additions and exact owned hunks; retain prior
Workbench slices and unrelated dirty work. No reset or whole-tree revert.
