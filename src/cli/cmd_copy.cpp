// src/cli/cmd_copy.cpp
// @dottalk.usage v1
// owner: DOT|COPY
// command: COPY
// category: file-table
// status: supported
// noargs: usage
// effect: copy-or-convert
// mutates: filesystem
// usage-access: COPY USAGE
// summary:
//   Copy the current DBF, convert the current table to a target DBF flavor, or
//   copy a filesystem file.
//
// usage:
//   COPY USAGE
//   COPY TO <DBFNAME> [WITH SIDECARS] [OVERWRITE]
//   COPY TO <DBFNAME> AS <MSDOS|DBASE|FOX26|FOXPRO|VFP|X64> [OVERWRITE]
//   COPY TO <DBFNAME> AS X64 VECTOR [OVERWRITE]
//   COPY FILE <SRC> TO <DST> [OVERWRITE]
//
// examples:
//   COPY TO students_copy
//   COPY TO students_x64 AS X64 VECTOR OVERWRITE
//   COPY TO students_vfp AS VFP
//   COPY TO students_backup WITH SIDECARS OVERWRITE
//   COPY FILE source.txt TO tmp\source_copy.txt OVERWRITE
//
// notes:
//   COPY USAGE prints usage and does not require an open table.
//   COPY TO requires an open table.
//   COPY FILE does not require an open table.
//   WITH SIDECARS applies only to binary COPY TO.
//   OVERWRITE is required when the destination already exists.
//
// risk:
//   writes_filesystem: yes
//   overwrites_files: OVERWRITE
//   reads_current_table: COPY TO
//   mutates_table_data: no
//
// related:
//   USE
//   EXPORT
//   PACK
//
#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <algorithm>
#include <cctype>
#include <system_error>
#include <cstdint>

#include "xbase.hpp"
#include "xbase_64.hpp"
#include "xbase/dbf_create.hpp"
#include "xbase/field_name_policy.hpp"
#include "textio.hpp"

using namespace xbase;
using Flavor = xbase::dbf_create::Flavor;
using FieldSpec = xbase::dbf_create::FieldSpec;

namespace {

static inline std::string up(std::string s)   { return textio::up(std::move(s)); }
static inline std::string trim(std::string s) { return textio::trim(std::move(s)); }

static bool token_is(const std::string& t, const char* u) { return up(t) == u; }

static inline std::string lower_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c){ return static_cast<char>(std::tolower(c)); });
    return s;
}

static void usage_copy() {
    std::cout
        << "Usage:\n"
        << "  COPY USAGE\n"
        << "  COPY TO <DBFNAME> [WITH SIDECARS] [OVERWRITE]\n"
        << "  COPY TO <DBFNAME> AS <MSDOS|DBASE|FOX26|FOXPRO|VFP|X64> [OVERWRITE]\n"
        << "  COPY TO <DBFNAME> AS X64 VECTOR [OVERWRITE]\n"
        << "  COPY FILE <SRC> TO <DST> [OVERWRITE]\n"
        << "\n"
        << "Examples:\n"
        << "  COPY TO students_copy\n"
        << "  COPY TO students_x64 AS X64 VECTOR OVERWRITE\n"
        << "  COPY TO students_vfp AS VFP\n"
        << "  COPY TO students_backup WITH SIDECARS OVERWRITE\n"
        << "  COPY FILE source.txt TO tmp\\source_copy.txt OVERWRITE\n"
        << "\n"
        << "Notes:\n"
        << "  - COPY USAGE prints usage and does not require an open table.\n"
        << "  - COPY TO <name>                 : binary copy of the current DBF\n"
        << "  - COPY TO <name> AS <flavor>     : logical table copy/conversion\n"
        << "  - COPY TO <name> AS X64 VECTOR   : one-step copy from any open table to x64 vector form\n"
        << "  - VECTOR is target-driven and is valid only with AS X64\n"
        << "  - AS X64 controls output format only; the destination path is honored\n"
        << "  - AS VFP/FOX/MSDOS writes free-table 10-byte descriptor field names\n"
        << "  - COPY AS free-table fails if 10-byte descriptor names would collide\n"
        << "  - WITH SIDECARS applies to binary COPY TO only\n"
        << "  - OVERWRITE is required when the destination already exists\n"
        << "  - x64 output still writes .dbf for now (no .dbfx yet)\n"
        << "\n"
        << "SIDECARS (if present next to the DBF): .inx .cnx .dtx .dti.json\n";
}

