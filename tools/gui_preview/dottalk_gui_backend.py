"""Backend services for the DotTalk++ Python GUI frontend."""

from __future__ import annotations

import datetime as _dt
import os
import pathlib
import re
import struct
import sys
from dataclasses import dataclass, field


FIELD_TYPE_NAMES = {
    "C": "Character",
    "N": "Numeric",
    "F": "Float",
    "D": "Date",
    "L": "Logical",
    "M": "Memo",
    "I": "Integer",
    "Y": "Currency",
    "T": "DateTime",
    "B": "Double",
}

DBF_VERSION_X64 = 0x64
CLASSIC_DBF_DESCRIPTOR_START = 32
X64_DBF_DESCRIPTOR_START = 96


def repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2]


def field_type_name(code: str) -> str:
    return FIELD_TYPE_NAMES.get(code, code or "?")


def add_pydottalk_search_paths() -> None:
    repo = repo_root()
    candidates = []
    override = os.environ.get("PYDOTTALK_BIN", "")
    if override:
        candidates.append(pathlib.Path(override))

    candidates.extend([
        repo / "build" / "python",
        repo / "build" / "python" / "Release",
        repo / "build" / "python" / "Debug",
    ])

    for candidate in candidates:
        if candidate.exists():
            text = str(candidate)
            if text not in sys.path:
                sys.path.insert(0, text)


def decode_dbf_value(raw: bytes, field_type: str) -> str:
    text = raw.decode("latin-1", errors="replace").strip()
    if field_type == "D" and len(text) == 8 and text.isdigit():
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    return text


def descriptor_start_for_version(version: int) -> int:
    if version == DBF_VERSION_X64:
        return X64_DBF_DESCRIPTOR_START
    return CLASSIC_DBF_DESCRIPTOR_START


def read_dbf_with_pydottalk(path: pathlib.Path, max_records: int = 200) -> dict[str, object]:
    add_pydottalk_search_paths()
    import pydottalk  # type: ignore[import-not-found]

    area = pydottalk.xbase.DbArea()
    area.open(str(path))
    try:
        fields = [dict(field) for field in area.fields()]
        record_count = int(area.rec_count())
        rows: list[dict[str, object]] = []
        for recno in range(1, min(record_count, max_records) + 1):
            if not area.goto_rec(recno):
                break
            values = [str(area.get(index + 1)) for index in range(len(fields))]
            rows.append({
                "record_number": recno,
                "deleted": bool(area.is_deleted()),
                "values": values,
            })

        return {
            "backend": f"pydottalk {pydottalk.version()}",
            "path": path,
            "version": "runtime",
            "updated": "runtime",
            "record_count": record_count,
            "header_length": "runtime",
            "record_length": int(area.rec_length()),
            "fields": fields,
            "rows": rows,
            "truncated": record_count > len(rows),
        }
    finally:
        area.close()


def read_dbf_fallback(path: pathlib.Path, max_records: int = 200) -> dict[str, object]:
    with path.open("rb") as stream:
        header = stream.read(32)
        if len(header) != 32:
            raise ValueError("File is too small to be a DBF table.")

        version = header[0]
        year, month, day = header[1] + 1900, header[2], header[3]
        record_count = struct.unpack_from("<I", header, 4)[0]
        header_length = struct.unpack_from("<H", header, 8)[0]
        record_length = struct.unpack_from("<H", header, 10)[0]

        fields: list[dict[str, object]] = []
        stream.seek(descriptor_start_for_version(version))
        while True:
            descriptor = stream.read(32)
            if not descriptor:
                raise ValueError("DBF field descriptor terminator was not found.")
            if descriptor[0] == 0x0D:
                break

            name = descriptor[0:11].split(b"\0", 1)[0].decode("latin-1", errors="replace")
            field_type = chr(descriptor[11])
            length = descriptor[16]
            decimals = descriptor[17]
            fields.append({
                "name": name,
                "type": field_type,
                "length": length,
                "decimals": decimals,
            })

        stream.seek(header_length)
        rows: list[dict[str, object]] = []
        for recno in range(1, min(record_count, max_records) + 1):
            record = stream.read(record_length)
            if len(record) != record_length:
                break

            deleted = record[0:1] == b"*"
            offset = 1
            values: list[str] = []
            for field in fields:
                length = int(field["length"])
                raw = record[offset:offset + length]
                offset += length
                values.append(decode_dbf_value(raw, str(field["type"])))
            rows.append({"record_number": recno, "deleted": deleted, "values": values})

    try:
        updated = _dt.date(year, month, day).isoformat()
    except ValueError:
        updated = "unknown"

    return {
        "backend": "pure-python dbf preview",
        "path": path,
        "version": version,
        "updated": updated,
        "record_count": record_count,
        "header_length": header_length,
        "record_length": record_length,
        "fields": fields,
        "rows": rows,
        "truncated": record_count > len(rows),
    }


