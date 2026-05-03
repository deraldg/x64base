#pragma once

#include <string>
#include <vector>
#include <unordered_map>

namespace dottalk::cases {

struct CaseStudy {
    std::string id;
    std::string title;
    std::string type;
    std::string era;
    std::vector<std::string> domains;
    std::string level;
    std::string lab;
    std::string path;

    std::string summary;
    std::string problem;
    std::string workflow;
    std::string model;
    std::string takeaway;

    std::string raw_body;
};

class Catalog {
public:
    bool load(std::string* err = nullptr);
    bool reload(std::string* err = nullptr);

    bool empty() const;
    std::size_t size() const;

    const CaseStudy* find(const std::string& id) const;
    std::vector<const CaseStudy*> list() const;

    std::string cases_dir() const;

private:
    bool loaded_{false};
    std::unordered_map<std::string, CaseStudy> by_id_;
};

std::string up_copy(std::string s);
std::string trim_copy(std::string s);

Catalog& catalog();

} // namespace dottalk::cases