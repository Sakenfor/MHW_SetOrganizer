"""
UIList classes for MHW Set Organizer.

Provides list displays for export sets, objects, batch sets, and external sources.
"""

import bpy
from bpy.types import UIList


class MHW_UL_ExportSets(UIList):
    """UIList for displaying export sets."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        """Draw a single export set item."""
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # Show set name
            layout.prop(item, "name", text="", emboss=False, icon='OUTLINER_OB_ARMATURE')

            # Show count of selected objects in this set
            selected_in_set = [
                obj for obj in context.selected_objects
                if any(obj == entry.obje for entry in item.eobjs if entry.obje)
            ]

            if selected_in_set:
                layout.label(text=f"[{len(selected_in_set)}]", icon='MESH_CUBE')

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='OUTLINER_OB_ARMATURE')


class MHW_UL_SetObjects(UIList):
    """UIList for displaying objects in an export set."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        """Draw a single export set object item."""
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # Determine icon based on object type
            icon_name = 'OBJECT_DATAMODE'

            if item.obje:
                obj_type = item.obje.get('Type') or item.obje.get('TYPE')
                if obj_type == 'CCL':
                    icon_name = 'MESH_CAPSULE'

                # Highlight active/selected objects
                if context.active_object == item.obje:
                    icon_name = 'SPACE2'
                elif item.obje.select_get():
                    icon_name = 'SPACE3'

            # Object selector
            layout.prop_search(item, "obje", context.scene, 'objects', icon=icon_name, text="")

            # Export toggle
            export_icon = 'RADIOBUT_ON' if item.export else 'RADIOBUT_OFF'
            layout.prop(item, "export", text="", emboss=False, icon=export_icon)

            # Additional options based on view mode
            scene = context.scene
            if hasattr(scene, 'mhw_data'):
                mhw = scene.mhw_data
                if mhw.export_sets and mhw.active_export_set_index < len(mhw.export_sets):
                    export_set = mhw.export_sets[mhw.active_export_set_index]

                    if export_set.obj_views == 'OTHER':
                        layout.prop(item, 'preserve_quad', text='', icon='SURFACE_NSURFACE')

                    if item.obje:
                        if export_set.obj_views == 'SHAPE_KEY':
                            if item.obje.data and hasattr(item.obje.data, 'shape_keys'):
                                if item.obje.data.shape_keys:
                                    layout.prop_search(
                                        item, 'key_choice',
                                        item.obje.data.shape_keys, 'key_blocks',
                                        text=''
                                    )
                                    apply_icon = 'SPACE2' if item.apply_sk else 'SPACE3'
                                    layout.prop(item, 'apply_sk', text='', icon=apply_icon)

                        elif export_set.obj_views == 'OTHER':
                            # Show hook modifier toggle
                            hooks = [
                                m for m in item.obje.modifiers
                                if m.type == 'HOOK' and m.object
                            ]
                            if hooks:
                                layout.prop(item, 'apply_hooks', text='', icon='HOOK')

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='MESH_CUBE')


class MHW_UL_CTCCopySources(UIList):
    """UIList for displaying CTC copy sources."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        """Draw a single CTC copy source item."""
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # Show source and target
            if item.source:
                layout.label(text=item.source.name, icon='OUTLINER_OB_EMPTY')
            else:
                layout.label(text="<No Source>", icon='ERROR')

            layout.label(text="→", icon='FORWARD')

            if item.target:
                layout.label(text=item.target.name, icon='OUTLINER_OB_ARMATURE')
            else:
                layout.label(text="<No Target>", icon='ERROR')

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='OUTLINER_OB_EMPTY')


class MHW_UL_BatchSets(UIList):
    """UIList for displaying batch export sets."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        """Draw a single batch set item."""
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon='RENDERLAYERS')

            # Show number of sets in batch
            set_count = len(item.sets)
            layout.label(text=f"[{set_count}]", icon='OUTLINER_OB_GROUP_INSTANCE')

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='RENDERLAYERS')


class MHW_UL_BatchSetObjects(UIList):
    """UIList for displaying sets within a batch set."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        """Draw a single batch set object item."""
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            scene = context.scene
            if hasattr(scene, 'mhw_data'):
                mhw = scene.mhw_data

                # Show export set selector
                layout.prop_search(item, "export_set", mhw, "export_sets", text="", icon='OUTLINER_OB_ARMATURE')

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='OUTLINER_OB_ARMATURE')


class MHW_UL_ExternalSources(UIList):
    """UIList for displaying external .blend file sources."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        """Draw a single external source item."""
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "path", text="", emboss=False, icon='FILE_BLEND')

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='FILE_BLEND')


class MHW_UL_MaterialChoicesCTC(UIList):
    """UIList for displaying material choices for CTC weight transfer."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        """Draw a single material choice item."""
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # Show object and material
            if item.obje:
                layout.label(text=item.obje.name, icon='MESH_CUBE')
            else:
                layout.label(text="<No Object>", icon='ERROR')

            if item.mate:
                layout.label(text=item.mate.name, icon='MATERIAL')
            else:
                layout.label(text="<No Material>", icon='ERROR')

            # Toggle for including this material in transfer
            layout.prop(item, "toggle", text="", icon='CHECKBOX_HLT' if item.toggle else 'CHECKBOX_DEHLT')

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='MATERIAL')


# List of UIList classes for registration
classes = [
    MHW_UL_ExportSets,
    MHW_UL_SetObjects,
    MHW_UL_CTCCopySources,
    MHW_UL_BatchSets,
    MHW_UL_BatchSetObjects,
    MHW_UL_ExternalSources,
    MHW_UL_MaterialChoicesCTC,
]


def register():
    """Register UIList classes."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister UIList classes."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
