"""
Data models for EPUB parsing.
"""
from .dublin_core import (
    DublinCoreMetadata,
    DublinCoreCreator,
    DublinCoreDate,
    DublinCoreSubject,
    DublinCoreIdentifier,
    ParsedContentOpf
)

from .structure import (
    EpubStructure,
    StructureItem,
    ImageItem,
    NavigationPoint,
    ContentOrganization,
    ContentType
)

# Rebuild models to fix forward references
try:
    ParsedContentOpf.model_rebuild()
except BaseException:
    pass

__all__ = [
    # Dublin Core models
    'DublinCoreMetadata',
    'DublinCoreCreator',
    'DublinCoreDate',
    'DublinCoreSubject',
    'DublinCoreIdentifier',
    'ParsedContentOpf',

    # Structure models
    'EpubStructure',
    'StructureItem',
    'ImageItem',
    'NavigationPoint',
    'ContentOrganization',
    'ContentType'
]
