"""
Export preset property groups for MHW Set Organizer.

Stores named configurations of export settings for quick switching.
"""

import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
)
from bpy.types import PropertyGroup


class MHW_PG_ExportPreset(PropertyGroup):
    """
    A named preset of export settings.

    Stores all export-related settings that can be quickly applied.
    """

    # Preset info
    name: StringProperty(
        name="Preset Name",
        description="Name of this export preset",
        default="New Preset"
    )

    description: StringProperty(
        name="Description",
        description="What this preset is for",
        default=""
    )

    # MOD3 Export Settings
    split_normals: BoolProperty(
        name="Use Custom Normals",
        description="Use split/custom normals",
        default=True
    )

    highest_lod: BoolProperty(
        name="Highest LOD",
        description="Set all mesh parts to highest level of detail",
        default=True
    )

    coerce_fourth: BoolProperty(
        name="Coerce 4th Weight",
        description="Force non-explicit 4-weight vertices",
        default=True
    )

    # CTC Export Settings
    align_frames: BoolProperty(
        name="Align Frames",
        description="Align CTC frames in hierarchy",
        default=True
    )

    align_nodes: BoolProperty(
        name="Align Nodes",
        description="Align CTC nodes to bones",
        default=False
    )

    # Import Settings
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

    # CTC Import Settings
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

    # CCL Import Settings
    ccl_scale: FloatProperty(
        name="CCL Scale",
        description="Multiply collision sphere radii",
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

    # Weight Format
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

    # Skeleton Import
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

    # Flags
    is_builtin: BoolProperty(
        name="Is Built-in",
        description="Whether this is a built-in preset (can't be deleted)",
        default=False
    )


# Built-in presets that come with the addon
BUILTIN_PRESETS = {
    "High Quality": {
        "description": "Maximum quality for final export",
        "split_normals": True,
        "highest_lod": True,
        "coerce_fourth": True,
        "align_frames": True,
        "align_nodes": False,
        "import_textures": True,
        "import_materials": True,
        "high_lod": True,
        "is_builtin": True,
    },
    "Quick Test": {
        "description": "Fast export for testing iteration",
        "split_normals": False,
        "highest_lod": False,
        "coerce_fourth": False,
        "align_frames": False,
        "align_nodes": False,
        "import_textures": False,
        "import_materials": False,
        "high_lod": False,
        "is_builtin": True,
    },
    "Distribution": {
        "description": "Optimized for release/distribution",
        "split_normals": True,
        "highest_lod": True,
        "coerce_fourth": True,
        "align_frames": True,
        "align_nodes": True,
        "import_textures": True,
        "import_materials": False,
        "high_lod": True,
        "is_builtin": True,
    },
    "Import Full": {
        "description": "Import everything for editing",
        "clear_scene": False,
        "maximize_clipping": True,
        "high_lod": False,
        "import_header": True,
        "import_meshparts": True,
        "import_textures": True,
        "import_materials": True,
        "import_skeleton": 'EMPTY',
        "is_builtin": True,
    },
}


def create_builtin_presets(presets_collection):
    """Create built-in presets if they don't exist."""
    existing_names = {p.name for p in presets_collection}

    for preset_name, settings in BUILTIN_PRESETS.items():
        if preset_name not in existing_names:
            preset = presets_collection.add()
            preset.name = preset_name

            # Set all properties
            for key, value in settings.items():
                if hasattr(preset, key):
                    setattr(preset, key, value)


# Classes to register
classes = (
    MHW_PG_ExportPreset,
)


def register():
    """Register export preset property groups."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister export preset property groups."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
