# Blackbox and Maintenance Language Note v1

Blackbox is the educational model: data goes in, processing happens, information comes out.

Maintenance is the SDLC control layer around those blackboxes. Because maintenance procedures are intended to be repeatable across platforms, permanent maintenance launchers should be Python 3.12 rather than PowerShell.

PowerShell may still be used by MDO packages to create or stage artifacts on the current Windows workstation.
