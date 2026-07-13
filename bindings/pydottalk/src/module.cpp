#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cctype>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

namespace py = pybind11;
namespace fs = std::filesystem;

// =============================================================
// CRITICAL INCLUDE ORDER (MSVC)
// -------------------------------------------------------------
// xbase.hpp forward-declares xindex::IndexManager, but DbArea has
// unique_ptr<IndexManager> AND defaulted move ops inline:
//   DbArea(DbArea&&) = default;
//   DbArea& operator=(DbArea&&) = default;
//
// MSVC will require IndexManager COMPLETE in any TU that parses
// those inline definitions (pybind11 tends to trigger this).
//
// Therefore: include the header that DEFINES xindex::IndexManager
// BEFORE including xbase.hpp.
// =============================================================

#if defined(HAVE_XBASE)
  // Try common locations first. If your project uses a different header name,
  // add it here (or see the findstr command below).
  #if __has_include("xindex/index_manager.hpp")
    #include "xindex/index_manager.hpp"
  #elif __has_include("xindex/index_manager.h")
    #include "xindex/index_manager.h"
  #elif __has_include("xindex/IndexManager.hpp")
    #include "xindex/IndexManager.hpp"
  #elif __has_include("xindex/IndexManager.h")
    #include "xindex/IndexManager.h"
  #elif __has_include("xindex.hpp")
    #include "xindex.hpp"
  #else
    #error "pydottalk: cannot find a header that DEFINES xindex::IndexManager. Add the correct include above."
  #endif

  #include "xbase.hpp"
  #include "xbase_64.hpp"
  #include "xbase_field_getters.hpp"
  #include "memo/memo_auto.hpp"
  #include "memo/memostore.hpp"
#endif

static std::string pydottalk_version()
{
    return "pydottalk 0.4.0";
}

static std::string ping(const std::string& name)
{
    return "hello, " + name;
}

static std::vector<std::string> list_dbf(const std::string& dir)
{
    std::vector<std::string> out;
    fs::path base = fs::u8path(dir);
    if (!fs::exists(base) || !fs::is_directory(base)) return out;

    for (auto& e : fs::directory_iterator(base)) {
        if (!e.is_regular_file()) continue;
        auto ext = e.path().extension().string();
        for (auto& c : ext) c = static_cast<char>(::tolower(static_cast<unsigned char>(c)));
        if (ext == ".dbf") out.push_back(e.path().string());
    }
    return out;
}

#if defined(HAVE_XBASE)
static std::string resolve_abs_path(const std::string& path)
{
    fs::path p = fs::u8path(path);
    return fs::absolute(p).lexically_normal().string();
}

static py::list fields_as_dict_list(const xbase::DbArea& A)
{
    py::list out;
    const auto& defs = A.fields();
    for (const auto& f : defs) {
        py::dict d;
        d["name"]     = f.name;
        d["type"]     = std::string(1, f.type);
        d["length"]   = static_cast<int>(f.length);
        d["decimals"] = static_cast<int>(f.decimals);
        out.append(d);
    }
    return out;
}

static bool area_has_memo_fields(const xbase::DbArea& area)
{
    for (const auto& f : area.fields()) {
        if (f.type == 'M' || f.type == 'm') {
            return true;
        }
    }
    return false;
}

static void pydottalk_open_with_memo(xbase::DbArea& area, const std::string& abs_path)
{
    area.open(abs_path);

    std::string err;
    if (!cli_memo::memo_auto_on_use(area, abs_path, area_has_memo_fields(area), err)) {
        area.close();
        throw std::runtime_error("memo_auto_on_use failed: " + err);
    }
}

static void pydottalk_close_with_memo(xbase::DbArea& area)
{
    cli_memo::memo_auto_on_close(area);
    area.close();
}

static bool is_x64_memo_field(const xbase::DbArea& area, int field1)
{
    if (field1 < 1 || field1 > area.fieldCount()) return false;
    if (area.versionByte() != xbase::DBF_VERSION_64) return false;

    const auto& f = area.fields()[static_cast<std::size_t>(field1 - 1)];
    return (f.type == 'M' || f.type == 'm') &&
           f.length == xbase::X64_MEMO_FIELD_LEN;
}

