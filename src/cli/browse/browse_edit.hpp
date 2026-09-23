// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
#include <map>
#include <string>

namespace xbase { class DbArea; }

namespace dottalk::browse::edit {

using StageMap = std::map<int, std::string>;

int field_index_by_name(::xbase::DbArea& db, const std::string& name);
void list_fields(::xbase::DbArea& db);

// THE ONE EDITOR COMMIT DOOR (AIF-156, 2026-09-23). Every staged field is
// presented to xbase::cli::gateFieldWrites() BEFORE one byte moves, so a
// refusal (today: a write to a declared PRIMARY key) abandons the whole edit
// and leaves no partial row -- the cmd_replace_multi / hierarchy_service
// shape. Any browser or editor that stages field edits commits through here
// and inherits the funnel without writing its own; the two simple field-test
// editors are the historical examples. On refusal `err` (if given) names the
// refused field and the staged map is KEPT, so the caller can report and let
// the operator amend or cancel.
bool commit_staged(::xbase::DbArea& db, StageMap& staged,
                   std::string* err = nullptr);
void discard_staged(StageMap& staged);

} // namespace dottalk::browse::edit
