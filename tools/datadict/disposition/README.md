# Data Dictionary Disposition Tools

`artifact_disposition.py` classifies DD-025/DD-028 review rows into Data Dictionary self-change, tooling change, generated maintenance package evidence, manualgen evidence, source drift, runtime script change, and related disposition buckets.

This lane is report-only. It does not edit source, run builds, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, or promote dictionary facts.
