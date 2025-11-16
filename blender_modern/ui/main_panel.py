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

        # Export Presets
        if mhw.export_presets:
            box.separator()
            row = box.row(align=True)
            row.label(text="Preset:", icon='PRESET')

            # Show current preset name
            if mhw.active_preset_index < len(mhw.export_presets):
                preset = mhw.export_presets[mhw.active_preset_index]
                row.label(text=preset.name)
            else:
                row.label(text="None")

            # Navigation buttons
            col = row.column(align=True)
            col.operator('mhw.preset_navigate', text="", icon='TRIA_LEFT').direction = 'PREV'
            col.operator('mhw.preset_navigate', text="", icon='TRIA_RIGHT').direction = 'NEXT'

            # Apply button
            row.operator('mhw.preset_apply', text="Apply", icon='IMPORT')

            # Save/Delete buttons
            row = box.row(align=True)
            row.operator('mhw.preset_save', text="Save Current", icon='ADD')
            row.operator('mhw.preset_delete', text="Delete", icon='REMOVE')

            # Show preset description if available
            if mhw.active_preset_index < len(mhw.export_presets):
                preset = mhw.export_presets[mhw.active_preset_index]
                if preset.description:
                    row = box.row()
                    row.label(text=f"  {preset.description}", icon='INFO')

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

        # Visual feedback
        row = box.row(align=True)
        row.operator('mhw.highlight_export_set_objects', text='Highlight Set', icon='OUTLINER_OB_LIGHT')
        row.operator('mhw.isolate_export_set', text='Isolate', icon='RESTRICT_VIEW_OFF')

        row = box.row(align=True)
        row.operator('mhw.toggle_wireframe', text='Toggle Wireframe', icon='SHADING_WIRE')
        op = row.operator('mhw.isolate_export_set', text='Un-Isolate', icon='RESTRICT_VIEW_ON')
        op.restore = True

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


class MHW_PT_BackupPanel(Panel):
    """Backup settings panel for MHW Set Organizer."""
    bl_label = "Auto Backup"
    bl_idname = "MHW_PT_BackupPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MHW Tools"
    bl_parent_id = "MHW_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        """Draw panel header with enable checkbox."""
        layout = self.layout
        mhw = context.scene.mhw_data
        layout.prop(mhw, 'backup_enabled', text="")

    def draw(self, context):
        """Draw backup settings panel."""
        layout = self.layout
        scene = context.scene

        if not hasattr(scene, 'mhw_data'):
            layout.label(text="MHW Data not found", icon='ERROR')
            return

        mhw = scene.mhw_data

        # Enable/disable based on backup_enabled
        layout.enabled = mhw.backup_enabled

        # Backup triggers
        box = layout.box()
        box.label(text="Auto-Backup Before:", icon='SYSTEM')
        col = box.column(align=True)
        col.prop(mhw, 'backup_before_batch', text="Batch Operations")
        col.prop(mhw, 'backup_before_ctc', text="CTC Copy")
        col.prop(mhw, 'backup_before_weights', text="Weight Transfer")

        # Backup settings
        box = layout.box()
        box.label(text="Settings:", icon='PREFERENCES')
        col = box.column(align=True)
        col.prop(mhw, 'backup_max_count', text="Keep Backups")
        col.prop(mhw, 'backup_directory', text="Directory")

        # Manual backup operations
        layout.separator()
        row = layout.row(align=True)
        row.operator('mhw.create_backup', text="Create Backup Now", icon='FILE_BACKUP')

        row = layout.row(align=True)
        row.operator('mhw.view_backups', text="View Backups", icon='FILE_FOLDER')
        row.operator('mhw.cleanup_backups', text="Cleanup", icon='TRASH')

        layout.operator('mhw.restore_backup', text="Restore from Backup", icon='LOOP_BACK')


class MHW_PT_BatchOpsPanel(Panel):
    """Batch operations panel for MHW Set Organizer."""
    bl_label = "Batch Operations"
    bl_idname = "MHW_PT_BatchOpsPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MHW Tools"
    bl_parent_id = "MHW_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """Draw batch operations panel."""
        layout = self.layout

        # Batch Rename
        box = layout.box()
        box.label(text="Batch Rename:", icon='SORTALPHA')
        box.operator('mhw.batch_rename', text="Rename Objects", icon='GREASEPENCIL')

        # Batch Material
        box = layout.box()
        box.label(text="Batch Material:", icon='MATERIAL')
        box.operator('mhw.batch_material', text="Apply Material", icon='BRUSH_DATA')

        # Batch Modifiers
        box = layout.box()
        box.label(text="Batch Modifiers:", icon='MODIFIER')
        box.operator('mhw.batch_modifiers', text="Process Modifiers", icon='MODIFIER_ON')

        # Batch UV
        box = layout.box()
        box.label(text="Batch UV:", icon='UV')
        box.operator('mhw.batch_uv', text="Process UVs", icon='UV_DATA')


class MHW_PT_SymmetryPanel(Panel):
    """Symmetry operations panel for MHW Set Organizer."""
    bl_label = "Symmetry Tools"
    bl_idname = "MHW_PT_SymmetryPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MHW Tools"
    bl_parent_id = "MHW_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """Draw symmetry operations panel."""
        layout = self.layout

        # Mirror Export Set
        box = layout.box()
        box.label(text="Mirror Entire Set:", icon='MOD_MIRROR')
        box.operator('mhw.mirror_export_set', text="Mirror L→R", icon='FORWARD').direction = 'L_TO_R'
        box.operator('mhw.mirror_export_set', text="Mirror R→L", icon='BACK').direction = 'R_TO_L'

        # Mirror Materials Only
        box = layout.box()
        box.label(text="Mirror Materials:", icon='MATERIAL')
        box.operator('mhw.mirror_materials', text="Swap L/R Materials", icon='ARROW_LEFTRIGHT')

        # Symmetrize
        box = layout.box()
        box.label(text="Symmetrize:", icon='MOD_MIRROR')
        box.operator('mhw.symmetrize_set', text="Symmetrize Set", icon='MOD_MIRROR')

        # Check Symmetry
        box = layout.box()
        box.label(text="Validation:", icon='CHECKMARK')
        box.operator('mhw.check_symmetry', text="Check Symmetry", icon='VIEWZOOM')


class MHW_PT_TemplatesPanel(Panel):
    """Project templates panel for MHW Set Organizer."""
    bl_label = "Project Templates"
    bl_idname = "MHW_PT_TemplatesPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MHW Tools"
    bl_parent_id = "MHW_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """Draw templates panel."""
        layout = self.layout

        # New from Template
        box = layout.box()
        box.label(text="New Project:", icon='FILE_NEW')
        box.operator('mhw.new_from_template', text="Create from Template", icon='PLUS')

        # Save/Load Custom Templates
        box = layout.box()
        box.label(text="Custom Templates:", icon='DOCUMENTS')
        row = box.row(align=True)
        row.operator('mhw.save_as_template', text="Save", icon='EXPORT')
        row.operator('mhw.load_template', text="Load", icon='IMPORT')


# List of panel classes for registration
classes = [
    MHW_PT_MainPanel,
    MHW_PT_BackupPanel,
    MHW_PT_BatchOpsPanel,
    MHW_PT_SymmetryPanel,
    MHW_PT_TemplatesPanel,
]


def register():
    """Register panel classes."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister panel classes."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
