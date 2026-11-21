// AIF-174: exercise the real router with a console sink and an independent log.
#include "cli/output_router.hpp"
#include "cli/captured_process.hpp"
#include <iostream>
#include <sstream>
#include <stdexcept>

static void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

int main() {
    std::ostringstream screen, log;
    auto* original = std::cout.rdbuf(screen.rdbuf());
    auto& router = cli::OutputRouter::instance();
    router.set_wrap(true);
    require(router.begin_capture(log.rdbuf(), true), "begin quiet capture");
    require(!router.begin_capture(nullptr, false), "nested capture must refuse");
    auto* previous = std::cout.rdbuf(router.out().rdbuf());
    std::cout << "ordinary\n";
    router.out() << "routed\n";
    router.console_note("note");
    router.set_talk(true);
    router.talk_line("talk");
    require(screen.str().empty(), "quiet leaked to console");
    router.capture_quiet(false);
    std::cout << "summary\n";
    require(screen.str() == "summary\n", "summary missing or duplicated");
    std::cout.rdbuf(previous);
    require(router.end_capture(), "capture flush failed");
    require(log.str() == "ordinary\nrouted\nnote\ntalk\nsummary\n", "log missing or duplicated bytes");
    router.out() << "restored\n";
    require(screen.str() == "summary\nrestored\n", "console not restored");
    require(log.str().find("restored") == std::string::npos, "capture escaped scope");
    std::ostringstream full;
    require(router.begin_capture(full.rdbuf(), false), "begin full capture");
    router.out() << "full\n";
    require(router.end_capture(), "full flush failed");
    require(full.str() == "full\n", "full capture missing");
    require(screen.str().find("full\n") != std::string::npos, "full screen dump missing");
    std::ostringstream child;
    const auto screen_before_child = screen.str();
    require(router.begin_capture(child.rdbuf(), true), "begin child capture");
#ifdef _WIN32
    const char* child_command = "echo child-out& echo child-error 1>&2";
#else
    const char* child_command = "echo child-out; echo child-error 1>&2";
#endif
    require(cli::stream_shell_output(child_command, router.out()) == 0, "child launch failed");
    require(router.end_capture(), "child log flush failed");
    require(child.str().find("child-out") != std::string::npos, "missing child stdout");
    require(child.str().find("child-error") != std::string::npos, "missing child stderr");
    require(screen.str() == screen_before_child, "quiet child leaked output");
    struct FailingBuffer : std::streambuf {
        std::streamsize xsputn(const char*, std::streamsize) override { return 0; }
    } failing;
    require(router.begin_capture(&failing, true), "begin failing capture");
    router.out() << "cannot write\n";
    require(!router.end_capture(), "write failure was hidden");
    std::cout.rdbuf(original);
    std::cout << "regression output capture: PASS\n";
}
