"""
List management operators for UI lists.

Provides operators for adding, removing, and moving items in various lists.
"""

import bpy
from bpy.types import Operator
from bpy.props import EnumProperty, StringProperty


class MHW_OT_ExportSetAdd(Operator):
    """Add a new export set"""
    bl_idname = "mhw.export_set_add"
    bl_label = "Add Export Set"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mhw = context.scene.mhw_data
        new_set = mhw.export_sets.add()
        new_set.name = f"ExportSet_{len(mhw.export_sets)}"
        mhw.active_export_set_index = len(mhw.export_sets) - 1
        return {'FINISHED'}


class MHW_OT_ExportSetRemove(Operator):
    """Remove the active export set"""
    bl_idname = "mhw.export_set_remove"
    bl_label = "Remove Export Set"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        mhw = context.scene.mhw_data
        return mhw.export_sets

    def execute(self, context):
        mhw = context.scene.mhw_data
        mhw.export_sets.remove(mhw.active_export_set_index)
        if mhw.active_export_set_index >= len(mhw.export_sets):
            mhw.active_export_set_index = max(0, len(mhw.export_sets) - 1)
        return {'FINISHED'}


class MHW_OT_ExportSetMove(Operator):
    """Move export set up or down in the list"""
    bl_idname = "mhw.export_set_move"
    bl_label = "Move Export Set"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        items=[('UP', "Up", ""), ('DOWN', "Down", "")]
    )

    @classmethod
    def poll(cls, context):
        mhw = context.scene.mhw_data
        return len(mhw.export_sets) > 1

    def execute(self, context):
        mhw = context.scene.mhw_data
        idx = mhw.active_export_set_index

        if self.direction == 'UP' and idx > 0:
            mhw.export_sets.move(idx, idx - 1)
            mhw.active_export_set_index -= 1
        elif self.direction == 'DOWN' and idx < len(mhw.export_sets) - 1:
            mhw.export_sets.move(idx, idx + 1)
            mhw.active_export_set_index += 1

        return {'FINISHED'}


class MHW_OT_ExportSetObjectAdd(Operator):
    """Add a new object to the active export set"""
    bl_idname = "mhw.export_set_object_add"
    bl_label = "Add Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        mhw = context.scene.mhw_data
        return mhw.export_sets and mhw.active_export_set_index < len(mhw.export_sets)

    def execute(self, context):
        mhw = context.scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]
        new_obj = export_set.eobjs.add()
        new_obj.name = f"Object_{len(export_set.eobjs)}"
        export_set.active_object_index = len(export_set.eobjs) - 1
        return {'FINISHED'}


class MHW_OT_ExportSetObjectRemove(Operator):
    """Remove the active object from the export set"""
    bl_idname = "mhw.export_set_object_remove"
    bl_label = "Remove Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        mhw = context.scene.mhw_data
        if not mhw.export_sets or mhw.active_export_set_index >= len(mhw.export_sets):
            return False
        export_set = mhw.export_sets[mhw.active_export_set_index]
        return export_set.eobjs

    def execute(self, context):
        mhw = context.scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]
        export_set.eobjs.remove(export_set.active_object_index)
        if export_set.active_object_index >= len(export_set.eobjs):
            export_set.active_object_index = max(0, len(export_set.eobjs) - 1)
        return {'FINISHED'}


class MHW_OT_BatchSetAdd(Operator):
    """Add a new batch set"""
    bl_idname = "mhw.batch_set_add"
    bl_label = "Add Batch Set"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mhw = context.scene.mhw_data
        new_batch = mhw.batch_sets.add()
        new_batch.name = f"BatchSet_{len(mhw.batch_sets)}"
        mhw.active_batch_index = len(mhw.batch_sets) - 1
        return {'FINISHED'}


class MHW_OT_BatchSetRemove(Operator):
    """Remove the active batch set"""
    bl_idname = "mhw.batch_set_remove"
    bl_label = "Remove Batch Set"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        mhw = context.scene.mhw_data
        return mhw.batch_sets

    def execute(self, context):
        mhw = context.scene.mhw_data
        mhw.batch_sets.remove(mhw.active_batch_index)
        if mhw.active_batch_index >= len(mhw.batch_sets):
            mhw.active_batch_index = max(0, len(mhw.batch_sets) - 1)
        return {'FINISHED'}


class MHW_OT_BatchSetMove(Operator):
    """Move batch set up or down in the list"""
    bl_idname = "mhw.batch_set_move"
    bl_label = "Move Batch Set"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        items=[('UP', "Up", ""), ('DOWN', "Down", "")]
    )

    @classmethod
    def poll(cls, context):
        mhw = context.scene.mhw_data
        return len(mhw.batch_sets) > 1

    def execute(self, context):
        mhw = context.scene.mhw_data
        idx = mhw.active_batch_index

        if self.direction == 'UP' and idx > 0:
            mhw.batch_sets.move(idx, idx - 1)
            mhw.active_batch_index -= 1
        elif self.direction == 'DOWN' and idx < len(mhw.batch_sets) - 1:
            mhw.batch_sets.move(idx, idx + 1)
            mhw.active_batch_index += 1

        return {'FINISHED'}


