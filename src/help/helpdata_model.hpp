// ============================================================================
// File: src/help/helpdata_model.hpp
// Purpose: Canonical HELP DATA v2 model.
// ============================================================================
#pragma once

#include <string>
#include <vector>

namespace dottalk::helpdata {

enum class ArtifactKind {
    Summary,
    Usage,
    Syntax,
    Argument,
    Example,
    Note,
    Warning,
    Error,
    Hint,
    Message,
    Status,
    Compatibility,
    Deprecation,
    Unsupported,
    Alias,
    Variant,
    Related,
    SourceFact
};

enum class OwnerKind {
    Global,
    Command,
    Subsystem,
    Miner
};

enum class SourceKind {
    Registry,
    FoxRef,
    DotRef,
    EdRef,
    CuratedDoc,
    SharedMessage,
    SubsystemMessage,
    SourceMiner,
    UsageContract,
    Reflection,
    RuntimeProbe
};

enum class Confidence {
    Authoritative,
    Curated,
    Catalog,
    Reflected,
    Inferred,
    Heuristic
};

enum class Severity {
    None,
    Info,
    Warning,
    Error,
    Fatal
};

struct Owner {
    OwnerKind   kind { OwnerKind::Global };
    std::string name; // Empty for GLOBAL, command name for COMMAND, subsystem name, etc.
};

struct Artifact {
    int id { 0 };

    std::string catalog; // FOX, DOT, ED, SYSTEM, HELP, etc.
    std::string command; // LIST, COUNT, GO, etc. Empty for purely global messages.
    std::string cmdkey;  // CATALOG|COMMAND, empty for global SYSTEM facts.

    Owner owner;

    ArtifactKind kind { ArtifactKind::SourceFact };
    SourceKind   source { SourceKind::SourceMiner };
    Confidence   confidence { Confidence::Heuristic };
    Severity     severity { Severity::None };

    std::string name;     // ARG name, message key, alias target, variant name, etc.
    std::string text;     // Main payload.
    std::string detail;   // Optional extended text.
    std::string evidence; // File/function/pattern/source clue.

    int ordinal { 0 };
};

struct CommandDocV2 {
    std::string catalog;
    std::string command;
    std::string cmdkey;

    std::string category;
    std::string status;

    bool implemented { false };
    bool supported { false };

    std::vector<Artifact> artifacts;
};

std::string upper(std::string s);
std::string make_cmdkey(const std::string& catalog, const std::string& command);

std::string owner_to_string(const Owner& owner);

const char* to_string(ArtifactKind value);
const char* to_string(OwnerKind value);
const char* to_string(SourceKind value);
const char* to_string(Confidence value);
const char* to_string(Severity value);

Artifact make_artifact(const std::string& catalog,
                       const std::string& command,
                       Owner owner,
                       ArtifactKind kind,
                       SourceKind source,
                       Confidence confidence,
                       Severity severity,
                       const std::string& name,
                       const std::string& text,
                       int ordinal = 0,
                       const std::string& detail = {},
                       const std::string& evidence = {});

} // namespace dottalk::helpdata