def read_table_snapshot(path: pathlib.Path, max_records: int = 200) -> dict[str, object]:
    try:
        return read_dbf_with_pydottalk(path, max_records)
    except Exception as exc:  # noqa: BLE001 - fallback keeps frontend useful without bindings.
        snapshot = read_dbf_fallback(path, max_records)
        snapshot["backend"] = f"pure-python dbf preview (pydottalk unavailable: {exc})"
        return snapshot


def read_dbf_record_fallback(path: pathlib.Path, recno: int) -> dict[str, object]:
    if recno < 1:
        raise ValueError("record number must be positive")
    with path.open("rb") as stream:
        header = stream.read(32)
        if len(header) != 32:
            raise ValueError("File is too small to be a DBF table.")

        version = header[0]
        record_count = struct.unpack_from("<I", header, 4)[0]
        header_length = struct.unpack_from("<H", header, 8)[0]
        record_length = struct.unpack_from("<H", header, 10)[0]
        if recno > record_count:
            raise ValueError(f"record number is past the end of table: {recno}")

        fields: list[dict[str, object]] = []
        stream.seek(descriptor_start_for_version(version))
        while True:
            descriptor = stream.read(32)
            if not descriptor:
                raise ValueError("DBF field descriptor terminator was not found.")
            if descriptor[0] == 0x0D:
                break
            fields.append({
                "name": descriptor[0:11].split(b"\0", 1)[0].decode("latin-1", errors="replace"),
                "type": chr(descriptor[11]),
                "length": descriptor[16],
                "decimals": descriptor[17],
            })

        stream.seek(header_length + (recno - 1) * record_length)
        record = stream.read(record_length)
        if len(record) != record_length:
            raise ValueError(f"could not read record {recno}")

    deleted = record[0:1] == b"*"
    offset = 1
    values: list[str] = []
    for field in fields:
        length = int(field["length"])
        raw = record[offset:offset + length]
        offset += length
        values.append(decode_dbf_value(raw, str(field["type"])))

    return {
        "backend": "pure-python dbf record",
        "path": path,
        "version": version,
        "record_count": record_count,
        "record_length": record_length,
        "fields": fields,
        "row": {"record_number": recno, "deleted": deleted, "values": values},
    }


def read_table_record(path: pathlib.Path, recno: int) -> dict[str, object]:
    try:
        add_pydottalk_search_paths()
        import pydottalk  # type: ignore[import-not-found]

        area = pydottalk.xbase.DbArea()
        area.open(str(path))
        try:
            if recno < 1 or recno > int(area.rec_count()):
                raise ValueError(f"record number is past the end of table: {recno}")
            if not area.goto_rec(recno):
                raise ValueError(f"could not move to record {recno}")
            fields = [dict(field) for field in area.fields()]
            values = [str(area.get(index + 1)) for index in range(len(fields))]
            return {
                "backend": f"pydottalk {pydottalk.version()}",
                "path": path,
                "version": "runtime",
                "record_count": int(area.rec_count()),
                "record_length": int(area.rec_length()),
                "fields": fields,
                "row": {"record_number": recno, "deleted": bool(area.is_deleted()), "values": values},
            }
        finally:
            area.close()
    except Exception as exc:  # noqa: BLE001 - fallback keeps frontend useful without bindings.
        record = read_dbf_record_fallback(path, recno)
        record["backend"] = f"pure-python dbf record (pydottalk unavailable: {exc})"
        return record


@dataclass
class PythonArea:
    area_id: int
    path: pathlib.Path
    display_name: str
    snapshot: dict[str, object]
    recno: int = 1


@dataclass
class PythonIndexInfo:
    area_id: int
    area_name: str
    kind: str = "PHYSICAL"
    active: bool = False
    direction: str = "ASC"
    tag: str = ""
    tags: list[str] = field(default_factory=list)
    backend: str = "physical"
    container: pathlib.Path | None = None


