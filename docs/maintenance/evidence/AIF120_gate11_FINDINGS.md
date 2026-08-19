# Gate 11 -- acceptance test of AIF120_DESIGN_TABLE_CONTRACT_V1.md

Implementer: a Tk renderer (`render.py`) written from the contract and a DBF
reader, holding nothing else. No other implementation, importer or example was
consulted; the working directory was never left.

**Result: 4 of 5 tables render; 1 is refused for a reason the contract does not
actually authorise (see G-1).**

| table | outcome |
| --- | --- |
| `FONTDEMO.DBF` | renders. `FONTDEMO.png` |
| `TABDEMO.DBF` | renders. `TABDEMO.png` |
| `UIDEF_STUDENTS.DBF` | renders. `UIDEF_STUDENTS.png` |
| `UIDEF_MENU.DBF` | renders, real menubar, 7 popups, 67 items. `UIDEF_MENU.png` |
| `FLOWDEMO.DBF` | **refused** by default (grid with no `Columns`). `FLOWDEMO.png` is the `--force` render |

Headline: **the contract is sufficient for the shape of a document and
insufficient for its content.** Record kinds, the tree, requiredness, refusal
policy and the property mini-language are all crisply specified and I got them
right first time. But almost every *value* I actually had to read out of a memo
field -- what a `FONT` row contains, what `BINDING` looks like, what a menu row's
container flag is called, what determines a grid's wrap width, what
`ORIGIN_HEIGHT` is -- is either unnamed or contradicted by the fixtures. Two of
the five tables cannot be rendered correctly by a reader that follows the
contract literally.

---

## Contradictions

### C-1. Section 7's silent-drop rule makes section 11's menus unrenderable
**Sections 7 and 11.** Section 7: *"an unknown property is dropped silently,
never rejected (R3 -- import is an allow-list)."* Section 11 names exactly six
menu properties: `Caption`, `Key`, `Message`, `Checked`, `Enabled`, `Separator`.

`UIDEF_MENU.DBF` carries menu structure in properties that are in neither list:
`Container`, `Name`, `OpenedBy`, `OpenerPrompt`, `DeclaredItems`, `Mnemonic`,
`Mark`, `KeyLabel`, `SkipFor`. A conformant reader drops all nine. Having done
so it cannot tell a popup from an item, has no text at all for the seven bar
entries (the popup rows carry **no `Caption`** -- their label lives only in
`OpenerPrompt`), and has no mnemonics.

The allow-list rule and the menu vocabulary are individually reasonable and
jointly produce a blank menubar. I worked around it structurally: a `menu` row
that is the sole `menu` child of another `menu` row and has children of its own
*is* that row's popup. That is derivable from section 11's "nested by `PARENT`",
so it is legal, but the contract never states it and nothing hints at it.

### C-2. Section 11's `\<` and `\-` conventions are false against the data
**Section 11.** *"The `\<` mnemonic escape and `\-` separator convention are
inherited from the source vocabulary, which uses them consistently in both
captions and prompts (R8)."*

Measured in `UIDEF_MENU.DBF`: `\<` appears in **zero** of the 67 `Caption`
values. It appears only in `OpenerPrompt`, which section 11 does not mention.
Mnemonic position in `Caption` is instead carried by an integer `Mnemonic = N`.
`\-` appears **zero** times anywhere; separators are `Separator = .T.`.

"Consistently in both captions and prompts" is exactly wrong: it is used in
prompts and never in captions. I render bar labels from `OpenerPrompt` when a
popup exists so the mnemonics survive; that is a guess about which of two
disagreeing texts is the label.

### C-3. Section 9 enumerates two dispatches; the data has three
**Section 9.** *"`DISPATCH` is `ui` or `worker` (R11)."* Eighteen handlers in
`UIDEF_MENU.DBF` say `/ host` (`Click = edit.cut / host`). Section 9 says what
to do with an unknown *event name* ("dropped with a diagnostic") and says
nothing about an unknown dispatch. Section 12 says a generator "must implement
`DISPATCH`" -- implement an unspecified third value how? I diagnose and treat it
as `ui`. It could as defensibly have been a refusal, or a documented
host-delegation mode that section 9 forgot to list.

