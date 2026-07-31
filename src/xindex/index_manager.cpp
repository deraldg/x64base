// @dottalk.file v1
// subsystem: xindex
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/xindex/index_manager.cpp
#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <cstdlib>
#include <iostream>
#include <locale>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "xbase/ramfs.hpp"
#include "cdx/cdx_meta.hpp"
#include "cli/path_resolver.hpp"
#include "xindex/index_manager.hpp"
#include "cnx/cnx_backend.hpp"
#include "xindex/cdx_native_backend.hpp"

namespace fs = std::filesystem;

namespace xindex {

static inline bool ends_with_icase_(std::string s, std::string suf) {
    if (s.size() < suf.size()) return false;
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char ch){ return static_cast<char>(std::tolower(ch)); });
    std::transform(suf.begin(), suf.end(), suf.begin(),
        [](unsigned char ch){ return static_cast<char>(std::tolower(ch)); });
    return s.compare(s.size() - suf.size(), suf.size(), suf) == 0;
}

static inline std::string read_all_text_(const fs::path& p) {
    std::ifstream in(p, std::ios::binary);
    if (!in) return {};
    std::ostringstream ss;
    ss << in.rdbuf();
    return ss.str();
}

static inline std::string json_string_value_(const std::string& doc, const std::string& key) {
    const std::string needle = "\"" + key + "\"";
    auto pos = doc.find(needle);
    if (pos == std::string::npos) return {};
    pos = doc.find(':', pos + needle.size());
    if (pos == std::string::npos) return {};
    pos = doc.find('"', pos);
    if (pos == std::string::npos) return {};
    auto end = doc.find('"', pos + 1);
    if (end == std::string::npos) return {};
    return doc.substr(pos + 1, end - (pos + 1));
}

