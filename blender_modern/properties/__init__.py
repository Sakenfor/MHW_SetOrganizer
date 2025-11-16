"""
Property groups for MHW Set Organizer.

This module defines all Blender property groups used by the addon.
Property groups are registered to store addon data in the Blender file.
"""

import bpy
from bpy.props import PointerProperty, CollectionProperty

# Import all property group modules
from . import export_set
from . import ctc_properties
from . import batch_export
from . import export_history
from . import export_presets
from . import settings

# List of modules in registration order (dependencies first)
_modules = [
    export_set,
    ctc_properties,
    batch_export,
    export_history,
    export_presets,
    settings,
]


def register():
    """Register all property groups."""
    # Register modules
    for module in _modules:
        if hasattr(module, 'register'):
            module.register()

    # Register main settings property to Scene
    # This must happen after all property groups are registered
    # so forward references are resolved
    bpy.types.Scene.mhw_data = PointerProperty(
        type=settings.MHW_PG_Settings,
        name="MHW Set Organizer Data",
        description="Monster Hunter World Set Organizer addon data"
    )

    # Resolve forward references in settings
    # These couldn't be set directly due to circular dependencies
    settings.MHW_PG_Settings.__annotations__['export_sets'] = CollectionProperty(
        type=export_set.MHW_PG_ExportSet,
        name="Export Sets"
    )

    settings.MHW_PG_Settings.__annotations__['batch_sets'] = CollectionProperty(
        type=batch_export.MHW_PG_SetOfSets,
        name="Batch Sets"
    )

    # Add CTC properties to export sets
    export_set.MHW_PG_ExportSet.__annotations__['ctc_copy_sources'] = CollectionProperty(
        type=ctc_properties.MHW_PG_CTCCopySource,
        name="CTC Copy Sources"
    )

    export_set.MHW_PG_ExportSet.__annotations__['ctc_organizers'] = CollectionProperty(
        type=ctc_properties.MHW_PG_CTCOrganizer,
        name="CTC Organizers"
    )

    # Add export history to settings
    settings.MHW_PG_Settings.__annotations__['export_history'] = CollectionProperty(
        type=export_history.MHW_PG_ExportHistoryEntry,
        name="Export History"
    )

    # Add export presets to settings
    settings.MHW_PG_Settings.__annotations__['export_presets'] = CollectionProperty(
        type=export_presets.MHW_PG_ExportPreset,
        name="Export Presets"
    )


def unregister():
    """Unregister all property groups."""
    # Remove scene property
    if hasattr(bpy.types.Scene, 'mhw_data'):
        del bpy.types.Scene.mhw_data

    # Unregister modules in reverse order
    for module in reversed(_modules):
        if hasattr(module, 'unregister'):
            module.unregister()


# Export all classes for external use
__all__ = [
    'export_set',
    'ctc_properties',
    'batch_export',
    'export_history',
    'settings',
]
