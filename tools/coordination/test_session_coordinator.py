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


def test_quip_ack_is_honest_when_unlink_fails():
    # The bug this guards: on a mount that refuses unlink, --ack must NOT claim
    # success. The old test only ran where unlink works, so it never saw this.
    import io, contextlib
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        sc.checkin(root, "m.a", "RUN-A", "", "")
        sc.quip_send(root, "RUN-A", "RUN-A", "self note")
        assert _inbox_count(root, "RUN-A") == 1

        orig_unlink = Path.unlink
        def refuse(self, *a, **k):
            raise OSError("simulated mount that refuses unlink")
        Path.unlink = refuse
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                sc.quip_read(root, "RUN-A", ack=True)
            out = buf.getvalue()
        finally:
            Path.unlink = orig_unlink

        assert "acked 0 of 1" in out, out          # honest count, not "acked 1"
        assert "NOT acked" in out, out             # the failure is surfaced
        assert _inbox_count(root, "RUN-A") == 1    # file genuinely still present


def test_quip_direct_warns_but_delivers_when_target_absent():
    # warn-and-deliver (AIF-096): a direct quip to a run that is NOT checked in must
    # still land (the run may return to this tree) but WARN and point to the durable
    # board. The old direct path dropped silently -- the misfire that put a quip in an
    # empty room. Control: a direct quip to a LIVE peer must NOT warn.
    import io, contextlib
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        sc.checkin(root, "m.a", "RUN-A", "", "")

        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            rc = sc.quip_send(root, "RUN-A", "RUN-GHOST", "you there?")
        err = buf.getvalue()
        assert rc == 0                               # delivered, not refused
        assert _inbox_count(root, "RUN-GHOST") == 1  # the drop really happened
        assert "not checked in" in err, err          # liveness warning fired
        assert "pseudo-chat board" in err, err       # points up the ladder

        sc.checkin(root, "m.b", "RUN-B", "", "")
        buf2 = io.StringIO()
        with contextlib.redirect_stderr(buf2):
            sc.quip_send(root, "RUN-A", "RUN-B", "hi")
        assert "not checked in" not in buf2.getvalue()  # live peer -> no warning


def test_wake_records_durable_lineage_and_survives_checkout():
    # The gap this closes (AIF-096): a checked-out session could not recover its own
    # birth time or parent, because presence is deleted at checkout and a chat has no
    # self-memory. Lineage is a TRACKED, write-once record -- it must survive checkout
    # and must NOT be rewritten when a resumed run wakes again.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        assert sc.wake(root, "m.a", "RUN-CHILD", parent="RUN-PARENT") == 0
        rec = root / sc.LINEAGE_DIR / "RUN-CHILD.yaml"
        assert rec.exists()
        body = rec.read_text()
        assert "parent: RUN-PARENT" in body
        born1 = [l for l in body.splitlines() if l.startswith("born_utc:")][0]

        # checkout deletes PRESENCE but not lineage (the durability point)
        sc.checkout(root, "RUN-CHILD")
        assert not (root / sc.SESS_DIR / "RUN-CHILD.yaml").exists()
        assert rec.exists()

        # re-wake (resumed run): birth + parent are write-once, unchanged
        sc.wake(root, "m.a", "RUN-CHILD", parent="SOMEONE-ELSE")
        body2 = rec.read_text()
        assert "parent: RUN-PARENT" in body2                  # not overwritten
        born2 = [l for l in body2.splitlines() if l.startswith("born_utc:")][0]
        assert born1 == born2                                 # birth preserved


def test_wake_whoami_reads_identity_from_the_record():
    import io, contextlib
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        n = sc.claim_aif(root, "m.a", "RUN-X", "lane-x")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sc.wake(root, "m.a", "RUN-X")            # no parent given
        out = buf.getvalue()
        assert f"AIF-{n:03d}" in out                 # whoami lists what the run holds
        assert "parent: none" in out                 # absent parent -> none, honestly


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
    test_quip_ack_is_honest_when_unlink_fails()
    test_quip_direct_warns_but_delivers_when_target_absent()
    test_wake_records_durable_lineage_and_survives_checkout()
    test_wake_whoami_reads_identity_from_the_record()
    test_claim_is_atomic_and_unique()
    print("OK -- session_coordinator quip + claim tests passed")
