// @dottalk.file v1
// subsystem: memo
// layer: helper
// owns:
// project: project.x64base.runtime
// lane: AIF-070 (memo zoo, MEMO_ZOO_ORTHOGONALITY_STRESS_CHARTER_V1)
// owner: member.derald
// status: experimental
//
// memo_zoo.cpp -- the Quantum Memo Zoo, M1 solo harness.
//
// The claim under test: the memo store is PAYLOAD-AGNOSTIC and ORTHOGONAL.
// Memos have no behavior -- so the zoo's species are DRIVER PERSONAS: this
// harness performs each species' chaotic operation pattern AGAINST the store
// through the public MemoStore API. The store passes if it remains a passive,
// byte-faithful cage no matter what the animals do.
//
// Oracle: an in-memory shadow (animal -> {token, bytes}) mirrors every
// operation. After each generation a full sweep byte-compares every stored
// payload against the shadow. First divergence prints seed/generation/animal
// and exits 1 -- replay with --seed to reproduce (single PRNG, no wall-clock
// in any decision).
//
// Species -> verb coverage (charter section 3):
//   Entropy-Fawn   mutate own bytes            update_text (fidelity)
//   Pointer-Beetle overwrite ANOTHER's prefix  update_text cross-memo (isolation)
//   Stack-Serpent  grow, shed past threshold   update_text large/shrinking
//   Fork-Turtle    duplicate self              put_text under growth
//   Merge-Hawk     concat two, retire sources  put_text + erase
//   Null-Otter     empty own / erase another   zero-length payload + erase
//
// Ecosystem events: --reopen-every G = Temporal Collapse (flush/close/reopen
// mid-chaos). After the chaos phases: steady-state settling (quiet read-only
// sweeps, zero divergence drift) and a final close/reopen durability sweep.
//
// Build stamp prints in the banner: three stale-binary incidents on
// 2026-08-11 taught us the build stamp is part of every proof.

#include "memo/memostore.hpp"

#include <cstdint>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <random>
#include <string>
#include <vector>

namespace fs = std::filesystem;
using dottalk::memo::MemoStore;
using dottalk::memo::MemoRef;
using dottalk::memo::OpenMode;

namespace {

enum class Species { Fawn, Beetle, Serpent, Turtle, Hawk, Otter };

const char* species_name(Species s) {
    switch (s) {
        case Species::Fawn:    return "Entropy-Fawn";
        case Species::Beetle:  return "Pointer-Beetle";
        case Species::Serpent: return "Stack-Serpent";
        case Species::Turtle:  return "Fork-Turtle";
        case Species::Hawk:    return "Merge-Hawk";
        case Species::Otter:   return "Null-Otter";
    }
    return "?";
}

struct Animal {
    Species     species;
    std::string token;   // current store ref (update_text moves it -- append-new)
    std::string bytes;   // shadow truth
};

struct Zoo {
    std::mt19937_64      rng;
    MemoStore            store;
    std::vector<Animal>  animals;
    fs::path             file;
    std::uint64_t        ops = 0;
    std::uint64_t        seed = 0;

    std::uint64_t roll(std::uint64_t n) { return n ? rng() % n : 0; }

    // Payload-agnostic content: printable noise with occasional embedded
    // NUL and high bytes -- the store must not care (that IS the claim).
    std::string random_bytes(std::size_t len) {
        std::string s; s.reserve(len);
        for (std::size_t i = 0; i < len; ++i) {
            std::uint64_t r = rng() % 100;
            if (r < 2)       s.push_back('\0');
            else if (r < 6)  s.push_back(static_cast<char>(128 + (rng() % 128)));
            else             s.push_back(static_cast<char>(32 + (rng() % 95)));
        }
        return s;
    }

    bool put_animal(Species sp, std::string bytes) {
        auto pr = store.put_text(bytes);
        ++ops;
        if (!pr.ok) { std::cerr << "ZOO-FAIL: put_text: " << pr.error << "\n"; return false; }
        animals.push_back(Animal{sp, pr.ref.token, std::move(bytes)});
        return true;
    }

