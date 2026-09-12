// @dottalk.file v1
// subsystem: xbase
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "xbase.hpp"
#include "textio.hpp"
#include "xbase_64.hpp"
#include "xbase/field_codec.hpp"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <cstdint>
#include <limits>
#include <stdexcept>

namespace xbase {

namespace {

static inline bool is_memo_type(const FieldDef& f) noexcept
{
    return (f.type == 'M' || f.type == 'm');
}

static inline bool is_x64_memo_field_fast(bool is_x64, const FieldDef& f) noexcept
{
    return is_x64 && is_memo_type(f) && f.length == X64_MEMO_FIELD_LEN;
}

static inline std::uint64_t read_u64_le(const char* p) noexcept
{
    std::uint64_t v = 0;
    std::memcpy(&v, p, sizeof(v));
    return v;
}

static inline void write_u64_le(char* p, std::uint64_t v) noexcept
{
    std::memcpy(p, &v, sizeof(v));
}

static inline std::streampos checked_record_pos_(const DbArea& area, std::uint64_t recno64)
{
    if (recno64 < 1) {
        throw std::runtime_error("DbArea: invalid record number");
    }

    const auto data_start = area.dataStart64();
    const auto rec_len = area.recLength64();
    const auto row_index = recno64 - 1;

    if (rec_len != 0 &&
        row_index > ((std::numeric_limits<std::uint64_t>::max() - data_start) / rec_len)) {
        throw std::runtime_error("DbArea: record offset overflow");
    }

    const auto offset64 = data_start + row_index * rec_len;
    if (offset64 > static_cast<std::uint64_t>(std::numeric_limits<std::streamoff>::max())) {
        throw std::runtime_error("DbArea: record offset exceeds stream range");
    }

    return static_cast<std::streampos>(static_cast<std::streamoff>(offset64));
}

} // namespace

bool DbArea::readCurrent()
{
    if (_crn == 0) return false;

    const std::streampos pos =
        checked_record_pos_(*this, static_cast<std::uint64_t>(_crn));

    io().seekg(pos, std::ios::beg);
    io().read(_recbuf.data(), _recbuf.size());
    if (!io()) return false;

    _del = _recbuf[0];
    return loadFieldsFromBuffer();
}

bool DbArea::readCurrentRaw()
{
    if (_crn == 0) return false;

    const std::streampos pos =
        checked_record_pos_(*this, static_cast<std::uint64_t>(_crn));

    io().seekg(pos, std::ios::beg);
    io().read(_recbuf.data(), _recbuf.size());
    if (!io()) return false;

    _del = _recbuf[0];
    // Intentionally NO loadFieldsFromBuffer(): fields are decoded on demand via
    // decodeFieldFromBuffer()/fieldNumFromBuffer(). _fd is left stale.
    return true;
}

std::size_t DbArea::fieldByteOffset_(int idx1) const
{
    if (idx1 < 1 || idx1 > static_cast<int>(_fields.size()))
        return static_cast<std::size_t>(-1);

    std::size_t off = 1; // record byte 0 is the deleted flag
    for (int i = 0; i < idx1 - 1; ++i)
        off += _fields[static_cast<std::size_t>(i)].length;
    return off;
}

// AIF-091 M1 -- IS THIS FIELD NULL IN THE RECORD CURRENTLY IN THE BUFFER?
//
// The bitmap lives in the `_NullFlags` column, which partitionTrailingSystemField()
// removed from fields() but whose record offset it kept. So the bytes are still in
// `_recbuf` at `_null_flags.offset`; what was removed is the pretence that it is a
// user column.
//
// EVERY FAILURE PATH RETURNS FALSE, and that direction is chosen, not incidental.
// "Not null" makes the caller read the field's bytes -- which are really there, and
// which are what every caller saw before this function existed. "Null" would make a
// caller DISCARD a value on the strength of a bitmap we could not read. Given a
// short buffer or a missing layout, showing the stored bytes is the error that can
// be noticed; hiding them is the error that cannot.
//
// Nullability is a property of the TABLE (fieldIsNullable); nullness is a property
// of the ROW. A field with no null bit is not "not null" -- it is a field where the
// question does not apply, and both answer false here on purpose: a caller that
// needs to tell those apart asks fieldIsNullable() first.
bool DbArea::fieldIsNullFromBuffer(int idx1) const noexcept
{
    if (!_null_flags.present) return false;
    if (idx1 < 1 || idx1 > static_cast<int>(_fields.size())) return false;
    if (idx1 > static_cast<int>(_null_layout.fields.size())) return false;

    const int bit = _null_layout.fields[static_cast<std::size_t>(idx1 - 1)].null_bit;
    if (bit < 0) return false;                       // field is not nullable

    const std::size_t off = _null_flags.offset;
    const std::size_t len = _null_flags.length;
    if (len == 0) return false;
    if (off > _recbuf.size() || len > _recbuf.size() - off) return false;

    return vfp::bit_is_set(
        reinterpret_cast<const std::uint8_t*>(_recbuf.data()) + off, len, bit);
}

// A field is variable-length exactly when the bit layout gave it a "full" bit.
// That is derived from the descriptor (type V/Q) in ONE place -- see
// partitionTrailingSystemField() -- so this never re-decides it from f.type.
bool DbArea::isVarlengthField_(int idx1) const noexcept
{
    if (idx1 < 1 || idx1 > static_cast<int>(_null_layout.fields.size())) return false;
    return _null_layout.fields[static_cast<std::size_t>(idx1 - 1)].full_bit >= 0;
}

// How many of this V/Q field's bytes are the value, for the record in the buffer.
//
// The varlength bit SET means the trailing byte holds the length; CLEAR means the
// value fills the field. FAILS TOWARD THE DATA, like fieldIsNullFromBuffer(): with
// no readable bitmap the answer is "full", which shows every stored byte. Claiming
// a short length we could not verify would HIDE bytes that are really there.
std::size_t DbArea::varlengthValueLen_(int idx1, std::size_t off) const noexcept
{
    if (idx1 < 1 || idx1 > static_cast<int>(_fields.size()))
        return 0;
    const std::size_t width = _fields[static_cast<std::size_t>(idx1 - 1)].length;
    if (off + width > _recbuf.size()) return 0;

    const int bit = isVarlengthField_(idx1)
        ? _null_layout.fields[static_cast<std::size_t>(idx1 - 1)].full_bit
        : -1;
    if (bit < 0) return width;

    bool length_byte_in_use = false;
    if (_null_flags.present && _null_flags.length > 0 &&
        _null_flags.offset < _recbuf.size() &&
        _null_flags.length <= _recbuf.size() - _null_flags.offset) {
        length_byte_in_use = vfp::bit_is_set(
            reinterpret_cast<const std::uint8_t*>(_recbuf.data()) + _null_flags.offset,
            _null_flags.length, bit);
    }

    return vfp::varlength_value_length(
        reinterpret_cast<const std::uint8_t*>(_recbuf.data()) + off,
        width, length_byte_in_use);
}

std::string DbArea::decodeFieldFromBuffer(int idx1) const
{
    if (idx1 < 1 || idx1 > static_cast<int>(_fields.size())) return {};

    const std::size_t off = fieldByteOffset_(idx1);
    if (off == static_cast<std::size_t>(-1)) return {};

    const auto& f = _fields[static_cast<std::size_t>(idx1 - 1)];
    if (off + f.length > _recbuf.size()) return {};

    const bool is_x64 = (versionByte() == DBF_VERSION_64);

    if (is_x64_memo_field_fast(is_x64, f)) {
        const std::uint64_t object_id = read_u64_le(_recbuf.data() + off);
        if (object_id == 0) return {};
        return std::to_string(object_id);
    }

    // VARCHAR/VARBINARY: return exactly the stored value, and DO NOT rtrim it.
    // Trailing blanks inside the stored length are significant -- that is the
    // whole difference between `V` and `C`, and rtrimming would erase it. The
    // codec registry is bypassed here for the reason given in xbase.hpp.
    if (isVarlengthField_(idx1)) {
        const std::size_t n = varlengthValueLen_(idx1, off);
        return std::string(_recbuf.data() + off, n);
    }

    return fieldcodec::codec_for(f.type)
               .decode(_recbuf.data() + off, f.length, f);
}

bool DbArea::fieldNumFromBuffer(int idx1, double& out) const
{
    if (idx1 < 1 || idx1 > static_cast<int>(_fields.size())) return false;

    const auto& f = _fields[static_cast<std::size_t>(idx1 - 1)];
    const char ftype = static_cast<char>(std::toupper(static_cast<unsigned char>(f.type)));
    if (ftype != 'N' && ftype != 'F') return false;  // ASCII-numeric only

    const std::size_t off = fieldByteOffset_(idx1);
    if (off == static_cast<std::size_t>(-1)) return false;
    if (off + f.length > _recbuf.size()) return false;

    // N/F fields are right-justified, space-padded ASCII decimal. Copy the (short,
    // fixed-width) span to a stack buffer, NUL-terminate, and strtod -- no heap.
    const char* p = _recbuf.data() + off;
    const std::size_t len = f.length;

    char buf[64];
    if (len >= sizeof(buf)) return false;  // implausibly wide numeric; fall back

    std::size_t n = 0;
    for (std::size_t i = 0; i < len; ++i) {
        const char c = p[i];
        if (c == '\0') break;
        buf[n++] = c;
    }
    buf[n] = '\0';

    char* end = nullptr;
    const double v = std::strtod(buf, &end);
    if (end == buf) return false;               // nothing parsed (e.g., all spaces)
    while (*end == ' ' || *end == '\t') ++end;  // trailing pad is fine
    if (*end != '\0') return false;             // junk after the number
    out = v;
    return true;
}

bool DbArea::isDeleted() const
{
    if (!_recbuf.empty())
        return _recbuf[0] == IS_DELETED;

    return _del == IS_DELETED;
}

bool DbArea::writeCurrent()
{
    if (_crn == 0) return false;

    storeFieldsToBuffer();

    const std::streampos pos =
        checked_record_pos_(*this, static_cast<std::uint64_t>(_crn));

    io().seekp(pos, std::ios::beg);
    io().write(_recbuf.data(), _recbuf.size());
    io().flush();

    bool ok = static_cast<bool>(io());

    if (ok) _fd_snapshot = _fd;

    return ok;
}

std::string DbArea::get(int idx) const
{
    if (idx < 1 || idx > static_cast<int>(_fields.size())) return {};
    return _fd[idx];
}

bool DbArea::set(int idx, const std::string& val)
{
    if (idx < 1 || idx > static_cast<int>(_fields.size())) return false;
    _fd[idx] = val;
    return true;
}

bool DbArea::loadFieldsFromBuffer()
{
    _fd.assign(_fields.size() + 1, std::string{});
    // LOCKSTEP WITH _fd. Populated below from the bitmap the buffer carries, so
    // that the staged view starts out agreeing with the row on disk.
    _fd_null.assign(_fields.size() + 1, char{0});

    const bool is_x64 = (versionByte() == DBF_VERSION_64);

    size_t off = 1;

    for (size_t i = 0; i < _fields.size(); ++i) {
        const auto& f = _fields[i];

        if (off + f.length > _recbuf.size())
            return false;

        if (is_x64_memo_field_fast(is_x64, f)) {
            const std::uint64_t object_id = read_u64_le(_recbuf.data() + off);

            if (object_id == 0)
                _fd[i + 1].clear();
            else
                _fd[i + 1] = std::to_string(object_id);

        } else if (isVarlengthField_(static_cast<int>(i) + 1)) {
            // Varchar: the value, without its trailing length byte, un-rtrimmed.
            const std::size_t n = varlengthValueLen_(static_cast<int>(i) + 1, off);
            _fd[i + 1].assign(_recbuf.data() + off, n);

        } else {
            // Field-type codec: text (default) for C/N/F/D/L/M, binary for I (and
            // later B/Y/T / custom types). The text codec reproduces the legacy
            // fixed-width rtrim behavior exactly.
            _fd[i + 1] = fieldcodec::codec_for(f.type)
                             .decode(_recbuf.data() + off, f.length, f);
        }

        off += f.length;
    }

    // The staged null view is READ BACK OUT OF THE BITMAP rather than derived
    // from the values: an empty string and a NULL are different things and only
    // the bitmap can tell them apart. fieldIsNullFromBuffer() already fails
    // closed on a missing bitmap, a field with no null bit, or a short buffer.
    for (std::size_t i = 0; i < _fields.size(); ++i)
        _fd_null[i + 1] =
            fieldIsNullFromBuffer(static_cast<int>(i) + 1) ? char{1} : char{0};

    _fd_snapshot = _fd;

    return true;
}

bool DbArea::fieldIsNull(int idx1) const noexcept
{
    if (idx1 < 1 || idx1 >= static_cast<int>(_fd_null.size())) return false;
    return _fd_null[static_cast<std::size_t>(idx1)] != 0;
}

bool DbArea::setFieldNull(int idx1, bool make_null)
{
    if (idx1 < 1 || idx1 > static_cast<int>(_fields.size())) return false;
    if (idx1 >= static_cast<int>(_fd_null.size()))           return false;

    // THE TABLE DECIDES. A field whose descriptor never carried 0x02 has no null
    // bit, so there is nowhere to record the answer; setting one anyway would
    // write a bit that belongs to some other field or to nothing at all. Refuse
    // rather than succeed silently -- this is the AIF-118 shape, and a cheerful
    // return here would be indistinguishable from having worked.
    if (!fieldIsNullable(idx1)) return false;

    _fd_null[static_cast<std::size_t>(idx1)] = make_null ? char{1} : char{0};

    // A null cell has no value. Clearing it keeps get() honest about what the
    // next write will put on disk (spaces), and -- for a Varchar -- it is also
    // what makes the byte encoding come out right without a special case: an
    // empty value is not full, so storeFieldsToBuffer() writes a trailing length
    // byte of 0x00 and SETS the varlength bit, which is exactly what Visual
    // FoxPro wrote for a null Varchar in nullfix.DBF rows 2 and 5.
    if (make_null) _fd[static_cast<std::size_t>(idx1)].clear();

    return true;
}

void DbArea::storeFieldsToBuffer()
{
    const bool is_x64 = (versionByte() == DBF_VERSION_64);

    // ---- PRESERVE THE PARTITIONED `_NullFlags` COLUMN ---------------------
    //
    // The space-fill below clears the WHOLE record, and the loop after it writes
    // one field per entry in `_fields`. Since fbd7e5ee5 the `_NullFlags` column is
    // NOT in `_fields` -- the partition removed it so it would stop surfacing as a
    // junk one-byte binary column -- so its bytes were cleared and never written
    // back. A write left the bitmap at 0x20: EVERY NULL BECAME NOT-NULL and every
    // short Varchar claimed to be full.
    //
    // The record kept its length, its field values and its deleted flag. Only the
    // nulls were gone, which is why nothing caught it: that is the AIF-110 shape,
    // and its spec says the lesson in one line -- a test that asserts SHAPE passes
    // green on a blanked table. Proved at runtime 2026-09-05 by
    // dottalkpp_vfp_null_write_guard_test, which does the most harmless write
    // available (re-setting a field to the value it already holds) and watched
    // 0x03 become 0x20.
    //
    // Honest about the history: before the partition this column was a visible
    // field, so `_fd` held its byte as text and the fixed-width text codec
    // re-encoded it -- rtrimming, so 0x20 decoded to empty and wrote back as a
    // space while other values survived by luck. It was an unreliable round trip
    // and the partition made it deterministic destruction. Both halves are true.
    //
    // THE BITMAP IS NOW FULLY RECOMPUTED. Every bit any field owns is written from
    // the staged row; the save/restore below survives only for bits NO FIELD OWNS
    // -- padding in a multi-byte bitmap -- which nothing here is entitled to
    // invent or destroy.
    //
    //   NULL bits       RECOMPUTED, from `_fd_null`, which setFieldNull() stages
    //                   and loadFieldsFromBuffer() seeds from the bitmap already
    //                   on disk. So a row that is merely re-written keeps its
    //                   nulls (the staged view was loaded from those same bits),
    //                   and a row whose null state was changed writes the change.
    //   VARLENGTH bits  RECOMPUTED, from the value actually being written. They
    //                   HAVE to be: a Varchar write changes whether the field is
    //                   full, and a carried-forward varlength bit would describe
    //                   the value that used to be there. Measured before it was
    //                   changed (dottalkpp_vfp_varchar_roundtrip_test): setting a
    //                   10-byte Varchar to a full-width value left the bit SET,
    //                   claiming a length byte that was now data.
    //
    // THIS COMMENT HAS NOW BEEN WRONG TWICE AND SAID SO BOTH TIMES, which is the
    // only reason it was cheap to correct. Version one said the carry-forward was
    // correct "because none of them can change a null bit ... when Varchar writes
    // land in M2 this must become a RECOMPUTE". Version two said the split was
    // half and half and that "when set-to-null lands, these must be recomputed
    // too, and this comment is the place that will be wrong until they are".
    // Set-to-null landed. This is that recompute.
    //
    // A NULL VARCHAR NEEDS NO SPECIAL CASE HERE, and that is a measurement rather
    // than a convenience: setFieldNull() clears the staged value, an empty value
    // is not full, so the branch below writes a trailing length byte of 0x00 and
    // SETS the varlength bit -- which is byte-for-byte what Visual FoxPro wrote
    // for a null Varchar in nullfix.DBF rows 2 and 5. If that rule is ever found
    // to be wrong, the fix belongs in the V branch and not here.
    std::vector<char> saved_null_flags;
    const bool have_bitmap =
        _null_flags.present &&
        _null_flags.length > 0 &&
        _null_flags.offset < _recbuf.size() &&
        _null_flags.length <= _recbuf.size() - _null_flags.offset;
    if (have_bitmap) {
        const auto first = _recbuf.begin() +
            static_cast<std::ptrdiff_t>(_null_flags.offset);
        saved_null_flags.assign(first,
            first + static_cast<std::ptrdiff_t>(_null_flags.length));
    }

    std::fill(_recbuf.begin(), _recbuf.end(), ' ');
    _recbuf[0] = _del;

    size_t off = 1;

    for (size_t i = 0; i < _fields.size(); ++i) {
        const auto& f = _fields[i];
        const std::string& src = _fd[i + 1];

        if (is_x64_memo_field_fast(is_x64, f)) {
            std::uint64_t object_id = 0;

            if (!src.empty()) {
                try {
                    object_id = std::stoull(src);
                }
                catch (...) {
                    object_id = 0;
                }
            }

            write_u64_le(_recbuf.data() + off, object_id);

        } else if (isVarlengthField_(static_cast<int>(i) + 1)) {
            // VARCHAR/VARBINARY. Three things must agree or the row is malformed:
            // the value bytes, the trailing length byte, and the varlength bit.
            // Only this function can see all three, which is why V is not a codec.
            const std::size_t width = f.length;
            std::size_t n = src.size();
            if (n > width) n = width;           // over-long truncates, and is then full

            std::copy(src.begin(), src.begin() + static_cast<std::ptrdiff_t>(n),
                      _recbuf.begin() + static_cast<std::ptrdiff_t>(off));

            // A value that fills the field leaves NO ROOM for a length byte, so the
            // bit must be CLEAR. Anything shorter stores its length in the last byte
            // and sets the bit. The longest "short" value is width-1.
            const bool full = (n >= width);
            if (!full) {
                _recbuf[off + width - 1] =
                    static_cast<char>(static_cast<unsigned char>(n));
            }

            const int bit = _null_layout.fields[i].full_bit;
            if (have_bitmap && bit >= 0) {
                vfp::set_bit(reinterpret_cast<std::uint8_t*>(saved_null_flags.data()),
                             saved_null_flags.size(), bit, !full);
            }

        } else {
            // Field-type codec encodes into the field's byte region (pre-filled with
            // spaces above). The write path validated the value already, so an encode
            // failure here just leaves the padded region rather than corrupting it.
            std::string cerr;
            (void)fieldcodec::codec_for(f.type)
                      .encode(src, f, _recbuf.data() + off, &cerr);
        }

        // ---- THE NULL BIT, WRITTEN FOR EVERY FIELD THAT OWNS ONE ---------
        // Outside the type branches on purpose: nullness is orthogonal to how a
        // value is encoded, and a null memo, a null Varchar and a null numeric
        // all record it in the same place. The value area is left as whatever the
        // branch above wrote -- for a null field that is the space fill, which is
        // what VFP writes too.
        if (have_bitmap && i < _null_layout.fields.size()) {
            const int nbit = _null_layout.fields[i].null_bit;
            if (nbit >= 0) {
                const bool is_null =
                    (i + 1) < _fd_null.size() && _fd_null[i + 1] != 0;
                vfp::set_bit(reinterpret_cast<std::uint8_t*>(saved_null_flags.data()),
                             saved_null_flags.size(), nbit, is_null);
            }
        }

        off += f.length;
    }

    // ---- and put it back --------------------------------------------------
    // After the field loop, so a mis-sized field that overran into the bitmap's
    // bytes cannot silently win over the row's real null state.
    if (have_bitmap) {
        std::copy(saved_null_flags.begin(), saved_null_flags.end(),
                  _recbuf.begin() + static_cast<std::ptrdiff_t>(_null_flags.offset));
    }
}

std::string DbArea::rtrim(std::string s)
{
    while (!s.empty() && s.back() == ' ')
        s.pop_back();
    return s;
}

// ---- [INDEX helpers] ----

int DbArea::findFieldCI(const std::string& name) const
{
    // First resolve against the final runtime names. For x64 tables these may
    // have been promoted from X64M metadata by xbase_64.hpp.
    for (size_t i = 0; i < _fields.size(); ++i) {
        if (textio::ieq(_fields[i].name, name))
            return static_cast<int>(i + 1);
    }

    // Then allow the raw DBF/VFP descriptor fallback token. This preserves
    // compatibility when an x64 field has an authoritative long name but older
    // scripts still refer to its 10-byte descriptor token. If duplicate fallback
    // tokens exist, the first descriptor wins, matching the older ambiguous
    // behavior and relying on CREATE-time warnings to make that ambiguity known.
    for (size_t i = 0; i < _rawFields.size(); ++i) {
        const std::string fallback(_rawFields[i].field_name,
                                   strnlen(_rawFields[i].field_name, 11));
        if (!fallback.empty() && textio::ieq(fallback, name))
            return static_cast<int>(i + 1);
    }

    return 0;
}

int DbArea::firstCharField() const
{
    for (size_t i = 0; i < _fields.size(); ++i) {
        if (_fields[i].type == 'C')
            return static_cast<int>(i + 1);
    }
    return 0;
}

std::vector<uint8_t> DbArea::encodeKeyFrom(const std::vector<std::string>& vals) const
{
    const int idx = firstCharField();
    if (idx <= 0) return {};

    // vals is a 1-based field-value vector: slot 0 is intentionally unused.
    // firstCharField() also returns a 1-based field index. Do not subtract one
    // when reading vals, or index key generation will use the previous field.
    const size_t value_slot = static_cast<size_t>(idx);
    if (value_slot >= vals.size()) return {};

    const auto& f = _fields[static_cast<size_t>(idx - 1)];
    const std::size_t width = static_cast<std::size_t>(f.length);
    const bool upper = true;

    std::string key = vals[value_slot];
    if (upper) {
        std::transform(key.begin(), key.end(), key.begin(),
                       [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    }
    if (key.size() < width) key.append(width - key.size(), ' ');
    else if (key.size() > width) key.resize(width);
    return std::vector<uint8_t>(key.begin(), key.end());
}

} // namespace xbase
