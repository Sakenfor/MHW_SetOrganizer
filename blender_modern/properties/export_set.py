"""
Export set property groups for MHW Set Organizer.

Defines the data structures for managing export sets, which contain
collections of objects to be exported together as an armor piece.
"""

from typing import Set
import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    CollectionProperty,
    PointerProperty,
)
from bpy.types import PropertyGroup

from .. import addon_config


# Poll functions for object pointers
def poll_mesh_object(self, obj: bpy.types.Object) -> bool:
    """Only allow mesh objects."""
    return obj.type == 'MESH'


def poll_empty_root(self, obj: bpy.types.Object) -> bool:
    """Only allow empty objects without parents (roots)."""
    return (
        obj.type == 'EMPTY' and
        obj.parent is None and
        obj.get('Type') != addon_config.TYPE_CTC_HEADER
    )


def poll_ctc_header(self, obj: bpy.types.Object) -> bool:
    """Only allow objects marked as CTC headers."""
    return obj.get('Type') == addon_config.TYPE_CTC_HEADER


def update_export_path(self, context):
    """Update the export path when armor settings change."""
    from ..utils import file_utils

    scene = context.scene
    mhw = scene.mhw_data

    # Handle batch export override
    batch_custom_path = None
    batch_native_override = None

    if self.is_batch and len(mhw.batch_sets) > 0:
        current_batch_index = mhw.batch_set_index
        if current_batch_index < len(mhw.batch_sets):
            batch_set = mhw.batch_sets[current_batch_index]
            if batch_set.use_sets_path:
                batch_custom_path = batch_set.sets_path
            batch_native_override = batch_set.use_native_pc_structure

    # Get armor name
    armor_id = None
    if self.armor_name:
        for armor in mhw.armor_database:
            if armor.name == self.armor_name:
                armor_id = armor.armor_id
                break

    if not armor_id:
        armor_id = 'pl_CHOOSE_ARMOR'

    # Construct export path
    custom_path = batch_custom_path or self.custom_export_path
    use_native = batch_native_override if batch_native_override is not None else self.use_native_pc_structure

    self.export_path = file_utils.construct_export_path(
        game_path=mhw.game_path,
        armor_name=armor_id,
        armor_part=self.armor_part,
        gender=self.gender,
        use_native_structure=use_native,
        custom_path=custom_path if custom_path else None
    )

    # Also construct import path
    if mhw.resource_path:
        native_part = f'pl/{self.gender}_equip/{armor_id}/{self.armor_part}/mod'
        filename = f'{self.gender}_{self.armor_part}{armor_id[2:]}'
        self.import_path = f'{mhw.resource_path}/chunkG0/{native_part}/{filename}'


class MHW_PG_ObjectTag(PropertyGroup):
    """A tag assigned to vertices for weight transfer."""

    use: BoolProperty(
        name="Use Tag",
        description="Toggle this tag on or off for weight transfer",
        default=True
    )

    count: IntProperty(
        name="Vertex Count",
        description="Number of vertices with this tag",
        default=0
    )


class MHW_PG_ExportSetObject(PropertyGroup):
    """
    An object within an export set.

    Represents a single mesh object with its export settings.
    """

    # Object reference
    obje: PointerProperty(
        name="Object",
        description="Mesh object to export",
        type=bpy.types.Object,
        poll=poll_mesh_object
    )

    # Export settings
    export: BoolProperty(
        name="Export",
        description="Include this object in export",
        default=True
    )

    preserve_quad: BoolProperty(
        name="Preserve Quads",
        description="Make a copy and triangulate it, preserving the original mesh",
        default=False
    )

    apply_hooks: BoolProperty(
        name="Apply Hook Modifiers",
        description="Apply hook modifiers on export (object will remain unchanged)",
        default=True
    )

    # Shape key settings
    apply_shape_key: BoolProperty(
        name="Apply Shape Key",
        description="Apply shape key on export",
        default=True
    )

    shape_key_choice: StringProperty(
        name="Shape Key",
        description="Specific shape key to apply for this object",
        default=""
    )

    # Material override
    material_name: StringProperty(
        name="Material Name Override",
        description="Override the material property name on export",
        default=""
    )

    # Weight transfer settings
    tag: StringProperty(
        name="Weight Transfer Tags",
        description="Tags for weight transfer, separated by commas (e.g. 'chest,arms')",
        default=""
    )

    tags: CollectionProperty(
        type=MHW_PG_ObjectTag,
        name="Tag Collection"
    )

    accept_weight_transfer: BoolProperty(
        name="Accept Weight Transfer",
        description="Allow weight transfer to this object (requires a tag)",
        default=True
    )

    accept_weight_smoothing: BoolProperty(
        name="Accept Weight Smoothing",
        description="Allow weight smoothing during CTC copy operation",
        default=True
    )

    # Normal transfer
    normals_source: PointerProperty(
        name="Normals Source",
        description="Object to transfer custom normals from",
        type=bpy.types.Object,
        poll=poll_mesh_object
    )

    # Internal flags
    to_copy: BoolProperty(
        name="To Copy",
        description="Internal flag for copy operations",
        default=False
    )


