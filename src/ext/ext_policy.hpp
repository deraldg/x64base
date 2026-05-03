#pragma once

/*
    Student Extension Contract
    --------------------------

    DotTalk++ has a protected built-in CLI command surface and an open extension layer.

    Rules:

    1. Built-in CLI commands are protected.
       They must be registered only through the central shell/bootstrap path.

    2. Custom/student CLI commands may self-register.
       These belong in the extension area, not in the built-in CLI command area.

    3. Function families such as strings, dates, formulas, predicates, and other
       expression helpers may self-register.

    4. Built-in CLI command names are reserved.
       Student/custom extensions must not self-register names such as LIST, USE,
       DELETE, SEEK, RECALL, HELP, APPEND, or REPLACE.

    5. No symbol may be registered by both mechanisms at once.

    6. DotTalk++ is a compact teaching sandbox.
       If an experiment damages the working copy, the normal recovery path is to
       discard it and unzip a fresh clean copy.

    Intent:

    - protect the native command surface
    - allow student experimentation
    - keep extensions clearly separated from the core system
*/
