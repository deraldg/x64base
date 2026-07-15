// @dottalk.contract v1
// component: shell_transcript
// role: implementation of shared shell transcript capture service
// owner: DotTalk++ CLI / SelfDoc command infrastructure
// first_consumer: DOTSCRIPT OUT/OUTPUT transcript capture
// behavior: TranscriptTeeBuf duplicates stream writes; ScopedShellTranscript owns start/stop lifecycle
// safety: restores std::cout/std::cerr buffers on scope exit; nested calls reuse active transcript instead of replacing it
// mutation_boundary: no DBF/CDX/LMDB/HELP/CMDHELPCHK/MANSTAR mutation; source service only
// @dottalk.usage v1
// service: shell_transcript::ScopedShellTranscript
// syntax: ScopedShellTranscript(path, append, tee_console, capture_cerr, error_out)
// output: transcript file receives full command output emitted through std::cout
// console: tee_console=true preserves interactive console visibility
// provenance: MDO-377G v1.1 shell transcript service source patch
// @dottalk.contract.end

#include "shell_transcript.hpp"

#include <iostream>
#include <mutex>

namespace shell_transcript {
namespace {
std::mutex g_mutex;
bool g_active = false;
} // namespace

TranscriptTeeBuf::TranscriptTeeBuf(std::streambuf* primary, std::streambuf* secondary)
    : primary_(primary), secondary_(secondary)
{
}

int TranscriptTeeBuf::overflow(int ch)
{
    if (ch == traits_type::eof()) {
        return sync() == 0 ? traits_type::not_eof(ch) : traits_type::eof();
    }

    bool ok = true;
    if (primary_) ok = ok && (primary_->sputc(static_cast<char>(ch)) != traits_type::eof());
    if (secondary_) ok = ok && (secondary_->sputc(static_cast<char>(ch)) != traits_type::eof());
    return ok ? ch : traits_type::eof();
}

int TranscriptTeeBuf::sync()
{
    bool ok = true;
    if (primary_) ok = ok && (primary_->pubsync() == 0);
    if (secondary_) ok = ok && (secondary_->pubsync() == 0);
    return ok ? 0 : -1;
}

ScopedShellTranscript::ScopedShellTranscript(
    const std::filesystem::path& transcript_path,
    bool append,
    bool tee_console,
    bool capture_cerr,
    std::string* error_out
) {
    std::lock_guard<std::mutex> lock(g_mutex);

    if (g_active) {
        nested_existing_ = true;
        ok_ = true;
        return;
    }

    try {
        const auto parent = transcript_path.parent_path();
        if (!parent.empty()) std::filesystem::create_directories(parent);

        const auto mode = std::ios::out | (append ? std::ios::app : std::ios::trunc);
        file_.open(transcript_path, mode);
        if (!file_) {
            if (error_out) *error_out = "unable to open transcript file: " + transcript_path.string();
            return;
        }

        old_cout_ = std::cout.rdbuf();
        cout_tee_ = std::make_unique<TranscriptTeeBuf>(tee_console ? old_cout_ : nullptr, file_.rdbuf());
        std::cout.rdbuf(cout_tee_.get());

        if (capture_cerr) {
            capture_cerr_ = true;
            old_cerr_ = std::cerr.rdbuf();
            cerr_tee_ = std::make_unique<TranscriptTeeBuf>(tee_console ? old_cerr_ : nullptr, file_.rdbuf());
            std::cerr.rdbuf(cerr_tee_.get());
        }

        g_active = true;
        started_here_ = true;
        ok_ = true;
    } catch (const std::exception& ex) {
        if (error_out) *error_out = ex.what();
        stop();
    } catch (...) {
        if (error_out) *error_out = "unknown transcript open failure";
        stop();
    }
}

ScopedShellTranscript::~ScopedShellTranscript()
{
    stop();
}

void ScopedShellTranscript::stop() noexcept
{
    if (!started_here_) return;

    try {
        if (cout_tee_) cout_tee_->pubsync();
        if (cerr_tee_) cerr_tee_->pubsync();

        if (old_cout_) std::cout.rdbuf(old_cout_);
        if (capture_cerr_ && old_cerr_) std::cerr.rdbuf(old_cerr_);

        if (file_) {
            file_.flush();
            file_.close();
        }
    } catch (...) {
        // Destructors must not throw. Stream restoration has already been attempted.
    }

    cout_tee_.reset();
    cerr_tee_.reset();
    old_cout_ = nullptr;
    old_cerr_ = nullptr;
    started_here_ = false;
    ok_ = false;

    std::lock_guard<std::mutex> lock(g_mutex);
    g_active = false;
}

bool active() noexcept
{
    std::lock_guard<std::mutex> lock(g_mutex);
    return g_active;
}

} // namespace shell_transcript
