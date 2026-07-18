from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ManualgenPaths:
    repo_root: Path
    manual_id: str = "developer"
    publication_workspace: str | None = None
    harvest_workspace: str | None = None

    @property
    def docs_root(self) -> Path:
        return self.repo_root / "docs"

    @property
    def manualgen_root(self) -> Path:
        return self.docs_root / "manuals" / self.manual_id / "manualgen"

    @property
    def reports_dir(self) -> Path:
        return self.manualgen_root / "reports"

    @property
    def manifests_dir(self) -> Path:
        return self.manualgen_root / "manifests"

    @property
    def logs_dir(self) -> Path:
        return self.manualgen_root / "logs"

    @property
    def run_logs_dir(self) -> Path:
        return self.logs_dir / "runs"

    @property
    def published_dir(self) -> Path:
        return self.manualgen_root / "published"

    @property
    def media_root(self) -> Path:
        return self.docs_root / "media"

    @property
    def mdo219_anchor_manifest(self) -> Path:
        return self.reports_dir / "mdo_219_media_anchor_manifest_v1.csv"

    def ensure_output_dirs(self) -> None:
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.manifests_dir.mkdir(parents=True, exist_ok=True)
        self.run_logs_dir.mkdir(parents=True, exist_ok=True)


def resolve_repo_root(raw: str | None) -> Path:
    root = Path(raw).expanduser().resolve() if raw else Path.cwd().resolve()
    return root
