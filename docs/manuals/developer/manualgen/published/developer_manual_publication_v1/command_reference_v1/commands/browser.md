<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# BROWSER

- Catalog/topic: `DOT` / `BROWSER`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Developer browser command (experimental).

- Enter a minimal interactive browser with list, display, goto, edit, help, and quit commands, delegating work to existing command handlers.

## Status

- implemented=yes; supported=yes

## Syntax

- BROWSER USAGE
- BROWSER
- BROWSER EDIT

## Usage

- BROWSER USAGE
- BROWSER
- BROWSER EDIT

## Note

- BROWSER with no arguments enters interactive browse mode.
- BROWSER EDIT displays edit mode in the banner; edit command is available inside the browser.
- Inside BROWSER, L lists records, D displays current record, G moves to a record, E edits via REPLACE, H or question-mark shows help, and Q quits.
- BROWSER itself is interactive; side effects come from delegated GOTO and REPLACE actions.
- risk:
- interactive: yes
- mutates_record_pointer: GOTO actions
- mutates_table_data: edit actions through REPLACE
- delegates_to_replace: yes

## Related

- BROWSE
- BROWSETUI
- LIST
- DISPLAY
- GOTO
- REPLACE
- ---- Forward declarations of existing command handlers ---------------------
- void cmd_LIST   (xbase::DbArea&amp;, std::istringstream&amp;);
- void cmd_DISPLAY(xbase::DbArea&amp;, std::istringstream&amp;);
- void cmd_GOTO   (xbase::DbArea&amp;, std::istringstream&amp;);
- void cmd_REPLACE(xbase::DbArea&amp;, std::istringstream&amp;);
- ---- Helpers ---------------------------------------------------------------
- static inline std::string trim(const std::string&amp; s) {
- size_t b = 0, e = s.size();
- while (b &lt; e &amp;&amp; std::isspace(static_cast&lt;unsigned char&gt;(s[b]))) ++b;
- while (e &gt; b &amp;&amp; std::isspace(static_cast&lt;unsigned char&gt;(s[e-1]))) --e;
- return s.substr(b, e - b);
- }
- static inline std::string upper(std::string s) {
- std::transform(s.begin(), s.end(), s.begin(),
- [](unsigned char c){ return static_cast&lt;char&gt;(std::toupper(c)); });
- return s;

## Provenance

- Topic key: `DOT|BROWSER`
- Included HELP rows: `40`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