static std::uint64_t parse_u64_or_zero(const std::string& s)
{
    if (s.empty()) return 0;
    try {
        std::size_t used = 0;
        const unsigned long long v = std::stoull(s, &used, 10);
        if (used != s.size()) return 0;
        return static_cast<std::uint64_t>(v);
    } catch (...) {
        return 0;
    }
}

static dottalk::memo::MemoStore* memo_store_for_area(xbase::DbArea& area) noexcept
{
    auto* backend = cli_memo::memo_backend_for(area);
    if (!backend) return nullptr;
    return dynamic_cast<dottalk::memo::MemoStore*>(backend);
}

static std::string get_logical_field_text(xbase::DbArea& area, int field1)
{
    if (field1 <= 0) return {};

    if (!is_x64_memo_field(area, field1)) {
        return xfg::rtrim_copy(area.get(field1));
    }

    const std::uint64_t oid = parse_u64_or_zero(area.get(field1));
    if (!oid) return {};

    auto* store = memo_store_for_area(area);
    if (!store) return {};

    std::string txt;
    if (!store->get_text_id(oid, txt, nullptr)) return {};
    return txt;
}

static py::dict read_record_dict(xbase::DbArea& area)
{
    if (!area.readCurrent()) {
        throw std::runtime_error("readCurrent failed");
    }

    py::dict out;
    const auto& defs = area.fields();
    for (std::size_t i = 0; i < defs.size(); ++i) {
        const int field1 = static_cast<int>(i) + 1;
        out[py::str(defs[i].name)] = get_logical_field_text(area, field1);
    }
    return out;
}

static py::list scan_records_list(xbase::DbArea& area, bool skip_deleted)
{
    py::list rows;
    if (!area.top()) {
        return rows;
    }

    for (;;) {
        if (!skip_deleted || !area.isDeleted()) {
            rows.append(read_record_dict(area));
        }

        if (area.eof()) {
            break;
        }
        if (!area.skip(1)) {
            break;
        }
    }

    return rows;
}
#endif

