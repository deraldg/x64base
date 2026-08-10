// @dottalk.file v1
// subsystem: include
// layer: test
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

namespace xbase { namespace tests {

    // Runs all security tests.
    // Returns number of failed tests (0 = success).
    int run_xbase_security_tests();

}}