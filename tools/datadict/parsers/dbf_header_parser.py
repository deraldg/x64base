#!/usr/bin/env python3
"""
dd017_dbf_header_parser.py

Report-only static DBF/x64-style DBF header parser for DotTalk++ / x64base data-dictionary work.

This tool reads DBF-like files from a path and emits JSON/CSV physical dictionary projections.
It does not open tables through DotTalk++, does not mutate data, and does not claim runtime proof.

Supported static evidence levels:
  - STANDARD_DBF_HEADER_STATIC: conventional DBF header/field descriptors at offset 32.
  - X64BASE_EXTENDED_HEADER_STATIC: x64-style header prefix with descriptors at offset 96.

The x64-style layout is intentionally conservative and based on observed project evidence:
  byte 0      : version/flavor marker, often 0x64 for x64-prepped DBF
  bytes 1..3 : YY MM DD
  offset 0x20: 64-bit record count mirror
  offset 0x28: 64-bit header length mirror
  offset 0x30: 64-bit record length mirror
  offset 0x60: field descriptor area
  descriptor : 11-byte name, 1-byte type, 8-byte offset, 8-byte length, remaining bytes reserved

If a file does not fit either layout, the parser emits a warning rather than guessing.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import struct
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

STANDARD_DESCRIPTOR_OFFSET = 32
X64_DESCRIPTOR_OFFSET = 96
DBF_TERMINATOR = 0x0D

@dataclass
class ParsedField:
    table_id: str
    field_id: str
    ordinal: int
    field_name: str
    field_type: str
    offset: Optional[int]
    width: Optional[int]
    decimals: Optional[int]
    descriptor_offset: int
    descriptor_kind: str
    evidence_kind: str
    trust_level: str
    warnings: List[str]

@dataclass
class ParsedTable:
    table_id: str
    path: str
    file_name: str
    sha256: str
    file_size: int
    header_kind: str
    version_byte: int
    date_yy: Optional[int]
    date_mm: Optional[int]
    date_dd: Optional[int]
    record_count: Optional[int]
    header_length: Optional[int]
    record_length: Optional[int]
    descriptor_offset: int
    field_count: int
    terminator_offset: Optional[int]
    evidence_kind: str
    trust_level: str
    warnings: List[str]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def c_name(raw: bytes) -> str:
    return raw.split(b'\x00', 1)[0].decode('ascii', errors='replace').strip()


def u16(data: bytes, off: int) -> Optional[int]:
    if off + 2 <= len(data):
        return struct.unpack_from('<H', data, off)[0]
    return None


def u32(data: bytes, off: int) -> Optional[int]:
    if off + 4 <= len(data):
        return struct.unpack_from('<I', data, off)[0]
    return None


def u64(data: bytes, off: int) -> Optional[int]:
    if off + 8 <= len(data):
        return struct.unpack_from('<Q', data, off)[0]
    return None


def find_terminator(data: bytes, start: int, max_end: int) -> Optional[int]:
    end = min(max_end, len(data))
    for i in range(start, end):
        if data[i] == DBF_TERMINATOR:
            return i
    return None


def plausible_field_type(t: int) -> bool:
    return chr(t) in set('CNDLMFYIBTGOVPQXZ@+0')


def detect_header_kind(data: bytes) -> Tuple[str, int, List[str]]:
    warnings: List[str] = []
    if len(data) < 32:
        return 'UNKNOWN_TOO_SMALL', STANDARD_DESCRIPTOR_OFFSET, ['file smaller than standard DBF header']

    version = data[0]
    std_header_len = u16(data, 8) or 0
    x64_header_len = u64(data, 0x28) or 0
    x64_record_len = u64(data, 0x30) or 0

    x64_term = find_terminator(data, X64_DESCRIPTOR_OFFSET, x64_header_len + 1 if x64_header_len else min(len(data), 4096))
    std_term = find_terminator(data, STANDARD_DESCRIPTOR_OFFSET, std_header_len + 1 if std_header_len else min(len(data), 4096))

    x64_descriptor_plausible = False
    if len(data) >= X64_DESCRIPTOR_OFFSET + 32:
        name = c_name(data[X64_DESCRIPTOR_OFFSET:X64_DESCRIPTOR_OFFSET+11])
        ftype = data[X64_DESCRIPTOR_OFFSET+11]
        off64 = u64(data, X64_DESCRIPTOR_OFFSET+12)
        len64 = u64(data, X64_DESCRIPTOR_OFFSET+20)
        x64_descriptor_plausible = bool(name) and plausible_field_type(ftype) and off64 is not None and len64 is not None and 0 < len64 < 100000

    if version == 0x64 and x64_header_len >= X64_DESCRIPTOR_OFFSET + 33 and x64_record_len and x64_descriptor_plausible and x64_term is not None:
        return 'X64BASE_EXTENDED_HEADER_STATIC', X64_DESCRIPTOR_OFFSET, warnings

    if std_header_len >= STANDARD_DESCRIPTOR_OFFSET + 33 and std_term is not None:
        return 'STANDARD_DBF_HEADER_STATIC', STANDARD_DESCRIPTOR_OFFSET, warnings

    if version == 0x64:
        warnings.append('version byte suggests x64-style DBF but header mirrors/descriptors were not fully plausible')
    warnings.append('could not confidently classify DBF header')
    return 'UNKNOWN_DBF_HEADER_STATIC', STANDARD_DESCRIPTOR_OFFSET, warnings


def parse_fields(data: bytes, table_id: str, header_kind: str, descriptor_start: int, header_length: int) -> Tuple[List[ParsedField], Optional[int], List[str]]:
    fields: List[ParsedField] = []
    warnings: List[str] = []
    term = find_terminator(data, descriptor_start, header_length + 1 if header_length else min(len(data), 4096))
    if term is None:
        warnings.append('field descriptor terminator 0x0D not found')
        return fields, None, warnings

    pos = descriptor_start
    ordinal = 1
    while pos + 32 <= len(data) and pos < term:
        desc = data[pos:pos+32]
        if not desc.strip(b'\x00'):
            warnings.append(f'blank descriptor before terminator at offset {pos}')
            break
        name = c_name(desc[:11])
        ftype = chr(desc[11]) if desc[11] else ''
        field_warnings: List[str] = []
        if not name:
            field_warnings.append('blank field name')
        if not plausible_field_type(desc[11]):
            field_warnings.append(f'unusual field type byte 0x{desc[11]:02x}')

        if header_kind == 'X64BASE_EXTENDED_HEADER_STATIC':
            offset = u64(desc, 12)
            width = u64(desc, 20)
            decimals = None
            descriptor_kind = 'x64base_32_byte_descriptor_with_64_bit_offset_length'
            if width is not None and width > 100000:
                field_warnings.append('x64 field width is unusually large')
        else:
            offset = u32(desc, 12)
            width = desc[16]
            decimals = desc[17]
            descriptor_kind = 'standard_32_byte_dbf_descriptor'

        field_id = f'{table_id}.F{ordinal:04d}.{name.upper()}'
        fields.append(ParsedField(
            table_id=table_id,
            field_id=field_id,
            ordinal=ordinal,
            field_name=name,
            field_type=ftype,
            offset=offset,
            width=width,
            decimals=decimals,
            descriptor_offset=pos,
            descriptor_kind=descriptor_kind,
            evidence_kind='STATIC_DBF_HEADER_PARSE',
            trust_level='STATIC_PARSE_ONLY_NOT_RUNTIME_PROOF',
            warnings=field_warnings,
        ))
        ordinal += 1
        pos += 32

    return fields, term, warnings


def parse_dbf(path: Path) -> Dict[str, Any]:
    data = path.read_bytes()
    table_id = path.stem.upper()
    header_kind, descriptor_start, detect_warnings = detect_header_kind(data)
    version = data[0] if data else 0
    yy = data[1] if len(data) > 1 else None
    mm = data[2] if len(data) > 2 else None
    dd = data[3] if len(data) > 3 else None

    if header_kind == 'X64BASE_EXTENDED_HEADER_STATIC':
        record_count = u64(data, 0x20)
        header_length = u64(data, 0x28)
        record_length = u64(data, 0x30)
    else:
        record_count = u32(data, 4)
        header_length = u16(data, 8)
        record_length = u16(data, 10)

    if not header_length:
        header_length = min(len(data), 4096)
    fields, term, field_warnings = parse_fields(data, table_id, header_kind, descriptor_start, int(header_length))
    warnings = list(detect_warnings) + field_warnings
    if header_kind.startswith('UNKNOWN'):
        trust = 'UNCLASSIFIED_STATIC_PARSE_REVIEW_REQUIRED'
    else:
        trust = 'STATIC_PARSE_ONLY_NOT_RUNTIME_PROOF'

    table = ParsedTable(
        table_id=table_id,
        path=str(path),
        file_name=path.name,
        sha256=sha256_file(path),
        file_size=len(data),
        header_kind=header_kind,
        version_byte=version,
        date_yy=yy,
        date_mm=mm,
        date_dd=dd,
        record_count=record_count,
        header_length=header_length,
        record_length=record_length,
        descriptor_offset=descriptor_start,
        field_count=len(fields),
        terminator_offset=term,
        evidence_kind='STATIC_DBF_HEADER_PARSE',
        trust_level=trust,
        warnings=warnings,
    )
    return {'table': asdict(table), 'fields': [asdict(f) for f in fields]}


def iter_dbfs(paths: List[Path]) -> Iterable[Path]:
    for p in paths:
        if p.is_file() and p.suffix.lower() == '.dbf':
            yield p
        elif p.is_dir():
            for child in p.rglob('*.dbf'):
                if child.is_file():
                    yield child
            for child in p.rglob('*.DBF'):
                if child.is_file():
                    yield child


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, '') for k in fieldnames})


def main() -> int:
    ap = argparse.ArgumentParser(description='DD-017 report-only static DBF/x64 header parser')
    ap.add_argument('paths', nargs='+', help='DBF files or directories to scan')
    ap.add_argument('--out-json', default='dd017_static_dbf_projection.json')
    ap.add_argument('--out-tables-csv', default='dd017_tables_projection.csv')
    ap.add_argument('--out-fields-csv', default='dd017_fields_projection.csv')
    args = ap.parse_args()

    paths = [Path(p) for p in args.paths]
    results = []
    warnings = []
    for dbf in sorted(set(iter_dbfs(paths))):
        try:
            results.append(parse_dbf(dbf))
        except Exception as exc:
            warnings.append({'path': str(dbf), 'warning': f'parse_failed: {exc}'})

    manifest = {
        'manifest_kind': 'DD017_STATIC_DBF_PHYSICAL_PROJECTION',
        'trust_level': 'STATIC_PARSE_ONLY_NOT_RUNTIME_PROOF',
        'source_paths': [str(p) for p in paths],
        'table_count': len(results),
        'field_count': sum(len(r['fields']) for r in results),
        'tables': [r['table'] for r in results],
        'fields': [f for r in results for f in r['fields']],
        'warnings': warnings,
    }
    Path(args.out_json).write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    write_csv(Path(args.out_tables_csv), manifest['tables'], [
        'table_id','path','file_name','sha256','file_size','header_kind','version_byte','date_yy','date_mm','date_dd',
        'record_count','header_length','record_length','descriptor_offset','field_count','terminator_offset','evidence_kind','trust_level','warnings'
    ])
    write_csv(Path(args.out_fields_csv), manifest['fields'], [
        'table_id','field_id','ordinal','field_name','field_type','offset','width','decimals','descriptor_offset','descriptor_kind','evidence_kind','trust_level','warnings'
    ])
    print(f"DD-017 static parse complete: tables={manifest['table_count']} fields={manifest['field_count']} warnings={len(warnings)}")
    print(f"JSON: {args.out_json}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
