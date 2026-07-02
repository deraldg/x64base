/*
    Registration Policy
    -------------------

    This file is the central, explicit registry for built-in DotTalk++ CLI
    commands. The shell should be able to answer one basic question by reading
    this file: "what command names are built in, and which handler owns each
    one?"

    Built-in CLI commands are registered here. Do not self-register built-in
    commands elsewhere; otherwise startup order, duplicate names, help/reflection,
    and command-audit tooling become harder to reason about.

    Custom/student commands are the exception. Those may self-register from the
    extension/custom area so experiments do not keep expanding this core registry.

    Expression/function families, such as string/date/numeric functions, are
    governed separately by the function catalog system. They may self-register
    through that catalog because they are not shell commands.

    Important architectural rule:
      - This file wires commands to handlers.
      - It should not contain command implementations.
      - Cross-cutting policy may appear here only as wrapper behavior, such as
        dirty prompts or relation refresh after a mutation.
*/
// src/cli/shell_commands.cpp
// DotTalk++: Extracted command registry (was previously embedded in shell.cpp)

#include "shell_commands.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>

#include "shell_api.hpp"               // shell_dispatch_line() decl
#include "cli/command_registry.hpp"    // dli::registry()
#include "set_relations.hpp"           // relations_api::refresh_if_enabled()
#include "cli/order_state.hpp"         // orderstate helpers
#include "cli/dirty_prompt.hpp"        // dirty prompt wrappers

#include "xbase.hpp"
#include "cli/cmd_quit.hpp"

using xbase::DbArea;

