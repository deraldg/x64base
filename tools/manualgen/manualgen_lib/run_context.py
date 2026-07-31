from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import uuid


@dataclass(frozen=True, slots=True)
class RunContext:
    run_id: str
    repo_root: Path
    stage: str
    run_dir: Path

    @classmethod
    def create(cls, repo_root: Path, stage: str) -> "RunContext":
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"MANRUN-{stamp}-{uuid.uuid4().hex[:8].upper()}"
        run_dir = repo_root / "docs" / "manuals" / "developer" / "manualgen" / "logs" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return cls(run_id=run_id, repo_root=repo_root, stage=stage, run_dir=run_dir)
