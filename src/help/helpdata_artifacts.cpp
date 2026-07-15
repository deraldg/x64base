// ============================================================================
// File: src/help/helpdata_artifacts.cpp
// ============================================================================
#include "helpdata_artifacts.hpp"

namespace dottalk::helpdata {

Owner owner_from_string(const std::string& text)
{
    const std::string value = upper(text);

    if (value.empty() || value == "GLOBAL") {
        return { OwnerKind::Global, {} };
    }
    if (value.rfind("COMMAND:", 0) == 0) {
        return { OwnerKind::Command, value.substr(8) };
    }
    if (value.rfind("SUBSYSTEM:", 0) == 0) {
        return { OwnerKind::Subsystem, value.substr(10) };
    }
    if (value.rfind("MINER:", 0) == 0) {
        return { OwnerKind::Miner, value.substr(6) };
    }
    return { OwnerKind::Global, value };
}

ArtifactKind artifact_kind_from_category(const std::string& category)
{
    const std::string value = upper(category);

    if (value == "SUMMARY")       return ArtifactKind::Summary;
    if (value == "SYNTAX")        return ArtifactKind::Syntax;
    if (value == "ARGUMENT")      return ArtifactKind::Argument;
    if (value == "ARG")           return ArtifactKind::Argument;
    if (value == "EXAMPLE")       return ArtifactKind::Example;
    if (value == "SAMPLE")        return ArtifactKind::Example;
    if (value == "NOTE")          return ArtifactKind::Note;
    if (value == "WARNING")       return ArtifactKind::Warning;
    if (value == "ERROR")         return ArtifactKind::Error;
    if (value == "HINT")          return ArtifactKind::Hint;
    if (value == "MESSAGE")       return ArtifactKind::Message;
    if (value == "STATUS")        return ArtifactKind::Status;
    if (value == "COMPATIBILITY") return ArtifactKind::Compatibility;
    if (value == "COMPAT")        return ArtifactKind::Compatibility;
    if (value == "DEPRECATION")   return ArtifactKind::Deprecation;
    if (value == "UNSUPPORTED")   return ArtifactKind::Unsupported;
    if (value == "ALIAS")         return ArtifactKind::Alias;
    if (value == "VARIANT")       return ArtifactKind::Variant;
    if (value == "RELATED")       return ArtifactKind::Related;
    if (value == "SOURCE_FACT")   return ArtifactKind::SourceFact;

    return ArtifactKind::Message;
}

Severity severity_from_string(const std::string& severity)
{
    const std::string value = upper(severity);

    if (value == "INFO")    return Severity::Info;
    if (value == "WARNING") return Severity::Warning;
    if (value == "ERROR")   return Severity::Error;
    if (value == "FATAL")   return Severity::Fatal;
    return Severity::None;
}

Artifact artifact_from_message(const MessageDef& message)
{
    Artifact artifact;
    artifact.catalog = "SYSTEM";
    artifact.command.clear();
    artifact.cmdkey.clear();
    artifact.owner = owner_from_string(message.owner ? message.owner : "GLOBAL");
    artifact.kind = artifact_kind_from_category(message.category ? message.category : "MESSAGE");
    artifact.source = SourceKind::SharedMessage;
    artifact.confidence = Confidence::Authoritative;
    artifact.severity = severity_from_string(message.severity ? message.severity : "INFO");
    artifact.name = message.key ? message.key : "";
    artifact.text = message.text ? message.text : "";
    artifact.ordinal = 0;
    return artifact;
}

std::vector<Artifact> artifacts_from_standard_messages()
{
    std::vector<Artifact> out;
    int ordinal = 1;
    for (const auto& message : all_messages()) {
        Artifact artifact = artifact_from_message(message);
        artifact.ordinal = ordinal++;
        out.push_back(std::move(artifact));
    }
    return out;
}

} // namespace dottalk::helpdata
