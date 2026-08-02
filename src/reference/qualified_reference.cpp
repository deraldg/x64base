#include "reference/qualified_reference.hpp"

#include <cctype>
#include <limits>
#include <sstream>
#include <utility>

namespace dottalk::reference {
namespace {

bool is_ident_start(char ch) {
    return std::isalpha(static_cast<unsigned char>(ch)) != 0 || ch == '_';
}

bool is_ident_part(char ch) {
    return std::isalnum(static_cast<unsigned char>(ch)) != 0 || ch == '_';
}

std::string trim_copy(std::string_view input) {
    std::size_t first = 0;
    while (first < input.size() &&
           std::isspace(static_cast<unsigned char>(input[first])) != 0) {
        ++first;
    }

    std::size_t last = input.size();
    while (last > first &&
           std::isspace(static_cast<unsigned char>(input[last - 1])) != 0) {
        --last;
    }

    return std::string(input.substr(first, last - first));
}

class Parser final {
public:
    explicit Parser(std::string_view input) : input_(input) {}

    ParseReferenceResult run() {
        ParseReferenceResult result;
        skip_space();
        if (eof()) return fail("reference is empty", pos_, pos_);

        RootSyntax root_syntax = RootSyntax::Bare;
        std::string root_name;
        std::uint32_t area_slot = 0;

        if (peek() == '#') {
            root_syntax = RootSyntax::AreaSlot;
            const std::size_t start = pos_++;
            if (eof() || !std::isdigit(static_cast<unsigned char>(peek()))) {
                return fail("area slot requires digits", start, pos_);
            }

            std::uint64_t slot = 0;
            while (!eof() &&
                   std::isdigit(static_cast<unsigned char>(peek())) != 0) {
                const unsigned digit = static_cast<unsigned>(peek() - '0');
                if (slot > (std::numeric_limits<std::uint32_t>::max() - digit) / 10) {
                    return fail("area slot is out of range", start, pos_ + 1);
                }
                slot = slot * 10 + digit;
                ++pos_;
            }
            area_slot = static_cast<std::uint32_t>(slot);
        } else if (peek() == '$') {
            root_syntax = RootSyntax::Variable;
            ++pos_;
            if (!parse_identifier(root_name)) {
                return fail("variable reference requires an identifier", pos_, pos_ + 1);
            }
        } else {
            if (!parse_identifier(root_name)) {
                return fail("reference root must be an identifier, #slot, or $variable",
                            pos_, pos_ + 1);
            }
            root_syntax = RootSyntax::Named;
        }

        std::vector<ReferenceSegment> segments;

        while (true) {
            skip_space();
            if (eof()) break;

            if (peek() == '.') {
                const std::size_t start = pos_++;
                skip_space();

                if (eof()) return fail("member name expected after '.'", start, pos_);

                if (peek() == '*') {
                    ++pos_;
                    segments.push_back(
                        ReferenceSegment{SegmentSyntax::Wildcard, "*", {start, pos_}});
                    continue;
                }

                std::string member;
                if (!parse_identifier(member)) {
                    return fail("member name expected after '.'", start, pos_ + 1);
                }
                segments.push_back(
                    ReferenceSegment{SegmentSyntax::Member, std::move(member), {start, pos_}});
                continue;
            }

            if (peek() == '[') {
                const std::size_t start = pos_++;
                const std::size_t content_start = pos_;
                bool in_single = false;
                bool in_double = false;
                bool escaped = false;
                int nested = 0;

                while (!eof()) {
                    const char ch = peek();

                    if (escaped) {
                        escaped = false;
                        ++pos_;
                        continue;
                    }
                    if (ch == '\\' && (in_single || in_double)) {
                        escaped = true;
                        ++pos_;
                        continue;
                    }
                    if (in_single) {
                        if (ch == '\'') in_single = false;
                        ++pos_;
                        continue;
                    }
                    if (in_double) {
                        if (ch == '"') in_double = false;
                        ++pos_;
                        continue;
                    }
                    if (ch == '\'') {
                        in_single = true;
                        ++pos_;
                        continue;
                    }
                    if (ch == '"') {
                        in_double = true;
                        ++pos_;
                        continue;
                    }
                    if (ch == '[') {
                        ++nested;
                        ++pos_;
                        continue;
                    }
                    if (ch == ']') {
                        if (nested == 0) break;
                        --nested;
                        ++pos_;
                        continue;
                    }
                    ++pos_;
                }

                if (eof()) return fail("missing closing ']'", start, pos_);

                const std::size_t content_end = pos_;
                ++pos_; // closing bracket

                std::string content =
                    trim_copy(input_.substr(content_start, content_end - content_start));
                if (content.empty()) {
                    return fail("bracket reference cannot be empty", start, pos_);
                }

                SegmentSyntax syntax = SegmentSyntax::Index;
                if (content.size() >= 2 &&
                    ((content.front() == '"' && content.back() == '"') ||
                     (content.front() == '\'' && content.back() == '\''))) {
                    syntax = SegmentSyntax::Key;
                    content = content.substr(1, content.size() - 2);
                }

                segments.push_back(ReferenceSegment{syntax, std::move(content), {start, pos_}});
                continue;
            }

            return fail("unexpected trailing character", pos_, pos_ + 1);
        }

        if (root_syntax == RootSyntax::Named && segments.empty()) {
            root_syntax = RootSyntax::Bare;
        }

        result.ok = true;
        result.reference = QualifiedReference(root_syntax,
                                              std::move(root_name),
                                              area_slot,
                                              std::move(segments),
                                              std::string(input_));
        return result;
    }

private:
    ParseReferenceResult fail(const std::string& message,
                              std::size_t begin,
                              std::size_t end) const {
        ParseReferenceResult result;
        result.error = message;
        result.error_range = SourceRange{begin, end};
        return result;
    }

