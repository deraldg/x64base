
#!/usr/bin/env python3
"""DotTalk++ / x64base manualgen entry point.

MDO-226: build/rebuild dry-run command.
Requires Python 3.12+.
"""

from __future__ import annotations

# MDO-256 MAN_CATALOG_CLI_HARDENING_BEGIN
# Read-only MAN* catalog CLI hardening layer.
# This block supersedes the MDO-255 skeleton and remains intentionally self-contained.
# It intercepts manualgen commands of the form:
#   manual catalog status|tables|counts|drift|export
#   manual sections|media|review
# It performs no DBF writes and no x64base import. Export writes report CSV/Markdown only.
def _mdo256_expected_counts():
    return {
        "MANRUN": 3,
        "MANSECTION": 25,
        "MANMEDIA": 9,
        "MANANCHOR": 9,
        "MANHASH": 13,
        "MANREVIEW": 3,
        "MANPUB": 4,
        "MANAPPX": 6,
    }


def _mdo256_repo_root(argv):
    import os
    for i, token in enumerate(argv):
        if token == "--repo-root" and i + 1 < len(argv):
            return os.path.abspath(argv[i + 1])
    return os.getcwd()


def _mdo256_paths(repo_root):
    import os
    root = os.path.join(repo_root, "docs", "manuals", "developer", "manualgen")
    accepted = os.path.join(root, "accepted_catalogs", "man_catalog_v1")
    return {
        "manualgen_root": root,
        "accepted_catalog_dir": accepted,
        "dbf_dir": os.path.join(accepted, "dbf"),
        "staging_csv_dir": os.path.join(accepted, "csv", "staging"),
        "execution_csv_dir": os.path.join(accepted, "csv", "execution"),
        "reports_dir": os.path.join(root, "reports"),
    }


def _mdo256_sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _mdo256_read_dbf_count(path):
    import struct
    try:
        with open(path, "rb") as f:
            data = f.read(12)
        if len(data) < 12:
            return -1
        return struct.unpack("<I", data[4:8])[0]
    except Exception:
        return -1


def _mdo256_read_dbf_header_info(path):
    import os
    import struct
    info = {
        "magic": "",
        "record_count": -1,
        "header_length": -1,
        "record_length": -1,
        "field_count": -1,
    }
    try:
        with open(path, "rb") as f:
            data = f.read(4096)
        if len(data) < 12:
            return info
        info["magic"] = hex(data[0])
        info["record_count"] = struct.unpack("<I", data[4:8])[0]
        info["header_length"] = struct.unpack("<H", data[8:10])[0]
        info["record_length"] = struct.unpack("<H", data[10:12])[0]
        # Standard DBF descriptors usually begin at 32; current x64base extended DBFs may begin at 96.
        candidates = []
        for start in (32, 96):
            count = 0
            pos = start
            while pos + 32 <= len(data):
                if data[pos] in (0x0D, 0x00):
                    break
                name_bytes = data[pos:pos+11].split(b"\x00", 1)[0]
                if not name_bytes:
                    break
                try:
                    name_bytes.decode("ascii")
                except Exception:
                    break
                count += 1
                pos += 32
            candidates.append(count)
        info["field_count"] = max(candidates)
        return info
    except Exception:
        return info