@dataclass
class PythonRelationInfo:
    parent: str
    child: str
    parent_key: str = ""
    child_key: str = ""
    match_count: int = 0
    source: str = "DotTalk++ shell"


@dataclass
class _SchemaArea:
    slot: int
    dbf: pathlib.Path
    index: pathlib.Path = pathlib.Path()
    index_type: str = ""
    tag: str = ""
    alias: str = ""


def data_root() -> pathlib.Path:
    for env_name in ("DOTTALKPP_DATA", "DOTTALK_DATA"):
        value = os.environ.get(env_name)
        if value and pathlib.Path(value).is_dir():
            return pathlib.Path(value).resolve()
    root = repo_root()
    for candidate in (root / "dottalkpp" / "data", root / "data", pathlib.Path.cwd()):
        if candidate.is_dir():
            return candidate.resolve()
    return pathlib.Path.cwd().resolve()


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _first_existing(paths: list[pathlib.Path]) -> pathlib.Path | None:
    for path in paths:
        try:
            if path.is_file():
                return path.resolve()
        except OSError:
            continue
    return None


def resolve_workspace_schema_token(token: pathlib.Path) -> pathlib.Path | None:
    if not str(token):
        return None

    candidates: list[pathlib.Path] = []

    def add(path: pathlib.Path) -> None:
        if not str(path):
            return
        candidates.append(path)
        if not path.suffix:
            candidates.append(path.with_suffix(".dtschema"))
            candidates.append(path.with_suffix(".dtschemas"))

    data = data_root()
    root = data.parent
    if token.is_absolute():
        add(token)
    else:
        for base in (
            root / "user" / "default" / "workspaces",
            root / "user" / "public" / "workspaces",
            data / "workspaces",
            data / "schemas",
            pathlib.Path.cwd(),
        ):
            add(base / token)
        add(token)
    return _first_existing(candidates)


def _parse_key_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for segment in text.split("|"):
        if "=" not in segment:
            continue
        key, value = segment.split("=", 1)
        values[key.strip().lower()] = value.strip()
    return values


def load_dtschema2(path: pathlib.Path) -> tuple[list[_SchemaArea], list[PythonRelationInfo]]:
    areas: list[_SchemaArea] = []
    relations: list[PythonRelationInfo] = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if line.upper().startswith("AREA "):
            parts = line.split("|", 1)
            header = parts[0].split()
            if len(header) < 2 or not header[1].isdigit():
                continue
            values = _parse_key_values(parts[1] if len(parts) > 1 else "")
            areas.append(_SchemaArea(
                slot=int(header[1]),
                dbf=pathlib.Path(_strip_quotes(values.get("dbf", ""))),
                index=pathlib.Path(_strip_quotes(values.get("index", ""))),
                index_type=values.get("indextype", "").upper(),
                tag=values.get("tag", "").upper(),
                alias=values.get("alias", "").upper(),
            ))
            continue
        if line.upper().startswith("RELATION "):
            tokens = line.split()
            if len(tokens) >= 5 and tokens[3].upper() == "ON":
                key = tokens[4].upper()
                relations.append(PythonRelationInfo(
                    parent=tokens[1].upper(),
                    child=tokens[2].upper(),
                    parent_key=key,
                    child_key=key,
                    source="DTSchema",
                ))
    return areas, relations


def _resolve_schema_dbf(path: pathlib.Path, index_type: str) -> pathlib.Path | None:
    if path.is_absolute():
        return _first_existing([path])
    data = data_root()
    mode = index_type.upper()
    candidates = []
    if mode == "CDX":
        candidates.append(data / "dbf" / "x64" / path)
    if mode in {"CNX", "INX", "IDX"}:
        candidates.append(data / "dbf" / "x32" / path)
    candidates.extend([data / "dbf" / path, data / path, path])
    return _first_existing(candidates)


def _resolve_schema_index(path: pathlib.Path, index_type: str) -> pathlib.Path | None:
    if not str(path) or str(path).lower() in {"none", "noindex", "physical"}:
        return None
    if path.is_absolute():
        return _first_existing([path])
    data = data_root()
    mode = index_type.upper()
    candidates = []
    if mode == "CDX":
        candidates.append(data / "indexes" / "x64" / path)
    if mode in {"CNX", "INX", "IDX"}:
        candidates.append(data / "indexes" / "x32" / path)
    candidates.extend([data / "indexes" / path, data / path, path])
    return _first_existing(candidates)


