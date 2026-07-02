"""Toolkit-neutral GUI text resolver for the Python GUI lane."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from generated_gui_text import SUPPORTED_LOCALES, TEXT


@dataclass(frozen=True)
class LocaleContext:
    message_locale: str = "en-US"
    display_locale: str = "en-US"
    parse_locale: str = "en-US"
    region_id: str = "GLOBAL"


def normalize_locale(locale: str) -> str:
    lowered = (locale or "en-US").replace("_", "-").split(".", 1)[0].lower()
    if lowered in {"default", "en", "en-us", "enus"}:
        return "en-US"
    if lowered in {"es", "es-es", "es-mx"}:
        return "es"
    if lowered in {"fr", "fr-fr", "fr-ca"}:
        return "fr"
    if lowered in {"de", "de-de"}:
        return "de"
    if lowered in {"it", "it-it"}:
        return "it"
    return "en-US"


def locale_context_from_message_locale(locale: str) -> LocaleContext:
    normalized = normalize_locale(locale)
    return LocaleContext(
        message_locale=normalized,
        display_locale=normalized,
        parse_locale=normalized,
        region_id="GLOBAL",
    )


def locale_context_from_environment() -> LocaleContext:
    return locale_context_from_message_locale(
        os.environ.get("DOTTALK_GUI_LOCALE")
        or os.environ.get("DOTTALK_LOCALE")
        or os.environ.get("LANG")
        or "en-US"
    )


def available_gui_message_locales() -> tuple[str, ...]:
    return SUPPORTED_LOCALES


def text(key: str, locale: LocaleContext | None = None) -> str:
    context = locale or LocaleContext()
    row = TEXT.get(key)
    if not row:
        return ""
    normalized = normalize_locale(context.message_locale)
    return row.get(normalized) or row.get("en-US", "")


def render_label(label_code: str, fallback: str, locale: LocaleContext | None = None) -> str:
    resolved = text(label_code, locale) if label_code else ""
    return resolved or fallback


def render_status_line(message: Mapping[str, str], locale: LocaleContext | None = None) -> str:
    severity = message.get("severity", "info")
    severity_text = text(f"gui.severity.{severity}", locale) or severity
    code = message.get("code", "")
    body = text(code, locale) or message.get("text", "")
    detail = message.get("detail", "")
    prefix = f"{severity_text}: "
    if code:
        prefix += f"[{code}] "
    return f"{prefix}{body}{(' ' + detail) if detail else ''}"
