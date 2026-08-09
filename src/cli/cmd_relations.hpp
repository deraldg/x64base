// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_relations.hpp
#pragma once
#include <sstream>
namespace xbase { class DbArea; }

void cmd_SET_RELATIONS(xbase::DbArea& A, std::istringstream& iss);
void cmd_RELATIONS_LIST(xbase::DbArea& A, std::istringstream& iss);
void cmd_RELATIONS_REFRESH(xbase::DbArea& A, std::istringstream& iss);
void cmd_REL_SAVE(xbase::DbArea& A, std::istringstream& iss);
void cmd_REL_LOAD(xbase::DbArea& A, std::istringstream& iss);
void cmd_REL_JOIN(xbase::DbArea& A, std::istringstream& iss);
void cmd_REL_ENUM(xbase::DbArea& A, std::istringstream& iss);