def _mdo256_table_rows(repo_root):
    import glob
    import os
    paths = _mdo256_paths(repo_root)
    dbf_dir = paths["dbf_dir"]
    expected = _mdo256_expected_counts()
    rows = []
    seen = set()
    for name in expected.keys():
        path = os.path.join(dbf_dir, name + ".dbf")
        exists = os.path.exists(path)
        info = _mdo256_read_dbf_header_info(path) if exists else {}
        count = int(info.get("record_count", -1)) if exists else -1
        size = os.path.getsize(path) if exists else 0
        sha = _mdo256_sha256(path) if exists else ""
        ok = bool(exists and count == expected[name])
        rows.append({
            "table": name,
            "expected": expected[name],
            "records": count,
            "exists": 1 if exists else 0,
            "bytes": size,
            "sha256": sha,
            "field_count": info.get("field_count", "") if exists else "",
            "record_length": info.get("record_length", "") if exists else "",
            "header_length": info.get("header_length", "") if exists else "",
            "pass": 1 if ok else 0,
            "failure_class": "" if ok else "COUNT_OR_TABLE_DRIFT",
            "path": path,
        })
        # Normalize the expected filename exactly as the discovery comparison
        # does below. Windows normally hides this mismatch, but the string
        # comparison is still case-sensitive and previously classified every
        # accepted MAN*.dbf as a second, "extra" table.
        seen.add((name + ".dbf").upper())
    if os.path.isdir(dbf_dir):
        for path in sorted(glob.glob(os.path.join(dbf_dir, "MAN*.dbf"))):
            base = os.path.basename(path)
            if base.upper() in seen:
                continue
            name = os.path.splitext(base)[0]
            info = _mdo256_read_dbf_header_info(path)
            rows.append({
                "table": name,
                "expected": "",
                "records": info.get("record_count", -1),
                "exists": 1,
                "bytes": os.path.getsize(path),
                "sha256": _mdo256_sha256(path),
                "field_count": info.get("field_count", ""),
                "record_length": info.get("record_length", ""),
                "header_length": info.get("header_length", ""),
                "pass": 0,
                "failure_class": "EXTRA_MAN_DBF",
                "path": path,
            })
    return paths, rows


def _mdo256_csv_print(rows, fieldnames=None):
    import csv
    import sys
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row.keys():
                if key not in fieldnames:
                    fieldnames.append(key)
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)


def _mdo256_read_csv(path):
    import csv
    import os
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _mdo256_table_csv(repo_root, table):
    import os
    paths = _mdo256_paths(repo_root)
    candidates = [
        os.path.join(paths["staging_csv_dir"], table + ".csv"),
        os.path.join(paths["execution_csv_dir"], table + ".csv"),
    ]
    for path in candidates:
        rows = _mdo256_read_csv(path)
        if rows:
            for row in rows:
                row.setdefault("source_csv", path)
            return path, rows
    return candidates[0], []


