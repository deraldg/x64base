#!/usr/bin/env python3
"""In-memory FakeArea implementing the crud.Area protocol.

Lets the CRUD logic run WITHOUT the win_amd64 pydottalk .pyd (which the steward
sandbox cannot load), so "test the tool, do not merely write it" (AIF-085) holds
even here. Rows are dicts of {FIELD: str}; deletion sets a per-row tombstone flag,
exactly as the DBF deleted byte behaves.
"""
from __future__ import annotations


class FakeArea:
    def __init__(self, spec):
        self._names = list(spec.field_names())
        self._rows: list[dict] = []      # each: {"_del": bool, **fields}
        self._cur = 0                    # 0-based cursor

    # seeding helper (tests only)
    def seed(self, rows: list[dict]):
        for r in rows:
            row = {"_del": False}
            row.update({n: str(r.get(n, "")) for n in self._names})
            self._rows.append(row)
        return self

    # --- protocol ---
    def rec_count(self):
        return len(self._rows)

    def top(self):
        self._cur = 0

    def skip(self, delta):
        self._cur += delta

    def goto_rec(self, recno):
        self._cur = recno - 1  # recno is 1-based

    def recno(self):
        return self._cur + 1

    def eof(self):
        return self._cur >= len(self._rows)

    def is_deleted(self):
        return self._rows[self._cur]["_del"]

    def get_field(self, name):
        return self._rows[self._cur].get(name.upper(), "")

    def set_field(self, name, value):
        up = name.upper()
        if up not in self._names:
            raise KeyError(up)
        self._rows[self._cur][up] = str(value)

    def append_blank(self):
        row = {"_del": False}
        row.update({n: "" for n in self._names})
        self._rows.append(row)
        self._cur = len(self._rows) - 1

    def write_current(self):
        pass  # in-memory; nothing to flush

    def delete_current(self):
        self._rows[self._cur]["_del"] = True

    def close(self):
        pass

    # test introspection
    def live_rows(self):
        return [{k: v for k, v in r.items() if k != "_del"}
                for r in self._rows if not r["_del"]]

    def all_rows(self):
        return list(self._rows)
