#include "xbase.hpp"

#if DOTTALK_HAS_XINDEX
#include "xindex/attach.hpp"
#include "xindex/index_manager.hpp"
#endif

#include <algorithm>
#include <cctype>
#include <iostream>
#include <string>

extern "C" { xbase::DbArea* cli_current_area_get(); }
static inline xbase::DbArea& A(){ return *cli_current_area_get(); }

#if DOTTALK_HAS_XINDEX
namespace xindex {
  bool db_move_top(xbase::DbArea&); bool db_move_next(xbase::DbArea&);
  bool db_at_eof(const xbase::DbArea&); bool db_record_is_deleted(const xbase::DbArea&);
  bool db_delete_current(xbase::DbArea&); bool db_position_valid(const xbase::DbArea&);
  void db_render_current(const xbase::DbArea&);
  bool db_index_has_active(const xbase::DbArea&);
  bool db_seek_key(const std::string&, bool, xbase::DbArea&);
  bool db_index_clear(xbase::DbArea&); bool db_index_load_file(const std::string&, xbase::DbArea&);
  bool db_index_set_order(const std::string&, xbase::DbArea&);
  int db_index_tag_count(const xbase::DbArea&); const char* db_index_active_tag(const xbase::DbArea&);
  std::string db_current_table_path(const xbase::DbArea&);
  int db_record_count(const xbase::DbArea&); int db_record_length(const xbase::DbArea&);
  int db_current_recno(const xbase::DbArea&); bool db_order_descending(const xbase::DbArea&);
  bool db_field_get_char(const std::string&, std::string&, const xbase::DbArea&);
  bool db_field_get_numeric(const std::string&, double&, const xbase::DbArea&);
  bool db_field_get_logical(const std::string&, bool&, const xbase::DbArea&);
  bool db_field_get_date_yyyymmdd(const std::string&, std::string&, const xbase::DbArea&);
}
#endif

namespace {

thread_local bool g_eof = true;
thread_local std::string g_active_tag;

int find_field_ci(const xbase::DbArea& area, const std::string& name)
{
    const auto& fields = area.fields();
    for (std::size_t i = 0; i < fields.size(); ++i) {
        if (fields[i].name.size() != name.size()) continue;
        const bool equal = std::equal(
            fields[i].name.begin(), fields[i].name.end(), name.begin(),
            [](unsigned char a, unsigned char b) {
                return std::tolower(a) == std::tolower(b);
            });
        if (equal) return static_cast<int>(i + 1);
    }
    return 0;
}

} // namespace

// Physical table operations belong to xbase and must remain available when no
// index engine is present.
bool db_move_top(){ g_eof = false; return A().top(); }
bool db_move_next(){ if (g_eof) return false; const bool ok = A().skip(1); if (!ok) g_eof = true; return ok; }
bool db_at_eof(){ return g_eof; }
bool db_record_is_deleted(){ return A().isDeleted(); }
bool db_delete_current(){ return A().deleteCurrent(); }
bool db_position_valid(){ return A().recno() > 0 && A().recno() <= A().recCount(); }
void db_render_current(){ std::cout << "[" << A().recno() << "]\n"; }

bool db_index_has_active(){
#if DOTTALK_HAS_XINDEX
    const auto* manager = xindex::manager_if_attached(A());
    return manager && manager->has_active();
#else
    return false;
#endif
}
bool db_seek_key(const std::string& k,bool d){
#if DOTTALK_HAS_XINDEX
    return xindex::db_seek_key(k,d,A());
#else
    (void)k; (void)d; return false;
#endif
}
bool db_index_clear(){
#if DOTTALK_HAS_XINDEX
    return xindex::db_index_clear(A());
#else
    return true;
#endif
}
bool db_index_load_file(const std::string& p){
#if DOTTALK_HAS_XINDEX
    return xindex::db_index_load_file(p,A());
#else
    (void)p; return false;
#endif
}
bool db_index_set_order(const std::string& t){
#if DOTTALK_HAS_XINDEX
    return xindex::db_index_set_order(t,A());
#else
    (void)t; return false;
#endif
}
int db_index_tag_count(){
#if DOTTALK_HAS_XINDEX
    return xindex::db_index_tag_count(A());
#else
    return 0;
#endif
}
const char* db_index_active_tag(){
#if DOTTALK_HAS_XINDEX
    return xindex::db_index_active_tag(A());
#else
    g_active_tag.clear(); return g_active_tag.c_str();
#endif
}

std::string db_current_table_path(){ return A().filename(); }
int db_record_count(){ return A().recCount(); }
int db_record_length(){ return A().recordLength(); }
int db_current_recno(){ return A().recno(); }
bool db_order_descending(){ return false; }

bool db_field_get_char(const std::string& n, std::string& out){
    const int field = find_field_ci(A(), n);
    if (field == 0) { out.clear(); return false; }
    out = A().get(field);
    return true;
}
bool db_field_get_numeric(const std::string& n, double& out){
    std::string value;
    if (!db_field_get_char(n, value)) return false;
    try { out = std::stod(value); return true; } catch (...) { return false; }
}
bool db_field_get_logical(const std::string& n, bool& out){
    std::string value;
    if (!db_field_get_char(n, value) || value.empty()) return false;
    const char c = static_cast<char>(std::toupper(static_cast<unsigned char>(value.front())));
    if (c == 'T' || c == 'Y' || c == '1') { out = true; return true; }
    if (c == 'F' || c == 'N' || c == '0') { out = false; return true; }
    return false;
}
bool db_field_get_date_yyyymmdd(const std::string& n, std::string& out){
    return db_field_get_char(n, out) && out.size() == 8;
}