static bool copy_file_binary(const std::filesystem::path& src,
                             const std::filesystem::path& dst,
                             bool overwrite,
                             std::string* err = nullptr) {
    std::error_code ec;

    if (!std::filesystem::exists(src, ec) || ec) {
        if (err) *err = "Source does not exist: " + src.string();
        return false;
    }

    if (std::filesystem::exists(dst, ec) && !overwrite) {
        if (err) *err = "Destination exists (use OVERWRITE): " + dst.string();
        return false;
    }

    if (dst.has_parent_path() && !dst.parent_path().empty()) {
        std::filesystem::create_directories(dst.parent_path(), ec);
        ec.clear();
    }

    const auto opt = overwrite ? std::filesystem::copy_options::overwrite_existing
                               : std::filesystem::copy_options::none;

    if (!std::filesystem::copy_file(src, dst, opt, ec) || ec) {
        if (err) *err = "Copy failed: " + src.string() + " -> " + dst.string();
        return false;
    }

    return true;
}

static std::filesystem::path ensure_dbf_path(const std::filesystem::path& p) {
    // Intentionally stays .dbf for all flavors for now.
    return std::filesystem::path(xbase::dbNameWithExt(p.string()));
}

static bool dst_token_has_explicit_dir(const std::filesystem::path& dstp) {
    return dstp.has_parent_path() &&
           !dstp.parent_path().empty() &&
           dstp.parent_path().string() != ".";
}

static std::filesystem::path resolve_dst_for_copy_to(const DbArea& a, const std::string& dstToken) {
    // Binary COPY behavior: if dstToken includes a directory, honor it;
    // otherwise write next to the open DBF.
    std::filesystem::path dstp(trim(dstToken));
    const std::filesystem::path srcp(a.filename());

    std::filesystem::path leaf = dstp.filename();
    leaf = ensure_dbf_path(leaf);

    if (dst_token_has_explicit_dir(dstp)) return dstp.parent_path() / leaf;
    return srcp.parent_path() / leaf;
}

static std::filesystem::path resolve_dst_for_logical_copy_to(const DbArea& a,
                                                             const std::string& dstToken) {
    // Logical COPY AS changes the destination table format only.  It must not
    // silently redirect the destination to an x64/vfp/etc. profile directory.
    // A bare name follows the established COPY behavior and is written beside
    // the currently open source DBF.  An explicit relative or absolute path is
    // honored exactly as the user supplied it.
    std::filesystem::path dstp(trim(dstToken));
    const std::filesystem::path srcp(a.filename());

    std::filesystem::path leaf = dstp.filename();
    leaf = ensure_dbf_path(leaf);

    if (dst_token_has_explicit_dir(dstp)) return dstp.parent_path() / leaf;
    return srcp.parent_path() / leaf;
}

static bool exists_file(const std::filesystem::path& p) {
    std::error_code ec;
    return std::filesystem::exists(p, ec) && !ec;
}

static void copy_sidecars(const std::filesystem::path& src_dbf,
                          const std::filesystem::path& dst_dbf,
                          bool overwrite) {
    const auto src_dir  = src_dbf.parent_path();
    const auto dst_dir  = dst_dbf.parent_path();
    const auto src_stem = src_dbf.stem().string();
    const auto dst_stem = dst_dbf.stem().string();

    struct SidecarSpec { const char* suffix; };
    const SidecarSpec specs[] = {
        { ".inx" },
        { ".cnx" },
        { ".dtx" },
        { ".dti.json" },
    };

    int found = 0;
    int copied = 0;
    int failed = 0;

    for (const auto& s : specs) {
        const std::filesystem::path src_side = src_dir / (src_stem + s.suffix);
        if (!exists_file(src_side)) continue;
        ++found;

        const std::filesystem::path dst_side = dst_dir / (dst_stem + s.suffix);

        std::string err;
        if (copy_file_binary(src_side, dst_side, overwrite, &err)) {
            ++copied;
        } else {
            ++failed;
            std::cout << "COPY SIDECAR failed: " << err << "\n";
        }
    }

    if (found == 0) {
        std::cout << "COPY SIDECARS: none found.\n";
    } else {
        std::cout << "COPY SIDECARS: found " << found << ", copied " << copied;
        if (failed) std::cout << ", failed " << failed;
        std::cout << ".\n";
    }
}

