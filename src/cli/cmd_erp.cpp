// @dottalk.usage v1
// owner: DOT|ERP_IMPL
// command: ERP
// category: integration-helper
// status: implementation-shim
// noargs: n/a
// effect: none
// mutates: none
// usage-access: not-registered-here
// summary:
//   Translation-unit shim for ERP/LabTalk integration includes.
//
// usage:
//   This file currently does not export a command handler.
//   If ERP becomes user-facing from this file, add the runtime command handler and full usage contract together.
//
// notes:
//   Keep ERP application behavior owned by the ERP/LabTalk application layer.
//
// risk:
//   mutates_table_data: no
//

// Interface to exercise ERP DEV using cmd_erp.cpp/.hpp pair
// use app_erp.* for initial LabTalk main.

#include "labtalk/lab_labtalk.hpp"
#include "erp/erp_erp.hpp"





