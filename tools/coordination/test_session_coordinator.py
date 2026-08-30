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


def _seed_intake(root, numbers):
    """Give the throwaway root an ALLOCATION AUTHORITY.

    Before AIF-135 these tests ran against a bare directory, and the allocator
    happily minted AIF-006 into it. That is now a REFUSAL -- an empty universe
    is a broken path, not an empty project -- so a fixture that wants a number
    has to say which numbers are already spent, exactly as the real register
    does. The fixture had been hiding the very condition the tool must catch.
    """
    p = root / sc.INTAKE
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = "".join("| AIF-%03d | seeded row | lane |\n" % n for n in numbers)
    p.write_text("| id | subject | lane |\n|---|---|---|\n" + rows, encoding="utf-8")


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
        _seed_intake(root, [6, 7])
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
        _seed_intake(root, [6, 7, 8])
        n1 = sc.claim_aif(root, "m.a", "RUN-A", "lane-one")
        n2 = sc.claim_aif(root, "m.b", "RUN-B", "lane-two")
        assert n1 == 9 and n2 == 10                   # max+1, then max+1 again
        # re-claiming a specific taken number fails (no double-allocation)
        assert sc.claim_aif(root, "m.c", "RUN-C", "dup", want=n1) is None


def test_allocator_is_monotonic_and_never_fills_a_gap():
    """AIF-135, ruled 2026-08-30: max+1, never the lowest free number.

    The old rule walked from AIF_LO and took the first hole, which is how a
    live lane's number (AIF-043) was minted three times. Here 7, 8 and 9 are
    holes and the allocator must walk straight past all of them.
    """
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_intake(root, [6, 10])
        assert sc.next_aif_number(root) == 11
        assert sc.claim_aif(root, "m.a", "RUN-A", "lane") == 11
        assert sc.claim_aif(root, "m.b", "RUN-B", "lane") == 12
        assert not (root / sc.AIF_DIR / "AIF-007.claim").exists()


def test_a_number_cited_but_not_rowed_is_still_seen():
    """AIF-043's shape: three mentions inside other rows' Notes, no row of its
    own, no claim file. The narrow universe must still see it, or max+1 lands
    on it the moment it is the highest thing written down.
    """
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_intake(root, [6, 7])
        p = root / sc.INTAKE
        p.write_text(p.read_text(encoding="utf-8")
                     + "| AIF-007 | note mentioning AIF-020 | lane |\n", encoding="utf-8")
        assert 20 in sc.taken(root)
        assert sc.next_aif_number(root) == 21


def test_empty_authority_fails_closed():
    """A bare root is a BROKEN PATH, not an empty project. Returning AIF-006
    on it is the AIF-118 shape -- one answer for "unreadable" and for "fine" --
    inside the tool whose whole job is preventing collisions.
    """
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        assert sc.next_aif_number(root) is None
        assert sc.claim_aif(root, "m.a", "RUN-A", "lane") is None
        # and it refused WITHOUT writing a claim file
        assert list((root / sc.AIF_DIR).glob("AIF-*.claim")) == []


def test_number_cannot_skip_forward():
    """AIF-135 rule 3: --number mints only the next monotonic number. A hole
    made on purpose is still a hole, and the sequence cannot say why it exists.
    """
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_intake(root, [6, 7, 8])
        assert sc.claim_aif(root, "m.a", "RUN-A", "lane", want=40) is None
        assert list((root / sc.AIF_DIR).glob("AIF-*.claim")) == []
        assert sc.claim_aif(root, "m.a", "RUN-A", "lane", want=9) == 9


def test_backfill_of_an_existing_identity_must_be_explicit():
    """Writing the row before running the claim is how AIF-146 was burned.
    The allocator now makes re-declaring a known identity an explicit act.
    """
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_intake(root, [6, 7, 8])
        assert sc.claim_aif(root, "m.a", "RUN-A", "lane", want=8) is None
        assert sc.claim_aif(root, "m.a", "RUN-A", "lane", want=8,
                            backfill_existing=True) == 8


if __name__ == "__main__":
    test_quip_direct_and_broadcast_and_ack()
    test_quip_ack_is_honest_when_unlink_fails()
    test_quip_direct_warns_but_delivers_when_target_absent()
    test_wake_records_durable_lineage_and_survives_checkout()
    test_wake_whoami_reads_identity_from_the_record()
    test_claim_is_atomic_and_unique()
    test_allocator_is_monotonic_and_never_fills_a_gap()
    test_a_number_cited_but_not_rowed_is_still_seen()
    test_empty_authority_fails_closed()
    test_number_cannot_skip_forward()
    test_backfill_of_an_existing_identity_must_be_explicit()
    print("OK -- session_coordinator quip + claim tests passed")
