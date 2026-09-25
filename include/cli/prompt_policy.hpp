// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: prompt suppression policy -- whether an interactive prompt may be asked
// project: project.x64base.runtime
// lane: AIF-120
// owner: member.derald
// status: supported

#pragma once

// THE HOME FOR "MAY THIS PROCESS ASK A HUMAN".
//
// Until 2026-09-25 this was a file-static `g_suppress_prompts` inside
// src/cli/dirty_prompt.cpp, reachable by nothing and owned by one command's
// translation unit while three call families depended on it (R131 recorded it
// is set only on the QUIT path and that DOTSCRIPT never touches it).
//
// IT IS MOVED HERE BECAUSE IT IS NOT dirty_prompt's PROPERTY. It answers a
// process-wide question -- is anyone there to answer -- which R147's ASK
// protocol will consult for every prompt, not only the dirty-buffer one. When
// that protocol lands, an unanswerable ASK resolves to its declared default
// instead of being asked; under the owner's ruling of 2026-09-25 the dirty
// precondition's default is PROCEED, which is exactly what suppression does
// today, so unattended behaviour does not change.
//
// SuppressScope EXISTS BECAUSE THE HAND-ROLLED SAVE/RESTORE LEAKED.
// `commit_area0()` saved the flag, set it, called ::cmd_COMMIT, and restored it
// on the NEXT LINE -- inside a try block whose catch(...) prints "COMMIT failed
// (exception)" and returns. A throwing COMMIT therefore skipped the restore and
// left suppression ON FOR THE LIFE OF THE PROCESS, after which every USE, CLOSE
// and QUIT proceeds without asking and without committing. The GUI bridge keeps
// ONE dottalkpp.exe alive across every command, so there it would persist for
// the whole session. A scope guard restores on both paths.

namespace cli::prompt {

// True when prompts must not be asked: the caller is unattended, or is already
// inside a prompt-driven operation. Readers treat it as "proceed with the
// declared default", never as "the answer was no".
bool suppressed();

void set_suppressed(bool value);

// Restores the previous value on destruction, including when the guarded call
// throws. Prefer this to a manual save/restore.
class SuppressScope {
public:
    explicit SuppressScope(bool value = true);
    ~SuppressScope();

    SuppressScope(const SuppressScope&) = delete;
    SuppressScope& operator=(const SuppressScope&) = delete;
    SuppressScope(SuppressScope&&) = delete;
    SuppressScope& operator=(SuppressScope&&) = delete;

private:
    bool prev_;
};

} // namespace cli::prompt
