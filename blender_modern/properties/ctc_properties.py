"""
CTC (Cloth Physics) property groups for MHW Set Organizer.

Defines data structures for tracking CTC copy operations, bone mappings,
and weight transfer settings.
"""

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


def poll_mesh_object(self, obj: bpy.types.Object) -> bool:
    """Only allow mesh objects."""
    return obj.type == 'MESH'


class MHW_PG_VertexGroupRef(PropertyGroup):
    """Reference to a vertex group created during CTC copy."""

    obje: PointerProperty(
        name="Object",
        description="Object containing the vertex group",
        type=bpy.types.Object
    )


class MHW_PG_CTCCopyTrack(PropertyGroup):
    """
    Tracks a single object copied during CTC copy operation.

    Stores both the source object and the created copy, along with
    bone function mappings and metadata.
    """

    # Object references
    caster: PointerProperty(
        name="Source Object",
        description="Original object that was copied from",
        type=bpy.types.Object
    )

    o2: PointerProperty(
        name="Target Object",
        description="The created copy",
        type=bpy.types.Object
    )

    pair: PointerProperty(
        name="Mirror Pair",
        description="The mirror bone (L/R opposite)",
        type=bpy.types.Object
    )

    ctc_src: PointerProperty(
        name="CTC Source",
        description="Source CTC header",
        type=bpy.types.Object
    )

    armature: PointerProperty(
        name="Target Armature",
        description="Target armature root",
        type=bpy.types.Object
    )

    # Type and metadata
    ttype: StringProperty(
        name="Object Type",
        description="Type of object (Bone, CTC, CTC_Chain, etc.)",
        default=""
    )

    id_name: StringProperty(
        name="ID Property Name",
        description="Name of the ID property (boneFunction or boneFunctionID)",
        default=""
    )

    # Bone function IDs
    bone_id: IntProperty(
        name="Bone Function ID",
        description="Original bone function ID",
        default=0
    )

    changed_id: IntProperty(
        name="Changed Bone ID",
        description="New bone function ID if remapped (0 = not changed)",
        default=0
    )

    # Side detection for mirroring
    side_x: StringProperty(
        name="X Side",
        description="Left/Right side (L/R/0)",
        default=""
    )

    side_y: StringProperty(
        name="Y Side",
        description="Up/Down side (U/D/0)",
        default=""
    )

    side_z: StringProperty(
        name="Z Side",
        description="Front/Back side (F/B/0)",
        default=""
    )

    # Vertex groups created
    vertex_groups: CollectionProperty(
        type=MHW_PG_VertexGroupRef,
        name="Vertex Groups"
    )

    # UI state
    edit_view: BoolProperty(
        name="Edit View",
        description="Show edit options for this object",
        default=False
    )

    is_new: BoolProperty(
        name="Is New",
        description="This object was newly created (not pre-existing)",
        default=False
    )


class MHW_PG_CTCCopySource(PropertyGroup):
    """
    Tracks a CTC copy operation from a source to target.

    Stores all the objects that were copied and their relationships.
    """

    # Source and target
    source: PointerProperty(
        name="Source CTC",
        description="Source CTC header that was copied from",
        type=bpy.types.Object
    )

    target: PointerProperty(
        name="Target Root",
        description="Target bone hierarchy root",
        type=bpy.types.Object
    )

    # Tracked copies
    copy_src_track: CollectionProperty(
        type=MHW_PG_CTCCopyTrack,
        name="Copy Tracking"
    )

    # UI view modes
    view_mode: EnumProperty(
        name="View Mode",
        description="How to display the copied objects",
        items=[
            ('LIST', "List View", "Simple list of copies"),
            ('SOURCE', "Edit Source", "Edit source objects"),
            ('COPIES', "Edit Copies", "Edit copied objects"),
        ],
        default='COPIES'
    )

    view_toggle: BoolProperty(
        name="View Toggle",
        description="Show or hide this CTC copy group",
        default=True
    )

    # Filters
    edit_filter: StringProperty(
        name="Filter",
        description="Filter objects by name",
        default=""
    )

    filter_header: BoolProperty(
        name="Show Headers",
        description="Show CTC header objects",
        default=True
    )

    filter_chain: BoolProperty(
        name="Show Chains",
        description="Show CTC chain objects",
        default=True
    )

    filter_frame: BoolProperty(
        name="Show Frames",
        description="Show CTC frame objects",
        default=True
    )

    filter_bone: BoolProperty(
        name="Show Bones",
        description="Show bone objects",
        default=True
    )

    # Mirror settings
    mirror_direction: EnumProperty(
        name="Mirror Direction",
        description="Which direction to mirror bones",
        items=[
            ('L_TO_R', "Left to Right", "Mirror from left to right"),
            ('R_TO_L', "Right to Left", "Mirror from right to left"),
        ],
        default='L_TO_R'
    )

    insert_keyframe: BoolProperty(
        name="Insert Keyframe",
        description="Insert keyframe after mirroring",
        default=False
    )

    # UI options
    info_when_closed: BoolProperty(
        name="Info When Closed",
        description="Show some properties even when object is collapsed",
        default=False
    )

    show_copied: BoolProperty(
        name="Show Copied",
        description="Display copied objects",
        default=False
    )

    edit_source: BoolProperty(
        name="Edit Source",
        description="Edit source objects",
        default=False
    )

    edit_targets: BoolProperty(
        name="Edit Targets",
        description="Edit target objects",
        default=False
    )


