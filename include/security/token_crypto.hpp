// @dottalk.file v1
// subsystem: security
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: AIF-053
// owner: member.derald
// status: supported

// token_crypto.hpp -- gold-standard identity crypto (M3): Argon2id + CSPRNG via libsodium.
//
// Replaces the placeholder identity crypto:
//   - gen_token()      : was mt19937_64 (predictable) -> libsodium randombytes_buf, 256-bit.
//   - make_credential(): was salt + FNV-1a-64 -> Argon2id (crypto_pwhash_str), memory-hard.
//
// libsodium is a vetted, audited implementation -- chosen so authentication does not depend on
// hand-rolled cryptography. The credential is a self-describing PHC string
// ("$argon2id$v=19$m=...,t=...,p=...$salt$hash"); its parameters travel with the hash, so
// raising cost later does not break existing credentials. Verification is constant-time
// (crypto_pwhash_str_verify). verify_credential() accepts only Argon2 strings; legacy FNV
// credentials are handled by the caller (identity_admin) during migration.
#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace dottalk::security {

// Initialize libsodium (idempotent, thread-safe). Throws std::runtime_error on failure.
// Called lazily by the functions below; exposed so a SECURITY SELFTEST can assert availability.
void crypto_init();

// Cryptographically secure random bytes (libsodium randombytes_buf). Throws on init failure.
std::vector<std::uint8_t> secure_random_bytes(std::size_t n);

// A 256-bit opaque token, base64url (43 chars, no padding), for owner-issued agent credentials.
std::string gen_token();

// Hash a secret (token or password) for storage in SYSUSER.CRED, using Argon2id at the configured
// cost (see token_crypto.cpp). Returns a PHC string that fits crypto_pwhash_STRBYTES (128).
std::string make_credential(const std::string& secret);

// Constant-time Argon2id verify. Returns false for any non-Argon2 string (caller handles legacy).
bool verify_credential(const std::string& stored, const std::string& secret);

// True if `stored` is an Argon2 PHC credential (vs a legacy FNV credential).
bool is_argon2_credential(const std::string& stored);

// ---- content identity (AIF-120, owner instruction 2026-10-13) --------------
//
// SHA-256 of an arbitrary byte string, as 64 LOWERCASE HEX characters.
//
// NOT A CREDENTIAL PRIMITIVE, and deliberately not in the family above. There
// is no salt, no cost parameter and no secret. The two functions above are slow
// ON PURPOSE because a password must resist being guessed; this one is fast on
// purpose because it answers a different question -- "are these the same bytes"
// and "what is the identity of these bytes". Using it on a secret would be a
// defect; using Argon2id for content identity would be unusable.
//
// WHY IT LIVES HERE rather than beside its caller. This file is the ONE place
// the product speaks to libsodium, which is the whole reason it exists, and
// crypto_init()'s call_once discipline is already correct in it. A hash helper
// anywhere else would either re-derive that discipline or skip it. The file's
// own rule -- "No hand-rolled crypto" -- rules out writing a second SHA-256,
// and sodium_bin2hex means the hex conversion is not hand-rolled either.
//
// 64 hex characters is not a coincidence: WORKSPACES.dbf's PAYLOAD_SHA column
// was chartered C(64) on 2026-08-11, which is exactly SHA-256 hex. The column
// was sized for this before anything wrote it.
std::string sha256_hex(const std::string& bytes);

} // namespace dottalk::security
