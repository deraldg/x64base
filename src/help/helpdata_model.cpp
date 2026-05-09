// ============================================================================
// File: src/help/helpdata_model.cpp
// ============================================================================
#include "helpdata_model.hpp"

#include <algorithm>
#include <cctype>

namespace dottalk::helpdata {

std::string upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char ch) {
        return static_cast<char>(std::toupper(ch));
    });
    return s;
}

std::string make_cmdkey(const std::string& catalog, const std::string& command)
{
    if (catalog.empty() || command.empty()) {
        return {};
    }
    return upper(catalog) + "|" + upper(command);
}

std::string owner_to_string(const Owner& owner)
{
    switch (owner.kind) {
        case OwnerKind::Global:
            return "GLOBAL";
        case OwnerKind::Command:
            return owner.name.empty() ? "COMMAND" : "COMMAND:" + upper(owner.name);
        case OwnerKind::Subsystem:
            return owner.name.empty() ? "SUBSYSTEM" : "SUBSYSTEM:" + upper(owner.name);
        case OwnerKind::Miner:
            return owner.name.empty() ? "MINER" : "MINER:" + upper(owner.name);
    }
    return "GLOBAL";
}

const char* to_string(ArtifactKind value)
{
    switch (value) {
        case ArtifactKind::Summary:       return "SUMMARY";
        case ArtifactKind::Usage:         return "USAGE";
        case ArtifactKind::Syntax:        return "SYNTAX";
        case ArtifactKind::Argument:      return "ARGUMENT";
        case ArtifactKind::Example:       return "EXAMPLE";
        case ArtifactKind::Note:          return "NOTE";
        case ArtifactKind::Warning:       return "WARNING";
        case ArtifactKind::Error:         return "ERROR";
        case ArtifactKind::Hint:          return "HINT";
        case ArtifactKind::Message:       return "MESSAGE";
        case ArtifactKind::Status:        return "STATUS";
        case ArtifactKind::Compatibility: return "COMPAT";
        case ArtifactKind::Deprecation:   return "DEPRECATION";
        case ArtifactKind::Unsupported:   return "UNSUPPORTED";
        case ArtifactKind::Alias:         return "ALIAS";
        case ArtifactKind::Variant:       return "VARIANT";
        case ArtifactKind::Related:       return "RELATED";
        case ArtifactKind::SourceFact:    return "SOURCE_FACT";
    }
    return "SOURCE_FACT";
}

const char* to_string(OwnerKind value)
{
    switch (value) {
        case OwnerKind::Global:    return "GLOBAL";
        case OwnerKind::Command:   return "COMMAND";
        case OwnerKind::Subsystem: return "SUBSYSTEM";
        case OwnerKind::Miner:     return "MINER";
    }
    return "GLOBAL";
}

const char* to_string(SourceKind value)
{
    switch (value) {
        case SourceKind::Registry:         return "REGISTRY";
        case SourceKind::FoxRef:           return "FOXREF";
        case SourceKind::DotRef:           return "DOTREF";
        case SourceKind::EdRef:            return "EDREF";
        case SourceKind::CuratedDoc:       return "CURATED_DOC";
        case SourceKind::SharedMessage:    return "SHARED_MSG";
        case SourceKind::SubsystemMessage: return "SUBSYS_MSG";
        case SourceKind::SourceMiner:      return "SOURCE_MINER";
        case SourceKind::UsageContract:    return "USAGE_CONTRACT";
        case SourceKind::Reflection:       return "REFLECTION";
        case SourceKind::RuntimeProbe:     return "RUNTIME_PROBE";
    }
    return "SOURCE_MINER";
}

const char* to_string(Confidence value)
{
    switch (value) {
        case Confidence::Authoritative: return "AUTHORITATIVE";
        case Confidence::Curated:       return "CURATED";
        case Confidence::Catalog:       return "CATALOG";
        case Confidence::Reflected:     return "REFLECTED";
        case Confidence::Inferred:      return "INFERRED";
        case Confidence::Heuristic:     return "HEURISTIC";
    }
    return "HEURISTIC";
}

const char* to_string(Severity value)
{
    switch (value) {
        case Severity::None:    return "NONE";
        case Severity::Info:    return "INFO";
        case Severity::Warning: return "WARNING";
        case Severity::Error:   return "ERROR";
        case Severity::Fatal:   return "FATAL";
    }
    return "NONE";
}

Artifact make_artifact(const std::string& catalog,
                       const std::string& command,
                       Owner owner,
                       ArtifactKind kind,
                       SourceKind source,
                       Confidence confidence,
                       Severity severity,
                       const std::string& name,
                       const std::string& text,
                       int ordinal,
                       const std::string& detail,
                       const std::string& evidence)
{
    Artifact artifact;
    artifact.catalog = upper(catalog);
    artifact.command = upper(command);
    artifact.cmdkey = make_cmdkey(artifact.catalog, artifact.command);
    artifact.owner = std::move(owner);
    artifact.kind = kind;
    artifact.source = source;
    artifact.confidence = confidence;
    artifact.severity = severity;
    artifact.name = name;
    artifact.text = text;
    artifact.ordinal = ordinal;
    artifact.detail = detail;
    artifact.evidence = evidence;
    return artifact;
}

} // namespace dottalk::helpdata
