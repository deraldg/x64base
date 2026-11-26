// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

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
//   COPY TO <DBFNAME> AS <MSDOS|DBASE|FOX26|FOXPRO|VFP|X64> [KEY DROP] [OVERWRITE]
//   COPY TO <DBFNAME> AS X64 VECTOR [KEY DROP] [OVERWRITE]
//   COPY FILE <SRC> TO <DST> [OVERWRITE]
//   COPY TABLE TO <WS> [WITH INDEXES] [OVERWRITE]
//   COPY TABLE FROM <WS> [WITH INDEXES] [OVERWRITE]
//   COPY TABLE <STEM> TO <WS> [WITH INDEXES] [OVERWRITE]
//   COPY TABLE <STEM> FROM <WS> [WITH INDEXES] [OVERWRITE]
//   COPY TABLE <STEM> FROM <WS> TO <WS> [WITH INDEXES] [OVERWRITE]
//
// examples:
//   COPY TO students_copy
//   COPY TO students_x64 AS X64 VECTOR OVERWRITE
//   COPY TO students_vfp AS VFP
//   COPY TO students_backup WITH SIDECARS OVERWRITE
//   COPY FILE source.txt TO tmp\source_copy.txt OVERWRITE
//   COPY TABLE TO mcc_v3 WITH INDEXES
//   COPY TABLE FROM mcc_x64 WITH INDEXES OVERWRITE
//   COPY TABLE STUDENTS TO mcc_v3 WITH INDEXES
//   COPY TABLE STUDENTS FROM mcc_x64 TO mcc_v3 WITH INDEXES OVERWRITE
//
// notes:
//   COPY USAGE prints usage and does not require an open table.
//   COPY TO requires an open table.
//   COPY FILE does not require an open table.
//   COPY TABLE DEFAULTS THE STEM, FROM AND TO INDEPENDENTLY. An omitted
//   <STEM> is the table open in the CURRENT work area; an omitted FROM or
//   TO is the CURRENT workspace. So TO <WS> pushes out and FROM <WS>
//   pulls in, and any form that omits the stem requires an open table
//   while the forms naming one do not. This mirrors COPY TO, which also
//   reads the current area. Omitting BOTH FROM and TO is refused rather
//   than treated as a copy onto itself.
//   THE PULL FORM OVERWRITES WHAT YOU ARE LOOKING AT, which is why the
//   open-destination refusal below is not a corner case: COPY TABLE FROM
//   <WS> takes the stem from the current area and writes into the current
//   workspace, so its destination is usually the very file that area has
//   open. Close it first.
//   NO DESTINATION LEG MAY BE A FILE OPEN IN A WORK AREA. Rewriting the
//   bytes under a live area leaves the engine holding a header that no
//   longer describes the file -- a record count and field map from the old
//   table over the new one, which reads as data rather than as an error.
//   The run refuses and names the areas, having written nothing.
//   COPY TABLE requires every workspace it uses -- named or defaulted --
//   to be OPEN in this session. The catalog columns are never consulted.
//   A name that is not open is refused and WORKSPACE SWITCH is the fix.
//   WHICH ROOTS IT USES DEPENDS ON WHETHER THE WORKSPACE IS CURRENT. The
//   CURRENT workspace resolves through the LIVE PATH SLOTS, because those
//   are what every other command resolves a filename through and because
//   WORKSPACE LOAD ... MEMO RAM moves them WITHOUT re-stamping membership
//   (workspace_roots_ensure_stamped is called only from SWITCH and NEW).
//   A non-current workspace resolves through its R131 stamp, which is the
//   only authority available for it. Each run prints [slots] or [stamp]
//   per side, and a stamp that disagrees with the slots is reported.
//   COPY TABLE MOVES COMPANIONS AND INDEXES FROM DIFFERENT ROOTS, which is
//   the whole reason it exists. A memo (.dbt/.fpt) sits BESIDE the table
//   under DBFROOT; an index container (.cdx/.cdx.meta/.cnx/.inx/.dtx, and
//   the .cdx.d environment) sits under IDXROOT. WITH SIDECARS cannot do
//   this -- it builds every candidate from the source table's own
//   directory -- so the two flags are not interchangeable.
//   TWO WORKSPACES CAN SHARE ROOTS, and that is refused separately from
//   naming the same workspace twice: a WORKSPACE NEW stamps from whatever
//   the slots hold, so two made without a SET PATH between them are
//   distinct handles over one directory. Every leg would copy a file onto
//   itself, so the run refuses by PATH as well as by handle.
//   WITH INDEXES IS A REFUSAL, NOT A BEST EFFORT. Asking for it when no
//   index container exists for the stem refuses before writing anything,
//   the same line WORKSPACE WRITEBACK draws. Omit it to copy the table and
//   its memo alone.
//   IT DOES NOT JUDGE INDEX KIND. An x64 area accepts CDX and CNX both
//   (AIF-099, owner ruling 2026-08-09); every container found for the stem
//   travels and none is called wrong.
//   COPY TABLE CROSSES RAM AND DISK IN BOTH DIRECTIONS, so a workspace
//   hydrated from a MINIDB (WORKSPACE LOAD <name> MEMO RAM) is a legal
//   FROM and a legal TO. Residence is decided per file by
//   xbase::ramfs::is_virtual on the ABSOLUTE path, and the run prints
//   which side is which. Disk-to-disk still goes through the same
//   copy_file_binary() every other COPY form uses.
//   A RAM DESTINATION IS ERASED BEFORE IT IS REWRITTEN. ramfs::open
//   positions at the start and does not truncate, so overwriting in place
//   would leave the tail of a longer previous file behind. OVERWRITE on a
//   virtual path therefore erases first.
//   THE .cdx.d ENVIRONMENT CANNOT LIVE IN RAM. The registry maps paths to
//   byte buffers and has no directories, so a stem carrying one refuses
//   rather than copying the containers and dropping the environment.
//   LMDB NEVER TRAVELS, by either route. It must mmap a real OS file, it
//   is out of scope for the VFS, and no form of COPY carries it; the
//   destination needs BUILDLMDB.
//   WITH SIDECARS applies only to binary COPY TO.
//   OVERWRITE is required when the destination already exists.
//   KEY DROP accepts a destination that cannot carry the source's primary
//     key. Without it, COPY TO ... AS REFUSES rather than discarding the
//     designation in silence -- which is what a downgrade to VFP, FOX26 or
//     MSDOS does, since those headers have nowhere to record one.
//   Binary COPY TO takes exactly one destination token; a stray token after
//     it REFUSES (corrected 2026-09-23: COPY TO <name> VECTOR without AS X64
//     used to fall through to a silent binary copy).
//
// refuses:
//   VECTOR without AS X64 (any position), stray tokens after the binary
//   destination, unknown flavors, key-carrying source into a keyless target
//   without KEY DROP.
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
#include <sstream>
#include <string>
#include <vector>
#include <algorithm>
#include <cctype>
#include <system_error>
#include <cstdint>
#include <fstream>
#include <memory>

