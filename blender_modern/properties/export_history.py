"""
Export history property groups for MHW Set Organizer.

Tracks export operations for easy re-export and debugging.
"""

import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    EnumProperty,
)
from bpy.types import PropertyGroup
from datetime import datetime


class MHW_PG_ExportHistoryEntry(PropertyGroup):
    """A single export history entry."""

    # Export info
    export_set_name: StringProperty(
        name="Export Set",
        description="Name of the export set that was exported",
        default=""
    )

    export_type: EnumProperty(
        name="Export Type",
        description="Type of file that was exported",
        items=[
            ('MOD3', "MOD3", "Mesh file"),
            ('CTC', "CTC", "Cloth physics file"),
            ('CCL', "CCL", "Collision capsule file"),
            ('BATCH', "Batch", "Batch export"),
        ],
        default='MOD3'
    )

    file_path: StringProperty(
        name="File Path",
        description="Full path to the exported file",
        default="",
        subtype='FILE_PATH'
    )

    # Timestamp
    timestamp: StringProperty(
        name="Timestamp",
        description="When the export occurred",
        default=""
    )

    # Success status
    success: BoolProperty(
        name="Success",
        description="Whether the export succeeded",
        default=True
    )

    error_message: StringProperty(
        name="Error Message",
        description="Error message if export failed",
        default=""
    )

    # Export settings (for re-export)
    split_normals: BoolProperty(default=True)
    highest_lod: BoolProperty(default=True)
    coerce_fourth: BoolProperty(default=True)
    align_frames: BoolProperty(default=False)
    align_nodes: BoolProperty(default=False)


def add_export_history_entry(
    context,
    export_set_name: str,
    export_type: str,
    file_path: str,
    success: bool,
    error_message: str = "",
    **settings
):
    """
    Add an entry to the export history.

    Args:
        context: Blender context
        export_set_name: Name of the export set
        export_type: Type of export ('MOD3', 'CTC', 'CCL', 'BATCH')
        file_path: Path to exported file
        success: Whether export succeeded
        error_message: Error message if failed
        **settings: Export settings to store
    """
    mhw = context.scene.mhw_data

    # Create new entry
    entry = mhw.export_history.add()

    # Set basic info
    entry.export_set_name = export_set_name
    entry.export_type = export_type
    entry.file_path = file_path
    entry.success = success
    entry.error_message = error_message

    # Set timestamp
    entry.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Store export settings
    for key, value in settings.items():
        if hasattr(entry, key):
            setattr(entry, key, value)

    # Keep only last 100 entries
    while len(mhw.export_history) > 100:
        mhw.export_history.remove(0)


# Classes to register
classes = (
    MHW_PG_ExportHistoryEntry,
)


def register():
    """Register export history property groups."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister export history property groups."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
