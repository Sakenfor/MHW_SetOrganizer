"""
Visual feedback operators for MHW Set Organizer.

Provides visual highlighting of objects in the active export set.
"""

import bpy
from bpy.types import Operator
from bpy.props import BoolProperty


class MHW_OT_HighlightExportSetObjects(Operator):
    """Highlight objects in active export set with color coding"""
    bl_idname = "mhw.highlight_export_set_objects"
    bl_label = "Highlight Export Set"
    bl_description = "Color-code objects by export set membership"
    bl_options = {'REGISTER', 'UNDO'}

    clear_highlight: BoolProperty(
        name="Clear Highlight",
        description="Remove all highlighting",
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

    def execute(self, context):
        """Apply visual feedback to objects."""
        mhw = context.scene.mhw_data

        if self.clear_highlight:
            # Clear all highlighting
            cleared_count = 0
            for obj in bpy.data.objects:
                if obj.type == 'MESH' and obj.color != (1.0, 1.0, 1.0, 1.0):
                    obj.color = (1.0, 1.0, 1.0, 1.0)
                    obj.show_wire = False
                    cleared_count += 1

            self.report({'INFO'}, f"Cleared highlighting on {cleared_count} object(s)")
            return {'FINISHED'}

        # Get active export set
        export_set = mhw.export_sets[mhw.active_export_set_index]

        # Color map by armor part
        color_map = {
            'head': (1.0, 0.2, 0.2, 1.0),      # Red
            'body': (1.0, 0.6, 0.2, 1.0),      # Orange
            'arm': (1.0, 1.0, 0.2, 1.0),       # Yellow
            'waist': (0.2, 1.0, 0.2, 1.0),     # Green
            'leg': (0.2, 0.6, 1.0, 1.0),       # Blue
        }

        set_color = color_map.get(export_set.armor_part, (0.8, 0.8, 0.8, 1.0))

        # First, reset all objects to default
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                obj.color = (0.3, 0.3, 0.3, 1.0)  # Dim gray for non-set objects
                obj.show_wire = False

        # Highlight objects in active export set
        highlighted_count = 0
        for eobj in export_set.eobjs:
            if not eobj.obje:
                continue

            obj = eobj.obje

            # Set color
            obj.color = set_color

            # Enable wireframe overlay for extra visibility
            obj.show_wire = True
            obj.show_all_edges = True

            highlighted_count += 1

        # Also highlight root and CTC header
        if export_set.empty_root:
            export_set.empty_root.color = set_color
            export_set.empty_root.show_axis = True
            highlighted_count += 1

        if export_set.ctc_header:
            export_set.ctc_header.color = set_color
            export_set.ctc_header.show_axis = True
            highlighted_count += 1

        self.report({'INFO'}, f"Highlighted {highlighted_count} object(s) in '{export_set.name}'")
        return {'FINISHED'}


class MHW_OT_ToggleWireframe(Operator):
    """Toggle wireframe display for export set objects"""
    bl_idname = "mhw.toggle_wireframe"
    bl_label = "Toggle Wireframe"
    bl_description = "Toggle wireframe display for objects in active export set"
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

        return True

    def execute(self, context):
        """Toggle wireframe for export set objects."""
        mhw = context.scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        # Check current state (use first object as reference)
        current_state = False
        for eobj in export_set.eobjs:
            if eobj.obje:
                current_state = eobj.obje.show_wire
                break

        # Toggle to opposite state
        new_state = not current_state
        toggled_count = 0

        for eobj in export_set.eobjs:
            if not eobj.obje:
                continue

            eobj.obje.show_wire = new_state
            eobj.obje.show_all_edges = new_state
            toggled_count += 1

        state_text = "enabled" if new_state else "disabled"
        self.report({'INFO'}, f"Wireframe {state_text} for {toggled_count} object(s)")
        return {'FINISHED'}


class MHW_OT_IsolateExportSet(Operator):
    """Hide all objects except those in active export set"""
    bl_idname = "mhw.isolate_export_set"
    bl_label = "Isolate Export Set"
    bl_description = "Hide all objects except those in the active export set"
    bl_options = {'REGISTER', 'UNDO'}

    restore: BoolProperty(
        name="Restore",
        description="Restore visibility of all objects",
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

    def execute(self, context):
        """Isolate or restore visibility."""
        mhw = context.scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        if self.restore:
            # Restore visibility of all objects
            for obj in bpy.data.objects:
                obj.hide_set(False)
                obj.hide_viewport = False

            self.report({'INFO'}, "Restored visibility of all objects")
            return {'FINISHED'}

        # Get set of objects in export set
        set_objects = set()
        for eobj in export_set.eobjs:
            if eobj.obje:
                set_objects.add(eobj.obje)

        if export_set.empty_root:
            set_objects.add(export_set.empty_root)

        if export_set.ctc_header:
            set_objects.add(export_set.ctc_header)

        # Hide everything except set objects
        hidden_count = 0
        for obj in bpy.data.objects:
            if obj not in set_objects:
                obj.hide_set(True)
                hidden_count += 1

        self.report({'INFO'}, f"Isolated {len(set_objects)} object(s), hid {hidden_count}")
        return {'FINISHED'}


class MHW_OT_ShowInViewport(Operator):
    """Toggle viewport visibility for export set objects"""
    bl_idname = "mhw.show_in_viewport"
    bl_label = "Toggle Viewport Visibility"
    bl_description = "Show/hide objects in viewport"
    bl_options = {'REGISTER', 'UNDO'}

    mode: BoolProperty(
        name="Show",
        description="True to show, False to hide",
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

    def execute(self, context):
        """Toggle viewport visibility."""
        mhw = context.scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        toggled_count = 0
        for eobj in export_set.eobjs:
            if not eobj.obje:
                continue

            eobj.obje.hide_viewport = not self.mode
            toggled_count += 1

        state_text = "shown" if self.mode else "hidden"
        self.report({'INFO'}, f"{toggled_count} object(s) {state_text}")
        return {'FINISHED'}


# Classes to register
classes = (
    MHW_OT_HighlightExportSetObjects,
    MHW_OT_ToggleWireframe,
    MHW_OT_IsolateExportSet,
    MHW_OT_ShowInViewport,
)


def register():
    """Register visual feedback operators."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister visual feedback operators."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