def _mdo256_export(repo_root, table_rows):
    import csv
    import os
    paths, _ = _mdo256_table_rows(repo_root)
    report_dir = paths["reports_dir"]
    os.makedirs(report_dir, exist_ok=True)
    table_csv = os.path.join(report_dir, "manual_catalog_cli_tables_v2.csv")
    drift_csv = os.path.join(report_dir, "manual_catalog_cli_drift_v2.csv")
    md_path = os.path.join(report_dir, "manual_catalog_cli_export_v2.md")
    fields = ["table", "expected", "records", "exists", "bytes", "pass", "failure_class", "field_count", "record_length", "header_length", "sha256", "path"]
    with open(table_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in table_rows:
            w.writerow(r)
    drift_rows = [r for r in table_rows if str(r.get("pass")) != "1"]
    with open(drift_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in drift_rows:
            w.writerow(r)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# MAN* Catalog CLI Export v2\n\n")
        f.write("Accepted catalog: `" + paths["accepted_catalog_dir"] + "`\n\n")
        f.write("| Table | Records | Expected | Pass | Failure |\n")
        f.write("|---|---:|---:|---:|---|\n")
        for r in table_rows:
            f.write("| {table} | {records} | {expected} | {pass} | {failure_class} |\n".format(**r))
        f.write("\nDrift failures: " + str(len(drift_rows)) + "\n")
    print("export_tables_csv=" + table_csv)
    print("export_drift_csv=" + drift_csv)
    print("export_md=" + md_path)


def _mdo256_handle_manual_catalog_cli():
    import sys
    argv = list(sys.argv[1:])
    lowered = [a.lower() for a in argv]
    commands = []
    if "manual" in lowered:
        i = lowered.index("manual")
        commands = lowered[i:]
    elif "manual-catalog-status" in lowered:
        commands = ["manual", "catalog", "status"]
    elif "manual-catalog-tables" in lowered:
        commands = ["manual", "catalog", "tables"]
    elif "manual-catalog-counts" in lowered:
        commands = ["manual", "catalog", "counts"]
    elif "manual-catalog-drift" in lowered:
        commands = ["manual", "catalog", "drift"]
    elif "manual-catalog-export" in lowered:
        commands = ["manual", "catalog", "export"]
    else:
        return False

    if not commands or commands[0] != "manual":
        return False

    repo_root = _mdo256_repo_root(sys.argv[1:])
    paths, rows = _mdo256_table_rows(repo_root)
    failures = [r for r in rows if str(r.get("pass")) != "1"]

    if len(commands) >= 3 and commands[1] == "catalog":
        action = commands[2]
        if action == "status":
            print("MAN* catalog status")
            print("accepted_catalog_dir=" + paths["accepted_catalog_dir"])
            print("accepted_dbf_dir=" + paths["dbf_dir"])
            print("tables_readback=" + str(len([r for r in rows if r.get("exists") == 1])))
            print("drift_failures=" + str(len(failures)))
            print("status=" + ("GREEN" if len(failures) == 0 else "DRIFT"))
            return True
        if action in ("tables", "counts"):
            _mdo256_csv_print(rows, ["table", "expected", "records", "exists", "bytes", "field_count", "record_length", "pass", "failure_class", "sha256", "path"])
            return True
        if action == "drift":
            _mdo256_csv_print(rows, ["table", "expected", "records", "exists", "pass", "failure_class", "path"])
            print("drift_failures=" + str(len(failures)))
            return True
        if action == "export":
            _mdo256_export(repo_root, rows)
            return True

    if len(commands) >= 2 and commands[1] == "sections":
        path, csv_rows = _mdo256_table_csv(repo_root, "MANSECTION")
        print("source_csv=" + path)
        if csv_rows:
            _mdo256_csv_print(csv_rows)
        else:
            _mdo256_csv_print([r for r in rows if r["table"] == "MANSECTION"])
        return True

    if len(commands) >= 2 and commands[1] == "media":
        media_path, media_rows = _mdo256_table_csv(repo_root, "MANMEDIA")
        anchor_path, anchor_rows = _mdo256_table_csv(repo_root, "MANANCHOR")
        print("media_source_csv=" + media_path)
        print("anchor_source_csv=" + anchor_path)
        merged = []
        for r in media_rows:
            rr = dict(r)
            rr["catalog_table"] = "MANMEDIA"
            merged.append(rr)
        for r in anchor_rows:
            rr = dict(r)
            rr["catalog_table"] = "MANANCHOR"
            merged.append(rr)
        if merged:
            _mdo256_csv_print(merged)
        else:
            _mdo256_csv_print([r for r in rows if r["table"] in ("MANMEDIA", "MANANCHOR")])
        return True

    if len(commands) >= 2 and commands[1] == "review":
        path, csv_rows = _mdo256_table_csv(repo_root, "MANREVIEW")
        print("source_csv=" + path)
        if csv_rows:
            _mdo256_csv_print(csv_rows)
        else:
            _mdo256_csv_print([r for r in rows if r["table"] == "MANREVIEW"])
        return True

    return False


if __name__ == "__main__":
    try:
        if _mdo256_handle_manual_catalog_cli():
            raise SystemExit(0)
    except SystemExit:
        raise
    except Exception as _mdo256_exc:
        import sys
        print("MDO-256 manual catalog CLI error: " + str(_mdo256_exc), file=sys.stderr)
        raise SystemExit(2)
# MDO-256 MAN_CATALOG_CLI_HARDENING_END




import sys

from manualgen_lib.commands import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

