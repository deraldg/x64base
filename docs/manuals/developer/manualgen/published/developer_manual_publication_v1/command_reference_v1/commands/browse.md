<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# BROWSE

- Catalog/topic: `DOT` / `BROWSE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Open the classic browse surface for the current table/work-area context.

- Enter the refactored BROWSE module through the legacy global command symbol, preserving existing callers while delegating implementation.

## Status

- implemented=yes; supported=yes

## Syntax

- BROWSE USAGE
- BROWSE
- BROWSE EDIT

## Usage

- BROWSE USAGE
- BROWSE
- BROWSE EDIT

## Note

- BROWSE is a thin forwarder to the browse module.
- BROWSE with no arguments enters interactive browse mode.
- BROWSE EDIT requests edit-capable browse behavior where supported by the module.
- Side effects depend on browse actions and delegated commands.
- risk:
- interactive: yes
- mutates_data: possible through edit actions
- delegates_to_browse_module: yes

## Related

- BROWSER
- BROWSETUI
- LIST
- DISPLAY
- REPLACE
- Public entrypoint from the new module
- namespace {
- static std::string browse_trim(std::string s)
- {
- while (!s.empty() &amp;&amp; std::isspace(static_cast&lt;unsigned char&gt;(s.front()))) s.erase(s.begin());
- while (!s.empty() &amp;&amp; std::isspace(static_cast&lt;unsigned char&gt;(s.back()))) s.pop_back();
- return s;
- }
- static std::string browse_upper(std::string s)
- std::transform(s.begin(), s.end(), s.begin(),
- [](unsigned char c) { return static_cast&lt;char&gt;(std::toupper(c)); });
- static bool is_browse_usage_request(std::string raw)
- std::string t = browse_upper(browse_trim(std::move(raw)));
- if (t.rfind("BROWSE ", 0) == 0) t = browse_trim(t.substr(7));
- return t == "USAGE" || t == "HELP" || t == "?";
- static void print_browse_usage()
- std::cout
- &lt;&lt; "Usage:\n"

## Provenance

- Topic key: `DOT|BROWSE`
- Included HELP rows: `40`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
