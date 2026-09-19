// @dottalk.file v1
// subsystem: gui
// layer: service
// owns: native DTX traversal and private image admission
// project: project.x64base.gui
// lane: AIF-120
// owner: member.derald
// status: candidate
#include "workbench_images.hpp"
#include "dottalk/minidb_hydrate.hpp"
#include "memo/memostore.hpp"
#include "xbase.hpp"
#include "xbase/durable.hpp"
#include <atomic>
#include <chrono>
#include <fstream>
#include <functional>
#include <set>
#include <sstream>

namespace dottalk::workbench {
namespace fs = std::filesystem;
namespace {
constexpr std::size_t payload_limit = 128 * 1024 * 1024;
constexpr unsigned depth_limit = 8;
constexpr std::size_t node_limit = 128;
struct MemoCopy {
    fs::path dir, file;
    MemoCopy() {
        static std::atomic<unsigned> sequence{};
        dir = fs::temp_directory_path() / ("arctictalk-nested-" +
            std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()) + "-" + std::to_string(sequence++));
        if (!fs::create_directory(dir)) throw std::runtime_error("Nested inspection directory collision");
        file = dir / "MEMO.dtx";
    }
    ~MemoCopy() { std::error_code ec; fs::remove(file, ec); fs::remove(dir, ec); }
};
std::string normalized(std::string value) {
    value = minidb::detail::trim_ascii(value);
    std::replace(value.begin(), value.end(), '\\', '/');
    return minidb::detail::lower_ascii(value);
}
std::string field(const std::string& line, const char* key) {
    // Matches posture_area_field in cmd_workspace.cpp, including exact keys.
    const auto start = line.find(key);
    if (start == std::string::npos) return {};
    const auto value = start + std::char_traits<char>::length(key);
    return minidb::detail::trim_ascii(line.substr(value, line.find('|', value) - value));
}
}
ImageTree inspect_images(std::string payload, std::stop_token stop) {
    ImageTree tree;
    std::size_t total = 0;
    std::function<void(std::string, std::string, unsigned)> visit;
    visit = [&](std::string bytes, std::string location, unsigned depth) {
        if (stop.stop_requested()) throw std::runtime_error("Nested inspection cancelled");
        if (tree.nodes.size() >= node_limit || bytes.size() > payload_limit - total)
            throw std::runtime_error("Nested inspection limit reached (128 images / 128 MiB)");
        total += bytes.size();
        const auto index = tree.nodes.size();
        ImageNode node; node.location = std::move(location); node.depth = depth;
        node.payload = std::move(bytes); node.scan = minidb::scan(node.payload);
        if (!node.scan.ok) node.error = node.scan.error;
        tree.nodes.push_back(std::move(node));
        if (!tree.nodes[index].scan.ok) return;
        if (depth >= depth_limit) { tree.nodes[index].error = "Inspection depth limit reached (8)"; return; }
        const auto members = tree.nodes[index].scan.files;
        for (const auto& member : members) {
            if (stop.stop_requested()) throw std::runtime_error("Nested inspection cancelled");
            const auto ext = normalized(fs::path(member.relpath).extension().string());
            if (ext == ".dbt" || ext == ".fpt") {
                tree.nodes[index].error += "Nested inspection supports DTX; " + member.relpath + " was not expanded. ";
                continue;
            }
            if (ext != ".dtx") continue;
            MemoCopy copy;
            {
                std::ofstream out(copy.file, std::ios::binary);
                out.write(tree.nodes[index].payload.data() + member.offset, static_cast<std::streamsize>(member.length));
                out.close(); if (!out) throw std::runtime_error("Cannot write private nested memo copy");
            }
            memo::MemoStore store;
            const auto opened = store.open(copy.file.string(), memo::OpenMode::OpenExisting);
            if (!opened.ok) { tree.nodes[index].error += member.relpath + ": " + opened.error + "; "; continue; }
            std::vector<std::uint64_t> ids;
            if (!store.list_live_ids(ids)) throw std::runtime_error("Cannot enumerate live DTX objects");
            std::sort(ids.begin(), ids.end());
            for (auto id : ids) {
                if (stop.stop_requested()) throw std::runtime_error("Nested inspection cancelled");
                std::uint64_t size = 0; std::string error, nested;
                if (!store.get_object_size_id(id, size, &error)) throw std::runtime_error(error);
                if (size > payload_limit - total) throw std::runtime_error("Nested memo object exceeds remaining 128 MiB inspection budget");
                if (!store.get_text_id(id, nested, &error)) throw std::runtime_error(error);
                if (!minidb::is_container(nested)) continue;
                const auto location = tree.nodes[index].location + " / " + member.relpath + " / object " + std::to_string(id);
                visit(std::move(nested), location, depth + 1);
            }
        }
    };
    try { visit(std::move(payload), "Selected image", 0); }
    catch (const std::exception& e) { tree.error = e.what(); }
    return tree;
}

