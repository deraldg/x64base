from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ManualgenEvent:
    time: str
    run_id: str
    level: str
    stage: str
    event: str
    message: str
    status: str = ""
    count: int | None = None
    artifact_id: str = ""
    path: str = ""
    details: dict[str, Any] | None = None


class JsonlLogger:
    """Structured JSONL event logger for manualgen runs."""

    def __init__(self, log_path: Path, run_id: str) -> None:
        self.log_path = log_path
        self.run_id = run_id
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def emit(
        self,
        *,
        level: str,
        stage: str,
        event: str,
        message: str,
        status: str = "",
        count: int | None = None,
        artifact_id: str = "",
        path: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        record = ManualgenEvent(
            time=datetime.now(timezone.utc).isoformat(),
            run_id=self.run_id,
            level=level,
            stage=stage,
            event=event,
            message=message,
            status=status,
            count=count,
            artifact_id=artifact_id,
            path=path,
            details=details,
        )
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), ensure_ascii=False, sort_keys=True) + "\n")

    def info(self, *, stage: str, event: str, message: str, **kwargs: Any) -> None:
        self.emit(level="INFO", stage=stage, event=event, message=message, **kwargs)

    def pass_event(self, *, stage: str, event: str, message: str, **kwargs: Any) -> None:
        self.emit(level="PASS", stage=stage, event=event, message=message, status="PASS", **kwargs)

    def boundary(self, *, stage: str, event: str, message: str, **kwargs: Any) -> None:
        self.emit(level="BOUNDARY", stage=stage, event=event, message=message, **kwargs)

    def error(self, *, stage: str, event: str, message: str, **kwargs: Any) -> None:
        self.emit(level="ERROR", stage=stage, event=event, message=message, status="FAIL", **kwargs)
