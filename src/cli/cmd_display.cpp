#include "xbase.hpp"
#include "cli/memo_display.hpp"
#include "cli/output_router.hpp"
#include "cli/message_catalog.hpp"

#include <sstream>
#include <string>
#include <algorithm>
#include <cctype>

using namespace xbase;

namespace {

static inline void print_line(const std::string& s)
{
    auto& out = cli::OutputRouter::instance().out();
    out << s << '\n';
}

static std::string trim(std::string s)
{
    auto issp = [](unsigned char c){
        return c==' '||c=='\t'||c=='\r'||c=='\n';
    };
    while(!s.empty() && issp((unsigned char)s.front())) s.erase(s.begin());
    while(!s.empty() && issp((unsigned char)s.back()))  s.pop_back();
    return s;
}

static std::string up(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c){ return (char)std::toupper(c); });
    return s;
}

} // anonymous namespace

void cmd_DISPLAY(DbArea& a, std::istringstream& iss)
{
    using namespace dottalk::msg;

    if (!a.isOpen()) {
        print_line(text(Code::NotFound));   // "No table open" → standardized
        return;
    }

    long want = 0;
    if (iss >> want) {
        if (want < 1 || want > (long)a.recCount()) {
            print_line(text(Code::InvalidSyntax)); // better than custom string
            return;
        }
        a.gotoRec((int32_t)want);
    }

    const long rec = a.recno();
    if (rec <= 0 || rec > (long)a.recCount()) {
        print_line(text(Code::InternalError)); // fallback for bad state
        return;
    }

    a.readCurrent();

    {
        auto& out = cli::OutputRouter::instance().out();

        out << "Record " << rec;
        if (a.isDeleted())
            out << " [DELETED]";
        out << "\n";

        const auto& fields = a.fields();

        for (size_t i = 0; i < fields.size(); ++i) {
            const auto& f = fields[i];

            std::string raw;
            try {
                raw = a.get((int)i + 1);
            } catch (...) {
                raw.clear();
            }

            const std::string shown =
                cli_memo::resolve_display_value(a, (int)i + 1, raw);

            out << "  " << up(f.name) << " = " << trim(shown) << "\n";
        }
    }
}