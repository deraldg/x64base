// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/dotscript_lexing.hpp
//
// Canonical DotTalk++ / DotScript comment + line lexing.
//
// One place -- and only one -- defines the comment vocabulary (AIF-037,
// "Representative by Design", the Rule of Three). Before this module the same
// logic lived in five drifting copies (three `begins_with_comment`, one
// `looks_like_comment_or_blank`, two `strip_hash_comment`); those are now thin
// delegates to the functions declared here.
//
// The vocabulary:
//   full-line comments : *  REM        (canonical)   #  //   (tolerated)
//   inline comments    : &&  #         (cut to end of line, quote/escape aware)
//   ;                  : line continuation, NOT a comment
//
// A single `&` is the xBase macro-substitution operator and is never treated as
// a comment; only the doubled `&&` opens a comment.

#pragma once

#include <string>

namespace dottalk::lexing {

// Return `line` with any inline comment removed. An inline comment starts at the
// first unquoted `#` or `&&`; trailing whitespace before the cut is trimmed.
// Quote- and backslash-escape aware, so `#`/`&&` inside a string literal are kept.
std::string strip_inline_comment(const std::string& line);

// True if `line` (ignoring leading whitespace) begins with a full-line comment
// token: `*`, `#`, `//`, `&&`, or `REM` (REM = first token, case-insensitive,
// followed by whitespace or end of line). A blank line is NOT a comment line.
bool is_comment_line(const std::string& line);

// True if `line` is blank, a full-line comment (see is_comment_line), or begins
// with a bare `;` continuation marker.
bool is_comment_or_blank(const std::string& line);

} // namespace dottalk::lexing
