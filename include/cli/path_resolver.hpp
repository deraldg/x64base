// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

// AIF-145 R-c. This header and include/common/path_resolver.hpp declared the
// SAME dottalk::paths functions, with the same signatures, in the same
// namespace, differing only in a subsystem tag and trailing whitespace. Ten CLI
// translation units include this spelling and three include the other, so ONE
// namespace had TWO declaration sites that could drift apart independently --
// AIF-143's shape (two structs, one name) at header scope.
//
// The definitions live in src/common/path_resolver.cpp, so common/ is the home.
// This file is now a SHIM: every existing include site keeps compiling and
// there is exactly one declaration left to maintain. Nothing was moved and no
// include site was edited, deliberately -- a de-duplication that also churns
// ten files cannot be reviewed as one change.
#include "common/path_resolver.hpp"
