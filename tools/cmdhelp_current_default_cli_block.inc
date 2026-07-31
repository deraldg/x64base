// === CLI =====================================================================

static std::vector<std::string> cmdhelp_words(const std::string& s) {
    std::vector<std::string> out;
    std::istringstream ss(s);
    std::string w;
    while (ss >> w) out.push_back(w);
    return out;
}

static int cmdhelp_field_index(const DbfTable& tbl, const char* wanted) {
    const std::string W = up(wanted);
    for (int i = 0; i < static_cast<int>(tbl.fields.size()); ++i) {
        std::string fn(tbl.fields[static_cast<size_t>(i)].name,
                       tbl.fields[static_cast<size_t>(i)].name +
                           strnlen(tbl.fields[static_cast<size_t>(i)].name, 11));
        if (up(fn) == W) return i;
    }
    return -1;
}

static std::string cmdhelp_cell(const std::vector<std::string>& row, int ix) {
    if (ix < 0 || ix >= static_cast<int>(row.size())) return {};
    return row[static_cast<size_t>(ix)];
}

static bool load_help_line_table(const std::string& dir, DbfTable& out) {
    const std::string dbf = (fs::path(dir) / "help_line.dbf").string();
    return read_dbf_with_memo(dbf, std::string(), out);
}

static void cmdhelp_usage() {
    std::cout
        << "CMDHELP usage\n"
        << "  CMDHELP\n"
        << "  CMDHELP USAGE\n"
        << "  CMDHELP BUILD\n"
        << "  CMDHELP BUILD . <source-root>\n"
        << "  CMDHELP BUILD LEGACY\n"
        << "  CMDHELP LEGACY\n"
        << "\n"
        << "Notes:\n"
        << "  CMDHELP BUILD writes current HELP DATA tables.\n"
        << "  CMDHELP LEGACY reads the old commands.dbf/cmd_args.dbf report.\n";
}

static void print_count_map(const char* title, const std::unordered_map<std::string, int>& counts) {
    std::vector<std::pair<std::string, int>> rows(counts.begin(), counts.end());
    std::sort(rows.begin(), rows.end(), [](const auto& a, const auto& b) {
        return a.first < b.first;
    });

    std::cout << "\n" << title << ":\n";
    for (const auto& kv : rows) {
        std::cout << "  " << std::left << std::setw(18) << kv.first << " " << kv.second << "\n";
    }
}

static void print_current_help_report(const std::string& dir) {
    DbfTable tbl;
    if (!load_help_line_table(dir, tbl)) {
        std::cout << "CMDHELP: could not read current HELP DATA in \"" << dir << "\".\n"
                  << "Expected: help_line.dbf\n"
                  << "Tip: run: CMDHELP BUILD . <source-root>\n";
        return;
    }

    const int ix_topic_key = cmdhelp_field_index(tbl, "TOPICKEY");
    const int ix_kind      = cmdhelp_field_index(tbl, "KIND");
    const int ix_source    = cmdhelp_field_index(tbl, "SOURCE");
    const int ix_confid    = cmdhelp_field_index(tbl, "CONFID");
    const int ix_role      = cmdhelp_field_index(tbl, "ROLE");
    const int ix_text      = cmdhelp_field_index(tbl, "TEXT");

    if (ix_topic_key < 0 || ix_kind < 0 || ix_source < 0 || ix_text < 0) {
        std::cout << "CMDHELP: help_line.dbf is missing expected columns.\n"
                  << "Need at least TOPICKEY, KIND, SOURCE, TEXT.\n";
        return;
    }

    std::set<std::string> topics;
    std::unordered_map<std::string, int> by_kind;
    std::unordered_map<std::string, int> by_source;

    for (const auto& r : tbl.rows) {
        const std::string topic = cmdhelp_cell(r, ix_topic_key);
        const std::string kind = cmdhelp_cell(r, ix_kind);
        const std::string source = cmdhelp_cell(r, ix_source);

        if (!topic.empty()) topics.insert(topic);
        by_kind[kind.empty() ? "(blank)" : kind]++;
        by_source[source.empty() ? "(blank)" : source]++;
    }

    std::cout << "CMDHELP Report (current HELP DATA)\n";
    std::cout << "  directory : " << dir << "\n";
    std::cout << "  line rows : " << tbl.rows.size() << "\n";
    std::cout << "  topics    : " << topics.size() << "\n";

    print_count_map("By KIND", by_kind);
    print_count_map("By SOURCE", by_source);

    std::cout << "\nPreview rows\n";
    std::cout << std::left
              << std::setw(20) << "TOPICKEY"
              << std::setw(14) << "KIND"
              << std::setw(16) << "SOURCE"
              << std::setw(14) << "CONFID"
              << std::setw(10) << "ROLE"
              << "TEXT\n";
    std::cout << "--------------------------------------------------------------------------------\n";

    int shown = 0;
    for (const auto& r : tbl.rows) {
        if (shown >= 24) break;

        std::string text = cmdhelp_cell(r, ix_text);
        for (char& ch : text) {
            if (ch == '\n' || ch == '\r' || ch == '\t') ch = ' ';
        }
        if (text.size() > 100) text.resize(100);

        std::cout << std::left
                  << std::setw(20) << cmdhelp_cell(r, ix_topic_key).substr(0, 19)
                  << std::setw(14) << cmdhelp_cell(r, ix_kind).substr(0, 13)
                  << std::setw(16) << cmdhelp_cell(r, ix_source).substr(0, 15)
                  << std::setw(14) << cmdhelp_cell(r, ix_confid).substr(0, 13)
                  << std::setw(10) << cmdhelp_cell(r, ix_role).substr(0, 9)
                  << text << "\n";
        ++shown;
    }
}

