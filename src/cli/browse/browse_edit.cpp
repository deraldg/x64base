// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "browse_edit.hpp"
#include "xbase.hpp"
#include "xbase_cli.hpp"
#include <iostream>
#include <vector>

namespace dottalk::browse::edit {

int field_index_by_name(::xbase::DbArea& db, const std::string& name){
    auto up = [](std::string s){ for (auto& c : s) c = (char)std::toupper((unsigned char)c); return s; };
    const auto& defs = db.fields();
    auto needle = up(name);
    for (size_t i = 0; i < defs.size(); ++i){
        if (up(defs[i].name) == needle) return (int)i + 1;
    }
    return 0;
}

void list_fields(::xbase::DbArea& db){
    const auto& defs = db.fields();
    std::cout << "Fields (" << defs.size() << ")\n";
    for (size_t i = 0; i < defs.size(); ++i){
        const auto& f = defs[i];
        std::cout << "  " << (i+1) << ": " << f.name << " [" << f.type << "]";
        if (f.type=='C' || f.type=='N') std::cout << " len=" << f.length;
        if (f.type=='N' && f.decimals>0) std::cout << " dec=" << f.decimals;
        std::cout << "\n";
    }
}

bool commit_staged(::xbase::DbArea& db, StageMap& staged, std::string* err){
    if (err) err->clear();
    if (staged.empty()) return true;

    // THE GATE, BEFORE ANY WRITE (AIF-156). Ask about EVERY staged field
    // before writing ANY of them -- all or nothing, the whole point of
    // gateFieldWrites(). A refusal names its field and leaves the staged
    // map intact for the operator to amend or cancel.
    std::vector<std::pair<int, std::string>> writes;
    writes.reserve(staged.size());
    for (const auto& kv : staged) writes.emplace_back(kv.first, kv.second);

    std::string gate_err;
    int refused1 = 0;
    if (!::xbase::cli::gateFieldWrites(db, writes, &gate_err, &refused1)){
        if (err){
            *err = gate_err.empty() ? std::string("write refused") : gate_err;
            const auto& defs = db.fields();
            if (refused1 >= 1 && refused1 <= static_cast<int>(defs.size()))
                *err += std::string(" (field ") + defs[static_cast<size_t>(refused1) - 1].name + ")";
        }
        return false;   // nothing was written
    }

    for (auto& kv : staged){
        if (!db.set(kv.first, kv.second)){
            if (err) *err = "failed to set field #" + std::to_string(kv.first);
            return false;
        }
    }
    if (!db.writeCurrent()){
        if (err) *err = "failed to write record";
        return false;
    }
    staged.clear();
    return true;
}

void discard_staged(StageMap& staged){
    staged.clear();
}

} // namespace dottalk::browse::edit