### C-4. Section 5's "never default an absent dimension" vs. section 5 needing one
**Section 5 and section 8's R16/R17 note.** *"An absent dimension is never
defaulted to a number."* / *"A control that does not state a size gets one from
its content and its font."* Applied to `FLOWDEMO`'s unbound `text` controls
(`T1`, `T2`, `T3`, `T9`: no `BINDING`, no `ORIGIN` at all) the two sentences
give: don't default it, and derive it from content -- of which an empty entry
box has none. The rule as written produces a zero-width text box. I default to
20 characters and log it as derived.

---

## Gaps

### G-1. A `grid` container has no stated wrap width, and no rule for a missing `Columns`
**Sections 3 and 5.** Section 5: *"`grid` | children in reading order, wrapping;
`SPAN` gives cells consumed."* Wrapping *at what*? Section 3 names `Columns` in
a parenthetical list of PROPS keys ("`Columns` on a `grid` container (R23.2)")
and never makes it required -- the `R` column for `PROPS` is `O`.

`FLOWDEMO.DBF` contains a group captioned **"Grid with no Columns -- must be
refused"**. The fixture asserts a rule the contract does not contain. Nothing in
the document says a grid without `Columns` is invalid; the natural reading of a
P/C/O schema where `PROPS` is `O` is that it is legal.

I refuse it, on the chain: section 5 forbids defaulting an absent dimension to a
number -> `Columns` is the grid's only dimension -> no layout is obtainable.
That chain is a construction of mine, not a statement of the contract's, and I
would not fault an implementer who defaulted to 1 column, or to `len(children)`,
or to 2. Three plausible readings, no text to choose between them. **This is the
single worst gap in the document** because it is the one place a fixture
declares an expectation the prose does not.

`--force` demotes the refusal to a diagnostic and lays it out in one column, to
produce `FLOWDEMO.png`.

### G-2. Nothing says what a `FONT` row contains
**Sections 2 and 3.** Section 2 gives `FONT` one line: *"one font metric row"*.
Section 3's field table describes `FONTREF` as an index into them. **The
properties of a `FONT` row are never named anywhere in the document.** I read
`Name` and `Size` off the fixtures, i.e. I reverse-engineered the format the
contract exists to make unnecessary.

`UIDEF_STUDENTS.DBF` also carries `Metrics = Arial, 0, 9, 5, 15, 12, 32, 3, 0` --
nine undocumented positional numbers. Since section 2 calls these "font *metric*"
rows, that tuple is plausibly the whole point of the record kind, and it is
undecodable. `Size` has no unit; I assumed points.

Section 14 item 6 half-admits this: *"`fontname`/`fontsize` are carried twice --
once raw, once resolved into `FONTREF` -- and `fontbold`/`fontitalic` are in
neither, so the `FONT` row is the incomplete copy."* That names four keys in
lowercase in a list of open defects; the fixtures use `Name` and `Size`. Even
the confession doesn't match the data.

### G-3. `FONTREF` indexes "this document's FONT rows" -- in what order?
**Sections 2 and 3.** Section 3: *"1-based index into this document's `FONT`
rows"*. Section 2 forbids the obvious answer: *"a conformant reader locates
records by `RECKIND`, **never by position**."* So the index cannot be into
physical record order. It must be into `ORDINAL` -- except `ORDINAL` is
documented as *"position among siblings"* and a `FONT` row has no siblings and
no `PARENT`. I use `ORDINAL` when every `FONT` row has a distinct non-zero one
and fall back to record order otherwise, and print which basis was used. Both
fixtures agree under either rule, so the ambiguity is invisible until it isn't.

Also unstated: whether `FONTREF` on a container is inherited by its descendants.
I do not inherit. No fixture distinguishes.

### G-4. No rule for a dangling `FONTREF`
**Section 3.** `FONTDEMO.DBF` has a label captioned "FONTREF 9 -- no such FONT
row" and there are three `FONT` rows. `0` is specified ("target default");
out-of-range is not. Given section 4's refuse-loudly stance on unknown `KIND`
("a document that looks correct and is not"), refusal is arguable. I diagnose
and fall back to the target default. Guessed.