    bool update_animal(Animal& a, std::string bytes) {
        MemoRef ref{}; ref.token = a.token;
        auto pr = store.update_text(ref, bytes);
        ++ops;
        if (!pr.ok) { std::cerr << "ZOO-FAIL: update_text: " << pr.error << "\n"; return false; }
        a.token = pr.ref.token;   // append-new semantics: the token MOVES
        a.bytes = std::move(bytes);
        return true;
    }

    bool erase_animal(std::size_t idx) {
        MemoRef ref{}; ref.token = animals[idx].token;
        auto er = store.erase(ref);
        ++ops;
        if (!er.ok) { std::cerr << "ZOO-FAIL: erase: " << er.error << "\n"; return false; }
        animals.erase(animals.begin() + static_cast<std::ptrdiff_t>(idx));
        return true;
    }

    // The oracle: every shadow entry must read back byte-identical.
    bool sweep(std::uint64_t gen, const char* phase) {
        for (std::size_t i = 0; i < animals.size(); ++i) {
            const Animal& a = animals[i];
            MemoRef ref{}; ref.token = a.token;
            auto gr = store.get_text(ref);
            if (!gr.ok || gr.text != a.bytes) {
                std::cerr << "MEMO-ZOO DIVERGENCE: phase=" << phase
                          << " gen=" << gen << " animal=" << i
                          << " species=" << species_name(a.species)
                          << " shadow=" << a.bytes.size() << "B store="
                          << (gr.ok ? std::to_string(gr.text.size()) + "B differs"
                                    : ("read failed: " + gr.error))
                          << " seed=" << seed << "\n";
                return false;
            }
        }
        return true;
    }

    bool reopen() {
        auto fr = store.flush();
        if (!fr.ok) { std::cerr << "ZOO-FAIL: flush: " << fr.error << "\n"; return false; }
        store.close();
        auto orr = store.open(file.string(), OpenMode::OpenExisting);
        if (!orr.ok) { std::cerr << "ZOO-FAIL: reopen: " << orr.error << "\n"; return false; }
        return true;
    }
};

std::uint64_t arg_u64(int argc, char** argv, const char* name, std::uint64_t defv) {
    for (int i = 1; i + 1 < argc; ++i)
        if (std::strcmp(argv[i], name) == 0) return std::strtoull(argv[i + 1], nullptr, 10);
    return defv;
}

} // namespace

