# R127 -- what a command-reference page is composed of

    Run    : DOCFLUSH-20260812-001 (flush v5) / COWORK-20260825-001
    Ruled  : 2026-08-25, member.derald
    Number : R127, next free after R126 (`highest: R126` from the R-number
             collision gate at `2bca2a60a`).
    Lane   : AIF-068. No new AIF.
    Status : review-needed. The author does not self-approve.

---

## 1. Why this was asked

Phase 6's remaining content work is 20 supported commands with no page. The
generator that would build them keys each page on ONE `TOPICKEY`, and
measurement showed that for several of the 20 the command's evidence is split
across catalogs, so the page would carry a fraction of it silently.

    BROWSETV   DOT|BROWSETV  3 lines     UI|BROWSETV  41 lines
    FORMULA    DOT|FORMULA  15 lines     EDU|FORMULA  53 lines
    BOOLEAN    DOT|BOOLEAN  15 lines     EDU|BOOLEAN  32 lines
    AVERAGE    DOT|AVERAGE   3 lines     FOX|AVERAGE   3 lines
    REL_LIST   DOT|REL_LIST  3 lines     FOX|REL_LIST  3 lines

**It is not two subjects. It is one command, mined twice.** `DOT|BOOLEAN`'s
SYNTAX lines cite `src/edu/edu_boolean.cpp:79 pattern=usage_output_block`;
`EDU|BOOLEAN`'s USAGE lines cite `src/edu/edu_boolean.cpp:18
pattern=usage_contract`. Same source file, two collectors, two catalog keys,
and the page builder picks one.

SCALE: **160** DOT topics have a same-name sibling in another catalog; **29**
have a sibling carrying more lines than the DOT topic.

## 2. The ruling, three parts

### 2a. Which catalogs compose a developer command page

**DOT + FOX + UI + DEV.** A page for a DOT command may absorb the lines of a
same-TOPIC sibling in those catalogs.

**EDU, EXT, INTERNAL and ED do not compose.** They are separate surfaces with
their own homes -- `EDU|BIBLETALK` is 125 lines of lesson material and
`INTERNAL|LOOP_BUFFER` is internal notes; neither belongs in a developer
command reference merely because a command shares its name. Their existence is
recorded as a cross-reference, NOT silently dropped.

FOX earns its place even though its siblings are mostly three-line stubs: the
one SYNTAX line `FOX|AVERAGE` carries is the full xBase form --
`AVERAGE <expr> TO <memvar> [ALL|DELETED] [FOR <pred>] [WHILE <pred>]
[NEXT <n>|REST]` -- which `DOT|AVERAGE` does not have at all.

### 2b. A source contract makes a command supported -- unless its own status says otherwise

**Owner's rule, 2026-08-25: "once a source file has a contract it is
supported."**

MEASURED AGAINST THE STORE, and the store already half-agrees:

    topics carrying pattern=usage_contract : 215
      marked SUPPORTED                     : 186
      NOT marked SUPPORTED                 :  29

    of those 29, by their OWN status= marker:
      status=supported              11   EDU|ASCII BIBLETALK BOOLEAN CASE
                                         CHRISTMAS COBOL EDIT ERP EVALUATE
                                         FORMULA HANUKKAH TEXT
      status=supported-conditional   4   UI|ARCTICTALK FOXPRO RECORD RECORDVIEW
      status=developer / dev-tool    7   UI|BROWSETV UI|GENERIC DEV|HIER
                                         INTERNAL|{LOOP,SCAN,UNTIL,WHILE}_BUFFER
      status=experimental            1   DOT|TRANSACTION
      status=sample-extension        2   EXT|STUDENTECHO EXT|STUDENTHELLO
      status=backend-helper          1   EDU|IDX
      status=implementation-present  1   EDU|SIX

**FIFTEEN TOPICS DECLARE `status=supported` OR `supported-conditional` IN THEIR
OWN CONTRACT WHILE `HELP_TOPIC.SUPPORTED` SAYS FALSE.** That is two answers to
one question inside one store -- the R5 shape -- and it means the rule is not a
policy being imposed. It is the store being made to agree with itself.

**But a contract is not a blanket.** `experimental`, `sample-extension`,
`backend-helper` and `implementation-present` are the contract's OWN words for
"not that". So:

> A usage contract makes the marker AUTHORITATIVE. The marker, not the
> contract's mere presence, says whether the command is supported.

### 2c. `developer` is an AUDIENCE, not a denial of support

**Owner's qualifier, same exchange: "but that doesn't mean its not dev
though."**

`UI|BROWSETV`, `UI|GENERIC`, `DEV|HIER` and the four `INTERNAL|*_BUFFER` topics
all carry contracts and all say developer. They are supported AND developer;
the two are orthogonal axes and neither implies the other.

Consequence for composition: when a page absorbs a sibling that is
developer-marked, **the page must carry that forward.** A developer tool
presented as general-audience reference is a worse defect than a thin page.

## 3. What this does NOT rule

- **The `status=` vocabulary is uncontrolled -- NINETEEN distinct spellings**
  across contract-bearing topics: supported, supported-conditional,
  supported-stub-mixed, active, implementation-present, implementation-shim,
  implementation-helper, dev-tool, developer, dev-canary, experimental, stub,
  deprecated, deprecated-compat, compatibility-alias, document-control-readonly,
  backend-helper, sample-extension, review-needed. **2b makes that string
  load-bearing, so it now needs a closed set.** Named as a dependency of this
  ruling and NOT ruled here; it is a separate lane.
- Whether `HELP_TOPIC.SUPPORTED` should be repaired at the source, or the
  contract read at render time. 2b says which is authoritative; it does not say
  who writes the correction.
- The 26 sibling-richer cases outside the 20 (2a applies to them, but no page
  is built for them by this ruling -- owner's scope call, "rule now, apply to
  the 20").
- The 191 already-accepted pages are NOT reopened.

## 4. Scope of application

**Rule now, apply to the 20** (owner, 2026-08-25). The ruling stands for the
whole manual; only the 20 written-debt pages are built under it. The other 26
are a measured backlog with the ruling already made, so the next session
inherits an answer rather than the question.

## 5. Implementation note -- the renderer is NOT touched

`_render_page` derives its entire header block from the `topic` dict it is
handed (CATALOG, TOPIC, STATUS, SUPPORTED, IMPLEMENT, PRIMARY, CONFID) and
computes its own attention banner from STATUS and SUPPORTED. So composition is
done by the GENERATOR handing a composed topic record and a merged line set;
`manualgen_lib/command_reference_candidate.py` is unchanged.

That matters: the renderer is shared with the 191 accepted pages, and changing
it would retroactively redefine them.

**KNOWN LIMIT, stated rather than hidden:** carrying the developer audience
into the page BODY as its own marked field would require a renderer change.
Under this ruling the composition is recorded in the page's Catalog field
(`DOT+UI`) and in full in the lineage CSV and manifest. If 2c is judged to need
a body-level audience banner, that is a renderer change and a separate
authorization.

## 6. Good neighbour

    What changed:      this ruling and its register row. No code, no page.
    Whose area:        AIF-068 / full_stack_documentation, manualgen.
    Authorization:     member.derald, 2026-08-25 -- catalog set chosen from
                       four options, scope chosen from three, plus the two
                       rules in 2b and 2c given in his own words.
    How to verify:     section 2b's counts reproduce from
                       `harvested/HELP_HELP_LINE.csv` and
                       `harvested/HELP_HELP_TOPIC.csv` -- count topics whose
                       lines contain `pattern=usage_contract`, join to the
                       topic table on TOPICKEY, and split on SUPPORTED.
    How to undo:       revert. Nothing downstream consumes it yet.
