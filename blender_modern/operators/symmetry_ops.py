"""
Symmetry operations for MHW Set Organizer.

Provides full left-right mirroring for meshes, materials, weights, and CTC.
"""

import bpy
from bpy.types import Operator
import re


def swap_lr_suffix(name: str) -> str:
    """
    Swap L/R suffixes in a name.

    Supports patterns: _L/_R, .L/.R, _l/_r, .l/.r

    Args:
        name: Name to process

    Returns:
        Name with swapped L/R suffix
    """
    # Try different patterns
    patterns = [
        (r'_L$', '_R'),
        (r'_R$', '_L'),
        (r'\.L$', '.R'),
        (r'\.R$', '.L'),
        (r'_l$', '_r'),
        (r'_r$', '_l'),
        (r'\.l$', '.r'),
        (r'\.r$', '.l'),
    ]

    for pattern, replacement in patterns:
        if re.search(pattern, name):
            return re.sub(pattern, replacement, name)

    return name


class MHW_OT_MirrorExportSet(Operator):
    """Mirror entire export set (meshes, materials, weights) from L to R or R to L"""
    bl_idname = "mhw.mirror_export_set"
    bl_label = "Mirror Export Set"
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(
        name="Direction",
        description="Mirror direction",
        items=[
            ('L_TO_R', "Left to Right", "Mirror from left to right"),
            ('R_TO_L', "Right to Left", "Mirror from right to left"),
        ],
        default='L_TO_R',
    )

    mirror_meshes: bpy.props.BoolProperty(
        name="Mirror Meshes",
        description="Mirror mesh geometry",
        default=True,
    )

    mirror_materials: bpy.props.BoolProperty(
        name="Mirror Materials",
        description="Mirror material assignments (swap _L/_R suffixes)",
        default=True,
    )

    mirror_weights: bpy.props.BoolProperty(
        name="Mirror Weights",
        description="Mirror vertex group weights",
        default=True,
    )

    mirror_shapekeys: bpy.props.BoolProperty(
        name="Mirror Shape Keys",
        description="Mirror shape keys",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        if not hasattr(context.scene, 'mhw_data'):
            return False

        mhw = context.scene.mhw_data
        if not mhw.export_sets or mhw.active_export_set_index >= len(mhw.export_sets):
            return False

        return True

    def execute(self, context):
        """Mirror export set."""
        # Import backup function
        from . import backup_ops
        if backup_ops.should_create_backup(context, 'batch_ops'):
            backup_ops.create_backup(context, 'mirror_export_set')

        mhw = context.scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        # Get all mesh objects in export set
        mesh_objects = [eobj.obje for eobj in export_set.eobjs if eobj.obje and eobj.obje.type == 'MESH']

        if not mesh_objects:
            self.report({'WARNING'}, "No mesh objects in export set")
            return {'CANCELLED'}

        mirrored_count = 0

        for obj in mesh_objects:
            try:
                # Mirror mesh geometry
                if self.mirror_meshes:
                    self.mirror_mesh_geometry(obj, self.direction)

                # Mirror materials
                if self.mirror_materials:
                    self.mirror_object_materials(obj)

                # Mirror vertex groups/weights
                if self.mirror_weights:
                    self.mirror_vertex_groups(obj, self.direction)

                # Mirror shape keys
                if self.mirror_shapekeys and obj.data.shape_keys:
                    self.mirror_shape_keys(obj, self.direction)

                mirrored_count += 1

            except Exception as e:
                self.report({'WARNING'}, f"Failed to mirror {obj.name}: {e}")

        self.report({'INFO'}, f"Mirrored {mirrored_count} object(s)")
        return {'FINISHED'}

    def mirror_mesh_geometry(self, obj, direction):
        """Mirror mesh geometry across X axis."""
        # Store current mode
        original_mode = bpy.context.mode

        # Select only this object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        # Enter edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')

        # Mirror across X axis
        # This uses Blender's built-in mirror functionality
        bpy.ops.transform.mirror(orient_type='GLOBAL', constraint_axis=(True, False, False))

        # Flip normals to maintain correct facing
        bpy.ops.mesh.flip_normals()

        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')

    def mirror_object_materials(self, obj):
        """Mirror material assignments by swapping L/R suffixes."""
        for i, mat_slot in enumerate(obj.material_slots):
            if not mat_slot.material:
                continue

            current_mat_name = mat_slot.material.name
            mirrored_mat_name = swap_lr_suffix(current_mat_name)

            # Try to find the mirrored material
            mirrored_mat = bpy.data.materials.get(mirrored_mat_name)
            if mirrored_mat:
                obj.material_slots[i].material = mirrored_mat

    def mirror_vertex_groups(self, obj, direction):
        """Mirror vertex groups."""
        if not obj.vertex_groups:
            return

        # Use Blender's built-in mirror vertex groups
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.vertex_group_mirror(use_topology=False)

    def mirror_shape_keys(self, obj, direction):
        """Mirror shape keys."""
        if not obj.data.shape_keys:
            return

        # Store current mode
        original_mode = bpy.context.mode

        # Enter edit mode
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')

        # Mirror each shape key
        for key_block in obj.data.shape_keys.key_blocks:
            if key_block.name == 'Basis':
                continue

            # Set active shape key
            obj.active_shape_key_index = obj.data.shape_keys.key_blocks.keys().index(key_block.name)

            # Mirror the shape key
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.transform.mirror(orient_type='GLOBAL', constraint_axis=(True, False, False))

        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')

    def invoke(self, context, event):
        """Show dialog."""
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        """Draw operator properties."""
        layout = self.layout

        layout.prop(self, 'direction')
        layout.separator()

        col = layout.column(align=True)
        col.prop(self, 'mirror_meshes')
        col.prop(self, 'mirror_materials')
        col.prop(self, 'mirror_weights')
        col.prop(self, 'mirror_shapekeys')


class MHW_OT_MirrorMaterials(Operator):
    """Mirror material assignments only (swap _L/_R suffixes)"""
    bl_idname = "mhw.mirror_materials"
    bl_label = "Mirror Materials"
    bl_options = {'REGISTER', 'UNDO'}

    target: bpy.props.EnumProperty(
        name="Target",
        description="Which objects to process",
        items=[
            ('SELECTED', "Selected Objects", "Mirror materials on selected objects"),
            ('EXPORT_SET', "Active Export Set", "Mirror materials on active export set"),
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
        """Mirror materials."""
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

        swapped_count = 0

        for obj in objects:
            for i, mat_slot in enumerate(obj.material_slots):
                if not mat_slot.material:
                    continue

                current_mat_name = mat_slot.material.name
                mirrored_mat_name = swap_lr_suffix(current_mat_name)

                # Try to find the mirrored material
                mirrored_mat = bpy.data.materials.get(mirrored_mat_name)
                if mirrored_mat and mirrored_mat != mat_slot.material:
                    obj.material_slots[i].material = mirrored_mat
                    swapped_count += 1

        self.report({'INFO'}, f"Swapped {swapped_count} material assignment(s)")
        return {'FINISHED'}


class MHW_OT_SymmetrizeSet(Operator):
    """Make export set perfectly symmetric by mirroring one side"""
    bl_idname = "mhw.symmetrize_set"
    bl_label = "Symmetrize Set"
    bl_options = {'REGISTER', 'UNDO'}

    source_side: bpy.props.EnumProperty(
        name="Source Side",
        description="Which side to use as source",
        items=[
            ('LEFT', "Left to Right", "Use left side as source, mirror to right"),
            ('RIGHT', "Right to Left", "Use right side as source, mirror to left"),
        ],
        default='LEFT',
    )

    merge_center: bpy.props.BoolProperty(
        name="Merge Center Vertices",
        description="Merge vertices at the center (X=0)",
        default=True,
    )

    merge_distance: bpy.props.FloatProperty(
        name="Merge Distance",
        description="Distance threshold for merging center vertices",
        default=0.001,
        min=0.0001,
        max=1.0,
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        if not hasattr(context.scene, 'mhw_data'):
            return False

        mhw = context.scene.mhw_data
        if not mhw.export_sets or mhw.active_export_set_index >= len(mhw.export_sets):
            return False

        return True

    def execute(self, context):
        """Symmetrize export set."""
        # Import backup function
        from . import backup_ops
        if backup_ops.should_create_backup(context, 'batch_ops'):
            backup_ops.create_backup(context, 'symmetrize_set')

        mhw = context.scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        # Get all mesh objects in export set
        mesh_objects = [eobj.obje for eobj in export_set.eobjs if eobj.obje and eobj.obje.type == 'MESH']

        if not mesh_objects:
            self.report({'WARNING'}, "No mesh objects in export set")
            return {'CANCELLED'}

        symmetrized_count = 0

        for obj in mesh_objects:
            try:
                # Store current mode
                original_mode = bpy.context.mode

                # Select only this object
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj

                # Enter edit mode
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')

                # Delete one side
                if self.source_side == 'LEFT':
                    # Delete right side (positive X)
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.mesh.select_axis(mode='POSITIVE', axis='X', threshold=0.0001)
                    bpy.ops.mesh.delete(type='VERT')
                else:
                    # Delete left side (negative X)
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.mesh.select_axis(mode='NEGATIVE', axis='X', threshold=0.0001)
                    bpy.ops.mesh.delete(type='VERT')

                # Select all remaining geometry
                bpy.ops.mesh.select_all(action='SELECT')

                # Add mirror modifier
                bpy.ops.object.mode_set(mode='OBJECT')
                mirror_mod = obj.modifiers.new(name="Symmetrize", type='MIRROR')
                mirror_mod.use_axis[0] = True  # X axis
                mirror_mod.use_axis[1] = False
                mirror_mod.use_axis[2] = False
                mirror_mod.use_clip = self.merge_center
                mirror_mod.merge_threshold = self.merge_distance

                # Apply mirror modifier
                bpy.ops.object.modifier_apply(modifier="Symmetrize")

                symmetrized_count += 1

            except Exception as e:
                self.report({'WARNING'}, f"Failed to symmetrize {obj.name}: {e}")

        self.report({'INFO'}, f"Symmetrized {symmetrized_count} object(s)")
        return {'FINISHED'}

    def invoke(self, context, event):
        """Show dialog."""
        return context.window_manager.invoke_props_dialog(self)


class MHW_OT_CheckSymmetry(Operator):
    """Check if export set is symmetric"""
    bl_idname = "mhw.check_symmetry"
    bl_label = "Check Symmetry"
    bl_options = {'REGISTER'}

    tolerance: bpy.props.FloatProperty(
        name="Tolerance",
        description="Maximum difference to consider symmetric",
        default=0.001,
        min=0.0001,
        max=1.0,
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        if not hasattr(context.scene, 'mhw_data'):
            return False

        mhw = context.scene.mhw_data
        if not mhw.export_sets or mhw.active_export_set_index >= len(mhw.export_sets):
            return False

        return True

    def execute(self, context):
        """Check symmetry."""
        mhw = context.scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        # Get all mesh objects in export set
        mesh_objects = [eobj.obje for eobj in export_set.eobjs if eobj.obje and eobj.obje.type == 'MESH']

        if not mesh_objects:
            self.report({'WARNING'}, "No mesh objects in export set")
            return {'CANCELLED'}

        asymmetric_objects = []

        for obj in mesh_objects:
            if not self.is_mesh_symmetric(obj, self.tolerance):
                asymmetric_objects.append(obj.name)

        if asymmetric_objects:
            self.report({'WARNING'}, f"Asymmetric objects: {', '.join(asymmetric_objects)}")
        else:
            self.report({'INFO'}, "All objects are symmetric!")

        return {'FINISHED'}

    def is_mesh_symmetric(self, obj, tolerance):
        """
        Check if a mesh is symmetric across X axis.

        Args:
            obj: Object to check
            tolerance: Maximum distance difference

        Returns:
            True if symmetric, False otherwise
        """
        mesh = obj.data

        # For each vertex, check if there's a corresponding mirrored vertex
        for vert in mesh.vertices:
            co = vert.co
            mirrored_co = (-co.x, co.y, co.z)

            # Find closest vertex to mirrored position
            found_mirror = False
            for other_vert in mesh.vertices:
                if (other_vert.co - mirrored_co).length < tolerance:
                    found_mirror = True
                    break

            if not found_mirror:
                return False

        return True

    def invoke(self, context, event):
        """Show dialog."""
        return context.window_manager.invoke_props_dialog(self)


# Classes to register
classes = (
    MHW_OT_MirrorExportSet,
    MHW_OT_MirrorMaterials,
    MHW_OT_SymmetrizeSet,
    MHW_OT_CheckSymmetry,
)


def register():
    """Register symmetry operators."""
    for cls in classes:
        bpy.utils.register_class(cls)

    print("  Symmetry System: ✓ Registered")


def unregister():
    """Unregister symmetry operators."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
