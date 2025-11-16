"""
Batch export property groups for MHW Set Organizer.

Defines data structures for "Sets of Sets" - batch exporting multiple
armor sets with shared settings.
"""

import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    CollectionProperty,
)
from bpy.types import PropertyGroup


class MHW_PG_SetOfSetsObject(PropertyGroup):
    """
    Reference to an export set within a batch export group.
    """

    # This is just a name reference, the actual set is looked up
    # in the main export_sets collection by name
    name: StringProperty(
        name="Set Name",
        description="Name of the export set to include",
        default=""
    )

    export: BoolProperty(
        name="Export",
        description="Include this set in batch export",
        default=True
    )


class MHW_PG_SetOfSets(PropertyGroup):
    """
    Batch export group containing multiple export sets.

    Allows exporting multiple armor pieces with shared settings
    in a single operation.
    """

    # Group identification
    name: StringProperty(
        name="Batch Name",
        description="Name for this batch export group",
        default="New Batch"
    )

    # Sets in this batch
    eobjs: CollectionProperty(
        type=MHW_PG_SetOfSetsObject,
        name="Sets"
    )

    object_index: IntProperty(
        name="Active Set Index",
        description="Currently selected set in the list",
        default=0
    )

    # Shared export path
    sets_path: StringProperty(
        name="Batch Export Path",
        description="Shared export path for all sets in this batch",
        default="",
        subtype='DIR_PATH'
    )

    use_sets_path: BoolProperty(
        name="Use Batch Path",
        description="Use the batch export path instead of per-set paths",
        default=True
    )

    # What to export
    export_mod3: BoolProperty(
        name="Export MOD3",
        description="Export mesh files (.mod3)",
        default=True
    )

    export_ctc: BoolProperty(
        name="Export CTC",
        description="Export cloth physics files (.ctc)",
        default=False
    )

    export_ccl: BoolProperty(
        name="Export CCL",
        description="Export collision capsule files (.ccl)",
        default=False
    )

    # Path settings
    use_native_pc_structure: BoolProperty(
        name="Use Native PC Structure",
        description="Apply nativePC folder structure to batch path",
        default=False
    )

    allow_per_set_custom_path: BoolProperty(
        name="Allow Per-Set Custom Paths",
        description="Allow individual sets to use their custom export paths",
        default=False
    )


# Classes to register
classes = (
    MHW_PG_SetOfSetsObject,
    MHW_PG_SetOfSets,
)


def register():
    """Register batch export property groups."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister batch export property groups."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
