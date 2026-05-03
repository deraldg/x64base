#include "memo/memo_store.hpp"

#include <cstdio>
#include <filesystem>
#include <fstream>
#include <sstream>

namespace dottalk::memo {
namespace {

class X64MemoStore final : public IMemoStore {
public:
    explicit X64MemoStore(std::string directory)
        : directory_(std::move(directory))
    {
    }

    std::string store_id() const override { return "x64"; }

    MemoRef create(const MemoPayload& payload, std::string* error) override
    {
        try {
            std::filesystem::create_directories(directory_);
            const std::uint64_t id = next_id();
            if (!write_payload(id, payload, error)) return MemoRef{};
            return make_x64_ref(id);
        } catch (const std::exception& e) {
            if (error) *error = e.what();
            return MemoRef{};
        }
    }

    MemoRef replace(const MemoRef& old_ref, const MemoPayload& payload, std::string* error) override
    {
        (void)old_ref;
        // Replacement creates a new object reference. Old-object cleanup belongs
        // to PACK MEMO / GC so table mutation remains safe and recoverable.
        return create(payload, error);
    }

    bool read_all(const MemoRef& ref, std::vector<char>& out, std::string* error) override
    {
        out.clear();
        std::ifstream is(data_path(ref.object_id), std::ios::binary);
        if (!is) {
            if (error) *error = "memo object not found";
            return false;
        }
        is.seekg(0, std::ios::end);
        const std::streamoff n = is.tellg();
        is.seekg(0, std::ios::beg);
        if (n > 0) {
            out.resize(static_cast<std::size_t>(n));
            is.read(out.data(), n);
        }
        return static_cast<bool>(is) || is.eof();
    }

    bool info(const MemoRef& ref, MemoObject& out, std::string* error) const override
    {
        out = MemoObject{};
        out.ref = ref;
        if (!exists(ref)) {
            if (error) *error = "memo object not found";
            return false;
        }

        out.size_bytes = static_cast<std::uint64_t>(std::filesystem::file_size(data_path(ref.object_id)));
        read_meta(ref.object_id, out.content_type, out.encoding);
        out.content_type = normalize_content_type(out.content_type);
        out.object_class = classify_content_type(out.content_type);
        return true;
    }

    bool exists(const MemoRef& ref) const override
    {
        return ref.store_id.empty() || ref.store_id == "x64"
            ? std::filesystem::exists(data_path(ref.object_id))
            : false;
    }

    bool remove(const MemoRef& ref, std::string* error) override
    {
        try {
            std::filesystem::remove(data_path(ref.object_id));
            std::filesystem::remove(meta_path(ref.object_id));
            return true;
        } catch (const std::exception& e) {
            if (error) *error = e.what();
            return false;
        }
    }

    MemoVerifyResult verify(const MemoRef& ref) const override
    {
        if (!exists(ref)) return MemoVerifyResult{false, "missing memo object"};

        MemoObject obj;
        std::string error;
        if (!info(ref, obj, &error)) return MemoVerifyResult{false, error};

        if (obj.content_type == "application/pdf") {
            std::ifstream is(data_path(ref.object_id), std::ios::binary);
            char sig[4]{};
            is.read(sig, 4);
            if (!(sig[0] == '%' && sig[1] == 'P' && sig[2] == 'D' && sig[3] == 'F')) {
                return MemoVerifyResult{false, "PDF object does not start with %PDF"};
            }
        }

        return MemoVerifyResult{true, "OK"};
    }

private:
    std::string directory_;

    std::filesystem::path data_path(std::uint64_t id) const
    {
        return std::filesystem::path(directory_) / (std::to_string(id) + ".lob");
    }

    std::filesystem::path meta_path(std::uint64_t id) const
    {
        return std::filesystem::path(directory_) / (std::to_string(id) + ".meta");
    }

    std::uint64_t next_id() const
    {
        std::uint64_t max_id = 0;
        if (std::filesystem::exists(directory_)) {
            for (const auto& e : std::filesystem::directory_iterator(directory_)) {
                if (!e.is_regular_file() || e.path().extension() != ".lob") continue;
                try {
                    const std::uint64_t id = static_cast<std::uint64_t>(std::stoull(e.path().stem().string()));
                    if (id > max_id) max_id = id;
                } catch (...) {
                }
            }
        }
        return max_id + 1u;
    }

    bool write_payload(std::uint64_t id, const MemoPayload& payload, std::string* error)
    {
        std::ofstream os(data_path(id), std::ios::binary | std::ios::trunc);
        if (!os) {
            if (error) *error = "could not create memo payload";
            return false;
        }
        if (payload.data && payload.size > 0) {
            os.write(payload.data, static_cast<std::streamsize>(payload.size));
        }
        if (!os) {
            if (error) *error = "could not write memo payload";
            return false;
        }

        std::ofstream ms(meta_path(id), std::ios::binary | std::ios::trunc);
        if (ms) {
            ms << "content_type=" << normalize_content_type(payload.content_type) << "\n";
            ms << "encoding=" << payload.encoding << "\n";
        }
        return true;
    }

    void read_meta(std::uint64_t id, std::string& content_type, std::string& encoding) const
    {
        content_type = "application/octet-stream";
        encoding.clear();

        std::ifstream is(meta_path(id), std::ios::binary);
        std::string line;
        while (std::getline(is, line)) {
            const std::size_t eq = line.find('=');
            if (eq == std::string::npos) continue;
            const std::string key = line.substr(0, eq);
            const std::string value = line.substr(eq + 1);
            if (key == "content_type") content_type = value;
            else if (key == "encoding") encoding = value;
        }
    }
};

} // namespace

std::shared_ptr<IMemoStore> make_x64_memo_store(const std::string& directory)
{
    return std::make_shared<X64MemoStore>(directory);
}

} // namespace dottalk::memo
