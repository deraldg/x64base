// ============================================================================
// File: src/help/helpdata_messages.cpp
// ============================================================================
#include "helpdata_messages.hpp"

namespace dottalk::helpdata {

const std::vector<MessageDef>& all_messages()
{
    static const std::vector<MessageDef> messages = {
        {
            MessageId::HelpHintCommand,
            "HELP_HINT_COMMAND",
            "GLOBAL",
            "HINT",
            "INFO",
            "Type HELP {command} for more information."
        },
        {
            MessageId::UnknownCommand,
            "UNKNOWN_COMMAND",
            "GLOBAL",
            "ERROR",
            "ERROR",
            "Unknown command: {command}"
        },
        {
            MessageId::MissingArgument,
            "MISSING_ARGUMENT",
            "GLOBAL",
            "ERROR",
            "ERROR",
            "Missing required argument."
        },
        {
            MessageId::TooManyArguments,
            "TOO_MANY_ARGUMENTS",
            "GLOBAL",
            "ERROR",
            "ERROR",
            "Too many arguments."
        },
        {
            MessageId::InvalidOption,
            "INVALID_OPTION",
            "GLOBAL",
            "ERROR",
            "ERROR",
            "Invalid option: {option}"
        },
        {
            MessageId::CommandNotImplemented,
            "COMMAND_NOT_IMPLEMENTED",
            "GLOBAL",
            "STATUS",
            "WARNING",
            "Command is recognized but not implemented: {command}"
        },
        {
            MessageId::CommandDeprecated,
            "COMMAND_DEPRECATED",
            "GLOBAL",
            "DEPRECATION",
            "WARNING",
            "Command is deprecated: {command}"
        },
        {
            MessageId::NoOpenTable,
            "NO_OPEN_TABLE",
            "SUBSYSTEM:DBAREA",
            "ERROR",
            "ERROR",
            "No table is currently open."
        },
        {
            MessageId::NoSelectedArea,
            "NO_SELECTED_AREA",
            "SUBSYSTEM:DBAREA",
            "ERROR",
            "ERROR",
            "No current work area is selected."
        }
    };
    return messages;
}

const MessageDef* find_message(MessageId id)
{
    for (const auto& message : all_messages()) {
        if (message.id == id) {
            return &message;
        }
    }
    return nullptr;
}

const MessageDef* find_message_by_key(const std::string& key)
{
    for (const auto& message : all_messages()) {
        if (key == message.key) {
            return &message;
        }
    }
    return nullptr;
}

std::string format_message(MessageId id,
                           const std::unordered_map<std::string, std::string>& vars)
{
    const MessageDef* message = find_message(id);
    if (!message) {
        return {};
    }

    std::string out = message->text ? message->text : "";
    for (const auto& kv : vars) {
        const std::string needle = "{" + kv.first + "}";
        std::string::size_type pos = 0;
        while ((pos = out.find(needle, pos)) != std::string::npos) {
            out.replace(pos, needle.size(), kv.second);
            pos += kv.second.size();
        }
    }
    return out;
}

} // namespace dottalk::helpdata
