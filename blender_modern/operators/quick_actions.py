"""
Quick action operators for MHW Set Organizer.

Provides convenient shortcuts and context menu actions.
"""

import bpy
from bpy.types import Operator, Menu


class MHW_OT_QuickAddToExportSet(Operator):
    """Add selected objects to active export set"""
    bl_idname = "mhw.quick_add_to_export_set"
    bl_label = "Add to Active Export Set"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        if not context.selected_objects:
            return False

        scene = context.scene
        if not hasattr(scene, 'mhw_data'):
            return False

        mhw = scene.mhw_data
        if not mhw.export_sets or mhw.active_export_set_index >= len(mhw.export_sets):
            return False

        return True

    def execute(self, context):
        """Add selected objects to active export set."""
        mhw = context.scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        added_count = 0
        skipped_count = 0

        for obj in context.selected_objects:
            # Check if object is a mesh
            if obj.type != 'MESH':
                skipped_count += 1
                continue

            # Check if already in export set
            already_exists = False
            for eobj in export_set.eobjs:
                if eobj.obje == obj:
                    already_exists = True
                    break

            if already_exists:
                skipped_count += 1
                continue

            # Add to export set
            new_entry = export_set.eobjs.add()
            new_entry.obje = obj
            new_entry.export = True
            added_count += 1

        # Report results
        if added_count > 0:
            self.report({'INFO'}, f"Added {added_count} object(s) to '{export_set.name}'")

        if skipped_count > 0:
            self.report({'WARNING'}, f"Skipped {skipped_count} object(s) (non-mesh or already in set)")

        return {'FINISHED'}


class MHW_OT_QuickRemoveFromExportSet(Operator):
    """Remove selected objects from active export set"""
    bl_idname = "mhw.quick_remove_from_export_set"
    bl_label = "Remove from Active Export Set"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        if not context.selected_objects:
            return False

        scene = context.scene
        if not hasattr(scene, 'mhw_data'):
            return False

        mhw = scene.mhw_data
        if not mhw.export_sets or mhw.active_export_set_index >= len(mhw.export_sets):
            return False

        return True

    def execute(self, context):
        """Remove selected objects from active export set."""
        mhw = context.scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        removed_count = 0

        # Collect indices to remove (iterate in reverse to avoid index issues)
        indices_to_remove = []
        for i, eobj in enumerate(export_set.eobjs):
            if eobj.obje in context.selected_objects:
                indices_to_remove.append(i)

        # Remove in reverse order
        for i in reversed(indices_to_remove):
            export_set.eobjs.remove(i)
            removed_count += 1

        if removed_count > 0:
            self.report({'INFO'}, f"Removed {removed_count} object(s) from '{export_set.name}'")
        else:
            self.report({'WARNING'}, "No objects were in the export set")

        return {'FINISHED'}


class MHW_OT_SelectExportSetObjects(Operator):
    """Select all objects in active export set"""
    bl_idname = "mhw.select_export_set_objects"
    bl_label = "Select Export Set Objects"
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
        """Select all objects in active export set."""
        mhw = context.scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        # Deselect all
        bpy.ops.object.select_all(action='DESELECT')

        # Select objects in export set
        selected_count = 0
        for eobj in export_set.eobjs:
            if eobj.obje and eobj.export:
                eobj.obje.select_set(True)
                selected_count += 1

        if selected_count > 0:
            self.report({'INFO'}, f"Selected {selected_count} object(s) from '{export_set.name}'")
        else:
            self.report({'WARNING'}, "No exportable objects in set")

        return {'FINISHED'}


class MHW_MT_ObjectContextMenu(Menu):
    """MHW context menu for objects"""
    bl_label = "MHW Set Organizer"
    bl_idname = "MHW_MT_object_context_menu"

    def draw(self, context):
        layout = self.layout

        # Check if MHW data exists
        if not hasattr(context.scene, 'mhw_data'):
            layout.label(text="MHW data not found", icon='ERROR')
            return

        mhw = context.scene.mhw_data

        # Show active export set name
        if mhw.export_sets and mhw.active_export_set_index < len(mhw.export_sets):
            export_set = mhw.export_sets[mhw.active_export_set_index]
            layout.label(text=f"Active Set: {export_set.name}", icon='OUTLINER_OB_ARMATURE')
            layout.separator()

            layout.operator("mhw.quick_add_to_export_set", icon='ADD')
            layout.operator("mhw.quick_remove_from_export_set", icon='REMOVE')
            layout.separator()
            layout.operator("mhw.select_export_set_objects", icon='RESTRICT_SELECT_OFF')
        else:
            layout.label(text="No active export set", icon='INFO')


def mhw_object_context_menu_func(self, context):
    """Add MHW submenu to object context menu."""
    # Only show for mesh objects
    if context.object and context.object.type == 'MESH':
        layout = self.layout
        layout.separator()
        layout.menu("MHW_MT_object_context_menu", icon='EXPORT')


# Classes to register
classes = (
    MHW_OT_QuickAddToExportSet,
    MHW_OT_QuickRemoveFromExportSet,
    MHW_OT_SelectExportSetObjects,
    MHW_MT_ObjectContextMenu,
)


def register():
    """Register quick action operators and menus."""
    for cls in classes:
        bpy.utils.register_class(cls)

    # Add to object context menu
    bpy.types.VIEW3D_MT_object_context_menu.append(mhw_object_context_menu_func)


def unregister():
    """Unregister quick action operators and menus."""
    # Remove from object context menu
    bpy.types.VIEW3D_MT_object_context_menu.remove(mhw_object_context_menu_func)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
