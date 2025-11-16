"""
Import operators for MHW Set Organizer.

Thin wrappers around core.import_logic module that handle user interaction.
"""

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty

from ..core import import_logic


class MHW_OT_Import(Operator):
    """Import MOD3, CTC, or CCL file with options"""
    bl_idname = "mhw.import"
    bl_label = "Import MHW File"
    bl_options = {'REGISTER', 'UNDO'}

    import_type: StringProperty(
        name="Import Type",
        description="Type of file to import",
        default="MOD3"
    )

    add_to_export_set: BoolProperty(
        name="Add to Export Set",
        description="Automatically add imported objects to current export set",
        default=True
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
        """Show options dialog unless Shift is held."""
        scene = context.scene
        mhw = scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        # Store for draw() method
        self._export_set = export_set

        # If Shift held, skip dialog
        if event.shift:
            return self.execute(context)

        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        """Perform the import."""
        scene = context.scene
        mhw = scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        # Perform import
        try:
            success, message = import_logic.perform_import(
                export_set,
                context,
                self.import_type
            )

            if not success:
                self.report({'ERROR'}, message)
                return {'CANCELLED'}

            # Post-process imported objects
            if self.add_to_export_set:
                post_success, post_message = import_logic.post_import_processing(
                    export_set,
                    context,
                    self.import_type,
                    add_to_export_set=True
                )

                if post_success:
                    message += f"\n{post_message}"

            self.report({'INFO'}, message)
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Import failed: {e}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}

    def draw(self, context):
        """Draw operator options dialog."""
        layout = self.layout
        export_set = getattr(self, '_export_set', None)

        # Show warning if clear_scene is enabled
        if export_set and getattr(export_set, 'clear_scene', False):
            box = layout.box()
            box.label(text='NOTE: "clear scene" will erase all SETS data', icon='ERROR')

        # Show type-specific options
        if self.import_type == 'MOD3':
            col = layout.column(align=True)
            col.label(text="MOD3 Import Options:")
            if export_set:
                col.prop(export_set, 'clear_scene')
                col.prop(export_set, 'maximize_clipping')
                col.prop(export_set, 'high_lod')
                col.prop(export_set, 'import_header')
                col.prop(export_set, 'import_meshparts')
                col.prop(export_set, 'import_textures')
                col.prop(export_set, 'import_materials')
                col.prop(export_set, 'load_group_functions')
                col.prop(export_set, 'texture_path')
                col.prop(export_set, 'import_skeleton')
                col.prop(export_set, 'weight_format')

        elif self.import_type == 'CTC':
            col = layout.column(align=True)
            col.label(text="CTC Import Options:")
            if export_set:
                col.prop(export_set, 'ctc_missing_function_behaviour')

        elif self.import_type == 'CCL':
            col = layout.column(align=True)
            col.label(text="CCL Import Options:")
            if export_set:
                col.prop(export_set, 'ccl_scale')
                col.prop(export_set, 'ccl_missing_function_behaviour')

        # Common option
        layout.separator()
        layout.prop(self, 'add_to_export_set')


class MHW_OT_BatchImport(Operator):
    """Import files for multiple export sets"""
    bl_idname = "mhw.batch_import"
    bl_label = "Batch Import"
    bl_options = {'REGISTER', 'UNDO'}

    import_type: StringProperty(
        name="Import Type",
        description="Type of files to import",
        default="MOD3"
    )

    add_to_export_sets: BoolProperty(
        name="Add to Export Sets",
        description="Add imported objects to their respective export sets",
        default=True
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        scene = context.scene
        if not hasattr(scene, 'mhw_data'):
            return False

        mhw = scene.mhw_data
        if not mhw.batch_sets or mhw.active_batch_index >= len(mhw.batch_sets):
            return False

        batch_set = mhw.batch_sets[mhw.active_batch_index]
        return len(batch_set.sets) > 0

    def execute(self, context):
        """Perform batch import."""
        scene = context.scene
        mhw = scene.mhw_data
        batch_set = mhw.batch_sets[mhw.active_batch_index]

        # Get all export sets in the batch
        export_sets = []
        for set_ref in batch_set.sets:
            if set_ref.export_set:
                export_sets.append(set_ref.export_set)

        if not export_sets:
            self.report({'ERROR'}, "No valid export sets in batch")
            return {'CANCELLED'}

        # Perform batch import
        try:
            success, message = import_logic.batch_import(
                export_sets,
                context,
                self.import_type,
                add_to_export_sets=self.add_to_export_sets
            )

            if success:
                self.report({'INFO'}, message)
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, message)
                return {'FINISHED'}  # Still finish even if some imports failed

        except Exception as e:
            self.report({'ERROR'}, f"Batch import failed: {e}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}


# List of operator classes for registration
classes = [
    MHW_OT_Import,
    MHW_OT_BatchImport,
]


def register():
    """Register operator classes."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister operator classes."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
