"""
Utility operators for MHW Set Organizer.

Helper operators for common tasks like renaming, cleanup, and set management.
"""

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty, BoolProperty

from ..utils import bone_utils, mesh_utils


class MHW_OT_RenameBonesAndVG(Operator):
    """Rename bones and vertex groups with .L/.R suffixes"""
    bl_idname = "mhw.rename_bones_and_vg"
    bl_label = "Rename Bones and Vertex Groups"
    bl_options = {'REGISTER', 'UNDO'}

    target_objects: EnumProperty(
        name="Target",
        description="Which objects to process",
        items=[
            ('SELECTED', "Selected Objects", "Process selected objects"),
            ('EXPORT_SET', "Export Set Objects", "Process all objects in active export set"),
        ],
        default='EXPORT_SET'
    )

    bone_naming: EnumProperty(
        name="Bone Naming",
        description="How to name bones",
        items=[
            ('STATYK', "Statyk Armature", "Remove 'Bone_' prefix from bone names"),
            ('RAW', "Raw Bone Names", "Use raw bone names without prefix"),
        ],
        default='STATYK'
    )

    prefix: StringProperty(
        name="Prefix",
        description="Optional prefix to add to renamed objects",
        default=""
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return context.scene is not None

    def execute(self, context):
        """Rename bones and vertex groups."""
        scene = context.scene
        mhw = getattr(scene, 'mhw_data', None)

        # Get objects to process
        if self.target_objects == 'EXPORT_SET':
            if not mhw or not mhw.export_sets:
                self.report({'ERROR'}, "No export sets available")
                return {'CANCELLED'}

            export_set = mhw.export_sets[mhw.active_export_set_index]
            obj_pool = [
                entry.obje for entry in export_set.eobjs
                if entry.obje and entry.obje.name in scene.objects
            ]
        else:
            obj_pool = context.selected_objects

        if not obj_pool:
            self.report({'WARNING'}, "No objects to process")
            return {'CANCELLED'}

        # Get bone hierarchy
        if mhw and mhw.export_sets:
            export_set = mhw.export_sets[mhw.active_export_set_index]
            if export_set.empty_root:
                bone_hierarchy = bone_utils.get_all_children(export_set.empty_root)
            else:
                self.report({'ERROR'}, "No bone hierarchy root set")
                return {'CANCELLED'}
        else:
            self.report({'ERROR'}, "No export set available")
            return {'CANCELLED'}

        # Build bone lookup by function ID
        bone_by_id = {}
        for bone in bone_hierarchy:
            bone_id = bone.get('boneFunction')
            if bone_id is not None:
                bone_by_id[bone_id] = bone

        # Build bone location map for mirror detection
        bone_locations = {}
        for bone in bone_hierarchy:
            world_loc = bone.matrix_world.to_translation()
            mirror_loc = Vector([-world_loc.x, world_loc.y, world_loc.z])
            bone_locations[bone] = (world_loc, mirror_loc)

        # Process each object
        renamed_count = 0

        for obj in obj_pool:
            if obj.type != 'MESH':
                continue

            # Rename vertex groups to match bones
            for vg in obj.vertex_groups:
                # Find corresponding bone
                bone = bpy.data.objects.get(vg.name)
                if not bone or bone not in bone_hierarchy:
                    continue

                bone_id = bone.get('boneFunction')
                if bone_id is None:
                    continue

                # Generate new name
                new_name = bone.name

                # Apply naming convention
                if self.bone_naming == 'STATYK':
                    new_name = new_name.replace('Bone_', '')

                # Add prefix if specified
                if self.prefix:
                    new_name = f"{self.prefix}{new_name}"

                # Detect L/R suffix if needed
                if not new_name.endswith(('.L', '.R')):
                    world_loc = bone_locations[bone][0]
                    if world_loc.x < -0.01:
                        new_name += '.R'
                    elif world_loc.x > 0.01:
                        new_name += '.L'

                # Rename vertex group
                if vg.name != new_name:
                    vg.name = new_name
                    renamed_count += 1

        self.report({'INFO'}, f"Renamed {renamed_count} vertex group(s)")
        return {'FINISHED'}


class MHW_OT_ToggleSetObjects(Operator):
    """Toggle export enabled for all objects in set"""
    bl_idname = "mhw.toggle_set_objects"
    bl_label = "Toggle Set Objects"
    bl_options = {'REGISTER', 'UNDO'}

    enable: BoolProperty(
        name="Enable",
        description="Enable or disable export for all objects",
        default=True
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        scene = context.scene
        if not hasattr(scene, 'mhw_data'):
            return False

        mhw = scene.mhw_data
        return mhw.export_sets and len(mhw.export_sets) > 0

    def execute(self, context):
        """Toggle export for all objects in active set."""
        scene = context.scene
        mhw = scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        count = 0
        for entry in export_set.eobjs:
            entry.export = self.enable
            count += 1

        action = "Enabled" if self.enable else "Disabled"
        self.report({'INFO'}, f"{action} export for {count} object(s)")
        return {'FINISHED'}


class MHW_OT_AssignWeightTag(Operator):
    """Assign weight transfer tag to selected mesh object"""
    bl_idname = "mhw.assign_weight_tag"
    bl_label = "Assign Weight Tag"
    bl_options = {'REGISTER', 'UNDO'}

    tag_name: StringProperty(
        name="Tag Name",
        description="Name of the weight transfer tag",
        default="default"
    )

    role: EnumProperty(
        name="Role",
        description="Role of this object in weight transfer",
        items=[
            ('SOURCE', "Source", "Source object for weight transfer"),
            ('TARGET', "Target", "Target object for weight transfer"),
        ],
        default='TARGET'
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        """Assign weight transfer tag."""
        obj = context.active_object
        scene = context.scene
        mhw = getattr(scene, 'mhw_data', None)

        if not mhw or not mhw.export_sets:
            self.report({'ERROR'}, "No export sets available")
            return {'CANCELLED'}

        export_set = mhw.export_sets[mhw.active_export_set_index]

        # Find object in export set
        obj_entry = None
        for entry in export_set.eobjs:
            if entry.obje == obj:
                obj_entry = entry
                break

        if not obj_entry:
            self.report({'ERROR'}, "Object not in export set")
            return {'CANCELLED'}

        # Get or create tag
        tag_entry = obj_entry.tags.get(self.tag_name)
        if not tag_entry:
            tag_entry = obj_entry.tags.add()
            tag_entry.name = self.tag_name

        # Set tag properties
        tag_entry.use = True
        tag_entry.role = self.role

        self.report({'INFO'}, f"Assigned tag '{self.tag_name}' as {self.role} to {obj.name}")
        return {'FINISHED'}


class MHW_OT_BatchNormalsTransfer(Operator):
    """Transfer normals from source to multiple target objects"""
    bl_idname = "mhw.batch_normals_transfer"
    bl_label = "Batch Normals Transfer"
    bl_options = {'REGISTER', 'UNDO'}

    method: EnumProperty(
        name="Method",
        description="Normal transfer method",
        items=[
            ('TRANSFER', "Data Transfer", "Use data transfer modifier"),
            ('DIRECTIONAL', "Directional", "Use normal edit modifier with directional mode"),
        ],
        default='TRANSFER'
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return (
            context.active_object and
            context.active_object.type == 'MESH' and
            len(context.selected_objects) > 1
        )

    def execute(self, context):
        """Transfer normals from active to selected objects."""
        source = context.active_object
        targets = [obj for obj in context.selected_objects if obj != source and obj.type == 'MESH']

        if not targets:
            self.report({'WARNING'}, "No target objects selected")
            return {'CANCELLED'}

        success_count = 0
        for target in targets:
            try:
                success = mesh_utils.transfer_normals(
                    source,
                    target,
                    method=self.method
                )
                if success:
                    success_count += 1
            except Exception as e:
                self.report({'WARNING'}, f"Failed to transfer normals to {target.name}: {e}")

        self.report({'INFO'}, f"Transferred normals to {success_count}/{len(targets)} object(s)")
        return {'FINISHED'}


class MHW_OT_CopyObjectChangeVG(Operator):
    """Copy selected object and remap vertex groups to target bone hierarchy"""
    bl_idname = "mhw.copy_object_change_vg"
    bl_label = "Copy Object and Change Vertex Groups"
    bl_options = {'REGISTER', 'UNDO'}

    suffix: StringProperty(
        name="Suffix",
        description="Suffix to add to copied object name",
        default="_copy"
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        """Copy object and remap vertex groups."""
        source = context.active_object
        scene = context.scene

        # Create copy
        mesh_copy = source.data.copy()
        obj_copy = source.copy()
        obj_copy.data = mesh_copy
        obj_copy.name = f"{source.name}{self.suffix}"

        # Link to scene
        scene.collection.objects.link(obj_copy)

        # Copy location
        obj_copy.location = source.location

        # Select the copy
        bpy.ops.object.select_all(action='DESELECT')
        obj_copy.select_set(True)
        context.view_layer.objects.active = obj_copy

        self.report({'INFO'}, f"Created copy: {obj_copy.name}")
        return {'FINISHED'}


class MHW_OT_DeleteCollection(Operator):
    """Delete a collection from the scene"""
    bl_idname = "mhw.delete_collection"
    bl_label = "Delete Collection"
    bl_options = {'REGISTER', 'UNDO'}

    collection_type: StringProperty(
        name="Collection Type",
        description="Type of collection to delete",
        default="export_set"
    )

    index: StringProperty(
        name="Index",
        description="Index of item to delete",
        default="0"
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return hasattr(context.scene, 'mhw_data')

    def invoke(self, context, event):
        """Confirm deletion."""
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        """Delete the collection item."""
        scene = context.scene
        mhw = scene.mhw_data

        try:
            idx = int(self.index)
        except ValueError:
            self.report({'ERROR'}, "Invalid index")
            return {'CANCELLED'}

        if self.collection_type == "export_set":
            if idx < len(mhw.export_sets):
                mhw.export_sets.remove(idx)
                # Adjust active index if needed
                if mhw.active_export_set_index >= len(mhw.export_sets):
                    mhw.active_export_set_index = max(0, len(mhw.export_sets) - 1)

                self.report({'INFO'}, "Deleted export set")
                return {'FINISHED'}

        elif self.collection_type == "batch_set":
            if idx < len(mhw.batch_sets):
                mhw.batch_sets.remove(idx)
                if mhw.active_batch_index >= len(mhw.batch_sets):
                    mhw.active_batch_index = max(0, len(mhw.batch_sets) - 1)

                self.report({'INFO'}, "Deleted batch set")
                return {'FINISHED'}

        self.report({'ERROR'}, "Invalid collection or index")
        return {'CANCELLED'}


# List of operator classes for registration
classes = [
    MHW_OT_RenameBonesAndVG,
    MHW_OT_ToggleSetObjects,
    MHW_OT_AssignWeightTag,
    MHW_OT_BatchNormalsTransfer,
    MHW_OT_CopyObjectChangeVG,
    MHW_OT_DeleteCollection,
]


def register():
    """Register operator classes."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister operator classes."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
