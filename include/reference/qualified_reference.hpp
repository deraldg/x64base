#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace dottalk::reference {

enum class RootSyntax : std::uint8_t {
    Bare,
    Named,
    AreaSlot,
    Variable
};

enum class SegmentSyntax : std::uint8_t {
    Member,
    Index,
    Key,
    Wildcard
};

struct SourceRange final {
    std::size_t begin{0};
    std::size_t end{0};
};

struct ReferenceSegment final {
    SegmentSyntax syntax{SegmentSyntax::Member};
    std::string text;
    SourceRange source;
};

class QualifiedReference final {
public:
    QualifiedReference() = default;

    QualifiedReference(RootSyntax root_syntax,
                       std::string root_name,
                       std::uint32_t area_slot,
                       std::vector<ReferenceSegment> segments,
                       std::string original_text);

    [[nodiscard]] RootSyntax root_syntax() const noexcept { return root_syntax_; }
    [[nodiscard]] const std::string& root_name() const noexcept { return root_name_; }
    [[nodiscard]] std::uint32_t area_slot() const noexcept { return area_slot_; }
    [[nodiscard]] const std::vector<ReferenceSegment>& segments() const noexcept {
        return segments_;
    }
    [[nodiscard]] const std::string& original_text() const noexcept {
        return original_text_;
    }

    [[nodiscard]] std::string canonical_syntax() const;

private:
    RootSyntax root_syntax_{RootSyntax::Bare};
    std::string root_name_;
    std::uint32_t area_slot_{0};
    std::vector<ReferenceSegment> segments_;
    std::string original_text_;
};

struct ParseReferenceResult final {
    bool ok{false};
    QualifiedReference reference;
    std::string error;
    SourceRange error_range;
};

class QualifiedReferenceParser final {
public:
    [[nodiscard]] ParseReferenceResult parse(std::string_view input) const;
};

} // namespace dottalk::reference
