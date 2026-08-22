#!/usr/bin/env python3
"""Depth census over MINIDB containers and the WORKSPACES catalog.

WHY THIS EXISTS
    AIF-120 R110 (docs/maintenance/AIF120_WORKSPACE_PATH_DEPTH_RULING_V1.md)
    rules on whether the memo-resident workspace case is genuinely NESTED --
    that is, whether anything in the live corpus needs a workspace address of
    depth > 1. The ruling's numbers come from this script, so the script ships
    with it. A ruling whose evidence cannot be re-run is an assertion.

WHY IT IS WRITTEN IN PYTHON
    On purpose, and independently. The container grammar is re-implemented from
    include/dottalk/minidb.hpp (the MINIDB 1 / POSTURE / FILE / END grammar),
    the memo record layout from include/memo/dtx_format.hpp (4096-byte DTX1
    header, 16-byte alignment, 56-byte OBJ1 records), and the table header from
    the X64 DBF layout. If this and the engine agree, the format is a format and
    not a habit. If they disagree, one of them is wrong and that is worth
    knowing.

WHAT IT DOES NOT DO
    It writes nothing. Every path is opened read-only.

USAGE
    minidb_depth_census.py containers <dir-of-container-payloads>
        Every *.bin in <dir> is treated as a raw MINIDB 1 payload. Reports the
        member census and flags any member that is itself a container or a
        posture -- i.e. a level below the hydrated workspace.

    minidb_depth_census.py objects <dir-of-container-payloads>
        One level deeper. A memo-resident workspace lives inside a .dtx OBJECT,
        not as a member file, so a file listing cannot see the recursion even
        when it is there. Unpacks every live object in every carried .dtx and
        classifies its payload.

    minidb_depth_census.py catalog <path-to-WORKSPACES.dbf>
        Reports the recursion columns of the live catalog: DEPTH, SELF_REF,
        PAYLOAD_SHA, plus FMT / MAX_AREAS / EST_HYD_B for cross-checking.

    minidb_depth_census.py all <dir-of-container-payloads> <WORKSPACES.dbf>
        All three, in order.

EXTRACTING THE PAYLOADS
    The container payloads are the SNAPSHOT memo of each MINIDB 1 row of the
    catalog. scripts/dtx_app.py reads a .dtx store; the payloads used by R110
    were written to tmp/minidb/NNN.bin, one file per object id.
"""

import collections
import os
import struct
import sys

DTX_HEADER = '<4sHHIII QQQ QQ QQQ II 4004s'
DTX_OBJECT = '<4sHH QQQ II QQ'
assert struct.calcsize(DTX_HEADER) == 4096, struct.calcsize(DTX_HEADER)
assert struct.calcsize(DTX_OBJECT) == 56, struct.calcsize(DTX_OBJECT)

CONTAINER_MAGIC = b'MINIDB 1\n'


# ---- the MINIDB 1 container grammar ---------------------------------------
# include/dottalk/minidb.hpp:26-28
#   MINIDB 1\n
#   POSTURE <len>\n<posture text bytes>
#   FILE <len> <relative-path>\n<file bytes>
#   END\n
# Length-prefixed and binary-safe: no byte of a member is ever scanned for a
# keyword, which is the whole reason the format is length-prefixed.

def scan_container(payload):
    """(posture_bytes, [(relpath, member_bytes), ...]) or None if not a container."""
    if not payload.startswith(CONTAINER_MAGIC):
        return None
    pos = len(CONTAINER_MAGIC)
    posture = b''
    members = []
    while pos < len(payload):
        nl = payload.find(b'\n', pos)
        if nl < 0:
            return None
        line = payload[pos:nl]
        pos = nl + 1
        if line.strip() == b'END':
            return posture, members
        parts = line.split(b' ', 2)
        keyword = parts[0]
        if keyword == b'POSTURE' and len(parts) >= 2:
            n = int(parts[1])
            posture = payload[pos:pos + n]
            pos += n
        elif keyword == b'FILE' and len(parts) >= 3:
            n = int(parts[1])
            members.append((parts[2].decode('latin-1'), payload[pos:pos + n]))
            pos += n
        else:
            return None
    # No END. minidb.hpp treats this as an error; so do we.
    return None


# ---- the DTX memo store ----------------------------------------------------

def dtx_header(blob):
    if len(blob) < 4096 or blob[:4] != b'DTX1':
        return None
    v = struct.unpack(DTX_HEADER, blob[:4096])
    return dict(next_object_id=v[6], live=v[7], dead=v[8],
                first_object_offset=v[9], object_align=v[4] or 16)


def dtx_objects(blob):
    """Yield every OBJ1 record in file order."""
    h = dtx_header(blob)
    if h is None:
        return
    off = h['first_object_offset']
    align = h['object_align']
    while off + 56 <= len(blob):
        o = struct.unpack(DTX_OBJECT, blob[off:off + 56])
        if o[0] != b'OBJ1':
            return
        yield dict(object_id=o[3], state=o[1], kind=o[2],
                   payload_bytes=o[4], logical_bytes=o[5],
                   payload=blob[off + 56: off + 56 + o[4]])
        off += ((56 + o[4]) + align - 1) // align * align


def classify(payload):
    if payload.startswith(CONTAINER_MAGIC):
        return 'MINIDB container'
    if payload[:12].upper().startswith(b'DTSHEMA'):
        return 'DTSHEMA posture'
    if payload[:4] == b'DTX1':
        return 'DTX store'
    return 'other/text'


def each_container(directory):
    for name in sorted(os.listdir(directory)):
        if not name.endswith('.bin'):
            continue
        with open(os.path.join(directory, name), 'rb') as f:
            payload = f.read()
        got = scan_container(payload)
        if got is not None:
            yield name, got[0], got[1]


