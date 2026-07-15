#!/usr/bin/env python3
"""Read-only runtime smoke for the selected engine/product composition."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str, output: str) -> None:
    if not condition:
        raise SystemExit(f"{message}\n--- dottalkpp output ---\n{output}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--index-mode", choices=("NONE", "LEGACY", "LMDB"), required=True)
    parser.add_argument(
        "--product",
        choices=("LEAN", "PROFESSIONAL", "EDUCATIONAL", "DEVELOPMENT"),
        required=True,
    )
    args = parser.parse_args()

    data = args.root.resolve() / "dottalkpp" / "data"
    dbf = data / "dbf" / "x32" / "STUDENTS.dbf"
    cnx = data / "indexes" / "x32" / "STUDENTS.cnx"
    before_dbf = digest(dbf)
    before_cnx = digest(cnx)

    commands = ["USE dbf\\x32\\students.dbf NOINDEX"]
    if args.index_mode == "NONE":
        commands.extend(("STATUS", "SEEK ANDERSON"))
    else:
        commands.extend(
            (
                "SETCNX indexes\\x32\\students.cnx",
                "SETORDER indexes\\x32\\students.cnx LNAME --asc",
                "SEEK ANDERSON",
                "LIST 1",
            )
        )
        commands.append("LMDB USAGE")

    if args.product in ("LEAN", "PROFESSIONAL"):
        commands.append("BIBLETALK")
    commands.append("QUIT")

    completed = subprocess.run(
        [str(args.exe.resolve())],
        cwd=data,
        input="\n".join(commands) + "\n",
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    output = completed.stdout + completed.stderr
    folded = output.casefold()

    require(completed.returncode == 0, "dottalkpp returned nonzero", output)
    require("opened students" in folded, "profile did not open the DBF", output)

    if args.index_mode == "NONE":
        require("none (table-only build)" in folded, "NONE did not report table-only", output)
        require("unknown command: seek" in folded, "NONE unexpectedly registered SEEK", output)
    else:
        require("set cnx: attached" in folded, "indexed profile did not attach CNX", output)
        require("set order: cnx tag 'lname'" in folded, "indexed profile did not select LNAME", output)
        require("anderson" in folded, "SEEK/LIST did not return Anderson", output)
        require("unknown command: seek" not in folded, "indexed profile omitted SEEK", output)

    if args.index_mode == "LEGACY":
        require("unknown command: lmdb" in folded, "LEGACY exposed LMDB commands", output)
    if args.index_mode == "LMDB":
        require("unknown command: lmdb" not in folded, "LMDB profile omitted LMDB commands", output)

    if args.product in ("LEAN", "PROFESSIONAL"):
        require("unknown command: bibletalk" in folded, "lean product exposed BIBLETALK", output)

    require(digest(dbf) == before_dbf, "profile smoke changed the DBF fixture", output)
    require(digest(cnx) == before_cnx, "profile smoke changed the CNX fixture", output)
    print(f"PASS: {args.product} + {args.index_mode} profile smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
