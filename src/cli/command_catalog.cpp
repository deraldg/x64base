#include "command_catalog.hpp"

namespace dottalk::doc {

static const CommandDoc GO_DOC = {
    "GO",
    "Move to a record or navigation endpoint",

    {
        "GO",
        "GO TOP",
        "GO BOTTOM",
        "GO FIRST",
        "GO LAST",
        "GO [TO] <recno>",
        "GO RECORD <recno>",
        "GO +/-<n>"
    },

    {
        "GO",
        "GO TOP",
        "GO TO 10",
        "GO RECORD 25",
        "GO +5",
        "GO -1"
    },

    {
        "GO with no arguments refreshes the current record",
        "TOP and FIRST are synonyms",
        "BOTTOM and LAST are synonyms"
    },

    {
        "IN <alias> is not supported yet"
    }
};

static const CommandDoc COUNT_DOC = {
    "COUNT",
    "Count records in the current work area",

    {
        "COUNT",
        "COUNT ALL",
        "COUNT DELETED",
        "COUNT NOT DELETED",
        "COUNT FOR <expr>",
        "COUNT WHERE <expr>",
        "COUNT <expr>"
    },

    {
        "COUNT",
        "COUNT ALL",
        "COUNT DELETED",
        "COUNT FOR LNAME = \"SMITH\"",
        "COUNT WHERE AGE > 30"
    },

    {
        "Uses current SET FILTER if active",
        "Uses index when possible for optimization"
    },

    {
        "COUNT preserves the current record position"
    }
};

const CommandDoc* get(const std::string& command)
{
    if (command == "GO") return &GO_DOC;
    if (command == "COUNT") return &COUNT_DOC;
    return nullptr;
}

static const CommandDoc DISPLAY_DOC = {
    "DISPLAY",
    "Display field values for the current or specified record",

    {
        "DISPLAY",
        "DISPLAY <recno>"
    },

    {
        "DISPLAY",
        "DISPLAY 10"
    },

    {
        "Displays all fields for the current record",
        "Optional record number repositions before display"
    },

    {
        "Displays memo fields using resolved display view"
    }
};


} // namespace dottalk::doc
