// @dottalk.file v1
// subsystem: xindex
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
#include "xindex/key_common.hpp"

#include <cstdint>
#include <memory>
#include <string>

namespace xindex {

// Simple cursor interface returning a stream of (Key, RecNo)
struct Cursor {
    virtual ~Cursor() = default;

    // Position to the first record in the cursor's range.
    // Returns false if empty. On true, fills out parameters.
    virtual bool first(Key& outKey, RecNo& outRec) = 0;

    // Advance forward; same return contract as first()
    virtual bool next(Key& outKey, RecNo& outRec) = 0;

    // Position to the last record in the cursor's range.
    // Returns false if empty. On true, fills out parameters.
    virtual bool last(Key& outKey, RecNo& outRec) = 0;

    // Advance backward; same return contract as first()
    virtual bool prev(Key& outKey, RecNo& outRec) = 0;
};

struct IIndexBackend {
    virtual ~IIndexBackend() = default;

    virtual bool open(const std::string& path) = 0;
    virtual void close() = 0;

    virtual void setFingerprint(std::uint32_t /*fp*/) = 0;
    virtual bool wasStale() const = 0;

    virtual void rebuild() = 0;

    virtual void upsert(const Key& key, RecNo rec) = 0;
    virtual void erase(const Key& key, RecNo rec) = 0;

    virtual std::unique_ptr<Cursor> seek(const Key& key) const = 0;
    virtual std::unique_ptr<Cursor> scan(const Key& low, const Key& high) const = 0;

    // RECNO64 capability report: the largest record number this backend can store
    // and return without truncation. 64-bit backends (CDX/LMDB, B+tree) support the
    // full range (default). Classic 32-bit on-disk formats (CNX, legacy .inx)
    // override this so an x64 table bound to an insufficient backend can be
    // rejected with a clear error instead of silently truncating record numbers
    // beyond UINT32_MAX. Reporting only -- not intense classic-32 support.
    virtual std::uint64_t maxRecordNumber() const { return UINT64_MAX; }
    bool supportsWideRecords() const { return maxRecordNumber() > UINT32_MAX; }

    // MAINTENANCE capability report -- the second capability axis of the open
    // index API, and a sibling of maxRecordNumber() above.
    //
    // Answers "can this backend keep itself CORRECT across a single record
    // mutation, through upsert/erase, without a full rebuild?" It does NOT
    // answer "which backend is this", and callers must not infer it from the
    // concrete type. Deciding maintenance policy by asking `isCdx()` or
    // `isCnx()` is what this replaces: that phrasing has to be revisited every
    // time a backend is added or gains a capability, and it was already wrong
    // once -- CNX gained working upsert/erase (XIDX-TXN-02 M1) while the commit
    // seam still classed it as rebuild-only.
    //
    // THE DEFAULT IS FALSE, AND THAT IS DELIBERATE. False is the safe answer:
    // a backend that does not override this gets a full rebuild, which is slow
    // but correct. If the default were true, forgetting to override would leave
    // a silently stale index that reports success -- the exact failure shape
    // this codebase treats as its most common defect. Cost of the safe default
    // is wasted work; cost of the unsafe default is wrong data.
    //
    // Returning true is a CLAIM, and it carries obligations:
    //   - upsert() and erase() must actually maintain, not set a stale flag
    //     and return normally.
    //   - the maintained ordering must be identical to the ordering a
    //     rebuild() would produce, or a REBUILD will silently change results.
    //   - wasStale() must report honestly when maintenance could not happen.
    // Prove those with a runtime regression before flipping this to true.
    virtual bool maintainsIncrementally() const { return false; }

    // DURABILITY. Write any maintained-but-unpersisted state to the container.
    //
    // A THIRD, INDEPENDENT AXIS. maintainsIncrementally() says the index stays
    // correct across a mutation; it says nothing about whether that correctness
    // survives a close. CNX proves the two come apart: it maintained correctly
    // from XIDX-TXN-02 M1 while its permutation lived only in memory, so the
    // ordering was right all session and reverted on the next load. Callers
    // asking "is this durable" must ask here, not there.
    //
    // DEFAULT IS NO-OP SUCCESS, and that asymmetry with maintainsIncrementally()
    // is deliberate. There, silence means "cannot maintain" and the caller must
    // do the work itself, so false is the safe answer. Here, a backend with
    // nothing to persist -- one that writes through on every mutation, like
    // CDX/LMDB -- has already met the obligation, and returning false would
    // report a failure that did not happen. NOTHING TO SAVE IS SUCCESS. This is
    // the same lesson beginBulkWrite() had to be taught the hard way: refusing
    // an operation a backend does not need is not safety, it is a false alarm
    // that denies the caller a path it was entitled to.
    //
    // Implementations must be idempotent: saving twice with no intervening
    // mutation must be harmless, because close-time and commit-time saves can
    // both fire for the same edit.
    //
    // On false, *err (when non-null) carries a reportable reason. The caller
    // should treat the index as needing a rebuild.
    virtual bool save(std::string* err = nullptr) { (void)err; return true; }
};

} // namespace xindex