"""Create and validate portable provenance manifests for generated diagrams."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def normalized_sources(values: list[str], artifact: Path) -> list[str]:
    result: list[str] = []
    artifact_key = str(artifact.resolve()).casefold()
    for value in values:
        source = Path(value)
        key = str(source.resolve()).casefold()
        if key == artifact_key:
            raise ValueError("generated diagram cannot derive from itself")
        portable = source.as_posix()
        if portable not in result:
            result.append(portable)
    if not result:
        raise ValueError("at least one derived_from artifact is required")
    return result


def manifest(artifact: Path, sources: list[str], generator: str, status: str) -> dict[str, object]:
    return {
        "id": f"diagram.{artifact.stem}",
        "label": artifact.stem.replace("_", " ").title(),
        "kind": "diagram",
        "path": artifact.as_posix(),
        "status": status,
        "generator": generator,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "truth_status": "derived_view",
        "derived_from": normalized_sources(sources, artifact),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--derived-from", action="append", required=True)
    parser.add_argument("--generator", required=True)
    parser.add_argument("--status", default="generated")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.artifact.with_suffix(args.artifact.suffix + ".provenance.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest(args.artifact, args.derived_from, args.generator, args.status), indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
