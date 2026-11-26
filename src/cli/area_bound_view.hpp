// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: AreaBoundView
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: supported

// ==============================
// File: src/cli/area_bound_view.hpp
// ==============================
//
// R146 -- A SCHEMA PANEL IS BOUND TO THE AREA, AND AN AREA CAN CHANGE UNDER IT.
//
// Anything derived FROM the area rather than FROM the row -- a logical schema,
// a JSON sidecar -- is bound to the AREA and must be re-derived when the area
// changes. A browser that navigates between areas and does not re-derive is not
// STALE, it is WRONG: it labels one table's rows with another table's structure.
//
// WHY THIS IS A TYPE AND NOT TWO LINES INSIDE THE PAGER. Two reasons, and the
// second is the load-bearing one.
//
//   (1) The pager is interactive, and under a script SMARTBROWSER paints the
//       first page and exits on the failed getline -- measured and written down
//       in dottalkpp/data/scripts/buffer_visibility_probe_v3_smartbrowser.dts.
//       So NO .dts IN THIS TREE CAN REACH `OPEN CHILD`, and no script can
//       exercise this rule or its failure. An inlined comparison would be
//       ungradeable, which is the INDEX_X64 v2 shape the suite reported as PASS.
//       Extracted, it is a ctest: src/tests/test_area_bound_view.cpp.
//
//   (2) The rule is about WHEN TO RE-DERIVE, not about what a schema is. So the
//       payloads are template parameters and this header includes nothing from
//       the schema lane -- which is also what lets the test instantiate it with
//       plain strings and assert on counts rather than on field lists.
//
// THE SIGNAL IS AN AREA CHANGE, NOT A CURSOR MOVE, and the distinction is the
// point of R146. A cursor move inside one area leaves the derivation CORRECT;
// the fields do not change because you skipped ten records. Note that the
// pager's own `nav_event` is NOT the right test either: it means "the stream
// moved" and is set by TOP, SKIP, FOR and ORDER as well as by the three
// commands that change area. The area NAME is the exact test, and it costs one
// string compare against a next_page().
//
// xbase::cursor_hook is deliberately NOT used here. It carries the DbArea, but
// its own header says it is "Called by DbArea movement/edit methods" and it has
// no reason-code meaning "the view changed area" -- so a listener would learn
// about an area change only as a side effect of the new area's cursor moving,
// and would still need this same comparison. The hook keeps a rendered ROW
// current. That is a different job.

#pragma once

#include <cstddef>
#include <functional>
#include <string>
#include <utility>

namespace dottalk {

// Holds one area's derived views and re-derives them when, and only when, the
// area name changes. Construct with the two resolvers; call sync() once per
// paint with the stream's current area name; read schema()/sidecar().
//
// derivations() is the graded observable: it must advance on a real area change
// and must NOT advance on a repaint of the same area.
template <class Schema, class Sidecar>
class AreaBoundView {
public:
    using SchemaResolverFn  = std::function<Schema(const std::string&)>;
    using SidecarResolverFn = std::function<Sidecar(const std::string&)>;

    AreaBoundView(SchemaResolverFn resolve_schema, SidecarResolverFn resolve_sidecar)
        : resolve_schema_(std::move(resolve_schema)),
          resolve_sidecar_(std::move(resolve_sidecar)) {}

    // Idempotent for a given area name. The FIRST call always derives, even for
    // an empty name: an unopened stream must show the resolver's own answer for
    // "nothing", not a default-constructed payload nobody produced.
    void sync(const std::string& area_name)
    {
        if (primed_ && area_name == area_)
            return;
        area_    = area_name;
        schema_  = resolve_schema_(area_);
        sidecar_ = resolve_sidecar_(area_);
        primed_  = true;
        ++derivations_;
    }

    const Schema&      schema()  const noexcept { return schema_;  }
    const Sidecar&     sidecar() const noexcept { return sidecar_; }
    const std::string& area()    const noexcept { return area_;    }

    // True once sync() has run. A caller that prints before any sync is a bug
    // this makes visible rather than papering over with a default payload.
    bool primed() const noexcept { return primed_; }

    // Count of derivations performed. Exists for the test; a release build that
    // never reads it pays one size_t.
    std::size_t derivations() const noexcept { return derivations_; }

private:
    SchemaResolverFn  resolve_schema_;
    SidecarResolverFn resolve_sidecar_;

    std::string area_;
    Schema      schema_{};
    Sidecar     sidecar_{};
    bool        primed_{false};
    std::size_t derivations_{0};
};

} // namespace dottalk