### G-5. `ORIGIN_HEIGHT` is used by the data and named nowhere in the contract
**Section 8.** The section's worked example lists `ORIGIN_TOP`, `ORIGIN_LEFT`,
`ORIGIN_WIDTH`, `ORIGIN_SCALE`. `UIDEF_STUDENTS.DBF`'s form record carries
`ORIGIN_HEIGHT = 338`. The `ORIGIN_*` member set is never enumerated -- the
example is the only definition, and it is incomplete. I accept `ORIGIN_HEIGHT`
by analogy. There is no way to know from the document whether
`ORIGIN_BOTTOM` / `ORIGIN_RIGHT` / `ORIGIN_ZORDER` also exist.

### G-6. `ORIGIN_SCALE` enumerates five units and gives conversions for none
**Section 8.** *"`ORIGIN_SCALE` values: `px`, `pt`, `mm`, `in`, `cell`."* No
conversion factor to anything, and `cell` -- whose cell? -- is not defined at
all. Section 8 also insists a generator honouring a position *"must honour
`ORIGIN_SCALE` or refuse the row"*. Since honouring is impossible for four of
the five values, a conformant generator refuses every non-`px` row. That is what
mine does, and it is absurd. All five fixtures are `px`, so the enumeration has
never been exercised.

### G-7. `BINDING`'s syntax is undefined, and R17 cannot be implemented without it
**Sections 3, 8, 10.** Section 3: *"`BINDING` | data field this control reads
and writes."* That is the entire definition. R17 then makes `BINDING`
load-bearing: *"data-sized and **bound** | the bound field's declared width, in
characters."*

To get a declared width I must (a) parse `students.sid` into alias and field --
the contract never says `BINDING` is dotted, or that the left part is an alias,
or that it should be matched against `SOURCE.Alias`; (b) open `SOURCE.Table`;
(c) read a DBF field descriptor. None of (a)-(c) is described. Note the contrast
with `OBJID`, which section 3 explicitly marks *"Opaque; never parsed"* -- the
document knows how to say that when it means it, and says nothing here.

Related, unstated: what "declared width in characters" means for a numeric field
(`GPA` is `N(4,2)` -- 4 or 5?) or a date (`D` is 8 bytes, displayed as 10 with
separators). I used the DBF byte width.

### G-8. Section 10 fixes the path's base and says nothing about its case -- **and this bit me**
**Section 10.** *"`Table` is **relative to the UIDEF document's own location**,
never absolute and never a bare name resolved against ambient state."* The whole
section is about the *base* of resolution and is excellent on it.

`UIDEF_STUDENTS.DBF` says `Table = students.dbf`. The file beside it is
`STUDENTS.dbf`. On a case-sensitive filesystem the contract's rule resolves to
nothing. See W-1 for what that did.

### G-9. Nothing describes `pageset`/`page` behaviour, and `FLOW` on a `pageset` is meaningless
**Sections 4 and 5.** Section 4 lists `pageset` and `page` among the containers
and says nothing more; the word "tab" does not occur in the document. Section 3
marks `FLOW` *"P on containers"*, so `TABDEMO.DBF`'s pageset must carry one and
carries `free` -- which under section 5 means *"children positioned only by
`ORIGIN`"*, and there is no `ORIGIN` on it or its pages. I render a notebook and
ignore the `FLOW`, which is certainly what was meant and is not what the
document says. Section 14 item 3 concedes `pageset` had never been rendered
until the day this was written.

Equally unstated: whether `page` may appear outside a `pageset`, whether a
`pageset` may hold non-`page` children (I refuse), and what a `page`'s `Caption`
is for (I assume the tab label).

### G-10. `FLOW = free` with no `ORIGIN` anywhere has no rule
**Section 5b.** The correction proposes *"a generator that accepts `free`
**must** honour `ORIGIN`, since there is nothing else to lay the document out
with."* `FLOWDEMO.DBF`'s panel `P3` is `free` and neither it nor its child
carries any `ORIGIN` -- the child's caption is literally "free with no ORIGIN:
order is all a target has". So the fixture states the answer and the contract
does not. I stack in `ORDINAL` order and record it as derived.

Same class: section 8 says *"any member may be absent. Absence is normal"* and
gives partial-`ORIGIN` rates, but a `free` child with `ORIGIN_TOP` and no
`ORIGIN_LEFT` cannot be placed. I substitute 0 and log it.

### G-11. The R16/R17 size table covers 11 of the 14 kinds and never defines "data-sized"
**Section 8.** The four-row table names content-sized kinds explicitly, names
containers explicitly, and uses the undefined term *"data-sized"* for the rest.
`text`, `list`, `combo` and `image` appear in **no** row of it. I read
"data-sized" as the complement, which is the only available reading but is
inference.

