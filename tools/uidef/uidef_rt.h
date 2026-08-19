// The UIDEF dispatch runtime, in C++. AIF-120, R41.
//
// R37 built this in Python and R38/R39 proved it on Tk. R40 emitted wx C++ and
// bound no events, so the concurrency half of the contract had never run on a
// compiled target with a different threading primitive. This is that runtime:
// std::thread and std::mutex instead of Python threads, wxWindow::CallAfter
// instead of a queue polled by `after()`.
//
//   R21.1  the lock is taken around the WHOLE handler, not per operation
//   R21.4  a completion is delivered AT MOST once; a destroyed scope drops it
//   R26    the lock is per LOCK DOMAIN, read from the document's SOURCE (R36)
//   R11.3  a completion runs on the UI thread; asserted, not assumed
//   R20    a `host` handler needs no thread rule and no completion
#pragma once
#include <wx/wx.h>
#include <wx/statbox.h>
#include <wx/sizer.h>
#include <atomic>
#include <functional>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

namespace uidef {

struct Scope {
    std::string name;
    std::atomic<bool> cancelled{false};
    std::atomic<bool> alive{true};
    explicit Scope(std::string n) : name(std::move(n)) {}
    void destroy() { alive = false; cancelled = true; }
};

// R45: a UIDEF `group` becomes a wxStaticBox, and a wxStaticBoxSizer OWNS that
// box. Calling Destroy() on the box leaves the sizer holding a freed pointer, and
// the next Layout() segfaults -- exit 139, no diagnostic. R44 named the containers
// so a target could reach them and thereby handed out a handle that is unsafe to
// use in the obvious way.
//
// The safe teardown is to delete the OWNING SIZER, whose destructor destroys the
// box; the box's wxEVT_DESTROY still fires, so the scope is still cancelled. A
// target must not have to know that, so it is here rather than in a comment.
inline wxStaticBoxSizer* uidef_owner_of(wxSizer* s, wxStaticBox* box) {
    if (!s) return nullptr;
    if (auto* sb = dynamic_cast<wxStaticBoxSizer*>(s))
        if (sb->GetStaticBox() == box) return sb;
    for (auto* item : s->GetChildren())
        if (auto* r = uidef_owner_of(item->GetSizer(), box)) return r;
    return nullptr;
}

inline bool uidef_detach(wxSizer* from, wxSizer* target) {
    if (!from) return false;
    if (from->Detach(target)) return true;
    for (auto* item : from->GetChildren())
        if (uidef_detach(item->GetSizer(), target)) return true;
    return false;
}

// Destroying a window with Destroy() defers to idle and every descendant gets its
// own wxEVT_DESTROY on the way down. Deleting a sizer runs the destructors
// IMMEDIATELY, and the descendants' bound handlers are gone by the time their
// windows die -- so the safe-teardown path silently stopped cancelling nested
// scopes while the crashing path had cancelled them correctly. Two ways to remove
// the same container disagreed about R21.4.
//
// So the intent is announced before either teardown runs, depth-first, and the
// handlers are idempotent (Scope::destroy only sets flags) so the second
// announcement from a real wxEVT_DESTROY costs nothing.
inline void uidef_announce_destroy(wxWindow* w) {
    for (auto* c : w->GetChildren()) uidef_announce_destroy(c);
    wxWindowDestroyEvent e(w);
    w->GetEventHandler()->ProcessEvent(e);
}

/// Destroy the container named `objid` (its OBJID, set by the generator).
/// Returns false if no such container is reachable from `root`.
inline bool destroy_container(wxWindow* root, const wxString& objid) {
    wxWindow* w = wxWindow::FindWindowByName(objid, root);
    if (!w) return false;
    uidef_announce_destroy(w);
    if (auto* box = wxDynamicCast(w, wxStaticBox)) {
        wxWindow* parent = box->GetParent();
        wxSizer* top = parent ? parent->GetSizer() : nullptr;
        if (wxStaticBoxSizer* owner = uidef_owner_of(top, box)) {
            if (owner == top) parent->SetSizer(nullptr, false);
            else uidef_detach(top, owner);
            delete owner;              // destroys the box, fires wxEVT_DESTROY
            if (parent) parent->Layout();
            return true;
        }
    }
    w->Destroy();
    if (w->GetParent()) w->GetParent()->Layout();
    return true;
}

class Runtime {
public:
    using Handler   = std::function<std::string(Scope&)>;
    using Completion= std::function<void(Scope&, const std::string&, const std::string&)>;

