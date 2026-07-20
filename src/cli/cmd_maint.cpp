// cmd_maint.cpp
// DotTalk++ native MAINT command
// First-wave maintenance/SDLC inspection surface.
//
// @dottalk.usage v1
// owner: DOT|MAINT
// command: MAINT
// category: maintenance
// status: experimental
// noargs: report
// effect: report
// mutates: none
// risk: READ_ONLY
// usage-access: MAINT USAGE
// summary: Inspect DotTalk++ maintenance lanes, cookbooks, status, AI Portal onboarding, contracts, and protected-system boundaries.
// syntax: MAINT [USAGE|STATUS|LANES|COOKBOOK|BOUNDARY|BBOX|DOCS|GUI|AI [USAGE|STATUS|DASHBOARD|ASSIMILATE|BOOK|INTAKE|GATES|VISIBILITY]|CONTRACTS [USAGE|STATUS|SCAN|REGISTRY|INTAKE|DRIFT|GATES]]
// usage: MAINT
// usage: MAINT USAGE
// usage: MAINT STATUS
// usage: MAINT LANES
// usage: MAINT COOKBOOK
// usage: MAINT BOUNDARY
// usage: MAINT BBOX
// usage: MAINT DOCS
// usage: MAINT GUI
// usage: MAINT AI
// usage: MAINT AI USAGE
// usage: MAINT AI STATUS
// usage: MAINT AI DASHBOARD
// usage: MAINT AI ASSIMILATE
// usage: MAINT AI BOOK
// usage: MAINT AI INTAKE
// usage: MAINT AI GATES
// usage: MAINT AI VISIBILITY
// usage: MAINT CONTRACTS
// usage: MAINT CONTRACTS USAGE
// usage: MAINT CONTRACTS STATUS
// usage: MAINT CONTRACTS SCAN
// usage: MAINT CONTRACTS REGISTRY
// usage: MAINT CONTRACTS INTAKE
// usage: MAINT CONTRACTS DRIFT
// usage: MAINT CONTRACTS GATES
// note: MAINT is read-only first wave.
// note: MAINT does not run maintenance scripts or mutate HELP, CMDHELPCHK, DBFs, source, runtime scripts, or publications.
// note: MAINT AI is a read-only native visibility surface for AI Portal partner onboarding, curation, and routing.
// note: The AI Portal is an Alpha Python/registry surface; MAINT AI does not launch it or authorize mutation.
// note: MAINT CONTRACTS is the first contract-lane manager mode; it reports docs/tooling only and does not edit the registry.
// note: MAINT explains the maintenance/SDLC control surface; BBOX teaches the Blackbox model.
// related: BBOX
// related: CMDHELP
// related: DDICT
// related: MANUAL
// @dottalk.end

#include "xbase.hpp"
#include "cli/command_output.hpp"

#include <algorithm>
#include <cctype>
#include <sstream>
#include <string>

namespace {

using dottalk::helpdata::MessageId;

std::string trim_copy(const std::string& value) {
    const auto first = value.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) {
        return std::string();
    }
    const auto last = value.find_last_not_of(" \t\r\n");
    return value.substr(first, last - first + 1);
}

std::string upper_copy(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char ch) {
        return static_cast<char>(std::toupper(ch));
    });
    return value;
}

bool starts_with_word(const std::string& text, const std::string& word) {
    return text == word || text.rfind(word + " ", 0) == 0;
}

std::string after_first_word(const std::string& text) {
    const auto pos = text.find(' ');
    if (pos == std::string::npos) {
        return std::string();
    }
    return trim_copy(text.substr(pos + 1));
}

void print_usage() {
    cli::cmdout::print_message(MessageId::MaintUsageText);
}

void print_status() {
    cli::cmdout::print_message(MessageId::MaintStatusText);
}

void print_lanes() {
    cli::cmdout::print_message(MessageId::MaintLanesText);
}

void print_cookbook() {
    cli::cmdout::print_message(MessageId::MaintCookbookText);
}

void print_boundary() {
    cli::cmdout::print_message(MessageId::MaintBoundaryText);
}

void print_bbox_relation() {
    cli::cmdout::print_message(MessageId::MaintBboxRelationText);
}

