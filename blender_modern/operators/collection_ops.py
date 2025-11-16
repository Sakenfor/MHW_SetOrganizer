"""
Collection management operators for MHW Set Organizer.

Provides automatic collection creation and organization for export sets.
"""

import bpy
from bpy.types import Operator


class MHW_OT_CreateExportSetCollection(Operator):
    """Create collection for active export set and move objects to it"""
    bl_idname = "mhw.create_export_set_collection"
    bl_label = "Create Collection for Set"
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
        """Create collection and organize objects."""
        mhw = context.scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        # Generate collection name
        collection_name = f"MHW_{export_set.name}"

        # Check if collection already exists
        collection = bpy.data.collections.get(collection_name)

        if not collection:
            # Create new collection
            collection = bpy.data.collections.new(collection_name)
            context.scene.collection.children.link(collection)

        # Set collection color based on armor part
        color_map = {
            'head': 'COLOR_01',      # Red
            'body': 'COLOR_02',      # Orange
            'arm': 'COLOR_03',       # Yellow
            'waist': 'COLOR_04',     # Green
            'leg': 'COLOR_05',       # Blue
        }
        collection.color_tag = color_map.get(export_set.armor_part, 'COLOR_08')

        # Move objects to collection
        moved_count = 0
        for eobj in export_set.eobjs:
            if not eobj.obje:
                continue

            obj = eobj.obje

            # Remove from all other collections
            for coll in obj.users_collection:
                coll.objects.unlink(obj)

            # Add to our collection
            if obj.name not in collection.objects:
                collection.objects.link(obj)
                moved_count += 1

        # Also add root and CTC header if present
        if export_set.empty_root:
            for coll in export_set.empty_root.users_collection:
                coll.objects.unlink(export_set.empty_root)
            if export_set.empty_root.name not in collection.objects:
                collection.objects.link(export_set.empty_root)
                moved_count += 1

        if export_set.ctc_header:
            for coll in export_set.ctc_header.users_collection:
                coll.objects.unlink(export_set.ctc_header)
            if export_set.ctc_header.name not in collection.objects:
                collection.objects.link(export_set.ctc_header)
                moved_count += 1

        self.report({'INFO'}, f"Created collection '{collection_name}' with {moved_count} object(s)")
        return {'FINISHED'}


class MHW_OT_CreateAllCollections(Operator):
    """Create collections for all export sets"""
    bl_idname = "mhw.create_all_collections"
    bl_label = "Create All Collections"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        scene = context.scene
        if not hasattr(scene, 'mhw_data'):
            return False

        mhw = scene.mhw_data
        return len(mhw.export_sets) > 0

    def execute(self, context):
        """Create collections for all export sets."""
        mhw = context.scene.mhw_data

        created_count = 0

        for i, export_set in enumerate(mhw.export_sets):
            # Temporarily set as active
            old_index = mhw.active_export_set_index
            mhw.active_export_set_index = i

            # Create collection
            bpy.ops.mhw.create_export_set_collection()
            created_count += 1

            # Restore active index
            mhw.active_export_set_index = old_index

        self.report({'INFO'}, f"Created {created_count} collection(s)")
        return {'FINISHED'}


class MHW_OT_SyncCollectionToSet(Operator):
    """Add all objects from collection to active export set"""
    bl_idname = "mhw.sync_collection_to_set"
    bl_label = "Sync Collection to Set"
    bl_description = "Add all mesh objects from the export set's collection"
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
        """Sync collection objects to export set."""
        mhw = context.scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        # Find collection
        collection_name = f"MHW_{export_set.name}"
        collection = bpy.data.collections.get(collection_name)

        if not collection:
            self.report({'ERROR'}, f"Collection '{collection_name}' not found")
            return {'CANCELLED'}

        # Add mesh objects from collection to export set
        added_count = 0

        for obj in collection.objects:
            if obj.type != 'MESH':
                continue

            # Check if already in export set
            already_exists = False
            for eobj in export_set.eobjs:
                if eobj.obje == obj:
                    already_exists = True
                    break

            if not already_exists:
                new_entry = export_set.eobjs.add()
                new_entry.obje = obj
                new_entry.export = True
                added_count += 1

        self.report({'INFO'}, f"Added {added_count} object(s) from collection")
        return {'FINISHED'}


class MHW_OT_OrganizeCollections(Operator):
    """Organize all MHW collections into a parent collection"""
    bl_idname = "mhw.organize_collections"
    bl_label = "Organize Collections"
    bl_description = "Create master MHW collection and organize all export set collections under it"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Organize collections into hierarchy."""
        # Create master collection if it doesn't exist
        master_name = "MHW_Set_Organizer"
        master = bpy.data.collections.get(master_name)

        if not master:
            master = bpy.data.collections.new(master_name)
            context.scene.collection.children.link(master)
            master.color_tag = 'COLOR_07'  # Purple for master

        # Find all MHW_ collections
        mhw_collections = [c for c in bpy.data.collections if c.name.startswith("MHW_") and c != master]

        moved_count = 0
        for coll in mhw_collections:
            # Remove from scene root
            if coll in context.scene.collection.children.values():
                context.scene.collection.children.unlink(coll)

            # Add to master
            if coll.name not in master.children:
                master.children.link(coll)
                moved_count += 1

        self.report({'INFO'}, f"Organized {moved_count} collection(s) under '{master_name}'")
        return {'FINISHED'}


# Classes to register
classes = (
    MHW_OT_CreateExportSetCollection,
    MHW_OT_CreateAllCollections,
    MHW_OT_SyncCollectionToSet,
    MHW_OT_OrganizeCollections,
)


def register():
    """Register collection operators."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister collection operators."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
