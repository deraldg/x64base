# Messaging Schema Notes v1

Candidate future x64base tables:

| Table | Role |
|---|---|
| MSGDEF | Canonical message definitions: id/key, owner, category, severity, default text, status. |
| MSGTEXT | Locale-specific text templates and fallback policy. |
| MSGARG | Placeholder metadata and validation rules. |
| MSGUSE | Source usage evidence and runtime context. |
| MSGLANG | Supported locales/languages and fallbacks. |
| MSGRUN | Extraction/import/validation/promotion run records. |
| MSGREVIEW | Review/disposition rows for duplicates, ambiguous strings, and candidate replacements. |

The schema should support report-only extraction before any source rewrite.
