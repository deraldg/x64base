#pragma once

#include <cstdint>
#include <filesystem>
#include <iosfwd>
#include <optional>
#include <string>
#include <vector>

namespace xindex {

struct InxEntry {
    std::string key;
    std::uint32_t recno{0};
};

class InxPayload final {
public:
    enum class Format : std::uint16_t {
        Unknown = 0,
        V1_1INX = 1,
        V2_2INX = 2
    };

    InxPayload() = default;

    void clear() noexcept;
    bool empty() const noexcept;

    Format format() const noexcept { return format_; }
    bool is1Inx() const noexcept { return format_ == Format::V1_1INX; }
    bool is2Inx() const noexcept { return format_ == Format::V2_2INX; }

    const std::string& exprToken() const noexcept { return expr_token_; }
    std::uint16_t keyLength() const noexcept { return key_len_; }
    std::uint32_t recordCountSnapshot() const noexcept { return record_count_snapshot_; }

    const std::vector<InxEntry>& entries() const noexcept { return entries_; }
    std::size_t size() const noexcept { return entries_.size(); }
    const InxEntry& entryAt(std::size_t i) const;

    bool hasPosByRecno() const noexcept { return !pos_by_recno_.empty(); }
    std::int32_t positionOfRecno(std::uint32_t recno) const noexcept;

    // payload-level lookup helpers
    std::optional<std::size_t> topPos() const noexcept;
    std::optional<std::size_t> bottomPos() const noexcept;
    std::optional<std::size_t> seekExact(const std::string& key) const;
    std::optional<std::size_t> seekFirstGe(const std::string& key) const;

    // serialization
    bool readFromStream(std::istream& in, std::string* err = nullptr);
    bool writeToStream(std::ostream& out, std::string* err = nullptr) const;

    bool readFromFile(const std::filesystem::path& path, std::string* err = nullptr);
    bool writeToFile(const std::filesystem::path& path, std::string* err = nullptr) const;

    // canonical builders from sorted entries
    static InxPayload fromEntries1Inx(const std::string& expr_token,
                                      const std::vector<InxEntry>& entries);

    static InxPayload fromEntries2Inx(const std::string& expr_token,
                                      std::uint16_t key_len,
                                      std::uint32_t rec_count_snapshot,
                                      const std::vector<InxEntry>& entries);

private:
    Format format_{Format::Unknown};
    std::string expr_token_{};

    std::uint16_t key_len_{0};                 // V2 only
    std::uint32_t record_count_snapshot_{0};   // V2 only

    std::vector<InxEntry> entries_{};
    std::vector<std::int32_t> pos_by_recno_{};

private:
    static bool lessEntryKey_(const InxEntry& e, const std::string& key);
    static bool lessKeyEntry_(const std::string& key, const InxEntry& e);
};

} // namespace xindex