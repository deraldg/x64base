// @dottalk.file v1
// subsystem: gui
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
// @dottalk.contract v1
// family: selfdoc.api_contract
// component: gui_runtime_adapter
// role: immutable GUI model projection from runtime-owned table state
// owner: DotTalk++ GUI open-architecture lane
// contract: Runtime adapters may project DbArea state into GUI models, but they must not redefine database semantics or take ownership of engine truth.
// authority: xbase/memo/xindex/xexpr and dottalkpp runtime remain authoritative; adapters are translation seams only.
// gui: frontends should render AreaInfo/TableSnapshot results rather than reading mutable runtime state directly from widgets.
// @dottalk.contract.end

#include "gui/core/model.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace xbase {
class DbArea;
}

namespace dottalk::gui {

/// Which workspace owns this area.
///
/// ONE overload, and it takes the AREA. The engine stamps _ws_handle at open(),
/// so an area in hand knows its workspace in O(1), exactly, with no lookup and
/// no assumption about what an AreaId means.
///
/// There was an AreaId overload beside this one until AIF-078 (2026-08-23). It
/// returned the constant DEFAULT for every input, which is the same answer for
/// "DEFAULT" and for "I cannot tell". Its single caller had the DbArea
/// available one frame earlier, so the answer now travels in OpenTableResult
/// and the stub was deleted rather than kept as a seam nothing was using.
/// gui_runtime_adapter.cpp records why unifying AreaId did not make it
/// writable after all.
std::string gui_workspace_of_area(const xbase::DbArea& area);

AreaInfo gui_area_info_from_dbarea(AreaId area_id,
                                   bool active,
                                   const xbase::DbArea& area,
                                   const std::string& display_name);

TableSnapshot gui_snapshot_from_dbarea(AreaId area_id,
                                       xbase::DbArea& area,
                                       const std::string& display_name,
                                       std::uint64_t first_record,
                                       std::uint32_t max_records);


// ---- AIF-120: the memo read path -------------------------------------------
//
// Read-only projection of the WORKSPACES catalog and its memo sidecar. This is
// what lets the GUI show what is inside a memo field without hydrating it.
//
// STRICTLY READ-ONLY. The CLI's open_catalog() calls ensure_catalog(), which
// CREATES the catalog when absent; that is right for a SAVE and wrong for a
// browser. These functions open what exists and report when it does not.
//
// The catalog location is not re-derived here: it is
// paths::Slot::WORKSPACES / "WORKSPACES.dbf", the same slot and filename
// cmd_workspace.cpp's WORKSPACE_root() and catalog_path() use.

struct MemoWorkspaceRow {
    std::uint64_t ws_id      = 0;
    std::string   name;          // WS_NAME
    std::string   fmt;           // "MINIDB 1", "DTSHEMA 3", ...
    std::string   snapshot;      // memo token; the handle for gui_read_memo_payload
    std::uint64_t size_b     = 0;
    std::uint64_t est_hyd_b  = 0;   // blank in the catalog reads back as 0
    std::string   saved_at;
    std::string   author;
    bool          superseded = false;
};

/// Every row of the catalog, newest last. Empty with `error` set when the
/// catalog is absent or unreadable; empty with `error` clear means no rows.
std::vector<MemoWorkspaceRow> gui_list_memo_workspaces(std::string& error);

/// The raw payload bytes behind a SNAPSHOT token. Binary-safe: a MINIDB
/// container carries table images containing every byte value.
std::string gui_read_memo_payload(const std::string& snapshot_token,
                                  std::string& error);

} // namespace dottalk::gui
