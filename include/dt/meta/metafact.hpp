#pragma once

#include <cstdint>
#include <string>

namespace dt::meta {

enum class MetaFactDomain : std::uint8_t {
    Unknown = 0,
    Command,
    Function,
    Subcommand,
    EntryVariant,
    Argument,
    HelpText,
    Message,
    FieldDictionary,
    RuntimeProof
};

enum class MetaFactEvidenceKind : std::uint8_t {
    Unknown = 0,
    SourceCatalog,
    SourceRegistry,
    MetadataTable,
    RuntimeTranscript,
    GeneratedHelp,
    CuratedHelp,
    GeneratedReport
};

struct MetaFact {
    MetaFactDomain domain = MetaFactDomain::Unknown;
    MetaFactEvidenceKind evidence_kind = MetaFactEvidenceKind::Unknown;

    std::string canonical_name;
    std::string display_name;
    std::string owner;
    std::string visibility_tier;
    std::string implementation_status;

    std::string source_authority;
    std::string source_file;
    std::string handler;

    bool dispatch_reachable = false;
    bool public_surface = false;
    bool self_registered = false;
    bool generated = false;
    bool curated = false;
    bool active = true;

    std::string evidence_value;
    std::string notes;
};

const char* to_string(MetaFactDomain domain) noexcept;
const char* to_string(MetaFactEvidenceKind kind) noexcept;

} // namespace dt::meta
