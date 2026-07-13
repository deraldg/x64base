"""Command-line interface for the reserved LabTalk LMS pipe."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__:
    from .pipe import FileOutbox, LmsMessage
else:  # Allow direct execution from the LabTalk portal.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from labtalk.lms.pipe import FileOutbox, LmsMessage


def json_object(value: str) -> dict[str, Any]:
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("expected a JSON object")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect or enqueue LabTalk LMS messages.")
    parser.add_argument("--queue", type=Path, required=True, help="Local outbox directory")
    parser.add_argument("--provider", default="moodle", help="Candidate LMS provider")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Show the reserved pipe status")
    subparsers.add_parser("list", help="List queued message envelopes")

    enqueue = subparsers.add_parser("enqueue", help="Add a message to the local outbox")
    enqueue.add_argument("--operation", required=True)
    enqueue.add_argument("--subject", type=json_object, default={})
    enqueue.add_argument("--payload", type=json_object, default={})
    enqueue.add_argument("--correlation-id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    outbox = FileOutbox(args.queue)

    if args.command == "status":
        print(json.dumps(outbox.status(args.provider), indent=2))
        return 0

    if args.command == "list":
        rows = [message.to_dict() for message in outbox.pending_messages()]
        print(json.dumps(rows, indent=2))
        return 0

    message = LmsMessage(
        operation=args.operation,
        subject=args.subject,
        payload=args.payload,
        provider=args.provider,
        correlation_id=args.correlation_id,
    )
    path = outbox.enqueue(message)
    result = {"queued": True, "message_id": message.message_id, "path": str(path)}
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
