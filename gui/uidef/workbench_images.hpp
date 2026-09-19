// @dottalk.file v1
// subsystem: gui
// layer: service
// owns: nested MINIDB inspection and hydration admission
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#pragma once
#include "dottalk/minidb.hpp"
#include <filesystem>
#include <stop_token>

namespace dottalk::workbench {
struct ImageNode {
    std::string location, payload, error;
    unsigned depth{};
    minidb::Scan scan;
};
struct ImageTree {
    std::vector<ImageNode> nodes;
    std::string error, provenance, source_label;
};
// Follows live DTX objects only. Does not claim every live object is referenced
// by a DBF row. VFP FPT/DBT containers are reported as unsupported for expansion.
ImageTree inspect_images(std::string payload, std::stop_token stop = {});
std::string read_image_file(const std::filesystem::path& path, std::stop_token stop = {});
// Export the inspected bytes, not a new workspace snapshot. Never replaces an
// existing destination. Throws on validation, write, readback or sync failure;
// private staging files and any partial destination remain for review.
std::filesystem::path export_image(const std::string& payload, const std::filesystem::path& destination,
                                   const std::filesystem::path& staging_directory);
struct ImageAdmission {
    minidb::Scan scan;
    std::size_t tables{};
    std::string error;
    bool ok() const { return error.empty(); }
};
// Checks that every AREA path is carried in the image. No outside table/index
// paths may be opened from a catalog snapshot. The command still parses/loads.
ImageAdmission admit_image(const std::string& payload, const std::filesystem::path& root);
}
