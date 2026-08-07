#!/usr/bin/env python3
"""Drift guard for session_coordinator.py -- exercises the quip primitive and the
claim allocator against a throwaway root. Stdlib only; run:

    python tools/coordination/test_session_coordinator.py

Exists so `quip` (added 2026-08-07, AIF-050) cannot rot silently: the coordinator
had no test, which is the exact drift this checks against.
"""
import importlib.util
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("sc", HERE / "session_coordinator.py")
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)


def _inbox_count(root, run):
    d = root / sc.QUIP_DIR / run
    return len(list(d.glob("*.quip"))) if d.exists() else 0


def test_quip_direct_and_broadcast_and_ack():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        sc.checkin(root, "m.a", "RUN-A", "", "")
        sc.checkin(root, "m.b", "RUN-B", "", "")

        # direct send A -> B
        assert sc.quip_send(root, "RUN-A", "RUN-B", "hold the manifest") == 0
        assert _inbox_count(root, "RUN-B") == 1
        assert _inbox_count(root, "RUN-A") == 0

        # broadcast B -> all (reaches A, not B itself)
        assert sc.quip_send(root, "RUN-B", "all", "checked in on VFP") == 0
        assert _inbox_count(root, "RUN-A") == 1
        assert _inbox_count(root, "RUN-B") == 1  # unchanged; sender excluded

        # read without ack leaves them; read with ack clears them
        assert sc.quip_read(root, "RUN-A", ack=False) == 0
        assert _inbox_count(root, "RUN-A") == 1
        assert sc.quip_read(root, "RUN-A", ack=True) == 0
        assert _inbox_count(root, "RUN-A") == 0

        # broadcast with no other active session -> exit 1
        sc.checkout(root, "RUN-A")
        assert sc.quip_send(root, "RUN-B", "all", "anyone?") == 1


def test_claim_is_atomic_and_unique():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        n1 = sc.claim_aif(root, "m.a", "RUN-A", "lane-one")
        n2 = sc.claim_aif(root, "m.b", "RUN-B", "lane-two")
        assert n1 is not None and n2 is not None and n1 != n2
        # re-claiming a specific taken number fails (no double-allocation)
        assert sc.claim_aif(root, "m.c", "RUN-C", "dup", want=n1) is None


if __name__ == "__main__":
    test_quip_direct_and_broadcast_and_ack()
    test_claim_is_atomic_and_unique()
    print("OK -- session_coordinator quip + claim tests passed")
