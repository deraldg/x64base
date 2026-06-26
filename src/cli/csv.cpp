#include "csv.hpp"

#include <istream>

namespace csv {

namespace {
bool csv_record_needs_more_data(const std::string& record) {
    bool in_quotes = false;
    for (size_t i = 0; i < record.size(); ++i) {
        char c = record[i];
        if (c != '\"') continue;
        if (in_quotes) {
            if (i + 1 < record.size() && record[i + 1] == '\"') {
                ++i;
            } else {
                in_quotes = false;
            }
        } else {
            in_quotes = true;
        }
    }
    return in_quotes;
}

void strip_trailing_cr(std::string& line) {
    if (!line.empty() && line.back() == '\r') {
        line.pop_back();
    }
}
} // namespace

std::vector<std::string> split_line(const std::string& line) {
    std::vector<std::string> out;
    std::string cur;
    bool in_quotes = false;

    for (size_t i = 0; i < line.size(); ++i) {
        char c = line[i];
        if (in_quotes) {
            if (c == '\"') {
                if (i + 1 < line.size() && line[i+1] == '\"') {
                    cur.push_back('\"'); ++i;
                } else {
                    in_quotes = false;
                }
            } else cur.push_back(c);
        } else {
            if (c == ',') { out.push_back(cur); cur.clear(); }
            else if (c == '\"') in_quotes = true;
            else cur.push_back(c);
        }
    }
    out.push_back(cur);
    return out;
}

bool read_record(std::istream& in, std::string& record) {
    record.clear();

    std::string line;
    if (!std::getline(in, line)) {
        return false;
    }

    strip_trailing_cr(line);
    record = std::move(line);

    while (csv_record_needs_more_data(record)) {
        if (!std::getline(in, line)) {
            break;
        }
        strip_trailing_cr(line);
        record.push_back('\n');
        record += line;
    }

    return true;
}

std::string escape(const std::string& s) {
    bool need_quote = s.find_first_of(",\"\n\r") != std::string::npos;
    if (!need_quote) return s;
    std::string t = "\"";
    for (char c : s) { if (c == '\"') t.push_back('\"'); t.push_back(c); }
    t.push_back('\"');
    return t;
}

} // namespace csv



