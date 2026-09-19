// @dottalk.file v1
// subsystem: gui
// layer: test
// owns: native table paging and memo readback proof
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#include "workbench_session.hpp"
#include "xbase.hpp"
#include "xbase/dbf_create.hpp"
#include "cli/table_object.hpp"
#include "memo/memostore.hpp"
#include <fstream>
#include <iostream>
namespace fs = std::filesystem;
using namespace dottalk::workbench;
void require(bool value, const std::string& why) { if (!value) throw std::runtime_error(why); }
std::string bytes(const fs::path& path) {
    std::ifstream in(path, std::ios::binary); return {std::istreambuf_iterator<char>(in), {}};
}
int main() {
    try {
        {
            xbase::XBaseEngine engine;
            constexpr std::uint64_t high = 0x100000007ULL;
            dottalk::table::set_enabled(4, true);
            dottalk::table::get_tb(4).add_change(high, dottalk::table::CHANGE_UPDATE, nullptr, 1, "wide record");
            dottalk::table::Table table(engine, 4);
            require(table.overlay_for(high).new_values.at(1) == "wide record" && !table.overlay_for(7).has,
                "overlay preserves all 64 record bits");
            dottalk::table::reset_all();
        }
        const auto root = fs::temp_directory_path() / ("workbench table " + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
        require(fs::create_directory(root), "fixture directory");
        const auto source = root / "PEOPLE.dbf", sidecar = root / "PEOPLE.dtx";
        std::string error;
        require(xbase::dbf_create::create_dbf(source.string(), {{"NAME", 'C', 24}, {"NOTE", 'M', 16}, {"NUMBER", 'N', 8}},
            xbase::dbf_create::Flavor::X64, error), error);
        {
            dottalk::memo::MemoStore memo;
            require(memo.open(sidecar.string(), dottalk::memo::OpenMode::CreateIfMissing).ok, "create memo store");
            xbase::DbArea area; area.open(source.string());
            for (int n = 1; n <= 205; ++n) {
                std::string value = "Workbench memo record " + std::to_string(n) + "\nSecond line";
                if (n == 203) value = std::string("binary\0payload", 14);
                if (n == 204) value.assign(70000, 'x');
                if (n == 205) value.assign(1024 * 1024 + 1, 'y');
                const auto stored = memo.put_text(value); require(stored.ok, "memo fixture");
                require(area.appendBlank() && area.set(1, "Person " + std::to_string(n)) && area.set(2, stored.ref.token) &&
                    area.set(3, std::to_string(n)) && area.writeCurrent(), "row fixture");
            }
        }
        const auto original = bytes(source), original_memo = bytes(sidecar);
        WorkbenchSession session;
        auto run = [&](Request request) {
            auto value = session.submit(std::move(request)).get();
            require(value.ok(), value.error + "\n" + value.transcript);
            require(value.table.error.empty(), value.table.error); return value;
        };
        auto command = [&](const std::string& line) { Request r; r.action = Action::Command; r.name = line; return run(r); };
        Request open; open.action = Action::OpenCopy; open.path = source; auto s = run(open);
        command("GO 7"); s = command("BROWSE");
        require(s.browse_requested && s.table.rows.size() == 100 && s.table.more && s.table.current_record == 7 &&
            s.table.rows.front().recno == 1 && s.table.rows.back().recno == 100, "BROWSE first page and cursor");
        const auto slot = s.table.slot; const auto handle = s.table.area_handle;
        Request page; page.action = Action::Browse; page.area_handle = handle; page.offset = 100;
        s = run(page); require(s.table.rows.size() == 100 && s.table.rows[0].recno == 101 && s.table.current_record == 7, "second page");
        page.offset = 200; s = run(page);
        require(s.table.rows.size() == 5 && !s.table.more && s.table.rows.back().recno == 205, "last partial page");
        auto value = [&](std::uint64_t record) { return session.inspect_field(slot, handle, record, 2, "NOTE").get(); };
        auto memo = value(7); require(memo.error.empty() && memo.memo && memo.text == "Workbench memo record 7\nSecond line", "memo resolution");
        memo = value(203); require(memo.error.empty() && memo.binary && memo.text.find("00") != std::string::npos, "binary memo hex");
        memo = value(204); require(memo.error.empty() && memo.truncated && memo.bytes == 70000, "bounded text preview");
        require(!value(205).error.empty(), "oversized memo refused before read");
        require(!session.inspect_field(slot, handle, 7, 2, "WRONG").get().error.empty(), "stale field refused");
        require(session.submit().get().table.current_record == 7, "memo reads preserve cursor");
        s = command("SET FILTER TO NUMBER > 200");
        require(s.table.filtered && s.table.rows.size() == 5 && s.table.rows.front().recno == 201, "filter matches visible rows");
        command("SET FILTER TO"); command("SET DELETED ON"); command("GO 1"); s = command("DELETE");
        require(s.table.rows.front().recno == 2, "deleted visibility");
        s = command("SET DELETED OFF"); require(s.table.rows.front().deleted, "deleted marker");
        command("RECALL"); command("GO 7"); command("TABLE ON"); s = command("REPLACE NAME WITH 'Buffered name'");
        require(s.table.rows[6].pending && s.table.rows[6].values[0] == "Buffered name", "pending buffered values");
        auto field = session.inspect_field(slot, handle, 7, 1, "NAME").get();
        require(field.pending && field.text == "Buffered name", "field inspector overlays buffer");
        command("REPLACE NOTE WITH 'Buffered memo'"); memo = value(7);
        require(memo.error.empty() && memo.pending && memo.text == "Buffered memo", "memo inspector overlays buffer");
        s = command("ROLLBACK"); require(!s.table.rows[6].pending && s.table.rows[6].values[0] == "Person 7", "rollback refresh");
        command("REPLACE NAME WITH 'Committed name'"); s = command("COMMIT");
        require(!s.table.rows[6].pending && s.table.rows[6].values[0] == "Committed name", "commit refresh");
        command("TABLE OFF");
        command("CDX CREATE"); command("CDX ADDTAG NUMBER"); command("BUILDLMDB YES");
        s = command("SET ORDER PEOPLE.cdx NUMBER DESC");
        // Current BUILDLMDB encodes N keys as right-padded display strings, so
        // this fixture is lexical (99 before 205). Preserve the engine order.
        require(s.table.rows.front().recno == 99 && s.table.rows.back().recno == 194, "descending index order: " + s.transcript +
            "first=" + std::to_string(s.table.rows.front().recno) + " last=" + std::to_string(s.table.rows.back().recno) + " order=" + s.table.order);
        require(command("LIST TOP 1").transcript.find("Person 99") != std::string::npos, "grid agrees with LIST on CDX order");
        command("SET ORDER NATURAL");
        Request select; select.action = Action::SelectRecord; select.slot = slot; select.area_handle = handle; select.record = 42;
        s = run(select); require(s.table.current_record == 42, "explicit select record");
        s = command("CLOSE"); require(!s.table.open && s.table.rows.empty(), "closed area clears view");
        require(!value(7).error.empty(), "closed area stale identity refused");
        require(!session.submit(select).get().ok(), "stale navigation refused");
        const auto edit_source = root / "EDIT.dbf";
        require(xbase::dbf_create::create_dbf(edit_source.string(), {{"TEXT", 'C', 60}, {"AMOUNT", 'N', 8, 2},
            {"DAY", 'D', 8}, {"ACTIVE", 'L', 1}, {"PRECISE", 'B', 8}, {"KEY", 'C', 20}},
            xbase::dbf_create::Flavor::X64, error), error);
        {
            xbase::DbArea area; area.open(edit_source.string());
            for (int n = 1; n <= 2; ++n) require(area.appendBlank() && area.set(1, "original") && area.set(2, "1.25") &&
                area.set(3, "20260918") && area.set(4, "T") && area.set(5, "3.140625") &&
                area.set(6, "key" + std::to_string(n)) && area.writeCurrent(), "edit fixture");
        }
        const auto source_before_edit = bytes(edit_source);
        open.path = edit_source; s = run(open);
        const auto edit_slot = s.table.slot; const auto edit_handle = s.table.area_handle;
        fs::path edit_copy;
        for (const auto& area : s.areas) if (area.slot == edit_slot) edit_copy = area.path;
        const auto copy_before_edit = bytes(edit_copy);
        auto edit_request = [&](int f, std::string text) {
            const auto current = session.inspect_field(edit_slot, edit_handle, 1, f, s.table.fields[f - 1].name).get();
            require(current.error.empty(), current.error);
            Request r; r.action = Action::EditField;
            r.edit = {edit_slot, f, edit_handle, 1, s.table.fields[f - 1].name, current.text, std::move(text)};
            return r;
        };
        auto edit_finish = [&](Action action) {
            Request r; r.action = action; r.slot = edit_slot; r.area_handle = edit_handle; return run(r);
        };
        command("GO 2");
        const std::string literal = "O'Brien &amount; QUIT\nsecond line";
        auto stale_edit = edit_request(1, "stale edit");
        s = run(edit_request(1, literal));
        require(s.table.buffered && s.table.pending_records == 1 && s.table.current_record == 2 &&
            session.inspect_field(edit_slot, edit_handle, 1, 1, "TEXT").get().text == literal, "literal buffered editor preserves cursor");
        require(bytes(edit_copy) == copy_before_edit, "stage does not change physical DBF");
        require(!session.submit(stale_edit).get().ok(), "stale original value refused");
        require(!session.submit(edit_request(1, std::string(61, 'x'))).get().ok(), "overwidth text refused");
        require(!session.submit(edit_request(2, "12.5 GARBAGE")).get().ok(), "invalid numeric refused");
        require(!session.submit(edit_request(4, "maybe")).get().ok(), "invalid logical refused");
        s = run(edit_request(2, "42.75")); s = run(edit_request(3, "02/14/1956"));
        s = run(edit_request(4, "false")); s = run(edit_request(5, "3.140625"));
        require(s.table.rows[0].values[1] == "42.75" && s.table.rows[0].values[2] == "19560214" &&
            s.table.rows[0].values[3] == "F", "canonical types in buffer");
        s = edit_finish(Action::RollbackTable);
        require(s.table.pending_records == 0 && s.table.rows[0].values[0] == "original" && bytes(edit_copy) == copy_before_edit,
            "native rollback restores original without disk edits");
        command("SET UNIQUE FIELD KEY PRIMARY");
        require(!session.inspect_field(edit_slot, edit_handle, 1, 6, "KEY").get().editable, "primary key editor disabled");
        require(!session.submit(edit_request(6, "tampered")).get().ok(), "primary key write gate enforced");
        command("SET MODE SQL"); command("BEGIN");
        require(!session.submit(edit_request(1, "inside SQL transaction")).get().ok(), "editor refuses SQL transaction");
        Request unsafe_commit; unsafe_commit.action = Action::CommitTable; unsafe_commit.slot = edit_slot; unsafe_commit.area_handle = edit_handle;
        require(!session.submit(unsafe_commit).get().ok(), "native commit refuses SQL transaction");
        command("ROLLBACK"); command("SET MODE NATIVE");
        s = run(edit_request(1, literal)); s = run(edit_request(2, "42.75"));
        Request peer; peer.action = Action::NewWorkspace; peer.name = "EditPeer"; run(peer);
        command("SWITCH EditPeer");
        open.path = source; const auto peer_snapshot = run(open);
        Request peer_edit; peer_edit.action = Action::EditField;
        peer_edit.edit = {peer_snapshot.table.slot, 1, peer_snapshot.table.area_handle, 1, "NAME", "Person 1", "Peer edit"};
        run(peer_edit);
        require(!session.submit(unsafe_commit).get().ok(), "commit cannot target a previously selected area");
        Request select_edit; select_edit.action = Action::SelectArea; select_edit.slot = edit_slot; select_edit.area_handle = edit_handle;
        s = run(select_edit); s = edit_finish(Action::CommitTable);
        require(s.table.pending_records == 0 && s.dirty_areas == 1, "commit touches only selected table");
        command("CLOSE"); s = command("USE " + edit_copy.string());
        require(s.table.open && !s.table.rows.empty(), "reopen selected edit copy " + edit_copy.string() + ": " + s.transcript);
        const auto reopened_value = session.inspect_field(s.table.slot, s.table.area_handle, 1, 1, "TEXT").get();
        require(reopened_value.text == literal && s.table.rows[0].values[1] == "42.75",
            "committed literal and numeric survive reopen: value=[" + reopened_value.text + "] error=[" + reopened_value.error +
            "] amount=[" + s.table.rows[0].values[1] + "] " + s.transcript);
        Request select_peer; select_peer.action = Action::SelectArea; select_peer.slot = peer_snapshot.table.slot; select_peer.area_handle = peer_snapshot.table.area_handle;
        const auto retained_peer = run(select_peer);
        require(retained_peer.table.pending_records == 1 && retained_peer.table.rows[0].values[0] == "Peer edit", "peer buffer remains intact");
        select_peer.action = Action::RollbackTable; run(select_peer);
        require(bytes(edit_source) == source_before_edit, "original edit source preserved");
        // M3 uses the exact command route, stable area identity and native buffers.
        auto operation = [&](const std::string& name, const std::string& input = "", std::uint64_t record = 0) {
            Request r; r.action = Action::TableCommand; r.name = name; r.payload = input;
            r.slot = s.table.slot; r.area_handle = s.table.area_handle; r.record = record; return r;
        };
        s = run(select_peer); command("TABLE OFF");
        s = run(operation("last")); require(s.table.current_record == 205 && s.table.offset == 200, "M3 last record page");
        s = run(operation("first")); require(s.table.current_record == 1, "M3 first record");
        s = run(operation("forward")); require(s.table.current_record == 2, "M3 next record");
        s = run(operation("back")); require(s.table.current_record == 1, "M3 previous record");
        s = run(operation("filter", "NUMBER > 200")); require(s.table.rows.size() == 5, "M3 filter");
        s = run(operation("filter"));
        command("CDX CREATE"); command("CDX ADDTAG NUMBER"); command("BUILDLMDB YES");
        s = run(operation("order", "PEOPLE.cdx NUMBER ASC"));
        s = run(operation("seek", "42")); require(s.table.current_record == 42, "M3 seek matches native index: " + s.transcript + " order=" + s.table.order + " record=" + std::to_string(s.table.current_record));
        require(!session.submit(operation("seek", "'Person 42'")).get().ok(), "M3 unsupported spaced key explained");
        s = run(operation("order")); s = run(operation("go", "", 7)); require(s.table.current_record == 7, "M3 go");
        Request stale = operation("delete", "", 7); stale.area_handle += 100000;
        require(!session.submit(stale).get().ok(), "M3 stale record operation refused");
        fs::path peer_copy; for (const auto& a : s.areas) if (a.handle == s.table.area_handle) peer_copy = a.path;
        const auto before_delete = bytes(peer_copy);
        s = run(operation("delete", "", 7)); require(s.table.rows[6].delete_pending && bytes(peer_copy) == before_delete, "M3 delete only buffered");
        require(!session.submit(operation("append")).get().ok() && !session.submit(operation("recall", "", 7)).get().ok(), "M3 unsupported buffered operations refused");
        Request typed; typed.action = Action::Command; typed.name = "APPEND BLANK";
        require(!session.submit(typed).get().ok() && bytes(peer_copy) == before_delete, "M3 typed append respects TABLE ON guard");
        Request finish; finish.action = Action::RollbackTable; finish.slot = s.table.slot; finish.area_handle = s.table.area_handle;
        s = run(finish); require(!s.table.rows[6].delete_pending && bytes(peer_copy) == before_delete, "M3 deletion rollback");
        command("TABLE OFF"); s = run(operation("append")); require(s.table.records == 206, "M3 explicit TABLE OFF append");
        s = run(operation("delete", "", 206)); finish.action = Action::CommitTable; s = run(finish);
        command("TABLE OFF"); s = run(operation("recall", "", 206)); require(!s.table.rows.back().deleted, "M3 explicit recall");

        const auto memo_source = root / "MEMOEDIT.dbf";
        require(xbase::dbf_create::create_dbf(memo_source.string(), {{"TOKEN", 'M', 16}, {"FIXED", 'M', 8}}, xbase::dbf_create::Flavor::X64, error), error);
        {
            dottalk::memo::MemoStore store;
            require(store.open((root / "MEMOEDIT.dtx").string(), dottalk::memo::OpenMode::CreateIfMissing).ok, "M3 memo store");
            const auto put = store.put_text("shared original"); std::uint64_t id{};
            require(put.ok && store.try_object_id_from_ref(put.ref, id), "M3 initial memo");
            xbase::DbArea a; a.open(memo_source.string());
            for (int i = 0; i < 2; ++i) require(a.appendBlank() && a.set(1, put.ref.token) && a.set(2, std::to_string(id)) && a.writeCurrent(), "M3 shared reference fixture");
        }
        const auto memo_original = bytes(memo_source), memo_sidecar_original = bytes(root / "MEMOEDIT.dtx");
        open.path = memo_source; s = run(open);
        fs::path memo_copy; for (const auto& a : s.areas) if (a.handle == s.table.area_handle) memo_copy = a.path;
        const auto memo_copy_before = bytes(memo_copy);
        auto memo_edit = [&](int field, const std::string& text) {
            const auto name = field == 1 ? "TOKEN" : "FIXED";
            const auto current = session.inspect_field(s.table.slot, s.table.area_handle, 1, field, name).get();
            require(current.error.empty() && current.editable, "M3 memo editable: " + current.error + current.edit_reason);
            Request r; r.action = Action::EditField;
            r.edit = {s.table.slot, field, s.table.area_handle, 1, name, current.text, text}; return r;
        };
        const auto stale_memo = memo_edit(1, "stale");
        for (int field : {1, 2}) s = run(memo_edit(field, "M3 memo\n'quoted' & literal"));
        require(bytes(memo_copy) == memo_copy_before, "M3 memo references remain uncommitted");
        require(!session.submit(stale_memo).get().ok(), "M3 stale memo edit refused");
        require(session.inspect_field(s.table.slot, s.table.area_handle, 2, 1, "TOKEN").get().text == "shared original" &&
                session.inspect_field(s.table.slot, s.table.area_handle, 2, 2, "FIXED").get().text == "shared original", "M3 shared memo not overwritten");
        finish.slot = s.table.slot; finish.area_handle = s.table.area_handle; finish.action = Action::RollbackTable; s = run(finish);
        require(session.inspect_field(s.table.slot, s.table.area_handle, 1, 2, "FIXED").get().text == "shared original", "M3 memo rollback");
        for (int field : {1, 2}) s = run(memo_edit(field, "M3 committed memo"));
        s = run(memo_edit(1, "M3 second buffered edit"));
        finish.action = Action::CommitTable; s = run(finish); command("CLOSE"); s = command("USE " + memo_copy.string());
        require(session.inspect_field(s.table.slot, s.table.area_handle, 1, 1, "TOKEN").get().text == "M3 second buffered edit" &&
                session.inspect_field(s.table.slot, s.table.area_handle, 1, 2, "FIXED").get().text == "M3 committed memo", "M3 both memo formats survive commit and reopen");
        s = run(memo_edit(2, "")); finish.slot = s.table.slot; finish.area_handle = s.table.area_handle; s = run(finish);
        require(session.inspect_field(s.table.slot, s.table.area_handle, 1, 2, "FIXED").get().text.empty(), "M3 empty memo commits");
        require(bytes(memo_source) == memo_original && bytes(root / "MEMOEDIT.dtx") == memo_sidecar_original, "M3 source memo family unchanged");
        const auto nullable = root / "NULLTEST.dbf";
        require(xbase::dbf_create::create_dbf(nullable.string(), {{"NAME", 'C', 12, 0, "", true}}, xbase::dbf_create::Flavor::VFP, error), error);
        { xbase::DbArea a; a.open(nullable.string()); require(a.appendBlank() && a.set(1, "not null") && a.writeCurrent(), "M3 nullable fixture"); }
        open.path = nullable; s = run(open);
        Request make_null; make_null.action = Action::SetNullField;
        make_null.edit = {s.table.slot, 1, s.table.area_handle, 1, "NAME", "not null", ""};
        command("TABLE ON"); require(!session.submit(make_null).get().ok(), "M3 NULL refuses buffer mode");
        command("TABLE OFF"); s = run(make_null);
        const auto null_value = session.inspect_field(s.table.slot, s.table.area_handle, 1, 1, "NAME").get();
        require(null_value.error.empty() && null_value.text == ".NULL.", "M3 explicit native NULL readback: " + null_value.text);
        session.shutdown();
        require(bytes(source) == original && bytes(sidecar) == original_memo, "source fixture bytes unchanged");
        std::cout << "PASS table paging, order/filter/deleted, cursor, buffer, memo, stale identity and 64-bit overlay\n"
                  << "table_source=" << source.string() << '\n';
        std::cout << "PASS native value editor: literal text, validation, stale edits, buffer readback, rollback, commit/reopen, primary gate, SQL guard and peer isolation\n";
        std::cout << "PASS M3: record controls, filter/order/seek, TABLE ON refusal, buffered delete/rollback, explicit TABLE OFF append/recall, token/fixed memo edit/rollback/commit/reopen, shared references and native NULL\n";
        return 0;
    } catch (const std::exception& e) { std::cerr << "FAIL " << e.what() << '\n'; return 1; }
}
