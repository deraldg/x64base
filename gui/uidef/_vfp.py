"""Load the TRACKED VFP binary reader, by path, so nothing can shadow it.

AIF-120 R87. Eleven files in this directory said `from read_vfp_binary import
Dbf`. Every one of them worked, and every one of them worked for the wrong
reason: `gui/uidef/read_vfp_binary.py` is a GITIGNORED working copy, and it is
what they were importing. The tracked file is `tools/vfp/read_vfp_binary.py`.

Seven of the eleven already carried a fix for this -- and the fix was wrong:

    sys.path.insert(0, os.path.join(HERE, '..', 'vfp'))    # -> gui/vfp

`gui/vfp` does not exist. From `gui/uidef` the tracked directory is
`../../tools/vfp`. So the correction was written, commented ("tools/vfp goes on
the path FIRST so the ignored copy can never shadow it"), believed, and never
did anything; the ignored copy answered every import and the mistake was
invisible to anyone whose tree contained it. Which is everyone who had ever run
the tools once.

That makes this a clean-clone defect, and a clean clone is exactly what an MSVC
build on a fresh Windows checkout is. `uidef_wx.py` is a CMake custom command
(`gui/uidef/CMakeLists.txt`), so on a fresh checkout the R76 target fails while
GENERATING its source, before a compiler is ever invoked.

Two decisions worth stating:

- **Loaded by explicit path, not by `sys.path`.** Every importer also inserts its
  own directory, so a path-order fix depends on which insert ran last -- which is
  how the original fix could look right. `importlib` on an absolute filename has
  no ordering to get wrong, and the ignored copy becomes unreachable rather than
  merely lower-priority.
- **It raises rather than falling back.** A fallback to the ignored copy would
  restore exactly the silence being removed.
"""
import importlib.util
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
TRACKED = os.path.normpath(os.path.join(_HERE, '..', '..', 'tools', 'vfp',
                                        'read_vfp_binary.py'))

if not os.path.isfile(TRACKED):
    raise ImportError(
        "gui/uidef/_vfp.py: the tracked VFP reader is missing.\n"
        "  expected: %s\n"
        "  This file is the ONLY supported source. gui/uidef/read_vfp_binary.py\n"
        "  is a gitignored working copy and is deliberately not used." % TRACKED)

_spec = importlib.util.spec_from_file_location('dottalk_read_vfp_binary', TRACKED)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

Dbf = _mod.Dbf