#include "xbase.hpp"
#include "xbase_64.hpp"
#include "xbase/dbf_create.hpp"
#include "xbase_cli.hpp"
#include "xbase/field_name_policy.hpp"
#include "cli/command_output.hpp"
#include "xbase/workspace_membership.hpp"
#include "xbase/ramfs.hpp"
#include "cli/cmd_setpath.hpp"
#include "cli/workarea_util.hpp"
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
    ::cli::cmdout::print_message(dottalk::helpdata::MessageId::CopyUsageText);
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
            ::cli::cmdout::print_message(
                dottalk::helpdata::MessageId::CopySidecarFailedText, {{"detail", err}});
        }
    }

    if (found == 0) {
        ::cli::cmdout::print_message(dottalk::helpdata::MessageId::CopySidecarsNoneText);
    } else {
        ::cli::cmdout::print_message(
            dottalk::helpdata::MessageId::CopySidecarsFoundText,
            {{"found", std::to_string(found)},
             {"copied", std::to_string(copied)},
             {"failed", failed ? (", failed " + std::to_string(failed)) : std::string()}});
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
                               bool key_drop,
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
        ::cli::cmdout::print_message(
            dottalk::helpdata::MessageId::CopyWarningDetailText, {{"detail", w}});
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

    // R142. THE DESIGNATION TRAVELS LAST, after every row is in place;
    // xbase_cli.hpp carries the argument for why that order is load-bearing.
    //
    // COPY never drops or reorders a column and copies values verbatim, so the
    // scan clears on any destination that can hold a flag at all. What this
    // catches is AS: a downgrade to VFP, FOX26 or MSDOS produces a header with
    // nowhere to record the key, and until now that discarded it in silence.
    const auto kt = xbase::cli::carryPrimaryKey(
        src, dst,
        key_drop ? xbase::cli::KeyTravel::Drop
                 : xbase::cli::KeyTravel::RefuseIfBlocked);

    if (!kt.proceed) {
        err = kt.detail + ". The destination " + dstp.string() +
              " was written and carries no key -- re-run with KEY DROP to "
              "accept that, or choose a target flavor that can hold one.";
        return false;
    }

    // Quiet on success: one line, and only when there was something to say.
    if (!kt.detail.empty()) {
        ::cli::cmdout::print_message(
            dottalk::helpdata::MessageId::CopyDetailText, {{"detail", kt.detail}});
    }

    return true;
}

} // namespace

// ---- COPY TABLE <stem> FROM <ws> TO <ws> ------------------------------------
//
// WHY THIS VERB EXISTS. Owner, 2026-10-13: "can i copy ws1:students.dbf
// ws2:students.dbf? in a minidb ... or accross any workspace". The answer was
// no. COPY TO names a file resolved through the CURRENT path slots, so there
// was no way to say "that other workspace's root", and COPY FILE takes two
// hand-built paths the operator has to look up first -- twice, because the
// table and its index do not live in the same place.
//
// SO THIS IS A RESOLVER, NOT A NEW COPY ENGINE. A workspace already knows
// where its tables and indexes live: R131 stamps DBF, INDEXES and LMDB as a
// set. The bytes still move through copy_file_binary() above.
//
// OPEN WORKSPACES ONLY (owner decision, 2026-10-13). Roots come from the LIVE
// stamp. The catalog's DBF_ROOT / IDX_ROOT columns are deliberately NOT used:
// the WORKSPACE contract records that both catalog write sites store the
// SESSION slot rather than the workspace's own stamp, and whether the live
// stamp and the durable columns are one thing or two is explicitly unruled
// (R131 sec 11.8). Resolving through them today could land a table under the
// wrong root, which IS the founding defect R131 exists to close.
//
// TWO ROOTS, NOT ONE, AND THAT IS THE POINT. copy_sidecars() above builds
// every candidate from src_dbf.parent_path(), so it can never carry an index
// that lives under IDXROOT -- and its list has no .cdx, .dbt or .fpt either.
// It is not reused here, and this is not a fix to it; which of its two lists
// is right is a question for the COPY contract and its owner.
//
// IT DOES NOT JUDGE INDEX KIND. An x64 area accepts CDX and CNX both (AIF-099,
// owner ruling 2026-08-09; valid_index_types_for() in cmd_use.cpp is the
// authority, not the flavor sentence in the WORKSPACE help). Every container
// found for the stem travels and none is called wrong. Refusing on extension
// would re-make a mistake that ruling already settled.
//
// GATHER-ALL-BEFORE-WRITING, borrowed from WORKSPACE WRITEBACK. The whole
// manifest is resolved and probed BEFORE the first byte moves, so a shortfall
// refuses having written nothing. A missing index cannot leave a table copied
// without it, which is the half-state this verb exists to avoid.

