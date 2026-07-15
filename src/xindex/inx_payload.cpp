#include "xindex/inx_payload.hpp"

#include <algorithm>
#include <fstream>
#include <istream>
#include <ostream>
#include <cstring>

namespace xindex {

namespace {

static bool rd_u16(std::istream& in, std::uint16_t& v)
{
    unsigned char b[2]{};
    if (!in.read(reinterpret_cast<char*>(b), 2)) return false;
    v = static_cast<std::uint16_t>(b[0])
      | (static_cast<std::uint16_t>(b[1]) << 8);
    return true;
}

static bool rd_u32(std::istream& in, std::uint32_t& v)
{
    unsigned char b[4]{};
    if (!in.read(reinterpret_cast<char*>(b), 4)) return false;
    v = static_cast<std::uint32_t>(b[0])
      | (static_cast<std::uint32_t>(b[1]) << 8)
      | (static_cast<std::uint32_t>(b[2]) << 16)
      | (static_cast<std::uint32_t>(b[3]) << 24);
    return true;
}

static bool rd_i32(std::istream& in, std::int32_t& v)
{
    std::uint32_t u = 0;
    if (!rd_u32(in, u)) return false;
    v = static_cast<std::int32_t>(u);
    return true;
}

static void rtrim_spaces(std::string& s)
{
    while (!s.empty() && s.back() == ' ') s.pop_back();
}

} // namespace

void InxPayload::clear() noexcept
{
    format_ = Format::Unknown;
    expr_token_.clear();
    key_len_ = 0;
    record_count_snapshot_ = 0;
    entries_.clear();
    pos_by_recno_.clear();
}

bool InxPayload::empty() const noexcept
{
    return entries_.empty();
}

const InxEntry& InxPayload::entryAt(std::size_t i) const
{
    return entries_.at(i);
}

std::int32_t InxPayload::positionOfRecno(std::uint32_t recno) const noexcept
{
    if (recno < pos_by_recno_.size()) return pos_by_recno_[recno];
    return -1;
}

std::optional<std::size_t> InxPayload::topPos() const noexcept
{
    if (entries_.empty()) return std::nullopt;
    return 0;
}

std::optional<std::size_t> InxPayload::bottomPos() const noexcept
{
    if (entries_.empty()) return std::nullopt;
    return entries_.size() - 1;
}

bool InxPayload::lessEntryKey_(const InxEntry& e, const std::string& key)
{
    return e.key < key;
}

bool InxPayload::lessKeyEntry_(const std::string& key, const InxEntry& e)
{
    return key < e.key;
}

std::optional<std::size_t> InxPayload::seekExact(const std::string& key) const
{
    if (entries_.empty()) return std::nullopt;

    auto it = std::lower_bound(
        entries_.begin(), entries_.end(), key,
        [](const InxEntry& e, const std::string& k) { return e.key < k; });

    if (it == entries_.end() || it->key != key) return std::nullopt;
    return static_cast<std::size_t>(std::distance(entries_.begin(), it));
}

std::optional<std::size_t> InxPayload::seekFirstGe(const std::string& key) const
{
    if (entries_.empty()) return std::nullopt;

    auto it = std::lower_bound(
        entries_.begin(), entries_.end(), key,
        [](const InxEntry& e, const std::string& k) { return e.key < k; });

    if (it == entries_.end()) return std::nullopt;
    return static_cast<std::size_t>(std::distance(entries_.begin(), it));
}

bool InxPayload::readFromStream(std::istream& in, std::string* err)
{
    clear();

    if (!in) {
        if (err) *err = "input stream not ready";
        return false;
    }

    char magic[4]{};
    if (!in.read(magic, 4)) {
        if (err) *err = "unable to read INX magic";
        return false;
    }

    if (std::memcmp(magic, "1INX", 4) == 0) {
        format_ = Format::V1_1INX;

        std::uint16_t version = 0;
        std::uint16_t expr_len = 0;
        std::uint32_t count = 0;

        if (!rd_u16(in, version) || !rd_u16(in, expr_len) || !rd_u32(in, count)) {
            if (err) *err = "truncated 1INX header";
            clear();
            return false;
        }

        expr_token_.resize(expr_len);
        if (expr_len > 0 && !in.read(expr_token_.data(), expr_len)) {
            if (err) *err = "truncated 1INX expr token";
            clear();
            return false;
        }

        entries_.reserve(count);

        for (std::uint32_t i = 0; i < count; ++i) {
            std::uint16_t klen = 0;
            std::uint32_t recno = 0;

            if (!rd_u16(in, klen)) {
                if (err) *err = "truncated 1INX key length";
                clear();
                return false;
            }

            std::string key;
            key.resize(klen);
            if (klen > 0 && !in.read(key.data(), klen)) {
                if (err) *err = "truncated 1INX key data";
                clear();
                return false;
            }

            if (!rd_u32(in, recno)) {
                if (err) *err = "truncated 1INX recno";
                clear();
                return false;
            }

            entries_.push_back(InxEntry{std::move(key), recno});
        }

        return true;
    }

    if (std::memcmp(magic, "2INX", 4) == 0) {
        format_ = Format::V2_2INX;

        std::uint16_t version = 0;
        std::uint16_t expr_len = 0;
        std::uint32_t count = 0;

        if (!rd_u16(in, version) ||
            !rd_u16(in, key_len_) ||
            !rd_u16(in, expr_len) ||
            !rd_u32(in, count) ||
            !rd_u32(in, record_count_snapshot_)) {
            if (err) *err = "truncated 2INX header";
            clear();
            return false;
        }

        expr_token_.resize(expr_len);
        if (expr_len > 0 && !in.read(expr_token_.data(), expr_len)) {
            if (err) *err = "truncated 2INX expr token";
            clear();
            return false;
        }

        entries_.reserve(count);

        for (std::uint32_t i = 0; i < count; ++i) {
            std::string key;
            key.resize(key_len_);

            if (key_len_ > 0 && !in.read(key.data(), key_len_)) {
                if (err) *err = "truncated 2INX key data";
                clear();
                return false;
            }

            rtrim_spaces(key);

            std::uint32_t recno = 0;
            if (!rd_u32(in, recno)) {
                if (err) *err = "truncated 2INX recno";
                clear();
                return false;
            }

            entries_.push_back(InxEntry{std::move(key), recno});
        }

        pos_by_recno_.assign(static_cast<std::size_t>(record_count_snapshot_) + 1u, -1);
        for (std::size_t i = 0; i < pos_by_recno_.size(); ++i) {
            if (!rd_i32(in, pos_by_recno_[i])) {
                if (err) *err = "truncated 2INX pos-by-recno table";
                clear();
                return false;
            }
        }

        return true;
    }

    if (err) *err = "unknown INX magic";
    clear();
    return false;
}

bool InxPayload::writeToStream(std::ostream& out, std::string* err) const
{
    if (!out) {
        if (err) *err = "output stream not ready";
        return false;
    }

    if (err) *err = "InxPayload::writeToStream not implemented";
    return false;
}

bool InxPayload::readFromFile(const std::filesystem::path& path, std::string* err)
{
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        if (err) *err = "cannot open file: " + path.string();
        return false;
    }
    return readFromStream(in, err);
}

