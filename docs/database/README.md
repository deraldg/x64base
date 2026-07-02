# DotTalk++ Database Contracts

Status: active contract index.

This folder holds database behavior contracts that apply across CLI, TUI,
Python GUI, C++ GUI, tests, and future service/binding layers.

## Contracts

- `VALUE_LOCALE_COLLATION_CONTRACT_V1.md`
  - separates storage bytes, logical values, display text, parse locale, and
    collation/index identity.
- `DATABASE_SAFETY_CONTRACT_V1.md`
  - defines read-only defaults, mutating-operation boundaries, integrity checks,
    index safety, memo safety, and recovery expectations.

## Related UI Contracts

- `../contracts/CONTRACT_REGISTRY_V1.md`
- `../ui/CORE_UI_PRINCIPLES_V1.md`
- `../gui/UNIFIED_GUI_CORE_V1.md`
- `../gui/WINDOWED_APP_CONTRACT_V1.md`

## Working Rule

New database-facing UI features should pass through these contracts before
adding controls or commands, especially if they involve values, locale, search,
indexes, editing, import/export, repair, or background threading.