def _field_names(snapshot: dict[str, object]) -> list[str]:
    return [str(field.get("name", "")).upper() for field in snapshot.get("fields", []) if isinstance(field, dict)]


def _default_index_tags(snapshot: dict[str, object], active_tag: str) -> list[str]:
    names = _field_names(snapshot)
    if active_tag and active_tag not in names:
        return [active_tag, *names]
    return names


def _value_for_record(area: PythonArea, field_name: str) -> str:
    fields = _field_names(area.snapshot)
    try:
        field_index = fields.index(field_name.upper())
    except ValueError:
        return ""
    rows = list(area.snapshot.get("rows", []))
    for row in rows:
        if int(row.get("record_number", 0) or 0) == area.recno:
            values = list(row.get("values", []))
            return str(values[field_index]).strip() if field_index < len(values) else ""
    return ""


def _count_child_matches(child: PythonArea, field_name: str, value: str) -> int:
    if not value:
        return 0
    fields = _field_names(child.snapshot)
    try:
        field_index = fields.index(field_name.upper())
    except ValueError:
        return 0
    snapshot = read_table_snapshot(child.path, int(child.snapshot.get("record_count", 0) or 0))
    count = 0
    for row in snapshot.get("rows", []):
        values = list(row.get("values", []))
        if field_index < len(values) and str(values[field_index]).strip() == value:
            count += 1
    return count


