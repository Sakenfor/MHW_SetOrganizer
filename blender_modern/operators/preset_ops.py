"""
Export preset operators for MHW Set Organizer.

Allows saving, loading, and managing export setting presets.
"""

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty
from ..properties import export_presets


class MHW_OT_PresetApply(Operator):
    """Apply preset settings to active export set"""
    bl_idname = "mhw.preset_apply"
    bl_label = "Apply Preset"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        scene = context.scene
        if not hasattr(scene, 'mhw_data'):
            return False

        mhw = scene.mhw_data
        if not mhw.export_sets or mhw.active_export_set_index >= len(mhw.export_sets):
            return False

        if not mhw.export_presets or mhw.active_preset_index >= len(mhw.export_presets):
            return False

        return True

    def execute(self, context):
        """Apply selected preset to active export set."""
        mhw = context.scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]
        preset = mhw.export_presets[mhw.active_preset_index]

        # Apply all preset settings to export set
        export_set.split_normals = preset.split_normals
        export_set.highest_lod = preset.highest_lod
        export_set.coerce_fourth = preset.coerce_fourth
        export_set.align_frames = preset.align_frames
        export_set.align_nodes = preset.align_nodes

        # Import settings
        export_set.clear_scene = preset.clear_scene
        export_set.maximize_clipping = preset.maximize_clipping
        export_set.high_lod = preset.high_lod
        export_set.import_header = preset.import_header
        export_set.import_meshparts = preset.import_meshparts
        export_set.import_textures = preset.import_textures
        export_set.import_materials = preset.import_materials
        export_set.ctc_missing_function_behaviour = preset.ctc_missing_function_behaviour
        export_set.ccl_scale = preset.ccl_scale
        export_set.ccl_missing_function_behaviour = preset.ccl_missing_function_behaviour
        export_set.weight_format = preset.weight_format
        export_set.import_skeleton = preset.import_skeleton

        self.report({'INFO'}, f"Applied preset '{preset.name}' to '{export_set.name}'")
        return {'FINISHED'}


class MHW_OT_PresetSave(Operator):
    """Save current export settings as a new preset"""
    bl_idname = "mhw.preset_save"
    bl_label = "Save Preset"
    bl_options = {'REGISTER'}

    preset_name: StringProperty(
        name="Preset Name",
        description="Name for this preset",
        default="New Preset"
    )

    description: StringProperty(
        name="Description",
        description="What this preset is for",
        default=""
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        scene = context.scene
        if not hasattr(scene, 'mhw_data'):
            return False

        mhw = scene.mhw_data
        if not mhw.export_sets or mhw.active_export_set_index >= len(mhw.export_sets):
            return False

        return True

    def invoke(self, context, event):
        """Show dialog to enter preset name."""
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        """Draw operator dialog."""
        layout = self.layout
        layout.prop(self, "preset_name")
        layout.prop(self, "description")

    def execute(self, context):
        """Save current settings as preset."""
        mhw = context.scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        # Check if preset name already exists
        for preset in mhw.export_presets:
            if preset.name == self.preset_name:
                if preset.is_builtin:
                    self.report({'ERROR'}, f"Cannot overwrite built-in preset '{self.preset_name}'")
                    return {'CANCELLED'}

                # Overwrite existing
                self.report({'WARNING'}, f"Overwriting existing preset '{self.preset_name}'")
                # Remove old one
                for i, p in enumerate(mhw.export_presets):
                    if p.name == self.preset_name:
                        mhw.export_presets.remove(i)
                        break

        # Create new preset
        preset = mhw.export_presets.add()
        preset.name = self.preset_name
        preset.description = self.description

        # Copy settings from export set
        preset.split_normals = export_set.split_normals
        preset.highest_lod = export_set.highest_lod
        preset.coerce_fourth = export_set.coerce_fourth
        preset.align_frames = export_set.align_frames
        preset.align_nodes = export_set.align_nodes
        preset.clear_scene = export_set.clear_scene
        preset.maximize_clipping = export_set.maximize_clipping
        preset.high_lod = export_set.high_lod
        preset.import_header = export_set.import_header
        preset.import_meshparts = export_set.import_meshparts
        preset.import_textures = export_set.import_textures
        preset.import_materials = export_set.import_materials
        preset.ctc_missing_function_behaviour = export_set.ctc_missing_function_behaviour
        preset.ccl_scale = export_set.ccl_scale
        preset.ccl_missing_function_behaviour = export_set.ccl_missing_function_behaviour
        preset.weight_format = export_set.weight_format
        preset.import_skeleton = export_set.import_skeleton
        preset.is_builtin = False

        # Set as active
        mhw.active_preset_index = len(mhw.export_presets) - 1

        self.report({'INFO'}, f"Saved preset '{preset.name}'")
        return {'FINISHED'}


class MHW_OT_PresetDelete(Operator):
    """Delete the selected preset"""
    bl_idname = "mhw.preset_delete"
    bl_label = "Delete Preset"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        scene = context.scene
        if not hasattr(scene, 'mhw_data'):
            return False

        mhw = scene.mhw_data
        if not mhw.export_presets or mhw.active_preset_index >= len(mhw.export_presets):
            return False

        # Can't delete built-in presets
        preset = mhw.export_presets[mhw.active_preset_index]
        return not preset.is_builtin

    def invoke(self, context, event):
        """Confirm deletion."""
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        """Delete the preset."""
        mhw = context.scene.mhw_data
        preset = mhw.export_presets[mhw.active_preset_index]
        preset_name = preset.name

        mhw.export_presets.remove(mhw.active_preset_index)

        # Adjust active index
        if mhw.active_preset_index >= len(mhw.export_presets):
            mhw.active_preset_index = max(0, len(mhw.export_presets) - 1)

        self.report({'INFO'}, f"Deleted preset '{preset_name}'")
        return {'FINISHED'}


class MHW_OT_PresetInitialize(Operator):
    """Initialize built-in presets"""
    bl_idname = "mhw.preset_initialize"
    bl_label = "Initialize Presets"
    bl_options = {'REGISTER'}

    def execute(self, context):
        """Create built-in presets if they don't exist."""
        mhw = context.scene.mhw_data

        export_presets.create_builtin_presets(mhw.export_presets)

        preset_count = len(mhw.export_presets)
        self.report({'INFO'}, f"Initialized {preset_count} preset(s)")
        return {'FINISHED'}


class MHW_OT_PresetNavigate(Operator):
    """Navigate between presets"""
    bl_idname = "mhw.preset_navigate"
    bl_label = "Navigate Presets"
    bl_options = {'REGISTER'}

    direction: StringProperty(
        name="Direction",
        description="Navigation direction",
        default="NEXT"
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        scene = context.scene
        if not hasattr(scene, 'mhw_data'):
            return False

        mhw = scene.mhw_data
        return len(mhw.export_presets) > 0

    def execute(self, context):
        """Navigate to next/previous preset."""
        mhw = context.scene.mhw_data

        if self.direction == 'NEXT':
            mhw.active_preset_index = (mhw.active_preset_index + 1) % len(mhw.export_presets)
        elif self.direction == 'PREV':
            mhw.active_preset_index = (mhw.active_preset_index - 1) % len(mhw.export_presets)

        return {'FINISHED'}


# Classes to register
classes = (
    MHW_OT_PresetApply,
    MHW_OT_PresetSave,
    MHW_OT_PresetDelete,
    MHW_OT_PresetInitialize,
    MHW_OT_PresetNavigate,
)


def register():
    """Register preset operators."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister preset operators."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
