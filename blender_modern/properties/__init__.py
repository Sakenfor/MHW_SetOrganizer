"""
Property groups for MHW Set Organizer.

This module defines all Blender property groups used by the addon.
Property groups are registered to store addon data in the Blender file.
"""

import bpy
from bpy.props import PointerProperty

from .export_set import (
    MHW_PG_ExportSetObject,
    MHW_PG_ExportSet,
)
from .ctc_properties import (
    MHW_PG_CTCCopyTrack,
    MHW_PG_CTCCopySource,
    MHW_PG_CTCOrganizer,
    MHW_PG_CTCChainEntry,
    MHW_PG_CTCMaterialChoice,
)
from .settings import (
    MHW_PG_Settings,
    MHW_PG_ArmorEntry,
    MHW_PG_BlendAppendPath,
    MHW_PG_ExternalCTCSource,
)
from .batch_export import (
    MHW_PG_SetOfSetsObject,
    MHW_PG_SetOfSets,
)

# List of all property group classes
classes = (
    # Export set properties
    MHW_PG_ExportSetObject,
    MHW_PG_ExportSet,

    # CTC properties
    MHW_PG_CTCCopyTrack,
    MHW_PG_CTCCopySource,
    MHW_PG_CTCOrganizer,
    MHW_PG_CTCChainEntry,
    MHW_PG_CTCMaterialChoice,

    # Settings
    MHW_PG_ArmorEntry,
    MHW_PG_BlendAppendPath,
    MHW_PG_ExternalCTCSource,
    MHW_PG_Settings,

    # Batch export
    MHW_PG_SetOfSetsObject,
    MHW_PG_SetOfSets,
)


def register():
    """Register all property groups."""
    for cls in classes:
        bpy.utils.register_class(cls)

    # Register main settings property to Scene
    bpy.types.Scene.mhw_data = PointerProperty(
        type=MHW_PG_Settings,
        name="MHW Set Organizer Data",
        description="Monster Hunter World Set Organizer addon data"
    )


def unregister():
    """Unregister all property groups."""
    # Remove scene property
    del bpy.types.Scene.mhw_data

    # Unregister classes in reverse order
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


__all__ = [
    'MHW_PG_ExportSetObject',
    'MHW_PG_ExportSet',
    'MHW_PG_CTCCopyTrack',
    'MHW_PG_CTCCopySource',
    'MHW_PG_CTCOrganizer',
    'MHW_PG_CTCChainEntry',
    'MHW_PG_CTCMaterialChoice',
    'MHW_PG_Settings',
    'MHW_PG_ArmorEntry',
    'MHW_PG_BlendAppendPath',
    'MHW_PG_ExternalCTCSource',
    'MHW_PG_SetOfSetsObject',
    'MHW_PG_SetOfSets',
]
