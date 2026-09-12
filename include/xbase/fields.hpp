// @dottalk.file v1
// subsystem: xbase
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include "xbase.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace fields {

enum class Op {
    None = 0,
    Show,
    Append,
    DeleteField,
    ModifyName,
    ModifyType,
    ModifyTo,
    CopyTo,
    CopyToMap,
    Validate,
    Check,
    RebuildIndexes
};

enum class Status {
    Ok = 0,
    InvalidArgument,
    InvalidState,
    Unsupported,
    NotImplemented,
    Failed
};

enum class IndexImpact {
    None = 0,
    Unknown,
    RebuildRecommended,
    RebuildRequired,
    Blocked
};

struct Result {
    Status      status{Status::Ok};
    IndexImpact indexImpact{IndexImpact::None};
    bool        changed{false};
    bool        rebuildSuggested{false};
    std::string message;
};

struct FieldProtectionInfo {
    bool isIndexed{false};
    bool isUnique{false};
    bool isPrimaryKey{false};
};

struct AppendOptions {
    // NOT IMPLEMENTED. Declared here and READ NOWHERE -- measured 2026-08-31
    // across src/ and include/: the only occurrences are this line and the
    // caller in cmd_fieldmgr.cpp that sets it to false. Setting it true today
    // changes nothing, which is worse than the option not existing, because a
    // caller reasonably reads it as a working switch.
    //
    // AND IT CANNOT SIMPLY BE TURNED ON HERE. fields::append lives in
    // src/xbase; rebuilding a CDX is xindex + the CLI's BUILDLMDB path, which
    // is a HIGHER layer. xbase must keep standing alone -- the standalone
    // pydottalk build compiles it with DOTTALK_INDEX_MODE=NONE and no xindex
    // target at all. So a rebuild belongs to the caller, and this option
    // should either grow a callback the caller supplies or be retired.
    // Left in place rather than deleted because retiring a public struct
    // member is a decision, not a tidy-up.
    bool rebuildIndexesIfPossible{false};

    // IMPLEMENTED (fields_mgr.cpp, appendField). Refuses the append outright
    // when an index is attached. Off by default.
    bool failIfIndexesPresent{false};
};

struct CopyMapEntry {
    int         srcIndex{-1};
    int         dstIndex{-1};
    std::string dstName;
};

struct CopyPlan {
    std::vector<CopyMapEntry> entries;
};

std::string usage();
std::string opName(Op op);

bool parseFieldSpec(const std::string& text, xbase::FieldDef& out, std::string& err);
bool validateFieldName(const std::string& name, std::string& err);
bool validateFieldDef(const xbase::FieldDef& fd, std::string& err);

int  findFieldCI(const xbase::DbArea& db, const std::string& name);
bool hasFieldCI(const xbase::DbArea& db, const std::string& name);

FieldProtectionInfo getFieldProtectionInfo(const xbase::DbArea& db,
                                           const std::string& fieldName);

Result show(const xbase::DbArea& db);

Result append(xbase::DbArea& db,
              const xbase::FieldDef& fd,
              const AppendOptions& opts = {});

Result deleteField(xbase::DbArea& db, const std::string& fieldName);
Result modifyName(xbase::DbArea& db,
                  const std::string& oldName,
                  const std::string& newName);
Result modifyType(xbase::DbArea& db,
                  const std::string& fieldName,
                  const xbase::FieldDef& newDef);
Result modifyTo(xbase::DbArea& db,
                const std::string& oldName,
                const xbase::FieldDef& newDef);

Result copyTo(xbase::DbArea& db, const std::string& targetPath);
Result copyToMap(xbase::DbArea& db,
                 const std::string& targetPath,
                 const CopyPlan& plan);

Result validate(const xbase::DbArea& db);
Result check(const xbase::DbArea& db);
Result rebuildIndexes(xbase::DbArea& db);

IndexImpact assessAppendIndexImpact(const xbase::DbArea& db,
                                    const xbase::FieldDef& fd);

} // namespace fields
