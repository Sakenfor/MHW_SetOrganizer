"""
Main settings property groups for MHW Set Organizer.

Defines the root settings structure that holds all addon data,
including armor database, export sets, and configuration.
"""

import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    CollectionProperty,
    PointerProperty,
)
from bpy.types import PropertyGroup


def poll_armature(self, obj: bpy.types.Object) -> bool:
    """Only allow armature objects."""
    return obj.type == 'ARMATURE'


class MHW_PG_ArmorEntry(PropertyGroup):
    """
    Entry in the armor database.

    Maps armor IDs to display names for the UI.
    """

    # Display name (e.g., "Leather (pl001_0000)")
    name: StringProperty(
        name="Armor Name",
        description="Display name for this armor set",
        default=""
    )

    # Armor ID (e.g., "pl001_0000")
    armor_id: StringProperty(
        name="Armor ID",
        description="Armor set identifier used in file paths",
        default=""
    )


class MHW_PG_BlendAppendPath(PropertyGroup):
    """
    Path to a blend file for appending CTC sources.
    """

    path: StringProperty(
        name="Blend File Path",
        description="Path to .blend file containing CTC sources",
        default="",
        subtype='FILE_PATH'
    )


class MHW_PG_ExternalCTCSource(PropertyGroup):
    """
    Reference to a CTC source in an external blend file.
    """

    # Unique identifier (blend filename + object name)
    name: StringProperty(
        name="Source Name",
        description="Unique name for this CTC source",
        default=""
    )

    blend: StringProperty(
        name="Blend File",
        description="Path to blend file",
        default=""
    )

    folder: StringProperty(
        name="Folder",
        description="Folder containing the blend file",
        default=""
    )


class MHW_PG_Settings(PropertyGroup):
    """
    Main addon settings property group.

    This is registered to bpy.types.Scene and contains all addon data.
    """

    # ===== Paths =====
    game_path: StringProperty(
        name="Game Path",
        description="Path to Monster Hunter World installation directory",
        default="",
        subtype='DIR_PATH'
    )

    resource_path: StringProperty(
        name="Resource Path",
        description="Path to MHW resources for importing",
        default="",
        subtype='DIR_PATH'
    )

    # ===== Export Sets =====
    export_sets: CollectionProperty(
        type='MHW_PG_ExportSet',  # Forward reference, will be resolved at registration
        name="Export Sets"
    )

    active_export_set_index: IntProperty(
        name="Active Set Index",
        description="Currently selected export set",
        default=0
    )

    # ===== Batch Export (Sets of Sets) =====
    batch_sets: CollectionProperty(
        type='MHW_PG_SetOfSets',  # Forward reference
        name="Batch Sets"
    )

    active_batch_index: IntProperty(
        name="Active Batch Index",
        description="Currently selected batch set",
        default=0
    )

    # ===== Armor Database =====
    armor_database: CollectionProperty(
        type=MHW_PG_ArmorEntry,
        name="Armor Database"
    )

    # ===== Blend Append Paths =====
    blend_append_paths: CollectionProperty(
        type=MHW_PG_BlendAppendPath,
        name="Blend Append Paths"
    )

    blend_append_path_index: IntProperty(
        name="Active Append Path Index",
        description="Currently selected blend append path",
        default=0
    )

    # ===== External CTC Sources =====
    external_ctc_sources: CollectionProperty(
        type=MHW_PG_ExternalCTCSource,
        name="External CTC Sources"
    )

    # ===== UI Toggles =====
    show_import_options: BoolProperty(
        name="Show Import Options",
        description="Show import configuration options",
        default=False
    )

    show_export_options: BoolProperty(
        name="Show Export Options",
        description="Show export configuration options",
        default=False
    )

    show_batch_sets: BoolProperty(
        name="Show Batch Sets",
        description="Show batch export (Sets of Sets) panel",
        default=False
    )

    show_export_sets: BoolProperty(
        name="Show Export Sets",
        description="Show main export sets panel",
        default=True
    )

    show_ctc_copier: BoolProperty(
        name="Show CTC Copier",
        description="Show CTC header copier panel",
        default=False
    )

    show_main_sets: BoolProperty(
        name="Show Main Sets",
        description="Show main export sets panel (legacy name)",
        default=True
    )

    show_header_copy: BoolProperty(
        name="Show Header Copy",
        description="Show CTC header copy panel (legacy name)",
        default=False
    )

    show_blend_paths: BoolProperty(
        name="Show Blend Paths",
        description="Show blend file append paths",
        default=False
    )

    show_resource_list: BoolProperty(
        name="Show Resource List",
        description="Show list of external CTC resources",
        default=False
    )

    # ===== CTC Copy Settings =====
    ctc_prepend_text: StringProperty(
        name="Prepend Text",
        description="Text to prepend to copied CTC object names",
        default=""
    )

    ctc_new_name: StringProperty(
        name="New Name",
        description="Base name for renamed CTC objects",
        default=""
    )

    ctc_type_prefix: BoolProperty(
        name="Type Name Prefix",
        description="Put object type before name instead of after",
        default=False
    )

    # Legacy names (keep for backward compatibility)
    header_copy_prepend: StringProperty(
        name="Prepend Text (Legacy)",
        description="Text to prepend to copied CTC object names (legacy property)",
        default=""
    )

    header_new_names: StringProperty(
        name="New Name (Legacy)",
        description="Base name for renamed CTC objects (legacy property)",
        default=""
    )

    type_name_prefix: BoolProperty(
        name="Type Name Prefix (Legacy)",
        description="Put object type before name instead of after (legacy property)",
        default=False
    )

    ctc_copy_use_active: BoolProperty(
        name="Use Active Object",
        description="Use active object as target instead of set's root",
        default=False
    )

    ctc_copy_add_lr: BoolProperty(
        name="Add .L/.R Suffixes",
        description="Add .L/.R suffixes to bone names based on position",
        default=True
    )

    ctc_copy_add_vg: BoolProperty(
        name="Add Vertex Groups",
        description="Create vertex groups for copied bones",
        default=True
    )

    # ===== Operator Properties =====
    # These are used by operators since they can't have PointerProperty directly
    vg_rename_armature: PointerProperty(
        name="Armature for VG Rename",
        description="Armature to use for vertex group renaming",
        type=bpy.types.Object,
        poll=poll_armature
    )


# Classes to register
classes = (
    MHW_PG_ArmorEntry,
    MHW_PG_BlendAppendPath,
    MHW_PG_ExternalCTCSource,
    MHW_PG_Settings,
)


def register():
    """Register settings property groups."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister settings property groups."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
