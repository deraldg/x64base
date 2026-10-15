#!/usr/bin/env python3
"""Prove both DOTREF help routes address every live catalog member exactly."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SCHEMA = "dottalk.dotref.router_parity.v1"
EXPECTED_PROJECTION_SHA256 = (
    "2184A0085DA4D617863EC01373E16191B3D7FE86E466D4BDC756A077CAE2DCD3"
)


class VerificationError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def confined(root: Path, value: str, *, must_exist: bool) -> Path:
    path = (root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise VerificationError(f"PATH_OUTSIDE_REPOSITORY:{path}") from exc
    if must_exist and not path.is_file():
        raise VerificationError(f"INPUT_MISSING:{path}")
    return path


def write_text_new(path: Path, value: str) -> None:
    if path.exists():
        raise VerificationError(f"PROOF_OUTPUT_ALREADY_EXISTS:{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def run_capture(command: list[str], root: Path, log: Path) -> None:
    if log.exists():
        raise VerificationError(f"PROOF_OUTPUT_ALREADY_EXISTS:{log}")
    completed = subprocess.run(
        command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        check=False,
    )
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_bytes(completed.stdout)
    if completed.returncode != 0:
        raise VerificationError(
            f"COMMAND_FAILED:{completed.returncode}:{' '.join(command)}:{log}"
        )


def load_header_parser(root: Path):
    path = root / "dottalkpp/tools/help/generate_dotref_from_metadata_v1.py"
    spec = importlib.util.spec_from_file_location("dotref_router_parity_parser", path)
    if spec is None or spec.loader is None:
        raise VerificationError(f"HEADER_PARSER_LOAD_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_approved_projection(path: Path, header_parser: Any) -> list[Any]:
    actual_hash = sha256_file(path)
    if actual_hash != EXPECTED_PROJECTION_SHA256:
        raise VerificationError(
            f"PROJECTION_HASH_MISMATCH:{actual_hash}!={EXPECTED_PROJECTION_SHA256}"
        )
    text = path.read_text(encoding="utf-8")
    rows = [
        header_parser._parse_entry(entry)
        for entry in header_parser._iter_entries(text)
    ]
    names = [row.name for row in rows]
    if not names or len(names) != len(set(names)) or any(not name for name in names):
        raise VerificationError(
            f"INVALID_APPROVED_MEMBER_SET:{len(names)}:{len(set(names))}"
        )
    return rows


def structured_members(text: str, items: list[Any]) -> list[str]:
    syntax_by_name = {item.name: item.syntax for item in items}
    lines = text.splitlines()
    observed: list[str] = []
    for index, line in enumerate(lines[:-1]):
        syntax = syntax_by_name.get(line)
        if syntax is not None and lines[index + 1] == "  " + syntax:
            observed.append(line)
    return observed


def run_member_probe(
    root: Path, out: Path, executable: Path, items: list[Any],
    prefix: str, stem: str,
) -> dict[str, Any]:
    names = [item.name for item in items]
    script = out / f"{stem}.dts"
    alternate = out / f"{stem}.txt"
    console = out / f"{stem}.console.txt"
    relative_alt = str(alternate.relative_to(root)).replace("/", "\\")
    commands = [
        "* AIF-171 generated read-only DOTREF router parity probe.",
        f"SET ALTERNATE TO {relative_alt}",
        "SET ALTERNATE ON",
        *(f"{prefix} {name}" for name in names),
        "SET ALTERNATE OFF",
        "QUIT",
    ]
    write_text_new(script, "\n".join(commands) + "\n")
    run_capture([str(executable), "--script", str(script)], root, console)
    if not alternate.is_file():
        raise VerificationError(f"ALTERNATE_LOG_MISSING:{alternate}")
    observed = structured_members(
        alternate.read_text(encoding="utf-8", errors="replace"), items
    )
    if observed != names:
        raise VerificationError(
            f"{stem.upper()}_MEMBER_DIFF:"
            f"missing={sorted(set(names) - set(observed))}:"
            f"unexpected={sorted(set(observed) - set(names))}:"
            f"order_equal={observed == names}"
        )
    return {
        "members": len(observed),
        "script_sha256": sha256_file(script),
        "alternate_sha256": sha256_file(alternate),
        "console_sha256": sha256_file(console),
    }


def run_compatibility_probe(
    root: Path, out: Path, executable: Path,
) -> dict[str, Any]:
    script = out / "compatibility_probe.dts"
    log = out / "compatibility_probe.txt"
    commands = [
        "* AIF-171 preserved compatibility probe.",
        "DOTHELP USAGE",
        "DOTHELP ?",
        "HELP PREDICATES",
        "SET VAR routecheck = retained",
        "SHOW VAR routecheck",
        "CLEAR VAR routecheck",
        "SHOW VAR routecheck",
        "SET VAR! routebang = 40 + 2",
        "SHOW VAR routebang",
        "CLEAR VAR routebang",
        "SHOW VAR routebang",
        "QUIT",
    ]
    write_text_new(script, "\n".join(commands) + "\n")
    run_capture([str(executable), "--script", str(script)], root, log)
    text = log.read_text(encoding="utf-8", errors="replace")
    required = [
        "DOTHELP USAGE",
        "DOTHELP <term>",
        "Predicate help (COUNT/LOCATE)",
        "ROUTECHECK = retained",
        "VAR not defined: routecheck",
        "ROUTEBANG = 42",
        "VAR not defined: routebang",
    ]
    missing = [marker for marker in required if marker not in text]
    if missing:
        raise VerificationError(f"COMPATIBILITY_MARKERS_MISSING:{missing}")
    if text.count("  DOTHELP USAGE") != 2:
        raise VerificationError(
            f"DOTHELP_USAGE_PATH_COUNT:{text.count('  DOTHELP USAGE')}!=2"
        )
    forbidden = ["Usage: SET VAR | SHOW VAR | CLEAR VAR"]
    present = [marker for marker in forbidden if marker in text]
    if present:
        raise VerificationError(f"COMPATIBILITY_FORBIDDEN_MARKERS:{present}")
    return {
        "required_markers": len(required) + 1,
        "forbidden_markers": 0,
        "script_sha256": sha256_file(script),
        "log_sha256": sha256_file(log),
    }


def run_validation_tools(root: Path, out: Path, build_dir: Path) -> dict[str, Any]:
    checks = {
        "help_router_ctest": [
            "ctest", "--test-dir", str(build_dir), "-C", "Release",
            "-R", "^dottalkpp_help_router_test$", "--output-on-failure",
        ],
        "refcheck_selftest": [
            sys.executable, "tools/fullstack_docs/refcheck_v1.py", "--root", ".",
            "--selftest",
        ],
        "refcheck_live": [
            sys.executable, "tools/fullstack_docs/refcheck_v1.py", "--root", ".",
        ],
        "normcheck": [
            sys.executable, "tools/fullstack_docs/normcheck_v1.py", ".",
        ],
    }
    results: dict[str, Any] = {}
    for name, command in checks.items():
        log = out / f"{name}.txt"
        run_capture(command, root, log)
        results[name] = {"sha256": sha256_file(log), "bytes": log.stat().st_size}
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--executable", default="build/src/Release/dottalkpp.exe")
    parser.add_argument("--header", default="include/dotref.hpp")
    parser.add_argument("--build-dir", default="build")
    parser.add_argument(
        "--candidate",
        default=(
            "docs/maintenance/lanes/full_stack_documentation/runs/"
            "DOCFLUSH-20261013-002/dotref_m3/m3d_pilot_v1/run_a/candidate/"
            "include/dotref_catalog.generated.inc"
        ),
    )
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    try:
        executable = confined(root, args.executable, must_exist=True)
        header = confined(root, args.header, must_exist=True)
        candidate = confined(root, args.candidate, must_exist=True)
        build_dir = (root / args.build_dir).resolve()
        try:
            build_dir.relative_to(root)
        except ValueError as exc:
            raise VerificationError(f"PATH_OUTSIDE_REPOSITORY:{build_dir}") from exc
        if not build_dir.is_dir():
            raise VerificationError(f"BUILD_DIR_MISSING:{build_dir}")
        out = confined(root, args.out, must_exist=False)
        if out.exists():
            raise VerificationError(f"PROOF_OUTPUT_ALREADY_EXISTS:{out}")
        out.mkdir(parents=True)

        header_parser = load_header_parser(root)
        _prefix, items, _suffix = header_parser.parse_header(
            header.read_text(encoding="utf-8")
        )
        candidate_rows = read_approved_projection(candidate, header_parser)
        names = [item.name for item in items]
        if not names or len(names) != len(set(names)):
            raise VerificationError(
                f"INVALID_LIVE_MEMBER_SET:{len(names)}:{len(set(names))}"
            )
        header_projection = [
            (item.name, item.syntax, item.summary, "T" if item.supported else "F")
            for item in items
        ]
        approved_projection = [
            (row.name, row.syntax, row.summary, "T" if row.supported else "F")
            for row in candidate_rows
        ]
        if header_projection != approved_projection:
            raise VerificationError("LIVE_HEADER_DIFFERS_FROM_APPROVED_CANDIDATE")

        dothelp = run_member_probe(root, out, executable, items, "DOTHELP", "dothelp")
        help_dot = run_member_probe(root, out, executable, items, "HELP /DOT", "help_dot")
        compatibility = run_compatibility_probe(root, out, executable)
        validations = run_validation_tools(root, out, build_dir)
        summary = {
            "schema": SCHEMA,
            "status": "PASS",
            "catalog_members": len(names),
            "approved_projection_sha256": sha256_file(candidate),
            "header_sha256": sha256_file(header),
            "executable_sha256": sha256_file(executable),
            "dothelp_exact": dothelp,
            "help_dot_exact": help_dot,
            "compatibility": compatibility,
            "validations": validations,
            "router_exceptions": [],
        }
        summary_path = out / "router_parity_summary.json"
        summary_path.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n",
        )
        print(
            "DOTREF ROUTER PARITY: PASS -- "
            f"DOTHELP={dothelp['members']} HELP/DOT={help_dot['members']}"
        )
        print(summary_path)
        return 0
    except (VerificationError, OSError, ValueError, KeyError) as exc:
        print(f"DOTREF ROUTER PARITY: FAIL -- {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
