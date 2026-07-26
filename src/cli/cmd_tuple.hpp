// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
#include <sstream>
#include "xbase.hpp"

// TUPLE <spec>
// Examples:
//   TUPLE *                           (all fields from current area)
//   TUPLE #11.*                       (all fields from slot 11)
//   TUPLE LNAME,FNAME,#11.DEPT_ID     (fields from current and slot 11)
//   TUPLE #9.*,#11.LNAME,#11.FNAME
//
// Writes one line to stdout with fields separated by ASCII Unit Separator (0x1F).
void cmd_TUPLE(xbase::DbArea& A, std::istringstream& args);



