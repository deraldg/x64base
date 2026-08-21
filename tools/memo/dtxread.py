#!/usr/bin/env python3
"""Read a DTX memo sidecar and unpack MINIDB 1 containers.

Owner: member.derald. Author: member.ai.claude.cowork. Lane: AIF-120. 2026-08-21.
Python 3 stdlib only, per AIF-085.

Written from include/memo/dtx_format.hpp (DtxHeader 4096, DtxObjectHeader 56)
and docs/maintenance/MEMO_RESIDENT_MINIDB_V1.md 2.1 (the container grammar).
Independent of the engine on purpose: if this and the engine agree, the format
is a format and not a habit.
"""
import struct, sys, os

HDR = '<4sHHIII QQQ QQ QQQ II 4004s'
OBJ = '<4sHH QQQ II QQ'
assert struct.calcsize(HDR) == 4096, struct.calcsize(HDR)
assert struct.calcsize(OBJ) == 56, struct.calcsize(OBJ)

def read_header(f):
    f.seek(0)
    v = struct.unpack(HDR, f.read(4096))
    return dict(magic=v[0], vmaj=v[1], vmin=v[2], header_bytes=v[3],
                object_align=v[4], file_flags=v[5], next_object_id=v[6],
                live=v[7], dead=v[8], first_object_offset=v[9],
                append_offset=v[10], crc32=v[13])

def objects(path):
    """Yield every object record in the store, in file order."""
    size = os.path.getsize(path)
    with open(path, 'rb') as f:
        h = read_header(f)
        if h['magic'] != b'DTX1':
            raise SystemExit('not a DTX store: %r' % h['magic'])
        align = h['object_align'] or 16
        off = h['first_object_offset']
        while off + 56 <= size:
            f.seek(off)
            v = struct.unpack(OBJ, f.read(56))
            if v[0] != b'OBJ1':
                break
            rec = dict(offset=off, tag=v[0], state=v[1], kind=v[2],
                       object_id=v[3], payload_bytes=v[4], logical_bytes=v[5],
                       crc32=v[6], previous_version_of=v[8])
            rec['payload_at'] = off + 56
            yield rec, f
            span = 56 + rec['payload_bytes']
            span = (span + align - 1) // align * align
            off += span

def payload(path, object_id):
    for rec, f in objects(path):
        if rec['object_id'] == object_id:
            f.seek(rec['payload_at'])
            return rec, f.read(rec['payload_bytes'])
    return None, None

def parse_minidb(blob):
    """MINIDB 1: length-prefixed sections. Returns (posture, [(path, bytes)])."""
    def line(i):
        j = blob.index(b'\n', i)
        return blob[i:j].decode('latin-1'), j + 1
    head, i = line(0)
    if head != 'MINIDB 1':
        raise ValueError('not a MINIDB 1 container: %r' % head[:40])
    posture, files = None, []
    while True:
        s, i = line(i)
        if s == 'END':
            break
        if s.startswith('POSTURE '):
            n = int(s.split()[1]); posture = blob[i:i+n]; i += n
        elif s.startswith('FILE '):
            _, n, rel = s.split(' ', 2)
            n = int(n); files.append((rel, blob[i:i+n])); i += n
        else:
            raise ValueError('unknown section: %r' % s[:60])
    return posture, files
