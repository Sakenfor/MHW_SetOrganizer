"""
Pie Menu for MHW Set Organizer.

Provides quick access to common operations via radial menu (default: Q key).
"""

import bpy
from bpy.types import Menu


class MHW_MT_PieMenu(Menu):
    """Main MHW Tools Pie Menu"""
    bl_label = "MHW Tools"
    bl_idname = "MHW_MT_pie_menu"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        # Check if MHW data exists
        if not hasattr(context.scene, 'mhw_data'):
            pie.label(text="MHW data not found", icon='ERROR')
            return

        mhw = context.scene.mhw_data

        # West - Quick Export submenu
        pie.menu("MHW_MT_PieExport", text="Quick Export", icon='EXPORT')

        # East - Collections
        pie.operator("mhw.create_collection_from_export_set", text="Create Collection", icon='OUTLINER_COLLECTION')

        # South - Highlight Set
        pie.operator("mhw.highlight_export_set_objects", text="Highlight Set", icon='LIGHT')

        # North - Validate
        pie.operator("mhw.validate_export_set", text="Validate Set", icon='CHECKMARK')

        # North-West - Add to Active Set
        if context.selected_objects:
            pie.operator("mhw.quick_add_to_export_set", text="Add to Active Set", icon='ADD')
        else:
            pie.separator()

        # North-East - Import from Game
        pie.operator("mhw.import_armor_from_game", text="Import from Game", icon='IMPORT')

        # South-West - Select Set Objects
        pie.operator("mhw.select_export_set_objects", text="Select Set Objects", icon='RESTRICT_SELECT_OFF')

        # South-East - Utilities submenu
        pie.menu("MHW_MT_PieUtilities", text="Utilities", icon='TOOL_SETTINGS')


class MHW_MT_PieExport(Menu):
    """Export submenu for Pie Menu"""
    bl_label = "Quick Export"
    bl_idname = "MHW_MT_PieExport"

    def draw(self, context):
        layout = self.layout

        # Check if we have an active export set
        mhw = context.scene.mhw_data
        if not mhw.export_sets or mhw.active_export_set_index >= len(mhw.export_sets):
            layout.label(text="No active export set", icon='ERROR')
            return

        export_set = mhw.export_sets[mhw.active_export_set_index]
        layout.label(text=f"Export: {export_set.name}", icon='OUTLINER_OB_ARMATURE')
        layout.separator()

        # Export operators
        layout.operator("mhw.export_mod3", text="Export MOD3", icon='MESH_DATA')
        layout.operator("mhw.export_ctc", text="Export CTC", icon='PHYSICS')
        layout.operator("mhw.export_ccl", text="Export CCL", icon='MESH_CAPSULE')
        layout.separator()
        layout.operator("mhw.export_all", text="Export All", icon='EXPORT')


class MHW_MT_PieUtilities(Menu):
    """Utilities submenu for Pie Menu"""
    bl_label = "Utilities"
    bl_idname = "MHW_MT_PieUtilities"

    def draw(self, context):
        layout = self.layout

        # CTC Operations
        layout.label(text="CTC Tools", icon='PHYSICS')
        layout.operator("mhw.copy_ctc_from_set", text="Copy CTC from Set", icon='COPYDOWN')
        layout.operator("mhw.mirror_bones", text="Mirror Bones", icon='MOD_MIRROR')
        layout.separator()

        # Validation & Cleanup
        layout.label(text="Validation", icon='CHECKMARK')
        layout.operator("mhw.validate_weights", text="Validate Weights", icon='GROUP_VERTEX')
        layout.separator()

        # Visual Feedback
        layout.label(text="Visual", icon='LIGHT')
        layout.operator("mhw.highlight_export_set_objects", text="Highlight Objects", icon='LIGHT')
        layout.operator("mhw.isolate_export_set_objects", text="Isolate Objects", icon='RESTRICT_VIEW_ON')


class MHW_MT_PieSetSwitch(Menu):
    """Switch Export Set submenu for Pie Menu"""
    bl_label = "Switch Export Set"
    bl_idname = "MHW_MT_PieSetSwitch"

    def draw(self, context):
        layout = self.layout
        mhw = context.scene.mhw_data

        if not mhw.export_sets:
            layout.label(text="No export sets", icon='INFO')
            return

        # List all export sets
        for i, export_set in enumerate(mhw.export_sets):
            icon = 'RADIOBUT_ON' if i == mhw.active_export_set_index else 'RADIOBUT_OFF'
            op = layout.operator("mhw.switch_export_set", text=export_set.name, icon=icon)
            op.set_index = i


class MHW_OT_SwitchExportSet(bpy.types.Operator):
    """Switch to a specific export set"""
    bl_idname = "mhw.switch_export_set"
    bl_label = "Switch Export Set"
    bl_options = {'REGISTER', 'UNDO'}

    set_index: bpy.props.IntProperty(
        name="Set Index",
        description="Index of the export set to switch to",
        default=0,
    )

    def execute(self, context):
        """Switch to the specified export set."""
        mhw = context.scene.mhw_data

        if 0 <= self.set_index < len(mhw.export_sets):
            mhw.active_export_set_index = self.set_index
            export_set = mhw.export_sets[self.set_index]
            self.report({'INFO'}, f"Switched to export set: {export_set.name}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Invalid export set index")
            return {'CANCELLED'}


# Keymap storage
addon_keymaps = []


# Classes to register
classes = (
    MHW_MT_PieMenu,
    MHW_MT_PieExport,
    MHW_MT_PieUtilities,
    MHW_MT_PieSetSwitch,
    MHW_OT_SwitchExportSet,
)


def register():
    """Register pie menu classes and keymaps."""
    for cls in classes:
        bpy.utils.register_class(cls)

    # Add keymap
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new("wm.call_menu_pie", 'Q', 'PRESS')
        kmi.properties.name = "MHW_MT_pie_menu"
        addon_keymaps.append((km, kmi))

    print("  Pie Menu: ✓ Registered (Press Q in 3D View)")


def unregister():
    """Unregister pie menu classes and keymaps."""
    # Remove keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # Unregister classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