@dataclass
class PythonAreaSession:
    next_area_id: int = 1
    active_area_id: int = 0
    areas: list[PythonArea] = field(default_factory=list)
    indexes: list[PythonIndexInfo] = field(default_factory=list)
    relations: list[PythonRelationInfo] = field(default_factory=list)

    def open_table(self, path: pathlib.Path, max_records: int = 200) -> PythonArea:
        comparable = path.resolve()
        for area in self.areas:
            try:
                if area.path.resolve() == comparable:
                    self.active_area_id = area.area_id
                    return area
            except OSError:
                if area.path == path:
                    self.active_area_id = area.area_id
                    return area

        snapshot = read_table_snapshot(path, max_records)
        area = PythonArea(
            area_id=self.next_area_id,
            path=path,
            display_name=path.name,
            snapshot=snapshot,
        )
        self.next_area_id += 1
        self.areas.append(area)
        self.active_area_id = area.area_id
        self._ensure_physical_index(area)
        return area

    def select_area(self, area_id: int) -> PythonArea:
        for area in self.areas:
            if area.area_id == area_id:
                self.active_area_id = area_id
                self.refresh_relation_matches()
                return area
        raise KeyError(f"area is not open: {area_id}")

    def select_area_by_user_token(self, token: str) -> PythonArea:
        token = token.strip()
        if not token:
            raise KeyError("area is not open: ")
        if token.isdigit():
            return self.select_area(int(token) + 1)

        wanted = token.lower()
        for area in self.areas:
            names = {
                area.display_name.lower(),
                area.path.name.lower(),
                area.path.stem.lower(),
            }
            if wanted in names or f"{wanted}.dbf" in names:
                self.active_area_id = area.area_id
                return area
        raise KeyError(f"area is not open: {token}")

    def goto_record(self, recno: int) -> PythonArea:
        area = self.active_area()
        if area is None:
            raise KeyError("no current table")
        total = int(area.snapshot.get("record_count", 0))
        if total <= 0:
            area.recno = 0
            return area
        area.recno = max(1, min(int(recno), total))
        self.refresh_relation_matches()
        return area

    def skip_records(self, delta: int) -> PythonArea:
        area = self.active_area()
        if area is None:
            raise KeyError("no current table")
        return self.goto_record(area.recno + int(delta))

    def top(self) -> PythonArea:
        return self.goto_record(1)

    def bottom(self) -> PythonArea:
        area = self.active_area()
        if area is None:
            raise KeyError("no current table")
        return self.goto_record(int(area.snapshot.get("record_count", 0)))

    def close_area(self, area_id: int) -> None:
        remaining = [area for area in self.areas if area.area_id != area_id]
        if len(remaining) == len(self.areas):
            raise KeyError(f"area is not open: {area_id}")
        self.areas = remaining
        self.indexes = [index for index in self.indexes if index.area_id != area_id]
        if self.active_area_id == area_id:
            self.active_area_id = self.areas[0].area_id if self.areas else 0

    def active_area(self) -> PythonArea | None:
        for area in self.areas:
            if area.area_id == self.active_area_id:
                return area
        return None

    def clear_workspace(self) -> int:
        closed = len(self.areas)
        self.areas = []
        self.indexes = []
        self.relations = []
        self.active_area_id = 0
        self.next_area_id = 1
        return closed

    def _ensure_physical_index(self, area: PythonArea) -> None:
        if any(index.area_id == area.area_id for index in self.indexes):
            return
        self.indexes.append(PythonIndexInfo(
            area_id=area.area_id,
            area_name=area.display_name,
            kind="PHYSICAL",
            active=True,
            direction="ASC",
            backend="physical",
        ))

    def _area_by_alias(self, alias: str) -> PythonArea | None:
        wanted = alias.upper()
        for area in self.areas:
            names = {
                area.display_name.upper(),
                area.path.stem.upper(),
                f"{area.path.stem.upper()}.DBF",
            }
            if wanted in names or f"{wanted}.DBF" in names:
                return area
        return None

    def refresh_relation_matches(self) -> None:
        active = self.active_area()
        if active is None:
            return
        active_alias = active.path.stem.upper()
        for relation in self.relations:
            if relation.parent.upper() != active_alias and f"{relation.parent.upper()}.DBF" != active.display_name.upper():
                relation.match_count = 0
                continue
            child = self._area_by_alias(relation.child)
            if child is None:
                relation.match_count = 0
                continue
            value = _value_for_record(active, relation.parent_key)
            relation.match_count = _count_child_matches(child, relation.child_key or relation.parent_key, value)

    def mirror_workspace_open_directory(self, directory: pathlib.Path, max_records: int = 200) -> int:
        if not directory.is_dir():
            return 0
        self.clear_workspace()
        opened = 0
        tables = list(directory.glob("*.DBF")) + list(directory.glob("*.dbf"))
        tables.sort(key=lambda path: path.name.lower())
        for table in tables:
            if any(existing.path == table for existing in self.areas):
                continue
            self.open_table(table, max_records)
            opened += 1
        if self.areas:
            self.active_area_id = self.areas[0].area_id
        self.refresh_relation_matches()
        return opened

    def attach_default_indexes(self, index_mode: str, dbf_dir: pathlib.Path | None = None) -> int:
        mode = index_mode.upper()
        if mode in {"", "NONE", "NOINDEX", "NOINDEXES", "PHYSICAL"}:
            return 0
        attached = 0
        for area in self.areas:
            ext = ".cdx" if mode == "CDX" else f".{mode.lower()}"
            index_name = area.path.with_suffix(ext).name
            container = _resolve_schema_index(pathlib.Path(index_name), mode)
            if container is None and dbf_dir is not None:
                container = _first_existing([dbf_dir / index_name])
            if container is None:
                continue
            self.indexes = [index for index in self.indexes if index.area_id != area.area_id]
            tags = _default_index_tags(area.snapshot, "")
            self.indexes.append(PythonIndexInfo(
                area_id=area.area_id,
                area_name=area.display_name,
                kind=mode,
                active=True,
                direction="ASC",
                tag=tags[0] if tags else "",
                tags=tags,
                backend=mode,
                container=container,
            ))
            attached += 1
        return attached

    def mirror_workspace_load_schema(self, schema_path: pathlib.Path, max_records: int = 200) -> int:
        areas, relations = load_dtschema2(schema_path)
        if not areas:
            return 0
        self.clear_workspace()
        max_area_id = 0
        opened = 0
        for schema_area in sorted(areas, key=lambda area: area.slot):
            dbf = _resolve_schema_dbf(schema_area.dbf, schema_area.index_type)
            if dbf is None:
                continue
            snapshot = read_table_snapshot(dbf, max_records)
            area_id = schema_area.slot + 1
            max_area_id = max(max_area_id, area_id)
            area = PythonArea(
                area_id=area_id,
                path=dbf,
                display_name=f"{schema_area.alias}.DBF" if schema_area.alias else dbf.name,
                snapshot=snapshot,
            )
            self.areas.append(area)
            if self.active_area_id == 0:
                self.active_area_id = area.area_id
            index = _resolve_schema_index(schema_area.index, schema_area.index_type)
            if index is not None:
                tags = _default_index_tags(snapshot, schema_area.tag)
                self.indexes.append(PythonIndexInfo(
                    area_id=area.area_id,
                    area_name=area.display_name,
                    kind=schema_area.index_type or index.suffix.lstrip(".").upper(),
                    active=True,
                    direction="ASC",
                    tag=schema_area.tag,
                    tags=tags,
                    backend=schema_area.index_type or index.suffix.lstrip(".").upper(),
                    container=index,
                ))
            else:
                self._ensure_physical_index(area)
            opened += 1
        self.relations = relations
        self.next_area_id = max(max_area_id + 1, 1)
        self.refresh_relation_matches()
        return opened

    def mirror_cli_output(self, command_text: str, output: str) -> list[str]:
        notes: list[str] = []
        schema = workspace_load_schema_from_cli_output(command_text, output)
        if schema is not None:
            opened = self.mirror_workspace_load_schema(schema)
            if opened:
                notes.append(f"GUI mirror: WORKSPACE LOAD created {opened} GUI area(s) from {schema}")
        directory = workspace_open_directory_from_cli_output(output)
        if directory is not None:
            opened = self.mirror_workspace_open_directory(directory)
            mode = workspace_open_index_mode_from_output(output)
            attached = self.attach_default_indexes(mode, directory) if mode else 0
            notes.append(f"GUI mirror: WORKSPACE OPEN created {opened} GUI area(s) from {directory}")
            if attached:
                notes.append(f"GUI mirror: WORKSPACE OPEN attached {attached} {mode} index container(s)")
        parsed_relations = relations_from_cli_output(output)
        if parsed_relations:
            self.relations = merge_relations(self.relations, parsed_relations)
            self.refresh_relation_matches()
            notes.append(f"GUI mirror: captured {len(parsed_relations)} relation edge(s) from DotTalk++ output")
        return notes