PYBIND11_MODULE(pydottalk, m)
{
    m.doc() = "DotTalk++ Python bindings (canonical: xbase::DbArea).";

    m.def("version", &pydottalk_version);
    m.def("ping", &ping, py::arg("name") = "world");
    m.def("list_dbf", &list_dbf, py::arg("directory"));

#if !defined(HAVE_XBASE)
    m.attr("HAVE_XBASE") = py::bool_(false);
    return;
#else
    m.attr("HAVE_XBASE") = py::bool_(true);

    py::module_ mx = m.def_submodule("xbase", "xbase engine bindings (DbArea is canonical).");

    py::enum_<xbase::DbArea::MemoKind>(mx, "MemoKind")
        .value("NONE", xbase::DbArea::MemoKind::NONE)
        .value("FPT",  xbase::DbArea::MemoKind::FPT)
        .value("DBT",  xbase::DbArea::MemoKind::DBT)
        .export_values();

    py::class_<xbase::DbArea>(mx, "DbArea")
        .def(py::init<>())

        // lifecycle
        .def("open", [](xbase::DbArea& self, const std::string& path) {
            pydottalk_open_with_memo(self, resolve_abs_path(path));
        }, py::arg("path"))
        .def("close", [](xbase::DbArea& self) {
            pydottalk_close_with_memo(self);
        })
        .def("isOpen", &xbase::DbArea::isOpen)
        .def("is_open", &xbase::DbArea::isOpen)

        // deleted flag
        .def("isDeleted", &xbase::DbArea::isDeleted)
        .def("is_deleted", &xbase::DbArea::isDeleted)

        // navigation
        .def("gotoRec", &xbase::DbArea::gotoRec, py::arg("recno"))
        .def("goto_rec", &xbase::DbArea::gotoRec, py::arg("recno"))
        .def("top", &xbase::DbArea::top)
        .def("bottom", &xbase::DbArea::bottom)
        .def("skip", &xbase::DbArea::skip, py::arg("delta"))

        // record I/O
        .def("readCurrent", &xbase::DbArea::readCurrent)
        .def("read_current", &xbase::DbArea::readCurrent)
        .def("writeCurrent", &xbase::DbArea::writeCurrent)
        .def("write_current", &xbase::DbArea::writeCurrent)
        .def("appendBlank", &xbase::DbArea::appendBlank)
        .def("append_blank", &xbase::DbArea::appendBlank)
        .def("deleteCurrent", &xbase::DbArea::deleteCurrent)
        .def("delete_current", &xbase::DbArea::deleteCurrent)

        // schema/fields
        .def("fields", [](const xbase::DbArea& self) { return fields_as_dict_list(self); })
        .def("fieldCount", &xbase::DbArea::fieldCount)
        .def("field_count", &xbase::DbArea::fieldCount)
        .def("get", &xbase::DbArea::get, py::arg("idx1"))
        .def("set", &xbase::DbArea::set, py::arg("idx1"), py::arg("value"))
        .def("get_field", [](xbase::DbArea& self, const std::string& name) {
            const int idx0 = xfg::resolve_field_index_std(self, name);
            if (idx0 < 0) {
                throw py::key_error("field not found: " + name);
            }
            return get_logical_field_text(self, idx0 + 1);
        }, py::arg("name"))
        .def("set_field", [](xbase::DbArea& self, const std::string& name, const std::string& value) {
            const int idx0 = xfg::resolve_field_index_std(self, name);
            if (idx0 < 0) {
                throw py::key_error("field not found: " + name);
            }
            if (!self.set(idx0 + 1, value)) {
                throw std::runtime_error("set_field failed for: " + name);
            }
        }, py::arg("name"), py::arg("value"))
        .def("get_memo_text", [](xbase::DbArea& self, const std::string& name) -> py::object {
            const int idx0 = xfg::resolve_field_index_std(self, name);
            if (idx0 < 0) {
                throw py::key_error("field not found: " + name);
            }
            const int field1 = idx0 + 1;
            const auto& f = self.fields()[static_cast<std::size_t>(idx0)];
            if (f.type != 'M' && f.type != 'm') {
                throw std::runtime_error("field is not memo type: " + name);
            }
            const std::string text = get_logical_field_text(self, field1);
            if (text.empty() && self.get(field1).empty()) {
                return py::none();
            }
            return py::str(text);
        }, py::arg("name"))
        .def("read_record", &read_record_dict)
        .def("scan_records", &scan_records_list,
             py::arg("skip_deleted") = true)

        // info
        .def("recno", &xbase::DbArea::recno)
        .def("recCount", &xbase::DbArea::recCount)
        .def("rec_count", &xbase::DbArea::recCount)
        .def("bof", &xbase::DbArea::bof)
        .def("eof", &xbase::DbArea::eof)
        .def("recLength", &xbase::DbArea::recLength)
        .def("rec_length", &xbase::DbArea::recLength)
        .def("recordLength", &xbase::DbArea::recordLength)
        .def("cpr", &xbase::DbArea::cpr)

        // canonical identity
        .def("filename", &xbase::DbArea::filename)
        .def("dbfDir", &xbase::DbArea::dbfDir)
        .def("dbf_dir", &xbase::DbArea::dbfDir)
        .def("dbfBasename", &xbase::DbArea::dbfBasename)
        .def("dbf_basename", &xbase::DbArea::dbfBasename)
        .def("logicalName", &xbase::DbArea::logicalName)
        .def("logical_name", &xbase::DbArea::logicalName)
        .def("name", &xbase::DbArea::name)

        // memo facts
        .def("memoPath", &xbase::DbArea::memoPath)
        .def("memo_path", &xbase::DbArea::memoPath)
        .def("memoKind", &xbase::DbArea::memoKind)
        .def("memo_kind", &xbase::DbArea::memoKind)

        // x64 introspection
        .def("version_byte", &xbase::DbArea::versionByte)
        .def("table_flags", &xbase::DbArea::tableFlags)
        .def("area_kind", &xbase::DbArea::kind);

    // convenience alias
    m.attr("Dbf") = mx.attr("DbArea");
#endif
}