void print_docs() {
    cli::cmdout::print_line("MAINT DOCS - durable information classes");
    cli::cmdout::print_line("");
    cli::cmdout::print_line("Most useful document classes for AI/maintenance work:");
    cli::cmdout::print_line("  contracts      - durable rules that constrain future work");
    cli::cmdout::print_line("  usage contracts- source-level command/user-IO help obligations");
    cli::cmdout::print_line("  architecture   - layer boundaries, ownership, and source-of-truth decisions");
    cli::cmdout::print_line("  workflow       - repeatable staged/parallel implementation procedures");
    cli::cmdout::print_line("  smoke/proof    - commands, transcripts, and observed runtime evidence");
    cli::cmdout::print_line("  status/closeout- current truth, known gaps, next gates, and accepted risk");
    cli::cmdout::print_line("  catalog docs   - HELP, messaging, datadict, manualgen, and GUI catalog shape");
    cli::cmdout::print_line("");
    cli::cmdout::print_line("Rules:");
    cli::cmdout::print_line("  - Keep source comments and @dottalk.usage as harvested evidence.");
    cli::cmdout::print_line("  - Keep contracts short, explicit, and registered when active.");
    cli::cmdout::print_line("  - Keep status docs current; stale status is worse than missing status.");
    cli::cmdout::print_line("  - Keep message/localization keys stable; translate wording, not identity.");
}

void print_gui() {
    cli::cmdout::print_line("MAINT GUI - open architecture GUI synchronization lane");
    cli::cmdout::print_line("");
    cli::cmdout::print_line("Purpose:");
    cli::cmdout::print_line("  keep wxWidgets, Python/Tkinter, and ArcticTalk/FoxTalk aligned over one");
    cli::cmdout::print_line("  DotTalk++ / x64base runtime truth.");
    cli::cmdout::print_line("");
    cli::cmdout::print_line("Primary docs:");
    cli::cmdout::print_line("  docs/gui/GUI_SYNC_DEVELOPMENT_WORKFLOW_V1.md");
    cli::cmdout::print_line("  docs/gui/UNIFIED_GUI_CORE_V1.md");
    cli::cmdout::print_line("  docs/gui/GUI_LOCALIZATION_MESSAGE_CONTRACT_V1.md");
    cli::cmdout::print_line("  docs/ui/CORE_UI_PRINCIPLES_V1.md");
    cli::cmdout::print_line("  docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md");
    cli::cmdout::print_line("");
    cli::cmdout::print_line("Current lanes:");
    cli::cmdout::print_line("  wx      : primary native desktop workbench");
    cli::cmdout::print_line("  Python  : rapid mirror/prototype and inspection lane");
    cli::cmdout::print_line("  TUI     : command taxonomy and shell/session reference");
    cli::cmdout::print_line("");
    cli::cmdout::print_line("Messaging:");
    cli::cmdout::print_line("  GUI message seeds live in dottalkpp/data/messaging/gui_messages.csv.");
    cli::cmdout::print_line("  C++ and Python consume generated GUI message adapters.");
    cli::cmdout::print_line("  This is aligned with the messaging lane, but not yet one physical DBF-backed catalog.");
}

void print_ai_usage() {
    cli::cmdout::print_line("MAINT AI - read-only AI Portal partner visibility");
    cli::cmdout::print_line("");
    cli::cmdout::print_line("Usage:");
    cli::cmdout::print_line("  MAINT AI");
    cli::cmdout::print_line("  MAINT AI USAGE");
    cli::cmdout::print_line("  MAINT AI STATUS");
    cli::cmdout::print_line("  MAINT AI DASHBOARD");
    cli::cmdout::print_line("  MAINT AI ASSIMILATE");
    cli::cmdout::print_line("  MAINT AI BOOK");
    cli::cmdout::print_line("  MAINT AI INTAKE");
    cli::cmdout::print_line("  MAINT AI GATES");
    cli::cmdout::print_line("  MAINT AI VISIBILITY");
    cli::cmdout::print_line("");
    cli::cmdout::print_line("Notes:");
    cli::cmdout::print_line("  - MAINT AI is read-only.");
    cli::cmdout::print_line("  - It does not import chat, run scanners, mutate queues, edit HELP, or publish manuals.");
    cli::cmdout::print_line("  - The Alpha AI Portal is Python/registry based; this native command reports its entry paths only.");
    cli::cmdout::print_line("  - AI interaction material is source material until distilled, anchored, and routed.");
}

