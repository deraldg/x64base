// @dottalk.file v1
// subsystem: include
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <string>
#include <string_view>
#include <vector>

namespace edref {

// What an entry IS. Before 2026-08-15 every entry was implicitly a concept
// page, so 29 entries sat in one undifferentiated pile and the catalog could
// not tell a definition from a drill.
//
// LAB IS DELIBERATELY ABSENT (owner ruling 2026-08-15): labs stay in LabTalk.
// EDREF points at them via `lab_ref` and does not hold them. One home per
// artifact -- the same rule that keeps the theme control in one place.
enum class Kind {
    Concept,     // what a thing is. The 29 originals.
    Example,     // worked, and RUNNABLE -- pair with script_ref.
    Exercise,    // the student produces something.
    StudyGuide,  // review / end-of-chapter consolidation.
    Assessment,  // self-check with a knowable answer.
    Glossary,    // terminology lookup.
};

// Who the entry is pitched at. Owner 2026-08-15: college is the target, and
// high-school AP is a good target too. Both is the default because most
// concept text serves both, and marking the exceptions is cheaper than
// marking the rule.
enum class Level {
    Both,
    Ap,       // AP Computer Science scope.
    College,  // assumes more, e.g. complexity analysis.
};

struct Item {
    const char* topic;    // canonical upper-case topic name
    const char* syntax;   // short form / heading
    const char* summary;  // full teaching text
    bool supported;       // whether the topic reflects current DotTalk++ behavior

    // One sentence, <= 80 chars. THE COMPILED FALLBACK'S ENTIRE TEXT.
    //
    // Positioned here, immediately after `supported`, on purpose: C++20 forbids
    // mixing designated and positional initialisers in one braced list, so a
    // field the 29 existing positional entries must supply cannot sit after the
    // designated-only block below. It is the fifth positional slot.
    //
    // Why it exists (measured 2026-08-16). HELP_TOPIC.TITLE is C80 and, for all
    // 29 ED rows, merely echoes TOPIC -- helpdata_export_dbf.cpp:362 sets
    // `row.title = command.empty() ? key : command`. Meanwhile SUMMARY is C200
    // and every one of the 29 rows sits at 195-200 chars: it is the prose HARD
    // TRUNCATED, not a summary, so it reads as a sentence cut in half. So the
    // catalog had no one-line summary anywhere, in either the header or the DBF.
    // SYSTEM rows already use TITLE meaningfully (138 of 138), so filling it for
    // ED follows existing practice rather than bending the schema.
    //
    // 80 is a discipline, not a limit to fill: if it does not fit in a sentence
    // it is not a summary.
    const char* title = "";

    // --- added 2026-08-15, BEFORE population, deliberately -------------------
    // Every field below carries a default, so the 29 existing brace
    // initialisers still compile unchanged (C++20 permits aggregates with
    // default member initialisers). New entries should use designated
    // initialisers: { .topic = "...", .kind = Kind::Exercise, ... }.
    //
    // Doing this at 29 entries rather than 200 is the whole point. The shape
    // of a catalog is cheap to change while it is still mostly empty and
    // ruinous afterwards.

    Kind kind = Kind::Concept;
    Level level = Level::Both;

    // Reading order. 0 means unplaced -- a topic that exists but has not been
    // given a home in the syllabus yet. A vector has array order; a course
    // needs a stated one, and the difference should be visible.
    int sequence = 0;

    // Comma-separated topic names that must be understood first. This is the
    // syllabus DAG: INDEX needs TABLE_RECORD_FIELD, PROJECTION needs RELATION.
    // Checkable -- a prereq naming a topic that does not exist is a defect a
    // tool can find, which is more than most curricula can say.
    const char* prereq = "";

    // Path, repo-relative, to a .dts script that DEMONSTRATES this entry.
    //
    // This is the field that makes EDREF unlike a textbook. Point it at a
    // script under tests/ and the regression harness EXECUTES the teaching
    // material. An example that stops working breaks a test instead of
    // quietly misleading a student for a year. Every programming text ever
    // printed contains code that no longer runs; this one is structurally
    // incapable of it.
    //
    // Empty means "no script yet", which is honest. It does NOT mean "no
    // script needed" -- tools/fullstack_docs/edrefcheck_v1.py reports the
    // count of Example entries lacking one, because an unrunnable example is
    // the thing this field exists to prevent.
    const char* script_ref = "";

