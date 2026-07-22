// xbase::ramfs — in-process RAM filesystem (AIF-043 in-memory tables, drop V1)
//
// Path-keyed byte files served from process memory. See include/xbase/ramfs.hpp
// for the model. This TU provides:
//   * RamFile          : a growable byte buffer (the file's bytes)
//   * ramfilebuf       : a random-access std::streambuf over a shared RamFile
//   * ramstream        : a std::iostream owning a ramfilebuf
//   * a process-global registry of mounted roots + path -> RamFile
//
// Design notes:
//   * Single shared cursor for get and put. The DBF/CDX I/O path always seeks
//     before every read/write (verified in the M1 assembly), so one cursor is
//     safe and matches how a file position behaves.
//   * Writes past end grow the buffer, zero-filling any gap — identical to
//     seeking past EOF and writing on a real file.
//   * On Windows, path keys are lowercased and backslash-normalized so
//     case/separator variants of the same path resolve to one RamFile.

#include "xbase/ramfs.hpp"

#include <algorithm>
#include <cctype>
#include <cstring>
#include <filesystem>
#include <streambuf>
#include <unordered_map>

namespace xbase::ramfs {
namespace {

// ---- the bytes of one RAM file ------------------------------------------------
struct RamFile {
    std::vector<char> data;   // logical size == data.size()
};

// ---- path normalization (keying) ---------------------------------------------
std::string norm(const std::string& p)
{
    std::string s = std::filesystem::path(p).lexically_normal().string();
#if defined(_WIN32)
    std::replace(s.begin(), s.end(), '/', '\\');
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
#endif
    while (s.size() > 1 && (s.back() == '\\' || s.back() == '/')) s.pop_back();
    return s;
}

// Is `path` equal to `root` or nested under it (with a real separator between)?
bool under(const std::string& path, const std::string& root)
{
    if (path.size() < root.size()) return false;
    if (path.compare(0, root.size(), root) != 0) return false;
    if (path.size() == root.size()) return true;
    const char sep = path[root.size()];
    return sep == '\\' || sep == '/';
}

// ---- process-global registry --------------------------------------------------
struct Registry {
    std::vector<std::string> roots;                                   // normalized
    std::unordered_map<std::string, std::shared_ptr<RamFile>> files;  // key = norm(path)
};

Registry& reg()
{
    static Registry r;
    return r;
}

// ---- random-access memory streambuf over a shared RamFile ---------------------
class ramfilebuf final : public std::streambuf {
public:
    explicit ramfilebuf(std::shared_ptr<RamFile> f) : f_(std::move(f)) {}

protected:
    std::streamsize xsgetn(char* s, std::streamsize n) override
    {
        const std::streamoff avail =
            static_cast<std::streamoff>(f_->data.size()) - pos_;
        if (avail <= 0 || n <= 0) return 0;
        const std::streamsize k =
            std::min<std::streamsize>(n, static_cast<std::streamsize>(avail));
        std::memcpy(s, f_->data.data() + pos_, static_cast<std::size_t>(k));
        pos_ += k;
        return k;
    }

    int underflow() override
    {
        if (pos_ >= static_cast<std::streamoff>(f_->data.size()))
            return traits_type::eof();
        return traits_type::to_int_type(f_->data[static_cast<std::size_t>(pos_)]);
    }

    int uflow() override
    {
        if (pos_ >= static_cast<std::streamoff>(f_->data.size()))
            return traits_type::eof();
        return traits_type::to_int_type(f_->data[static_cast<std::size_t>(pos_++)]);
    }

    std::streamsize xsputn(const char* s, std::streamsize n) override
    {
        if (n <= 0) return 0;
        ensure(pos_ + n);
        std::memcpy(f_->data.data() + pos_, s, static_cast<std::size_t>(n));
        pos_ += n;
        return n;
    }

    int overflow(int c) override
    {
        if (traits_type::eq_int_type(c, traits_type::eof()))
            return traits_type::not_eof(c);
        ensure(pos_ + 1);
        f_->data[static_cast<std::size_t>(pos_++)] = traits_type::to_char_type(c);
        return c;
    }

