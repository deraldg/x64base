from __future__ import annotations

import json
import platform
import secrets
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .util import sha256_file, write_csv, write_json, relpath_posix


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_run_id(prefix: str = "MANRUN") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}-{stamp}-{secrets.token_hex(4).upper()}"


@dataclass
class RunLogger:
    paths: Any
    command: str
    run_id: str = field(default_factory=new_run_id)
    events: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    boundary_rows: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)

    @property
    def run_dir(self) -> Path:
        return self.paths.run_logs_dir / self.run_id

    def start(self) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.event("INFO", "run", "start", command=self.command, python=sys.version.split()[0])

    def event(self, level: str, stage: str, event: str, **data: Any) -> None:
        row = {
            "time": utc_now_iso(),
            "level": level,
            "stage": stage,
            "event": event,
        }
        row.update(data)
        self.events.append(row)

    def artifact(self, kind: str, path: Path, note: str = "") -> None:
        sha = sha256_file(path) if path.exists() and path.is_file() else ""
        row = {
            "artifact_kind": kind,
            "relative_path": relpath_posix(path, self.paths.repo_root),
            "sha256": sha,
            "note": note,
        }
        self.artifacts.append(row)
        self.event("ARTIFACT", kind, "write", path=row["relative_path"], sha256=sha)

    def boundary(self, name: str, value: int | str, status: str, note: str) -> None:
        row = {"boundary": name, "value": value, "status": status, "note": note}
        self.boundary_rows.append(row)
        self.event("BOUNDARY", "boundary", name, value=value, status=status)

    def error(self, stage: str, message: str, recovery: str = "") -> None:
        row = {"time": utc_now_iso(), "stage": stage, "message": message, "recovery": recovery}
        self.errors.append(row)
        self.event("ERROR", stage, "error", message=message, recovery=recovery)

    def close(self, status: str = "PASS") -> None:
        self.event("INFO", "run", "finish", status=status)
        events_path = self.run_dir / "events.jsonl"
        with events_path.open("w", encoding="utf-8") as f:
            for row in self.events:
                f.write(json.dumps(row, sort_keys=True) + "\n")
        write_csv(self.run_dir / "artifacts.csv", self.artifacts, ["artifact_kind", "relative_path", "sha256", "note"])
        write_csv(self.run_dir / "boundary.csv", self.boundary_rows, ["boundary", "value", "status", "note"])
        write_csv(self.run_dir / "errors.csv", self.errors, ["time", "stage", "message", "recovery"])
        summary = [
            {"metric": "run_id", "value": self.run_id, "note": "Structured manualgen run id."},
            {"metric": "command", "value": self.command, "note": "manualgen command."},
            {"metric": "event_rows", "value": len(self.events), "note": "events.jsonl rows."},
            {"metric": "artifact_rows", "value": len(self.artifacts), "note": "artifacts.csv rows."},
            {"metric": "boundary_rows", "value": len(self.boundary_rows), "note": "boundary.csv rows."},
            {"metric": "error_rows", "value": len(self.errors), "note": "errors.csv rows."},
            {"metric": "status", "value": status, "note": "Run close status."},
        ]
        write_csv(self.run_dir / "summary.csv", summary, ["metric", "value", "note"])
        run_manifest = {
            "run_id": self.run_id,
            "command": self.command,
            "status": status,
            "created_utc": utc_now_iso(),
            "python_version": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "repo_root": str(self.paths.repo_root),
            "event_rows": len(self.events),
            "artifact_rows": len(self.artifacts),
            "boundary_rows": len(self.boundary_rows),
            "error_rows": len(self.errors),
        }
        write_json(self.run_dir / "run.json", run_manifest)
