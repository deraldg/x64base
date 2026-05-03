#include "memo/memo_object.hpp"

#include <algorithm>
#include <cctype>

namespace dottalk::memo {
namespace {

static std::string lower(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return s;
}

static bool starts_with(const std::string& s, const std::string& prefix)
{
    return s.rfind(prefix, 0) == 0;
}

} // namespace

std::string normalize_content_type(const std::string& content_type)
{
    std::string t = lower(content_type);
    const std::size_t semi = t.find(';');
    if (semi != std::string::npos) t = t.substr(0, semi);
    if (t.empty()) return "application/octet-stream";
    return t;
}

bool is_text_content_type(const std::string& content_type)
{
    const std::string t = normalize_content_type(content_type);
    return starts_with(t, "text/") ||
           t == "application/json" ||
           t == "application/xml" ||
           t == "application/xhtml+xml";
}

MemoObjectClass classify_content_type(const std::string& content_type)
{
    const std::string t = normalize_content_type(content_type);

    if (starts_with(t, "text/")) return MemoObjectClass::TextMemo;
    if (t == "application/json" || t == "application/xml" || t == "application/xhtml+xml")
        return MemoObjectClass::StructuredTextMemo;
    if (t == "application/pdf") return MemoObjectClass::DocumentBlob;
    if (starts_with(t, "image/")) return MemoObjectClass::ImageBlob;
    if (starts_with(t, "audio/")) return MemoObjectClass::AudioBlob;
    if (starts_with(t, "video/")) return MemoObjectClass::VideoBlob;
    if (t == "application/zip" || t == "application/gzip") return MemoObjectClass::CompressedBlob;
    if (t == "application/encrypted") return MemoObjectClass::EncryptedBlob;
    return MemoObjectClass::BinaryBlob;
}

MemoCapabilities capabilities_for_content_type(const std::string& content_type)
{
    const std::string t = normalize_content_type(content_type);
    MemoCapabilities c;

    if (is_text_content_type(t)) {
        c.text_displayable = true;
        c.line_pageable = true;
        c.searchable_text = true;
    }

    if (t == "application/pdf" || starts_with(t, "image/") ||
        starts_with(t, "audio/") || starts_with(t, "video/")) {
        c.externally_openable = true;
    }

    if (starts_with(t, "audio/") || starts_with(t, "video/")) {
        c.text_displayable = false;
        c.line_pageable = false;
        c.searchable_text = false;
    }

    return c;
}

} // namespace dottalk::memo
