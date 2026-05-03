#include "cli/text_editor.hpp"

#include <cstdlib>
#include <fstream>
#include <filesystem>
#include <chrono>
#include <sstream>
#include <random>

namespace fs = std::filesystem;

namespace text_editor
{

//------------------------------------------------------------
// Resolve editor command
//------------------------------------------------------------

std::string resolve_editor()
{
    const char* env;

    env = std::getenv("DOTTALK_EDITOR");
    if (env && *env) return env;

    env = std::getenv("VISUAL");
    if (env && *env) return env;

    env = std::getenv("EDITOR");
    if (env && *env) return env;

#ifdef _WIN32
    return "notepad";
#elif defined(__APPLE__)
    return "open -W -t";
#else
    return "nano";
#endif
}

//------------------------------------------------------------
// Create temp file (collision-safe)
//------------------------------------------------------------

std::string make_temp_file()
{
    auto tmp = fs::temp_directory_path();

    // add randomness to avoid collisions
    static std::mt19937_64 rng{ std::random_device{}() };
    auto now = std::chrono::high_resolution_clock::now()
        .time_since_epoch()
        .count();

    std::stringstream ss;
    ss << "dottalk_memo_" << now << "_" << rng() << ".txt";

    fs::path p = tmp / ss.str();
    return p.string();
}

//------------------------------------------------------------
// Launch editor
//------------------------------------------------------------

bool launch_editor(const std::string& editor, const std::string& file)
{
    std::string cmd = editor + " \"" + file + "\"";

    int result = std::system(cmd.c_str());

    return result == 0;
}

//------------------------------------------------------------
// Core edit workflow
//------------------------------------------------------------

static bool edit_text(std::string& text, std::string* err)
{
    std::string editor = resolve_editor();
    std::string temp   = make_temp_file();

    // write current text contents
    {
        std::ofstream out(temp, std::ios::binary);
        if (!out)
        {
            if (err) *err = "unable to create temp file";
            return false;
        }
        out << text;
    }

    // launch editor
    if (!launch_editor(editor, temp))
    {
        if (err) *err = "editor launch failed";
        return false;
    }

    // read edited contents
    {
        std::ifstream in(temp, std::ios::binary);
        if (!in)
        {
            if (err) *err = "unable to read temp file";
            return false;
        }

        std::stringstream buffer;
        buffer << in.rdbuf();
        text = buffer.str();
    }

    // remove temp file (ignore failure)
    std::error_code ec;
    fs::remove(temp, ec);

    return true;
}

//------------------------------------------------------------
// Public API
//------------------------------------------------------------

bool edit_text_via_editor(std::string& text, std::string* err)
{
    if (!edit_text(text, err))
        return false;

    if (err) err->clear();
    return true;
}

} // namespace text_editor