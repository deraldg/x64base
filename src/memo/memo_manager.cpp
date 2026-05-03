#include "memo/memo_manager.hpp"

#include <fstream>
#include <string>
#include <vector>

namespace dottalk::memo {
namespace {

bool payload_is_text(const MemoPayload& payload)
{
    return is_text_content_type(payload.content_type);
}

std::string payload_to_string(const MemoPayload& payload)
{
    if (!payload.data || payload.size == 0) return std::string{};
    return std::string(payload.data, payload.data + payload.size);
}

const char* payload_kind_content_type(MemoPayloadKind kind) noexcept
{
    switch (kind) {
        case MemoPayloadKind::TextUtf8: return "text/plain";
        case MemoPayloadKind::Binary:   return "application/octet-stream";
        case MemoPayloadKind::Unknown:
        default:                        return "application/octet-stream";
    }
}

} // namespace

// -----------------------------------------------------------------------------
// Runtime bridge constructor.
// The bridge remains passive; it must not inspect records or own payload logic.
// -----------------------------------------------------------------------------
MemoManager::MemoManager(xbase::DbArea& area, MemoContext& ctx)
    : area_(&area),
      ctx_(&ctx),
      backend_(nullptr)
{
}

// -----------------------------------------------------------------------------
// Service wrapper over the existing DTX backend.
// -----------------------------------------------------------------------------
MemoManager::MemoManager(IMemoBackend& backend)
    : area_(nullptr),
      ctx_(nullptr),
      backend_(&backend)
{
}

bool MemoManager::open_auto(const std::string& opened_path,
                            bool has_memo_fields,
                            std::string& err)
{
    (void)opened_path;
    (void)has_memo_fields;

    // Intentional no-op.  The live open/close policy remains in memo_auto.cpp.
    err.clear();
    return true;
}

void MemoManager::close() noexcept
{
    // Intentional no-op.  The owning memo_auto layer closes the backend.
    backend_ = nullptr;
}

bool MemoManager::flush(std::string* err)
{
    if (!backend_) {
        if (err) err->clear();
        return true;
    }

    MemoOpResult r = backend_->flush();
    if (!r.ok && err) *err = r.error;
    else if (err) err->clear();
    return r.ok;
}

IMemoBackend* MemoManager::backend() noexcept
{
    return backend_;
}

const IMemoBackend* MemoManager::backend() const noexcept
{
    return backend_;
}

MemoRef MemoManager::create_object(const MemoPayload& payload,
                                   std::string* error)
{
    if (!backend_) {
        if (error) *error = "memo backend is not attached";
        return MemoRef{};
    }

    if (!payload_is_text(payload)) {
        if (error) *error = "binary/blob object writes are not enabled on the DTX text path yet";
        return MemoRef{};
    }

    MemoPutResult r = backend_->put_text(payload_to_string(payload));
    if (!r.ok && error) *error = r.error;
    else if (error) error->clear();
    return r.ref;
}

MemoRef MemoManager::replace_object(const MemoRef& ref,
                                    const MemoPayload& payload,
                                    std::string* error)
{
    if (!backend_) {
        if (error) *error = "memo backend is not attached";
        return MemoRef{};
    }

    if (!payload_is_text(payload)) {
        if (error) *error = "binary/blob object writes are not enabled on the DTX text path yet";
        return MemoRef{};
    }

    MemoPutResult r = backend_->update_text(ref, payload_to_string(payload));
    if (!r.ok && error) *error = r.error;
    else if (error) error->clear();
    return r.ref;
}

bool MemoManager::get_info(const MemoRef& ref,
                           MemoObject& out,
                           std::string* error) const
{
    out = MemoObject{};
    out.ref = ref;

    if (!backend_) {
        if (error) *error = "memo backend is not attached";
        return false;
    }

    if (backend_->is_null_ref(ref)) {
        out.content_type = "application/octet-stream";
        out.object_class = classify_content_type(out.content_type);
        out.size_bytes = 0;
        if (error) error->clear();
        return true;
    }

    if (!backend_->validate_ref(ref)) {
        if (error) *error = "invalid memo reference";
        return false;
    }

    MemoStat st = backend_->stat(ref);
    if (!st.exists) {
        if (error) *error = "memo object not found";
        return false;
    }

    out.size_bytes = st.logical_bytes;
    out.content_type = payload_kind_content_type(st.kind);
    out.encoding = (st.kind == MemoPayloadKind::TextUtf8) ? "UTF-8" : std::string{};
    out.object_class = classify_content_type(out.content_type);

    if (error) error->clear();
    return true;
}

bool MemoManager::read_all(const MemoRef& ref,
                           std::vector<char>& out,
                           std::string* error) const
{
    out.clear();

    if (!backend_) {
        if (error) *error = "memo backend is not attached";
        return false;
    }

    if (backend_->is_null_ref(ref)) {
        if (error) error->clear();
        return true;
    }

    MemoGetResult r = backend_->get_text(ref);
    if (!r.ok) {
        if (error) *error = r.error;
        return false;
    }

    if (!r.bytes.empty()) {
        out.reserve(r.bytes.size());
        for (std::byte b : r.bytes) {
            out.push_back(static_cast<char>(b));
        }
    } else {
        out.assign(r.text.begin(), r.text.end());
    }

    if (error) error->clear();
    return true;
}

bool MemoManager::export_to_file(const MemoRef& ref,
                                 const std::string& path,
                                 std::string* error) const
{
    std::vector<char> bytes;
    if (!read_all(ref, bytes, error)) return false;

    std::ofstream os(path, std::ios::binary | std::ios::trunc);
    if (!os) {
        if (error) *error = "could not create export file";
        return false;
    }

    if (!bytes.empty()) {
        os.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
    }

    if (!os) {
        if (error) *error = "could not write export file";
        return false;
    }

    if (error) error->clear();
    return true;
}

MemoVerifyResult MemoManager::verify_object(const MemoRef& ref) const
{
    if (!backend_) {
        return MemoVerifyResult{false, "memo backend is not attached"};
    }

    if (backend_->is_null_ref(ref)) {
        return MemoVerifyResult{true, "null memo reference"};
    }

    if (!backend_->validate_ref(ref)) {
        return MemoVerifyResult{false, "invalid memo reference"};
    }

    const MemoStat st = backend_->stat(ref);
    if (!st.exists) {
        return MemoVerifyResult{false, "memo object not found"};
    }

    return MemoVerifyResult{true, "OK"};
}

} // namespace dottalk::memo