void print_ai_status() {
    cli::cmdout::print_line("MAINT AI status");
    cli::cmdout::print_line("  lane          : AI Portal / AI Friendly");
    cli::cmdout::print_line("  mode          : Alpha Python/registry portal plus read-only native visibility");
    cli::cmdout::print_line("  root entry    : AI_PORTAL.md");
    cli::cmdout::print_line("  portal        : labtalk/portal/labtalk_portal.py");
    cli::cmdout::print_line("  seeds         : labtalk/ai_portal");
    cli::cmdout::print_line("  registry      : labtalk/registries/ai_portal.yaml");
    cli::cmdout::print_line("  legacy docs   : docs/AI-Friendly");
    cli::cmdout::print_line("  dashboard     : docs/AI-Friendly/AI_FRIENDLY_DASHBOARD_V1.md");
    cli::cmdout::print_line("  book          : docs/AI-Friendly/AI_ASSIMILATION_BOOK_V1.md");
    cli::cmdout::print_line("  manifest      : docs/AI-Friendly/AI_FRIENDLY_LANE_MANIFEST_V1.md");
    cli::cmdout::print_line("  workflow      : docs/AI-Friendly/AI_FRIENDLY_WORKFLOW_V1.md");
    cli::cmdout::print_line("  intake queue  : docs/AI-Friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md");
    cli::cmdout::print_line("  purpose       : fast-start AI development partners with durable authority, SDLC, contracts, and proof");
    cli::cmdout::print_line("  native scope  : reports paths only; does not launch the portal or grant source mutation");
}

void print_ai_dashboard() {
    cli::cmdout::print_line("MAINT AI dashboard");
    cli::cmdout::print_line("  user surface  : docs/AI-Friendly/AI_FRIENDLY_DASHBOARD_V1.md");
    cli::cmdout::print_line("  shows         : lane state, status buckets, authority levels, work log, review needs, proof needs, drift risks");
    cli::cmdout::print_line("  current state : seeded");
    cli::cmdout::print_line("  portal state  : Alpha/Experimental");
    cli::cmdout::print_line("  portal entry  : AI_PORTAL.md");
    cli::cmdout::print_line("  portal launch : launch_portal.ps1");
    cli::cmdout::print_line("  implementation: Python plus reviewed YAML/Markdown registries; no native autonomous AI runtime");
}

void print_ai_assimilate() {
    cli::cmdout::print_line("MAINT AI assimilate");
    cli::cmdout::print_line("  purpose       : durable AI development-partner fast start when prior chat/provider memory is unavailable");
    cli::cmdout::print_line("  root entry    : AI_PORTAL.md");
    cli::cmdout::print_line("  portal launch : launch_portal.ps1");
    cli::cmdout::print_line("  first reads   :");
    cli::cmdout::print_line("    1. AI_PORTAL.md");
    cli::cmdout::print_line("    2. labtalk/ai_portal/DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md");
    cli::cmdout::print_line("    3. labtalk/ai_portal/SDLC_FAST_START_SEED_V1.md");
    cli::cmdout::print_line("    4. labtalk/ai_portal/SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md");
    cli::cmdout::print_line("    5. labtalk/ai_portal/DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md");
    cli::cmdout::print_line("  rule          : use repo-local evidence and contracts; do not rely on lost chat history or model memory");
    cli::cmdout::print_line("  boundary      : MAINT AI reports onboarding paths only; portal execution remains external and guarded");
}

void print_ai_intake() {
    cli::cmdout::print_line("MAINT AI intake");
    cli::cmdout::print_line("  queue         : docs/AI-Friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md");
    cli::cmdout::print_line("  shape         : ID, Source, Classification, Candidate route, Evidence anchor, Status, Notes");
    cli::cmdout::print_line("  authority     : read the queue for current rows; MAINT does not hardcode queue counts");
    cli::cmdout::print_line("  rule          : add distilled candidates, not entire conversations");
    cli::cmdout::print_line("  preference    : existing destinations before new documents");
}

void print_ai_gates() {
    cli::cmdout::print_line("MAINT AI gates");
    cli::cmdout::print_line("  1. capture only interaction material with reuse value");
    cli::cmdout::print_line("  2. classify the candidate route and evidence class");
    cli::cmdout::print_line("  3. distill long material into a small durable artifact");
    cli::cmdout::print_line("  4. anchor to source, proof, HELP/CMDHELP, CMDHELPCHK, SelfDoc, contracts, LabTalk, or manualgen");
    cli::cmdout::print_line("  5. route to the existing lane before creating new AI Friendly material");
    cli::cmdout::print_line("  6. promote only with honest authority status");
}

