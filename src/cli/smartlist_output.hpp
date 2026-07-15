#pragma once

#include "xbase.hpp"
#include "cli/table_object.hpp"

namespace cli::smartlist {

int recno_width(const xbase::DbArea& a);

void print_header(const xbase::DbArea& a, int recw);
void print_row(const xbase::DbArea& a, int recw);

// Buffer-aware SMARTLIST row printer.
// The schema/widths still come from DbArea, but values come from table::Row
// so TABLE BUFFER overlays are visible without changing the DBF reader.
void print_row(const xbase::DbArea& schema_area,
               const dottalk::table::Row& row,
               int recw,
               bool physical_deleted = false);

void print_footer(bool all, int limit, int printed);

} // namespace cli::smartlist
