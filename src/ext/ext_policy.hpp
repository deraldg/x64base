#pragma once

// @dottalk.contract v1
// component: extension_policy
// role: declares the protected core versus student/custom extension boundary
// owner: DotTalk++ CLI extension lane
// authority: source-policy annotation for the extension contract
// docs: docs/contracts/DOTTALK_EXTENSION_EXIT_CONTRACT_V1.md
// usage_contract_lane: C++ commands use @dottalk.usage; non-C++ artifacts are manifest-controlled and curated until language miners exist.
// document_control: dottalkpp/user/exits stores reviewed local/student artifacts outside the core upgrade path.
// @dottalk.contract.end

/*
    Student Extension Contract
    --------------------------

    DotTalk++ has a protected built-in CLI command surface and an open extension layer.

    Rules:

    1. Built-in CLI commands are protected.
       They must be registered only through the central shell/bootstrap path.

    2. Custom/student CLI commands may self-register only from the extension
       area and must use custom names. The preferred custom prefixes are Z_,
       Y_, and STU_.

    3. Function families such as strings, dates, formulas, predicates, and other
       expression helpers may self-register.

    4. Built-in CLI command names are reserved.
       Student/custom extensions must not self-register names such as LIST, USE,
       DELETE, SEEK, RECALL, HELP, APPEND, or REPLACE.

    5. No symbol may be registered by both mechanisms at once.

    6. C++ extension commands that expose user-facing behavior should carry
       @dottalk.usage v1 blocks and runtime USAGE/HELP/? branches.

    7. Non-C++ extension artifacts are stored and curated through manifest
       control. They are not mined for usage contracts until language-specific
       tooling exists.

    8. Runtime exits should start observe-only and disabled-by-default. External
       process execution requires explicit enablement, a timeout, and logging.

    9. DotTalk++ is a compact teaching sandbox.
       If an experiment damages the working copy, the normal recovery path is to
       discard it and unzip a fresh clean copy.

    Intent:

    - protect the native command surface
    - allow student experimentation
    - keep extensions clearly separated from the core system
    - preserve non-C++ student work through a document-control process before
      treating it as executable runtime authority
*/