namespace {

static std::string abs_norm(const std::filesystem::path& p);
static std::string path_key(const std::filesystem::path& p);

struct WsRoots {
    std::uint64_t handle = 0;
    std::string name;            // as the operator sees it, defaulted or not
    std::filesystem::path dbf;
    std::filesystem::path idx;
    bool from_slots = false;     // live global slots, not the membership stamp
    std::string stamp_divergence; // set when the stamp disagreed with the slots
};

// An EMPTY name means the CURRENT workspace -- the default for FROM.
//
// TWO AUTHORITIES, AND WHICH ONE WINS DEPENDS ON WHETHER THE WORKSPACE IS
// CURRENT. R131's model is that SWITCH copies a workspace's stamped roots INTO
// the global path slots, so for the CURRENT workspace the two agree by
// construction -- and the GLOBAL SLOTS are what every other command actually
// resolves a filename through.
//
// They can disagree, and the case that matters is the one this verb was
// extended for. WORKSPACE LOAD <name> MEMO RAM repoints the POSTURE at the RAM
// root and loads through the v3 mechanism, which moves the global DBF and
// INDEXES slots -- but that path does not call workspace_roots_ensure_stamped,
// whose only callers are in SWITCH and NEW. So after a RAM load the global
// slots are the RAM paths while the membership stamp still holds the DISK paths
// it was last switched to.
//
// Resolving the CURRENT workspace through the stamp would therefore copy to
// disk while the operator is working in RAM, find the hydrated table "missing",
// or quietly hit a stale disk copy of it. All three are wrong answers that
// look like clean outcomes, so: CURRENT resolves through the live slots, a
// NAMED non-current workspace resolves through its stamp (the only thing there
// is), and a disagreement is REPORTED rather than silently preferred.
//
// This is not a fix to the missing stamp. That belongs to the LOAD path and is
// a separate change; this only declines to be misled by it.
static bool resolve_ws_roots(const std::string& name, WsRoots& out, std::string& err) {
    const bool implied = name.empty();
    const std::uint64_t cur = xbase::workspace::current_handle();
    const std::uint64_t h = implied ? cur : xbase::workspace::find_by_name_ci(name);
    if (h == 0) {
        err = implied
            ? std::string("there is no current workspace to copy from.")
            : "'" + name + "' is not an open workspace in this session. Open it"
              " (WORKSPACE SWITCH " + name + ") or name directories with COPY FILE.";
        return false;
    }
    out.handle = h;
    out.name = implied ? xbase::workspace::name_of(h) : name;
    if (out.name.empty()) out.name = "handle " + std::to_string(h);

    std::string d, i, l;
    const bool stamped = xbase::workspace::roots_stamped(h) &&
                         xbase::workspace::roots_of(h, d, i, l);

    if (h == cur) {
        const std::filesystem::path sd = dottalk::paths::get_slot(dottalk::paths::Slot::DBF);
        const std::filesystem::path si = dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES);
        if (sd.empty() || si.empty()) {
            err = "'" + out.name + "' is current but the DBF or INDEXES path slot"
                  " is empty. SET PATH them, or DO a profile script.";
            return false;
        }
        out.dbf = sd;
        out.idx = si;
        out.from_slots = true;
        if (stamped) {
            const bool dsame = path_key(std::filesystem::path(d)) == path_key(sd);
            const bool isame = path_key(std::filesystem::path(i)) == path_key(si);
            if (!dsame || !isame) {
                out.stamp_divergence =
                    "'" + out.name + "' is current and its stamped roots DISAGREE"
                    " with the live path slots; the slots win. Stamp: " + d + " | " + i;
            }
        }
        return true;
    }

    // Not current: the stamp is the only authority there is. R131 wants all
    // three or none, so a partial stamp is refused rather than completed
    // piecemeal.
    if (!stamped) {
        err = "'" + out.name + "' is open but its three roots are not all"
              " stamped, and it is not the current workspace, so there are no"
              " live slots to fall back on. WORKSPACE SWITCH " + out.name +
              " stamps them as a set.";
        return false;
    }
    out.dbf = std::filesystem::path(d);
    out.idx = std::filesystem::path(i);
    return true;
}

// A memo belongs to the TABLE and sits beside it under DBFROOT.
static const char* const kTableCompanions[] = { ".dbt", ".fpt" };

// Index containers sit under IDXROOT. All of them travel; see the AIF-099 note
// above for why none of them is judged.
static const char* const kIndexContainers[] = {
    ".cdx", ".cdx.meta", ".cnx", ".inx", ".dtx"
};