void print_ai_visibility() {
    cli::cmdout::print_line("MAINT AI visibility");
    cli::cmdout::print_line("  user needs to see:");
    cli::cmdout::print_line("    - what AI is working on");
    cli::cmdout::print_line("    - what evidence it read");
    cli::cmdout::print_line("    - what files or systems it touched");
    cli::cmdout::print_line("    - whether mutation was performed or only proposed");
    cli::cmdout::print_line("    - where each useful interaction was routed");
    cli::cmdout::print_line("    - what still needs review, proof, or promotion");
    cli::cmdout::print_line("");
    cli::cmdout::print_line("  authority levels:");
    cli::cmdout::print_line("    chat-only, captured, draft, design-intended, source-defined, runtime-proven,");
    cli::cmdout::print_line("    HELP-documented, CMDHELPCHK-validated, publication-ready, student-ready, rejected, superseded");
}

void print_ai(const std::string& topic) {
    const std::string subtopic = upper_copy(after_first_word(topic));

    if (subtopic.empty() || subtopic == "STATUS") {
        print_ai_status();
        return;
    }
    if (subtopic == "USAGE" || subtopic == "HELP" || subtopic == "?") {
        print_ai_usage();
        return;
    }
    if (subtopic == "DASHBOARD") {
        print_ai_dashboard();
        return;
    }
    if (subtopic == "ASSIMILATE" || subtopic == "ASSIMILATION" || subtopic == "BOOK" ||
        subtopic == "PORTAL" || subtopic == "ONBOARD" || subtopic == "ONBOARDING") {
        print_ai_assimilate();
        return;
    }
    if (subtopic == "INTAKE" || subtopic == "QUEUE") {
        print_ai_intake();
        return;
    }
    if (subtopic == "GATES") {
        print_ai_gates();
        return;
    }
    if (subtopic == "VISIBILITY" || subtopic == "VISIBLE") {
        print_ai_visibility();
        return;
    }

    cli::cmdout::print_info("MAINT", "unknown AI topic: " + trim_copy(after_first_word(topic)));
    print_ai_usage();
}

void print_contracts_usage() {
    cli::cmdout::print_line("MAINT CONTRACTS - read-only contract lane manager");
    cli::cmdout::print_line("");
    cli::cmdout::print_line("Usage:");
    cli::cmdout::print_line("  MAINT CONTRACTS");
    cli::cmdout::print_line("  MAINT CONTRACTS USAGE");
    cli::cmdout::print_line("  MAINT CONTRACTS STATUS");
    cli::cmdout::print_line("  MAINT CONTRACTS SCAN");
    cli::cmdout::print_line("  MAINT CONTRACTS REGISTRY");
    cli::cmdout::print_line("  MAINT CONTRACTS INTAKE");
    cli::cmdout::print_line("  MAINT CONTRACTS DRIFT");
    cli::cmdout::print_line("  MAINT CONTRACTS GATES");
    cli::cmdout::print_line("");
    cli::cmdout::print_line("Notes:");
    cli::cmdout::print_line("  - MAINT CONTRACTS is read-only.");
    cli::cmdout::print_line("  - It does not edit source, DBFs, HELP, registry docs, intake queues, or publications.");
    cli::cmdout::print_line("  - BBOX CONTRACTS explains the lane model; DDICT may later catalog contract rows.");
}

void print_contracts_status() {
    cli::cmdout::print_line("MAINT CONTRACTS status");
    cli::cmdout::print_line("  manager mode : MAINT CONTRACTS");
    cli::cmdout::print_line("  lane docs    : docs/contracts");
    cli::cmdout::print_line("  registry     : docs/contracts/CONTRACT_REGISTRY_V1.md");
    cli::cmdout::print_line("  lifecycle    : docs/contracts/CONTRACT_LIFECYCLE_V1.md");
    cli::cmdout::print_line("  intake queue : docs/contracts/CONTRACT_INTAKE_QUEUE_V1.md");
    cli::cmdout::print_line("  scanner      : tools/contracts/contract_scan.py");
    cli::cmdout::print_line("  mode         : read-only first wave");
}

void print_contracts_scan() {
    cli::cmdout::print_line("MAINT CONTRACTS scan baseline");
    cli::cmdout::print_line("  scanner command      : python tools\\contracts\\contract_scan.py --summary");
    cli::cmdout::print_line("  baseline report      : docs/contracts/reports/CONTRACT_SCAN_BASELINE_V1.md");
    cli::cmdout::print_line("  current counts       : generated by the scanner; not embedded in this command");
    cli::cmdout::print_line("  runtime behavior     : reports the proof path; does not execute the scanner");
}

