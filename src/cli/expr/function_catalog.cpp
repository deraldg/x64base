// src/cli/expr/function_catalog.cpp
#include "cli/expr/function_catalog.hpp"

#include <algorithm>
#include <cctype>
#include <string>
#include <vector>

namespace dottalk::expr {
namespace {

std::string upcopy(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

// -----------------------------------------------------------------------------
// STRING / SEARCH / CONSTRUCTION / CONVERSION / LOGICAL
// -----------------------------------------------------------------------------

const FunctionDoc UPPER_DOC = {
    "UPPER",
    {},
    FunctionCategory::String,
    1, 1,
    "Convert text to uppercase.",
    { "UPPER(<expr>)" },
    { "UPPER(LNAME)", "UPPER(\"smith\")" },
    {
        "Input is coerced through the expression engine string path."
    },
    {}
};

const FunctionDoc LOWER_DOC = {
    "LOWER",
    {},
    FunctionCategory::String,
    1, 1,
    "Convert text to lowercase.",
    { "LOWER(<expr>)" },
    { "LOWER(FNAME)", "LOWER(\"SMITH\")" },
    {
        "Input is coerced through the expression engine string path."
    },
    {}
};

const FunctionDoc ALLTRIM_DOC = {
    "ALLTRIM",
    {},
    FunctionCategory::String,
    1, 1,
    "Trim leading and trailing spaces from a string value.",
    { "ALLTRIM(<expr>)" },
    { "ALLTRIM(NAME)", "ALLTRIM(\"  SMITH  \")" },
    {
        "Useful for normalization before comparison or display."
    },
    {}
};

const FunctionDoc LTRIM_DOC = {
    "LTRIM",
    {},
    FunctionCategory::String,
    1, 1,
    "Trim leading spaces from a string value.",
    { "LTRIM(<expr>)" },
    { "LTRIM(NAME)", "LTRIM(\"  SMITH\")" },
    {},
    {}
};

const FunctionDoc RTRIM_DOC = {
    "RTRIM",
    { "TRIM" },
    FunctionCategory::String,
    1, 1,
    "Trim trailing spaces from a string value.",
    { "RTRIM(<expr>)", "TRIM(<expr>)" },
    { "RTRIM(NAME)", "TRIM(NAME)" },
    {
        "TRIM is treated as an alias of RTRIM."
    },
    {}
};

const FunctionDoc LEFT_DOC = {
    "LEFT",
    {},
    FunctionCategory::String,
    2, 2,
    "Return the leftmost characters of a string.",
    { "LEFT(<expr>, <n>)" },
    { "LEFT(LNAME, 3)", "LEFT(\"SMITH\", 2)" },
    {
        "If n <= 0, returns an empty string.",
        "If n exceeds the string length, returns the whole string."
    },
    {
        "Non-numeric length arguments currently rely on integer parsing in the implementation."
    }
};

const FunctionDoc RIGHT_DOC = {
    "RIGHT",
    {},
    FunctionCategory::String,
    2, 2,
    "Return the rightmost characters of a string.",
    { "RIGHT(<expr>, <n>)" },
    { "RIGHT(LNAME, 3)", "RIGHT(\"SMITH\", 2)" },
    {
        "If n <= 0, returns an empty string.",
        "If n exceeds the string length, returns the whole string."
    },
    {
        "Non-numeric length arguments currently rely on integer parsing in the implementation."
    }
};

const FunctionDoc SUBSTR_DOC = {
    "SUBSTR",
    {},
    FunctionCategory::String,
    2, 3,
    "Return a substring starting at a 1-based position.",
    {
        "SUBSTR(<expr>, <start>)",
        "SUBSTR(<expr>, <start>, <length>)"
    },
    { "SUBSTR(LNAME, 1, 3)", "SUBSTR(NAME, 5)" },
    {
        "Start position is 1-based.",
        "Start values <= 0 are treated as 1."
    },
    {
        "Non-numeric start/length arguments currently rely on integer parsing in the implementation."
    }
};

const FunctionDoc LEN_DOC = {
    "LEN",
    {},
    FunctionCategory::Numeric,
    1, 1,
    "Return the length of a string value.",
    { "LEN(<expr>)" },
    { "LEN(LNAME)", "LEN(\"SMITH\")" },
    {
        "Returns a numeric value represented through the expression engine's string result path."
    },
    {}
};

const FunctionDoc SOUNDEX_DOC = {
    "SOUNDEX",
    {},
    FunctionCategory::Search,
    1, 1,
    "Return a four-character phonetic Soundex code for a character expression.",
    { "SOUNDEX(<expr>)" },
    {
        "SOUNDEX(\"WHITE\")",
        "SOUNDEX(\"WHYTE\")",
        "SOUNDEX(LNAME)"
    },
    {
        "Classic Soundex keeps the first alphabetic letter, encodes following consonant classes, removes duplicate adjacent codes, and pads to four characters.",
        "Useful for phonetic matching in LOCATE, SMARTLIST, and future computed index tags."
    },
    {
        "SOUNDEX is phonetic matching, not SET NEAR. SET NEAR controls ordered-key navigation; SOUNDEX computes a comparable value.",
        "Current implementation ignores non-alphabetic characters and uppercases internally. SETCASE does not change SOUNDEX output."
    }
};

const FunctionDoc AT_DOC = {
    "AT",
    {},
    FunctionCategory::Search,
    2, 3,
    "Return the 1-based position of a substring occurrence.",
    {
        "AT(<needle>, <haystack>)",
        "AT(<needle>, <haystack>, <occurrence>)"
    },
    { "AT(\"IT\", \"SMITH\")", "AT(\"A\", \"BANANA\", 2)" },
    {
        "Returns 0 if the substring is not found.",
        "Occurrence defaults to 1."
    },
    {
        "Search is case-sensitive."
    }
};

const FunctionDoc ATC_DOC = {
    "ATC",
    {},
    FunctionCategory::Search,
    2, 3,
    "Return the 1-based position of a substring occurrence, case-insensitive.",
    {
        "ATC(<needle>, <haystack>)",
        "ATC(<needle>, <haystack>, <occurrence>)"
    },
    { "ATC(\"it\", \"SMITH\")", "ATC(\"a\", \"BANANA\", 2)" },
    {
        "Returns 0 if the substring is not found.",
        "Occurrence defaults to 1."
    },
    {}
};

const FunctionDoc LIKE_DOC = {
    "LIKE",
    {},
    FunctionCategory::Logical,
    2, 2,
    "Match a value against a wildcard pattern.",
    { "LIKE(<value>, <pattern>)" },
    { "LIKE(LNAME, \"SM*\")", "LIKE(NAME, \"A_%\")" },
    {
        "The implementation normalizes SQL wildcards: % becomes * and _ becomes ?.",
        "Matching is case-insensitive."
    },
    {
        "Returns .T. or .F. as logical strings."
    }
};

const FunctionDoc STR_DOC = {
    "STR",
    {},
    FunctionCategory::Conversion,
    1, 3,
    "Convert a numeric value to a formatted string.",
    {
        "STR(<value>)",
        "STR(<value>, <length>)",
        "STR(<value>, <length>, <decimals>)"
    },
    { "STR(123.45)", "STR(123.45, 8, 2)" },
    {
        "Defaults to length 10 and 0 decimals.",
        "If the formatted value does not fit, the function returns a field of asterisks."
    },
    {
        "Non-numeric input currently relies on numeric parsing in the implementation."
    }
};

const FunctionDoc VAL_DOC = {
    "VAL",
    {},
    FunctionCategory::Conversion,
    1, 1,
    "Extract the leading numeric portion of a string.",
    { "VAL(<expr>)" },
    { "VAL(\"123.45\")", "VAL(\"  -10ABC\")" },
    {
        "Returns 0 when no numeric prefix is present.",
        "Result is returned through the expression engine's string path."
    },
    {}
};

const FunctionDoc CONCAT_DOC = {
    "CONCAT",
    { "STRCAT" },
    FunctionCategory::Construction,
    1, 32,
    "Concatenate all arguments into a single string.",
    {
        "CONCAT(<expr1>, <expr2>, ...)",
        "STRCAT(<expr1>, <expr2>, ...)"
    },
    { "CONCAT(FNAME, \" \", LNAME)", "STRCAT(\"A\", \"B\", \"C\")" },
    {
        "Accepts between 1 and 32 arguments.",
        "STRCAT is treated as an alias of CONCAT."
    },
    {}
};

const FunctionDoc ASC_DOC = {
    "ASC",
    {},
    FunctionCategory::String,
    1, 1,
    "Return the character code of the first character in a string.",
    { "ASC(<expr>)" },
    { "ASC(\"A\")", "ASC(code_value)" },
    {
        "Only the first character is considered."
    },
    {
        "Empty-string behavior should remain explicit and stable."
    }
};

const FunctionDoc CHR_DOC = {
    "CHR",
    {},
    FunctionCategory::String,
    1, 1,
    "Return the single-character string for a numeric character code.",
    { "CHR(<code>)" },
    { "CHR(65)", "CHR(ascii_code)" },
    {
        "Useful as the inverse of ASC for basic character conversion."
    },
    {
        "Out-of-range behavior should remain explicit and stable."
    }
};

const FunctionDoc CHRTRAN_DOC = {
    "CHRTRAN",
    {},
    FunctionCategory::String,
    3, 3,
    "Replace characters in a string by position-mapped translation.",
    { "CHRTRAN(<expr>, <search_chars>, <replace_chars>)" },
    { "CHRTRAN(\"ABC\", \"AC\", \"XZ\")", "CHRTRAN(code, old_chars, new_chars)" },
    {
        "Applies character-by-character substitution based on search and replacement sets."
    },
    {
        "Length mismatch behavior between search and replacement sets should remain documented."
    }
};

const FunctionDoc EMPTY_DOC = {
    "EMPTY",
    {},
    FunctionCategory::Logical,
    1, 1,
    "Return whether a value is empty according to expression-engine rules.",
    { "EMPTY(<expr>)" },
    { "EMPTY(NAME)", "EMPTY(\"\")" },
    {
        "Useful for validation and filters."
    },
    {
        "Exact emptiness rules for strings, numerics, dates, and logicals should remain explicit."
    }
};

const FunctionDoc RAT_DOC = {
    "RAT",
    {},
    FunctionCategory::Search,
    2, 2,
    "Return the 1-based position of the last occurrence of a substring.",
    { "RAT(<needle>, <haystack>)" },
    { "RAT(\"A\", \"BANANA\")", "RAT(\"/\", path_value)" },
    {
        "Useful when searching from the end of a string."
    },
    {
        "Returns 0 when the substring is not found."
    }
};

const FunctionDoc REPLICATE_DOC = {
    "REPLICATE",
    {},
    FunctionCategory::Construction,
    2, 2,
    "Repeat a string value a specified number of times.",
    { "REPLICATE(<expr>, <count>)" },
    { "REPLICATE(\"-\", 10)", "REPLICATE(fill_char, width)" },
    {
        "Useful for padding and simple formatting."
    },
    {
        "Negative or invalid counts should remain explicitly handled."
    }
};

const FunctionDoc SPACE_DOC = {
    "SPACE",
    {},
    FunctionCategory::Construction,
    1, 1,
    "Return a string containing the requested number of spaces.",
    { "SPACE(<count>)" },
    { "SPACE(5)", "SPACE(pad_width)" },
    {
        "Useful for fixed-width formatting and output padding."
    },
    {
        "Negative counts should remain explicitly handled."
    }
};

const FunctionDoc STRTRAN_DOC = {
    "STRTRAN",
    {},
    FunctionCategory::String,
    3, 3,
    "Replace occurrences of a substring within a string.",
    { "STRTRAN(<expr>, <search>, <replace>)" },
    { "STRTRAN(\"ABCABC\", \"AB\", \"XY\")", "STRTRAN(text_value, old_part, new_part)" },
    {
        "Useful for substring replacement rather than character-by-character translation."
    },
    {}
};

const FunctionDoc TRANSFORM_DOC = {
    "TRANSFORM",
    {},
    FunctionCategory::Conversion,
    1, 2,
    "Convert a value to display-oriented character form.",
    {
        "TRANSFORM(<expr>)",
        "TRANSFORM(<expr>, <picture>)"
    },
    { "TRANSFORM(total)", "TRANSFORM(total, \"999,999.99\")" },
    {
        "Intended for formatting values for presentation."
    },
    {
        "Picture formatting support should be documented explicitly if partial."
    }
};

// -----------------------------------------------------------------------------
// DATE
// -----------------------------------------------------------------------------

const FunctionDoc DATE_DOC = {
    "DATE",
    {},
    FunctionCategory::Date,
    0, 0,
    "Return the current system date.",
    { "DATE()" },
    { "DATE()", "DATE() = TODAY()" },
    {
        "Zero-argument date function.",
        "Intended to return the current date without time."
    },
    {
        "Results depend on system clock accuracy."
    }
};

const FunctionDoc TODAY_DOC = {
    "TODAY",
    {},
    FunctionCategory::Date,
    0, 0,
    "Return the current system date.",
    { "TODAY()" },
    { "TODAY()", "TODAY() = DATE()" },
    {
        "Functionally equivalent to DATE() unless the engine later distinguishes them."
    },
    {
        "Results depend on system clock accuracy."
    }
};

const FunctionDoc NOW_DOC = {
    "NOW",
    {},
    FunctionCategory::Date,
    0, 0,
    "Return the current date/time value.",
    { "NOW()" },
    { "NOW()" },
    {
        "Intended as the current timestamp-style function.",
        "Use when both date and time matter."
    },
    {
        "Exact formatting and representation should remain consistent across the expression engine."
    }
};

const FunctionDoc DATETIME_DOC = {
    "DATETIME",
    {},
    FunctionCategory::Date,
    0, 0,
    "Return the current date/time value.",
    { "DATETIME()" },
    { "DATETIME()" },
    {
        "Current zero-argument timestamp-style function.",
        "May overlap conceptually with NOW(); keep both documented if both are supported."
    },
    {
        "If NOW() and DATETIME() differ later, document the distinction explicitly."
    }
};

const FunctionDoc TIME_DOC = {
    "TIME",
    {},
    FunctionCategory::Date,
    0, 0,
    "Return the current system time.",
    { "TIME()" },
    { "TIME()" },
    {
        "Intended to return current clock time without date."
    },
    {
        "Representation format should be documented consistently."
    }
};

const FunctionDoc SECONDS_DOC = {
    "SECONDS",
    {},
    FunctionCategory::Date,
    0, 0,
    "Return the current time expressed as seconds-of-day or equivalent engine-specific seconds value.",
    { "SECONDS()" },
    { "SECONDS()" },
    {
        "Useful for elapsed-time comparisons and lightweight timing logic."
    },
    {
        "Exact semantics should be documented clearly if they differ from classic seconds-of-day behavior."
    }
};

const FunctionDoc CTOD_DOC = {
    "CTOD",
    {},
    FunctionCategory::Date,
    1, 1,
    "Convert a character string to a date value.",
    { "CTOD(<expr>)" },
    { "CTOD(\"2025-01-01\")", "CTOD(order_date_text)" },
    {
        "Input must match one of the accepted date formats supported by the engine.",
        "Common bridge from text import into date logic."
    },
    {
        "Invalid or ambiguous date text should raise an error or return a clearly documented failure value.",
        "Accepted formats should remain explicit and stable."
    }
};

const FunctionDoc DTOC_DOC = {
    "DTOC",
    {},
    FunctionCategory::Date,
    1, 2,
    "Convert a date value to character form.",
    { "DTOC(<date>)", "DTOC(<date>, <style>)" },
    { "DTOC(DATE())", "DTOC(invoice_date)" },
    {
        "Used for display-oriented date formatting.",
        "Second argument, if supported, should remain clearly documented."
    },
    {
        "Output format should not drift unpredictably across environments."
    }
};

const FunctionDoc DTOS_DOC = {
    "DTOS",
    {},
    FunctionCategory::Date,
    1, 1,
    "Convert a date value to sortable character form.",
    { "DTOS(<date>)" },
    { "DTOS(DATE())", "DTOS(invoice_date)" },
    {
        "Intended for stable lexicographic sorting and comparison.",
        "Commonly used for key-building and normalized date strings."
    },
    {
        "Output format should stay invariant and machine-friendly."
    }
};

const FunctionDoc DAY_DOC = {
    "DAY",
    {},
    FunctionCategory::Date,
    1, 1,
    "Return the day-of-month component of a date.",
    { "DAY(<date>)" },
    { "DAY(DATE())", "DAY(birth_date)" },
    {
        "Returns the calendar day number within the month."
    },
    {
        "Input must be a valid date value."
    }
};

const FunctionDoc MONTH_DOC = {
    "MONTH",
    {},
    FunctionCategory::Date,
    1, 1,
    "Return the month component of a date.",
    { "MONTH(<date>)" },
    { "MONTH(DATE())", "MONTH(invoice_date)" },
    {
        "Returns the month number."
    },
    {
        "Input must be a valid date value."
    }
};

const FunctionDoc YEAR_DOC = {
    "YEAR",
    {},
    FunctionCategory::Date,
    1, 1,
    "Return the year component of a date.",
    { "YEAR(<date>)" },
    { "YEAR(DATE())", "YEAR(hire_date)" },
    {
        "Returns the full year value."
    },
    {
        "Input must be a valid date value."
    }
};

const FunctionDoc DOW_DOC = {
    "DOW",
    {},
    FunctionCategory::Date,
    1, 1,
    "Return the day-of-week number for a date.",
    { "DOW(<date>)" },
    { "DOW(DATE())", "DOW(order_date)" },
    {
        "Numeric day-of-week function.",
        "The numbering convention should be documented explicitly."
    },
    {
        "Day numbering must remain stable and clearly defined."
    }
};

const FunctionDoc CDOW_DOC = {
    "CDOW",
    {},
    FunctionCategory::Date,
    1, 1,
    "Return the day-of-week name for a date.",
    { "CDOW(<date>)" },
    { "CDOW(DATE())", "CDOW(order_date)" },
    {
        "Character day-of-week function.",
        "Useful for reports and formatted output."
    },
    {
        "Language/localization behavior should be documented if it ever becomes configurable."
    }
};

const FunctionDoc CMONTH_DOC = {
    "CMONTH",
    {},
    FunctionCategory::Date,
    1, 1,
    "Return the month name for a date.",
    { "CMONTH(<date>)" },
    { "CMONTH(DATE())", "CMONTH(invoice_date)" },
    {
        "Character month-name function.",
        "Useful for display and reporting."
    },
    {
        "Language/localization behavior should be documented if it changes from fixed English output."
    }
};

const FunctionDoc DATEADD_DOC = {
    "DATEADD",
    {},
    FunctionCategory::Date,
    2, 2,
    "Return a new date shifted by a specified interval.",
    { "DATEADD(<date>, <delta>)" },
    { "DATEADD(DATE(), 7)", "DATEADD(start_date, 30)" },
    {
        "Current reflected signature is two arguments.",
        "Use for forward/backward date offset logic."
    },
    {
        "The unit implied by <delta> must be explicit in implementation and docs.",
        "If only days are supported, say so clearly."
    }
};

const FunctionDoc DATEDIFF_DOC = {
    "DATEDIFF",
    {},
    FunctionCategory::Date,
    2, 2,
    "Return the difference between two date values.",
    { "DATEDIFF(<date1>, <date2>)" },
    { "DATEDIFF(DATE(), DATE())", "DATEDIFF(start_date, end_date)" },
    {
        "Current reflected signature is two arguments.",
        "Commonly used for elapsed-day comparisons."
    },
    {
        "Result sign/order should be documented clearly.",
        "If units are fixed to days, say so explicitly."
    }
};

const FunctionDoc GOMONTH_DOC = {
    "GOMONTH",
    {},
    FunctionCategory::Date,
    2, 2,
    "Return a date shifted by a specified number of months.",
    { "GOMONTH(<date>, <months>)" },
    { "GOMONTH(DATE(), 1)", "GOMONTH(invoice_date, -3)" },
    {
        "Month-aware shifting function.",
        "Prefer this over day arithmetic when month boundaries matter."
    },
    {
        "End-of-month rollover behavior should be explicitly documented."
    }
};

// -----------------------------------------------------------------------------
// NUMERIC
// -----------------------------------------------------------------------------

const FunctionDoc ABS_DOC = {
    "ABS",
    {},
    FunctionCategory::Numeric,
    1, 1,
    "Return the absolute value of a numeric expression.",
    { "ABS(<n>)" },
    { "ABS(-5)", "ABS(balance)" },
    {
        "Positive values remain unchanged."
    },
    {
        "Non-numeric input should be treated as an evaluation/type error unless explicitly coerced."
    }
};

const FunctionDoc INT_DOC = {
    "INT",
    {},
    FunctionCategory::Numeric,
    1, 1,
    "Return the integer portion of a numeric value.",
    { "INT(<n>)" },
    { "INT(12.9)", "INT(-3.2)" },
    {
        "Intended as integer truncation/floor-style numeric reduction depending on implementation contract.",
        "Verify negative-number behavior if exact FoxPro compatibility matters."
    },
    {
        "INT(-3.2) should be explicitly tested to confirm whether behavior is truncation toward zero or floor toward negative infinity."
    }
};

const FunctionDoc ROUND_DOC = {
    "ROUND",
    {},
    FunctionCategory::Numeric,
    1, 2,
    "Round a numeric value to a specified number of decimal places.",
    {
        "ROUND(<n>)",
        "ROUND(<n>, <decimals>)"
    },
    { "ROUND(12.3456)", "ROUND(12.3456, 2)" },
    {
        "One-argument form rounds using the engine's default integer-style behavior."
    },
    {
        "Half-boundary behavior should be documented explicitly if financial use becomes important."
    }
};

const FunctionDoc MIN_DOC = {
    "MIN",
    {},
    FunctionCategory::Numeric,
    2, 32,
    "Return the smallest value from two or more numeric expressions.",
    {
        "MIN(<a>, <b>)",
        "MIN(<a>, <b>, ...)"
    },
    { "MIN(4, 9)", "MIN(price1, price2, price3)" },
    {
        "Accepts two or more arguments.",
        "Useful for upper-bound clamping when paired with MAX."
    },
    {
        "Mixed-type argument behavior should remain explicit if coercion is permitted."
    }
};

const FunctionDoc MAX_DOC = {
    "MAX",
    {},
    FunctionCategory::Numeric,
    2, 32,
    "Return the largest value from two or more numeric expressions.",
    {
        "MAX(<a>, <b>)",
        "MAX(<a>, <b>, ...)"
    },
    { "MAX(4, 9)", "MAX(score1, score2, score3)" },
    {
        "Accepts two or more arguments.",
        "Useful for lower-bound clamping when paired with MIN."
    },
    {
        "Mixed-type argument behavior should remain explicit if coercion is permitted."
    }
};

const FunctionDoc MOD_DOC = {
    "MOD",
    {},
    FunctionCategory::Numeric,
    2, 2,
    "Return the remainder from dividing one numeric value by another.",
    { "MOD(<dividend>, <divisor>)" },
    { "MOD(10, 3)", "MOD(counter, 2)", "MOD(day_index, 7)" },
    {
        "Useful for parity checks, cycle logic, and repeating patterns.",
        "Common in date math and rotational indexing."
    },
    {
        "Division by zero must be treated as an error.",
        "Negative-operand remainder behavior should be documented if strict compatibility matters."
    }
};

const FunctionDoc SQRT_DOC = {
    "SQRT",
    {},
    FunctionCategory::Numeric,
    1, 1,
    "Return the square root of a numeric value.",
    { "SQRT(<n>)" },
    { "SQRT(9)", "SQRT(area)", "SQRT(distance_squared)" },
    {
        "Intended for non-negative numeric inputs.",
        "Common in geometry and distance calculations."
    },
    {
        "Negative inputs should raise an error unless complex-number support is intentionally added."
    }
};

const FunctionDoc LOG_DOC = {
    "LOG",
    {},
    FunctionCategory::Numeric,
    1, 1,
    "Return the natural logarithm of a numeric value.",
    { "LOG(<n>)" },
    { "LOG(1)", "LOG(value)", "LOG(total)" },
    {
        "Natural logarithm uses base e.",
        "Often paired with EXP."
    },
    {
        "Input must be greater than zero.",
        "Zero or negative inputs should raise an error."
    }
};

const FunctionDoc LOG10_DOC = {
    "LOG10",
    {},
    FunctionCategory::Numeric,
    1, 1,
    "Return the base-10 logarithm of a numeric value.",
    { "LOG10(<n>)" },
    { "LOG10(10)", "LOG10(1000)", "LOG10(measurement)" },
    {
        "Useful for scale, magnitude, and scientific/logarithmic reporting."
    },
    {
        "Input must be greater than zero.",
        "Zero or negative inputs should raise an error."
    }
};

const FunctionDoc EXP_DOC = {
    "EXP",
    {},
    FunctionCategory::Numeric,
    1, 1,
    "Return e raised to the power of the supplied numeric value.",
    { "EXP(<n>)" },
    { "EXP(1)", "EXP(rate)", "EXP(growth_factor)" },
    {
        "Natural exponential function.",
        "Often paired with LOG."
    },
    {
        "Large positive values may overflow depending on numeric backend limits."
    }
};

const FunctionDoc SIN_DOC = {
    "SIN",
    {},
    FunctionCategory::Numeric,
    1, 1,
    "Return the sine of an angle expressed in radians.",
    { "SIN(<radians>)" },
    { "SIN(0)", "SIN(angle)", "SIN(3.14159 / 2)" },
    {
        "Input is assumed to be radians, not degrees.",
        "Part of the trigonometric family with COS and TAN."
    },
    {
        "Degree-based expectations should not be silently assumed."
    }
};

const FunctionDoc COS_DOC = {
    "COS",
    {},
    FunctionCategory::Numeric,
    1, 1,
    "Return the cosine of an angle expressed in radians.",
    { "COS(<radians>)" },
    { "COS(0)", "COS(3.14159)" },
    {
        "Input is assumed to be radians.",
        "Common for periodic and geometric calculations."
    },
    {}
};

const FunctionDoc TAN_DOC = {
    "TAN",
    {},
    FunctionCategory::Numeric,
    1, 1,
    "Return the tangent of an angle expressed in radians.",
    { "TAN(<radians>)" },
    { "TAN(0)", "TAN(angle)", "TAN(3.14159 / 4)" },
    {
        "Input is assumed to be radians.",
        "Complements SIN and COS in the trig family."
    },
    {
        "Values near odd multiples of pi/2 can grow very large and may expose floating-point instability."
    }
};

const FunctionDoc ASIN_DOC = {
    "ASIN",
    {},
    FunctionCategory::Numeric,
    1, 1,
    "Return the arc-sine of a numeric value.",
    { "ASIN(<n>)" },
    { "ASIN(0)", "ASIN(1)", "ASIN(ratio)" },
    {
        "Inverse sine function.",
        "Result is expected in radians."
    },
    {
        "Input domain should be limited to [-1, 1].",
        "Out-of-range values should raise an error."
    }
};

const FunctionDoc ACOS_DOC = {
    "ACOS",
    {},
    FunctionCategory::Numeric,
    1, 1,
    "Return the arc-cosine of a numeric value.",
    { "ACOS(<n>)" },
    { "ACOS(0)", "ACOS(1)", "ACOS(ratio)" },
    {
        "Inverse cosine function.",
        "Result is expected in radians."
    },
    {
        "Input domain should be limited to [-1, 1].",
        "Out-of-range values should raise an error."
    }
};

const FunctionDoc ATAN_DOC = {
    "ATAN",
    {},
    FunctionCategory::Numeric,
    1, 1,
    "Return the arc-tangent of a numeric value.",
    { "ATAN(<n>)" },
    { "ATAN(0)", "ATAN(1)", "ATAN(slope)" },
    {
        "Inverse tangent function.",
        "Result is expected in radians."
    },
    {
        "Very large magnitudes may compress toward asymptotic output values, which is mathematically expected."
    }
};

const FunctionDoc CEILING_DOC = {
    "CEILING",
    {},
    FunctionCategory::Numeric,
    1, 1,
    "Return the smallest integer greater than or equal to the numeric value.",
    { "CEILING(<n>)" },
    { "CEILING(3.1)", "CEILING(9.0)", "CEILING(rate)" },
    {
        "Moves fractional positive values up to the next integer boundary.",
        "Values already integral remain unchanged."
    },
    {
        "Negative-number behavior should still follow the mathematical ceiling definition, not truncation."
    }
};

const FunctionDoc FLOOR_DOC = {
    "FLOOR",
    {},
    FunctionCategory::Numeric,
    1, 1,
    "Return the largest integer less than or equal to the numeric value.",
    { "FLOOR(<n>)" },
    { "FLOOR(3.9)", "FLOOR(9.0)", "FLOOR(rate)" },
    {
        "Moves fractional positive values down to the prior integer boundary.",
        "Values already integral remain unchanged."
    },
    {
        "Negative-number behavior should still follow the mathematical floor definition, not truncation toward zero."
    }
};

const FunctionDoc BETWEEN_DOC = {
    "BETWEEN",
    {},
    FunctionCategory::Numeric,
    3, 3,
    "Return whether a numeric value lies within an inclusive lower and upper bound.",
    { "BETWEEN(<value>, <low>, <high>)" },
    { "BETWEEN(age, 18, 65)", "BETWEEN(score, 0, 100)", "BETWEEN(x, min_x, max_x)" },
    {
        "Useful for range validation and filter predicates.",
        "Should be treated as logical output even if grouped among numeric-oriented helpers."
    },
    {
        "Bound ordering behavior should be explicit; if <low> > <high>, either document the behavior or normalize it consistently."
    }
};

const FunctionDoc RAND_DOC = {
    "RAND",
    {},
    FunctionCategory::Numeric,
    0, 0,
    "Return a pseudo-random numeric value.",
    { "RAND()" },
    { "RAND()" },
    {
        "Current implementation returns a random value on each call."
    },
    {
        "Distribution and seeding behavior should be documented more precisely if stability matters."
    }
};

// -----------------------------------------------------------------------------
// ALL DOCS
// -----------------------------------------------------------------------------

const std::vector<const FunctionDoc*> ALL_DOCS = {
    // String / Search / Construction / Conversion / Logical
    &UPPER_DOC,
    &LOWER_DOC,
    &ALLTRIM_DOC,
    &LTRIM_DOC,
    &RTRIM_DOC,
    &LEFT_DOC,
    &RIGHT_DOC,
    &SUBSTR_DOC,
    &LEN_DOC,
    &SOUNDEX_DOC,
    &AT_DOC,
    &ATC_DOC,
    &LIKE_DOC,
    &STR_DOC,
    &VAL_DOC,
    &CONCAT_DOC,
    &ASC_DOC,
    &CHR_DOC,
    &CHRTRAN_DOC,
    &EMPTY_DOC,
    &RAT_DOC,
    &REPLICATE_DOC,
    &SPACE_DOC,
    &STRTRAN_DOC,
    &TRANSFORM_DOC,

    // Date
    &DATE_DOC,
    &TODAY_DOC,
    &NOW_DOC,
    &DATETIME_DOC,
    &TIME_DOC,
    &SECONDS_DOC,
    &CTOD_DOC,
    &DTOC_DOC,
    &DTOS_DOC,
    &DAY_DOC,
    &MONTH_DOC,
    &YEAR_DOC,
    &DOW_DOC,
    &CDOW_DOC,
    &CMONTH_DOC,
    &DATEADD_DOC,
    &DATEDIFF_DOC,
    &GOMONTH_DOC,

    // Numeric
    &ABS_DOC,
    &INT_DOC,
    &ROUND_DOC,
    &MIN_DOC,
    &MAX_DOC,
    &MOD_DOC,
    &SQRT_DOC,
    &LOG_DOC,
    &LOG10_DOC,
    &EXP_DOC,
    &SIN_DOC,
    &COS_DOC,
    &TAN_DOC,
    &ASIN_DOC,
    &ACOS_DOC,
    &ATAN_DOC,
    &CEILING_DOC,
    &FLOOR_DOC,
    &BETWEEN_DOC,
    &RAND_DOC
};

} // anonymous namespace

const FunctionDoc* get_function_doc(const std::string& name)
{
    const std::string want = upcopy(name);

    for (const auto* doc : ALL_DOCS) {
        if (doc->name == want) {
            return doc;
        }
        for (const auto& alias : doc->aliases) {
            if (alias == want) {
                return doc;
            }
        }
    }

    return nullptr;
}

std::vector<const FunctionDoc*> all_function_docs()
{
    return ALL_DOCS;
}

const char* to_string(FunctionCategory cat)
{
    switch (cat) {
        case FunctionCategory::String:       return "String";
        case FunctionCategory::Search:       return "Search";
        case FunctionCategory::Construction: return "Construction";
        case FunctionCategory::Conversion:   return "Conversion";
        case FunctionCategory::Logical:      return "Logical";
        case FunctionCategory::Numeric:      return "Numeric";
        case FunctionCategory::Date:         return "Date";
        case FunctionCategory::Misc:
        default:                             return "Misc";
    }
}

} // namespace dottalk::expr