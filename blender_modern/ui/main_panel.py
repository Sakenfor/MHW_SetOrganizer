"""
Main UI panel for MHW Set Organizer.

Provides the primary interface in the 3D View sidebar for managing export sets,
importing/exporting files, and configuring CTC physics.
"""

import bpy
from bpy.types import Panel


class MHW_PT_MainPanel(Panel):
    """Main panel for MHW Set Organizer in 3D View sidebar."""
    bl_label = "MHW Set Organizer"
    bl_idname = "MHW_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MHW Tools"

    def draw(self, context):
        """Draw the main panel."""
        layout = self.layout
        scene = context.scene

        if not hasattr(scene, 'mhw_data'):
            layout.label(text="MHW Data not found", icon='ERROR')
            return

        mhw = scene.mhw_data

        # Settings Section
        self.draw_settings(layout, mhw)

        # CTC Header Copier Section
        self.draw_ctc_copier(layout, context, mhw)

        # Batch Sets Section
        self.draw_batch_sets(layout, context, mhw)

        # Main Export Sets Section
        self.draw_export_sets(layout, context, mhw)

    def draw_settings(self, layout, mhw):
        """Draw settings section."""
        box = layout.box()
        box.label(text="Settings:", icon='PREFERENCES')

        # Game path
        box.prop(mhw, 'game_path', text='Game')

        # Resource path
        box.prop(mhw, 'resource_path', text='Resource')

        # Settings buttons row
        row = box.row()
        row.operator('mhw.save_settings', text='Save Settings', icon='FILE_TICK')
        row.operator('mhw.load_settings', text='Load Settings', icon='FILE_REFRESH')

        # Collection organization
        row = box.row()
        row.operator('mhw.create_all_collections', text='Create All Collections', icon='OUTLINER_COLLECTION')
        row.operator('mhw.organize_collections', text='Organize', icon='FILE_FOLDER')

    def draw_ctc_copier(self, layout, context, mhw):
        """Draw CTC header copier section."""
        box = layout.box()

        # Header with toggle
        row = box.row()
        row.label(text="CTC Header Copier:", icon='OUTLINER_OB_FORCE_FIELD')
        row.prop(mhw, 'show_ctc_copier', text="", icon='TRIA_DOWN' if mhw.show_ctc_copier else 'TRIA_RIGHT')

        if not mhw.show_ctc_copier:
            return

        # Get active export set
        if not mhw.export_sets or mhw.active_export_set_index >= len(mhw.export_sets):
            box.label(text="No active export set", icon='INFO')
            return

        export_set = mhw.export_sets[mhw.active_export_set_index]

        # Local copy
        row = box.row(align=True)
        row.prop_search(export_set, 'header_copy_source', bpy.data, 'objects', text='')
        op = row.operator('mhw.copy_ctc', text='Local Copy', icon='COPYDOWN')
        op.copy_from = 'LOCAL'

        # External copy
        row = box.row(align=True)
        row.operator('mhw.refresh_external_ctc', text='', icon='FILE_REFRESH')
        row.prop_search(export_set, 'ext_header_copy_name', mhw, 'external_ctc_sources', text='', icon='PLUGIN')
        op = row.operator('mhw.copy_ctc', text='External Copy', icon='APPEND_BLEND')
        op.copy_from = 'EXTERNAL'

        # Copy options
        row = box.row()
        row.prop(mhw, 'ctc_prepend_text', text='Prepend')
        row.prop(mhw, 'ctc_new_name', text='New Name')

        row = box.row()
        row.prop(mhw, 'ctc_type_prefix', text='Type Name Position')
        row.prop(mhw, 'ctc_copy_use_active', text='Use Active Object')

    def draw_batch_sets(self, layout, context, mhw):
        """Draw batch sets section."""
        box = layout.box()

        # Header with toggle
        row = box.row()
        row.label(text="Batch Export:", icon='RENDERLAYERS')
        row.prop(mhw, 'show_batch_sets', text="", icon='TRIA_DOWN' if mhw.show_batch_sets else 'TRIA_RIGHT')

        if not mhw.show_batch_sets:
            return

        # Batch sets list
        row = box.row()
        col = row.column()
        col.template_list(
            "MHW_UL_BatchSets", "",
            mhw, "batch_sets",
            mhw, "active_batch_index",
            rows=2
        )

        # List controls
        col = row.column(align=True)
        col.operator('mhw.batch_set_add', icon='ADD', text="")
        col.operator('mhw.batch_set_remove', icon='REMOVE', text="")
        col.separator()
        col.operator('mhw.batch_set_move', icon='TRIA_UP', text="").direction = 'UP'
        col.operator('mhw.batch_set_move', icon='TRIA_DOWN', text="").direction = 'DOWN'

        # Active batch set details
        if mhw.batch_sets and mhw.active_batch_index < len(mhw.batch_sets):
            batch_set = mhw.batch_sets[mhw.active_batch_index]

            # Batch set settings
            box.prop(batch_set, 'export_path', text='Export Path')
            row = box.row()
            row.prop(batch_set, 'export_mod3', text='MOD3', icon='MESH_CUBE')
            row.prop(batch_set, 'export_ctc', text='CTC', icon='MOD_SIMPLEDEFORM')
            row.prop(batch_set, 'export_ccl', text='CCL', icon='META_CAPSULE')

            # Batch export buttons
            row = box.row(align=True)
            row.operator('mhw.batch_export', text=f'Batch Export: {batch_set.name}', icon='EXPORT')
            row.operator('mhw.validate_batch_set', text='Validate', icon='CHECKMARK')

            # Sets in batch list
            box.label(text="Sets in Batch:", icon='OUTLINER_OB_GROUP_INSTANCE')
            row = box.row()
            col = row.column()
            col.template_list(
                "MHW_UL_BatchSetObjects", "",
                batch_set, "sets",
                batch_set, "active_set_index",
                rows=2
            )

            # List controls
            col = row.column(align=True)
            col.operator('mhw.batch_set_object_add', icon='ADD', text="")
            col.operator('mhw.batch_set_object_remove', icon='REMOVE', text="")

    def draw_export_sets(self, layout, context, mhw):
        """Draw main export sets section."""
        box = layout.box()

        # Header with toggle
        row = box.row()
        row.label(text="Export Sets:", icon='OUTLINER_OB_ARMATURE')
        row.prop(mhw, 'show_export_sets', text="", icon='TRIA_DOWN' if mhw.show_export_sets else 'TRIA_RIGHT')

        if not mhw.show_export_sets:
            return

        # Export sets list
        row = box.row()
        col = row.column()
        col.template_list(
            "MHW_UL_ExportSets", "",
            mhw, "export_sets",
            mhw, "active_export_set_index",
            rows=3
        )

        # List controls
        col = row.column(align=True)
        col.operator('mhw.export_set_add', icon='ADD', text="")
        col.operator('mhw.export_set_remove', icon='REMOVE', text="")
        col.separator()
        col.operator('mhw.export_set_move', icon='TRIA_UP', text="").direction = 'UP'
        col.operator('mhw.export_set_move', icon='TRIA_DOWN', text="").direction = 'DOWN'

        # Active export set details
        if mhw.export_sets and mhw.active_export_set_index < len(mhw.export_sets):
            export_set = mhw.export_sets[mhw.active_export_set_index]
            self.draw_export_set_details(box, context, export_set, mhw)

    def draw_export_set_details(self, layout, context, export_set, mhw):
        """Draw active export set details."""
        # Export section
        box = layout.box()
        box.label(text=f"Export: {export_set.name}", icon='EXPORT')

        row = box.row(align=True)
        op = row.operator('mhw.export', text='MOD3', icon='MESH_CUBE')
        op.export_type = 'MOD3'
        op = row.operator('mhw.export', text='CTC', icon='MOD_SIMPLEDEFORM')
        op.export_type = 'CTC'
        op = row.operator('mhw.export', text='CCL', icon='META_CAPSULE')
        op.export_type = 'CCL'

        # Validation button
        row = box.row()
        row.operator('mhw.validate_export_set', text='Validate Set', icon='CHECKMARK')

        if export_set.export_path:
            row = box.row()
            row.label(text=export_set.export_path, icon='FILE_FOLDER')

        # Import section
        box = layout.box()
        box.label(text=f"Import: {export_set.name}", icon='IMPORT')

        row = box.row(align=True)
        op = row.operator('mhw.import', text='MOD3', icon='IMPORT')
        op.import_type = 'MOD3'
        op = row.operator('mhw.import', text='CTC', icon='IMPORT')
        op.import_type = 'CTC'
        op = row.operator('mhw.import', text='CCL', icon='IMPORT')
        op.import_type = 'CCL'

        if export_set.import_path:
            row = box.row()
            row.label(text=export_set.import_path, icon='FILE_FOLDER')

        # Export set settings
        box = layout.box()
        box.label(text="Set Settings:", icon='SETTINGS')

        # Armor settings
        row = box.row()
        row.prop_search(export_set, 'armor_name', mhw, 'armor_database', text='')
        row.prop(export_set, 'armor_part', text='')
        row.prop(export_set, 'gender', text='')

        # Root and header
        row = box.row()
        row.prop_search(export_set, 'empty_root', context.scene, 'objects', text='Root', icon='OUTLINER_OB_MESH')

        row = box.row()
        row.prop_search(export_set, 'ctc_header', context.scene, 'objects', text='CTC Header', icon='OUTLINER_OB_FORCE_FIELD')

        # Custom export path
        row = box.row()
        row.prop(export_set, 'custom_export_path', text='Custom Path')

        row = box.row(align=True)
        row.prop(export_set, 'use_custom_path', text='Use Custom Path', icon='COPY_ID')
        row.prop(export_set, 'append_native_pc', text='Native PC', icon='WORDWRAP_OFF')

        # Utility buttons
        row = box.row(align=True)
        row.operator('mhw.rename_bones_and_vg', text='Rename Bones/VG', icon='SORTALPHA')
        row.operator('mhw.update_ctc_users', text='Update CTC', icon='FILE_REFRESH')

        # Collection management
        row = box.row(align=True)
        row.operator('mhw.create_export_set_collection', text='Create Collection', icon='OUTLINER_COLLECTION')
        row.operator('mhw.sync_collection_to_set', text='Sync from Collection', icon='FILE_REFRESH')

        # Objects in set
        box = layout.box()
        box.label(text="Objects in Set:", icon='MESH_CUBE')

        # View mode selector
        row = box.row(align=True)
        row.prop(export_set, 'obj_views', text='View', expand=True)

        # Objects list
        row = box.row()
        col = row.column()
        col.template_list(
            "MHW_UL_SetObjects", "",
            export_set, "eobjs",
            export_set, "active_object_index",
            rows=4
        )

        # List controls
        col = row.column(align=True)
        col.operator('mhw.export_set_object_add', icon='ADD', text="")
        col.operator('mhw.export_set_object_remove', icon='REMOVE', text="")
        col.separator()
        col.operator('mhw.toggle_set_objects', icon='CHECKBOX_HLT', text="").enable = True
        col.operator('mhw.toggle_set_objects', icon='CHECKBOX_DEHLT', text="").enable = False


# List of panel classes for registration
classes = [
    MHW_PT_MainPanel,
]


def register():
    """Register panel classes."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister panel classes."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