    // LabTalk lab this entry leads into, by id. EDREF does not hold labs.
    const char* lab_ref = "";
};

inline const char* kind_name(Kind k) {
    switch (k) {
        case Kind::Concept:    return "concept";
        case Kind::Example:    return "example";
        case Kind::Exercise:   return "exercise";
        case Kind::StudyGuide: return "study-guide";
        case Kind::Assessment: return "assessment";
        case Kind::Glossary:   return "glossary";
    }
    return "concept";
}

inline const char* level_name(Level l) {
    switch (l) {
        case Level::Both:    return "ap+college";
        case Level::Ap:      return "ap";
        case Level::College: return "college";
    }
    return "ap+college";
}

inline const std::vector<Item>& catalog() {
    static const std::vector<Item> k = {

        {
            "INTRO",
            "INTRO",
R"(DotTalk++ Educational Reference

Purpose
    EDREF is the instructional help catalog for learning DotTalk++ as a system.

What belongs here
    - programming concepts shown by DotScript and command flow
    - data concepts such as tables, records, fields, indexes, and relations
    - engine concepts such as metadata, tuple projection, ordering, buffering
    - practical examples written in the style of DotTalk++ commands

What does not belong here
    - FoxPro compatibility syntax reference itself
    - raw command catalog material already kept in foxref.hpp / dotref.hpp

Teaching approach
    This file explains the system in plain language.
    It is meant to answer:
        "What is this feature for?"
        "How do I think about it?"
        "What is the simplest example?"
        "How does it relate to the larger engine?" )",
            true,
            "What EDREF is, and what belongs in it."
        },

        {
            "MODEL",
            "SYSTEM MODEL",
R"(How to think about DotTalk++

DotTalk++ is best understood as four layers working together:

1. Command Layer
    The CLI accepts commands such as:
        USE
        SELECT
        LIST
        SET ORDER
        SET RELATION
        REL ENUM

2. Data Layer
    The engine works with:
        tables
        records
        fields
        indexes
        relations

3. Logic Layer
    DotScript and command execution provide:
        sequential flow
        decision flow
        looping flow
        expression evaluation

4. View / Projection Layer
    Results are shown through:
        LIST
        DISPLAY
        TUPLE
        SMARTLIST
        REL ENUM
        browser commands

A practical mental model
    Table       = stored rows
    Record      = one row
    Field       = one column value in a row
    Index       = alternate ordered path through rows
    Relation    = parent-child path between tables
    Tuple       = projected logical row, possibly across multiple tables )",
            true,
            "DotTalk++ understood as four layers working together."
        },