// ---- residence ------------------------------------------------------------
//
// ramfs is a flat registry of absolute paths to byte buffers, and its own
// header is explicit that callers normalize to an absolute path FIRST (the same
// rule DbArea::open follows). Every predicate below goes through abs() for that
// reason; is_virtual on a relative path is a silent wrong answer.
static std::string abs_norm(const std::filesystem::path& p) {
    std::error_code ec;
    auto a = std::filesystem::absolute(p, ec);
    if (ec) a = p;
    return a.lexically_normal().string();
}

// COMPARING TWO PATHS IS NOT THE SAME OPERATION AS HANDING ONE TO RAMFS, and
// conflating them cost this verb its open-destination refusal on the spec's
// first run. abs_norm() is for ramfs: the registry is keyed by normalized
// absolute path and lowercasing a key could stop a lookup matching, so what
// goes to ramfs goes verbatim. path_key() is for ASKING WHETHER TWO PATHS ARE
// THE SAME FILE, and on Windows that question is case-insensitive.
//
// MEASURED 2026-10-13, copy_table_regression CT_T10 red: the destination root
// came from a stamp as ...\data\DBF\SANDBOX\CTDST while the open area
// reported ...\data\dbf\sandbox\CTDST\CTSRC.dbf. Same file, different
// spelling, string-unequal -- so the open-destination check never matched and
// the copy overwrote a table that was open in area 8.
//
// same_path() at the top of this file has done it correctly all along. This is
// not a new technique, it is the one already here, finally reused.
static std::string path_key(const std::filesystem::path& p) {
    std::string k = abs_norm(p);
#if defined(_WIN32)
    std::transform(k.begin(), k.end(), k.begin(),
        [](unsigned char c){ return static_cast<char>(std::tolower(c)); });
#endif
    return k;
}

static bool path_is_virtual(const std::filesystem::path& p) {
    return xbase::ramfs::is_virtual(abs_norm(p));
}

// Residence-aware "is there a file here". fs::is_regular_file answers FALSE for
// every virtual path, so a probe that used it alone would report a hydrated
// table as missing -- and this verb refuses on a missing source, so that would
// read as a clean refusal rather than a wrong answer.
static bool file_exists_any(const std::filesystem::path& p) {
    const std::string a = abs_norm(p);
    if (xbase::ramfs::is_virtual(a)) return xbase::ramfs::exists(a);
    std::error_code ec;
    return std::filesystem::exists(p, ec) && !ec &&
           std::filesystem::is_regular_file(p, ec) && !ec;
}

static bool dir_exists_real(const std::filesystem::path& p) {
    std::error_code ec;
    return std::filesystem::exists(p, ec) && !ec &&
           std::filesystem::is_directory(p, ec) && !ec;
}

// The four combinations. Disk-to-disk is DELEGATED rather than reimplemented,
// so the ordinary case keeps using the exact function COPY TO and COPY FILE
// use and this change cannot alter it.
static bool copy_bytes_any(const std::filesystem::path& src,
                           const std::filesystem::path& dst,
                           bool overwrite,
                           std::string* err) {
    const std::string sa = abs_norm(src);
    const std::string da = abs_norm(dst);
    const bool sv = xbase::ramfs::is_virtual(sa);
    const bool dv = xbase::ramfs::is_virtual(da);

    if (!sv && !dv) return copy_file_binary(src, dst, overwrite, err);

    if (!file_exists_any(src)) {
        if (err) *err = "Source does not exist: " + src.string();
        return false;
    }
    if (file_exists_any(dst) && !overwrite) {
        if (err) *err = "Destination exists (use OVERWRITE): " + dst.string();
        return false;
    }

    // ---- reader ----
    std::unique_ptr<std::iostream> rin;
    std::ifstream fin;
    if (sv) {
        rin = xbase::ramfs::open(sa, /*create*/false);
        if (!rin) { if (err) *err = "RAM source could not be opened: " + src.string();
                    return false; }
    } else {
        fin.open(src, std::ios::binary);
        if (!fin.good()) { if (err) *err = "Source could not be opened: " + src.string();
                           return false; }
    }
    std::istream& in = sv ? static_cast<std::istream&>(*rin)
                          : static_cast<std::istream&>(fin);

    // ---- writer ----
    //
    // A VIRTUAL destination is ERASED FIRST. ramfs::open positions at the start
    // and has no truncate, so rewriting a shorter file in place would leave the
    // previous tail attached -- a DBF whose header says N records followed by
    // the bytes of a longer table is not a detectable error, it is a readable
    // wrong answer. erase() then create is the only safe order.
    std::unique_ptr<std::iostream> rout;
    std::ofstream fout;
    if (dv) {
        if (xbase::ramfs::exists(da)) xbase::ramfs::erase(da);
        rout = xbase::ramfs::open(da, /*create*/true);
        if (!rout) { if (err) *err = "RAM destination could not be created: " + dst.string();
                     return false; }
    } else {
        std::error_code ec;
        if (dst.has_parent_path() && !dst.parent_path().empty()) {
            std::filesystem::create_directories(dst.parent_path(), ec);
            ec.clear();
        }
        fout.open(dst, std::ios::binary | std::ios::trunc);
        if (!fout.good()) { if (err) *err = "Destination could not be created: " + dst.string();
                            return false; }
    }
    std::ostream& out = dv ? static_cast<std::ostream&>(*rout)
                           : static_cast<std::ostream&>(fout);

    char buf[1 << 16];
    while (in.read(buf, sizeof(buf)) || in.gcount() > 0) {
        out.write(buf, in.gcount());
        if (!out) { if (err) *err = "Write failed into " + dst.string(); return false; }
    }
    out.flush();
    if (!out) { if (err) *err = "Flush failed into " + dst.string(); return false; }
    return true;
}

