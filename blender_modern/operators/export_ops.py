"""
Export operators for MHW Set Organizer.

Thin wrappers around core.export_logic module that handle user interaction.
"""

from typing import Set
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty

from ..core import export_logic
from ..properties import export_history
from ..utils import validation


class MHW_OT_Export(Operator):
    """Export MOD3, CTC, or CCL file"""
    bl_idname = "mhw.export"
    bl_label = "Export"
    bl_options = {'REGISTER', 'UNDO'}

    export_type: StringProperty(
        name="Export Type",
        description="Type of export to perform",
        default="MOD3"
    )

    # Optional overrides for CTC export
    align_frames: BoolProperty(
        name="Align Frames",
        description="Align all CTC frames",
        default=True
    )

    align_nodes: BoolProperty(
        name="Realign Nodes",
        description="Realign all CTC nodes",
        default=False
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

        # Store export set for draw() method
        self._export_set = export_set

        # If Shift held, skip dialog
        if event.shift:
            return self.execute(context)

        # If Ctrl held, force all boolean options to False
        if event.ctrl:
            self.align_frames = False
            self.align_nodes = False

        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        """Perform the export."""
        scene = context.scene
        mhw = scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        # Validate export set
        is_valid, errors = validation.validate_export_set(export_set)
        if not is_valid:
            self.report({'ERROR'}, f"Export validation failed: {', '.join(errors)}")
            return {'CANCELLED'}

        # Perform export based on type
        success = False
        message = ""

        try:
            if self.export_type == 'MOD3':
                success, message = export_logic.perform_export(
                    export_set,
                    context,
                    export_type='MOD3'
                )
            elif self.export_type == 'CTC':
                success, message = export_logic.perform_export(
                    export_set,
                    context,
                    export_type='CTC',
                    align_frames=self.align_frames,
                    align_nodes=self.align_nodes
                )
            elif self.export_type == 'CCL':
                success, message = export_logic.perform_export(
                    export_set,
                    context,
                    export_type='CCL'
                )
            else:
                self.report({'ERROR'}, f"Unknown export type: {self.export_type}")
                return {'CANCELLED'}

        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {e}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}

        # Report result and log to history
        if success:
            # Log successful export to history
            export_history.add_export_history_entry(
                context,
                export_set_name=export_set.name,
                export_type=self.export_type,
                file_path=export_set.export_path,
                success=True,
                split_normals=export_set.split_normals,
                highest_lod=export_set.highest_lod,
                coerce_fourth=export_set.coerce_fourth if self.export_type == 'MOD3' else False,
                align_frames=self.align_frames if self.export_type == 'CTC' else False,
                align_nodes=self.align_nodes if self.export_type == 'CTC' else False
            )

            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            # Log failed export to history
            export_history.add_export_history_entry(
                context,
                export_set_name=export_set.name,
                export_type=self.export_type,
                file_path=export_set.export_path,
                success=False,
                error_message=message
            )

            self.report({'ERROR'}, message)
            return {'CANCELLED'}

    def draw(self, context):
        """Draw operator options dialog."""
        layout = self.layout

        # Show warning if export set has clear_scene enabled (for imports)
        export_set = getattr(self, '_export_set', None)
        if export_set and getattr(export_set, 'clear_scene', False):
            box = layout.box()
            box.label(text='NOTE: "clear scene" will erase all SETS data', icon='ERROR')

        # Show type-specific options
        if self.export_type == 'CTC':
            layout.prop(self, 'align_frames', icon='META_ELLIPSOID')
            layout.prop(self, 'align_nodes', icon='META_BALL')


class MHW_OT_BatchExport(Operator):
    """Export multiple sets in sequence"""
    bl_idname = "mhw.batch_export"
    bl_label = "Batch Export"
    bl_options = {'REGISTER', 'UNDO'}

    export_type: StringProperty(
        name="Export Type",
        description="Type of export to perform",
        default="MOD3"
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
        """Perform batch export."""
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

        # Perform batch export
        try:
            success, message = export_logic.batch_export(
                export_sets,
                context,
                self.export_type
            )

            if success:
                self.report({'INFO'}, message)
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, message)
                return {'FINISHED'}  # Still finish even if some exports failed

        except Exception as e:
            self.report({'ERROR'}, f"Batch export failed: {e}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}


# List of operator classes for registration
classes = [
    MHW_OT_Export,
    MHW_OT_BatchExport,
]


def register():
    """Register operator classes."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister operator classes."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
