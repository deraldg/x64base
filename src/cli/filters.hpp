// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/filters.hpp
#pragma once
#include <optional>
#include <string>
namespace xbase { class DbArea; }

namespace filters {
    struct Simple {
        std::string field;
        std::string value;
        bool active = false;
    };
    // set/clear for an area
    void set(xbase::DbArea& area, std::optional<Simple> f);
    // read current area filter (if any)
    std::optional<Simple> get(const xbase::DbArea& area);
}