void print_contracts_registry() {
    cli::cmdout::print_line("MAINT CONTRACTS registry");
    cli::cmdout::print_line("  active registry: docs/contracts/CONTRACT_REGISTRY_V1.md");
    cli::cmdout::print_line("  purpose        : durable index of contracts meant to constrain future work");
    cli::cmdout::print_line("  evidence rule  : do not claim runtime-proven behavior without runtime/test/report proof");
}

void print_contracts_intake() {
    cli::cmdout::print_line("MAINT CONTRACTS intake");
    cli::cmdout::print_line("  queue: docs/contracts/CONTRACT_INTAKE_QUEUE_V1.md");
    cli::cmdout::print_line("  use : capture implied or missing contracts before they graduate to the registry");
}

void print_contracts_drift() {
    cli::cmdout::print_line("MAINT CONTRACTS drift");
    cli::cmdout::print_line("  first drift class     : discovered contract-like docs not yet normalized into registry rows");
    cli::cmdout::print_line("  second drift class    : registry rows whose source is not detected by the current scanner");
    cli::cmdout::print_line("  current counts        : run python tools\\contracts\\contract_scan.py --summary");
    cli::cmdout::print_line("  current report        : docs/contracts/reports/CONTRACT_SCAN_BASELINE_V1.md");
}

void print_contracts_gates() {
    cli::cmdout::print_line("MAINT CONTRACTS gates");
    cli::cmdout::print_line("  1. inventory contract-like docs and source markers");
    cli::cmdout::print_line("  2. map usage contracts through metacollect/SRCUSAGE evidence");
    cli::cmdout::print_line("  3. classify discovered candidates as active, historical, superseded, rejected, or note-only");
    cli::cmdout::print_line("  4. add registry rows for active contracts with honest evidence class");
    cli::cmdout::print_line("  5. promote source-defined/runtime-proven contracts into HELP/SelfDoc/manualgen where appropriate");
}

void print_contracts(const std::string& topic) {
    const std::string subtopic = upper_copy(after_first_word(topic));

    if (subtopic.empty() || subtopic == "STATUS") {
        print_contracts_status();
        return;
    }
    if (subtopic == "USAGE" || subtopic == "HELP" || subtopic == "?") {
        print_contracts_usage();
        return;
    }
    if (subtopic == "SCAN") {
        print_contracts_scan();
        return;
    }
    if (subtopic == "REGISTRY") {
        print_contracts_registry();
        return;
    }
    if (subtopic == "INTAKE") {
        print_contracts_intake();
        return;
    }
    if (subtopic == "DRIFT") {
        print_contracts_drift();
        return;
    }
    if (subtopic == "GATES") {
        print_contracts_gates();
        return;
    }

    cli::cmdout::print_info("MAINT", "unknown CONTRACTS topic: " + trim_copy(after_first_word(topic)));
    print_contracts_usage();
}

} // namespace

void cmd_MAINT(xbase::DbArea& area, std::istringstream& iss) {
    (void)area;

    std::string rest;
    std::getline(iss, rest);
    const std::string topic = upper_copy(trim_copy(rest));

    if (topic.empty() || topic == "STATUS") {
        print_status();
        return;
    }
    if (topic == "USAGE" || topic == "HELP") {
        print_usage();
        return;
    }
    if (topic == "LANES") {
        print_lanes();
        return;
    }
    if (topic == "COOKBOOK" || topic.rfind("COOKBOOK ", 0) == 0) {
        print_cookbook();
        return;
    }
    if (topic == "BOUNDARY" || topic == "BOUNDARIES") {
        print_boundary();
        return;
    }
    if (topic == "BBOX" || topic == "BLACKBOX") {
        print_bbox_relation();
        return;
    }
    if (topic == "DOCS" || topic == "DOCUMENTS" || topic == "DOCUMENTATION") {
        print_docs();
        return;
    }
    if (topic == "GUI" || topic == "UIS" || topic == "UI") {
        print_gui();
        return;
    }
    if (starts_with_word(topic, "AI") || starts_with_word(topic, "AIFRIENDLY") ||
        starts_with_word(topic, "AI-FRIENDLY") || starts_with_word(topic, "AI_FRIENDLY")) {
        print_ai(topic);
        return;
    }
    if (starts_with_word(topic, "CONTRACTS") || starts_with_word(topic, "CONTRACT")) {
        print_contracts(topic);
        return;
    }

    cli::cmdout::print_prefixed_message(
        "MAINT",
        MessageId::MaintUnknownTopic,
        {{"topic", trim_copy(rest)}});
}