static bool same_path(const std::filesystem::path& a,
                      const std::filesystem::path& b) {
    std::error_code ec1, ec2;
    const auto ca = std::filesystem::weakly_canonical(a, ec1);
    const auto cb = std::filesystem::weakly_canonical(b, ec2);

#if defined(_WIN32)
    auto sa = (ec1 ? std::filesystem::absolute(a).string() : ca.string());
    auto sb = (ec2 ? std::filesystem::absolute(b).string() : cb.string());
    std::transform(sa.begin(), sa.end(), sa.begin(),
        [](unsigned char c){ return static_cast<char>(std::tolower(c)); });
    std::transform(sb.begin(), sb.end(), sb.begin(),
        [](unsigned char c){ return static_cast<char>(std::tolower(c)); });
    return sa == sb;
#else
    return (ec1 ? std::filesystem::absolute(a) : ca) ==
           (ec2 ? std::filesystem::absolute(b) : cb);
#endif
}

static bool parse_flavor_token(const std::string& tok, Flavor& out) {
    const std::string u = up(trim(tok));

    if (u == "MSDOS" || u == "DBASE") {
        out = Flavor::MSDOS;
        return true;
    }
    if (u == "FOX26" || u == "FOXPRO26" || u == "FOXPRO") {
        out = Flavor::FOX26;
        return true;
    }
    if (u == "VFP") {
        out = Flavor::VFP;
        return true;
    }
    if (u == "X64") {
        out = Flavor::X64;
        return true;
    }
    return false;
}

static std::string flavor_name_local(Flavor f) {
    return xbase::dbf_create::flavor_name(f);
}


struct CopyVectorOptions {
    bool vector_requested = false;
};

static constexpr std::size_t FREE_TABLE_FIELD_TOKEN_BYTES = 10;

static std::string free_table_descriptor_token(const std::string& name) {
    if (name.size() <= FREE_TABLE_FIELD_TOKEN_BYTES) return name;
    return name.substr(0, FREE_TABLE_FIELD_TOKEN_BYTES);
}

