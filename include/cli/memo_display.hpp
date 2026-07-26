// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <string>

namespace xbase { class DbArea; }

namespace cli_memo
{
    std::string resolve_display_value(xbase::DbArea& area,
                                      int field1,
                                      const std::string& raw_value);
}