int main(int argc, char** argv) {
    Zoo z;
    z.seed                        = arg_u64(argc, argv, "--seed", 20260811);
    const std::uint64_t gens      = arg_u64(argc, argv, "--generations", 500);
    const std::uint64_t popCap    = arg_u64(argc, argv, "--population-cap", 500);
    const std::uint64_t reopenEv  = arg_u64(argc, argv, "--reopen-every", 100);
    const std::uint64_t quietGens = arg_u64(argc, argv, "--quiet-generations", 5);
    const std::uint64_t popStart  = arg_u64(argc, argv, "--population", 50);
    const std::size_t   popFloor  = 8;   // predation pauses below this

    std::cout << "MEMO-ZOO M1 (solo) -- the zoo proves the cage\n"
              << "  build: " << __DATE__ << " " << __TIME__ << "\n"
              << "  seed=" << z.seed << " generations=" << gens
              << " population=" << popStart << " cap=" << popCap
              << " reopen-every=" << reopenEv
              << " quiet=" << quietGens << "\n";

    z.rng.seed(z.seed);
    z.file = fs::path("tmp") / "memo_zoo.dtx";
    std::error_code ec;
    fs::create_directories("tmp", ec);
    fs::remove(z.file, ec);   // deterministic fresh biosphere per run

    {
        auto r = z.store.open(z.file.string(), OpenMode::CreateIfMissing);
        if (!r.ok) { std::cerr << "ZOO-FAIL: open/create: " << r.error << "\n"; return 1; }
    }

    // --- Genesis: seed the biosphere ---------------------------------------
    static const Species kCast[] = { Species::Fawn, Species::Beetle, Species::Serpent,
                                     Species::Turtle, Species::Hawk, Species::Otter };
    for (std::uint64_t i = 0; i < popStart; ++i) {
        Species sp = kCast[z.roll(6)];
        if (!z.put_animal(sp, z.random_bytes(10 + z.roll(191)))) return 1;
    }
    if (!z.sweep(0, "genesis")) return 1;

    // --- Chaos generations -------------------------------------------------
    for (std::uint64_t g = 1; g <= gens; ++g) {
        const std::size_t count = z.animals.size();
        for (std::size_t i = 0; i < count && i < z.animals.size(); ++i) {
            Animal& a = z.animals[i];
            switch (a.species) {
                case Species::Fawn: {   // mutate own characters
                    std::string b = a.bytes;
                    if (b.empty()) b = z.random_bytes(8);
                    const std::size_t hits = 1 + z.roll(1 + b.size() / 16);
                    for (std::size_t k = 0; k < hits; ++k)
                        b[z.roll(b.size())] = static_cast<char>(z.rng() % 256);
                    if (!z.update_animal(a, std::move(b))) return 1;
                    break;
                }
                case Species::Beetle: { // bite ANOTHER animal's first 64 bytes
                    if (z.animals.size() < 2) break;
                    std::size_t v = z.roll(z.animals.size());
                    if (v == i) v = (v + 1) % z.animals.size();
                    Animal& victim = z.animals[v];
                    std::string b = victim.bytes;
                    const std::size_t n = b.size() < 64 ? b.size() : 64;
                    for (std::size_t k = 0; k < n; ++k)
                        b[k] = static_cast<char>(z.rng() % 256);
                    if (!z.update_animal(victim, std::move(b))) return 1;
                    break;
                }
                case Species::Serpent: { // grow; shed past threshold
                    std::string b = a.bytes + z.random_bytes(100 + z.roll(901));
                    if (b.size() > 65536) b = b.substr(b.size() / 2); // shed the tail... head
                    if (!z.update_animal(a, std::move(b))) return 1;
                    break;
                }
                case Species::Turtle: { // fork a child (population growth)
                    if (z.animals.size() < popCap) {
                        Species childSp = kCast[z.roll(6)];
                        if (!z.put_animal(childSp, a.bytes)) return 1;
                    }
                    break;
                }
                case Species::Hawk: {   // merge two others, retire the sources
                    if (z.animals.size() <= popFloor) break;
                    std::size_t p = z.roll(z.animals.size());
                    std::size_t q = z.roll(z.animals.size());
                    if (p == i || q == i || p == q) break;
                    std::string hybrid = z.animals[p].bytes + z.animals[q].bytes;
                    if (hybrid.size() > 65536) hybrid.resize(65536);
                    Species hsp = kCast[z.roll(6)];
                    // erase higher index first so the lower stays valid
                    std::size_t hi = p > q ? p : q, lo = p > q ? q : p;
                    if (!z.erase_animal(hi)) return 1;
                    if (!z.erase_animal(lo)) return 1;
                    if (!z.put_animal(hsp, std::move(hybrid))) return 1;
                    break;                        // indices shifted: yield the turn
                }
                case Species::Otter: {  // empty own payload, or erase another
                    if (z.roll(2) == 0) {
                        if (!z.update_animal(a, std::string())) return 1;  // zero-length
                    } else if (z.animals.size() > popFloor) {
                        std::size_t v = z.roll(z.animals.size());
                        if (v != i) { if (!z.erase_animal(v)) return 1; break; }
                    }
                    break;
                }
            }
            if (i >= z.animals.size()) break;     // predation shrank us past i
        }

        if (!z.sweep(g, "chaos")) return 1;

        if (reopenEv && (g % reopenEv) == 0) {    // Temporal Collapse
            if (!z.reopen()) return 1;
            if (!z.sweep(g, "reopen")) return 1;
        }
    }

    // --- Steady state: the ecosystem settles, the oracle stays green -------
    for (std::uint64_t q = 1; q <= quietGens; ++q)
        if (!z.sweep(gens + q, "steady")) return 1;

    // --- Final durability: close, reopen, one last sweep --------------------
    if (!z.reopen()) return 1;
    if (!z.sweep(gens + quietGens + 1, "final-reopen")) return 1;
    z.store.close();

    std::uint64_t shadowBytes = 0;
    for (const auto& a : z.animals) shadowBytes += a.bytes.size();

    std::cout << "MEMO-ZOO: " << gens << " generations, " << z.ops << " ops, "
              << z.animals.size() << " animals, " << shadowBytes
              << " shadow bytes, 0 divergences, seed " << z.seed << "\n";
    return 0;
}