static std::string field_token_key(std::string s) {
    s = trim(std::move(s));
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool is_free_table_target(Flavor flavor) noexcept {
    return flavor == Flavor::MSDOS ||
           flavor == Flavor::FOX26 ||
           flavor == Flavor::VFP;
}

static bool apply_free_table_name_policy(Flavor flavor,
                                         std::vector<FieldSpec>& specs,
                                         std::vector<std::string>& warnings,
                                         std::string& err) {
    if (!is_free_table_target(flavor)) return true;

    struct SeenName {
        std::string key;
        std::string original;
        std::string token;
        std::size_t index = 0;
    };

    std::vector<SeenName> seen;

    for (std::size_t i = 0; i < specs.size(); ++i) {
        const std::string original = specs[i].name;
        const std::string token = free_table_descriptor_token(original);
        const std::string key = field_token_key(token);

        if (original.size() > FREE_TABLE_FIELD_TOKEN_BYTES) {
            warnings.push_back(
                "COPY TO AS " + flavor_name_local(flavor) +
                " WARNING: field name '" + original +
                "' exceeds free-table descriptor length 10; stored descriptor name will be '" +
                token + "'.");
        }

        for (const auto& s : seen) {
            if (s.key == key) {
                err = "COPY TO AS " + flavor_name_local(flavor) +
                      ": field name collision after 10-byte descriptor mapping: '" +
                      original + "' and earlier field '" + s.original +
                      "' both map to '" + token +
                      "'. Target free tables have no x64 metadata authority; "
                      "copy AS X64 VECTOR or rename fields first.";
                return false;
            }
        }

        specs[i].name = token;
        seen.push_back(SeenName{key, original, token, i});
    }

    return true;
}

static void apply_x64_descriptor_name_policy(Flavor flavor,
                                             std::vector<FieldSpec>& specs,
                                             std::vector<std::string>& warnings) {
    if (flavor != Flavor::X64) return;

    std::vector<std::string> names;
    names.reserve(specs.size());
    for (const auto& s : specs) names.push_back(s.name);

    const auto plans = xbase::field_name_policy::plan_x64_unique_fallback(names);

    for (std::size_t i = 0; i < specs.size(); ++i) {
        specs[i].descriptor_name = plans[i].descriptor_name;

        const bool metadata_fits = xbase::x64_field_name_fits(plans[i].logical_name.size());

        if (!metadata_fits) {
            std::string msg =
                "COPY TO AS X64 WARNING: field name '" + plans[i].logical_name +
                "' exceeds current x64 logical field-name length " +
                std::to_string(xbase::X64_FIELD_NAME_LENGTH) +
                "; it will not be stored as an authoritative x64 metadata name; "
                "descriptor fallback token is '" + plans[i].descriptor_name + "'";

            if (plans[i].mangled) {
                msg += "; token was mangled to avoid a fallback collision";
            }
            if (plans[i].sanitized) {
                msg += "; token was normalized for DBF descriptor safety";
            }
            msg += ".";
            warnings.push_back(std::move(msg));
            continue;
        }

        if (plans[i].truncated || plans[i].mangled || plans[i].sanitized) {
            std::string msg =
                "COPY TO AS X64 WARNING: field name '" + plans[i].logical_name +
                "' uses DBF/VFP descriptor fallback token '" +
                plans[i].descriptor_name +
                "'; authoritative x64 metadata name is preserved";

            if (plans[i].mangled) {
                msg += "; token was mangled to avoid a fallback collision";
            }
            if (plans[i].sanitized) {
                msg += "; token was normalized for DBF descriptor safety";
            }
            msg += ".";
            warnings.push_back(std::move(msg));
        }
    }
}

static bool parse_copy_vector_options(const std::vector<std::string>& tok,
                                      size_t start,
                                      Flavor flavor,
                                      CopyVectorOptions& out,
                                      std::string& err) {
    out = CopyVectorOptions{};

    for (size_t i = start; i < tok.size(); ++i) {
        const std::string u = up(trim(tok[i]));

        if (u == "VECTOR") {
            if (out.vector_requested) {
                err = "COPY TO AS: duplicate VECTOR option.";
                return false;
            }
            out.vector_requested = true;
            continue;
        }

        if (u == "FIELDNAMES" || u == "FIELDNAME" || u == "FIELDS" ||
            u == "TABLENAME" || u == "TABLENAMES" || u == "TABLE") {
            err = "COPY TO AS: explicit vector length parameters are not implemented yet; "
                  "use AS X64 VECTOR to apply the current x64 vector policy.";
            return false;
        }

        err = "COPY TO AS: unexpected option after target flavor: '" + tok[i] + "'.";
        return false;
    }

    if (out.vector_requested && flavor != Flavor::X64) {
        err = "COPY TO AS: VECTOR is valid only with target flavor X64.";
        return false;
    }

    return true;
}

static bool build_field_specs_from_area(const DbArea& src,
                                        Flavor flavor,
                                        std::vector<FieldSpec>& out,
                                        std::vector<std::string>& warnings,
                                        std::string& err) {
    out.clear();
    warnings.clear();
    for (const auto& fd : src.fields()) {
        const char T = static_cast<char>(std::toupper(static_cast<unsigned char>(fd.type)));

        if (!xbase::dbf_create::supports_type_now(T, flavor)) {
            err = "COPY TO AS: field type '" + std::string(1, T) +
                  "' is not implemented for target flavor " + flavor_name_local(flavor) + ".";
            return false;
        }

        FieldSpec fs;
        fs.name = fd.name;
        fs.type = T;
        fs.dec  = fd.decimals;
        fs.len  = fd.length;

        // Preserve CREATE semantics for memo width.
        if (T == 'M') {
            fs.len = (flavor == Flavor::X64) ? 8 : 10;
            fs.dec = 0;
        }

        out.push_back(fs);
    }

    if (out.empty()) {
        err = "COPY TO AS: source table has no fields.";
        return false;
    }

    apply_x64_descriptor_name_policy(flavor, out, warnings);

    if (!apply_free_table_name_policy(flavor, out, warnings, err)) {
        return false;
    }

    return true;
}

static void remove_conversion_artifacts(const std::filesystem::path& dst_dbf) {
    std::error_code ec;
    const auto dir  = dst_dbf.parent_path();
    const auto stem = dst_dbf.stem().string();

    const std::filesystem::path files[] = {
        dst_dbf,
        dir / (stem + ".inx"),
        dir / (stem + ".cnx"),
        dir / (stem + ".cdx"),
        dir / (stem + ".cdx.meta"),
        dir / (stem + ".dtx"),
        dir / (stem + ".dbt"),
        dir / (stem + ".fpt"),
        dir / (stem + ".dti.json"),
    };

    for (const auto& p : files) {
        std::filesystem::remove(p, ec);
        ec.clear();
    }

    const auto cdx_env = dir / (stem + ".cdx.d");
    std::filesystem::remove_all(cdx_env, ec);
}

static bool logical_copy_to_as(const DbArea& src,
                               const std::filesystem::path& dstp,
                               Flavor flavor,
                               bool overwrite,
                               const CopyVectorOptions& vector_opts,
                               std::string& err) {
    if (!src.isOpen()) {
        err = "COPY TO AS: no file open.";
        return false;
    }

    if (vector_opts.vector_requested && flavor != Flavor::X64) {
        err = "COPY TO AS: VECTOR is valid only with target flavor X64.";
        return false;
    }

    const std::filesystem::path srcp(src.filename());
    if (srcp.empty()) {
        err = "COPY TO AS: source filename unavailable.";
        return false;
    }

    if (same_path(srcp, dstp)) {
        err = "COPY TO AS: source and destination are the same file.";
        return false;
    }

    std::vector<FieldSpec> specs;
    std::vector<std::string> name_warnings;
    if (!build_field_specs_from_area(src, flavor, specs, name_warnings, err)) {
        return false;
    }

    for (const auto& w : name_warnings) {
        std::cout << w << "\n";
    }

    std::error_code ec;
    if (std::filesystem::exists(dstp, ec) && !overwrite) {
        err = "Destination exists (use OVERWRITE): " + dstp.string();
        return false;
    }

    if (dstp.has_parent_path() && !dstp.parent_path().empty()) {
        std::filesystem::create_directories(dstp.parent_path(), ec);
        ec.clear();
    }

    if (overwrite) {
        remove_conversion_artifacts(dstp);
    }

    if (!xbase::dbf_create::create_dbf(dstp.string(), specs, flavor, err)) {
        return false;
    }

    DbArea dst;
    try {
        dst.open(dstp.string());
    } catch (const std::exception& ex) {
        err = "Target created but reopen failed: " + std::string(ex.what());
        return false;
    } catch (...) {
        err = "Target created but reopen failed.";
        return false;
    }

    const int32_t total = src.recCount();

    for (int32_t rn = 1; rn <= total; ++rn) {
        DbArea& s = const_cast<DbArea&>(src); // source navigation/read APIs are non-const
        if (!s.gotoRec(rn) || !s.readCurrent()) {
            err = "COPY TO AS: failed reading source record " + std::to_string(rn);
            return false;
        }

        if (!dst.appendBlank()) {
            err = "COPY TO AS: appendBlank failed at target record " + std::to_string(rn);
            return false;
        }

        for (int i = 1; i <= s.fieldCount(); ++i) {
            if (!dst.set(i, s.get(i))) {
                err = "COPY TO AS: failed setting field " + std::to_string(i) +
                      " at source record " + std::to_string(rn);
                return false;
            }
        }

        if (!dst.writeCurrent()) {
            err = "COPY TO AS: writeCurrent failed at target record " + std::to_string(rn);
            return false;
        }

        if (s.isDeleted()) {
            // Best-effort preserve deleted state.
            if (!dst.deleteCurrent()) {
                err = "COPY TO AS: failed preserving deleted state at record " +
                      std::to_string(rn);
                return false;
            }
        }
    }

    return true;
}

} // namespace

