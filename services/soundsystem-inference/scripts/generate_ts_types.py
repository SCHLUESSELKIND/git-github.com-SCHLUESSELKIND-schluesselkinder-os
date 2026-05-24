"""Generate TypeScript types from the inference service's Pydantic schemas.

Scans `app.schemas` and `app.config` for `BaseModel` and `StrEnum` subclasses
and emits a single, deterministic TypeScript file at
`apps/web/app/admin/soundsystem/_lib/generated-inference-types.ts`.

Run manually:

    cd services/soundsystem-inference
    python scripts/generate_ts_types.py

The committed file is verified against the generator by the pytest drift
check `tests/test_generated_types.py::test_generated_ts_types_match_committed_file`.
That test fails if anyone forgets to regenerate after editing a Pydantic
model.
"""

from __future__ import annotations

import inspect
import json
import sys
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from types import NoneType, UnionType
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints
from uuid import UUID

SERVICE_ROOT = Path(__file__).resolve().parent.parent
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from pydantic import BaseModel  # noqa: E402

import app.config as config_module  # noqa: E402
import app.schemas as schemas_module  # noqa: E402

REPO_ROOT = SERVICE_ROOT.parent.parent
OUTPUT_PATH = (
    REPO_ROOT
    / "apps"
    / "web"
    / "app"
    / "admin"
    / "soundsystem"
    / "_lib"
    / "generated-inference-types.ts"
)

HEADER = """\
/* eslint-disable */
// AUTO-GENERATED FROM services/soundsystem-inference/app/schemas.py.
// DO NOT EDIT BY HAND.
//
// Regenerate via:
//   cd services/soundsystem-inference
//   python scripts/generate_ts_types.py
//
// The pytest drift check `tests/test_generated_types.py`
// will fail if this file is stale.

"""

SCALAR_MAP: dict[type, str] = {
    str: "string",
    int: "number",
    float: "number",
    bool: "boolean",
    bytes: "string",
    UUID: "string",
    datetime: "string",
    date: "string",
}


def _ts_type(annotation: Any) -> str:
    if annotation is None or annotation is NoneType:
        return "null"
    if annotation is Any:
        return "unknown"
    if isinstance(annotation, type) and annotation in SCALAR_MAP:
        return SCALAR_MAP[annotation]

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin in (Union, UnionType):
        non_none = [a for a in args if a is not NoneType]
        nullable = len(non_none) != len(args)
        if not non_none:
            return "null"
        rendered = " | ".join(_ts_type(a) for a in non_none)
        return f"{rendered} | null" if nullable else rendered

    if origin is list or origin is tuple or origin is set or origin is frozenset:
        if not args:
            return "ReadonlyArray<unknown>"
        item_type = args[0]
        return f"ReadonlyArray<{_ts_type(item_type)}>"

    if origin is dict:
        key_type, val_type = args if len(args) == 2 else (str, Any)
        return f"Readonly<Record<{_ts_type(key_type)}, {_ts_type(val_type)}>>"

    if origin is Literal:
        rendered_parts: list[str] = []
        for arg in args:
            if isinstance(arg, bool):
                rendered_parts.append("true" if arg else "false")
            elif arg is None:
                rendered_parts.append("null")
            elif isinstance(arg, (int, float)):
                rendered_parts.append(str(arg))
            else:
                rendered_parts.append(json.dumps(arg))
        return " | ".join(rendered_parts)

    if isinstance(annotation, type) and issubclass(annotation, StrEnum):
        return annotation.__name__

    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation.__name__

    return "unknown"


def _collect_types() -> tuple[list[type[StrEnum]], list[type[BaseModel]]]:
    enums: dict[str, type[StrEnum]] = {}
    models: dict[str, type[BaseModel]] = {}
    for module in (schemas_module, config_module):
        for _name, obj in inspect.getmembers(module):
            if not isinstance(obj, type):
                continue
            if obj.__module__ != module.__name__:
                continue
            if obj is StrEnum or obj is BaseModel:
                continue
            if issubclass(obj, StrEnum):
                enums[obj.__name__] = obj
            elif issubclass(obj, BaseModel):
                models[obj.__name__] = obj
    return (
        sorted(enums.values(), key=lambda cls: cls.__name__),
        sorted(models.values(), key=lambda cls: cls.__name__),
    )


def _emit_enum(enum_cls: type[StrEnum]) -> str:
    members = sorted(enum_cls, key=lambda member: member.value)
    if not members:
        return f"export type {enum_cls.__name__} = never;\n\n"
    quoted = [json.dumps(member.value) for member in members]
    if len(quoted) == 1:
        return f"export type {enum_cls.__name__} = {quoted[0]};\n\n"
    body = "\n  | ".join(quoted)
    return f"export type {enum_cls.__name__} =\n  | {body};\n\n"


def _emit_model(model_cls: type[BaseModel]) -> str:
    is_request = model_cls.__name__.endswith("Request")
    try:
        hints = get_type_hints(model_cls)
    except Exception:
        hints = {}
    lines = [f"export type {model_cls.__name__} = Readonly<{{"]
    for field_name, field in model_cls.model_fields.items():
        annotation = hints.get(field_name, field.annotation)
        ts = _ts_type(annotation)
        optional_marker = "?" if (is_request and not field.is_required()) else ""
        lines.append(f"  {field_name}{optional_marker}: {ts};")
    lines.append("}>;")
    lines.append("")
    return "\n".join(lines) + "\n"


def generate() -> str:
    enums, models = _collect_types()
    parts: list[str] = [HEADER]
    parts.append("// ---- Enums (string unions mirroring Python StrEnum) ----\n\n")
    for enum_cls in enums:
        parts.append(_emit_enum(enum_cls))
    parts.append("// ---- Models (Pydantic BaseModel subclasses) ----\n\n")
    for model_cls in models:
        parts.append(_emit_model(model_cls))
    return "".join(parts)


def main() -> int:
    content = generate()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(content, encoding="utf-8")
    print(f"wrote {len(content)} chars to {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