std::string IndexManager::to_upper_copy_ascii_(std::string s) {
    for (auto& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

IndexManager::IndexManager(xbase::DbArea& area) : area_(area) {}

IndexManager::~IndexManager() {
    close();
}

void IndexManager::close() noexcept {
    if (backend_) {
        backend_->close();
        backend_.reset();
    }
    container_path_.clear();
    tag_upper_.clear();
}

bool IndexManager::isCdx() const noexcept {
    return dynamic_cast<const CdxBackend*>(backend_.get()) != nullptr;
}

bool IndexManager::isCnx() const noexcept {
    return dynamic_cast<const CnxBackend*>(backend_.get()) != nullptr;
}

std::string IndexManager::activeTag() const {
    if (!backend_) return {};
    if (auto* tb = dynamic_cast<ITagBackend*>(backend_.get())) return tb->activeTag();
    return tag_upper_;
}

bool IndexManager::openCdx(const std::string& cdx_container_path,
                           const std::string& tag_upper,
                           std::string* err) {
    close();

    if (cdx_container_path.empty()) {
        if (err) *err = "openCdx: empty path";
        return false;
    }

    // In-memory tables (AIF-043 V4e): a .cdx under a mounted ramfs root uses the
    // native CDX-V64 backend (uint64, LMDB-free) served from RAM. Skip the
    // cdx_meta sidecar (not ramfs-routed) and the LMDB env gate entirely; the
    // native backend opens the .cdx container directly. Disk .cdx still routes to
    // the LMDB CdxBackend below.
    if (xbase::ramfs::is_virtual(cdx_container_path)) {
        auto b = std::make_unique<CdxNativeBackend>(area_, cdx_container_path, tag_upper);
        if (!b->open(cdx_container_path)) {
            if (err) *err = "openCdx(native): backend open failed: " + cdx_container_path;
            return false;
        }
        backend_ = std::move(b);
        container_path_ = cdx_container_path;
        if (!tag_upper.empty()) {
            if (!setTag(tag_upper, err)) return false;
        }
        return true;
    }

    const auto identity = cdxmeta::build_identity(area_);

    auto same_core_shape = [&](const cdxmeta::TableIdentity& a,
                               const cdxmeta::TableIdentity& b) -> bool {
        return a.kind        == b.kind &&
               a.version     == b.version &&
               a.rec_len     == b.rec_len &&
               a.field_count == b.field_count;
    };

    std::string meta_err;
    auto meta = cdxmeta::read_meta(cdx_container_path, &meta_err);

    if (meta.has_value()) {
        if (!cdxmeta::matches(identity, *meta)) {
            const bool core_ok = same_core_shape(identity, meta->table);

            if (core_ok) {
                cdxmeta::MetaRecord fresh = *meta;
                fresh.table = identity;

                if (!cdxmeta::write_meta(cdx_container_path, fresh, &meta_err)) {
                    if (err) {
                        std::ostringstream oss;
                        oss.imbue(std::locale::classic());
                        oss << "openCdx: stale metadata detected but refresh failed"
                            << " [table kind=" << identity.kind
                            << ", version=" << static_cast<unsigned>(identity.version)
                            << ", reclen=" << identity.rec_len
                            << ", fields=" << identity.field_count
                            << ", hash=" << identity.schema_hash
                            << "]"
                            << " vs"
                            << " [cdx kind=" << meta->table.kind
                            << ", version=" << static_cast<unsigned>(meta->table.version)
                            << ", reclen=" << meta->table.rec_len
                            << ", fields=" << meta->table.field_count
                            << ", hash=" << meta->table.schema_hash
                            << "]"
                            << " write_meta error=" << meta_err;
                        *err = oss.str();
                    }
                    return false;
                }

                meta = cdxmeta::read_meta(cdx_container_path, &meta_err);
                if (!meta.has_value()) {
                    if (err) *err = "openCdx: refreshed metadata but could not re-read sidecar";
                    return false;
                }
            } else {
                if (err) {
                    std::ostringstream oss;
                    oss.imbue(std::locale::classic());
                    oss << "openCdx: metadata mismatch"
                        << " [table kind=" << identity.kind
                        << ", version=" << static_cast<unsigned>(identity.version)
                        << ", reclen=" << identity.rec_len
                        << ", fields=" << identity.field_count
                        << ", hash=" << identity.schema_hash
                        << "]"
                        << " vs"
                        << " [cdx kind=" << meta->table.kind
                        << ", version=" << static_cast<unsigned>(meta->table.version)
                        << ", reclen=" << meta->table.rec_len
                        << ", fields=" << meta->table.field_count
                        << ", hash=" << meta->table.schema_hash
                        << "]";
                    *err = oss.str();
                }
                return false;
            }
        }
    } else {
        cdxmeta::MetaRecord fresh{};
        fresh.table = identity;

        if (!cdxmeta::write_meta(cdx_container_path, fresh, &meta_err)) {
            if (err) *err = "openCdx: failed to write metadata: " + meta_err;
            return false;
        }
    }

    const fs::path container_path(cdx_container_path);
    const fs::path env_path = dottalk::paths::resolve_lmdb_env_for_cdx(container_path);

    if (!fs::exists(env_path) || !fs::is_directory(env_path)) {
        if (err) {
            *err = "openCdx: LMDB env missing: " + env_path.string();
        }
        return false;
    }

    auto b = std::make_unique<CdxBackend>(area_, cdx_container_path);

    if (!b->open(env_path.string())) {
        if (err) {
            *err = "openCdx: backend open() failed"
                   " [container=" + container_path.string() +
                   ", env=" + env_path.string() + "]";
        }
        return false;
    }

    backend_ = std::move(b);
    container_path_ = cdx_container_path;

    if (!tag_upper.empty()) {
        if (!setTag(tag_upper, err)) return false;
    }
    return true;
}

bool IndexManager::openCnx(const std::string& cnx_path,
                           const std::string& tag_upper,
                           std::string* err) {
    if (cnx_path.empty()) {
        if (err) *err = "openCnx: empty path";
        return false;
    }

    if (backend_ && isCnx() && container_path_ == cnx_path) {
        if (!tag_upper.empty()) {
            if (!setTag(tag_upper, err)) return false;
        }
        return true;
    }

    close();

    auto b = std::make_unique<CnxBackend>(area_, cnx_path, tag_upper);

    if (!b->open(cnx_path)) {
        if (err) *err = "openCnx: backend open failed: " + cnx_path;
        return false;
    }

    backend_ = std::move(b);
    container_path_ = cnx_path;

    if (!tag_upper.empty()) {
        if (!setTag(tag_upper, err)) return false;
    }
    return true;
}

bool IndexManager::setTag(const std::string& tag_upper, std::string* err) {
    if (!backend_) {
        if (err) *err = "setTag: no active backend";
        return false;
    }
    auto* tb = dynamic_cast<ITagBackend*>(backend_.get());
    if (!tb) {
        if (err) *err = "setTag: backend not tag-capable";
        return false;
    }
    const auto up = to_upper_copy_ascii_(tag_upper);

    // Selecting a tag that does not exist is a clean failure, not an exception
    // and not a silent success.
    //
    // This used to call tb->setTag(up) and unconditionally return true, because
    // setTag returns void. Nothing validated the name against the container, so
    // any string was accepted -- and CdxBackend::setTag then created an LMDB
    // sub-database for it on demand. capture_delete_snapshot_for_current_record
    // enumerates FIELDS, so every mutated field silently became a tag DB.
    //
    // CdxBackend::setTag now throws for an unknown tag. Converting that to false
    // here matters: with_tag_switched_ calls this OUTSIDE its own try block, so
    // an escaping exception would unwind through apply_replace_snapshot and be
    // reported by replaceFieldStored as "index update failed" on every edit of
    // an untagged field. A clean false makes capture simply skip the field,
    // which is the correct outcome -- an untagged field has no index work.
    try {
        tb->setTag(up);
    } catch (const std::exception& ex) {
        if (err) *err = ex.what();
        return false;
    } catch (...) {
        if (err) *err = "setTag: unknown failure for tag " + up;
        return false;
    }

    tag_upper_ = up;
    return true;
}

std::unique_ptr<Cursor> IndexManager::seek(const Key& key) const {
    if (!backend_) return {};
    return backend_->seek(key);
}

std::unique_ptr<Cursor> IndexManager::scan(const Key& low, const Key& high) const {
    if (!backend_) return {};
    return backend_->scan(low, high);
}

bool IndexManager::lmdbSeekUserKey(const std::string& user_key,
                                   std::uint64_t& out_recno,
                                   std::string& out_err) const {
    out_recno = 0;
    out_err.clear();
    auto* cdx = dynamic_cast<const CdxBackend*>(backend_.get());
    if (!cdx) {
        out_err = "no CDX/LMDB backend active";
        return false;
    }
    return cdx->seekRecnoUserKey(user_key, out_recno, out_err);
}

int IndexManager::activeTagFieldIndex1() const {
    const auto tag = activeTag();
    if (tag.empty()) return 0;

    try {
        const auto defs = area_.fields();
        const auto want = to_upper_copy_ascii_(tag);
        for (std::size_t i = 0; i < defs.size(); ++i) {
            if (to_upper_copy_ascii_(defs[i].name) == want) {
                return static_cast<int>(i) + 1;
            }
        }
    } catch (...) {
    }
    return 0;
}

bool IndexManager::activeTagMatchesField(int field1) const {
    if (field1 <= 0) return false;
    return activeTagFieldIndex1() == field1;
}

Key IndexManager::buildActiveTagBaseKeyFromString(const std::string& raw_value) const {
    Key out;
    const int fld = activeTagFieldIndex1();
    if (fld <= 0) return out;

    try {
        const auto defs = area_.fields();
        const auto& fdef = defs[static_cast<std::size_t>(fld - 1)];

        std::string s = raw_value;

        const bool is_char = (fdef.type == 'C' || fdef.type == 'c');
        const int keylen = static_cast<int>(fdef.length);

        if (is_char) {
            for (char& c : s) {
                c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
            }
        }

        if (keylen > 0) {
            if (static_cast<int>(s.size()) > keylen) {
                s.resize(static_cast<std::size_t>(keylen));
            } else if (static_cast<int>(s.size()) < keylen) {
                s.append(static_cast<std::size_t>(keylen - static_cast<int>(s.size())), ' ');
            }
        }

        out.reserve(s.size());
        out.insert(out.end(), s.begin(), s.end());
    } catch (...) {
        out.clear();
    }

    return out;
}

Key IndexManager::buildActiveTagBaseKeyFromCurrentRecord() const {
    const int fld = activeTagFieldIndex1();
    if (fld <= 0) return {};
    try {
        return buildActiveTagBaseKeyFromString(area_.get(fld));
    } catch (...) {
        return {};
    }
}

namespace {

static bool index_trace_enabled_()
{
    const char* env = std::getenv("DOTTALK_INDEX_TRACE");
    if (!env) return true; // diagnostic drop-in: on by default
    std::string v(env);
    std::transform(v.begin(), v.end(), v.begin(),
        [](unsigned char ch){ return static_cast<char>(std::tolower(ch)); });
    return !(v == "0" || v == "off" || v == "false" || v == "no");
}

static std::string key_preview_(const Key& key)
{
    std::string s;
    s.reserve(key.size());
    for (auto b : key) {
        const unsigned char ch = static_cast<unsigned char>(b);
        if (ch >= 32 && ch <= 126) s.push_back(static_cast<char>(ch));
        else s.push_back('.');
    }
    return s;
}

static inline std::string field_name_upper_for_1based_(xbase::DbArea& area, int field1) {
    if (field1 <= 0) return {};
    try {
        const auto defs = area.fields();
        const std::size_t idx = static_cast<std::size_t>(field1 - 1);
        if (idx >= defs.size()) return {};
        std::string s = defs[idx].name;
        for (char& ch : s) {
            ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
        }
        return s;
    } catch (...) {
        return {};
    }
}

template<typename Fn>
static bool with_tag_switched_(IndexManager& im,
                               const std::string& want_tag_upper,
                               Fn&& fn)
{
    if (!im.hasBackend()) {
        if (index_trace_enabled_()) {
            std::cout << "[INDEX TRACE] with_tag tag=" << want_tag_upper
                      << " fail=no-backend\n";
        }
        return false;
    }
    if (want_tag_upper.empty()) {
        if (index_trace_enabled_()) {
            std::cout << "[INDEX TRACE] with_tag fail=empty-tag\n";
        }
        return false;
    }

    std::string err;
    const std::string saved_tag = im.activeTag();

    if (!im.setTag(want_tag_upper, &err)) {
        if (index_trace_enabled_()) {
            std::cout << "[INDEX TRACE] setTag tag=" << want_tag_upper
                      << " fail=" << err
                      << " container=" << im.containerPath() << "\n";
        }
        return false;
    }

    bool ok = false;
    try {
        fn();
        ok = true;
    } catch (const std::exception& e) {
        ok = false;
        if (index_trace_enabled_()) {
            std::cout << "[INDEX TRACE] op tag=" << want_tag_upper
                      << " fail=" << e.what()
                      << " container=" << im.containerPath()
                      << " savedTag=" << saved_tag << "\n";
        }
    } catch (...) {
        ok = false;
        if (index_trace_enabled_()) {
            std::cout << "[INDEX TRACE] op tag=" << want_tag_upper
                      << " fail=unknown-exception"
                      << " container=" << im.containerPath()
                      << " savedTag=" << saved_tag << "\n";
        }
    }

    if (!saved_tag.empty() && saved_tag != want_tag_upper) {
        std::string restore_err;
        if (!im.setTag(saved_tag, &restore_err) && index_trace_enabled_()) {
            std::cout << "[INDEX TRACE] restoreTag tag=" << saved_tag
                      << " fail=" << restore_err
                      << " container=" << im.containerPath() << "\n";
        }
    }

    return ok;
}

} // anonymous namespace

IndexManager::DeleteSnapshot
IndexManager::capture_delete_snapshot_for_current_record() const
{
    DeleteSnapshot out;
    if (!backend_) return out;
    if (!area_.isOpen()) return out;

    try {
        // CDX/LMDB: one tag DB per field-backed tag. Capture all.
        if (dynamic_cast<const CdxBackend*>(backend_.get()) != nullptr) {
            const auto defs = area_.fields();
            auto& self = const_cast<IndexManager&>(*this);

            for (std::size_t i = 0; i < defs.size(); ++i) {
                const std::string tag = to_upper_copy_ascii_(defs[i].name);
                if (tag.empty()) continue;

                with_tag_switched_(self, tag, [&]() {
                    Key key = self.buildActiveTagBaseKeyFromCurrentRecord();
                    if (!key.empty()) {
                        out.push_back(DeleteSnapshotEntry{tag, std::move(key)});
                    }
                });
            }
            return out;
        }

        // CNX / other single-active-tag backend: snapshot only active tag.
        const std::string tag = activeTag();
        const Key key = buildActiveTagBaseKeyFromCurrentRecord();
        if (!tag.empty() && !key.empty()) {
            out.push_back(DeleteSnapshotEntry{tag, key});
        }
    } catch (...) {
        out.clear();
    }

    return out;
}

bool IndexManager::apply_delete_snapshot(const DeleteSnapshot& snap, RecNo rec)
{
    if (!backend_) return false;
    if (snap.empty()) return false;

    bool any = false;
    for (const auto& e : snap) {
        if (e.tag_upper.empty() || e.key.empty()) continue;

        const bool ok = with_tag_switched_(*this, e.tag_upper, [&]() {
            on_delete(e.key, rec);
        });

        if (ok) any = true;
    }
    return any;
}

// Emit only the tags whose key actually changed.
//
// The snapshots carry one entry per field-backed tag (see
// capture_delete_snapshot_for_current_record), so a single-field REPLACE on an
// N-tag table used to issue N deletes and N inserts -- 2N committed LMDB write
// transactions -- when at most one tag's key had moved. The old==new guard on
// on_replace() was never reachable from here, because this path calls
// on_delete()/on_append() directly rather than going through it.
//
// Diffing on the (tag, key) pair restores that guard for every caller of this
// function at once: REPLACE/CALCWRITE (via index_hooks), REPLACE_MULTI, and the
// buffered COMMIT apply all funnel here.
//
// Behavior deliberately given up: the old delete-all/insert-all was accidentally
// self-repairing, because on_append() is an upsert. A record whose index entry
// had gone missing got silently re-inserted by the next unrelated REPLACE. That
// no longer happens -- an unchanged tag is skipped, so a missing entry stays
// missing until REINDEX/REBUILD. This is a deliberate trade: paying 2N index
// writes on every record edit is an unacceptable price for an undocumented
// repair that also hid the failure it was repairing. The failure is now
// reported instead (see DbArea::replaceFieldStored).
//
// Return-value contract (load-bearing -- do not "simplify" to `any`):
// callers treat false as an index-maintenance failure and mark fields stale
// (see cmd_replace_multi.cpp). A record edit that touches no indexed field is a
// legitimate no-op, not a failure, and must report success. `any` alone cannot
// distinguish "nothing needed doing" from "everything failed", so success is
// tracked as "no attempted operation failed".
bool IndexManager::apply_replace_snapshot(const DeleteSnapshot& before,
                                          const DeleteSnapshot& after,
                                          RecNo rec)
{
    // No backend means there is no index to maintain, so the index is
    // vacuously consistent -- that is success, not failure.
    //
    // This must be true, not false. A manager is created by ensure_manager()
    // and stays in the registry for the life of the area; close() clears the
    // backend but leaves the manager attached. So an area that merely ran
    // LOCATE/FIND/SEEK once, or had SET ORDER TO issued, has an attached
    // manager with a null backend for the rest of the session. Returning false
    // there made every later REPLACE/CALCWRITE report "index update failed" on
    // a table with no index open.
    if (!backend_) return true;

    // wasStale() TRANSITION, not a bare read.
    //
    // A backend that cannot maintain incrementally does not fail: CnxBackend
    // and CdxNativeBackend upsert/erase are no-ops that set stale_ = true and
    // return normally (cnx_backend.cpp:521-533). So every loop below reports
    // ok, all_ok stays true, and the caller is told the index was maintained
    // when it was not. That silent path is the COMMON case for CNX/native CDX
    // -- the exceptional LMDB throw is the rare one.
    //
    // Reading wasStale() bare would be wrong: stale_ is also set when a load
    // FAILS (cnx_backend.cpp:396), so a table whose index never opened would
    // warn on every REPLACE forever. Only a false -> true transition ACROSS
    // this apply means "this operation left the index stale".
    const bool stale_before = backend_->wasStale();

    auto usable = [](const DeleteSnapshotEntry& e) {
        return !e.tag_upper.empty() && !e.key.empty();
    };

    auto same_entry = [](const DeleteSnapshotEntry& a,
                         const DeleteSnapshotEntry& b) {
        return a.tag_upper == b.tag_upper && a.key == b.key;
    };

    auto present_in = [&](const DeleteSnapshot& snap,
                          const DeleteSnapshotEntry& e) {
        for (const auto& other : snap) {
            if (usable(other) && same_entry(other, e)) return true;
        }
        return false;
    };

    bool all_ok = true;
    std::size_t emitted_del = 0;
    std::size_t emitted_ins = 0;
    std::size_t skipped = 0;
    std::string emitted_tags;   // trace only: which tags actually moved

    auto note_tag = [&emitted_tags](const std::string& tag, const char* op) {
        if (!emitted_tags.empty()) emitted_tags += ",";
        emitted_tags += op;
        emitted_tags += tag;
    };

    // Remove old keys that the after-image no longer carries.
    for (const auto& e : before) {
        if (!usable(e)) continue;
        if (present_in(after, e)) { ++skipped; continue; }  // unchanged tag

        ++emitted_del;
        const bool ok = with_tag_switched_(*this, e.tag_upper, [&]() {
            on_delete(e.key, rec);
        });

        if (index_trace_enabled_()) note_tag(e.tag_upper, ok ? "-" : "-FAIL:");
        if (!ok) all_ok = false;
    }

    // Insert new keys the before-image did not already carry.
    for (const auto& e : after) {
        if (!usable(e)) continue;
        if (present_in(before, e)) { ++skipped; continue; }  // already correct

        ++emitted_ins;
        const bool ok = with_tag_switched_(*this, e.tag_upper, [&]() {
            on_append(e.key, rec);
        });

        if (index_trace_enabled_()) note_tag(e.tag_upper, ok ? "+" : "+FAIL:");
        if (!ok) all_ok = false;
    }

    // Makes the diff measurable instead of inferred. Under the old delete-all/
    // insert-all this line would have read emitted_del=N emitted_ins=N skipped=0
    // for any N-tag table; the win is visible as skipped rising while emitted
    // stays at the number of tags whose key actually moved.
    // Did this apply leave the index stale? Only counts if the backend was NOT
    // already stale on entry -- see the note at stale_before.
    //
    // Reported through the SAME false return the exceptional path uses, so
    // replaceFieldStored sets err and REPLACE/CALCWRITE warn
    // "record written, but index update failed...; REINDEX/REBUILD needed."
    // That wording is accurate here rather than merely reused: the index was
    // not updated, and REINDEX/REBUILD is exactly the remedy for a backend
    // that only maintains by rebuilding.
    //
    // Note on volume: this fires on EVERY replace against a CNX or native-CDX
    // order, because every one of them genuinely leaves the index stale. That
    // is honest but repetitive. If it proves too noisy in practice the fix is
    // to throttle the MESSAGE (once per area per order), not to re-silence the
    // condition -- the silence is what this change exists to end.
    const bool left_stale = (!stale_before && backend_->wasStale());

    if (index_trace_enabled_()) {
        std::cout << "[INDEX TRACE] apply_replace rec=" << rec
                  << " before=" << before.size()
                  << " after=" << after.size()
                  << " emitted_del=" << emitted_del
                  << " emitted_ins=" << emitted_ins
                  << " skipped=" << skipped
                  << " ok=" << (all_ok ? "yes" : "no")
                  << " staleBefore=" << (stale_before ? "yes" : "no")
                  << " leftStale=" << (left_stale ? "yes" : "no")
                  << " tags=[" << emitted_tags << "]"
                  << "\n";
    }

    return all_ok && !left_stale;
}

bool IndexManager::apply_insert_snapshot(const DeleteSnapshot& snap,
                                         RecNo rec)
{
    if (!backend_) {
        if (index_trace_enabled_()) {
            std::cout << "[INDEX TRACE] apply_insert rec=" << rec
                      << " fail=no-backend\n";
        }
        return false;
    }
    if (snap.empty()) {
        if (index_trace_enabled_()) {
            std::cout << "[INDEX TRACE] apply_insert rec=" << rec
                      << " fail=empty-snapshot container=" << container_path_ << "\n";
        }
        return false;
    }

    bool any = false;

    if (index_trace_enabled_()) {
        std::cout << "[INDEX TRACE] apply_insert rec=" << rec
                  << " entries=" << snap.size()
                  << " container=" << container_path_
                  << " activeTag=" << activeTag() << "\n";
    }

    for (const auto& e : snap) {
        if (e.tag_upper.empty() || e.key.empty()) {
            if (index_trace_enabled_()) {
                std::cout << "[INDEX TRACE] insert skip tag=" << e.tag_upper
                          << " reason=empty-tag-or-key\n";
            }
            continue;
        }

        const bool ok = with_tag_switched_(*this, e.tag_upper, [&]() {
            on_append(e.key, rec);
        });

        if (index_trace_enabled_()) {
            std::cout << "[INDEX TRACE] insert tag=" << e.tag_upper
                      << " rec=" << rec
                      << " key_len=" << e.key.size()
                      << " key=\"" << key_preview_(e.key) << "\""
                      << " result=" << (ok ? "true" : "false")
                      << " activeTagNow=" << activeTag() << "\n";
        }

        if (ok) any = true;
    }

    if (index_trace_enabled_()) {
        std::cout << "[INDEX TRACE] apply_insert result="
                  << (any ? "true" : "false")
                  << " rec=" << rec << "\n";
    }

    return any;
}

// ---- Bulk write batching passthrough (CDX only) --------------------------
bool IndexManager::beginBulkWrite(std::string* err) {
    if (auto* cdx = dynamic_cast<CdxBackend*>(backend_.get())) {
        return cdx->beginBulk(err);
    }
    if (err) *err = "bulk write not supported by active backend";
    return false;
}

bool IndexManager::commitBulkWrite(std::string* err) {
    if (auto* cdx = dynamic_cast<CdxBackend*>(backend_.get())) {
        return cdx->commitBulk(err);
    }
    return true; // nothing to commit for non-CDX backends
}

void IndexManager::abortBulkWrite() noexcept {
    if (auto* cdx = dynamic_cast<CdxBackend*>(backend_.get())) {
        cdx->abortBulk();
    }
}

bool IndexManager::replace_active_field_value(int field1,
                                              const std::string& old_value,
                                              const std::string& new_value,
                                              RecNo rec) {
    if (!backend_) return false;

    const std::string target_tag = field_name_upper_for_1based_(area_, field1);
    if (target_tag.empty()) return false;

    return with_tag_switched_(*this, target_tag, [&]() {
        const Key old_key = buildActiveTagBaseKeyFromString(old_value);
        const Key new_key = buildActiveTagBaseKeyFromString(new_value);
        on_replace(old_key, new_key, rec);
    });
}

bool IndexManager::append_active_field_value(int field1,
                                             const std::string& value,
                                             RecNo rec) {
    if (!backend_) return false;

    const std::string target_tag = field_name_upper_for_1based_(area_, field1);
    if (target_tag.empty()) return false;

    return with_tag_switched_(*this, target_tag, [&]() {
        const Key key = buildActiveTagBaseKeyFromString(value);
        on_append(key, rec);
    });
}

bool IndexManager::delete_active_field_value(int field1,
                                             const std::string& value,
                                             RecNo rec) {
    if (!backend_) return false;

    const std::string target_tag = field_name_upper_for_1based_(area_, field1);
    if (target_tag.empty()) return false;

    return with_tag_switched_(*this, target_tag, [&]() {
        const Key key = buildActiveTagBaseKeyFromString(value);
        on_delete(key, rec);
    });
}

std::optional<IndexManager::ActiveState> IndexManager::active() const {
    if (!backend_) return std::nullopt;
    ActiveState st;
    st.spec_.cdx = container_path_;
    st.spec_.tag = activeTag();
    return st;
}

bool IndexManager::set_active(const std::string& tagName) {
    std::string err;
    if (!backend_) {
        if (!load_for_table(area_.filename())) {
            return false;
        }
    }
    return setTag(tagName, &err);
}

std::vector<std::string> IndexManager::listTags() const {
    if (!backend_) return {};
    if (auto* cnx = dynamic_cast<const CnxBackend*>(backend_.get())) {
        return cnx->listTags();
    }
    if (dynamic_cast<const CdxBackend*>(backend_.get()) != nullptr && !container_path_.empty()) {
        std::vector<std::string> out;
        try {
            const auto defs = area_.fields();
            out.reserve(defs.size());
            for (const auto& def : defs) {
                auto tag = to_upper_copy_ascii_(def.name);
                if (!tag.empty()) {
                    out.push_back(std::move(tag));
                }
            }
        } catch (...) {
            out.clear();
        }
        if (!out.empty()) return out;
    }
    std::vector<std::string> out;
    const auto t = activeTag();
    if (!t.empty()) out.push_back(t);
    return out;
}

static inline fs::path candidate_in_dir_(const fs::path& dir,
                                         const std::string& stem_upper,
                                         const std::string& ext_lower) {
    fs::path p = dir / stem_upper;
    p += ext_lower;
    return p;
}

bool IndexManager::load_for_table(const std::string& path_or_dbf) {
    std::string err;

    if (path_or_dbf.empty()) return false;

    fs::path p(path_or_dbf);
    const auto ext = to_upper_copy_ascii_(p.extension().string());

    if (ext == ".CDX") {
        return openCdx(p.string(), {}, &err);
    }
    if (ext == ".CNX") {
        return openCnx(p.string(), {}, &err);
    }

    if (ext == ".DBF" || ext.empty()) {
        fs::path dbf = p;
        if (ext.empty()) {
            dbf = fs::path(area_.dbfDir()) / p;
            dbf += ".dbf";
        }

        const auto stem_upper = to_upper_copy_ascii_(dbf.stem().string());

        std::vector<fs::path> cand_cdx;
        std::vector<fs::path> cand_cnx;

        if (!dbf.parent_path().empty()) {
            cand_cdx.push_back(candidate_in_dir_(dbf.parent_path(), stem_upper, ".cdx"));
            cand_cdx.push_back(candidate_in_dir_(dbf.parent_path() / "indexes", stem_upper, ".cdx"));
            cand_cnx.push_back(candidate_in_dir_(dbf.parent_path(), stem_upper, ".cnx"));
            cand_cnx.push_back(candidate_in_dir_(dbf.parent_path() / "indexes", stem_upper, ".cnx"));
        }
        cand_cdx.push_back(candidate_in_dir_(fs::path("indexes"), stem_upper, ".cdx"));
        cand_cnx.push_back(candidate_in_dir_(fs::path("indexes"), stem_upper, ".cnx"));

        if (!area_.dbfDir().empty()) {
            const auto base_upper = to_upper_copy_ascii_(area_.dbfBasename());
            cand_cdx.push_back(candidate_in_dir_(fs::path(area_.dbfDir()), base_upper, ".cdx"));
            cand_cdx.push_back(candidate_in_dir_(fs::path(area_.dbfDir()) / "indexes", base_upper, ".cdx"));
            cand_cnx.push_back(candidate_in_dir_(fs::path(area_.dbfDir()), base_upper, ".cnx"));
            cand_cnx.push_back(candidate_in_dir_(fs::path(area_.dbfDir()) / "indexes", base_upper, ".cnx"));
        }

        for (const auto& c : cand_cdx) {
            if (fs::exists(c)) return openCdx(c.string(), {}, &err);
        }
        for (const auto& c : cand_cnx) {
            if (fs::exists(c)) return openCnx(c.string(), {}, &err);
        }

        if (!cand_cdx.empty()) return openCdx(cand_cdx.front().string(), {}, &err);
        return false;
    }

    return openCdx(p.string(), {}, &err);
}

bool IndexManager::load_json(const std::string& inx_path) {
    std::string err;
    if (inx_path.empty()) return false;

    fs::path p(inx_path);
    const auto doc = read_all_text_(p);
    if (doc.empty()) {
        return false;
    }

    std::string cdx = json_string_value_(doc, "cdx");
    std::string tag = json_string_value_(doc, "tag");

    if (cdx.empty()) {
        cdx = (p.parent_path() / p.stem()).string() + ".cdx";
    }
    if (tag.empty()) {
        tag = p.stem().string();
    }

    if (ends_with_icase_(cdx, ".cnx")) {
        return openCnx(cdx, to_upper_copy_ascii_(tag), &err);
    }

    return openCdx(cdx, to_upper_copy_ascii_(tag), &err);
}

} // namespace xindex
