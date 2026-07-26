// @dottalk.file v1
// subsystem: security
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: AIF-053
// owner: member.derald
// status: supported

// token_crypto.hpp — gold-standard identity crypto (M3): Argon2id + CSPRNG via libsodium.
//
// Replaces the placeholder identity crypto:
//   - gen_token()      : was mt19937_64 (predictable) -> libsodium randombytes_buf, 256-bit.
//   - make_credential(): was salt + FNV-1a-64 -> Argon2id (crypto_pwhash_str), memory-hard.
//
// libsodium is a vetted, audited implementation — chosen so authentication does not depend on
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

} // namespace dottalk::security