bool InxPayload::writeToFile(const std::filesystem::path& path, std::string* err) const
{
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) {
        if (err) *err = "cannot write file: " + path.string();
        return false;
    }
    return writeToStream(out, err);
}

InxPayload InxPayload::fromEntries1Inx(const std::string& expr_token,
                                       const std::vector<InxEntry>& entries)
{
    InxPayload p;
    p.format_ = Format::V1_1INX;
    p.expr_token_ = expr_token;
    p.entries_ = entries;
    return p;
}

InxPayload InxPayload::fromEntries2Inx(const std::string& expr_token,
                                       std::uint16_t key_len,
                                       std::uint32_t rec_count_snapshot,
                                       const std::vector<InxEntry>& entries)
{
    InxPayload p;
    p.format_ = Format::V2_2INX;
    p.expr_token_ = expr_token;
    p.key_len_ = key_len;
    p.record_count_snapshot_ = rec_count_snapshot;
    p.entries_ = entries;

    p.pos_by_recno_.assign(rec_count_snapshot + 1u, -1);
    for (std::size_t i = 0; i < p.entries_.size(); ++i) {
        const std::uint32_t rn = p.entries_[i].recno;
        if (rn < p.pos_by_recno_.size()) {
            p.pos_by_recno_[rn] = static_cast<std::int32_t>(i);
        }
    }

    return p;
}

} // namespace xindex