    pos_type seekoff(off_type off, std::ios_base::seekdir dir,
                     std::ios_base::openmode /*which*/) override
    {
        std::streamoff base =
            (dir == std::ios_base::beg) ? 0
          : (dir == std::ios_base::cur) ? pos_
          :                               static_cast<std::streamoff>(f_->data.size());
        const std::streamoff np = base + off;
        if (np < 0) return pos_type(off_type(-1));
        pos_ = np;
        return pos_type(pos_);
    }

    pos_type seekpos(pos_type sp, std::ios_base::openmode /*which*/) override
    {
        const std::streamoff np = static_cast<std::streamoff>(sp);
        if (np < 0) return pos_type(off_type(-1));
        pos_ = np;
        return pos_type(pos_);
    }

private:
    void ensure(std::streamoff need)
    {
        if (static_cast<std::streamoff>(f_->data.size()) < need)
            f_->data.resize(static_cast<std::size_t>(need), '\0');  // zero-fill gap
    }

    std::shared_ptr<RamFile> f_;
    std::streamoff           pos_ = 0;
};

// ---- iostream owning a ramfilebuf ---------------------------------------------
class ramstream final : public std::iostream {
public:
    explicit ramstream(std::shared_ptr<RamFile> f)
        : std::iostream(nullptr), buf_(std::move(f))
    {
        this->rdbuf(&buf_);
    }

private:
    ramfilebuf buf_;
};

} // namespace

// ============================ public API ======================================

void mount(const std::string& abs_root)
{
    const std::string r = norm(abs_root);
    auto& roots = reg().roots;
    if (std::find(roots.begin(), roots.end(), r) == roots.end())
        roots.push_back(r);
}

void unmount(const std::string& abs_root)
{
    const std::string r = norm(abs_root);
    auto& roots = reg().roots;
    roots.erase(std::remove(roots.begin(), roots.end(), r), roots.end());
}

bool mounted(const std::string& abs_root)
{
    const std::string r = norm(abs_root);
    auto& roots = reg().roots;
    return std::find(roots.begin(), roots.end(), r) != roots.end();
}

bool is_virtual(const std::string& abs_path)
{
    const std::string p = norm(abs_path);
    for (const auto& r : reg().roots)
        if (under(p, r)) return true;
    return false;
}

bool exists(const std::string& abs_path)
{
    return reg().files.find(norm(abs_path)) != reg().files.end();
}

std::uint64_t size(const std::string& abs_path)
{
    auto it = reg().files.find(norm(abs_path));
    return it == reg().files.end() ? 0
                                   : static_cast<std::uint64_t>(it->second->data.size());
}

bool erase(const std::string& abs_path)
{
    return reg().files.erase(norm(abs_path)) != 0;
}

std::vector<std::string> list(const std::string& abs_root)
{
    const std::string r = norm(abs_root);
    std::vector<std::string> out;
    for (const auto& kv : reg().files)
        if (under(kv.first, r)) out.push_back(kv.first);
    std::sort(out.begin(), out.end());
    return out;
}

void clear()
{
    reg().files.clear();
    reg().roots.clear();
}

std::uint64_t used_bytes()
{
    std::uint64_t total = 0;
    for (const auto& kv : reg().files)
        total += static_cast<std::uint64_t>(kv.second->data.size());
    return total;
}

std::unique_ptr<std::iostream> open(const std::string& abs_path, bool create)
{
    if (!is_virtual(abs_path)) return nullptr;

    const std::string k = norm(abs_path);
    auto& files = reg().files;
    auto it = files.find(k);

    std::shared_ptr<RamFile> f;
    if (it != files.end()) {
        f = it->second;
    } else if (create) {
        f = std::make_shared<RamFile>();
        files.emplace(k, f);
    } else {
        return nullptr;
    }

    return std::make_unique<ramstream>(f);
}

} // namespace xbase::ramfs