    Runtime(wxWindow* ui, const std::vector<std::vector<std::string>>& domains,
            bool per_area = false)
        : ui_(ui) {
        for (const auto& d : domains) {
            if (per_area) {                  // the wrong reading, kept runnable
                for (const auto& a : d) add_domain({a});
            } else {
                add_domain(d);
            }
        }
    }

    void reg(const std::string& n, Handler h)    { handlers_[n] = std::move(h); }
    void comp(const std::string& n, Completion c){ comps_[n]    = std::move(c); }
    void host(const std::string& n, std::function<void()> f) { host_[n] = std::move(f); }
    void log(const std::string& s) { std::lock_guard<std::mutex> g(logm_); log_.push_back(s); }
    std::vector<std::string> lines() { std::lock_guard<std::mutex> g(logm_); return log_; }

    bool fire(const std::string& name, const std::string& dispatch,
              std::shared_ptr<Scope> scope, const std::string& alias,
              const std::string& completion) {
        if (dispatch == "host") {
            auto it = host_.find(name);
            if (it == host_.end()) { log("refused " + name + " no host capability"); return false; }
            it->second();                                  // R20: no thread rule
            log("host " + name);
            return true;
        }
        auto h = handlers_.find(name);
        if (h == handlers_.end()) { log("refused " + name + " not in the registry"); return false; }

        if (dispatch == "ui") {
            std::lock_guard<std::mutex> g(*lock_for(alias));
            h->second(*scope);
            log("ui " + name);
            return true;
        }
        if (dispatch == "worker") {
            if (completion.empty()) {
                log("refused " + name + " worker with no ON_COMPLETE");
                return false;
            }
            std::mutex* m = lock_for(alias);
            Handler fn = h->second;
            wxWindow* ui = ui_;
            auto self = this;
            std::thread([this, fn, m, scope, completion, ui, self, name] {
                std::string result, state = "completed";
                try {
                    std::lock_guard<std::mutex> g(*m);     // R21.1 + R26
                    result = fn(*scope);
                } catch (const std::exception& e) { state = "failed"; result = e.what(); }
                if (scope->cancelled) state = "cancelled";
                ui->CallAfter([self, scope, completion, result, state] {
                    self->deliver(scope, completion, result, state);
                });
            }).detach();
            log("worker " + name);
            return true;
        }
        log("refused " + name + " unknown dispatch " + dispatch);
        return false;
    }

    void deliver(std::shared_ptr<Scope> scope, const std::string& comp,
                 const std::string& result, const std::string& state) {
        if (!scope->alive) { log("dropped " + comp + " " + scope->name); return; }
        auto it = comps_.find(comp);
        if (it == comps_.end()) { log("refused " + comp + " completion not registered"); return; }
        wxASSERT_MSG(wxThread::IsMain(), "a completion ran off the UI thread -- R11.3");
        it->second(*scope, result, state);
        log("complete " + comp + " " + state);
    }

    std::vector<std::vector<std::string>> describe() const {
        std::vector<std::vector<std::string>> out;
        for (const auto& d : domains_) out.push_back(d);
        return out;
    }

private:
    void add_domain(const std::vector<std::string>& d) {
        domains_.push_back(d);
        locks_.push_back(std::unique_ptr<std::mutex>(new std::mutex()));
        for (const auto& a : d) of_[a] = locks_.size() - 1;
    }
    std::mutex* lock_for(const std::string& alias) {
        auto it = of_.find(alias);
        if (it == of_.end()) { add_domain({alias}); it = of_.find(alias); }
        return locks_[it->second].get();
    }
    wxWindow* ui_;
    std::vector<std::vector<std::string>> domains_;
    std::vector<std::unique_ptr<std::mutex>> locks_;
    std::map<std::string, size_t> of_;
    std::map<std::string, Handler> handlers_;
    std::map<std::string, Completion> comps_;
    std::map<std::string, std::function<void()>> host_;
    std::vector<std::string> log_;
    std::mutex logm_;
};

}  // namespace uidef