### G-12. `Mask` and R17 give different widths, and nothing says which wins
**Sections 3 and 8.** `Mask` is a named key (R25). `O003` has
`Mask = "99,999,999"` (10 characters) bound to `STUDENTS.SID`, declared
`N(8,0)`. R17 says the bound field's declared width; the mask says 10. I use R17
and diagnose. Nothing in the document ranks them.

### G-13. No rule for which `KIND` may be a document root
**Sections 2, 3, 4.** Section 3 mentions "the root object" in passing (`PARENT`
is empty on it) and singular, but nothing says there is exactly one, nor which
kinds may be one. I refuse multiple roots and refuse a root that is not `form`
or `menu`, both invented.

### G-14. There is no way to tell a form document from a menu document
**Sections 2 and 11.** `UIDEF_MENU.DBF`'s `DOC` row carries `Kind = menu` -- an
undocumented `PROPS` key which section 7 orders me to drop silently. I detect it
from the root `OBJ`'s `KIND` instead, which works, but a document *is* "one form
or one menu" (section 1) and the contract provides no declaration of which.

### G-15. `image` names a kind and no property that carries a picture
**Sections 4 and 7.** `image` is in the fourteen. No `PROPS` key for its source
is named, and section 7 forbids interpreting property names as paths. An `image`
row is therefore unrenderable; my code refuses it. No fixture exercises it,
which is why it went unnoticed.

### G-16. `TABORDINAL` mandates a disclosure with no channel
**Section 3.** *"`0`/absent = the target derives it and must say so."* Same for
section 5's *"a reader that derives a dimension **must record that it derived
it**"* and section 12's *"records any dimension it derived"*. Say so **to whom,
in what form**? There is no diagnostic channel, log format, or sidecar defined.
I print a `DERIVED DIMENSIONS` block on stdout, which satisfies nobody
mechanically. A conformance requirement with no defined artifact cannot be
tested, which makes it decoration.

### G-17. `SPAN` overflow, `ORDINAL` gaps and duplicates are unhandled
**Sections 3 and 5.** `ORDINAL` allows gaps explicitly; duplicates are not
mentioned (my sort is stable, so ties fall back to record order -- forbidden by
section 2's never-by-position rule, so strictly I have no legal tie-break). A
`SPAN` larger than `Columns` has no rule; I clamp.

### G-18. Handler references are not names
**Section 9.** *"Each line is `Event = HandlerName / DISPATCH`."* Real values:
`Click = IIF(APP_GLOBAL.QueryDataSessionUnload(), / ui` and
`Click = APP_GLOBAL.ActivateSystemWindow("Command / ui` -- expressions,
truncated mid-string, containing commas, parens and unbalanced quotes.
"HandlerName" is a fiction; the field carries arbitrary host-language text.
Since it is undelimited I must split the dispatch off the **right**, which the
document does not say and which breaks silently the first time a handler
reference legitimately contains a trailing `/`.

### G-19. Section 7's value grammar does not cover the values present
**Section 7.** *"values: `"quoted string"`, a number, `.T.`/`.F.`, or bare
text."* Present in `UIDEF_MENU.DBF`: `Message = ""Creates a document""` (doubled
quotes -- an empty string then bare text, or an escaped quoted string? the
grammar admits no escape) and `Mark = "<NUL>"` (a literal 0x00 byte inside a
quoted string). "Bare text" as a catch-all makes the grammar unfalsifiable:
every malformed value is legal bare text.

---

## Ambiguities (chosen reading, and what else it could have meant)

- **A-1, section 12 / 5b -- `FLOW = free`.** Section 12 permits refusing it;
  5b measures that refusing it refuses 87.9% of real documents and calls the
  permission a defect against the draft; section 14 item 7 leaves it open. I
  **accept** `free`. Reading the permission literally instead would refuse
  `UIDEF_STUDENTS`, `TABDEMO` and part of `FLOWDEMO` -- three of the five
  fixtures -- and would still be conformant. **A specification whose two
  defensible readings differ on 60% of the test corpus has not specified
  anything.**
- **A-2, section 8 -- `ORIGIN` positions.** Section 12: a generator *"may ignore
  `ORIGIN` **positions**"*. I honour them (5b says a `free` acceptor must). A
  generator that ignores positions and accepts `free` is explicitly permitted
  and renders every imported form as a pile at the origin.