static const char* residence_label(const std::filesystem::path& p) {
    return path_is_virtual(p) ? "RAM" : "disk";
}

struct Leg {
    std::filesystem::path src;
    std::filesystem::path dst;
    bool is_dir = false;      // the .cdx.d environment
    bool mandatory = false;   // the table itself
};

} // namespace

static void copy_table_between_workspaces(const DbArea& a,
                                          const std::string& stem_in,
                                          const std::string& from_name,
                                          const std::string& to_name,
                                          bool with_indexes,
                                          bool overwrite) {
    namespace fs = std::filesystem;

    // An omitted stem is the CURRENT AREA's table. dbfBasename() is the name the
    // area was opened under, so the copy carries the name the operator is
    // looking at rather than one re-derived from a path.
    std::string stem = fs::path(trim(stem_in)).stem().string();
    if (stem.empty()) {
        if (!a.isOpen()) {
            std::cout << "COPY TABLE: refusing -- no table name was given and no"
                      << " table is open in the current area. Name one, or USE a"
                      << " table first.\n";
            return;
        }
        stem = fs::path(a.dbfBasename()).stem().string();
        if (stem.empty()) {
            std::cout << "COPY TABLE: refusing -- the open area has no table name"
                      << " to copy. Name one explicitly.\n";
            return;
        }
    }

    WsRoots from{}, to{};
    std::string err;
    if (!resolve_ws_roots(from_name, from, err)) {
        std::cout << "COPY TABLE: refusing -- FROM " << err << "\n";
        return;
    }
    if (!resolve_ws_roots(to_name, to, err)) {
        std::cout << "COPY TABLE: refusing -- TO " << err << "\n";
        return;
    }
    // Same workspace both ends is a no-op dressed as a copy, and with
    // OVERWRITE it would copy a file onto itself. Refuse and say which name
    // resolved where, because with a defaulted FROM the collision is invisible
    // in what the operator typed.
    if (from.handle == to.handle) {
        std::cout << "COPY TABLE: refusing -- FROM and TO are the same workspace ('"
                  << from.name << "'"
                  << (from_name.empty() ? ", defaulted from the current workspace" : "")
                  << "). Nothing was written.\n";
        return;
    }

    // ---- gather ------------------------------------------------------------
    std::vector<Leg> legs;

    const fs::path srcTable = from.dbf / (stem + ".dbf");
    if (!file_exists_any(srcTable)) {
        std::cout << "COPY TABLE: refusing -- '" << stem << ".dbf' is not under "
                  << from.name << "'s DBF root (" << from.dbf.string()
                  << "). Nothing was written.\n";
        return;
    }
    legs.push_back(Leg{srcTable, to.dbf / (stem + ".dbf"), false, true});

    for (const char* ext : kTableCompanions) {
        const fs::path c = from.dbf / (stem + ext);
        if (file_exists_any(c)) legs.push_back(Leg{c, to.dbf / (stem + ext), false, false});
    }

    int indexes_found = 0;
    if (with_indexes) {
        for (const char* ext : kIndexContainers) {
            const fs::path c = from.idx / (stem + ext);
            if (file_exists_any(c)) {
                legs.push_back(Leg{c, to.idx / (stem + ext), false, false});
                ++indexes_found;
            }
        }
        const fs::path env = from.idx / (stem + ".cdx.d");
        if (dir_exists_real(env)) {
            // The registry has no directories, so an environment cannot be
            // created in RAM and cannot be read out of one. Refuse the whole
            // run rather than carry the containers and drop the environment --
            // a CDX whose environment is missing is the kind of half-state this
            // verb exists to prevent.
            if (path_is_virtual(to.idx) || path_is_virtual(from.idx)) {
                std::cout << "COPY TABLE: refusing -- '" << stem << ".cdx.d' is a"
                          << " directory and one side of this copy is RAM-resident."
                          << " The RAM registry holds files, not directories, so the"
                          << " environment cannot travel. Nothing was written."
                          << " WORKSPACE WRITEBACK the RAM side to real disk first.\n";
                return;
            }
            legs.push_back(Leg{env, to.idx / (stem + ".cdx.d"), true, false});
            ++indexes_found;
        }
        // The shortfall refusal. WITH INDEXES was ASKED FOR, so finding none is
        // a failed request and not an empty set -- the same line WRITEBACK
        // draws, and the reason nothing has been written yet at this point.
        if (indexes_found == 0) {
            std::cout << "COPY TABLE: refusing -- WITH INDEXES was asked for and no"
                      << " index container for '" << stem << "' is under "
                      << from.name << "'s INDEXES root (" << from.idx.string()
                      << "). Nothing was written. Drop WITH INDEXES to copy the"
                      << " table alone, or REINDEX at the destination.\n";
            return;
        }
    }

    // ORDER: SAME PATH IS CHECKED BEFORE OPEN-DESTINATION, deliberately.
    // "These two names are one file" is a more fundamental complaint than
    // "that file is open", and a self-copy is usually ALSO open -- so the
    // other order made every same-path case report the open refusal and
    // say nothing about the real problem. Found by writing the regression
    // spec, before it had been run once.
    // SAME PATH IS A SEPARATE REFUSAL FROM SAME WORKSPACE, and the handle check
    // above does not cover it. Two DIFFERENT workspaces can carry the SAME
    // roots -- a WORKSPACE NEW stamps from whatever the slots hold, so two made
    // without a SET PATH between them are distinct handles over one directory.
    // Every leg would then be a file copied onto itself: without OVERWRITE the
    // destination-exists probe below would refuse it for the wrong reason, and
    // WITH OVERWRITE std::filesystem::copy_file on one path is undefined
    // territory this verb has no business entering. Refuse per leg, by path.
    {
        std::vector<std::string> selfcopy;
        for (const auto& L : legs) {
            if (path_key(L.src) == path_key(L.dst)) selfcopy.push_back(L.src.string());
        }
        if (!selfcopy.empty()) {
            std::cout << "COPY TABLE: refusing -- '" << from.name << "' and '"
                      << to.name << "' are different workspaces resolving to the"
                      << " same path, so " << selfcopy.size()
                      << " leg(s) would copy a file onto itself. Nothing was"
                      << " written.\n";
            for (const auto& f : selfcopy) std::cout << "    = " << f << "\n";
            return;
        }
    }

    // NO DESTINATION MAY BE OPEN IN A WORK AREA.
    //
    // THE REVERSE DEFAULT MAKES THIS THE COMMON CASE, NOT A CORNER. Owner,
    // 2026-10-13: "we can also use the reverse default of copy table from ws
    // (to current area)". COPY TABLE FROM <ws> takes the stem from the CURRENT
    // AREA and writes into the CURRENT WORKSPACE -- so by construction its
    // destination is usually the exact file that area has open.
    //
    // Rewriting those bytes underneath a live area is worse than a failure. On
    // disk Windows may refuse the share and the copy fails honestly, but that
    // is the platform's accident and not a rule. On the RAM path there is no
    // share to violate at all: ramfs hands out a shared reference to the
    // RamFile and erase() plus re-create swaps the bytes under a reader that
    // holds a header describing the OLD table. A stale record count and field
    // map over new bytes reads as DATA, not as an error.
    //
    // find_open_areas_by_name_ci() returns every candidate rather than picking
    // one, which is what makes it usable here: the question is "is ANY area on
    // this path", not "which one would resolve".
    //
    // LEADING :: IS REQUIRED, not style. This file carries `using namespace
    // xbase;` at :162, so a bare cli:: is AMBIGUOUS between global ::cli and
    // xbase::cli (xbase_cli.hpp:47) and MSVC refuses it with C2872. Every other
    // reference in this file is already spelled ::cli::cmdout for the same
    // reason; the first draft of this block was not, and the build caught it.
    {
        std::vector<std::string> live;
        for (const auto& L : legs) {
            const std::string da = path_key(L.dst);
            const std::string stem_of = L.dst.stem().string();
            for (xbase::DbArea* ar : ::cli::find_open_areas_by_name_ci(stem_of)) {
                if (!ar || !ar->isOpen()) continue;
                if (path_key(std::filesystem::path(ar->filename())) != da) continue;
                live.push_back("area " + std::to_string(::cli::slot_of_area(ar)) +
                               ": " + L.dst.string());
            }
        }
        if (!live.empty()) {
            std::cout << "COPY TABLE: refusing -- " << live.size()
                      << " destination(s) are OPEN in a work area. Rewriting a"
                      << " file under a live area leaves the engine holding a"
                      << " header that no longer describes it. Nothing was"
                      << " written; close these and re-run.\n";
            for (const auto& l : live) std::cout << "    = " << l << "\n";
            return;
        }
    }

    // ---- probe the destinations BEFORE writing anything --------------------
    if (!overwrite) {
        std::vector<std::string> blocked;
        for (const auto& L : legs) {
            if (file_exists_any(L.dst) || dir_exists_real(L.dst))
                blocked.push_back(L.dst.string());
        }
        if (!blocked.empty()) {
            std::cout << "COPY TABLE: refusing -- " << blocked.size()
                      << " destination(s) exist and OVERWRITE was not given."
                      << " Nothing was written.\n";
            for (const auto& b : blocked) std::cout << "    = " << b << "\n";
            return;
        }
    }

    // ---- write -------------------------------------------------------------
    if (!from.stamp_divergence.empty())
        std::cout << "  NOTE: " << from.stamp_divergence << "\n";
    if (!to.stamp_divergence.empty())
        std::cout << "  NOTE: " << to.stamp_divergence << "\n";

    std::cout << "COPY TABLE: " << stem << "  " << from.name
              << (from.from_slots ? " [slots]" : " [stamp]") << " -> " << to.name
              << (to.from_slots ? " [slots]" : " [stamp]") << "\n";
    std::cout << "  DBF    : " << from.dbf.string() << " [" << residence_label(from.dbf)
              << "]  ->  " << to.dbf.string() << " [" << residence_label(to.dbf) << "]\n";
    if (with_indexes)
        std::cout << "  INDEXES: " << from.idx.string() << " [" << residence_label(from.idx)
                  << "]  ->  " << to.idx.string() << " [" << residence_label(to.idx) << "]\n";

    int copied = 0, failed = 0;
    for (const auto& L : legs) {
        if (L.is_dir) {
            std::error_code ec;
            fs::create_directories(L.dst, ec);
            ec.clear();
            const auto opt = fs::copy_options::recursive |
                             (overwrite ? fs::copy_options::overwrite_existing
                                        : fs::copy_options::none);
            fs::copy(L.src, L.dst, opt, ec);
            if (ec) { ++failed; std::cout << "  ! " << L.src.filename().string()
                                          << " -- " << ec.message() << "\n"; }
            else    { ++copied; std::cout << "    " << L.src.filename().string()
                                          << "  (environment)\n"; }
            continue;
        }
        std::string e;
        if (copy_bytes_any(L.src, L.dst, overwrite, &e)) {
            ++copied;
            std::cout << "    " << L.src.filename().string() << "\n";
        } else {
            ++failed;
            std::cout << "  ! " << L.src.filename().string() << " -- " << e << "\n";
        }
    }

    std::cout << "COPY TABLE: " << copied << " file(s) copied";
    if (failed) std::cout << ", " << failed << " FAILED";
    std::cout << ".\n";

    // A copied index is a copied FILE, not a proven order. The destination has
    // to open it before anyone can claim it works -- SEEK a known key, since an
    // unordered area reports not-found for rows that exist.
    if (with_indexes && !failed)
        std::cout << "  The index travelled as bytes. Prove it at the destination"
                  << " (open the table there and SEEK a known key).\n";

    // Nothing here touches the destination workspace's POSTURE. A copied table
    // is on disk and absent from the .dtschema and the memo until someone saves
    // them, which is exactly the divergence AIPR-20261012-COWORK-213 reports.
    if (!failed)
        std::cout << "  The posture is unchanged: WORKSPACE OPEN the destination"
                  << " and SAVE it if this table should be a member.\n";

    // RAM IS EPHEMERAL BY DESIGN -- ramfs::clear() drops everything at session
    // teardown. A copy INTO RAM that is never written back or saved is gone at
    // QUIT, and saying so here costs one line against an operator losing work
    // they watched succeed.
    if (!failed && path_is_virtual(to.dbf))
        std::cout << "  THE DESTINATION IS RAM-RESIDENT AND RAM DOES NOT SURVIVE"
                  << " THIS SESSION. WORKSPACE WRITEBACK " << to.name
                  << " TO <dir> WITH INDEXES, or WORKSPACE SAVE " << to.name
                  << " MEMO MINIDB, before you quit.\n";
}

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
    bool with_indexes = false;
    bool key_drop = false;

    // Strip OVERWRITE, WITH, SIDECARS tokens (flexibly)
    {
        std::vector<std::string> kept;
        kept.reserve(tok.size());

        for (size_t i = 0; i < tok.size(); ++i) {
            const std::string u = up(tok[i]);

            if (u == "OVERWRITE") { overwrite = true; continue; }

            // KEY DROP -- the operator accepting that the primary key does not
            // travel. Bare KEY is left in place so it reaches the usage error
            // rather than being silently swallowed as if it meant something.
            if (u == "KEY" && i + 1 < tok.size() && up(tok[i + 1]) == "DROP") {
                key_drop = true;
                ++i;
                continue;
            }

            if (u == "WITH") {
                if (i + 1 < tok.size() && up(tok[i + 1]) == "SIDECARS") {
                    with_sidecars = true;
                    ++i;
                    continue;
                }
                // INDEXES is NOT a spelling of SIDECARS. SIDECARS looks beside
                // the table; INDEXES looks under IDXROOT. Only COPY TABLE can
                // honour the second, because only it knows two roots.
                if (i + 1 < tok.size() && up(tok[i + 1]) == "INDEXES") {
                    with_indexes = true;
                    ++i;
                    continue;
                }
                continue;
            }

            if (u == "SIDECARS") { with_sidecars = true; continue; }
            if (u == "INDEXES")  { with_indexes  = true; continue; }

            kept.push_back(tok[i]);
        }

        tok.swap(kept);
    }

    if (tok.empty()) { usage_copy(); return; }

    // COPY TABLE <stem> FROM <ws> TO <ws>
    if (token_is(tok[0], "TABLE")) {
        // Three forms, shortest first. An empty stem or an empty FROM name is
        // the DEFAULT and the handler resolves it; the parser's only job is to
        // say which slot was left out.
        //
        //   TABLE TO <ws>                 -> push:  current area's table out
        //   TABLE FROM <ws>               -> pull:  into the current workspace
        //   TABLE <stem> TO <ws>          -> push a named table
        //   TABLE <stem> FROM <ws>        -> pull a named table
        //   TABLE <stem> FROM <ws> TO <ws>
        //
        // AN EMPTY STRING MEANS "DEFAULTED" and the handler resolves it, so the
        // parser only decides which slot was left out. Omitting BOTH FROM and
        // TO would default both to the current workspace, which the same-path
        // and same-handle refusals would catch -- but refusing it HERE says
        // what is actually wrong instead of reporting a self-copy.
        std::string stem, fromName, toName;
        bool haveFrom = false, haveTo = false;

        if (tok.size() == 3 && token_is(tok[1], "TO")) {
            toName = trim(tok[2]);                       haveTo = true;
        } else if (tok.size() == 3 && token_is(tok[1], "FROM")) {
            fromName = trim(tok[2]);                     haveFrom = true;
        } else if (tok.size() == 4 && token_is(tok[2], "TO")) {
            stem = tok[1]; toName = trim(tok[3]);        haveTo = true;
        } else if (tok.size() == 4 && token_is(tok[2], "FROM")) {
            stem = tok[1]; fromName = trim(tok[3]);      haveFrom = true;
        } else if (tok.size() == 6 && token_is(tok[2], "FROM") && token_is(tok[4], "TO")) {
            stem = tok[1];
            fromName = trim(tok[3]);                     haveFrom = true;
            toName   = trim(tok[5]);                     haveTo   = true;
        } else {
            usage_copy();
            return;
        }

        if (!haveFrom && !haveTo) {
            std::cout << "COPY TABLE: refusing -- neither FROM nor TO was given,"
                      << " so both would default to the current workspace. Name"
                      << " at least one end.\n";
            return;
        }

        copy_table_between_workspaces(a, stem, fromName, toName,
                                      with_indexes, overwrite);
        return;
    }

    // COPY FILE <src> TO <dst>
    if (token_is(tok[0], "FILE")) {
        if (tok.size() < 4 || !token_is(tok[2], "TO")) { usage_copy(); return; }

        const std::filesystem::path src = trim(tok[1]);
        const std::filesystem::path dst = trim(tok[3]);

        std::string err;
        if (copy_file_binary(src, dst, overwrite, &err)) {
            ::cli::cmdout::print_message(
                dottalk::helpdata::MessageId::CopiedFileText, {{"dst", dst.string()}});
        } else {
            ::cli::cmdout::print_message(
                dottalk::helpdata::MessageId::CopyFileFailedText, {{"detail", err}});
        }
        return;
    }

    // COPY TO <dbf> [AS <flavor>]
    if (token_is(tok[0], "TO")) {
        if (!a.isOpen()) {
            ::cli::cmdout::print_message(dottalk::helpdata::MessageId::CopyToNoFileOpenText);
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
                ::cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::CopyAsUnexpectedTokenText, {{"token", tok[2]}});
                ::cli::cmdout::print_message(dottalk::helpdata::MessageId::CopyAsUseHintText);
                return;
            }
            if (as_pos + 1 >= tok.size()) {
                usage_copy();
                return;
            }

            Flavor flavor = Flavor::MSDOS;
            if (!parse_flavor_token(tok[as_pos + 1], flavor)) {
                ::cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::CopyAsUnknownFlavorText, {{"flavor", tok[as_pos + 1]}});
                return;
            }

            CopyVectorOptions vector_opts;
            std::string option_err;
            if (!parse_copy_vector_options(tok, as_pos + 2, flavor, vector_opts, option_err)) {
                ::cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::CopyDetailText, {{"detail", option_err}});
                return;
            }

            const std::filesystem::path dstp = resolve_dst_for_logical_copy_to(a, tok[1]);

            if (with_sidecars) {
                ::cli::cmdout::print_message(dottalk::helpdata::MessageId::CopyAsSidecarsIgnoredText);
            }

            if (vector_opts.vector_requested) {
                ::cli::cmdout::print_message(dottalk::helpdata::MessageId::CopyAsVectorPolicyText);
            }

            std::string err;
            if (!logical_copy_to_as(a, dstp, flavor, overwrite, key_drop, vector_opts, err)) {
                ::cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::CopyAsFailedText, {{"detail", err}});
                return;
            }

            ::cli::cmdout::print_message(
                dottalk::helpdata::MessageId::CopiedTableText,
                {{"dst", dstp.string()},
                 {"flavor", flavor_name_local(flavor)},
                 {"vector", vector_opts.vector_requested ? " VECTOR" : ""}});
            return;
        }

        // Existing binary copy behavior.
        //
        // Binary COPY TO takes exactly ONE destination token. A stray token
        // here was silently ignored until 2026-09-23, when
        //   COPY TO <name> VECTOR OVERWRITE     (missing AS X64)
        // fell through to this branch and produced a byte-identical v32 copy
        // the operator believed was a conversion -- measured afterward: the
        // "converted" tables still read DBF version byte 0x03. The usage
        // contract already said "VECTOR is ... valid only with AS X64"; the
        // parser just never enforced it on this path. Refuse loudly instead.
        if (tok.size() > 2) {
            std::string detail =
                "COPY TO: unexpected token after destination: '" + tok[2] + "'.";
            if (up(trim(tok[2])) == "VECTOR") {
                detail += " VECTOR is valid only with AS X64 -- did you mean: "
                          "COPY TO " + tok[1] + " AS X64 VECTOR ?";
            }
            ::cli::cmdout::print_message(
                dottalk::helpdata::MessageId::CopyDetailText, {{"detail", detail}});
            ::cli::cmdout::print_message(dottalk::helpdata::MessageId::CopyAsUseHintText);
            return;
        }

        const std::filesystem::path dstp = resolve_dst_for_copy_to(a, tok[1]);

        std::string err;
        if (!copy_file_binary(srcp, dstp, overwrite, &err)) {
            ::cli::cmdout::print_message(
                dottalk::helpdata::MessageId::CopyToFailedText, {{"detail", err}});
            return;
        }

        ::cli::cmdout::print_message(
            dottalk::helpdata::MessageId::CopiedDbfText, {{"dst", dstp.string()}});

        if (with_sidecars) {
            copy_sidecars(srcp, dstp, overwrite);
        }

        return;
    }

    usage_copy();
}