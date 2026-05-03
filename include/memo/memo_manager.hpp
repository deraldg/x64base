#pragma once

#include "memo/memo_backend.hpp"
#include "memo/memo_context.hpp"
#include "memo/memo_object.hpp"
#include "memo/memo_store.hpp" // MemoVerifyResult compatibility type only.

#include <cstdint>
#include <string>
#include <vector>

namespace xbase { class DbArea; }

namespace dottalk::memo {

struct MemoPayload {
    const char* data{nullptr};
    std::uint64_t size{0};
    std::string content_type{"text/plain"};
    std::string encoding{"UTF-8"};
};

/*
    MemoManager

    Service layer over the canonical live memo backend.

    Important architecture rule:
      - This class does not introduce a second x64 storage backend.
      - The live persistence path remains IMemoBackend / MemoStore / DTX.
      - MemoManager supplies OO-style object inspection and safe operations over
        that backend, similar to how CDX abstracts LMDB.
*/
class MemoManager {
public:
    // Existing runtime bridge constructor.
    MemoManager(xbase::DbArea& area, MemoContext& ctx);

    // Non-owning service wrapper around the existing open backend.
    explicit MemoManager(IMemoBackend& backend);

    ~MemoManager() = default;

    MemoManager(const MemoManager&) = delete;
    MemoManager& operator=(const MemoManager&) = delete;

    MemoManager(MemoManager&&) = delete;
    MemoManager& operator=(MemoManager&&) = delete;

    // Existing runtime lifecycle API.
    bool open_auto(const std::string& opened_path,
                   bool has_memo_fields,
                   std::string& err);

    void close() noexcept;
    bool flush(std::string* err = nullptr);

    IMemoBackend* backend() noexcept;
    const IMemoBackend* backend() const noexcept;

    // Compatibility names during transition.
    IMemoBackend* store() noexcept { return backend(); }
    const IMemoBackend* store() const noexcept { return backend(); }

    // Object-style API over DTX backend. Text is the only write path enabled now.
    MemoRef create_object(const MemoPayload& payload, std::string* error = nullptr);

    MemoRef replace_object(const MemoRef& ref,
                           const MemoPayload& payload,
                           std::string* error = nullptr);

    bool get_info(const MemoRef& ref,
                  MemoObject& out,
                  std::string* error = nullptr) const;

    bool read_all(const MemoRef& ref,
                  std::vector<char>& out,
                  std::string* error = nullptr) const;

    bool export_to_file(const MemoRef& ref,
                        const std::string& path,
                        std::string* error = nullptr) const;

    MemoVerifyResult verify_object(const MemoRef& ref) const;

private:
    xbase::DbArea* area_{nullptr};
    MemoContext* ctx_{nullptr};

    // Non-owning. Ownership remains with memo_auto / work-area wiring.
    IMemoBackend* backend_{nullptr};
};

} // namespace dottalk::memo
