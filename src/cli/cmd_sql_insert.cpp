// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// @dottalk.usage v1
// owner: DOT|INSERT
// command: INSERT
// category: sql
// status: supported
// noargs: usage
// effect: insert-record
// mutates: table-data
// usage-access: INSERT USAGE
// summary:
//   Insert a new record into the current DBF work area using SQL-like syntax.
//
// usage:
//   INSERT USAGE
//   INSERT (<field-list>) VALUES (<value-list>)
//   INSERT <field>=<value> [, <field>=<value> ...]
//
// examples:
//   INSERT (SID,LNAME,FNAME) VALUES (999,"SMITH","JANE")
//   INSERT SID=999, LNAME="SMITH", FNAME="JANE"
//
// notes:
//   INSERT USAGE prints usage before open-table checks.
//   INSERT appends a new record and writes supplied field values.
//   Field/value count must match in VALUES form.
//   INSERT HONOURS TABLE ON (2026-09-20). The two modes differ and the
//   difference is the contract:
//     TABLE OFF -- one table fence, one append, one write, immediately.
//                  Refuses with "INSERT: table locked (<reason>)" while
//                  another process holds the table (OI-043, 2026-09-19).
//                  ROLLBACK has nothing to discard; the row is already on disk.
//     TABLE ON  -- the row STAGES into the table buffer as CHANGE_INSERT and
//                  reaches the DBF at COMMIT. It takes NO OS lock at the
//                  statement, marks the area DIRTY, and ROLLBACK DISCARDS IT.
//                  A foreign table lock is refused at COMMIT rather than here,
//                  because a staged row touches no file.
//   marks_dirty: yes when TABLE ON; no when TABLE OFF
//   rollback_discards: yes when TABLE ON; no when TABLE OFF
//   Until 2026-09-20 this verb IGNORED TABLE ON entirely and wrote through in
//   both modes, so an INSERT inside a buffered session was durable before
//   COMMIT ran and ROLLBACK did not undo it. Measured from the DBF header
//   2026-09-19 (B0/BAREINS survived a ROLLBACK, no journal was ever written)
//   by dottalkpp/data/scripts/sql_insert_intervening_append_probe.dts ARM 0.
//   Same defect and same repair as MULTIREP under AIF-151.
//   THE STAGED NUMBER IS A BUFFER KEY, NOT AN ADDRESS (ruling (A), 2026-09-19).
//   Record identity is minted at COMMIT by the file.
//   MEMO IS UNMEASURED. This verb has never had memo-specific handling, so
//   staging changes nothing about where a payload lands, but what A.set() does
//   to a memo field here has not been measured either way.
//
// risk:
//   requires_open_table: yes except usage
//   requires_table_lock: TABLE OFF only -- REFUSES while another process holds
//     the table. Under TABLE ON no lock is taken here and the refusal moves to
//     COMMIT, which matches COMMIT's own contract: "TABLE ON buffers changes;
//     no OS locking should occur".
//   mutates_table_data: yes
//   appends_records: yes
//
// related:
//   SQL
//   UPDATE
//   SQLERASE
//
#include "xbase.hpp"
// AIF-156: the shared constraint gate. THIS FILE IS THE *LEGACY* INSERT/UPDATE
// VERB, NOT SQLSEL. PKPOLICY's arms T5 and T6 measure SQLSEL INSERT and SQLSEL
// UPDATE, which reach the buffer through evaluate_store_expression and are
// gated there -- and this pair is a SECOND, INDEPENDENT door registered at
// shell_commands.cpp:458-459 as the bare verbs INSERT and UPDATE. Three arms
// green said nothing whatever about this path.
#include "xbase_cli.hpp"
// OI-043: the append fence. MEASURED 2026-09-19 -- with a foreign LIVE table
// lock in place, APPEND BLANK, SQLSEL INSERT and REPLACE were all refused and
// THIS VERB INSERTED A ROW ANYWAY. One of two doors that let a second engine
// grow a table this one had fenced.
#include "cli/append_fence.hpp"
// AIF-151 / OI-043: TABLE ON makes this verb a buffered citizen, so it needs
// the buffer, the journal and the area-slot lookup the other buffered verbs use.
#include "cli/table_state.hpp"
#include "workarea_util.hpp"   // cli::slot_of_area -- which slot is this area?
#include "textio.hpp"
#include <algorithm>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