// Exported registration entry point used by shell startup. extern "C" keeps
// the symbol name stable while the implementation still uses C++ lambdas.
extern "C" void register_shell_commands(xbase::XBaseEngine& eng, bool include_ui_cmds)
{
    using namespace dli;

    // ---------------------------------------------------------------------
    // Relation-refresh policy
    // ---------------------------------------------------------------------
    // Cursor movement is handled by the engine cursor hook. Ordinary movement
    // commands should not manually refresh relations here. Manual refresh is
    // kept for state changes that may alter relation results without a normal
    // cursor move: open/close/select, relation changes, filters, mutations,
    // and buffer commit/rollback. Observer commands should not refresh.

    // ---------------------------------------------------------------------
    // Work-area open/close/select commands
    // ---------------------------------------------------------------------
    // These commands can change the current table or relation graph. Refresh
    // relations explicitly after they run.

    // With engine cursor hook active, avoid manual refresh on cursor-moving commands.
    // Keep manual refresh for: open/close/select, relation-definition changes, and data mutations.

    registry().add("USE",   [](DbArea& A, std::istringstream& S){
        if (!dottalk::dirty::maybe_prompt_area(A, "USE")) {
            std::cout << "USE canceled.\n";
            return;
        }
        cmd_USE(A,S);
        relations_api::refresh_if_enabled();
    });

    registry().add("CLOSE", [](DbArea& A, std::istringstream& S){
        if (!dottalk::dirty::maybe_prompt_area(A, "CLOSE")) {
            std::cout << "CLOSE canceled.\n";
            return;
        }
        cmd_CLOSE(A,S);
        relations_api::refresh_if_enabled();
    });

    registry().add("SELECT",  [](DbArea& A, std::istringstream& S){
        cmd_SELECT(A,S);
        relations_api::refresh_if_enabled();
    });

    // Developer/debug status command. It reports current area and order state
    // without invoking the full AREA command and without refreshing relations.
    registry().add("AREA51",    [&](DbArea&, std::istringstream&){
        int i = eng.currentArea();
        DbArea& cur = eng.area(i);
        std::cout << "Current area: " << i << "\n";
        if (cur.isOpen()) {
            std::cout << "  File: " << cur.name()
                      << "  Recs: " << cur.recCount()
                      << "  Recno: " << cur.recno() << "\n";
            try {
                bool asc = orderstate::isAscending(cur);
                std::string idx = orderstate::hasOrder(cur) ? orderstate::orderName(cur) : std::string("(none)");
                std::string tag = orderstate::hasOrder(cur) ? orderstate::activeTag(cur) : std::string("(none)");
                std::cout << "  Order: " << (asc ? "ASCEND" : "DESCEND") << "\n"
                          << "  Index file  : " << idx << "\n"
                          << "  Active tag  : " << tag << "\n";
            } catch (...) {}
        } else {
            std::cout << "  (no file open)\n";
        }
    });

    // ---------------------------------------------------------------------
    // Direct cursor movers
    // ---------------------------------------------------------------------
    // These should trigger relation maintenance through the engine cursor hook.
    // Do not add manual refresh calls here unless the hook contract changes.
    // Cursor movers: rely on engine cursor hook (no manual refresh here)
    registry().add("GO",           [](DbArea& A, std::istringstream& S){ cmd_GO(A,S);      });
    registry().add("TOP",          [](DbArea& A, std::istringstream& S){ cmd_TOP(A,S);     });
    registry().add("BOTTOM",       [](DbArea& A, std::istringstream& S){ cmd_BOTTOM(A,S);  });
    registry().add("GOTO",         [](DbArea& A, std::istringstream& S){ cmd_GOTO(A,S);    });
    registry().add("SKIP",         [](DbArea& A, std::istringstream& S){ cmd_SKIP(A,S);    });

    // ---------------------------------------------------------------------
    // Read/report commands that should preserve cursor position
    // ---------------------------------------------------------------------
    // These observe or print data. If one starts moving the cursor, fix that
    // command or route movement through the engine hook rather than adding a
    // registry refresh here.
    // Non-positioning (should preserve cursor): no refresh here
    registry().add("COUNT",        [](DbArea& A, std::istringstream& S){ cmd_COUNT(A,S);    });
    registry().add("LIST",         [](DbArea& A, std::istringstream& S){ cmd_LIST(A,S);     });
    registry().add("LIST_LMDB",    [](DbArea& A, std::istringstream& S){ cmd_LIST_LMDB(A,S);});
    registry().add("DISPLAY",      [](DbArea& A, std::istringstream& S){ cmd_DISPLAY(A,S);  });
    registry().add("GPS",          [](DbArea& A, std::istringstream& S){ cmd_GPS(A,S);      });

    // ---------------------------------------------------------------------
    // Browser-style commands
    // ---------------------------------------------------------------------
    // Browsers may move the active record during navigation. That movement
    // should flow through engine cursor APIs so the hook sees it.
    // Interactive browsers typically move cursor internally; hook covers it.
    registry().add("SIMPLEBROWSE", [](DbArea& A, std::istringstream& S){ cmd_SIMPLE_BROWSER(A,S); });
    registry().add("BROWSE",       [](DbArea& A, std::istringstream& S){ cmd_BROWSE(A,S);         });
    registry().add("RBROWSE",      [](DbArea& A, std::istringstream& S){ cmd_RBROWSE(A,S);        });
    registry().add("ERSATZ",       [](DbArea& A, std::istringstream& S){ cmd_ERSATZ(A,S);         });
    registry().add("HIER",         [](DbArea& A, std::istringstream& S){ cmd_HIER(A,S);           });
    registry().add("BROWSER",      [](DbArea& A, std::istringstream& S){ cmd_BROWSER(A,S);        });
    registry().add("BROWSETUI",    [](DbArea& A, std::istringstream& S){ cmd_BROWSETUI(A,S);      });
    registry().add("SMARTBROWSE",  [](DbArea& A, std::istringstream& S){ cmd_SMART_BROWSER(A,S);  });

    // ---------------------------------------------------------------------
    // TABLE buffering
    // ---------------------------------------------------------------------
    // COMMIT and ROLLBACK can alter visible records, buffered field values,
    // delete state, keys, or relation children, so they refresh explicitly.
    // TABLE buffering
    registry().add("TABLE_BUFFER", [](DbArea& A, std::istringstream& S){ cmd_TABLE_BUFFER(A,S); });
    registry().add("COMMIT",       [](DbArea& A, std::istringstream& S){ cmd_COMMIT(A,S);       relations_api::refresh_if_enabled(); });
    registry().add("ROLLBACK",     [](DbArea& A, std::istringstream& S){ cmd_ROLLBACK(A,S);    relations_api::refresh_if_enabled(); });

    // Filters change visibility without requiring a cursor move. Relation
    // projections may change even when recno is unchanged.
    // Filter changes affect relation results without moving cursor: keep manual refresh
    registry().add("SETFILTER", [](DbArea& A, std::istringstream& S){ cmd_SETFILTER(A,S); relations_api::refresh_if_enabled(); });


    // ---------------------------------------------------------------------
    // Optional Turbo Vision / UI commands
    // ---------------------------------------------------------------------
    // Registered only when TV support exists and caller requested UI commands.
#if defined(DOTTALK_TV_AVAILABLE) && DOTTALK_TV_AVAILABLE
    if (include_ui_cmds) {
        registry().add("TVISION",    [](DbArea& A, std::istringstream& S){ cmd_TVISION(A,S); });
        registry().add("FOXPRO",     [](DbArea& A, std::istringstream& S){ cmd_FOXPRO(A,S); });
        registry().add("FOXTALK",    [](DbArea& A, std::istringstream& S){ cmd_FOXTALK(A,S); });
        registry().add("TURBOTALK",  [](DbArea& A, std::istringstream& S){ cmd_FOXTALK(A,S); });
        registry().add("GENERIC",    [](DbArea& A, std::istringstream& S){ cmd_GENERIC(A,S); });
        registry().add("BROWSETV",   [](DbArea& A, std::istringstream& S){ cmd_BROWSETV(A,S); });
        registry().add("RECORD",     [](DbArea& A, std::istringstream& S){ cmd_RECORD(A,S); });
        registry().add("RECORDVIEW", [](DbArea& A, std::istringstream& S){ cmd_RECORDVIEW(A,S); });
    }
#else
    (void)include_ui_cmds;
#endif

    // ---------------------------------------------------------------------
    // File/import/export/sort utilities
    // ---------------------------------------------------------------------
    // No automatic relation refresh here. If one mutates the open table in
    // place, its command implementation should own the refresh.
    registry().add("COPY",         [](DbArea& A, std::istringstream& S){ cmd_COPY(A,S);   });
    registry().add("EXPORT",       [](DbArea& A, std::istringstream& S){ cmd_EXPORT(A,S); });
    registry().add("IMPORT",       [](DbArea& A, std::istringstream& S){ cmd_IMPORT(A,S); });
    registry().add("AUTODBF",      [](DbArea& A, std::istringstream& S){ cmd_AUTODBF(A,S); });
    registry().add("SORT",         [](DbArea& A, std::istringstream& S){ cmd_SORT(A,S);   });

    // ---------------------------------------------------------------------
    // Core table mutations
    // ---------------------------------------------------------------------
    // These can change keys, deleted visibility, record count, or relation
    // membership without an ordinary cursor move. Refresh after each handler.
    // Data mutations: keep manual refresh (keys/visibility can change without cursor move)
    registry().add("APPEND",       [](DbArea& A, std::istringstream& S){ cmd_APPEND(A,S);       relations_api::refresh_if_enabled(); });
    registry().add("APPEND_BLANK", [](DbArea& A, std::istringstream& S){ cmd_APPEND_BLANK(A,S); relations_api::refresh_if_enabled(); });
    registry().add("DELETE",       [](DbArea& A, std::istringstream& S){ cmd_DELETE(A,S);       relations_api::refresh_if_enabled(); });
    registry().add("RECALL",       [](DbArea& A, std::istringstream& S){ cmd_RECALL(A,S);       relations_api::refresh_if_enabled(); });
    registry().add("UNDELETE",     [](DbArea& A, std::istringstream& S){ cmd_RECALL(A,S);       relations_api::refresh_if_enabled(); });
    registry().add("PACK",         [](DbArea& A, std::istringstream& S){ cmd_PACK(A,S);         relations_api::refresh_if_enabled(); });
    registry().add("TURBOPACK",    [](DbArea& A, std::istringstream& S){ cmd_TURBOPACK(A,S);    relations_api::refresh_if_enabled(); });

    // ---------------------------------------------------------------------
    // Schema/field/rule inspection and validation
    // ---------------------------------------------------------------------
    // These mostly inspect metadata or validation state. Structure-changing
    // commands should handle their own state updates internally.
    registry().add("FIELDS",       [](DbArea& A, std::istringstream& S){ cmd_FIELDS(A,S);    });
    registry().add("FIELDMGR",     [](DbArea& A, std::istringstream& S){ cmd_FIELDMGR(A,S);  });
    registry().add("RULE",         [](DbArea& A, std::istringstream& S){ cmd_RULE(A,S);      });
    registry().add("VALIDATE",     [](DbArea& A, std::istringstream& S){ cmd_VALIDATE(A,S);  });

    // ---------------------------------------------------------------------
    // Ordered seek/find/order commands
    // ---------------------------------------------------------------------
    // FIND and SEEK are cursor movers. SETORDER is special: changing active
    // order can change logical relation context even if physical recno stays
    // fixed, so SETORDER also refreshes explicitly.
    // Cursor movers (seek/find/order): rely on cursor hook
    registry().add("FIND",         [](DbArea& A, std::istringstream& S){ cmd_FIND(A,S);     });
    registry().add("SEEK",         [](DbArea& A, std::istringstream& S){ cmd_SEEK(A,S);     });
    registry().add("SETORDER",     [](DbArea& A, std::istringstream& S){ cmd_SETORDER(A,S); relations_api::refresh_if_enabled(); });

    // General SET-family commands. SET UNIQUE is a multi-word command key.
    // SETPATH changes path slots, not open table state.
    registry().add("SET",          [](DbArea& A, std::istringstream& S){ cmd_SET(A,S); });
    registry().add("SET UNIQUE",   [](DbArea& A, std::istringstream& S){ cmd_SET_UNIQUE(A,S); });
    registry().add("SETPATH",      [](DbArea& A, std::istringstream& S){ cmd_SETPATH(A,S); });
    registry().add("SETCASE",      [](DbArea& A, std::istringstream& S){ cmd_SETCASE(A,S); });
    registry().add("SETNEAR",      [](DbArea& A, std::istringstream& S){ cmd_SETNEAR(A,S); });

    // ---------------------------------------------------------------------
    // Optional indexing command surface
    // ---------------------------------------------------------------------
    // INX/CNX/CDX/LMDB commands compile only when indexing support is enabled.
    // Position changes inside these commands should use engine movement APIs.
#if DOTTALK_WITH_INDEX
    // Index ops may reposition internally; rely on cursor hook
    registry().add("CNX",       [](DbArea& A, std::istringstream& S){ cmd_CNX(A,S);       });
    registry().add("CDX",       [](DbArea& A, std::istringstream& S){ cmd_CDX(A,S);       });
    registry().add("SETCNX",    [](DbArea& A, std::istringstream& S){ cmd_SETCNX(A,S);    });
    registry().add("SETCDX",    [](DbArea& A, std::istringstream& S){ cmd_SETCDX(A,S);    });
    registry().add("INDEX",     [](DbArea& A, std::istringstream& S){ cmd_INDEX(A,S);     });
    registry().add("REINDEX",   [](DbArea& A, std::istringstream& S){ cmd_REINDEX(A,S);   });
    registry().add("REBUILD",   [](DbArea& A, std::istringstream& S){ cmd_REBUILD(A,S);   });
    registry().add("BUILDLMDB", [](DbArea& A, std::istringstream& S){ cmd_BUILDLMDB(A,S); });
    registry().add("LMDBDUMP",  [](DbArea& A, std::istringstream& S){ cmd_LMDB_DUMP(A,S); });
    registry().add("SETLMDB",   [](DbArea& A, std::istringstream& S){ cmd_SETLMDB(A,S);   });
    registry().add("SETINDEX",  [](DbArea& A, std::istringstream& S){ cmd_SETINDEX(A,S);  });
    registry().add("ASCEND",    [](DbArea& A, std::istringstream& S){ cmd_ASCEND(A,S);    });
    registry().add("DESCEND",   [](DbArea& A, std::istringstream& S){ cmd_DESCEND(A,S);   });
    registry().add("INDEXSEEK", [](DbArea& A, std::istringstream& S){ cmd_INDEXSEEK(A,S); });
    registry().add("LMDB",      [](DbArea& A, std::istringstream& S){ cmd_LMDB(A,S);      });
    registry().add("LMDB_UTIL", [](DbArea& A, std::istringstream& S){ cmd_LMDB_UTIL(A,S); });
    registry().add("SIX",       [](DbArea& A, std::istringstream& S){ cmd_SIX(A,S);       });
//  registry().add("SNX",       [](DbArea& A, std::istringstream& S){ cmd_SNX(A,S);       });
#endif

    // ---------------------------------------------------------------------
    // Aggregate helpers
    // ---------------------------------------------------------------------
    // Aggregates should compute without leaving relation state altered. If an
    // aggregate walks the cursor, it should restore the cursor internally.
    // Aggregate helpers
    registry().add("AGGS",      [](DbArea& A, std::istringstream& S){ cmd_AGGS(A,S); });
    registry().add("SUM",       [](DbArea& A, std::istringstream& S){ cmd_SUM(A,S);  });
    registry().add("AVG",       [](DbArea& A, std::istringstream& S){ cmd_AVG(A,S);  });
    registry().add("AVERAGE",   [](DbArea& A, std::istringstream& S){ cmd_AVG(A,S);  });
    registry().add("MIN",       [](DbArea& A, std::istringstream& S){ cmd_MIN(A,S);  });
    registry().add("MAX",       [](DbArea& A, std::istringstream& S){ cmd_MAX(A,S);  });

    // ---------------------------------------------------------------------
    // Relation command surface
    // ---------------------------------------------------------------------
    // SET RELATION changes the relation graph and refreshes immediately.
    // REL_REFRESH owns its refresh in the handler.
#if DOTTALK_WITH_RELATIONS      // Relation-definition changes: refresh explicitly
    registry().add("SET RELATION", [](DbArea& A, std::istringstream& S){ cmd_SET_RELATIONS(A,S); relations_api::refresh_if_enabled(); });
    registry().add("RELATIONS",    [](DbArea& A, std::istringstream& S){ cmd_RELATIONS_LIST(A,S);    });
    registry().add("REL_LIST",     [](DbArea& A, std::istringstream& S){ cmd_RELATIONS_LIST(A,S);    });
    registry().add("REL_REFRESH",  [](DbArea& A, std::istringstream& S){ cmd_RELATIONS_REFRESH(A,S); });
    registry().add("REL",          [](DbArea& A, std::istringstream& S){ cmd_REL(A,S);               });
#endif

    // ---------------------------------------------------------------------
    // Tuple/relationship exploration commands
    // ---------------------------------------------------------------------
    // Aliases are kept together so help/reflection can see shared ownership.
    registry().add("TUPLEDELTA",   [](DbArea& A, std::istringstream& S){ cmd_TUPLEDELTA(A,S);  });
    registry().add("TUPTALK",      [](DbArea& A, std::istringstream& S){ cmd_TUPTALK(A,S);     });
    registry().add("TUPLE",        [](DbArea& A, std::istringstream& S){ cmd_TUPLE(A,S);       });
    registry().add("TUPVALIDATE",  [](DbArea& A, std::istringstream& S){ cmd_TUPVALIDATE(A,S); });
    registry().add("TUPEXPORT",    [](DbArea& A, std::istringstream& S){ cmd_TUPEXPORT(A,S);   });

    // ---------------------------------------------------------------------
    // Memo / large-object command surface
    // ---------------------------------------------------------------------
    // MEMO should preserve the DbArea/MemoManager boundary: table fields store
    // references; payload behavior belongs to the memo subsystem.
    registry().add("MEMO",      [](DbArea& A, std::istringstream& S){ cmd_MEMO(A,S); });

    // ---------------------------------------------------------------------
    // Locking and basic shell/table utilities
    // ---------------------------------------------------------------------
    // LOCK/UNLOCK coordinate access. CLEAR/CREATE/ERASE are utility commands;
    // destructive behavior should be handled inside the command implementation.
    registry().add("LOCK",      [](DbArea& A, std::istringstream& S){ cmd_LOCK(A,S);   });
    registry().add("UNLOCK",    [](DbArea& A, std::istringstream& S){ cmd_UNLOCK(A,S); });

    registry().add("CLEAR",     [](DbArea& A, std::istringstream& S){ cmd_CLEAR(A,S);  });
    registry().add("CREATE",    [](DbArea& A, std::istringstream& S){ cmd_CREATE(A,S); });
    registry().add("ERASE",     [](DbArea& A, std::istringstream& S){ cmd_ERASE(A,S);  });

    registry().add("DUMP",      [](DbArea& A, std::istringstream& S){ cmd_DUMP(A,S); });
    registry().add("EDIT",      [](DbArea& A, std::istringstream& S){ cmd_EDIT(A,S); });

    // LOCATE/CONTINUE are cursor movers and should use the same hook contract
    // as GO/TOP/SKIP/SEEK.
    // Cursor movers: rely on cursor hook
    registry().add("LOCATE",    [](DbArea& A, std::istringstream& S){ cmd_LOCATE(A,S);   });
    registry().add("CONTINUE",  [](DbArea& A, std::istringstream& S){ cmd_CONTINUE(A,S); });

    // AREA and RECNO are observer/developer commands. If RECNO sets position,
    // it should route through the normal movement path so the hook fires.
    registry().add("AREA",      [](DbArea& A, std::istringstream& S){ cmd_AREA(A,S);  });
    registry().add("RECNO",     [](DbArea& A, std::istringstream& S){ cmd_RECNO(A,S); });

    // Explicit user/developer refresh command. The handler performs visible
    // command behavior; the wrapper enforces relation refresh policy.
    // Explicit REFRESH: keep manual refresh (no cursor movement required)
    registry().add("REFRESH",   [](DbArea& A, std::istringstream& S){ cmd_REFRESH(A,S); relations_api::refresh_if_enabled(); });

    // REPLACE and MULTIREP are mutations. Even when recno is unchanged, field
    // values, keys, filters, and relation matches may change.
    // Data mutation: keep manual refresh
    registry().add("REPLACE",   [](DbArea& A, std::istringstream& S){ cmd_REPLACE(A,S);       relations_api::refresh_if_enabled(); });
    registry().add("MULTIREP",  [](DbArea& A, std::istringstream& S){ cmd_REPLACE_MULTI(A,S); relations_api::refresh_if_enabled(); });

    // STATUS is an observer. Do not refresh here; otherwise STATUS can mask
    // stale-relation defects during testing.
    registry().add("STATUS",    [](DbArea& A, std::istringstream& S){ cmd_STATUS(A,S); });

    // Structure, DDL, schema, workspace, and project surfaces. SCHEMAS can
    // open/close many areas depending on subcommand; SCHEMAS-specific refresh
    // belongs inside cmd_SCHEMAS, not in this registry wrapper.
    registry().add("STRUCT",    [](DbArea& A, std::istringstream& S){ cmd_STRUCT(A,S);    });
    registry().add("DDL",       [](DbArea& A, std::istringstream& S){ cmd_DDL(A,S);       });
    registry().add("SCHEMAS",   [](DbArea& A, std::istringstream& S){ cmd_SCHEMAS(A,S);   });
    registry().add("WORKSPACE", [](DbArea& A, std::istringstream& S){ cmd_WORKSPACE(A,S); });
    registry().add("PROJECTS",  [](DbArea& A, std::istringstream& S){ cmd_PROJECTS(A,S);  });
    registry().add("WSREPORT",  [](DbArea& A, std::istringstream& S){ cmd_WSREPORT(A,S);  });

    // ZAP is destructive and can invalidate cursor/relation assumptions.
    // Refresh explicitly after it runs.
    // Destructive: refresh explicitly (cursor may become invalid/zero)
    registry().add("ZAP", [](DbArea& A, std::istringstream& S){ cmd_ZAP(A,S); relations_api::refresh_if_enabled(); });

    // Console/UI convenience commands and external integration commands. These
    // should not alter table relation state unless their own implementation
    // explicitly documents and handles that behavior.
    registry().add("DIR",       [](DbArea& A, std::istringstream& S){ cmd_DIR(A,S);       });
    registry().add("BELL",      [](DbArea& A, std::istringstream& S){ cmd_BELL(A,S);      });
    registry().add("COLOR",     [](DbArea& A, std::istringstream& S){ cmd_COLOR(A,S);     });
    registry().add("CHRISTMAS", [](DbArea& A, std::istringstream& S){ cmd_CHRISTMAS(A,S); });

    registry().add("!",         [](DbArea& A, std::istringstream& S) { cmd_BANG(A,S); });
    registry().add("BANG",      [](DbArea& A, std::istringstream& S) { cmd_BANG(A,S); });
    registry().add("WEB",       [](DbArea& A, std::istringstream& S) { cmd_WEB(A,S);  });
    registry().add("IMAGE",     [](DbArea& A, std::istringstream& S) { cmd_IMAGE_DISPLAY(A,S); });
    registry().add("SFTP",      [](DbArea& A, std::istringstream& S) { cmd_SFTP(A,S); });

    // Calculator, expression, and education-expression commands. CALC should
    // remain usable without an open DBF. edu_* commands are shell commands, not
    // expression function self-registration.
    registry().add("CALC",      [](DbArea& A, std::istringstream& S){ cmd_CALC(A,S);       });
    registry().add("CALCWRITE", [](DbArea& A, std::istringstream& S){ cmd_CALCWRITE(A,S);  });
    registry().add("BOOLEAN",   [](DbArea& A, std::istringstream& S){ edu_BOOLEAN(A,S);    });
    registry().add("FORMULA",   [](DbArea& A, std::istringstream& S){ edu_FORMULA(A,S);    });
    registry().add("EVALUATE",  [](DbArea& A, std::istringstream& S){ edu_EVALUATE(A,S);   });
    registry().add("NORMALIZE", [](DbArea& A, std::istringstream& S){ edu_NORMALIZE(A,S);  });
    registry().add("IDX",       [](DbArea& A, std::istringstream& S){ edu_IDX(A,S);        });


    // SQL and SmartList command surface. SMARTLIST is the preferred
    // table-centric listing command for order-aware testing. SQL-side mutation
    // is not automatically treated as DbArea relation mutation here.
    registry().add("SQL",       [](DbArea& A, std::istringstream& S){ cmd_SQL(A,S);        });
    registry().add("SQLHELP",   [](DbArea& A, std::istringstream& S){ cmd_SQLHELP(A,S);    });
    registry().add("SQLSEL",    [](DbArea& A, std::istringstream& S){ cmd_SQL_SELECT(A,S); });
    registry().add("WHERE",     [](DbArea& A, std::istringstream& S){ cmd_WHERE(A,S);      });
    registry().add("WHERECACHE", [](DbArea& /*A*/, std::istringstream& S){ cmd_WHERECACHE(S); });
    registry().add("SMARTLIST", [](DbArea& A, std::istringstream& S){ cmd_SMARTLIST(A,S);  });
    registry().add("INSERT",    [](DbArea& A, std::istringstream& S){ cmd_SQL_INSERT(A,S); });
    registry().add("UPDATE",    [](DbArea& A, std::istringstream& S){ cmd_SQL_UPDATE(A,S); });
    registry().add("SHOW",      [](DbArea& A, std::istringstream& S){ cmd_SQL_SHOW(A,S);   });
    registry().add("SQLERASE",  [](DbArea& A, std::istringstream& S){ cmd_SQL_ERASE(A,S);  });
    registry().add("DBAREA",    [](DbArea& A, std::istringstream& S){ cmd_DBAREA(A,S);     });
    registry().add("DBAREAS",   [](DbArea& A, std::istringstream& S){ cmd_DBAREAS(A,S);    });
    registry().add("WA",        [](DbArea& A, std::istringstream& S){ cmd_WAMREPORT(A,S);  });

    registry().add("SQLITE",    [](DbArea& A, std::istringstream& S){ cmd_SQLITE(A,S);     });
    registry().add("SQLVER",    [](DbArea& A, std::istringstream& S){ cmd_SQLVER(A,S);     });
    registry().add("BIBLETALK", [](DbArea& A, std::istringstream& S){ edu_BIBLETALK(A,S);  });
    registry().add("ERP",       [](DbArea& A, std::istringstream& S){ edu_ERP(A,S);        });


    // ---------------------------------------------------------------------
    // Programming and scripting control-flow commands
    // ---------------------------------------------------------------------
    // These support DotScript-style flow control and should not perform
    // registry-level relation refresh unless the command body mutates table state.

//  Programming and Scripting
    registry().add("SCAN",         [](DbArea& A, std::istringstream& S){ cmd_SCAN(A,S);    });
    registry().add("ENDSCAN",      [](DbArea& A, std::istringstream& S){ cmd_ENDSCAN(A,S); });
    registry().add("LOOP",         [](DbArea& A, std::istringstream& S){ cmd_LOOP(A,S);    });
    registry().add("ENDLOOP",      [](DbArea& A, std::istringstream& S){ cmd_ENDLOOP(A,S); });

    registry().add("SCAN_BUFFER",  [](DbArea& A, std::istringstream& S){ cmd_SCAN_BUFFER(A,S); });
    registry().add("LOOP_BUFFER",  [](DbArea& A, std::istringstream& S){ cmd_LOOP_BUFFER(A,S); });

    registry().add("IF",           [](DbArea& A, std::istringstream& S){ cmd_IF(A,S);    });
    registry().add("ELSE",         [](DbArea& A, std::istringstream& S){ cmd_ELSE(A,S);  });
    registry().add("ENDIF",        [](DbArea& A, std::istringstream& S){ cmd_ENDIF(A,S); });

    registry().add("UNTIL",        [](DbArea& A, std::istringstream& S){ cmd_UNTIL(A,S);        });
    registry().add("ENDUNTIL",     [](DbArea& A, std::istringstream& S){ cmd_ENDUNTIL(A,S);     });
    registry().add("UNTIL_BUFFER", [](DbArea& A, std::istringstream& S){ cmd_UNTIL_BUFFER(A,S); });
    registry().add("WHILE",        [](DbArea& A, std::istringstream& S){ cmd_WHILE(A,S);        });
    registry().add("ENDWHILE",     [](DbArea& A, std::istringstream& S){ cmd_ENDWHILE(A,S);     });
    registry().add("WHILE_BUFFER", [](DbArea& A, std::istringstream& S){ cmd_WHILE_BUFFER(A,S); });

    // Help/reference commands. These observe command catalogs, historical
    // references, beta notes, and PowerShell notes.
    registry().add("HELP",         [](DbArea& A, std::istringstream& S){ cmd_HELP(A,S);        });
    registry().add("TEST",         [](DbArea& A, std::istringstream& S){ cmd_TEST(A,S);        });
    registry().add("FOXHELP",      [](DbArea& A, std::istringstream& S){ cmd_FOXHELP(A,S);     });
    registry().add("DOTHELP",      [](DbArea& A, std::istringstream& S){ cmd_DOTHELP(A,S);     });
    registry().add("FOXSTANDARD",  [](DbArea& A, std::istringstream& S){ cmd_FOXSTANDARD(A,S); });
    registry().add("BETA",         [](DbArea& A, std::istringstream& S){ cmd_BETA(A,S);        });
    registry().add("PSHELL",       [](DbArea& A, std::istringstream& S){ cmd_PSHELL(A,S);      });
    registry().add("MCC",          [](DbArea& A, std::istringstream& S){ cmd_MCC(A,S);         });

    // ---------------------------------------------------------------------
    // Metadata, command-help, diagnostics, and scripting utilities
    // ---------------------------------------------------------------------
    // These commands feed help/reflection and command-audit tooling.
    // METADATA
    registry().add("EXPFUNCs",     [](DbArea& A, std::istringstream& S){ cmd_EXPORTFUNCTIONS (A,S); });

    registry().add("SECURITY",     [](DbArea& A, std::istringstream& S){ cmd_SECURITY(A,S);    });

    registry().add("ERROR_CLEAR",  [](DbArea& A, std::istringstream& S){ cmd_ERROR_CLEAR(A,S);  });
    registry().add("ERROR_STATUS", [](DbArea& A, std::istringstream& S){ cmd_ERROR_STATUS(A,S); });
    registry().add("ERROR_TEST",   [](DbArea& A, std::istringstream& S){ cmd_ERROR_TEST(A,S);   });

    // Friendly multi-word aliases for the same diagnostic commands.
    registry().add("ERROR CLEAR",  [](DbArea& A, std::istringstream& S){ cmd_ERROR_CLEAR(A,S);  });
    registry().add("ERROR STATUS", [](DbArea& A, std::istringstream& S){ cmd_ERROR_STATUS(A,S); });
    registry().add("ERROR TEST",   [](DbArea& A, std::istringstream& S){ cmd_ERROR_TEST(A,S);   });


    registry().add("CMDHELP",      [](DbArea& A, std::istringstream& S){ cmd_CMDHELP(A,S);      });
    registry().add("COMMANDSHELP", [](DbArea& A, std::istringstream& S){ cmd_CMDHELP(A,S);      });
    registry().add("CMDHELPCHK",   [](DbArea& A, std::istringstream& S){ cmd_CMDHELPCHK(A,S);   });
    registry().add("CMDREL",       [](DbArea& A, std::istringstream& S){ cmd_CMDREL(A,S);       });
    registry().add("CMDARGCHK",    [](DbArea& A, std::istringstream& S){ cmd_CMDARGCHK(A,S);    });
    registry().add("CANARY",       [](DbArea& A, std::istringstream& S){ cmd_CATALOGCANARY(A,S);});


    registry().add("DOTSCRIPT",    [](DbArea& A, std::istringstream& S){ cmd_DOTSCRIPT(A,S);   });
    registry().add("VAR",          [](DbArea& A, std::istringstream& S){ cmd_VAR(A,S);         });
    registry().add("ZIP",          [](DbArea& A, std::istringstream& S){ cmd_ZIP(A,S);         });

    // Session lifecycle and environment-reporting commands. INIT/SHUTDOWN are
    // command-accessible lifecycle routines for scripts.
    registry().add("ECHO",         [](DbArea& A, std::istringstream& S){ cmd_ECHO(A,S);        });
    registry().add("VERSION",      [](DbArea& A, std::istringstream& S){ cmd_VERSION(A,S);     });
    registry().add("ABOUT",        [](DbArea& A, std::istringstream& S){ cmd_ABOUT(A,S);       });

    registry().add("INIT",         [](DbArea& A, std::istringstream& S){ cmd_INIT(A,S);        });
    registry().add("SHUTDOWN",     [](DbArea& A, std::istringstream& S){ cmd_SHUTDOWN(A,S);    });
    registry().add("SHOWINI",      [](DbArea& A, std::istringstream& S){ cmd_SHOWINI(A,S);     });
    registry().add("TABLEMETA",    [](DbArea& A, std::istringstream& S){ cmd_TABLEMETA(A,S);   });

    // FIRST/NEXT/PRIOR/LAST are navigation-like aliases. Implementations that
    // move the cursor should use the same hook path as TOP/SKIP/BOTTOM.
    registry().add("FIRST",        [](DbArea& A, std::istringstream& S){ cmd_FIRST(A,S);       });
    registry().add("NEXT",         [](DbArea& A, std::istringstream& S){ cmd_NEXT(A,S);        });
    registry().add("PRIOR",        [](DbArea& A, std::istringstream& S){ cmd_PRIOR(A,S);       });
    registry().add("LAST",         [](DbArea& A, std::istringstream& S){ cmd_LAST(A,S);        });

    // ---------------------------------------------------------------------
    // Education / historical-computing commands
    // ---------------------------------------------------------------------
    // Built-in educational commands live here. Student-created commands should
    // live in extension/custom and may self-register there.
//  EDUCATION
    registry().add("COBOL",        [](DbArea& A, std::istringstream& S){ cmd_COBOL(A,S);       });
    registry().add("CODASYL",      [](DbArea& A, std::istringstream& S){ cmd_CODASYL(A,S);     });
    registry().add("DRAWIO",       [](DbArea& A, std::istringstream& S){ cmd_DRAWIO(A,S);      });
    registry().add("RETRO",        [](DbArea& A, std::istringstream& S){ cmd_RETRO(A,S);       });
    registry().add("EXAMPLE",      [](DbArea& A, std::istringstream& S){ cmd_EXAMPLE(A,S);     });
    registry().add("ASCII",        [](DbArea& A, std::istringstream& S){ edu_ASCII_TABLE(A,S); });
    registry().add("CASE",         [](DbArea& A, std::istringstream& S){ edu_CASESTUDY(A,S);   });

    // ---------------------------------------------------------------------
    // External import/export and text/print helpers
    // ---------------------------------------------------------------------
    // SQL import/export bridges DBF/table data with SQL workflows. TEXT and
    // PRN are output helpers. No registry-level relation refresh is attached.
    registry().add("TEXT",         [](DbArea& A, std::istringstream& S){ cmd_TEXT(A,S);        });
    registry().add("PRN",          [](DbArea& A, std::istringstream& S){ cmd_PRN(A,S);         });

//  MSSQL et al Import/Export
    registry().add("IMPORTSQL",    [](DbArea& A, std::istringstream& S){ cmd_IMPORTSQL(A,S);   });
    registry().add("EXPORTSQL",    [](DbArea& A, std::istringstream& S){ cmd_EXPORTSQL(A,S);   });

    registry().add("DDICT",        [](DbArea& A, std::istringstream& S){ cmd_DDICT(A,S);       });
    registry().add("MSGMGR",       [](DbArea& A, std::istringstream& S){ cmd_MSGMGR(A,S);      });
    registry().add("MANUAL",       [](DbArea& A, std::istringstream& S){ cmd_MANUAL(A,S);      });
    registry().add("BBOX",         [](DbArea& A, std::istringstream& S){ cmd_BBOX(A,S);        });
    registry().add("MAINT",        [](DbArea& A, std::istringstream& S){ cmd_MAINT(A,S);       });
    registry().add("MANSTAR",      [](DbArea& A, std::istringstream& S){ cmd_MANSTAR(A,S);     });


    registry().add("QUIT",         [](DbArea& A, std::istringstream& S){ cmd_QUIT(A,S);        });
    registry().add("EXIT",         [](DbArea& A, std::istringstream& S){ cmd_QUIT(A,S);        });



}
