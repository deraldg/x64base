#pragma once

#include "memo/memo_ref.hpp"

#include <cstdint>
#include <string>

namespace dottalk::memo {

enum class MemoObjectClass {
    TextMemo,
    StructuredTextMemo,
    DocumentBlob,
    ImageBlob,
    AudioBlob,
    VideoBlob,
    BinaryBlob,
    CompressedBlob,
    EncryptedBlob
};

struct MemoCapabilities {
    bool streamable{true};
    bool text_displayable{false};
    bool line_pageable{false};
    bool searchable_text{false};
    bool exportable{true};
    bool importable{true};
    bool externally_openable{false};
    bool verifiable{true};
    bool repairable{false};
};

struct MemoObject {
    MemoRef ref;
    MemoObjectClass object_class{MemoObjectClass::BinaryBlob};
    std::string content_type{"application/octet-stream"};
    std::string encoding;
    std::uint64_t size_bytes{0};
    std::uint32_t flags{0};
};

MemoObjectClass classify_content_type(const std::string& content_type);
MemoCapabilities capabilities_for_content_type(const std::string& content_type);
bool is_text_content_type(const std::string& content_type);
std::string normalize_content_type(const std::string& content_type);

} // namespace dottalk::memo