class MHW_PG_ExportSet(PropertyGroup):
    """
    Main export set containing objects and export configuration.

    An export set represents a single armor piece (e.g., chest armor)
    with all its associated meshes and settings.
    """

    # Set identification
    name: StringProperty(
        name="Set Name",
        description="Name of this export set",
        default="New Set"
    )

    # Object collection
    eobjs: CollectionProperty(
        type=MHW_PG_ExportSetObject,
        name="Export Objects"
    )

    object_index: IntProperty(
        name="Active Object Index",
        description="Currently selected object in the list",
        default=0
    )

    # Armor settings
    armor_name: StringProperty(
        name="Armor Set",
        description="Armor set identifier",
        default="",
        update=update_export_path
    )

    armor_part: EnumProperty(
        name="Armor Part",
        description="Which armor piece this set represents",
        items=[
            (part, part.capitalize(), f"{part.capitalize()} armor piece")
            for part in addon_config.ARMOR_PARTS
        ],
        default='body',
        update=update_export_path
    )

    gender: EnumProperty(
        name="Gender",
        description="Gender variant of the armor",
        items=[
            ('f', "Female", "Female armor variant"),
            ('m', "Male", "Male armor variant"),
        ],
        default='f',
        update=update_export_path
    )

    # Root objects
    empty_root: PointerProperty(
        name="Skeleton Root",
        description="Root empty object for the bone hierarchy",
        type=bpy.types.Object,
        poll=poll_empty_root
    )

    ctc_header: PointerProperty(
        name="CTC Header",
        description="CTC physics header object",
        type=bpy.types.Object,
        poll=poll_ctc_header
    )

    # Export paths
    use_native_pc_structure: BoolProperty(
        name="Use Native PC Structure",
        description="Use the nativePC folder structure in export path",
        default=True,
        update=update_export_path
    )

    custom_export_path: StringProperty(
        name="Custom Export Path",
        description="Custom directory for export (overrides game path)",
        default="",
        subtype='DIR_PATH',
        update=update_export_path
    )

    use_custom_path: BoolProperty(
        name="Use Custom Path",
        description="Use the custom export path instead of game path",
        default=False,
        update=update_export_path
    )

    export_path: StringProperty(
        name="Export Path",
        description="Computed export path (read-only)",
        default=""
    )

    import_path: StringProperty(
        name="Import Path",
        description="Computed import path (read-only)",
        default=""
    )

    # CTC copy settings
    header_copy_source: PointerProperty(
        name="CTC Source",
        description="CTC header to copy from",
        type=bpy.types.Object,
        poll=poll_ctc_header
    )

    ext_header_copy_name: StringProperty(
        name="External CTC Source",
        description="External CTC source from blend file",
        default=""
    )

    align_frames: BoolProperty(
        name="Align Frames",
        description="Align CTC frames in hierarchy on export",
        default=True
    )

    align_nodes: BoolProperty(
        name="Align Nodes",
        description="Align CTC nodes to bones on export",
        default=False
    )

    # Shape key settings
    use_shape_keys: BoolProperty(
        name="Use Shape Keys",
        description="Apply shape keys on export",
        default=True
    )

    shape_key_method: EnumProperty(
        name="Shape Key Method",
        description="How to apply shape keys",
        items=[
            ('GLOBAL', "Global Key Name", "Use same key name for all objects"),
            ('ACTIVE', "Active Keys", "Apply all active shape keys"),
            ('SPECIFIC', "Specific Keys", "Use per-object key assignment"),
        ],
        default='ACTIVE'
    )

    shape_key_choice: StringProperty(
        name="Global Shape Key",
        description="Shape key name to apply to all objects (if using global method)",
        default=""
    )

    # Object copy source
    copy_obj_src: PointerProperty(
        name="Copy Source",
        description="Source object for copy/replace operations",
        type=bpy.types.Object,
        poll=poll_mesh_object
    )

    # MOD3 export options
    split_normals: BoolProperty(
        name="Use Custom Normals",
        description="Use split/custom normals instead of Blender auto-generated normals",
        default=True
    )

    highest_lod: BoolProperty(
        name="Highest LOD",
        description="Set all mesh parts to highest level of detail",
        default=True
    )

    coerce_fourth: BoolProperty(
        name="Coerce 4th Weight",
        description="Force non-explicit 4-weight vertices into 4-weight block type",
        default=True
    )

    # Import options
    clear_scene: BoolProperty(
        name="Clear Scene",
        description="Clear all scene contents before importing",
        default=False
    )

    maximize_clipping: BoolProperty(
        name="Maximize Clipping",
        description="Set far clipping distance to see entire model",
        default=True
    )

    high_lod: BoolProperty(
        name="High LOD Only",
        description="Only import high level of detail mesh parts",
        default=True
    )

    import_header: BoolProperty(
        name="Import Header",
        description="Import file headers as scene properties",
        default=True
    )

    import_meshparts: BoolProperty(
        name="Import Mesh Parts",
        description="Import mesh parts as meshes",
        default=True
    )

    import_textures: BoolProperty(
        name="Import Textures",
        description="Import textures as specified by MRL3",
        default=True
    )

    import_materials: BoolProperty(
        name="Import Materials",
        description="Import materials as specified by MRL3",
        default=False
    )

    load_group_functions: BoolProperty(
        name="Load Bounding Boxes",
        description="Load MOD3 as bounding boxes",
        default=False
    )

    texture_path: StringProperty(
        name="Texture Source",
        description="Root directory for textures (Native PC if importing from chunk)",
        default="",
        subtype='DIR_PATH'
    )

    import_skeleton: EnumProperty(
        name="Import Skeleton",
        description="How to import the skeleton",
        items=[
            ('NONE', "Don't Import", "Do not import skeleton"),
            ('EMPTY', "Empty Tree", "Import as tree of empties"),
            ('ARMATURE', "Armature", "Import as Blender armature"),
        ],
        default='EMPTY'
    )

    weight_format: EnumProperty(
        name="Weight Format",
        description="How to handle vertex weights",
        items=[
            ('GROUP', "Standard", "Group weights under same bone"),
            ('SPLIT', "Split Notation", "Mirror MOD3 weight separation"),
            ('SLASH', "Split-Slash", "Split weights with order preservation"),
        ],
        default='GROUP'
    )

    # CTC import options
    ctc_missing_function_behaviour: EnumProperty(
        name="Missing Bone Functions",
        description="What to do when encountering missing bone functions",
        items=[
            ('ABORT', "Abort", "Abort import process"),
            ('TRUNCATE', "Truncate", "Truncate chain at offending node"),
            ('NULL', "Null", "Set constraint target to null and continue"),
        ],
        default='NULL'
    )

    # CCL import options
    ccl_scale: FloatProperty(
        name="CCL Scale",
        description="Multiply collision sphere radii (Factor of 2 according to Statyk)",
        default=1.0,
        min=0.1,
        max=10.0
    )

    ccl_missing_function_behaviour: EnumProperty(
        name="Missing Bone Functions (CCL)",
        description="What to do when encountering missing bone functions in CCL",
        items=[
            ('ABORT', "Abort", "Abort import process"),
            ('OMIT', "Omit", "Omit the entire sphere"),
            ('NULL', "Null", "Set constraint target to null"),
        ],
        default='NULL'
    )

    # UI toggles
    show_ctc_manager: BoolProperty(
        name="Show CTC Manager",
        description="Show CTC copy source manager",
        default=False
    )

    more_obj_options: BoolProperty(
        name="More Object Options",
        description="Show additional per-object options",
        default=True
    )

    obj_view_mode: EnumProperty(
        name="Object View Mode",
        description="What to display for each object",
        items=[
            ('NONE', "None", "No additional options"),
            ('SHAPE_KEYS', "Shape Keys", "Show shape key options"),
            ('OTHER', "Other", "Show other options"),
        ],
        default='NONE'
    )

    toggler_hide_select: BoolProperty(
        name="Toggle Hide Select",
        description="Toggle hide select on set objects",
        default=False
    )

    # Internal flags
    is_batch: BoolProperty(
        name="Is Batch Export",
        description="Internal flag indicating batch export mode",
        default=False
    )


# Classes to register
classes = (
    MHW_PG_ObjectTag,
    MHW_PG_ExportSetObject,
    MHW_PG_ExportSet,
)


def register():
    """Register export set property groups."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister export set property groups."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
