from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

CCODE_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = CCODE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from labtalk.lms.pipe import (  # noqa: E402
    FileOutbox,
    LmsMessage,
    ReservedTransport,
    TransportNotConfigured,
)


class FileOutboxTests(unittest.TestCase):
    def test_enqueue_round_trips_a_versioned_message(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            outbox = FileOutbox(Path(directory))
            message = LmsMessage(
                operation="course.preview",
                subject={"course_key": "database-literacy"},
                payload={"title": "Database Literacy Starter"},
            )

            path = outbox.enqueue(message)
            stored = json.loads(path.read_text(encoding="utf-8"))

            self.assertEqual("labtalk.lms.message.v1", stored["schema_version"])
            self.assertEqual(message, outbox.pending_messages()[0])
            self.assertEqual(1, outbox.status()["queued_messages"])

    def test_rejects_an_empty_operation(self) -> None:
        with self.assertRaisesRegex(ValueError, "operation"):
            LmsMessage(operation=" ", subject={}, payload={}).validate()

    def test_reserved_transport_never_delivers(self) -> None:
        message = LmsMessage(operation="course.preview", subject={}, payload={})

        with self.assertRaises(TransportNotConfigured):
            ReservedTransport().send(message)


if __name__ == "__main__":
    unittest.main()