    bool eof() const noexcept { return pos_ >= input_.size(); }
    char peek() const noexcept { return eof() ? '\0' : input_[pos_]; }

    void skip_space() {
        while (!eof() &&
               std::isspace(static_cast<unsigned char>(peek())) != 0) {
            ++pos_;
        }
    }

    bool parse_identifier(std::string& out) {
        if (eof() || !is_ident_start(peek())) return false;
        const std::size_t start = pos_++;
        while (!eof() && is_ident_part(peek())) ++pos_;
        out = std::string(input_.substr(start, pos_ - start));
        return true;
    }

    std::string_view input_;
    std::size_t pos_{0};
};

} // namespace

QualifiedReference::QualifiedReference(
    RootSyntax root_syntax,
    std::string root_name,
    std::uint32_t area_slot,
    std::vector<ReferenceSegment> segments,
    std::string original_text)
    : root_syntax_(root_syntax),
      root_name_(std::move(root_name)),
      area_slot_(area_slot),
      segments_(std::move(segments)),
      original_text_(std::move(original_text)) {}

std::string QualifiedReference::canonical_syntax() const {
    std::ostringstream out;

    switch (root_syntax_) {
        case RootSyntax::AreaSlot:
            out << '#' << area_slot_;
            break;
        case RootSyntax::Variable:
            out << '$' << root_name_;
            break;
        case RootSyntax::Bare:
        case RootSyntax::Named:
            out << root_name_;
            break;
    }

    for (const auto& segment : segments_) {
        switch (segment.syntax) {
            case SegmentSyntax::Member:
                out << '.' << segment.text;
                break;
            case SegmentSyntax::Wildcard:
                out << ".*";
                break;
            case SegmentSyntax::Index:
                out << '[' << segment.text << ']';
                break;
            case SegmentSyntax::Key:
                out << "[\"" << segment.text << "\"]";
                break;
        }
    }

    return out.str();
}

ParseReferenceResult QualifiedReferenceParser::parse(std::string_view input) const {
    return Parser(input).run();
}

} // namespace dottalk::reference