std::string read_image_file(const fs::path& path, std::stop_token stop) {
    if (stop.stop_requested()) throw std::runtime_error("Image read cancelled.");
    if (!fs::is_regular_file(path)) throw std::runtime_error("Choose an existing MINIDB image file.");
    const auto size = fs::file_size(path);
    const auto stamp = fs::last_write_time(path);
    if (!size || size > payload_limit) throw std::runtime_error("Choose a MINIDB image no larger than 128 MiB.");
    std::ifstream file(path, std::ios::binary);
    std::string payload(static_cast<std::size_t>(size), '\0');
    file.read(payload.data(), static_cast<std::streamsize>(size));
    if (!file || file.peek() != EOF || file.bad() || fs::file_size(path) != size || fs::last_write_time(path) != stamp)
        throw std::runtime_error("Image could not be read consistently; retry when its writer is idle.");
    if (stop.stop_requested()) throw std::runtime_error("Image read cancelled.");
    return payload;
}

fs::path export_image(const std::string& payload, const fs::path& path, const fs::path& staging_directory) {
    if (path.empty()) throw std::runtime_error("Choose a new image file.");
    if (payload.size() > payload_limit) throw std::runtime_error("Image exceeds 128 MiB export limit.");
    const auto scan = minidb::scan(payload);
    if (!scan.ok) throw std::runtime_error("Cannot export an invalid MINIDB image: " + scan.error);
    const auto destination = fs::absolute(path);
    if (fs::exists(destination)) throw std::runtime_error("That file already exists. Choose a new image filename.");
    static std::atomic<unsigned> sequence{};
    const auto staged = staging_directory / ("export-" +
        std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()) + "-" +
        std::to_string(sequence++) + ".minidb");
    {
        std::ofstream file(staged, std::ios::binary);
        file.write(payload.data(), static_cast<std::streamsize>(payload.size()));
        file.close(); if (!file) throw std::runtime_error("Cannot stage the image for export.");
    }
    // No replacement, including a destination created after the initial check.
    if (!fs::copy_file(staged, destination, fs::copy_options::none))
        throw std::runtime_error("Image copy failed; destination is not verified.");
    // Read only the expected size; concurrent file growth cannot cause an
    // unbounded allocation. Exact equality also preserves embedded NUL bytes.
    std::ifstream file(destination, std::ios::binary);
    std::string back(payload.size(), '\0');
    file.read(back.data(), static_cast<std::streamsize>(back.size()));
    if (!file || back != payload || file.peek() != std::char_traits<char>::eof())
        throw std::runtime_error("Export readback differs; destination is not verified.");
    if (file.bad()) throw std::runtime_error("Cannot read back the exported image.");
    file.close(); std::string error;
    if (!xbase::durable_sync(destination.string(), &error))
        throw std::runtime_error("Image was written but durability sync failed: " + error);
    return destination;
}

ImageAdmission admit_image(const std::string& payload, const fs::path& root) {
    ImageAdmission result;
    if (payload.size() > payload_limit) { result.error = "Image exceeds 128 MiB admission limit"; return result; }
    result.scan = minidb::scan(payload);
    std::vector<fs::path> destinations;
    if (!minidb::materialization_paths(payload, result.scan, root, root / "indexes", destinations, result.error)) return result;
    std::set<std::string> files;
    for (const auto& member : result.scan.files) files.insert(normalized(member.relpath));
    std::set<int> keys;
    std::istringstream posture(result.scan.posture); std::string line;
    std::getline(posture, line);
    const auto header = normalized(line);
    if (header != "dtshema 2" && header != "dtshema 3") {
        result.error = "Image inspection supports DTSHEMA 2/3 postures"; return result;
    }
    while (std::getline(posture, line)) {
        line = minidb::detail::trim_ascii(line);
        if (normalized(line).rfind("area ", 0) != 0) continue;
        int key = -1; std::istringstream fields(line.substr(5)); fields >> key;
        if (key < 0 || key >= xbase::MAX_AREA || !keys.insert(key).second) {
            result.error = "Invalid or duplicate AREA key in image"; return result;
        }
        const auto dbf = normalized(field(line, "dbf="));
        const auto idx = normalized(field(line, "index="));
        if (dbf.empty() || !files.count(dbf) || fs::path(dbf).extension() != ".dbf") {
            result.error = "Posture table is not carried in this image: " + dbf; return result;
        }
        if (!idx.empty() && idx != "none" && !files.count("indexes/" + idx)) {
            result.error = "Posture index is not carried under indexes/: " + idx; return result;
        }
        ++result.tables;
    }
    if (!result.tables) result.error = "Image posture declares no tables";
    return result;
}
}