- **A-3, section 11 -- `Key`.** Label or binding? I display it as an accelerator
  and bind nothing. It could equally be a required keyboard registration.
- **A-4, section 11 -- `Mnemonic = N`.** Undocumented; read as a 0-based
  underline index. `Mnemonic = 0` is then indistinguishable from absent, and
  values like `Mnemonic = 4` on `"Print..."` (-> `t`) suggest I have the
  convention wrong. I drop it and take mnemonics from `\<` in `OpenerPrompt`
  instead.
- **A-5, section 13 -- `SkipFor`.** *"v1 carries them as opaque text in `PROPS`
  **or refuses them**"*. Two opposite behaviours offered with no criterion. I
  carry and ignore, leaving items enabled that VFP would grey out.
- **A-6, section 6 -- what a reader does with a missing `P` field.** *"A reader
  may still find it absent in a non-conformant document and **should say so**"* --
  say so and continue, or say so and stop? I continue except where the field is
  also `C`. The three-value model is the document's best idea and its
  consumer-side behaviour is still a `should`.
- **A-7, section 2 -- `RECKIND` case and padding.** `C(4)` holding `DOC`; case is
  never stated (property *names* are explicitly case-insensitive, `RECKIND` is
  not). I upper-case and strip.

---

## Things I got wrong first (the valuable ones)

### W-1. I implemented `SOURCE.Table` exactly as section 10 says and silently rendered every field at the wrong width
This is the important one. Section 10 is emphatic and precise about resolution
*base*. I implemented it literally, the lookup of `students.dbf` failed against
the on-disk `STUDENTS.dbf`, R17 had no schema to consult, and the code fell
through to the *unbound* branch -- `ORIGIN_WIDTH` divided by a character cell.

**The form rendered. It looked completely plausible.** Nine text boxes,
sensible-looking widths, no error. I only caught it because I had written the
`SOURCE.Table resolved to ...` diagnostic and noticed it said "not found". Had I
not been logging, I would have shipped it and reported success.

That is precisely the failure mode section 4 exists to prevent -- *"an importer
that emits an empty box for something it does not understand produces a document
that looks correct and is not"* -- reproduced by following the contract to the
letter. The contract's refusal machinery is aimed at unknown `KIND` and has
nothing to say about a silently-unresolvable `SOURCE`, which is a far easier
mistake and has worse consequences. **Section 10 should require a reader to
refuse a document whose `SOURCE.Table` does not resolve, since R17 makes correct
sizing depend on it.** It does not.

### W-2. I expected R16/R17 to make imported forms *more* correct. It makes them collide.
Section 8's replacement table governs size and says *"position is unaffected"*.
Applied to `UIDEF_STUDENTS`: positions are honoured from `ORIGIN` (authored in a
9px-cell font) while every label is re-sized to its content in Tk's font and
every bound entry is re-sized to its schema width. In `UIDEF_STUDENTS.png` the
label "Enroll_d:" now runs into its entry box, and `EMAIL` (R17: 40 chars, about
366px) is substantially wider than the authored `ORIGIN_WIDTH = 290`, pushing
past the form's own extent.

R16/R17 fix truncation by inflating sizes inside a coordinate system that was
laid out for the old sizes. The evidence cited (`AIF120_width_ace.png`,
r = 0.9982) measures the correlation and does not measure the collision.
**Honouring position and re-deriving size is not a coherent combination and the
contract mandates exactly it.** This surprised me; I expected the rule to be an
improvement and it is a different bug.

### W-3. I assumed a menu row was a menu item. Half of them are popups.
Section 11 reads as one flat statement: *"Menu rows are `OBJ` with `KIND = menu`,
nested by `PARENT`, ordered by `ORDINAL`."* My first tree walk treated every
`menu` row as an entry and produced a menubar with **17** top-level entries
(7 real bar items interleaved with 10 popup container rows). The actual model is
a strict alternation -- bar -> item -> popup -> item -> popup -- where a popup is
a child of *the item that opens it*. Section 11 does not mention that popups
exist as records, let alone that they alternate. Fixed structurally (C-1).