static inline std::string dt_trim(std::string s){
    auto sp=[](unsigned char c){ return c==' '||c=='\t'||c=='\r'||c=='\n'; };
    while(!s.empty() && sp((unsigned char)s.front())) s.erase(s.begin());
    while(!s.empty() && sp((unsigned char)s.back()))  s.pop_back();
    return s;
}
static inline std::string up(std::string s){ for(char& c: s) c=(char)std::toupper((unsigned char)c); return s; }

static bool parse_ident_list(const std::string& src, size_t& i, std::vector<std::string>& out){
    const size_t n = src.size();
    auto ws=[&]{ while(i<n && std::isspace((unsigned char)src[i])) ++i; };
    ws();
    if(i>=n || src[i] != '(') return false;
    ++i; ws();
    for(;;){
        if(i>=n) return false;
        size_t j=i;
        if(!(std::isalpha((unsigned char)src[j]) || src[j]=='_')) return false;
        ++j; while(j<n && (std::isalnum((unsigned char)src[j]) || src[j]=='_')) ++j;
        out.push_back(up(src.substr(i, j-i)));
        i=j; ws();
        if(i<n && src[i]==','){ ++i; ws(); continue; }
        if(i<n && src[i]==')'){ ++i; break; }
        return false;
    }
    return true;
}

static std::string parse_value_token(const std::string& src, size_t& i){
    const size_t n = src.size();
    auto ws=[&]{ while(i<n && std::isspace((unsigned char)src[i])) ++i; };
    ws(); if(i>=n) return {};
    if(src[i]=='\'' || src[i]=='"'){
        char q = src[i++];
        std::string out;
        while(i<n){
            char c = src[i++];
            if(c==q){
                if(i<n && src[i]==q){ out.push_back(q); ++i; continue; }
                break;
            }
            out.push_back(c);
        }
        return out;
    }
    size_t j=i; while(j<n && !std::isspace((unsigned char)src[j]) && src[j]!=',' && src[j]!=')') ++j;
    std::string t = src.substr(i, j-i); i=j; return t;
}

static bool parse_values_tuple(const std::string& src, size_t& i, std::vector<std::string>& out){
    const size_t n = src.size();
    auto ws=[&]{ while(i<n && std::isspace((unsigned char)src[i])) ++i; };
    ws(); if(i>=n || src[i] != '(') return false;
    ++i;
    for(;;){
        std::string v = parse_value_token(src, i);
        out.push_back(v);
        ws();
        if(i<n && src[i]==','){ ++i; continue; }
        if(i<n && src[i]==')'){ ++i; break; }
        return false;
    }
    return true;
}

static void print_insert_usage_contract()
{
    std::cout
        << "Usage:\n"
        << "  INSERT USAGE\n"
        << "  INSERT (<field-list>) VALUES (<value-list>)\n"
        << "  INSERT <field>=<value> [, <field>=<value> ...]\n"
        << "Examples:\n"
        << "  INSERT (SID,LNAME,FNAME) VALUES (999,\"SMITH\",\"JANE\")\n"
        << "  INSERT SID=999, LNAME=\"SMITH\", FNAME=\"JANE\"\n"
        << "Notes:\n"
        << "  - INSERT USAGE does not require an open table.\n"
        << "  - INSERT appends a new record.\n";
}