class MHW_PG_CTCChainEntry(PropertyGroup):
    """A CTC chain that can be toggled for copying."""

    chain: PointerProperty(
        name="Chain",
        description="CTC chain object",
        type=bpy.types.Object
    )

    toggle: BoolProperty(
        name="Include Chain",
        description="Include this chain in copy operation",
        default=True
    )


class MHW_PG_CTCMaterialChoice(PropertyGroup):
    """Material selection for weight transfer filtering."""

    obje: PointerProperty(
        name="Object",
        description="Object with materials",
        type=bpy.types.Object,
        poll=poll_mesh_object
    )

    mate: PointerProperty(
        name="Material",
        description="Material to filter by",
        type=bpy.types.Material
    )

    toggle: BoolProperty(
        name="Use Material",
        description="Include faces with this material in weight transfer",
        default=True
    )


class MHW_PG_CTCOrganizer(PropertyGroup):
    """
    Organizer for CTC copy operations.

    Contains settings for weight transfer, cleaning, and CTC chain selection.
    """

    # Source selection
    source: PointerProperty(
        name="CTC Source",
        description="Source CTC to copy from",
        type=bpy.types.Object
    )

    # Chain selection
    entries: CollectionProperty(
        type=MHW_PG_CTCChainEntry,
        name="Chain Entries"
    )

    # Material filtering
    material_choices: CollectionProperty(
        type=MHW_PG_CTCMaterialChoice,
        name="Material Filter"
    )

    material_choice_index: IntProperty(
        name="Material Index",
        description="Active material in list",
        default=0
    )

    # Main operations
    copy_ctc: BoolProperty(
        name="Copy CTC",
        description="Copy CTC hierarchy",
        default=True
    )

    transfer_weights: BoolProperty(
        name="Transfer Weights",
        description="Transfer vertex weights during copy",
        default=True
    )

    copy_properties: BoolProperty(
        name="Copy Properties",
        description="Copy object properties from source",
        default=True
    )

    # Weight transfer settings
    weight_limit: EnumProperty(
        name="Weight Transfer Range",
        description="Which bone IDs to transfer weights for",
        items=[
            ('ALL', "All Groups", "Transfer all vertex groups"),
            ('BELOW_150', "Below 150 ID", "Only vanilla bones"),
            ('ABOVE_150', "Above 150 ID", "Only custom bones"),
        ],
        default='ALL'
    )

    # Weight cleaning
    clean_after: BoolProperty(
        name="Clean Weights",
        description="Remove low-weight vertices after transfer",
        default=True
    )

    normalize_after: BoolProperty(
        name="Normalize Weights",
        description="Normalize all vertex weights after transfer",
        default=True
    )

    limit_after: BoolProperty(
        name="Limit Total Weights",
        description="Limit weights per vertex based on mesh block label",
        default=True
    )

    smooth_after: BoolProperty(
        name="Smooth Weights",
        description="Smooth vertex weights after transfer",
        default=False
    )

    smooth_strength: FloatProperty(
        name="Smooth Strength",
        description="Strength of weight smoothing",
        default=addon_config.DEFAULT_SMOOTH_STRENGTH,
        min=0.0,
        max=1.0
    )

    smooth_count: IntProperty(
        name="Smooth Iterations",
        description="Number of smoothing passes",
        default=addon_config.DEFAULT_SMOOTH_COUNT,
        min=1,
        max=20
    )

    # Vertex group management
    remove_vg_not_found: BoolProperty(
        name="Remove Unknown Groups",
        description="Remove vertex groups not found in target bone hierarchy",
        default=True
    )

    remove_vg_before_transfer: BoolProperty(
        name="Remove Groups Before Transfer",
        description="Clean vertex groups before transferring weights",
        default=True
    )

    remove_vg_range: EnumProperty(
        name="Remove Range",
        description="Which vertex groups to remove before transfer",
        items=[
            ('ALL', "All Groups", "Remove all groups"),
            ('BELOW_150', "Below 150 ID", "Only vanilla bone groups"),
            ('ABOVE_150', "Above 150 ID", "Only custom bone groups"),
        ],
        default='ALL'
    )


# Classes to register
classes = (
    MHW_PG_VertexGroupRef,
    MHW_PG_CTCCopyTrack,
    MHW_PG_CTCCopySource,
    MHW_PG_CTCChainEntry,
    MHW_PG_CTCMaterialChoice,
    MHW_PG_CTCOrganizer,
)


def register():
    """Register CTC property groups."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister CTC property groups."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