### W-4. `FLOWDEMO`'s `--force` render shows what defaulting `Columns` costs
When I built the `--force` path and defaulted the missing `Columns` to 1, the
group rendered as three stacked labels and looked entirely reasonable. Nothing
about the output says "this layout was invented". That is why G-1 matters: the
permissive reading of the contract is not detectably wrong from the render, and
the contract offers no reason to prefer the strict one.

### W-5. The imported form is missing its ten buttons and the contract calls that conformant
`UIDEF_STUDENTS`'s panel `O020` has no child records at all. Its ten buttons
exist only as dotted property names inside its own `PROPS`
(`cmdadd.caption = "\<Add"`, `cmdprev.enabled = .F.`, ...). Section 13 / R6 says
implicit children are out of v1, so a conformant reader renders an empty panel --
and because the panel also carries no `ORIGIN_WIDTH`/`HEIGHT`, it renders as
nothing at all. The screenshot is a data-entry form with no navigation bar and
no indication that anything is missing. That is section 4's own stated failure
mode, produced by a rule section 13 states deliberately.

---

## What was clear

Credit where due -- these told me exactly what to do and I implemented them
without hesitating:

- **Section 2, the three record kinds, and "locate by `RECKIND`, never by
  position."** Unambiguous, easy to implement, and immediately correct on all
  five tables. The explicit warning not to inherit `.SCX`'s header-first
  font-table-last convention is the kind of thing specifications usually omit.
- **Section 6, the three-value requiredness model.** The sharpest idea in the
  document and correctly argued. The `.SCX`/`CLASS`/`BASECLASS` worked example
  makes P-vs-C concrete in two sentences, and the `RESERVED4` anecdote earns the
  `O` category. I structured my validation around P/C/O directly.
- **Section 4's refusal rule.** *"Must refuse the document and name the kind. It
  must not render a placeholder."* Unambiguous, testable, and I implemented it as
  one line. The rationale is the best sentence in the document.
- **Section 3's field table.** Types, widths and the `R` marks are complete and I
  never had to guess a field's meaning -- only its *contents*.
- **Section 7's property mini-language.** One property per line, `name = value`,
  CRLF, names case-insensitive, unknown keys dropped. I wrote one 12-line parser
  and it handled `PROPS`, `ORIGIN`, `HANDLERS` and `SOURCE` because sections 8-10
  each say "same property text form". That reuse is good design and clearly
  stated. The case-insensitivity ruling in particular saved me: `FLOWDEMO` writes
  `Caption` and `UIDEF_STUDENTS` writes `caption`.
- **Section 8's "a row with `ORIGIN_*` and no `ORIGIN_SCALE` is invalid"** and
  **"`ORIGIN_SCALE` is per group, not per document"**, with the
  ten-thousandths-of-an-inch measurement behind it. A crisp validity rule with an
  empirical reason.
- **Section 11's "a menu row must not carry `ORIGIN`."** A flat prohibition with
  a count behind it (four `.MNX`, 205 records, zero geometry columns). One line
  of validation.
- **Section 5's `row`/`column`/`grid` semantics and `SPAN`'s default of 1.**
  Correct on the first run for `FLOWDEMO`'s row panel, column panel and 2-column
  grid with a spanning row.
- **Section 9's dispatch defaulting to `ui`,** with the reason given (loud
  failure beats intermittent corruption). I never had to wonder.
- **Section 14's honesty.** Struck-through items, "the measurement was wrong
  twice", and item 4 conceding this very gate was *"Spiked, not met. The Tk
  consumers were written by the same author as the table."* A document that
  records what it got wrong is far more usable than one that doesn't -- section
  5b's withdrawn-and-preserved framing is the reason I accepted `FLOW = free`
  rather than exercising section 12's permission to refuse it.

---

## The one-line verdict

The contract answers *"how is a UIDEF document structured?"* completely and
*"what is in one?"* barely. A second implementer can build the tree, validate
requiredness and refuse correctly; they cannot render a font, size a bound
control, or draw a menu without reverse-engineering the fixtures -- which is the
exact activity section 1 promises is unnecessary (*"A consumer needs **only this
document and a DBF reader**"*). That promise is not met. The nearest fixes, in
order of value: name the `FONT` row's properties; define `BINDING`'s syntax and
require refusal when `SOURCE.Table` does not resolve; state the grid wrap rule;
promote the menu structure keys out of the silent-drop allow-list; and either
give `ORIGIN_SCALE` conversions or cut the enumeration down to `px`.
