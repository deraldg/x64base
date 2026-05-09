// ============================================================================
// File: src/help/helpdata_artifacts.hpp
// Purpose: Artifact helpers for HELP DATA v2.
// ============================================================================
#pragma once

#include "helpdata_model.hpp"
#include "helpdata_messages.hpp"

#include <vector>

namespace dottalk::helpdata {

Owner owner_from_string(const std::string& text);
ArtifactKind artifact_kind_from_category(const std::string& category);
Severity severity_from_string(const std::string& severity);

Artifact artifact_from_message(const MessageDef& message);
std::vector<Artifact> artifacts_from_standard_messages();

} // namespace dottalk::helpdata
