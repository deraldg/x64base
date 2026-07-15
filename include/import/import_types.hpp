#pragma once
// @dottalk.contract
// file: include/import/import_types.hpp
// subsystem: import
// role: Declares import-path helpers for loading external data into DotTalk++ workflows
// authority: canonical-header-contract
// mutation: token-authorized
// notes: canonical contract annotation inserted by guarded SelfDoc apply script

#include <string>

namespace dottalkpp::import
{

    enum class Delimiter
    {
        Pipe,
        Tab,
        Comma,
        Custom
    };

    enum class Mode
    {
        Preview,
        Validate,
        File,
        Map
    };

    enum class Severity
    {
        Info,
        Warn,
        Error,
        Fatal
    };

    struct ImportOptions
    {
        std::string filePath;
        std::string mapFile;
        std::string targetTable;

        Delimiter delimiter = Delimiter::Pipe;

        bool strictMode = true;
        bool create = false;
        bool append = false;
        bool replace = false;

        std::string encoding = "UTF8";
        std::string nullToken = "\\N";

        int previewRows = 10;
    };

}