static void build_current_helpdata(const std::string& outdir,
                                   const std::vector<std::string>& roots) {
    auto list = collect_commands();
    auto counts = export_helpdata_v2_dbfs(outdir, list, roots);
    (void)counts;

    std::cout << "CMDHELP wrote current HELP DATA -> " << outdir << "\n"
              << "Artifacts mined from: " << (roots.empty() ? std::string("./src") : roots.front()) << "\n";
    print_current_help_report(outdir);
}

static void build_legacy_helpdata(const std::string& outdir,
                                  const std::vector<std::string>& roots) {
    auto counts = export_dbfs(outdir, roots);
    auto list = collect_commands();

    std::cout << "CMDHELP LEGACY wrote: " << counts.commands << " command rows, "
              << counts.args << " arg rows -> " << outdir << "\n"
              << "Switches mined from: " << (roots.empty() ? std::string("./src") : roots.front()) << "\n\n";
    print_commands_report(std::cout, list);
}

static void report_legacy_helpdata(const std::string& dir) {
    std::vector<CommandInfo> cmds;
    int arg_rows = 0;

    if (!CmdDbfLoader::load(dir, cmds, arg_rows)) {
        std::cout << "CMDHELP LEGACY: could not read commands.dbf/cmd_args.dbf in \"" << dir << "\".\n"
                  << "Tip: run: CMDHELP BUILD LEGACY\n";
        return;
    }

    std::cout << "CMDHELP LEGACY Report: "
              << cmds.size() << " command rows, "
              << arg_rows << " arg rows -> " << dir << "\n\n";
    print_commands_report(std::cout, cmds);
}

void cmd_COMMANDSHELP(DbArea& /*area*/, std::istringstream& in) {
    auto trim_inplace = [](std::string& s) {
        auto issp = [](unsigned char c){ return std::isspace(c) != 0; };
        s.erase(s.begin(), std::find_if(s.begin(), s.end(), [&](unsigned char c){ return !issp(c); }));
        while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    };

    std::string rest;
    std::getline(in, rest);
    trim_inplace(rest);

    const auto words = cmdhelp_words(rest);
    const std::string firstU = words.empty() ? std::string() : up(words[0]);

    if (firstU.empty()) {
        print_current_help_report(resolve_help_dir_arg(".").string());
        return;
    }

    if (firstU == "USAGE" || firstU == "HELP" || firstU == "?") {
        cmdhelp_usage();
        return;
    }

    if (firstU == "LEGACY") {
        const std::string dir_arg = (words.size() >= 2) ? words[1] : ".";
        report_legacy_helpdata(resolve_help_dir_arg(dir_arg).string());
        return;
    }

    if (firstU == "REPORT") {
        if (words.size() >= 2 && up(words[1]) == "LEGACY") {
            const std::string dir_arg = (words.size() >= 3) ? words[2] : ".";
            report_legacy_helpdata(resolve_help_dir_arg(dir_arg).string());
            return;
        }
        const std::string dir_arg = (words.size() >= 2) ? words[1] : ".";
        print_current_help_report(resolve_help_dir_arg(dir_arg).string());
        return;
    }

    if (firstU == "BUILD") {
        size_t pos = 1;
        bool legacy = false;

        if (pos < words.size()) {
            const std::string mode = up(words[pos]);
            if (mode == "V2") {
                // Silent compatibility.  V2 is the current build now.
                ++pos;
            } else if (mode == "LEGACY") {
                legacy = true;
                ++pos;
            }
        }

        const std::string outdir_arg = (pos < words.size()) ? words[pos++] : ".";
        const std::string srcroot = (pos < words.size()) ? words[pos++] : std::string();

        const std::string outdir = resolve_help_dir_arg(outdir_arg).string();
        const std::vector<std::string> roots =
            srcroot.empty() ? std::vector<std::string>{"./src"} : std::vector<std::string>{srcroot};

        if (legacy) {
            build_legacy_helpdata(outdir, roots);
        } else {
            build_current_helpdata(outdir, roots);
        }
        return;
    }

    // Future: bare CMDHELP <topic> should render a topic.
    // For now, treat bare argument as a current HELP DATA directory/report request.
    print_current_help_report(resolve_help_dir_arg(rest).string());
}

} // namespace cmdhelp

void cmd_CMDHELP(DbArea& area, std::istringstream& in)
{
    cmdhelp::cmd_COMMANDSHELP(area, in);
}
