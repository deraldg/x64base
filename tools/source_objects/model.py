from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ContractBlock:
    kind: str
    version: str
    start_line: int
    end_line: int
    fields: dict[str, str] = field(default_factory=dict)
    raw_lines: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceSection:
    kind: str
    start_line: int
    end_line: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceObject:
    schema: str
    source_id: str
    identity_status: str
    path: str
    extension: str
    content_sha256: str
    line_count: int
    usage_contracts: list[ContractBlock]
    location_contract: ContractBlock | None
    declared_home: str | None
    actual_home: str
    canonical_path: str | None
    location_status: str
    project: str | None
    role: str | None
    date: str | None
    author: str | None
    last_modified_by: str | None
    last_modified_date: str | None
    working_tree_state: str
    metadata_provenance: dict[str, str]
    comment_sections: list[SourceSection]
    code_sections: list[SourceSection]
    findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "usage_contracts": [item.to_dict() for item in self.usage_contracts],
            "location_contract": (
                self.location_contract.to_dict() if self.location_contract else None
            ),
            "comment_sections": [item.to_dict() for item in self.comment_sections],
            "code_sections": [item.to_dict() for item in self.code_sections],
        }
