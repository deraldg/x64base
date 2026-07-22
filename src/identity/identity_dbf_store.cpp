// src/identity/identity_dbf_store.cpp
// DBF-backed persistence for the identity / RBAC catalog (AIF-045 2b-ii, APH-5).
// Compiled into dottalkpp via the src glob (sibling of identity_bootstrap.cpp).
//
// Create tables with the engine's standalone serializer (xbase::dbf_create), then
// populate/read rows through the engine's DbArea + field codec — so identity
// tables are byte-identical to CLI-created tables and browsable/indexable.

#include "identity/identity_dbf_store.hpp"
#include "identity/identity_schema.hpp"

#include "xbase.hpp"
#include "xbase/dbf_create.hpp"
#include "xbase/field_name_policy.hpp"
#include "xbase/fields.hpp"
#include "common/path_state.hpp"

#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <stdexcept>
#include <string>
#include <vector>

namespace dottalk::identity {

namespace {

namespace fs = std::filesystem;

std::string join(const std::string& dir, const char* table) {
    return (fs::path(dir) / (std::string(table) + ".dbf")).string();
}

// ---- serialize helpers (values are strings at the DbArea boundary) ----
std::string s_u64(std::uint64_t v)                 { return std::to_string(v); }
std::string s_enum(std::uint8_t v)                 { return std::to_string(static_cast<unsigned>(v)); }
std::string s_bool(bool b)                         { return b ? "T" : "F"; }
template <class Id> std::string s_id(const Id& id) { return std::to_string(id.value()); }
template <class Id> std::string s_optid(const std::optional<Id>& id) {
    return std::to_string(id.has_value() ? id->value() : 0ULL);
}

// Row writer over an open, freshly appended record.
struct RowW {
    xbase::DbArea& a;
    std::string&   err;
    bool           ok = true;
    void set(const char* col, const std::string& v) {
        if (!ok) return;
        // findFieldCI is 0-based (-1 = not found); DbArea get/set are 1-based (slot 0 unused).
        int i = fields::findFieldCI(a, col);
        if (i < 0) { ok = false; err = std::string("identity save: missing column ") + col; return; }
        a.set(i + 1, v);
    }
};

// Row reader over the current record.
struct RowR {
    const xbase::DbArea& a;
    std::string str(const char* col) const {
        // findFieldCI is 0-based (-1 = not found); DbArea get is 1-based.
        int i = fields::findFieldCI(a, col);
        return i >= 0 ? a.get(i + 1) : std::string();
    }
    std::uint64_t u64(const char* col) const {
        std::string v = str(col);
        return v.empty() ? 0ULL : std::strtoull(v.c_str(), nullptr, 10);
    }
    bool boolean(const char* col) const {
        std::string v = str(col);
        return !v.empty() && (v[0] == 'T' || v[0] == 't' || v[0] == 'Y' || v[0] == '1');
    }
    template <class Id> Id id(const char* col) const { return Id{u64(col)}; }
    template <class Id> std::optional<Id> optid(const char* col) const {
        std::uint64_t v = u64(col);
        if (v == 0) return std::nullopt;
        return Id{v};
    }
};

// Create one table fresh (removing any prior .dbf/.dbt/.fpt sidecars first).
bool create_table(const std::string& dir, const schema::Table& t, std::string& err) {
    const std::string path = join(dir, t.name);
    std::error_code ec;
    fs::remove(path, ec);
    fs::remove(fs::path(path).replace_extension(".dbt"), ec);
    fs::remove(fs::path(path).replace_extension(".fpt"), ec);

    // X64 requires unique 10-byte physical descriptor tokens so DbArea can read the
    // logical field names back (findFieldCI). Apply the same policy CREATE uses.
    std::vector<xbase::dbf_create::FieldSpec> fields = t.fields;
    std::vector<std::string> names;
    names.reserve(fields.size());
    for (const auto& f : fields) names.push_back(f.name);
    const auto plans = xbase::field_name_policy::plan_x64_unique_fallback(names);
    for (std::size_t i = 0; i < fields.size() && i < plans.size(); ++i)
        fields[i].descriptor_name = plans[i].descriptor_name;

    return xbase::dbf_create::create_dbf(path, fields, xbase::dbf_create::Flavor::X64, err);
}

// Open a just-created table for appends.
bool open_table(const std::string& dir, const char* name, xbase::DbArea& a, std::string& err) {
    try {
        a.open(join(dir, name));
        return true;
    } catch (const std::exception& e) {
        err = std::string("identity: cannot open ") + name + ": " + e.what();
        return false;
    }
}

} // namespace

std::string default_identity_dir() {
    return (dottalk::paths::get_slot(dottalk::paths::Slot::DATA) / "metadata" / schema::kIdentityDir).string();
}

bool save_identity_tables(const InMemoryIdentityStore& store,
                          const std::string& dir, std::string& err) {
    std::error_code ec;
    fs::create_directories(dir, ec);
    if (ec) { err = "identity save: cannot create dir " + dir + ": " + ec.message(); return false; }

    // 1) create all nine tables fresh
    for (const auto& t : schema::all_tables())
        if (!create_table(dir, t, err)) return false;

    // 2) populate each from its vector
    auto append = [&](const char* name, auto&& emit) -> bool {
        xbase::DbArea a;
        if (!open_table(dir, name, a, err)) return false;
        bool ok = emit(a);
        a.close();
        return ok;
    };

    bool ok = true;

    ok = ok && append("SYSUSER", [&](xbase::DbArea& a) {
        for (const auto& u : store.users) {
            a.appendBlank(); RowW w{a, err};
            w.set("ID", s_id(u.id));          w.set("UKEY", u.key);
            w.set("LOGIN", u.login_name);      w.set("DISPLAY", u.display_name);
            w.set("AUTHKIND", s_enum(static_cast<std::uint8_t>(u.auth_kind)));
            w.set("CRED", u.credential_ref);   w.set("STATUS", s_enum(static_cast<std::uint8_t>(u.status)));
            w.set("PROFHOME", u.profile_home_key);
            w.set("VFROM", s_u64(u.stamp.valid_from)); w.set("VTHRU", s_u64(u.stamp.valid_through));
            w.set("ROWVER", s_u64(u.stamp.row_version));
            if (!w.ok) return false; a.writeCurrent();
        }
        return true;
    });

    ok = ok && append("SYSMEMBER", [&](xbase::DbArea& a) {
        for (const auto& m : store.members) {
            a.appendBlank(); RowW w{a, err};
            w.set("ID", s_id(m.id));            w.set("USERID", s_optid(m.user_id));
            w.set("MKEY", m.key);               w.set("KIND", s_enum(static_cast<std::uint8_t>(m.kind)));
            w.set("DEFROLE", s_optid(m.default_role));
            w.set("DEFPSET", s_optid(m.default_permission_set));
            w.set("STATUS", s_enum(static_cast<std::uint8_t>(m.status)));
            w.set("VFROM", s_u64(m.stamp.valid_from)); w.set("VTHRU", s_u64(m.stamp.valid_through));
            w.set("ROWVER", s_u64(m.stamp.row_version));
            if (!w.ok) return false; a.writeCurrent();
        }
        return true;
    });

    ok = ok && append("SYSROLE", [&](xbase::DbArea& a) {
        for (const auto& r : store.roles) {
            a.appendBlank(); RowW w{a, err};
            w.set("ID", s_id(r.id));  w.set("RKEY", r.key);   w.set("RNAME", r.name);
            w.set("RKIND", r.kind);   w.set("DESCR", r.description);
            w.set("STATUS", s_enum(static_cast<std::uint8_t>(r.status)));
            if (!w.ok) return false; a.writeCurrent();
        }
        return true;
    });

    ok = ok && append("SYSPERM", [&](xbase::DbArea& a) {
        for (const auto& p : store.permissions) {
            a.appendBlank(); RowW w{a, err};
            w.set("ID", s_id(p.id));   w.set("PKEY", p.key);
            w.set("RESCLASS", p.resource_class); w.set("PACTION", p.action);
            w.set("RISK", s_enum(static_cast<std::uint8_t>(p.risk)));
            w.set("REQAPPR", s_bool(p.requires_approval));
            w.set("STATUS", s_enum(static_cast<std::uint8_t>(p.status)));
            if (!w.ok) return false; a.writeCurrent();
        }
        return true;
    });

    ok = ok && append("SYSROLEPERM", [&](xbase::DbArea& a) {
        for (const auto& rp : store.role_permissions) {
            a.appendBlank(); RowW w{a, err};
            w.set("ROLEID", s_id(rp.role)); w.set("PERMID", s_id(rp.permission));
            if (!w.ok) return false; a.writeCurrent();
        }
        return true;
    });

    ok = ok && append("SYSMEMROLE", [&](xbase::DbArea& a) {
        for (const auto& mr : store.member_roles) {
            a.appendBlank(); RowW w{a, err};
            w.set("MEMBERID", s_id(mr.member)); w.set("ROLEID", s_id(mr.role));
            w.set("ORGSCOPE", s_optid(mr.org_scope)); w.set("WORKSCOPE", s_optid(mr.work_scope));
            if (!w.ok) return false; a.writeCurrent();
        }
        return true;
    });

    ok = ok && append("SYSOVERRIDE", [&](xbase::DbArea& a) {
        for (const auto& ov : store.overrides) {
            a.appendBlank(); RowW w{a, err};
            w.set("MEMBERID", s_id(ov.member)); w.set("PERMID", s_id(ov.permission));
            w.set("EFFECT", s_enum(static_cast<std::uint8_t>(ov.effect)));
            w.set("ORGSCOPE", s_optid(ov.org_scope)); w.set("WORKSCOPE", s_optid(ov.work_scope));
            if (!w.ok) return false; a.writeCurrent();
        }
        return true;
    });

    ok = ok && append("SYSASSIGN", [&](xbase::DbArea& a) {
        for (const auto& as : store.assignments) {
            a.appendBlank(); RowW w{a, err};
            w.set("ID", s_id(as.id));        w.set("MEMBERID", s_id(as.member));
            w.set("ORGUNIT", s_optid(as.org_unit)); w.set("WORK", s_optid(as.work));
            w.set("ROLE", s_optid(as.role)); w.set("PSET", s_optid(as.permission_set));
            w.set("REPORTSTO", s_optid(as.reports_to)); w.set("AKIND", as.assignment_kind);
            w.set("STATUS", s_enum(static_cast<std::uint8_t>(as.status)));
            w.set("VFROM", s_u64(as.stamp.valid_from)); w.set("VTHRU", s_u64(as.stamp.valid_through));
            w.set("ROWVER", s_u64(as.stamp.row_version));
            if (!w.ok) return false; a.writeCurrent();
        }
        return true;
    });

    ok = ok && append("SYSGRANT", [&](xbase::DbArea& a) {
        for (const auto& g : store.grants) {
            a.appendBlank(); RowW w{a, err};
            w.set("ID", s_id(g.id));         w.set("REQBY", s_id(g.requested_by));
            w.set("GRANTTO", s_id(g.granted_to)); w.set("ROLEASN", s_optid(g.role_assignment));
            w.set("WORK", s_optid(g.work));  w.set("RESSCOPE", g.resource_scope);
            w.set("ACTSCOPE", g.action_scope); w.set("RISK", s_enum(static_cast<std::uint8_t>(g.risk)));
            w.set("GRANTAT", s_u64(g.granted_at)); w.set("EXPAT", s_u64(g.expires_at));
            w.set("STATUS", s_enum(static_cast<std::uint8_t>(g.status)));
            w.set("REASON", g.reason);       w.set("SRCREPORT", g.source_report_id);
            if (!w.ok) return false; a.writeCurrent();
        }
        return true;
    });

    return ok;
}

bool load_identity_tables(const std::string& dir,
                          InMemoryIdentityStore& out, std::string& err) {
    out = InMemoryIdentityStore{};  // clear

    // Every table must be present for a clean load.
    for (const auto& t : schema::all_tables()) {
        if (!fs::exists(join(dir, t.name))) {
            err = std::string("identity load: missing table ") + t.name;
            return false;
        }
    }

    auto scan = [&](const char* name, auto&& per_row) -> bool {
        xbase::DbArea a;
        if (!open_table(dir, name, a, err)) return false;
        const std::uint64_t n = a.recCount64();
        for (std::uint64_t i = 1; i <= n; ++i) {
            if (!a.gotoRec64(i)) continue;
            RowR r{a};
            per_row(r);
        }
        a.close();
        return true;
    };

    bool ok = true;

    ok = ok && scan("SYSUSER", [&](const RowR& r) {
        User u;
        u.id = r.id<UserId>("ID"); u.key = r.str("UKEY");
        u.login_name = r.str("LOGIN"); u.display_name = r.str("DISPLAY");
        u.auth_kind = static_cast<AuthKind>(r.u64("AUTHKIND"));
        u.credential_ref = r.str("CRED");
        u.status = static_cast<EntityStatus>(r.u64("STATUS"));
        u.profile_home_key = r.str("PROFHOME");
        u.stamp.valid_from = r.u64("VFROM"); u.stamp.valid_through = r.u64("VTHRU");
        u.stamp.row_version = r.u64("ROWVER");
        out.users.push_back(std::move(u));
    });

    ok = ok && scan("SYSMEMBER", [&](const RowR& r) {
        TeamMember m;
        m.id = r.id<TeamMemberId>("ID"); m.user_id = r.optid<UserId>("USERID");
        m.key = r.str("MKEY"); m.kind = static_cast<MemberKind>(r.u64("KIND"));
        m.default_role = r.optid<RoleId>("DEFROLE");
        m.default_permission_set = r.optid<PermissionSetId>("DEFPSET");
        m.status = static_cast<EntityStatus>(r.u64("STATUS"));
        m.stamp.valid_from = r.u64("VFROM"); m.stamp.valid_through = r.u64("VTHRU");
        m.stamp.row_version = r.u64("ROWVER");
        out.members.push_back(std::move(m));
    });

    ok = ok && scan("SYSROLE", [&](const RowR& r) {
        Role x;
        x.id = r.id<RoleId>("ID"); x.key = r.str("RKEY"); x.name = r.str("RNAME");
        x.kind = r.str("RKIND"); x.description = r.str("DESCR");
        x.status = static_cast<EntityStatus>(r.u64("STATUS"));
        out.roles.push_back(std::move(x));
    });

    ok = ok && scan("SYSPERM", [&](const RowR& r) {
        Permission p;
        p.id = r.id<PermissionId>("ID"); p.key = r.str("PKEY");
        p.resource_class = r.str("RESCLASS"); p.action = r.str("PACTION");
        p.risk = static_cast<RiskClass>(r.u64("RISK"));
        p.requires_approval = r.boolean("REQAPPR");
        p.status = static_cast<EntityStatus>(r.u64("STATUS"));
        out.permissions.push_back(std::move(p));
    });

    ok = ok && scan("SYSROLEPERM", [&](const RowR& r) {
        out.role_permissions.push_back({r.id<RoleId>("ROLEID"), r.id<PermissionId>("PERMID")});
    });

    ok = ok && scan("SYSMEMROLE", [&](const RowR& r) {
        MemberRole mr;
        mr.member = r.id<TeamMemberId>("MEMBERID"); mr.role = r.id<RoleId>("ROLEID");
        mr.org_scope = r.optid<OrgUnitId>("ORGSCOPE"); mr.work_scope = r.optid<WorkNodeId>("WORKSCOPE");
        out.member_roles.push_back(std::move(mr));
    });

    ok = ok && scan("SYSOVERRIDE", [&](const RowR& r) {
        MemberPermissionOverride ov;
        ov.member = r.id<TeamMemberId>("MEMBERID"); ov.permission = r.id<PermissionId>("PERMID");
        ov.effect = static_cast<OverrideEffect>(r.u64("EFFECT"));
        ov.org_scope = r.optid<OrgUnitId>("ORGSCOPE"); ov.work_scope = r.optid<WorkNodeId>("WORKSCOPE");
        out.overrides.push_back(std::move(ov));
    });

    ok = ok && scan("SYSASSIGN", [&](const RowR& r) {
        TeamAssignment as;
        as.id = r.id<AssignmentId>("ID"); as.member = r.id<TeamMemberId>("MEMBERID");
        as.org_unit = r.optid<OrgUnitId>("ORGUNIT"); as.work = r.optid<WorkNodeId>("WORK");
        as.role = r.optid<RoleId>("ROLE"); as.permission_set = r.optid<PermissionSetId>("PSET");
        as.reports_to = r.optid<AssignmentId>("REPORTSTO"); as.assignment_kind = r.str("AKIND");
        as.status = static_cast<EntityStatus>(r.u64("STATUS"));
        as.stamp.valid_from = r.u64("VFROM"); as.stamp.valid_through = r.u64("VTHRU");
        as.stamp.row_version = r.u64("ROWVER");
        out.assignments.push_back(std::move(as));
    });

    ok = ok && scan("SYSGRANT", [&](const RowR& r) {
        AuthorizationGrant g;
        g.id = r.id<AuthorizationId>("ID"); g.requested_by = r.id<TeamMemberId>("REQBY");
        g.granted_to = r.id<TeamMemberId>("GRANTTO"); g.role_assignment = r.optid<AssignmentId>("ROLEASN");
        g.work = r.optid<WorkNodeId>("WORK"); g.resource_scope = r.str("RESSCOPE");
        g.action_scope = r.str("ACTSCOPE"); g.risk = static_cast<RiskClass>(r.u64("RISK"));
        g.granted_at = r.u64("GRANTAT"); g.expires_at = r.u64("EXPAT");
        g.status = static_cast<GrantStatus>(r.u64("STATUS"));
        g.reason = r.str("REASON"); g.source_report_id = r.str("SRCREPORT");
        out.grants.push_back(std::move(g));
    });

    return ok;
}

} // namespace dottalk::identity