static bool insert_usage_contract(std::string tok)
{
    std::transform(tok.begin(), tok.end(), tok.begin(),
        [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return tok == "USAGE" || tok == "HELP" || tok == "?";
}

// ---------------------------------------------------------------------------
// ONE PLACE WHERE A ROW BECOMES A ROW (OI-043 remainder, 2026-09-20).
//
// This file had the append-and-write sequence TWICE -- once per syntax form --
// and both copies wrote straight through the table buffer. Adding the buffered
// branch to each would have made four paths where there should be one, so the
// sequence is a function now and the fork lives inside it.
//
// AIF-151 IS THE PRECEDENT AND IT IS THE SAME DEFECT IN ANOTHER VERB.
// cmd_replace_multi.cpp:887 records it: "MULTIREP used to ignore TABLE ON
// entirely and lock-and-write regardless, so a MULTIREP inside a buffered
// session was durable before COMMIT ran and ROLLBACK did not undo it." The
// legacy bare INSERT verb was the last one still doing that, measured by
// dottalkpp/data/scripts/sql_insert_intervening_append_probe.dts ARM 0 --
// written in NATIVE mode on purpose, because SET MODE SQL aliases INSERT to
// SQLSEL and a probe in SQL mode measures the wrong door entirely.
//
// NO FENCE ON THE BUFFERED PATH, AND THAT IS THE RULING RATHER THAN AN
// OVERSIGHT. Owner, 2026-09-20. COMMIT's own contract says "TABLE ON buffers
// changes; no OS locking should occur", and MULTIREP's buffered branch is
// taken BEFORE its record lock for exactly that reason: a staged row touches
// no file, so there is nothing for a table fence to protect. The fence fires
// at COMMIT, where cmd_commit.cpp already takes a transaction-long table lock
// gated on has_insert. THE VISIBLE CONSEQUENCE, stated because it changes what
// shipped on 2026-09-19: with TABLE ON, a foreign lock no longer refuses this
// verb at the statement -- the refusal moves to COMMIT. With TABLE OFF, which
// is what the foreign-lock probe measures, nothing changes at all.
//
// THE KEY IS NOT AN ADDRESS. Under ruling (A) the staged number orders the
// buffer and nothing else; the record number is minted at COMMIT by the file.
// next_insert_key is the one producer of it.
//
// MEMO IS UNMEASURED AND DELIBERATELY UNTOUCHED. MULTIREP had to write memo
// payloads immediately and buffer only the handle. This file has never had any
// memo handling, so staging changes nothing about where a payload lands -- but
// nobody has measured what A.set() does to a memo field here, and this comment
// is the record that it was noticed rather than assumed.
static bool insert_one_row(xbase::DbArea& A,
                           const std::vector<std::pair<int,std::string>>& writes,
                           std::string& err)
{
    const int area0 = cli::slot_of_area(&A);
    if (area0 >= 0 && dottalk::table::is_enabled(area0)) {
        auto& tb = dottalk::table::get_tb(area0);
        const std::uint64_t key =
            dottalk::table::next_insert_key(area0, A.recCount64());

        for (const auto& w : writes) {
            std::uint64_t bits[dottalk::table::kWords]{};
            const int index0 = w.first - 1;
            if (index0 < 0 || index0 / 64 >= dottalk::table::kWords) {
                err = "field index out of range";
                return false;
            }
            bits[index0 / 64] |= (std::uint64_t{1} << (index0 % 64));

            const int priority = tb.add_change(
                key, dottalk::table::CHANGE_INSERT, bits, w.first, w.second);
            if (priority == 0) { err = "table buffer refused a change"; return false; }

            // Write-ahead redo, only under RamJournal. Same shape as MULTIREP:
            // journal the exact buffered edit with the priority add_change
            // assigned, so history mode keeps every retained edit per field.
            if (dottalk::table::is_persistent_enabled(area0)) {
                dottalk::table::ChangeEntry je;
                je.recno = key;
                je.dirty_flags = dottalk::table::CHANGE_INSERT;
                je.priority = priority;
                je.new_values[w.first] = w.second;
                if (!dottalk::table::journal_note_change(area0, je)) {
                    err = "write-ahead journal refused a change";
                    return false;
                }
            }
            dottalk::table::mark_stale_field(area0, w.first);
        }

        // A ROW WITH NO FIELDS STILL HAS TO EXIST. The loop above stages one
        // entry per field, so an empty write list would stage nothing and the
        // row would vanish silently. It cannot happen from either syntax form
        // today -- both refuse a mismatched count long before here -- and it is
        // handled anyway, because "cannot happen" is how a row goes missing.
        if (writes.empty()) {
            const int priority = tb.add_change(key, dottalk::table::CHANGE_INSERT);
            if (priority == 0) { err = "table buffer refused a change"; return false; }
            if (dottalk::table::is_persistent_enabled(area0)) {
                dottalk::table::ChangeEntry je;
                je.recno = key;
                je.dirty_flags = dottalk::table::CHANGE_INSERT;
                je.priority = priority;
                if (!dottalk::table::journal_note_change(area0, je)) {
                    err = "write-ahead journal refused a change";
                    return false;
                }
            }
            dottalk::table::set_stale(area0, true);
        }

        if (!dottalk::table::is_dirty(area0)) dottalk::table::set_dirty(area0, true);
        return true;
    }

    // TABLE OFF -- unchanged. One fence, one append, one write, immediately.
    std::string fence_err;
    if (!cli::fence::append_fenced(A, &fence_err)) {
        err = "table locked (" + (fence_err.empty() ? std::string("lock exists") : fence_err) + ")";
        return false;
    }
    if (!A.readCurrent()) { err = "APPEND failed"; return false; }
    for (const auto& w : writes) A.set(w.first, w.second);
    if (!A.writeCurrent()) { err = "write failed"; return false; }
    return true;
}

void cmd_SQL_INSERT(xbase::DbArea& A, std::istringstream& iss){
    // INSERT_USAGE_CONTRACT_BRANCH
    {
        const std::streampos usage_pos = iss.tellg();
        std::string usage_tok;
        if (iss >> usage_tok) {
            iss.clear();
            if (usage_pos != std::streampos(-1)) {
                iss.seekg(usage_pos);
            }

            if (insert_usage_contract(usage_tok)) {
                print_insert_usage_contract();
                return;
            }
        } else {
            iss.clear();
            if (usage_pos != std::streampos(-1)) {
                iss.seekg(usage_pos);
            }
        }
    }

    if(!A.isOpen()){ std::cout<<"No file open\n"; return; }

    std::string rest; std::getline(iss, rest);
    rest = dt_trim(rest);
    if(rest.empty()){ std::cout<<"INSERT syntax\n"; return; }

    auto defs = A.fields();
    auto idx_of = [&](const std::string& upname)->int{
        for(size_t f=0; f<defs.size(); ++f){
            std::string t = defs[f].name;
            for(char& c: t) c = (char)std::toupper((unsigned char)c);
            if(t == upname) return int(f)+1;
        }
        return -1;
    };

    int inserted = 0;

    if(!rest.empty() && rest[0]=='('){
        size_t i=0;
        std::vector<std::string> fields;
        if(!parse_ident_list(rest, i, fields)){ std::cout<<"INSERT: bad field list\n"; return; }
        while(i<rest.size() && std::isspace((unsigned char)rest[i])) ++i;
        if(up(rest.substr(i,6))!="VALUES"){ std::cout<<"INSERT: expected VALUES\n"; return; }
        i+=6;
        for(;;){
            std::vector<std::string> vals;
            if(!parse_values_tuple(rest, i, vals)){ std::cout<<"INSERT: bad VALUES tuple\n"; return; }
            if(vals.size()!=fields.size()){ std::cout<<"INSERT: field/value count mismatch\n"; return; }
            // RESOLVE AND GATE BEFORE APPEND, NOT AFTER. Appending first and
            // discovering the refusal second leaves a blank row behind for a
            // write that was never allowed -- and on a table with a generated
            // PRIMARY key that blank row has already consumed a key.
            std::vector<std::pair<int,std::string>> writes;
            writes.reserve(fields.size());
            for(size_t k=0;k<fields.size();++k){
                int idx = idx_of(fields[k]);
                if(idx<0){ std::cout<<"INSERT: unknown field "<<fields[k]<<"\n"; return; }
                writes.emplace_back(idx, vals[k]);
            }
            {
                std::string gate_err;
                if(!xbase::cli::gateFieldWrites(A, writes, &gate_err, nullptr)){
                    std::cout<<"INSERT: "<<gate_err<<"\n"; return;
                }
            }
            {
                std::string row_err;
                if(!insert_one_row(A, writes, row_err)){
                    std::cout<<"INSERT: "<<row_err<<"\n"; return; }
            }
            ++inserted;
            while(i<rest.size() && std::isspace((unsigned char)rest[i])) ++i;
            if(i<rest.size() && rest[i]==','){ ++i; continue; }
            break;
        }
    }else{
        std::istringstream ss(rest);
        std::string pair;
        std::vector<std::pair<int,std::string>> assigns;
        while(std::getline(ss, pair, ',')){
            auto eq = pair.find('=');
            if(eq==std::string::npos){ std::cout<<"INSERT: expected name=value\n"; return; }
            auto trim=[](std::string s){
                while(!s.empty() && (s.front()==' '||s.front()=='\t')) s.erase(s.begin());
                while(!s.empty() && (s.back()==' '||s.back()=='\t')) s.pop_back();
                return s;
            };
            std::string name = up(trim(pair.substr(0,eq)));
            std::string val  = trim(pair.substr(eq+1));
            if(!val.empty() && (val.front()=='\''||val.front()=='"')){
                if(val.size()>=2 && (val.back()=='\''||val.back()=='"')) val = val.substr(1, val.size()-2);
            }
            int idx = idx_of(name);
            if(idx<0){ std::cout<<"INSERT: unknown field "<<name<<"\n"; return; }
            assigns.push_back({idx, val});
        }
        // Gate before APPEND here too -- same reason as the tuple form above.
        {
            std::string gate_err;
            if(!xbase::cli::gateFieldWrites(A, assigns, &gate_err, nullptr)){
                std::cout<<"INSERT: "<<gate_err<<"\n"; return;
            }
        }
        {
            std::string row_err;
            if(!insert_one_row(A, assigns, row_err)){
                std::cout<<"INSERT: "<<row_err<<"\n"; return; }
        }
        ++inserted;
    }

    std::cout<<inserted<<" row(s) inserted\n";
}