# ---- census 1: the member census ------------------------------------------

def census_containers(directory):
    ext = collections.Counter()
    n = 0
    nested_containers = []
    nested_postures = []
    dtx_members = []
    for name, _posture, members in each_container(directory):
        n += 1
        for rel, blob in members:
            ext[os.path.splitext(rel)[1].lower() or '(none)'] += 1
            if blob.startswith(CONTAINER_MAGIC):
                nested_containers.append((name, rel))
            if blob[:12].upper().startswith(b'DTSHEMA'):
                nested_postures.append((name, rel))
            if rel.lower().endswith('.dtx'):
                dtx_members.append((name, rel, dtx_header(blob)))

    print('containers scanned          :', n)
    print('members total               :', sum(ext.values()))
    print('members by extension        :', dict(ext))
    print('members that ARE containers :', len(nested_containers))
    print('members that ARE postures   :', len(nested_postures))
    print('.dtx sidecar members        :', len(dtx_members))
    live = [d for d in dtx_members if d[2] and d[2]['live']]
    print('.dtx carrying a live object :', len(live))
    for name, rel in nested_containers + nested_postures:
        print('   NESTED: %s :: %s' % (name, rel))
    return len(nested_containers) + len(nested_postures)


# ---- census 2: one level below the member census ---------------------------

def census_objects(directory):
    kinds = collections.Counter()
    deep = []
    total = 0
    for name, _posture, members in each_container(directory):
        for rel, blob in members:
            if not rel.lower().endswith('.dtx'):
                continue
            for ob in dtx_objects(blob):
                total += 1
                k = classify(ob['payload'])
                kinds[(rel, k)] += 1
                if k in ('MINIDB container', 'DTSHEMA posture'):
                    deep.append((name, rel, ob['object_id'], k, ob['payload_bytes']))

    print('live memo objects inside carried .dtx members:', total)
    for (rel, k), count in sorted(kinds.items()):
        print('   %-20s %-18s %d' % (rel, k, count))
    print()
    print('DEPTH-3 OCCURRENCES (a workspace payload inside a container):', len(deep))
    for name, rel, oid, k, nbytes in deep[:20]:
        print('   %s :: %s obj=%s %s %d B' % (name, rel, oid, k, nbytes))
    return len(deep)


# ---- census 3: the live catalog -------------------------------------------
# The X64 header (version byte 0x64) prefixes the field-descriptor table, so
# descriptors are taken from WS_ID onward and offsets recomputed from the
# delete flag. Field NAMES are the on-disk 10-char forms (PAYLOAD_SH, not
# PAYLOAD_SHA) -- the truncation is the file's, not ours.

RECURSION_COLUMNS = ('DEPTH', 'SELF_REF', 'PAYLOAD_SH')
REPORT_COLUMNS = ('FMT', 'SUPERSEDED')


def census_catalog(path):
    with open(path, 'rb') as f:
        blob = f.read()
    version = blob[0]
    records = struct.unpack('<I', blob[4:8])[0]
    header_len = struct.unpack('<H', blob[8:10])[0]
    record_len = struct.unpack('<H', blob[10:12])[0]

    fields = []
    off = 32
    while off < header_len and blob[off] != 0x0D:
        name = blob[off:off + 11].split(b'\x00')[0].decode('latin-1')
        fields.append((name, chr(blob[off + 11]), blob[off + 16]))
        off += 32
    while fields and fields[0][0] != 'WS_ID':
        fields.pop(0)

    pos = {}
    o = 1  # past the delete flag
    for name, _t, length in fields:
        pos[name] = (o, length)
        o += length

    def get(rec, name):
        s, l = pos[name]
        return rec[s:s + l].decode('latin-1').strip()

    print('file        :', path)
    print('version     : 0x%02X   records: %d   record_len: %d' % (version, records, record_len))
    print('fields      :', ', '.join('%s(%s%d)' % f for f in fields))
    print()

    counters = {c: collections.Counter() for c in RECURSION_COLUMNS + REPORT_COLUMNS}
    max_areas = []
    est_set = 0
    n = 0
    for i in range(records):
        rec = blob[header_len + i * record_len: header_len + (i + 1) * record_len]
        if len(rec) < record_len:
            break
        n += 1
        for c in counters:
            if c in pos:
                counters[c][get(rec, c) or '(empty)'] += 1
        if 'MAX_AREAS' in pos and get(rec, 'MAX_AREAS'):
            max_areas.append(int(get(rec, 'MAX_AREAS')))
        if 'EST_HYD_B' in pos and get(rec, 'EST_HYD_B'):
            est_set += 1

    print('rows read   :', n)
    for c in RECURSION_COLUMNS:
        print('%-12s: %s' % (c, dict(counters[c])))
    for c in REPORT_COLUMNS:
        print('%-12s: %s' % (c, dict(counters[c])))
    if max_areas:
        print('%-12s: n=%d min=%d max=%d' % ('MAX_AREAS', len(max_areas), min(max_areas), max(max_areas)))
    print('%-12s: %d / %d rows populated' % ('EST_HYD_B', est_set, n))
    return n


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    verb = argv[1]
    if verb == 'containers' and len(argv) == 3:
        census_containers(argv[2])
    elif verb == 'objects' and len(argv) == 3:
        census_objects(argv[2])
    elif verb == 'catalog' and len(argv) == 3:
        census_catalog(argv[2])
    elif verb == 'all' and len(argv) == 4:
        print('== 1. member census ==')
        census_containers(argv[2])
        print()
        print('== 2. object census ==')
        census_objects(argv[2])
        print()
        print('== 3. catalog census ==')
        census_catalog(argv[3])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