class MHW_OT_BatchSetObjectAdd(Operator):
    """Add a new set to the active batch"""
    bl_idname = "mhw.batch_set_object_add"
    bl_label = "Add Set to Batch"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        mhw = context.scene.mhw_data
        return mhw.batch_sets and mhw.active_batch_index < len(mhw.batch_sets)

    def execute(self, context):
        mhw = context.scene.mhw_data
        batch_set = mhw.batch_sets[mhw.active_batch_index]
        new_obj = batch_set.sets.add()
        batch_set.active_set_index = len(batch_set.sets) - 1
        return {'FINISHED'}


class MHW_OT_BatchSetObjectRemove(Operator):
    """Remove the active set from the batch"""
    bl_idname = "mhw.batch_set_object_remove"
    bl_label = "Remove Set from Batch"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        mhw = context.scene.mhw_data
        if not mhw.batch_sets or mhw.active_batch_index >= len(mhw.batch_sets):
            return False
        batch_set = mhw.batch_sets[mhw.active_batch_index]
        return batch_set.sets

    def execute(self, context):
        mhw = context.scene.mhw_data
        batch_set = mhw.batch_sets[mhw.active_batch_index]
        batch_set.sets.remove(batch_set.active_set_index)
        if batch_set.active_set_index >= len(batch_set.sets):
            batch_set.active_set_index = max(0, len(batch_set.sets) - 1)
        return {'FINISHED'}


class MHW_OT_SaveSettings(Operator):
    """Save addon settings to file"""
    bl_idname = "mhw.save_settings"
    bl_label = "Save Settings"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..utils import file_utils

        try:
            success = file_utils.save_settings(context.scene.mhw_data)
            if success:
                self.report({'INFO'}, "Settings saved successfully")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, "Failed to save settings")
                return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error saving settings: {e}")
            return {'CANCELLED'}


class MHW_OT_LoadSettings(Operator):
    """Load addon settings from file"""
    bl_idname = "mhw.load_settings"
    bl_label = "Load Settings"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..utils import file_utils

        try:
            success = file_utils.load_settings(context.scene.mhw_data)
            if success:
                self.report({'INFO'}, "Settings loaded successfully")
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, "No settings file found")
                return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error loading settings: {e}")
            return {'CANCELLED'}


class MHW_OT_RefreshExternalCTC(Operator):
    """Refresh external CTC sources from blend files"""
    bl_idname = "mhw.refresh_external_ctc"
    bl_label = "Refresh External CTC"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from pathlib import Path
        from .. import addon_config

        mhw = context.scene.mhw_data

        # Clear existing external sources
        mhw.external_ctc_sources.clear()

        source_count = 0

        # Scan all blend append paths
        for path_entry in mhw.blend_append_paths:
            if not path_entry.path:
                continue

            blend_path = Path(path_entry.path)

            # Handle both single files and directories
            blend_files = []
            if blend_path.is_file() and blend_path.suffix == '.blend':
                blend_files = [blend_path]
            elif blend_path.is_dir():
                blend_files = list(blend_path.glob('*.blend'))
            else:
                continue

            # Scan each blend file for CTC headers
            for blend_file in blend_files:
                try:
                    # Use bpy.data.libraries to link objects temporarily
                    with bpy.data.libraries.load(str(blend_file), link=True) as (data_from, data_to):
                        # Check available objects
                        if hasattr(data_from, 'objects'):
                            for obj_name in data_from.objects:
                                # We can't check custom properties when linking,
                                # so we'll add all objects and let user filter
                                # In practice, CTC headers usually have identifiable names
                                if 'CTC' in obj_name.upper() or 'HEADER' in obj_name.upper():
                                    source = mhw.external_ctc_sources.add()
                                    source.name = f"{blend_file.stem}::{obj_name}"
                                    source.blend = str(blend_file)
                                    source.folder = obj_name
                                    source_count += 1
                except Exception as e:
                    self.report({'WARNING'}, f"Could not read {blend_file.name}: {e}")
                    continue

        if source_count > 0:
            self.report({'INFO'}, f"Found {source_count} external CTC source(s)")
        else:
            self.report({'WARNING'}, "No external CTC sources found")

        return {'FINISHED'}


# List of operator classes for registration
classes = [
    MHW_OT_ExportSetAdd,
    MHW_OT_ExportSetRemove,
    MHW_OT_ExportSetMove,
    MHW_OT_ExportSetObjectAdd,
    MHW_OT_ExportSetObjectRemove,
    MHW_OT_BatchSetAdd,
    MHW_OT_BatchSetRemove,
    MHW_OT_BatchSetMove,
    MHW_OT_BatchSetObjectAdd,
    MHW_OT_BatchSetObjectRemove,
    MHW_OT_SaveSettings,
    MHW_OT_LoadSettings,
    MHW_OT_RefreshExternalCTC,
]


def register():
    """Register list operator classes."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister list operator classes."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
