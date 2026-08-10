// @dottalk.file v1
// subsystem: selfdoc
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: AIF-050
// owner: member.derald
// status: supported

// event_record.hpp — runtime -> documentation intake seam (M5).
//
// Writes a proof/run transcript for a runtime event (an agent connection, an egress toggle) so it
// can be promoted into labtalk/proofs/runs/ + proofs.yaml + ai_runs.yaml by the SelfDoc/MDO tooling.
// Runtime writes to the DATA slot (never into the source tree); promotion to labtalk/proofs is a
// maintainer/tooling step (documented in the M5 package). Best-effort; never throws.
#pragma once

#include <string>
#include <vector>

namespace dottalk::selfdoc {

// Writes data/metadata/bbs/proofs/<YYYYMMDD_HHMMSS>_<kind>_<slug>.txt.
// kind: "runtime" | "probe" | "regression" (matches labtalk/proofs/runs naming).
// Returns the written path, or "" on failure. Does not throw.
std::string record_event(const std::string& kind,
                         const std::string& slug,
                         const std::string& actor,
                         const std::string& summary,
                         const std::vector<std::string>& lines);

} // namespace dottalk::selfdoc
