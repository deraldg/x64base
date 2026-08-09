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
#include <tvision/views.h>  // TPalette

// Minimal save/load helpers used by the palette tool.
// Stores a simple binary file in the working directory by default.

bool paletteSave(const TPalette &pal, const std::string &path = "dottalkpp.palette");
bool paletteLoad(TPalette &out, const std::string &path = "dottalkpp.palette");




