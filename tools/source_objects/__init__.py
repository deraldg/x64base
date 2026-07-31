"""Source files as reusable, provenance-aware objects."""

from .model import ContractBlock, SourceObject, SourceSection
from .parser import parse_source_file, parse_source_text

__all__ = [
    "ContractBlock",
    "SourceObject",
    "SourceSection",
    "parse_source_file",
    "parse_source_text",
]
