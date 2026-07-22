// @dottalk.usage v1
// owner: DOT|BUILDVECTORS
// command: BUILDVECTORS
// aliases: BUILD VECTORS, BUILD INFO
// category: diagnostics
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: BUILDVECTORS
// summary:
//   Report the compiled engine capacity "build vectors" (AIF-044) — the selected
//   maximums this binary was configured with, plus a fingerprint.
//
// usage:
//   BUILDVECTORS
//   BUILD VECTORS
//   BUILD INFO
//
// notes:
//   Read-only. Values come from the generated build-vector authority
//   (config/build_vectors.cmake -> dottalk::build::*). The fingerprint distinguishes
//   two binaries built with different capacities.
//
// risk:
//   mutates_table_data: no
//
// related:
//   ABOUT
//   VERSION
//

#include "xbase.hpp"
#include "cli/build_vectors_report.hpp"

#include <iostream>
#include <sstream>

void cmd_BUILDVECTORS(xbase::DbArea&, std::istringstream&)
{
    dottalk::build::print_build_vectors(std::cout);
}
