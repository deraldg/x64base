#pragma once
// xbase_security_signatures.hpp
// Compatibility facade for the xBase_64 security subsystem.
//
// The security subsystem is currently implemented as header-only interfaces in:
//   - xbase_security.hpp
//   - xbase_security_policy.hpp
//   - xbase_security_runtime.hpp
//
// Do not duplicate enum/struct/function declarations here. Earlier versions of
// this file redeclared policy::level, policy::config, runtime::context, and
// security::keychain, which created a split-interface/redefinition hazard when
// this header was included with the implementation headers.
//
// Include this facade only when a translation unit wants the complete public
// security interface without caring about the internal header split.

#include "xbase_security.hpp"
#include "xbase_security_policy.hpp"
#include "xbase_security_runtime.hpp"