        {
            "SEQUENTIAL",
            "SEQUENTIAL EXECUTION",
R"(Programming Construct 1: Sequential Flow

Definition
    Sequential flow means commands run one after another in the order written.

Why it matters
    Most DotTalk++ scripts are fundamentally sequential.
    The result of one step prepares the next step.

Example
    WORKSPACE OPEN DBF
    SELECT STUDENTS
    SET INDEX TO students.cdx
    SET ORDER TO TAG LNAME
    LIST 5

What happens
    1. Open tables
    2. Select STUDENTS
    3. Attach the container
    4. Activate the LNAME order
    5. Print rows

Teaching point
    In sequential flow, state accumulates.
    Later commands depend on earlier commands.

Common mistake
    Forgetting that SELECT changes the active work area before the next command runs.)",
            true,
            "Commands run in order, one after another: the first control construct."
        },

        {
            "DECISION",
            "DECISION / IF",
R"(Programming Construct 2: Decision Flow

Definition
    Decision flow chooses between alternatives based on a condition.

Current DotTalk++ form
    IF <expr>
        ...
    ELSE
        ...
    ENDIF

Concept
    IF asks a yes/no question.
    If true, the IF branch runs.
    Otherwise, the ELSE branch runs, if present.

Example
    IF GPA > 3.5
        ECHO HONOR STUDENT
    ELSE
        ECHO REGULAR STUDENT
    ENDIF

Educational importance
    This is how a script becomes selective instead of merely linear.

Typical uses
    - react to a calculation
    - guard a destructive operation
    - separate normal and exceptional paths

Teaching point
    Decision logic is about controlling execution, not merely testing truth.)",
            true,
            "IF and ELSE choose between alternatives on a condition."
        },

        {
            "LOOPS",
            "LOOPS",
R"(Programming Construct 3: Iteration / Looping

Definition
    A loop repeats work.

DotTalk++ loop families
    LOOP ... ENDLOOP
    WHILE ... ENDWHILE
    UNTIL ... ENDUNTIL
    SCAN ... ENDSCAN

1. LOOP
    Repeats a fixed number of times.

    Example
        LOOP 3 TIMES
            ECHO HELLO
        ENDLOOP

2. WHILE
    Repeats while a condition stays true.

    Example concept
        WHILE counter < 10
            ...
        ENDWHILE

3. UNTIL
    Repeats until a condition becomes true.

4. SCAN
    Record-oriented loop over table rows.

    Example
        SCAN
            TUPLE *
        ENDSCAN

Teaching point
    LOOP / WHILE / UNTIL are general control-flow constructs.
    SCAN is a data-aware loop specialized for table traversal.)",
            true,
            "LOOP, WHILE, UNTIL and SCAN: four ways to repeat work."
        },

        {
            "SCAN",
            "SCAN AS A DATA LOOP",
R"(SCAN deserves special emphasis.

What SCAN is
    SCAN is not just a general loop.
    It is a record-processing loop tied to the current work area.

What it does
    It iterates record by record through the active table context,
    respecting the current order and, where applicable, filtering behavior.

Example
    SELECT BUILDING
    SCAN
        TUPLE *
    ENDSCAN

What students should learn
    - SCAN is the database equivalent of "for each row"
    - SCAN makes table traversal explicit
    - SCAN is usually more educational than hiding iteration inside a command

Related idea
    LIST shows records.
    SCAN processes records.)",
            true,
            "The record-oriented loop: a loop that knows about rows."
        },

        {
            "STATE",
            "ENGINE STATE",
R"(State is one of the most important DotTalk++ concepts.

Definition
    State means the current internal condition of the session.

Examples of session state
    - current work area
    - current table
    - current record pointer
    - active order/tag
    - active filter
    - relation graph
    - buffering on/off
    - path settings

Why it matters
    Commands do not operate in a vacuum.
    They operate against the current state.

Example
    SELECT STUDENTS
    SET ORDER TO TAG LNAME
    SEEK TAYLOR

Here SEEK depends on:
    - STUDENTS being current
    - an order being active
    - the key format of that order

Teaching point
    Learning DotTalk++ means learning stateful programming.)",
            true,
            "What the engine remembers between one command and the next."
        },

        {
            "WORKAREA",
            "WORK AREAS",
R"(A work area is an active slot that can hold an open table.

Think of it as
    a numbered table handle
    or
    a live table workspace

Typical commands
    SELECT
    AREA
    DBAREA
    DBAREAS
    WORKSPACE OPEN DBF

Example
    SELECT STUDENTS
    SELECT ENROLL

Meaning
    SELECT switches the active work area to the named table.

Why work areas matter
    Relations, tuple projections, and cross-area logic all depend on multiple
    open tables existing at the same time.

Teaching point
    A work area is not merely a filename.
    It is a live operational context.)",
            true,
            "An active slot that can hold one open table."
        },

        {
            "TABLE_RECORD_FIELD",
            "TABLE / RECORD / FIELD",
R"(Core data hierarchy

Table
    A collection of records with a defined structure.

Record
    One row in a table.

Field
    One named value inside a record.

Example
    Table: STUDENTS
    Record: the current student row
    Fields:
        SID
        LNAME
        FNAME
        GPA

Typical commands
    STRUCT
    FIELDS
    DISPLAY
    TUPLE *
    REPLACE FNAME WITH "Derald"

Teaching point
    Most command behavior becomes clearer once this hierarchy is firm:
        table > record > field )",
            true,
            "The core hierarchy: tables hold records, records hold fields."
        },

        {
            "METADATA",
            "METADATA",
R"(Metadata = data about data.

Examples of metadata in DotTalk++
    - field names
    - field types
    - field lengths
    - decimal counts
    - record length
    - active order name
    - index file name
    - table path
    - logical table name

Commands that expose metadata
    STRUCT
    FIELDS
    AREA
    STATUS
    SHOW
    TUPTALK PUSH ROW / PUSH ALL

Why metadata matters
    Metadata is how the engine knows how to interpret bytes as meaningful values.

Educational use
    Metadata teaches students that a database row is not just raw text.
    It is structured according to schema rules.

Important distinction
    Data      = "Taylor"
    Metadata  = field FNAME, type C, len 15 )",
            true,
            "Data about data: what the engine knows about your tables."
        },

        {
            "SCHEMA",
            "SCHEMA / DDL",
R"(Schema means the structural definition of a table or dataset.

A schema answers questions like
    - what fields exist?
    - what types are they?
    - how wide are they?
    - what tables belong to this dataset?

Commands related to schema and live state
    DDL       - schema/definition work
    STRUCT    - current table structure
    FIELDS    - current table field list
    VALIDATE  - validation work
    WORKSPACE - live open-area/session layout, not schema definition

Compatibility notes
    SCHEMA is a deprecated alias for DDL.
    SCHEMAS is a deprecated compatibility shim for WORKSPACE.

Educational value
    Schema is the bridge between storage and meaning.

Example
    STUDENTS:
        SID       N(8,0)
        LNAME     C(20)
        FNAME     C(15)
        DOB       D
        GPA       N(4,2)

Teaching point
    Without schema, bytes are only bytes.
    With schema, bytes become records and fields.)",
            true,
            "The structural definition of a table or dataset."
        },

        {
            "INDEX",
            "INDEXES AND ORDERING",
R"(An index provides an alternate path through records.

Physical order
    The natural storage order in the table.

Indexed order
    An order defined by a tag or key expression.

Typical commands
    SET INDEX TO students.cdx
    SET ORDER TO TAG LNAME
    TOP
    SEEK TAYLOR
    FIND TAYLOR

Why indexes matter
    They change navigation behavior.
    They make seeks possible.
    They define logical ordering independent of physical storage order.

Teaching point
    An index does not usually change the record data itself.
    It changes how the engine reaches the records.)",
            true,
            "An alternate path through records, without moving them."
        },

        {
            "ORDER",
            "ORDER AND NAVIGATION",
R"(Order means the currently active navigation sequence.

Examples
    physical order
    LNAME order
    FNAME order

Commands
    SET ORDER TO TAG LNAME
    SET ORDER TO 0
    ASCEND
    DESCEND
    TOP
    BOTTOM
    SEEK
    FIND

Educational point
    TOP is not an abstract idea.
    TOP means "first row in the current order."

So:
    TOP in physical order may differ from
    TOP in indexed order.

This is one of the most important database-learning moments in DotTalk++.)",
            true,
            "The navigation sequence currently in force."
        },

        {
            "FILTER",
            "FILTERING",
R"(Filtering limits visible or processed rows according to a condition.

Common surfaces
    SET FILTER TO <expr>
    LOCATE FOR <expr>
    COUNT FOR <expr>
    SMARTLIST ... FOR <expr>
    SCAN FOR <expr>

Concept
    A filter is a logical gate placed in front of the row stream.

Example
    SMARTLIST 10 FOR GPA >= 3.5

Teaching point
    Filtering is not the same as ordering.
    Ordering rearranges rows.
    Filtering removes non-matching rows from consideration.)",
            true,
            "Limiting which rows are visible, by a condition."
        },

        {
            "PREDICATE",
            "PREDICATES AND BOOLEAN LOGIC",
R"(A predicate is a true/false expression.

Examples
    GPA > 3.5
    LNAME = "TAYLOR"
    GPA >= 2 AND GPA <= 4

Used by
    IF
    LOCATE
    COUNT
    WHERE
    SMARTLIST
    SET FILTER

Boolean logic words
    AND
    OR
    NOT

Teaching point
    Predicates are the language of selection.
    They control decisions, filters, and searches.)",
            true,
            "A true/false expression that decides what qualifies."
        },

        {
            "EXPRESSION",
            "EXPRESSIONS",
R"(An expression is something the engine evaluates to produce a value.

Kinds of expressions
    numeric
    character
    date
    logical

Examples
    1 + 2
    UPPER("abc")
    GPA + 0.01
    DATE() + 2
    LNAME = "TAYLOR"

Commands using expressions
    CALC
    EVAL
    REPLACE
    IF
    LOCATE
    SMARTLIST

Teaching point
    Expressions produce values.
    Predicates are expressions whose value is true or false.)",
            true,
            "Something the engine evaluates to produce a value."
        },

        {
            "TUPLE",
            "TUPLE / LOGICAL ROW",
R"(A tuple is a projected logical row.

Why tuple matters
    A tuple does not have to be identical to one physical DBF record.
    It can be:
        - all fields from one area
        - selected fields from one area
        - mixed fields from several areas

Examples
    TUPLE *
    TUPLE LNAME,FNAME
    TUPLE #11.*
    TUPLE #9.*,#11.LNAME

Educational meaning
    Tuple is your view of the data.
    It is the row as selected for output or processing.

This is a major bridge toward relational thinking.)",
            true,
            "A projected logical row, assembled across related areas."
        },

        {
            "RELATION",
            "RELATIONS",
R"(A relation connects a parent table to a child table.

Example
    STUDENTS -> ENROLL ON SID
    ENROLL   -> CLASSES ON CLS_ID

Meaning
    If the current STUDENTS row has SID = 50000020,
    the child ENROLL rows with that SID are related rows.

Public surfaces
    SET RELATION TO SID INTO ENROLL
    REL ADD STUDENTS ENROLL ON SID
    REL LIST
    REL LIST ALL
    REL REFRESH

Teaching point
    Relations are the backbone of multi-table thinking.
    They let a current parent row lead you into matching child rows.)",
            true,
            "A declared link from a parent table to a child table."
        },

        {
            "REL_ENUM",
            "REL ENUM",
R"(REL ENUM is the relation-walk projection engine.

What it does
    It walks a relation path and emits tuple rows.

Example
    REL ENUM LIMIT 10 ENROLL CLASSES TASSIGN TEACHERS TUPLE ;
        STUDENTS.SID,STUDENTS.LNAME,ENROLL.CLS_ID,CLASSES.CID,TEACHERS.LNAME

How to think about it
    Start at current parent row.
    Walk child by child.
    For each complete path, emit one logical row.

Educational value
    REL ENUM is the clearest current demonstration that DotTalk++
    is more than a single-table shell.
    It is a relation-aware projection engine.)",
            true,
            "The relation-walk projection engine."
        },

        {
            "ENUM",
            "ENUMERATION",
R"(Enumeration means generating a sequence of results one by one.

Examples in DotTalk++
    - SCAN enumerates records
    - LIST enumerates visible rows for display
    - REL ENUM enumerates relation paths
    - directory commands enumerate files

Why the concept matters
    Many engine features are fundamentally enumerators.

Teaching point
    Enumeration is how a system turns stored data into a visible stream of results.)",
            true,
            "Generating a sequence of results one at a time."
        },

        {
            "BUFFERING",
            "TABLE BUFFERING",
R"(Buffering means changes are staged before permanent commit.

Commands
    TABLE ON
    REPLACE ...
    COMMIT
    ROLLBACK   (planned/deferred in some contexts)

Observed model
    With TABLE ON:
        TUPLE may show buffered values immediately
        LIST may still show persisted/indexed values until COMMIT

Educational point
    Buffering separates:
        working state
        persisted state

This is a classic database concept and an important teaching tool.)",
            true,
            "Staging changes before they become permanent."
        },

        {
            "COMMIT",
            "COMMIT",
R"(COMMIT makes staged changes permanent.

What COMMIT means here
    - write buffered field changes to disk
    - clear stale/buffered state
    - possibly rebuild index state when needed

Why COMMIT matters educationally
    It teaches that editing is often a two-step process:
        1. stage
        2. persist

Contrast
    REPLACE without buffering may write directly.
    REPLACE with TABLE ON stages first, then COMMIT finalizes.)",
            true,
            "Making staged changes permanent."
        },

        {
            "PROJECTION",
            "PROJECTION",
R"(Projection means choosing which columns/fields to show.

Examples
    TUPLE LNAME,FNAME
    LIST FIELDS LNAME,FNAME
    REL ENUM ... TUPLE STUDENTS.SID,TEACHERS.LNAME

Educational point
    Projection is one of the three great data operations:
        selection   = which rows
        ordering    = in what sequence
        projection  = which columns )",
            true,
            "Choosing which fields to show."
        },

        {
            "NAVIGATION",
            "NAVIGATION",
R"(Navigation means moving the current record pointer.

Common navigation commands
    TOP
    BOTTOM
    SKIP
    GOTO
    SEEK
    FIND
    LOCATE

Important idea
    Many commands are pointer-sensitive.
    They use "current row" as their starting context.

Teaching point
    Navigation is to a database session what cursor movement is to an editor.)",
            true,
            "Moving the current record pointer."
        },

        {
            "SEARCH",
            "SEARCH AND MATCHING",
R"(DotTalk++ offers several search styles.

SEEK
    exact key search using current order/index

FIND
    search in current order/index context

LOCATE
    predicate-based search

SET FILTER / SMARTLIST
    visible subset driven by conditions

Educational point
    Not all searches are the same.
    Some are key-based.
    Some are predicate-based.
    Some are display-based.)",
            true,
            "SEEK, FIND and LOCATE: several search styles, different costs."
        },

        {
            "SCRIPT",
            "DOTSCRIPT",
R"(DotScript is the scripting surface of DotTalk++.

Purpose
    - automate repetitive commands
    - build regression tests
    - teach execution flow
    - preserve reproducible scenarios

Why it matters educationally
    DotScript turns interactive use into programming.

DotScript demonstrates
    sequential execution
    decision blocks
    loops
    command composition
    testing discipline )",
            true,
            "DotScript: the repeatable, scriptable surface of the shell."
        },

        {
            "TESTING",
            "REGRESSION AND TESTING",
R"(Testing is central to DotTalk++ development.

Observed style in this system
    - script-driven regression runs
    - canaries for known failures
    - safe / destructive separation
    - manual sections clearly marked

Educational value
    This teaches disciplined engineering:
        test what works
        document what fails
        preserve reproducible runs
        separate stable behavior from experiments )",
            true,
            "Why testing sits at the centre of DotTalk++ development."
        },

        {
            "EDUCATIONAL_USE",
            "HOW TO STUDY THIS SYSTEM",
R"(A practical study order

1. Open a table
    USE STUDENTS
    STRUCT
    FIELDS
    LIST 5

2. Learn navigation
    TOP
    SKIP 1
    BOTTOM
    RECNO

3. Learn ordering
    SET INDEX TO students.cdx
    SET ORDER TO TAG LNAME
    TOP
    LIST 5

4. Learn predicates
    LOCATE LNAME = Taylor
    SMARTLIST 5 FOR GPA >= 3.5

5. Learn tuple projection
    TUPLE *
    TUPLE LNAME,FNAME

6. Learn relations
    SET RELATION TO SID INTO ENROLL
    REL LIST

7. Learn relation traversal
    REL ENUM ...

8. Learn buffering
    TABLE ON
    REPLACE ...
    COMMIT

9. Learn scripting
    IF / ELSE / ENDIF
    LOOP / ENDLOOP
    SCAN / ENDSCAN

Teaching principle
    Move from single table -> ordered navigation -> predicate logic ->
    projection -> relations -> scripting.)",
            true,
            "A practical study order through these topics."
        },

        {
            "GLOSSARY",
            "GLOSSARY",
R"(Quick glossary

Alias
    Name used to refer to a table/work area.

Buffer
    Temporary staged change area before persistence.

Child
    Related table reached from a parent.

Current area
    The active work area.

Current record
    The row at the current record pointer.

Enum / enumerate
    Emit results one by one.

Field
    A named value within a record.

Index
    Ordered access path.

Metadata
    Structural information about data.

Order
    Current sequence used for navigation.

Parent
    Table from which relation traversal begins.

Predicate
    True/false expression.

Projection
    Selection of fields/columns for output.

Record
    One row.

Relation
    Parent-child matching rule between tables.

Schema
    Structural definition of a table/dataset.

Sequential flow
    Execute one command after another.

State
    The live session condition.

Tuple
    Logical projected row.

Work area
    Active open-table slot.)",
            true,
            "Quick definitions for the vocabulary used throughout."
        }
    };

    return k;
}

