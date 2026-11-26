// @dottalk.file v1
// subsystem: tests
// layer: test
// project: project.x64base.runtime
// owner: member.derald
// status: supported
#include "datadict/ddict_catalog_view.hpp"
#include "datadict/ddict_object_resolver.hpp"
#include "datadict/ddict_read_helpers.hpp"
#include "xbase/dbf_create.hpp"
#include "xbase.hpp"
#include "cli/cmd_ddict.hpp"
#include "cli/output_router.hpp"
#include <sstream>
#include "memo/memostore.hpp"
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>

namespace fs = std::filesystem;
using namespace dottalk::datadict;
using xbase::dbf_create::FieldSpec;
namespace {
int checks = 0;
void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
    ++checks;
    std::cout << "PASS " << message << '\n';
}
void create(const fs::path& dir, const std::string& file, const std::string& logical,
            std::vector<FieldSpec> fields, const std::vector<std::vector<std::string>>& records) {
    std::string why;
    // Unique descriptor fallbacks intentionally differ from authoritative names.
    for (std::size_t i=0; i<fields.size(); ++i) fields[i].descriptor_name = "F" + std::to_string(i+1);
    require(xbase::dbf_create::create_dbf((dir/(file+".dbf")).string(), logical, fields,
            xbase::dbf_create::Flavor::X64, why), "native CREATE " + file + ": " + why);
    xbase::DbArea area;
    area.open((dir/(file+".dbf")).string());
    require(area.logicalName() == logical, "native table identity " + logical);
    for (const auto& record : records) {
        require(area.appendBlank(), "native APPEND " + file);
        for (std::size_t i=0; i<record.size(); ++i)
            require(area.set(static_cast<int>(i+1),record[i]), "native field write " + fields[i].name);
        require(area.writeCurrent(), "native record write " + file);
    }
    area.close();
}
std::vector<FieldSpec> chars(std::initializer_list<const char*> names) {
    std::vector<FieldSpec> fields;
    for (const auto* n : names) fields.push_back({n,'C',128,0});
    return fields;
}
void corrupt(const fs::path& file, std::size_t offset, unsigned char value) {
    std::fstream out(file,std::ios::in|std::ios::out|std::ios::binary);
    out.seekp(static_cast<std::streamoff>(offset));out.put(static_cast<char>(value));
    require(bool(out), "write deliberate fixture corruption");
}
}
int main(int argc, char** argv) {
    try {
        if (argc == 3 && std::string(argv[1]) == "--command") {
            xbase::DbArea area;
            std::istringstream command(argv[2]);
            cmd_DDICT(area, command);
            return 0;
        }
        if (argc == 3 && std::string(argv[1]) == "--inspect") {
            auto view = read_catalog_view(argv[2]);
            for (const auto& table : view.physical_tables)
                std::cout << table.family << ' ' << table.physical_name << " state=" << int(table.state)
                          << " rows=" << table.rows << " logical=" << table.logical_name << '\n';
            for (const auto& d : view.diagnostics) std::cout << "REVIEW " << d << '\n';
            require(view.rows("DDOBJECT").size() > 0, "live catalog contains objects");
            for (const auto& key : {"DDOBJECT","DDATTR","DDEDGE","DDEVID"})
                std::cout << "VIEW " << key << ' ' << view.rows(key).size() << '\n';
            for (const auto& ev : view.rows("DDEVID"))
                std::cout << "MEMO " << value_of(ev,"_DD_FAMILY") << ' ' << value_of(ev,"_DD_ID")
                          << " bytes=" << value_of(ev,"DETAIL").size() << '\n';
            return view.diagnostics.empty() ? 0 : 2;
        }
        const auto stamp = std::chrono::high_resolution_clock::now().time_since_epoch().count();
        const fs::path root = fs::path(DDICT_TEST_ROOT)/std::to_string(stamp);
        require(fs::create_directories(root), "isolated fixture directory");
        std::cout << "FIXTURES " << root.string() << '\n';
        const std::string file = "DATA_DICTIONARY_DOGFOOD_LONG_PHYSICAL_FILENAME";
        const std::string logical = "DATA_DICTIONARY_DOGFOOD_DIFFERENT_LONG_TABLE_IDENTITY";
        const std::string field1 = "CATALOG_DOGFOOD_LONG_FIELD_FIRST";
        const std::string field2 = "CATALOG_DOGFOOD_LONG_FIELD_SECOND";
        const std::string longvalue(1024,'W');
        std::vector<std::vector<std::string>> records(13,{"first",longvalue});
        create(root,file,logical,{{field1,'C',128,0},{field2,'C',1024,0}},records);
        auto read = read_dbf_table_checked(root,file);
        require(read.state == TableReadState::Ready, "checked read native long-name file: " + read.error);
        require(read.logical_name == logical, "long table name independent of filename");
        require(read.rows.size()==13, "13 records use x64 geometry, not phantom descriptors");
        require(read.fields[1].width==1024 && read.rows[0].at(field2)==longvalue,
                "authoritative width above 255, without truncation");
        require(read.rows[0].at(field1)=="first", "two fields sharing first ten characters remain distinct");
        require(read_dbf_table_checked(root,"ABSENT").state==TableReadState::Missing,"missing distinct from empty");
        create(root,"EMPTY","LONG_EMPTY_TABLE",{{"LONG_EMPTY_FIELD",'C',20,0}},{});
        require(read_dbf_table_checked(root,"EMPTY").state==TableReadState::Ready,"valid empty native table");
        fs::copy_file(root/(file+".dbf"),root/"BAD.dbf");
        corrupt(root/"BAD.dbf",40,0xff);
        require(read_dbf_table_checked(root,"BAD").state==TableReadState::Error,"reject malformed record geometry");
        fs::copy_file(root/(file+".dbf"),root/"TRUNCATED.dbf");
        fs::resize_file(root/"TRUNCATED.dbf",120);
        require(read_dbf_table_checked(root,"TRUNCATED").state==TableReadState::Error,"reject truncated table");

        create(root,"DDOBJECT","LEGACY_OBJECT_CATALOG",chars({"OBJID","OBJTYPE","NAME","OWNER","STATUS","PROFILE","SRCID"}),
            {{"same-id","CATALOG_TABLE","LEGACY_TABLE","","READY","ENGINE","same-source"}});
        create(root,"DATA_DICTIONARY_OBJECTS","DATA_DICTIONARY_OBJECTS",
            chars({"CATALOG_OBJECT_ID","CATALOG_OBJECT_TYPE","CATALOG_OBJECT_NAME","CATALOG_OWNER_NAME","CATALOG_STATUS_CODE","CATALOG_PROFILE_CODE","SOURCE_ARTIFACT_ID"}),
            {{"same-id","COMMAND_SURFACE","A_VERY_LONG_COMMAND_SURFACE_NAME","DDICT","READY","ENGINE","same-source"}});
        auto attributes=chars({"CATALOG_ATTRIBUTE_ID","CATALOG_OBJECT_ID","CATALOG_ATTRIBUTE_NAME","CATALOG_ATTRIBUTE_VALUE"});
        attributes.push_back({"CATALOG_ATTRIBUTE_DETAIL",'M',8,0});
        attributes.push_back({"EVIDENCE_RECORD_ID",'C',128,0});
        // DbArea::set stores raw x64 memo ids. Populate the DTX with the native
        // MemoStore and pass its id through the native record writer below.
        const std::string memo_text="Native x64base dogfood memo with full long-name catalog detail.";
        create(root,"DATA_DICTIONARY_OBJECT_ATTRIBUTES","DATA_DICTIONARY_OBJECT_ATTRIBUTES",attributes,
            {{"attr-id","same-id","A_VERY_LONG_ATTRIBUTE_NAME","","","ev-id"}});
        const auto memo_path=root/"DATA_DICTIONARY_OBJECT_ATTRIBUTES.dtx";
        dottalk::memo::MemoStore writer;
        require(writer.open(memo_path.string(),dottalk::memo::OpenMode::CreateIfMissing).ok,"native DTX open");
        std::string why;
        const auto memo_id=writer.put_text_id(memo_text,&why);
        require(memo_id!=0,"native DTX memo write: "+why);
        writer.close();
        { xbase::DbArea area; area.open((root/"DATA_DICTIONARY_OBJECT_ATTRIBUTES.dbf").string());
          require(area.top(),"native memo row navigation");
          require(area.set(5,std::to_string(memo_id)),"native memo reference set");
          require(area.writeCurrent(),"native memo reference write"); area.close(); }
        create(root,"DATA_DICTIONARY_RELATION_EDGES","DATA_DICTIONARY_RELATION_EDGES",
            chars({"RELATION_EDGE_ID","RELATION_FROM_OBJECT_ID","RELATION_TO_OBJECT_ID","RELATION_EDGE_TYPE","EVIDENCE_RECORD_ID"}),
            {{"edge-id","same-id","attr-id","HAS_CATALOG_ATTRIBUTE","ev-id"}});
        auto evidence=chars({"EVIDENCE_RECORD_ID","CATALOG_OBJECT_ID","SOURCE_ARTIFACT_ID","EVIDENCE_KIND_CODE","EVIDENCE_CONFIDENCE_CODE"});
        evidence.push_back({"EVIDENCE_DETAIL_TEXT",'M',8,0});
        create(root,"DATA_DICTIONARY_EVIDENCE_RECORDS","DATA_DICTIONARY_EVIDENCE_RECORDS",evidence,
            {{"ev-id","same-id","same-source","NATIVE_DOGFOOD","HIGH",""}});
        const auto before=read_binary(memo_path);
        const auto time_before=fs::last_write_time(memo_path);
        { dottalk::memo::MemoStore ro;
          require(ro.open_read_only(memo_path.string()).ok,"DTX read-only open");
          std::string text;
          require(ro.get_text_id(memo_id,text,&why) && text==memo_text,"DTX read-only exact memo content");
          require(!ro.put_text("forbidden").ok,"DTX read-only rejects append");
          require(!ro.erase_id(memo_id,&why),"DTX read-only rejects erase");
          std::uint64_t next=0;
          require(!ro.update_text_id(memo_id,"forbidden",next,&why),"DTX read-only rejects update");
          dottalk::memo::MemoStore moved(std::move(ro));
          require(moved.flush().ok,"DTX read-only moved flush is no-op"); }
        auto view=read_catalog_view(root);
        for(const auto& d:view.diagnostics) std::cout<<"REVIEW "<<d<<'\n';
        require(view.diagnostics.empty(),"native fixture catalog has no diagnostics");
        require(view.rows("DDOBJECT").size()==2,"both catalog families retained");
        require(resolve_object(view.rows("DDOBJECT"),"same-id")->at("NAME")=="LEGACY_TABLE","legacy identity remains stable");
        const auto* obj=resolve_object(view.rows("DDOBJECT"),"x64:same-id");
        require(obj && obj->at("NAME")=="A_VERY_LONG_COMMAND_SURFACE_NAME","qualified long-name identity");
        require(obj->at("CATALOG_OBJECT_ID")=="same-id" && obj->at("_DD_FAMILY")=="X64","original identity and family retained");
        require(obj->at("SRCID")=="x64:artifact:same-source","source-artifact domain cannot join DDSOURCE by accident");
        require(view.rows("DDATTR")[0].at("ATTRMEMO")==memo_text,"catalog memo decoded through native DTX");
        require(view.rows("DDATTR")[0].at("_DD_MEMO_STATE:CATALOG_ATTRIBUTE_DETAIL")=="RESOLVED",
                "export distinguishes resolved native memo from null and unavailable");
        require(view.rows("DDEVID")[0].at("_DD_MEMO_STATE:EVIDENCE_DETAIL_TEXT")=="NULL",
                "native null memo carries explicit state");
        std::ostringstream exported, repeated;
        write_catalog_json(view, exported);
        write_catalog_json(view, repeated);
        require(exported.str()==repeated.str(), "native JSON export is deterministic");
        require(exported.str().find("CATALOG_ATTRIBUTE_DETAIL")!=std::string::npos &&
                exported.str().find(memo_text)!=std::string::npos &&
                exported.str().find("x64:same-id")!=std::string::npos,
                "native export retains long names, memo content and qualified identity");
        { auto escaped = view; escaped.tables["DDOBJECT"][0]["NAME"] = "quote\" slash\\ line\n";
          std::ostringstream json; write_catalog_json(escaped,json);
          require(json.str().find("quote\\\" slash\\\\ line\\u000a")!=std::string::npos,
                  "native JSON escapes quotes, backslashes and controls"); }
        require(view.rows("DDEDGE")[0].at("_DD_TO_KIND")=="ATTRIBUTE" && view.rows("DDEDGE")[0].at("_DD_TO_NAME")=="A_VERY_LONG_ATTRIBUTE_NAME","typed relation resolves attribute endpoint");
        require(read_binary(memo_path)==before && fs::last_write_time(memo_path)==time_before,"read-only memo bytes AND write time unchanged");
        const auto command_home = root/"command_home";
        const auto command_catalog = command_home/"data"/"datadict";
        fs::create_directories(command_catalog);
        for (const auto& table : view.physical_tables) for (const auto* extension : {".dbf", ".dtx"}) {
            const auto source = root/(table.physical_name + extension);
            if (fs::exists(source)) fs::copy_file(source,command_catalog/source.filename());
        }
        const auto saved_cwd = fs::current_path();
        // Regression for the 2026-10-09 reporting workflow: inspect the whole
        // catalog, not just the one memo used by the lower-level reader test.
        std::map<fs::path, std::pair<std::vector<unsigned char>, fs::file_time_type>> report_snapshot;
        for (const auto& entry : fs::directory_iterator(command_catalog)) {
            const auto bytes = read_binary(entry.path());
            report_snapshot.emplace(entry.path(), std::make_pair(
                std::vector<unsigned char>(bytes.begin(), bytes.end()), fs::last_write_time(entry.path())));
        }
        fs::current_path(command_home);
        unsigned command_number = 0;
        auto command = [&](const std::string& text) {
            const auto capture = root/("command-output-" + std::to_string(++command_number) + ".txt");
            auto& router = cli::OutputRouter::instance();
            require(router.set_dest_file(capture.string()), "capture real DDICT output");
            router.push_cout_redirect();
            xbase::DbArea unused;
            std::istringstream args(text);
            cmd_DDICT(unused,args);
            router.pop_cout_redirect();
            router.set_dest_console();
            const auto bytes = read_binary(capture);
            return std::string(bytes.begin(),bytes.end());
        };
        auto output = command("FIELDS DATA_DICTIONARY_OBJECTS");
        require(output.find("CATALOG_OBJECT_NAME") != std::string::npos && output.find("Physical schema:") != std::string::npos,
                "real DDICT FIELDS shows long physical field names");
        output = command("OBJECTS FAMILY X64");
        require(output.find("A_VERY_LONG_COMMAND_SURFACE_NAME") != std::string::npos && output.find("LEGACY_TABLE") == std::string::npos,
                "real DDICT OBJECTS scopes family and preserves long names");
        output = command("EVIDENCE x64:same-id");
        require(output.find(memo_text) != std::string::npos,"real DDICT EVIDENCE displays full memo text");
        output = command("REL x64:same-id OUT");
        require(output.find("A_VERY_LONG_ATTRIBUTE_NAME") != std::string::npos && output.find("ATTRIBUTE") != std::string::npos,
                "real DDICT REL displays typed attribute endpoint");
        output = command("TAGS DATA_DICTIONARY_OBJECTS");
        require(output.find("PHYSICAL_TAGS_FOUND") == std::string::npos && output.find("NO_CATALOG_TAGS_FOUND") != std::string::npos,
                "real DDICT TAGS does not count a DBF as an index");
        output = command("HELP");
        require(output.find("FAMILY LEGACY|X64") != std::string::npos,"real DDICT HELP documents family selection");
        output = command("STATUS");
        require(output.find("X64=") != std::string::npos, "real DDICT STATUS reports catalog families");
        output = command("TABLES");
        require(output.find("DATA_DICTIONARY_OBJECT_ATTRIBUTES") != std::string::npos,
                "real DDICT TABLES preserves long physical filenames");
        std::size_t remaining_files = 0;
        for (const auto& entry : fs::directory_iterator(command_catalog)) {
            ++remaining_files;
            require(report_snapshot.count(entry.path()) == 1, "reporting creates no catalog files");
        }
        require(remaining_files == report_snapshot.size(), "reporting preserves catalog file membership");
        for (const auto& [path, snapshot] : report_snapshot) {
            const auto bytes = read_binary(path);
            require(std::vector<unsigned char>(bytes.begin(), bytes.end()) == snapshot.first &&
                    fs::last_write_time(path) == snapshot.second,
                    "all DDICT reports preserve bytes and write time: " + path.filename().string());
        }
        const auto command_memo = command_catalog/"DATA_DICTIONARY_OBJECT_ATTRIBUTES.dtx";
        fs::rename(command_memo, root/"command_memo_saved.dtx");
        output = command("EVIDENCE x64:same-id");
        require(output.find("unavailable") != std::string::npos && output.find(memo_text) == std::string::npos,
                "real DDICT EVIDENCE diagnoses missing memo without stale text");
        output = command("STATUS");
        require(output.find("CATALOG_REVIEW") != std::string::npos,
                "real DDICT STATUS surfaces missing memo review");
        require(!fs::exists(command_memo), "real DDICT reports never recreate missing memo sidecar");
        fs::current_path(saved_cwd);
        fs::rename(memo_path,root/"saved_memo.dtx");
        view=read_catalog_view(root);
        require(!view.diagnostics.empty() && view.rows("DDATTR")[0].at("ATTRMEMO").find("unavailable")!=std::string::npos,"missing memo is explicit, never pointer text");
        require(!fs::exists(memo_path),"inspection never creates missing sidecar");
        require(view.rows("DDATTR")[0].at("_DD_MEMO_STATE:CATALOG_ATTRIBUTE_DETAIL")=="UNAVAILABLE",
                "missing sidecar exports unavailable state");
        std::size_t memo_cell = 0;
        { xbase::DbArea area; area.open((root/"DATA_DICTIONARY_OBJECT_ATTRIBUTES.dbf").string());
          memo_cell = static_cast<std::size_t>(area.dataStart64()) + 1 + 4 * 128;
          area.close(); }
        { std::fstream out(root/"DATA_DICTIONARY_OBJECT_ATTRIBUTES.dbf",std::ios::in|std::ios::out|std::ios::binary);
          out.seekp(static_cast<std::streamoff>(memo_cell)); out.write("        ",8); }
        view=read_catalog_view(root);
        require(view.rows("DDATTR")[0].at("ATTRMEMO")=="[invalid memo link: space-filled]",
                "space-filled imported links are diagnosed, not treated as null or memo text");
        require(view.rows("DDATTR")[0].at("_DD_MEMO_STATE:CATALOG_ATTRIBUTE_DETAIL")=="INVALID",
                "space-filled memo exports invalid state");
        const auto bad_schema = root/"bad_schema";
        fs::create_directories(bad_schema);
        create(bad_schema,"DDOBJECT","BAD_SCHEMA_OBJECTS",chars({"OBJID"}),{{"id-only"}});
        auto bad_view = read_catalog_view(bad_schema);
        require(bad_view.rows("DDOBJECT").empty() && !bad_view.diagnostics.empty(),
                "present legacy table with missing required fields is rejected explicitly");
        std::cout<<"PASS TOTAL "<<checks<<'\n';
        return 0;
    } catch (const std::exception& e) { std::cerr<<"FAIL "<<e.what()<<'\n';return 1; }
}
