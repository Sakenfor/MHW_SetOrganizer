"""
Batch operations for MHW Set Organizer.

Provides batch utilities for renaming, materials, modifiers, and UVs.
"""

import bpy
from bpy.types import Operator
import re


class MHW_OT_BatchRename(Operator):
    """Batch rename objects with find/replace (supports regex)"""
    bl_idname = "mhw.batch_rename"
    bl_label = "Batch Rename"
    bl_options = {'REGISTER', 'UNDO'}

    find: bpy.props.StringProperty(
        name="Find",
        description="Text to find (supports regex if enabled)",
        default="",
    )

    replace: bpy.props.StringProperty(
        name="Replace",
        description="Text to replace with",
        default="",
    )

    use_regex: bpy.props.BoolProperty(
        name="Use Regex",
        description="Use regular expressions for pattern matching",
        default=False,
    )

    target: bpy.props.EnumProperty(
        name="Target",
        description="Which objects to rename",
        items=[
            ('SELECTED', "Selected Objects", "Rename selected objects"),
            ('EXPORT_SET', "Active Export Set", "Rename objects in active export set"),
        ],
        default='SELECTED',
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return context.selected_objects or (
            hasattr(context.scene, 'mhw_data') and
            context.scene.mhw_data.export_sets
        )

    def execute(self, context):
        """Perform batch rename."""
        # Import backup function
        from . import backup_ops
        if backup_ops.should_create_backup(context, 'batch_ops'):
            backup_ops.create_backup(context, 'batch_rename')

        # Get target objects
        objects = []
        if self.target == 'SELECTED':
            objects = context.selected_objects
        else:  # EXPORT_SET
            mhw = context.scene.mhw_data
            if mhw.export_sets and mhw.active_export_set_index < len(mhw.export_sets):
                export_set = mhw.export_sets[mhw.active_export_set_index]
                objects = [eobj.obje for eobj in export_set.eobjs if eobj.obje]

        if not objects:
            self.report({'WARNING'}, "No objects to rename")
            return {'CANCELLED'}

        # Perform rename
        renamed_count = 0
        for obj in objects:
            old_name = obj.name

            if self.use_regex:
                try:
                    new_name = re.sub(self.find, self.replace, old_name)
                except re.error as e:
                    self.report({'ERROR'}, f"Regex error: {e}")
                    return {'CANCELLED'}
            else:
                new_name = old_name.replace(self.find, self.replace)

            if new_name != old_name:
                obj.name = new_name
                renamed_count += 1

        self.report({'INFO'}, f"Renamed {renamed_count} object(s)")
        return {'FINISHED'}

    def invoke(self, context, event):
        """Show dialog."""
        return context.window_manager.invoke_props_dialog(self)


class MHW_OT_BatchMaterial(Operator):
    """Apply material to multiple objects"""
    bl_idname = "mhw.batch_material"
    bl_label = "Batch Apply Material"
    bl_options = {'REGISTER', 'UNDO'}

    material_name: bpy.props.StringProperty(
        name="Material",
        description="Material to apply",
        default="",
    )

    target: bpy.props.EnumProperty(
        name="Target",
        description="Which objects to apply material to",
        items=[
            ('SELECTED', "Selected Objects", "Apply to selected objects"),
            ('EXPORT_SET', "Active Export Set", "Apply to objects in active export set"),
        ],
        default='SELECTED',
    )

    mode: bpy.props.EnumProperty(
        name="Mode",
        description="How to apply the material",
        items=[
            ('REPLACE_ALL', "Replace All", "Replace all materials with this one"),
            ('APPEND', "Append", "Add material to existing materials"),
            ('REPLACE_SLOT_0', "Replace Slot 0", "Replace only the first material slot"),
        ],
        default='REPLACE_ALL',
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return len(bpy.data.materials) > 0 and (
            context.selected_objects or (
                hasattr(context.scene, 'mhw_data') and
                context.scene.mhw_data.export_sets
            )
        )

    def execute(self, context):
        """Apply material to objects."""
        # Import backup function
        from . import backup_ops
        if backup_ops.should_create_backup(context, 'batch_ops'):
            backup_ops.create_backup(context, 'batch_material')

        # Get material
        material = bpy.data.materials.get(self.material_name)
        if not material:
            self.report({'ERROR'}, f"Material '{self.material_name}' not found")
            return {'CANCELLED'}

        # Get target objects
        objects = []
        if self.target == 'SELECTED':
            objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        else:  # EXPORT_SET
            mhw = context.scene.mhw_data
            if mhw.export_sets and mhw.active_export_set_index < len(mhw.export_sets):
                export_set = mhw.export_sets[mhw.active_export_set_index]
                objects = [eobj.obje for eobj in export_set.eobjs if eobj.obje and eobj.obje.type == 'MESH']

        if not objects:
            self.report({'WARNING'}, "No mesh objects to apply material to")
            return {'CANCELLED'}

        # Apply material
        applied_count = 0
        for obj in objects:
            if self.mode == 'REPLACE_ALL':
                obj.data.materials.clear()
                obj.data.materials.append(material)
                applied_count += 1
            elif self.mode == 'APPEND':
                obj.data.materials.append(material)
                applied_count += 1
            elif self.mode == 'REPLACE_SLOT_0':
                if len(obj.data.materials) > 0:
                    obj.data.materials[0] = material
                else:
                    obj.data.materials.append(material)
                applied_count += 1

        self.report({'INFO'}, f"Applied material to {applied_count} object(s)")
        return {'FINISHED'}

    def invoke(self, context, event):
        """Show dialog."""
        return context.window_manager.invoke_props_dialog(self)


class MHW_OT_BatchModifiers(Operator):
    """Batch modifier operations (apply/remove)"""
    bl_idname = "mhw.batch_modifiers"
    bl_label = "Batch Modifiers"
    bl_options = {'REGISTER', 'UNDO'}

    operation: bpy.props.EnumProperty(
        name="Operation",
        description="Modifier operation to perform",
        items=[
            ('APPLY_ALL', "Apply All", "Apply all modifiers"),
            ('REMOVE_ALL', "Remove All", "Remove all modifiers"),
            ('APPLY_BY_TYPE', "Apply by Type", "Apply specific modifier types"),
            ('REMOVE_BY_TYPE', "Remove by Type", "Remove specific modifier types"),
        ],
        default='APPLY_ALL',
    )

    target: bpy.props.EnumProperty(
        name="Target",
        description="Which objects to process",
        items=[
            ('SELECTED', "Selected Objects", "Process selected objects"),
            ('EXPORT_SET', "Active Export Set", "Process objects in active export set"),
        ],
        default='SELECTED',
    )

    subdivision: bpy.props.BoolProperty(
        name="Subdivision",
        description="Include Subdivision Surface modifiers",
        default=True,
    )

    mirror: bpy.props.BoolProperty(
        name="Mirror",
        description="Include Mirror modifiers",
        default=True,
    )

    armature: bpy.props.BoolProperty(
        name="Armature",
        description="Include Armature modifiers",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return context.selected_objects or (
            hasattr(context.scene, 'mhw_data') and
            context.scene.mhw_data.export_sets
        )

    def execute(self, context):
        """Perform batch modifier operations."""
        # Import backup function
        from . import backup_ops
        if backup_ops.should_create_backup(context, 'batch_ops'):
            backup_ops.create_backup(context, 'batch_modifiers')

        # Get target objects
        objects = []
        if self.target == 'SELECTED':
            objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        else:  # EXPORT_SET
            mhw = context.scene.mhw_data
            if mhw.export_sets and mhw.active_export_set_index < len(mhw.export_sets):
                export_set = mhw.export_sets[mhw.active_export_set_index]
                objects = [eobj.obje for eobj in export_set.eobjs if eobj.obje and eobj.obje.type == 'MESH']

        if not objects:
            self.report({'WARNING'}, "No mesh objects to process")
            return {'CANCELLED'}

        # Build modifier type filter
        modifier_types = []
        if self.subdivision:
            modifier_types.append('SUBSURF')
        if self.mirror:
            modifier_types.append('MIRROR')
        if self.armature:
            modifier_types.append('ARMATURE')

        # Process objects
        processed_count = 0
        modifier_count = 0

        for obj in objects:
            # Make object active for modifier operations
            context.view_layer.objects.active = obj

            modifiers_to_process = []

            if self.operation in ['APPLY_ALL', 'REMOVE_ALL']:
                modifiers_to_process = list(obj.modifiers)
            else:  # BY_TYPE
                modifiers_to_process = [m for m in obj.modifiers if m.type in modifier_types]

            if not modifiers_to_process:
                continue

            # Process modifiers
            for modifier in modifiers_to_process:
                try:
                    if self.operation in ['APPLY_ALL', 'APPLY_BY_TYPE']:
                        bpy.ops.object.modifier_apply(modifier=modifier.name)
                    else:  # REMOVE
                        obj.modifiers.remove(modifier)
                    modifier_count += 1
                except Exception as e:
                    print(f"Warning: Could not process modifier {modifier.name} on {obj.name}: {e}")

            processed_count += 1

        self.report({'INFO'}, f"Processed {modifier_count} modifier(s) on {processed_count} object(s)")
        return {'FINISHED'}

    def invoke(self, context, event):
        """Show dialog."""
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        """Draw operator properties."""
        layout = self.layout

        layout.prop(self, 'operation')
        layout.prop(self, 'target')

        if self.operation in ['APPLY_BY_TYPE', 'REMOVE_BY_TYPE']:
            layout.separator()
            layout.label(text="Modifier Types:")
            col = layout.column(align=True)
            col.prop(self, 'subdivision')
            col.prop(self, 'mirror')
            col.prop(self, 'armature')


class MHW_OT_BatchUV(Operator):
    """Batch UV operations"""
    bl_idname = "mhw.batch_uv"
    bl_label = "Batch UV"
    bl_options = {'REGISTER', 'UNDO'}

    operation: bpy.props.EnumProperty(
        name="Operation",
        description="UV operation to perform",
        items=[
            ('SMART_UV', "Smart UV Project", "Smart UV projection"),
            ('UNWRAP', "Unwrap", "Standard unwrap"),
            ('RESET', "Reset UVs", "Reset UVs to bounds"),
        ],
        default='SMART_UV',
    )

    target: bpy.props.EnumProperty(
        name="Target",
        description="Which objects to process",
        items=[
            ('SELECTED', "Selected Objects", "Process selected objects"),
            ('EXPORT_SET', "Active Export Set", "Process objects in active export set"),
        ],
        default='SELECTED',
    )

    angle_limit: bpy.props.FloatProperty(
        name="Angle Limit",
        description="Angle limit for Smart UV",
        default=66.0,
        min=0.0,
        max=89.0,
    )

    island_margin: bpy.props.FloatProperty(
        name="Island Margin",
        description="Margin between UV islands",
        default=0.001,
        min=0.0,
        max=1.0,
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return context.selected_objects or (
            hasattr(context.scene, 'mhw_data') and
            context.scene.mhw_data.export_sets
        )

    def execute(self, context):
        """Perform batch UV operations."""
        # Import backup function
        from . import backup_ops
        if backup_ops.should_create_backup(context, 'batch_ops'):
            backup_ops.create_backup(context, 'batch_uv')

        # Get target objects
        objects = []
        if self.target == 'SELECTED':
            objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        else:  # EXPORT_SET
            mhw = context.scene.mhw_data
            if mhw.export_sets and mhw.active_export_set_index < len(mhw.export_sets):
                export_set = mhw.export_sets[mhw.active_export_set_index]
                objects = [eobj.obje for eobj in export_set.eobjs if eobj.obje and eobj.obje.type == 'MESH']

        if not objects:
            self.report({'WARNING'}, "No mesh objects to process")
            return {'CANCELLED'}

        # Store original selection and mode
        original_active = context.view_layer.objects.active
        original_selection = context.selected_objects
        original_mode = context.mode

        # Process objects
        processed_count = 0

        try:
            for obj in objects:
                # Select only this object
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj

                # Enter edit mode
                bpy.ops.object.mode_set(mode='EDIT')

                # Select all geometry
                bpy.ops.mesh.select_all(action='SELECT')

                # Perform UV operation
                try:
                    if self.operation == 'SMART_UV':
                        bpy.ops.uv.smart_project(
                            angle_limit=self.angle_limit,
                            island_margin=self.island_margin
                        )
                    elif self.operation == 'UNWRAP':
                        bpy.ops.uv.unwrap()
                    elif self.operation == 'RESET':
                        bpy.ops.uv.reset()

                    processed_count += 1
                except Exception as e:
                    print(f"Warning: Could not process UV for {obj.name}: {e}")

                # Return to object mode
                bpy.ops.object.mode_set(mode='OBJECT')

        finally:
            # Restore original selection and mode
            bpy.ops.object.select_all(action='DESELECT')
            for obj in original_selection:
                obj.select_set(True)
            context.view_layer.objects.active = original_active

            if original_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode=original_mode)

        self.report({'INFO'}, f"Processed UVs for {processed_count} object(s)")
        return {'FINISHED'}

    def invoke(self, context, event):
        """Show dialog."""
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        """Draw operator properties."""
        layout = self.layout

        layout.prop(self, 'operation')
        layout.prop(self, 'target')

        if self.operation == 'SMART_UV':
            layout.separator()
            layout.prop(self, 'angle_limit')
            layout.prop(self, 'island_margin')


# Classes to register
classes = (
    MHW_OT_BatchRename,
    MHW_OT_BatchMaterial,
    MHW_OT_BatchModifiers,
    MHW_OT_BatchUV,
)


def register():
    """Register batch operation operators."""
    for cls in classes:
        bpy.utils.register_class(cls)

    print("  Batch Operations: ✓ Registered")


def unregister():
    """Unregister batch operation operators."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
