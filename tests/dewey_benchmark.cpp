/****************************************************************************************
 *  Dewey Hierarchical Index Benchmark for 64-bit xBase Engine
 *  Compares Dewey (as primary/clustered index) vs common alternatives
 *  Requires: xbase.hpp and dewey_index.hpp from previous implementation
 ****************************************************************************************/

#include "xbase.hpp"
#include "dewey_index.hpp"
#include <iostream>
#include <iomanip>
#include <chrono>
#include <vector>
#include <random>
#include <string>
#include <algorithm>
#include <cstdint>

using namespace std::chrono;
using Clock = high_resolution_clock;

// ===================================================================
// Benchmark Configuration
// ===================================================================
const int NUM_ROOTS          = 1000;      // Number of top-level nodes
const int NODES_PER_ROOT     = 120;       // Average children per level (wide tree)
const int BENCHMARK_QUERIES  = 20000;     // Number of subtree queries to run
const int BETWEEN_INSERTS    = 8000;      // Number of "insert between" operations

// ===================================================================
// Helper: Simple timer
// ===================================================================
struct Timer {
    time_point<Clock> start;
    std::string name;
    Timer(const std::string& n) : name(n) { start = Clock::now(); }
    ~Timer() {
        auto ms = duration_cast<milliseconds>(Clock::now() - start).count();
        std::cout << std::left << std::setw(45) << name 
                  << ": " << ms << " ms" << std::endl;
    }
};

// ===================================================================
// Main Benchmark
// ===================================================================
int main() {
    std::cout << "=== Dewey Hierarchical Index Benchmark ===\n\n";

    xbase::XBaseEngine engine;
    
    // Open or create the benchmark table (assumes table already has dewey_id C(200))
    // If table doesn't exist, your engine should create it with dewey_id as clustered index
    engine.area(1).open("dewey_benchmark.dbf");

    xbase::DeweyIndex dewey(engine.area(1));

    std::random_device rd;
    std::mt19937 gen(rd());

    std::vector<std::string> allNodes;        // Track some nodes for queries
    std::vector<std::string> leafNodes;       // For insert-between tests

    // ===================================================================
    // Phase 1: Bulk Insert Test (Build hierarchical tree)
    // ===================================================================
    {
        Timer t("Phase 1: Bulk Insert " + std::to_string(NUM_ROOTS * NODES_PER_ROOT) + " nodes");

        for (int r = 0; r < NUM_ROOTS; ++r) {
            std::string root = dewey.insertRoot("Root_" + std::to_string(r));
            allNodes.push_back(root);

            std::string currentParent = root;

            for (int i = 0; i < NODES_PER_ROOT; ++i) {
                // Mix of normal and dynamic inserts
                std::string child;
                if (i % 3 == 0) {
                    child = dewey.insertChildDynamic(currentParent, "Node_" + std::to_string(i));
                } else {
                    child = dewey.insertChild(currentParent, "Node_" + std::to_string(i));
                }
                
                allNodes.push_back(child);
                leafNodes.push_back(child);   // many will become parents later

                // Occasionally go deeper
                if (i % 7 == 0 && !currentParent.empty()) {
                    currentParent = child;
                }
            }
        }
    }

    std::cout << "Total nodes inserted: " << allNodes.size() << "\n\n";

    // ===================================================================
    // Phase 2: Subtree Query Benchmark
    // ===================================================================
    {
        Timer t("Phase 2: Subtree Queries (" + std::to_string(BENCHMARK_QUERIES) + " queries)");

        uint64_t totalNodesReturned = 0;
        std::uniform_int_distribution<> dist(0, static_cast<int>(allNodes.size()) - 1);

        for (int q = 0; q < BENCHMARK_QUERIES; ++q) {
            const std::string& sample = allNodes[dist(gen)];
            auto subtree = dewey.getSubtreeRecnos(sample);
            totalNodesReturned += subtree.size();
        }

        std::cout << "  Average subtree size: " 
                  << (totalNodesReturned / BENCHMARK_QUERIES) << " nodes\n";
    }

    // ===================================================================
    // Phase 3: Direct Children Query Benchmark
    // ===================================================================
    {
        Timer t("Phase 3: Direct Children Queries (" + std::to_string(BENCHMARK_QUERIES / 2) + " queries)");

        std::uniform_int_distribution<> dist(0, static_cast<int>(allNodes.size()) - 1);

        for (int q = 0; q < BENCHMARK_QUERIES / 2; ++q) {
            const std::string& sample = allNodes[dist(gen)];
            auto children = dewey.getDirectChildrenRecnos(sample);
            // We don't sum here, just testing speed
        }
    }

    // ===================================================================
    // Phase 4: Insert-Between (Dynamic) Benchmark
    // ===================================================================
    {
        Timer t("Phase 4: Insert-Between Dynamic (" + std::to_string(BETWEEN_INSERTS) + " inserts)");

        std::uniform_int_distribution<> dist(0, static_cast<int>(leafNodes.size()) - 2);

        for (int i = 0; i < BETWEEN_INSERTS; ++i) {
            int idx = dist(gen);
            std::string left  = leafNodes[idx];
            std::string right = leafNodes[idx + 1];

            // Only insert between if they share the same parent
            if (dewey.parentOf(left) == dewey.parentOf(right)) {
                dewey.insertBetweenDynamic(left, right, "Inserted_Between_" + std::to_string(i));
            }
        }
    }

    // ===================================================================
    // Phase 5: Path-to-Root Benchmark
    // ===================================================================
    {
        Timer t("Phase 5: Path-to-Root (" + std::to_string(BENCHMARK_QUERIES / 4) + " queries)");

        std::uniform_int_distribution<> dist(0, static_cast<int>(allNodes.size()) - 1);

        for (int q = 0; q < BENCHMARK_QUERIES / 4; ++q) {
            const std::string& node = allNodes[dist(gen)];
            auto path = dewey.getPathToRootRecnos(node);
        }
    }

    // ===================================================================
    // Final Statistics
    // ===================================================================
    std::cout << "\n=== Benchmark Complete ===\n";
    std::cout << "Total nodes in table : " << engine.area(1).recCount64() << "\n";
    
    // Optional: Show sample subtree
    if (!allNodes.empty()) {
        auto sampleSubtree = dewey.getSubtreeRecnos(allNodes[0]);
        std::cout << "Sample subtree size from root 0: " << sampleSubtree.size() << " nodes\n";
    }

    std::cout << "\nBenchmark finished successfully.\n";
    std::cout << "You can now analyze performance and compare with adjacency list or other methods.\n";

    return 0;
}