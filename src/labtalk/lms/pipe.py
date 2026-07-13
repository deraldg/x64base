"""Durable, provider-neutral message pipe for future LMS integrations.

This module deliberately does not contact an LMS. It establishes the message
and transport boundaries and supplies a local outbox that can be exercised
before a Moodle site, credentials, and approved operation mappings exist.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4


SCHEMA_VERSION = "labtalk.lms.message.v1"
MESSAGE_DIRECTIONS = frozenset({"outbound", "inbound"})


class TransportNotConfigured(RuntimeError):
    """Raised when live LMS delivery is attempted before it is configured."""


@dataclass(frozen=True)
class LmsMessage:
    """Versioned envelope exchanged at the LabTalk/LMS boundary."""

    operation: str
    subject: dict[str, Any]
    payload: dict[str, Any]
    provider: str = "moodle"
    direction: str = "outbound"
    correlation_id: str | None = None
    message_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported LMS message schema: {self.schema_version}")
        if not self.operation.strip():
            raise ValueError("LMS message operation must not be empty")
        if not self.provider.strip():
            raise ValueError("LMS message provider must not be empty")
        if self.direction not in MESSAGE_DIRECTIONS:
            raise ValueError(f"Unsupported LMS message direction: {self.direction}")
        if not isinstance(self.subject, dict) or not isinstance(self.payload, dict):
            raise ValueError("LMS message subject and payload must be objects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> LmsMessage:
        message = cls(**value)
        message.validate()
        return message


class LmsTransport(Protocol):
    """Contract a future Moodle or other LMS adapter must implement."""

    def send(self, message: LmsMessage) -> dict[str, Any]:
        """Deliver one message and return a provider receipt."""


class ReservedTransport:
    """Safe default transport: explicit status, never accidental delivery."""

    name = "reserved"
    live_delivery = False

    def send(self, message: LmsMessage) -> dict[str, Any]:
        message.validate()
        raise TransportNotConfigured(
            "Live LMS delivery is reserved for future work; the local outbox is active."
        )


class FileOutbox:
    """Append-only JSON outbox with atomic publication of each message."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def enqueue(self, message: LmsMessage) -> Path:
        data = message.to_dict()
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.root / f"{message.created_at[:10]}_{message.message_id}.json"
        temporary = self.root / f".{message.message_id}.tmp"
        body = json.dumps(data, indent=2, sort_keys=True) + "\n"

        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(body)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(target)
        finally:
            if temporary.exists():
                temporary.unlink()
        return target

    def pending_paths(self) -> list[Path]:
        if not self.root.exists():
            return []
        return sorted(path for path in self.root.glob("*.json") if path.is_file())

    def pending_messages(self) -> list[LmsMessage]:
        messages: list[LmsMessage] = []
        for path in self.pending_paths():
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError(f"Expected an object in LMS outbox file: {path}")
            messages.append(LmsMessage.from_dict(value))
        return messages

    def status(self, provider: str = "moodle") -> dict[str, Any]:
        return {
            "provider_candidate": provider,
            "transport": ReservedTransport.name,
            "live_delivery": ReservedTransport.live_delivery,
            "queue_path": str(self.root.resolve()),
            "queued_messages": len(self.pending_paths()),
            "schema_version": SCHEMA_VERSION,
        }
