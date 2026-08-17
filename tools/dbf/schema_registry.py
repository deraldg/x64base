#!/usr/bin/env python3
"""Per-table policy registry for the DBF CRUD (AIF-086, posture A).

One entry per SYS* table across the three catalogs the project dogfoods:
identity (data/metadata/identity), bbs (data/metadata/bbs), portal
(data/metadata/portal -- ruling + tracking). The CRUD engine (crud.py) is generic;
ALL the table-specific knowledge lives here as data:

  - subdir     : metadata subdirectory the .dbf lives in.
  - fields     : ordered (NAME, TYPE, LEN) triples, copied from the schema headers
                 (identity_schema.hpp / bbs_schema.hpp / ruling_schema.hpp /
                 tracking_schema.hpp). test_schema_registry.py reparses those
                 headers and fails if this drifts -- derived, not re-authored.
  - pk         : the N(20) monotonic id field, or None (pure crosswalks have none).
  - key        : the natural key used to LOCATE a row for update/close, or None.
  - ckey       : composite key tuple for crosswalks (no single natural key).
  - close      : soft-close policy (see ClosePolicy kinds below).
  - append_only: True => update-in-place is refused; history is a new row.
  - writable   : False => the CRUD refuses WRITES (bbs: dottalk_bbsd may hold the
                 store and pydottalk exposes NO lock -- see the capability review).

Soft-close ("delete" default) is policy-driven because the schemas are NOT uniform:
  - bitemporal : stamp VTHRU = now, bump ROWVER. Live filter = VTHRU in (0,'').
  - status     : set an enum field to its terminal code, stamp a close-epoch if the
                 table has one, bump ROWVER if present. Live filter = STATUS != term.
  - status_str : set a string state field to a terminal sentinel (a convention where
                 the schema ladder has no numeric terminal, e.g. SYSPROOF).
  - crosswalk  : no soft-close concept (a link either exists or does not). Soft
                 delete is refused; removal is --purge (the DBF tombstone).
  - append_term: append-only tables -- soft-close appends a NEW terminal row rather
                 than mutating in place (SYSRULING withdrawn, SYSRUN closed).

Grounding: pydottalk binds append/set/write/deleteCurrent only -- no LOCK, RECALL,
PACK, or COMMIT (PYDOTTALK_CAPABILITY_REVIEW_AND_CRUD_READINESS_V1.md). So --purge
here is the classic xBase deleted tombstone: irreversible via the binding and not
space-reclaiming. True undelete/compaction is an engine step (RECALL/PACK).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ClosePolicy:
    kind: str  # bitemporal | status | status_str | crosswalk | append_term
    field: Optional[str] = None       # STATUS / STATE / VTHRU target
    terminal: object = None           # terminal enum code (int) or sentinel (str)
    epoch: Optional[str] = None        # close-epoch field to stamp with now(), if any
    rowver: Optional[str] = None       # ROWVER field to bump, if any


@dataclass(frozen=True)
class TableSpec:
    name: str
    subdir: str
    fields: tuple           # ((NAME, TYPE, LEN), ...)
    close: ClosePolicy
    pk: Optional[str] = None
    key: Optional[str] = None
    ckey: tuple = ()
    append_only: bool = False
    writable: bool = True

    def field_names(self) -> tuple:
        return tuple(n for (n, _t, _l) in self.fields)

    def field_map(self) -> dict:
        return {n: (t, l) for (n, t, l) in self.fields}


# ---- field lists copied verbatim from the schema headers ----------------------
_ID = ("ID", "N", 20)


def _n(n, l=20):  # noqa: E743  (short by design; this is a data table)
    return (n, "N", l)


def _c(n, l):
    return (n, "C", l)


def _l(n):
    return (n, "L", 1)


IDENTITY = {
    "SYSUSER": TableSpec(
        "SYSUSER", "identity",
        (_ID, _c("UKEY", 64), _c("LOGIN", 32), _c("DISPLAY", 64), _n("AUTHKIND", 2),
         _c("CRED", 128), _n("STATUS", 2), _c("PROFHOME", 32),
         _n("VFROM"), _n("VTHRU"), _n("ROWVER")),
        ClosePolicy("bitemporal", field="VTHRU", rowver="ROWVER"),
        pk="ID", key="UKEY"),
    "SYSMEMBER": TableSpec(
        "SYSMEMBER", "identity",
        (_ID, _n("USERID"), _c("MKEY", 64), _n("KIND", 2), _n("DEFROLE"), _n("DEFPSET"),
         _n("STATUS", 2), _n("VFROM"), _n("VTHRU"), _n("ROWVER")),
        ClosePolicy("bitemporal", field="VTHRU", rowver="ROWVER"),
        pk="ID", key="MKEY"),
    "SYSROLE": TableSpec(
        "SYSROLE", "identity",
        (_ID, _c("RKEY", 48), _c("RNAME", 48), _c("RKIND", 24), _c("DESCR", 128),
         _n("STATUS", 2)),
        # No VTHRU/ROWVER; STATUS convention 0=active -> terminal 1=inactive.
        ClosePolicy("status", field="STATUS", terminal=1),
        pk="ID", key="RKEY"),
    "SYSPERM": TableSpec(
        "SYSPERM", "identity",
        (_ID, _c("PKEY", 48), _c("RESCLASS", 24), _c("PACTION", 24), _n("RISK", 2),
         _l("REQAPPR"), _n("STATUS", 2)),
        ClosePolicy("status", field="STATUS", terminal=1),
        pk="ID", key="PKEY"),
    "SYSROLEPERM": TableSpec(
        "SYSROLEPERM", "identity",
        (_n("ROLEID"), _n("PERMID")),
        ClosePolicy("crosswalk"),
        ckey=("ROLEID", "PERMID")),
    "SYSMEMROLE": TableSpec(
        "SYSMEMROLE", "identity",
        (_n("MEMBERID"), _n("ROLEID"), _n("ORGSCOPE"), _n("WORKSCOPE")),
        ClosePolicy("crosswalk"),
        ckey=("MEMBERID", "ROLEID")),
    "SYSOVERRIDE": TableSpec(
        "SYSOVERRIDE", "identity",
        (_n("MEMBERID"), _n("PERMID"), _n("EFFECT", 2), _n("ORGSCOPE"), _n("WORKSCOPE")),
        ClosePolicy("crosswalk"),
        ckey=("MEMBERID", "PERMID")),
    "SYSASSIGN": TableSpec(
        "SYSASSIGN", "identity",
        (_ID, _n("MEMBERID"), _n("ORGUNIT"), _n("WORK"), _n("ROLE"), _n("PSET"),
         _n("REPORTSTO"), _c("AKIND", 24), _n("STATUS", 2),
         _n("VFROM"), _n("VTHRU"), _n("ROWVER")),
        ClosePolicy("bitemporal", field="VTHRU", rowver="ROWVER"),
        pk="ID", key=None),
    "SYSGRANT": TableSpec(
        "SYSGRANT", "identity",
        (_ID, _n("REQBY"), _n("GRANTTO"), _n("ROLEASN"), _n("WORK"), _c("RESSCOPE", 48),
         _c("ACTSCOPE", 48), _n("RISK", 2), _n("GRANTAT"), _n("EXPAT"), _n("STATUS", 2),
         _c("REASON", 160), _c("SRCREPORT", 48)),
        # Grants expire; soft-close stamps EXPAT and sets STATUS terminal (2 = revoked
        # by convention; the ladder is not documented in the header, flagged).
        ClosePolicy("status", field="STATUS", terminal=2, epoch="EXPAT"),
        pk="ID", key=None),
}

BBS = {
    "SYSBOARD": TableSpec(
        "SYSBOARD", "bbs",
        (_ID, _c("BKEY", 64), _c("NAME", 48), _n("KIND", 2), _c("POSTPERM", 64),
         _n("STATUS", 2), _n("VFROM"), _n("VTHRU"), _n("ROWVER")),
        ClosePolicy("bitemporal", field="VTHRU", rowver="ROWVER"),
        pk="ID", key="BKEY", writable=False),
    "SYSTHREAD": TableSpec(
        "SYSTHREAD", "bbs",
        (_ID, _n("BOARDID"), _c("SUBJECT", 160), _n("OPENEDBY"), _n("OPENAT"),
         _n("STATE", 2), _n("LASTPOST")),
        ClosePolicy("status", field="STATE", terminal=2),  # 2 = closed
        pk="ID", key=None, writable=False),
    "SYSPOST": TableSpec(
        "SYSPOST", "bbs",
        (_ID, _n("BOARDID"), _n("THREADID"), _n("AUTHORID"), _n("AUTHKIND", 2),
         _n("KIND", 2), _c("BODY", 240), _n("REFGRANT"), _c("RUNID", 48),
         _n("POSTAT"), _n("STATUS", 2)),
        ClosePolicy("status", field="STATUS", terminal=1),  # 1 = redacted
        pk="ID", key=None, append_only=True, writable=False),
}

PORTAL = {
    "SYSRULING": TableSpec(
        "SYSRULING", "portal",
        (_ID, _c("RULEID", 16), _c("LANE", 12), _c("RULEGROUP", 24), _n("STATUS", 2),
         _n("DECIDEDAT"), _n("DECIDEDBY"), _n("PROPOSEDAT"), _c("STEWARD", 64),
         _c("SUPERBY", 16), _c("BLOCKS", 64), _c("NOTE", 240), _n("ROWVER")),
        # Append-only ladder: withdraw = a NEW row, STATUS 4, later DECIDEDAT.
        ClosePolicy("append_term", field="STATUS", terminal=4, epoch="DECIDEDAT",
                    rowver="ROWVER"),
        pk="ID", key="RULEID", append_only=True),
    "SYSLANE": TableSpec(
        "SYSLANE", "portal",
        (_ID, _c("LKEY", 16), _c("TITLE", 160), _c("OWNERKEY", 64), _c("STEWARDKEY", 64),
         _c("PROJECT", 48), _c("SDLCLANE", 24), _n("STATUS", 2), _l("CLAIMED"),
         _c("ANCHOR", 160), _n("OPENAT"), _n("CLOSEAT"), _n("ROWVER")),
        ClosePolicy("status", field="STATUS", terminal=4, epoch="CLOSEAT",
                    rowver="ROWVER"),  # 4 = closed
        pk="ID", key="LKEY"),
    "SYSRUN": TableSpec(
        "SYSRUN", "portal",
        (_ID, _c("RKEY", 48), _c("MEMBERKEY", 64), _c("ROLE", 24), _c("OWNERKEY", 64),
         _c("COMMITKEY", 64), _c("AUTHORKEY", 64), _c("PLANKEY", 64), _c("PROJECT", 48),
         _n("STATUS", 2), _n("STARTAT"), _c("BRANCH", 48), _c("HANDLE", 48),
         _c("REPORT", 48), _n("ROWVER")),
        ClosePolicy("append_term", field="STATUS", terminal=1, rowver="ROWVER"),
        pk="ID", key="RKEY", append_only=True),
    "SYSRUNLANE": TableSpec(
        "SYSRUNLANE", "portal",
        (_c("RUNKEY", 48), _c("LANEKEY", 16)),
        ClosePolicy("crosswalk"),
        ckey=("RUNKEY", "LANEKEY")),
    "SYSPROOF": TableSpec(
        "SYSPROOF", "portal",
        (_ID, _c("PKEY", 64), _c("LABEL", 160), _c("STATE", 24), _c("LANEKEY", 16),
         _c("SOURCE", 160), _n("OBSAT"), _n("ROWVER")),
        # STATE ladder has no numeric terminal; "retired" is a soft-close convention.
        ClosePolicy("status_str", field="STATE", terminal="retired", rowver="ROWVER"),
        pk="ID", key="PKEY"),
    "SYSTASK": TableSpec(
        "SYSTASK", "portal",
        (_ID, _c("TKEY", 48), _c("TITLE", 160), _c("ASSIGNKEY", 64), _n("STATUS", 2),
         _c("CHANNEL", 24), _c("LANEKEY", 16), _n("DUEAT"), _n("DONEAT"), _n("ROWVER")),
        ClosePolicy("status", field="STATUS", terminal=2, epoch="DONEAT",
                    rowver="ROWVER"),  # 2 = done
        pk="ID", key="TKEY"),
}

# ---- selfdoc catalogs (command / message / help self-documentation) -----------
# Registered read-only (writable=False): these are candidate-writer projections
# owned by the metacollect pipeline, so the CRUD reads + reports them but refuses
# writes -- exactly as it does for the daemon-owned bbs store. Field lists are
# DERIVED from the .dtschema contracts under data/schemas/**; the sibling test
# tools/dbf/tests/test_schema_registry_selfdoc.py reparses those contracts and
# fails on drift. subdir="" because the selfdoc .dbf files live in data/metadata/
# directly, not in a per-catalog subdirectory.
#
# R1 scope (SELFDOC_PORTAL_SCHEMA_SHARING_STUDY_V1): SYSCMD lands first because it
# satisfies every existing house invariant unchanged. The next catalog, SYSMSG,
# carries VER_AT as C(24); test_id_and_epoch_widths expects any *AT field to be
# N(20). That divergence IS study finding R5 (selfdoc VER_AT string vs portal
# N(20) epoch) and must be decided -- adopt the N(20) epoch, or exempt selfdoc's
# display stamp -- before SYSMSG and the remaining catalogs register here.
SELFDOC = {
    "SYSCMD": TableSpec(
        "SYSCMD", "",
        (_c("CMD_ID", 32), _c("CAN_NAME", 80), _c("TYPE", 20), _c("VIS", 20),
         _c("HANDLER", 96), _l("ACTIVE")),
        # ACTIVE L is the soft-close signal: close = set ACTIVE .F. (status kind,
        # terminal False). This catalog carries no numeric epoch/rowver.
        ClosePolicy("status", field="ACTIVE", terminal=False),
        pk="CMD_ID", key="CAN_NAME", writable=False),
}

TABLES: dict = {**IDENTITY, **BBS, **PORTAL, **SELFDOC}


def get(name: str) -> TableSpec:
    key = name.upper()
    if key not in TABLES:
        raise KeyError(f"unknown table: {name} (known: {', '.join(sorted(TABLES))})")
    return TABLES[key]


def writable_tables() -> list:
    return sorted(n for n, s in TABLES.items() if s.writable)


def readonly_tables() -> list:
    return sorted(n for n, s in TABLES.items() if not s.writable)