inline const Item* find(std::string_view name) {
    auto upper = [](std::string_view s) {
        std::string out;
        out.reserve(s.size());
        for (char ch : s) {
            if (ch >= 'a' && ch <= 'z') out.push_back(static_cast<char>(ch - 32));
            else out.push_back(ch);
        }
        return out;
    };

    const std::string key = upper(name);

    for (const auto& item : catalog()) {
        if (upper(item.topic) == key) return &item;
    }
    return nullptr;
}

inline std::vector<const Item*> search(std::string_view token) {
    auto upper = [](std::string_view s) {
        std::string out;
        out.reserve(s.size());
        for (char ch : s) {
            if (ch >= 'a' && ch <= 'z') out.push_back(static_cast<char>(ch - 32));
            else out.push_back(ch);
        }
        return out;
    };

    const std::string key = upper(token);
    std::vector<const Item*> out;

    for (const auto& item : catalog()) {
        const std::string t = upper(item.topic ? item.topic : "");
        const std::string s = upper(item.syntax ? item.syntax : "");
        const std::string d = upper(item.summary ? item.summary : "");

        if (t.find(key) != std::string::npos ||
            s.find(key) != std::string::npos ||
            d.find(key) != std::string::npos) {
            out.push_back(&item);
        }
    }
    return out;
}

} // namespace edref