def workspace_open_directory_from_cli_output(output: str) -> pathlib.Path | None:
    marker = "WORKSPACE OPEN: scanning directory:"
    found: pathlib.Path | None = None
    for line in output.splitlines():
        pos = line.find(marker)
        if pos == -1:
            continue
        text = line[pos + len(marker):].strip()
        option_pos = text.find(" [")
        if option_pos != -1:
            text = text[:option_pos].strip()
        if text:
            found = pathlib.Path(text)
    return found


def workspace_open_index_mode_from_output(output: str) -> str:
    match = re.search(r"WORKSPACE OPEN: scanning directory:.*\[(CDX|CNX|INX|IDX|LMDB)", output, re.IGNORECASE)
    return match.group(1).upper() if match else ""


def workspace_load_schema_from_cli_output(command_text: str, output: str) -> pathlib.Path | None:
    for line in output.splitlines():
        marker = line.find("WORKSPACE=")
        if marker == -1:
            continue
        text = line[marker + len("WORKSPACE="):].strip().split()[0]
        resolved = resolve_workspace_schema_token(pathlib.Path(_strip_quotes(text)))
        if resolved is not None:
            return resolved

    parts = command_text.strip().split()
    if len(parts) >= 3 and parts[0].lower() == "workspace" and parts[1].lower() == "load":
        return resolve_workspace_schema_token(pathlib.Path(_strip_quotes(parts[2])))
    return None


def relations_from_cli_output(output: str) -> list[PythonRelationInfo]:
    relations: list[PythonRelationInfo] = []
    for line in output.splitlines():
        text = line.strip()
        if not text.upper().startswith("REL:"):
            continue
        rest = text[4:].strip()
        arrow = rest.find("->")
        on = rest.upper().find(" ON ")
        if arrow == -1 or on == -1:
            continue
        parent = rest[:arrow].strip().upper()
        child = rest[arrow + 2:on].strip().upper()
        key = rest[on + 4:].strip().upper()
        relations.append(PythonRelationInfo(parent, child, key, key, source="DotTalk++ shell"))
    return relations


def merge_relations(existing: list[PythonRelationInfo],
                    updates: list[PythonRelationInfo]) -> list[PythonRelationInfo]:
    merged = list(existing)
    for update in updates:
        found = None
        for relation in merged:
            if relation.parent == update.parent and relation.child == update.child:
                found = relation
                break
        if found is None:
            merged.append(update)
        else:
            found.parent_key = update.parent_key or found.parent_key
            found.child_key = update.child_key or found.child_key
            found.source = update.source or found.source
            if update.match_count:
                found.match_count = update.match_count
    return merged
