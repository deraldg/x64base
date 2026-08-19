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
#include <wx/bookctrl.h>
#include <wx/sizer.h>
#include <atomic>
#include <functional>
#include <map>
#include <functional>
#include <memory>
#include <mutex>
#include <condition_variable>
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
    // R46: a notebook OWNS its pages. Destroy() on a page window leaves the book
    // control holding a freed entry and the next Layout() segfaults -- the same
    // shape as the wxStaticBox case, a different owner, a third removal verb.
    // DeletePage destroys the page window, so the scope is cancelled either way;
    // what changes is whether the process survives to observe it.
    if (auto* book = wxDynamicCast(w->GetParent(), wxBookCtrlBase)) {
        for (size_t i = 0; i < book->GetPageCount(); ++i)
            if (book->GetPage(i) == w) {
                book->DeletePage(i);
                book->Layout();
                return true;
            }
    }
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

    /// R47: dogfood x64base. Set this to a callable that issues the house's own
    /// verbs -- SELECT <alias> ; LOCK TABLE for acquire, SELECT <alias> ; UNLOCK
    /// for release -- through `xbase::locks`. It returns false when the engine
    /// refuses, and the runtime then refuses the handler. Left unset, the runtime
    /// gives in-process exclusion only, which is all a frontend with no engine
    /// attached can honestly claim.
    using LockProvider = std::function<bool(bool acquire,
                                            const std::vector<std::string>& aliases)>;
    void set_lock_provider(LockProvider p) { provider_ = std::move(p); }

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
            Hold hold(this, alias);                        // R47: one attempt
            if (!hold.ok) { log("refused " + name + " domain busy"); return false; }
            h->second(*scope);
            log("ui " + name);
            return true;
        }
        if (dispatch == "worker") {
            if (completion.empty()) {
                log("refused " + name + " worker with no ON_COMPLETE");
                return false;
            }
            Handler fn = h->second;
            wxWindow* ui = ui_;
            auto self = this;
            std::thread([this, fn, scope, completion, ui, self, name, alias] {
                std::string result, state = "completed";
                // R47: ONE attempt. A busy domain refuses the handler rather than
                // queueing it -- FLOCK() returns .F., it does not wait. Everything
                // recorded about contention before R47 described a blocking lock
                // the engine does not have.
                {
                    Hold hold(self, alias);
                    if (!hold.ok) {
                        self->log("refused " + name + " domain busy");
                        ui->CallAfter([self, scope, completion] {
                            self->deliver(scope, completion, "domain busy", "refused");
                        });
                        return;
                    }
                    try {
                        result = fn(*scope);               // R21.1 + R26
                    } catch (const std::exception& e) { state = "failed"; result = e.what(); }
                }
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
        aliases_.push_back(d);
        domains_.push_back(d);
        locks_.push_back(std::unique_ptr<std::mutex>(new std::mutex()));
        for (const auto& a : d) of_[a] = locks_.size() - 1;
    }
    // R47: a scoped, NON-BLOCKING domain hold. `xbase::locks::try_lock_table` is a
    // single attempt that returns false -- FLOCK()'s own semantic -- so this is
    // try_lock(), not lock(). Nothing here waits, so no circular wait can form:
    // the AB-BA case that deadlocks a blocking implementation is refused instead.
    // Re-entry by the SAME thread is allowed above the mutex, by depth, because a
    // handler calling a handler on its own data is not contention (R21.1).
    struct Hold {
        Runtime* rt = nullptr;
        size_t   ix = 0;
        bool     ok = false;
        bool     reentered = false;
        Hold(Runtime* r, const std::string& alias) : rt(r) {
            ix = r->index_for(alias);
            auto& depth = r->depth();
            auto d = depth.find(ix);
            if (d != depth.end() && d->second > 0) {
                d->second += 1; ok = reentered = true; return;
            }
            if (!r->locks_[ix]->try_lock()) return;
            if (r->provider_ && !r->provider_(true, r->aliases_[ix])) {
                r->locks_[ix]->unlock(); return;
            }
            depth[ix] = 1;
            ok = true;
        }
        ~Hold() {
            if (!ok) return;
            auto& depth = rt->depth();
            if (--depth[ix] > 0) return;
            if (rt->provider_) rt->provider_(false, rt->aliases_[ix]);
            rt->locks_[ix]->unlock();
        }
        Hold(const Hold&) = delete;
        Hold& operator=(const Hold&) = delete;
    };

    std::map<size_t, int>& depth() {
        static thread_local std::map<size_t, int> d;
        return d;
    }
    size_t index_for(const std::string& alias) {
        auto it = of_.find(alias);
        if (it == of_.end()) { add_domain({alias}); it = of_.find(alias); }
        return it->second;
    }

    std::mutex* lock_for(const std::string& alias) {
        auto it = of_.find(alias);
        if (it == of_.end()) { add_domain({alias}); it = of_.find(alias); }
        return locks_[it->second].get();
    }
    wxWindow* ui_;
    std::vector<std::vector<std::string>> domains_;
    std::vector<std::unique_ptr<std::mutex>> locks_;
    std::vector<std::vector<std::string>> aliases_;
    std::map<std::string, size_t> of_;
    std::map<std::string, Handler> handlers_;
    std::map<std::string, Completion> comps_;
    std::map<std::string, std::function<void()>> host_;
    std::vector<std::string> log_;
    std::mutex logm_;
    LockProvider provider_;
};

}  // namespace uidef
