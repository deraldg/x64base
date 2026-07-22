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
    // beyond UINT32_MAX. Reporting only — not intense classic-32 support.
    virtual std::uint64_t maxRecordNumber() const { return UINT64_MAX; }
    bool supportsWideRecords() const { return maxRecordNumber() > UINT32_MAX; }
};

} // namespace xindex