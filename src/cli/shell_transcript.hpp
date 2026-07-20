#pragma once
// @dottalk.contract v1
// component: shell_transcript
// role: shared shell transcript capture service
// owner: DotTalk++ CLI / SelfDoc command infrastructure
// first_consumer: DOTSCRIPT OUT/OUTPUT transcript capture
// future_consumer: TEST logfile/full-output capture after DOTSCRIPT proof
// safety: service only; no DBF/CDX/LMDB/HELP/CMDHELPCHK/MANSTAR mutation
// interface: shell_transcript::ScopedShellTranscript
// syntax: ScopedShellTranscript(path, append, tee_console, capture_cerr, error_out)
// behavior: tees std::cout, and optionally std::cerr, to transcript file while preserving console output
// contract: always restore stream buffers through RAII destruction
// provenance: MDO-377G v1.1 shell transcript service source patch
// @dottalk.contract.end

#include <filesystem>
#include <fstream>
#include <memory>
#include <streambuf>
#include <string>

namespace shell_transcript {

class TranscriptTeeBuf final : public std::streambuf {
public:
    TranscriptTeeBuf(std::streambuf* primary, std::streambuf* secondary);

protected:
    int overflow(int ch) override;
    int sync() override;

private:
    std::streambuf* primary_ = nullptr;
    std::streambuf* secondary_ = nullptr;
};

class ScopedShellTranscript final {
public:
    ScopedShellTranscript() = default;
    ScopedShellTranscript(
        const std::filesystem::path& transcript_path,
        bool append,
        bool tee_console,
        bool capture_cerr,
        std::string* error_out
    );

    ScopedShellTranscript(const ScopedShellTranscript&) = delete;
    ScopedShellTranscript& operator=(const ScopedShellTranscript&) = delete;
    ScopedShellTranscript(ScopedShellTranscript&&) = delete;
    ScopedShellTranscript& operator=(ScopedShellTranscript&&) = delete;

    ~ScopedShellTranscript();

    bool ok() const noexcept { return ok_; }
    bool active() const noexcept { return ok_; }
    bool started_here() const noexcept { return started_here_; }
    bool nested_existing() const noexcept { return nested_existing_; }

private:
    bool ok_ = false;
    bool started_here_ = false;
    bool nested_existing_ = false;
    bool capture_cerr_ = false;

    std::ofstream file_;
    std::streambuf* old_cout_ = nullptr;
    std::streambuf* old_cerr_ = nullptr;
    std::unique_ptr<TranscriptTeeBuf> cout_tee_;
    std::unique_ptr<TranscriptTeeBuf> cerr_tee_;

    void stop() noexcept;
};

bool active() noexcept;

} // namespace shell_transcript
