// @dottalk.file v1
// subsystem: security
// layer: engine-core
// owns: 
// project: project.x64base.runtime
// lane: AIF-053
// owner: member.derald
// status: supported

// token_crypto.cpp — gold-standard identity crypto via libsodium (Argon2id + CSPRNG).
//
// Depends on libsodium (vcpkg: "libsodium" -> unofficial-sodium::sodium). No hand-rolled crypto.
#include "security/token_crypto.hpp"

#include <sodium.h>

#include <mutex>
#include <stdexcept>

namespace dottalk::security {
namespace {

std::once_flag g_init_flag;
bool           g_init_ok = false;

// --- Argon2id cost ---------------------------------------------------------
// libsodium presets embed their parameters in the hash string, so raising these later does NOT
// invalidate existing credentials (verify reads the stored m/t/p). Default = INTERACTIVE
// (~64 MiB, t=2) — comfortably above OWASP's Argon2id minimum (19 MiB, t=2) while keeping logins
// snappy on student/lab machines. Raise to *_MODERATE (256 MiB) or *_SENSITIVE (1 GiB) for
// higher-value deployments.
constexpr unsigned long long kOps = crypto_pwhash_OPSLIMIT_INTERACTIVE;
constexpr std::size_t        kMem = crypto_pwhash_MEMLIMIT_INTERACTIVE;

} // namespace

void crypto_init() {
    std::call_once(g_init_flag, [] { g_init_ok = (sodium_init() >= 0); });
    if (!g_init_ok) throw std::runtime_error("token_crypto: libsodium init failed");
}

std::vector<std::uint8_t> secure_random_bytes(std::size_t n) {
    crypto_init();
    std::vector<std::uint8_t> out(n);
    if (n) randombytes_buf(out.data(), n);
    return out;
}

std::string gen_token() {
    crypto_init();
    unsigned char buf[32];                              // 256-bit
    randombytes_buf(buf, sizeof buf);
    char b64[64];                                       // 43 chars + NUL for 32B urlsafe-nopad
    sodium_bin2base64(b64, sizeof b64, buf, sizeof buf, sodium_base64_VARIANT_URLSAFE_NO_PADDING);
    sodium_memzero(buf, sizeof buf);
    return std::string(b64);
}

std::string make_credential(const std::string& secret) {
    crypto_init();
    char out[crypto_pwhash_STRBYTES];                  // == 128; matches SYSUSER.CRED width
    if (crypto_pwhash_str(out, secret.c_str(), secret.size(), kOps, kMem) != 0)
        throw std::runtime_error("token_crypto: Argon2id hashing failed (out of memory?)");
    return std::string(out);
}

bool is_argon2_credential(const std::string& stored) {
    return stored.rfind("$argon2", 0) == 0;            // "$argon2id$..." (or "$argon2i$")
}

bool verify_credential(const std::string& stored, const std::string& secret) {
    if (!is_argon2_credential(stored)) return false;   // caller handles legacy FNV
    crypto_init();
    // crypto_pwhash_str_verify is constant-time and reads the embedded m/t/p parameters.
    return crypto_pwhash_str_verify(stored.c_str(), secret.c_str(), secret.size()) == 0;
}

} // namespace dottalk::security
