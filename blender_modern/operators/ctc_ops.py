"""
CTC (Cloth Physics) operators for MHW Set Organizer.

Operators for copying CTC hierarchies, mirroring bones, and managing CTC chains.
"""

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty

from ..core import ctc_manager
from ..utils import bone_utils


class MHW_OT_CopyCTC(Operator):
    """Copy CTC hierarchy from source to target with weight transfer"""
    bl_idname = "mhw.copy_ctc"
    bl_label = "Copy CTC"
    bl_options = {'REGISTER', 'UNDO'}

    copy_from: EnumProperty(
        name="Copy From",
        description="Source of CTC to copy",
        items=[
            ('LOCAL', "Local", "Copy from object in current scene"),
            ('EXTERNAL', "External", "Copy from external .blend file"),
        ],
        default='LOCAL'
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
        """Set up CTC copy operation and show dialog."""
        scene = context.scene
        mhw = scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        # Get CTC organizer (create if doesn't exist)
        if not export_set.ctc_organizer:
            # Property group should already exist, just get it
            ctc_org = export_set.ctc_organizer
        else:
            ctc_org = export_set.ctc_organizer

        # Determine source
        if self.copy_from == 'LOCAL':
            source = export_set.header_copy_source
            if not source:
                self.report({'ERROR'}, "No local CTC source selected")
                return {'CANCELLED'}
        else:
            # External source
            ext_name = export_set.ext_header_copy_name
            if not ext_name:
                self.report({'ERROR'}, "No external CTC source selected")
                return {'CANCELLED'}

            # Parse blend file path
            try:
                blend_file, obj_name = ext_name.split('.blend__')
                blend_file += '.blend'
            except ValueError:
                self.report({'ERROR'}, f"Invalid external source format: {ext_name}")
                return {'CANCELLED'}

            # Check if source in external sources
            ext_source = None
            for ext_src in mhw.external_ctc_sources:
                if ext_src.name == ext_name:
                    ext_source = ext_src
                    break

            if not ext_source:
                self.report({'ERROR'}, f"External source not found: {ext_name}")
                return {'CANCELLED'}

            # Load external object if not already loaded
            source = bpy.data.objects.get(obj_name)
            if not source:
                try:
                    with bpy.data.libraries.load(ext_source.blend_path, link=True) as (data_from, data_to):
                        if obj_name in data_from.objects:
                            data_to.objects = [obj_name]
                        else:
                            self.report({'ERROR'}, f"Object '{obj_name}' not found in {blend_file}")
                            return {'CANCELLED'}

                    # Get the loaded object
                    for obj in data_to.objects:
                        if obj.name == obj_name:
                            source = obj
                            break

                except Exception as e:
                    self.report({'ERROR'}, f"Failed to load external source: {e}")
                    return {'CANCELLED'}

            if not source:
                self.report({'ERROR'}, "Failed to load source object")
                return {'CANCELLED'}

        # Get all children of source
        source_objects = bone_utils.get_all_children(source)
        source_objects.insert(0, source)  # Include source itself

        # Update CTC organizer entries for chains
        src_chains = [
            obj for obj in source_objects
            if obj.get('Type') == 'CTC_Chain' or obj.get('TYPE') == 'CTC_Chain'
        ]

        # Remove entries for chains that no longer exist
        to_remove = []
        for entry in ctc_org.entries:
            if entry.chain not in src_chains:
                to_remove.append(entry)

        for entry in to_remove:
            idx = ctc_org.entries.find(entry.name)
            if idx >= 0:
                ctc_org.entries.remove(idx)

        # Add entries for new chains
        existing_chains = [entry.chain for entry in ctc_org.entries]
        for chain in src_chains:
            if chain not in existing_chains:
                new_entry = ctc_org.entries.add()
                new_entry.chain = chain
                new_entry.toggle = True  # Enable by default

        # Store for execute
        self._export_set = export_set
        self._ctc_org = ctc_org
        self._source = source
        self._source_objects = source_objects

        # Find source export set (for weight transfer tags)
        self._source_export_set = None
        for scene_iter in bpy.data.scenes:
            if not hasattr(scene_iter, 'mhw_data'):
                continue

            for exp_set in scene_iter.mhw_data.export_sets:
                if exp_set.ctc_header == source:
                    self._source_export_set = exp_set
                    break

            if self._source_export_set:
                break

        return context.window_manager.invoke_props_dialog(self, width=400)

    def execute(self, context):
        """Perform CTC copy operation."""
        export_set = self._export_set
        ctc_org = self._ctc_org
        source = self._source
        source_objects = self._source_objects
        source_export_set = self._source_export_set

        try:
            # Perform CTC copy with weights
            success, message = ctc_manager.perform_ctc_copy_with_weights(
                source,
                source_objects,
                source_export_set,
                export_set,
                ctc_org,
                context,
                copy_from_external=(self.copy_from == 'EXTERNAL')
            )

            if success:
                self.report({'INFO'}, message)
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, message)
                return {'CANCELLED'}

        except Exception as e:
            self.report({'ERROR'}, f"CTC copy failed: {e}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}

    def draw(self, context):
        """Draw operator options dialog."""
        layout = self.layout
        ctc_org = self._ctc_org

        # Main options
        col = layout.column(align=True)
        col.label(text="Operation Mode:", icon='SETTINGS')
        row = col.row(align=True)
        row.prop(ctc_org, 'copy_props', icon='MOD_BOOLEAN')
        row = col.row(align=True)
        row.prop(ctc_org, 'transfer_weights', icon='MOD_VERTEX_WEIGHT', text='Transfer Weights')
        row.prop(ctc_org, 'copy_ctc_hierarchy', icon='OUTLINER', text='Copy CTC')

        # Weight transfer settings
        if ctc_org.transfer_weights:
            box = layout.box()
            box.label(text="Weight Transfer Settings:", icon='GROUP_VERTEX')

            row = box.row(align=True)
            row.prop(ctc_org, 'limit_total', text='Limit 4/8')
            row.prop(ctc_org, 'clean_threshold', text='Clean')
            row.prop(ctc_org, 'normalize_weights', text='Normalize')

            row = box.row(align=True)
            row.prop(ctc_org, 'smooth_iterations', text='Smooth')
            row.prop(ctc_org, 'smooth_factor', text='Strength')

            box.prop(ctc_org, 'weight_limit')

            col = box.column(align=True)
            col.label(text="Remove Vertex Groups:")
            col.prop(ctc_org, 'remove_vg_not_found', text='Not Found in Bones')
            row = col.row(align=True)
            row.prop(ctc_org, 'remove_vg_before_transfer', text='Before Transfer')
            row.prop(ctc_org, 'remove_vg_range')

        # Chain selection
        if ctc_org.entries:
            box = layout.box()
            box.label(text="Chains to Copy:", icon='OUTLINER_COLLECTION')

            for entry in ctc_org.entries:
                row = box.row()
                icon = 'CHECKBOX_HLT' if entry.toggle else 'CHECKBOX_DEHLT'
                row.prop(entry, 'toggle', text=entry.chain.name, icon=icon)


class MHW_OT_MirrorBones(Operator):
    """Mirror bone transforms from L to R or R to L"""
    bl_idname = "mhw.mirror_bones"
    bl_label = "Mirror Bones"
    bl_options = {'REGISTER', 'UNDO'}

    ctc_copy_source_index: StringProperty(
        name="CTC Copy Source Index",
        description="Index of CTC copy source to mirror",
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
        """Show mirror options dialog."""
        scene = context.scene
        mhw = scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        # Get CTC copy source
        if self.ctc_copy_source_index:
            try:
                idx = int(self.ctc_copy_source_index)
                if idx < len(export_set.ctc_copy_sources):
                    self._ctc_copy_src = export_set.ctc_copy_sources[idx]
                else:
                    self.report({'ERROR'}, "Invalid CTC copy source index")
                    return {'CANCELLED'}
            except ValueError:
                self.report({'ERROR'}, "Invalid CTC copy source index format")
                return {'CANCELLED'}
        else:
            # Use first copy source
            if export_set.ctc_copy_sources:
                self._ctc_copy_src = export_set.ctc_copy_sources[0]
            else:
                self.report({'ERROR'}, "No CTC copy sources available")
                return {'CANCELLED'}

        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        """Perform bone mirroring."""
        ctc_copy_src = self._ctc_copy_src

        # Determine mirror direction
        if ctc_copy_src.mirror_direction == 'L_TO_R':
            sources = [
                track for track in ctc_copy_src.copy_src_track
                if track.ttype == 'Bone' and track.side == 'L'
            ]
        else:  # R_TO_L
            sources = [
                track for track in ctc_copy_src.copy_src_track
                if track.ttype == 'Bone' and track.side == 'R'
            ]

        mirrored_count = 0

        for source_track in sources:
            if not source_track.pair:
                continue

            source_obj = source_track.o2
            target_obj = source_track.pair

            if not source_obj or not target_obj:
                continue

            # Mirror transform
            src_matrix = source_obj.matrix_local
            src_loc = src_matrix.to_translation()
            src_rot = src_matrix.to_euler()

            # Mirror location (flip X)
            target_obj.location = (-src_loc.x, src_loc.y, src_loc.z)

            # Mirror rotation (flip Y and Z)
            target_obj.rotation_euler = (src_rot.x, -src_rot.y, -src_rot.z)

            # Copy scale
            target_obj.scale = source_obj.scale

            # Insert keyframes if requested
            if ctc_copy_src.mirror_insert_keyframes:
                for obj in [source_obj, target_obj]:
                    obj.keyframe_insert(data_path='location')
                    obj.keyframe_insert(data_path='rotation_euler')
                    obj.keyframe_insert(data_path='scale')

            mirrored_count += 1

        self.report({'INFO'}, f"Mirrored {mirrored_count} bones")
        return {'FINISHED'}

    def draw(self, context):
        """Draw mirror options dialog."""
        layout = self.layout
        ctc_copy_src = self._ctc_copy_src

        layout.prop(ctc_copy_src, 'mirror_direction', text='Direction')
        layout.prop(ctc_copy_src, 'mirror_insert_keyframes', icon='KEYTYPE_KEYFRAME_VEC')


class MHW_OT_UpdateCTCUsers(Operator):
    """Update constraint targets for CTC users"""
    bl_idname = "mhw.update_ctc_users"
    bl_label = "Update CTC Users"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return context.active_object is not None

    def execute(self, context):
        """Update CTC constraint targets."""
        active_obj = context.active_object

        # Get all objects with constraints targeting the active object
        updated_count = 0

        for obj in context.scene.objects:
            for constraint in obj.constraints:
                if constraint.type == 'CHILD_OF' and constraint.name == 'Bone Function':
                    if constraint.target == active_obj:
                        # Update inverse matrix
                        if obj.parent:
                            constraint.inverse_matrix = obj.parent.matrix_world.inverted()
                            updated_count += 1

        self.report({'INFO'}, f"Updated {updated_count} CTC constraint(s)")
        return {'FINISHED'}


# List of operator classes for registration
classes = [
    MHW_OT_CopyCTC,
    MHW_OT_MirrorBones,
    MHW_OT_UpdateCTCUsers,
]


def register():
    """Register operator classes."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister operator classes."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
