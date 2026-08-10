// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
#include <optional>
#include <string>

struct ScanOptions {
    enum class DeleteMode { SkipDeleted, IncludeDeleted, OnlyDeleted };
    DeleteMode del_mode = DeleteMode::SkipDeleted;

    std::optional<std::string> for_expr;    // FOR <expr>
    std::optional<std::string> while_expr;  // WHILE <expr>

    enum class Range { AllFromCurrent, NextN, RecordN, Rest };
    Range range = Range::AllFromCurrent;
    int   n = 0; // for NEXT/RECORD

    std::string usageVerb;
};



