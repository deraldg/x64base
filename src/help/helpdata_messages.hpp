// ============================================================================
// File: src/help/helpdata_messages.hpp
// Purpose: Shared, compiled, reusable HELP/system message registry.
// ============================================================================
#pragma once

#include <string>
#include <unordered_map>
#include <vector>

namespace dottalk::helpdata {

enum class MessageId {
    HelpHintCommand,
    UnknownCommand,
    MissingArgument,
    TooManyArguments,
    InvalidOption,
    CommandNotImplemented,
    CommandDeprecated,
    NoOpenTable,
    NoSelectedArea
};

struct MessageDef {
    MessageId   id;
    const char* key;
    const char* owner;    // GLOBAL, COMMAND:<name>, SUBSYSTEM:<name>
    const char* category; // HINT, ERROR, WARNING, STATUS, etc.
    const char* severity; // INFO, WARNING, ERROR, FATAL
    const char* text;     // May contain {placeholders}.
};

const std::vector<MessageDef>& all_messages();
const MessageDef* find_message(MessageId id);
const MessageDef* find_message_by_key(const std::string& key);

std::string format_message(MessageId id,
                           const std::unordered_map<std::string, std::string>& vars = {});

} // namespace dottalk::helpdata