void cmd_COPY(DbArea& a, std::istringstream& iss) {
    std::vector<std::string> tok;
    {
        std::string t;
        while (iss >> t) tok.push_back(t);
    }

    if (tok.empty()) { usage_copy(); return; }
    if (token_is(tok[0], "USAGE") || token_is(tok[0], "HELP") || token_is(tok[0], "?")) {
        usage_copy();
        return;
    }

    bool overwrite = false;
    bool with_sidecars = false;

    // Strip OVERWRITE, WITH, SIDECARS tokens (flexibly)
    {
        std::vector<std::string> kept;
        kept.reserve(tok.size());

        for (size_t i = 0; i < tok.size(); ++i) {
            const std::string u = up(tok[i]);

            if (u == "OVERWRITE") { overwrite = true; continue; }

            if (u == "WITH") {
                if (i + 1 < tok.size() && up(tok[i + 1]) == "SIDECARS") {
                    with_sidecars = true;
                    ++i;
                    continue;
                }
                continue;
            }

            if (u == "SIDECARS") { with_sidecars = true; continue; }

            kept.push_back(tok[i]);
        }

        tok.swap(kept);
    }

    if (tok.empty()) { usage_copy(); return; }

    // COPY FILE <src> TO <dst>
    if (token_is(tok[0], "FILE")) {
        if (tok.size() < 4 || !token_is(tok[2], "TO")) { usage_copy(); return; }

        const std::filesystem::path src = trim(tok[1]);
        const std::filesystem::path dst = trim(tok[3]);

        std::string err;
        if (copy_file_binary(src, dst, overwrite, &err)) {
            std::cout << "Copied file to " << dst.string() << "\n";
        } else {
            std::cout << "COPY FILE failed: " << err << "\n";
        }
        return;
    }

    // COPY TO <dbf> [AS <flavor>]
    if (token_is(tok[0], "TO")) {
        if (!a.isOpen()) {
            std::cout << "COPY TO: no file open.\n";
            return;
        }
        if (tok.size() < 2) {
            usage_copy();
            return;
        }

        const std::filesystem::path srcp(a.filename());

        // Logical conversion branch: COPY TO <name> AS <flavor>
        size_t as_pos = tok.size();
        for (size_t i = 2; i < tok.size(); ++i) {
            if (token_is(tok[i], "AS")) {
                as_pos = i;
                break;
            }
        }

        if (as_pos != tok.size()) {
            if (as_pos != 2) {
                std::cout << "COPY TO AS failed: unexpected token between destination and AS: '"
                          << tok[2] << "'\n";
                std::cout << "Use: COPY TO <destination> AS <flavor> [VECTOR] [OVERWRITE]\n";
                return;
            }
            if (as_pos + 1 >= tok.size()) {
                usage_copy();
                return;
            }

            Flavor flavor = Flavor::MSDOS;
            if (!parse_flavor_token(tok[as_pos + 1], flavor)) {
                std::cout << "COPY TO AS failed: unknown flavor '" << tok[as_pos + 1] << "'\n";
                return;
            }

            CopyVectorOptions vector_opts;
            std::string option_err;
            if (!parse_copy_vector_options(tok, as_pos + 2, flavor, vector_opts, option_err)) {
                std::cout << option_err << "\n";
                return;
            }

            const std::filesystem::path dstp = resolve_dst_for_logical_copy_to(a, tok[1]);

            if (with_sidecars) {
                std::cout << "COPY TO AS: WITH SIDECARS ignored for logical conversion.\n";
            }

            if (vector_opts.vector_requested) {
                std::cout << "COPY TO AS X64 VECTOR: using current x64 vector metadata policy.\n";
            }

            std::string err;
            if (!logical_copy_to_as(a, dstp, flavor, overwrite, vector_opts, err)) {
                std::cout << "COPY TO AS failed: " << err << "\n";
                return;
            }

            std::cout << "Copied table to " << dstp.string()
                      << " [" << flavor_name_local(flavor) << "]";
            if (vector_opts.vector_requested) std::cout << " VECTOR";
            std::cout << "\n";
            return;
        }

        // Existing binary copy behavior
        const std::filesystem::path dstp = resolve_dst_for_copy_to(a, tok[1]);

        std::string err;
        if (!copy_file_binary(srcp, dstp, overwrite, &err)) {
            std::cout << "COPY TO failed: " << err << "\n";
            return;
        }

        std::cout << "Copied DBF to " << dstp.string() << "\n";

        if (with_sidecars) {
            copy_sidecars(srcp, dstp, overwrite);
        }

        return;
    }

    usage_copy();
}