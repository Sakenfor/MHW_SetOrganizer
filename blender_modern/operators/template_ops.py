"""
Project template operators for MHW Set Organizer.

Provides quick project setup with pre-configured templates.
"""

import bpy
from bpy.types import Operator


def create_full_armor_set(context, armor_id: str, armor_name: str):
    """
    Create a full armor set template.

    Args:
        context: Blender context
        armor_id: Armor ID (e.g., "pl999_0000")
        armor_name: Armor display name
    """
    mhw = context.scene.mhw_data

    # Define armor parts
    parts = [
        ("head", "Head"),
        ("body", "Body"),
        ("arm", "Arms"),
        ("waist", "Waist"),
        ("leg", "Legs"),
    ]

    for part_id, part_name in parts:
        # Create export set
        export_set = mhw.export_sets.add()
        export_set.name = f"{armor_name} - {part_name}"
        export_set.set_name = f"{armor_id}_{part_id}"

        # Set export paths
        export_set.mod3_export_path = f"//export/{armor_id}/{part_id}.mod3"
        export_set.ctc_export_path = f"//export/{armor_id}/{part_id}.ctc"
        export_set.ccl_export_path = f"//export/{armor_id}/{part_id}.ccl"

        # Create collection
        collection_name = f"{armor_id}_{part_id}"
        if collection_name not in bpy.data.collections:
            collection = bpy.data.collections.new(collection_name)
            context.scene.collection.children.link(collection)

    # Set active export set to first one
    if mhw.export_sets:
        mhw.active_export_set_index = 0


def create_single_piece_template(context, armor_id: str, armor_name: str, part_type: str):
    """
    Create a single piece template.

    Args:
        context: Blender context
        armor_id: Armor ID
        armor_name: Armor display name
        part_type: Part type (head, body, arm, waist, leg)
    """
    mhw = context.scene.mhw_data

    # Create export set
    export_set = mhw.export_sets.add()
    export_set.name = f"{armor_name} - {part_type.capitalize()}"
    export_set.set_name = f"{armor_id}_{part_type}"

    # Set export paths
    export_set.mod3_export_path = f"//export/{armor_id}/{part_type}.mod3"
    export_set.ctc_export_path = f"//export/{armor_id}/{part_type}.ctc"
    export_set.ccl_export_path = f"//export/{armor_id}/{part_type}.ccl"

    # Create collection
    collection_name = f"{armor_id}_{part_type}"
    if collection_name not in bpy.data.collections:
        collection = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(collection)

    # Set as active
    mhw.active_export_set_index = len(mhw.export_sets) - 1


def create_layered_armor_template(context, armor_id: str, armor_name: str):
    """
    Create a layered armor template.

    Args:
        context: Blender context
        armor_id: Armor ID
        armor_name: Armor display name
    """
    mhw = context.scene.mhw_data

    # Layered armor typically has all parts
    parts = [
        ("head", "Head"),
        ("body", "Body"),
        ("arm", "Arms"),
        ("waist", "Waist"),
        ("leg", "Legs"),
    ]

    for part_id, part_name in parts:
        # Create export set
        export_set = mhw.export_sets.add()
        export_set.name = f"{armor_name} (Layered) - {part_name}"
        export_set.set_name = f"{armor_id}_{part_id}_layered"

        # Set export paths (layered armor path structure)
        export_set.mod3_export_path = f"//export/{armor_id}/layered/{part_id}.mod3"
        export_set.ctc_export_path = f"//export/{armor_id}/layered/{part_id}.ctc"
        export_set.ccl_export_path = f"//export/{armor_id}/layered/{part_id}.ccl"

        # Create collection
        collection_name = f"{armor_id}_{part_id}_layered"
        if collection_name not in bpy.data.collections:
            collection = bpy.data.collections.new(collection_name)
            context.scene.collection.children.link(collection)

    # Set active export set to first one
    if mhw.export_sets:
        mhw.active_export_set_index = len(mhw.export_sets) - len(parts)


class MHW_OT_NewFromTemplate(Operator):
    """Create new project from template"""
    bl_idname = "mhw.new_from_template"
    bl_label = "New from Template"
    bl_options = {'REGISTER', 'UNDO'}

    template: bpy.props.EnumProperty(
        name="Template",
        description="Project template to use",
        items=[
            ('FULL_SET', "Full Armor Set", "Complete armor set with all 5 pieces"),
            ('SINGLE', "Single Piece", "Single armor piece"),
            ('LAYERED', "Layered Armor", "Layered armor set"),
        ],
        default='FULL_SET',
    )

    armor_id: bpy.props.StringProperty(
        name="Armor ID",
        description="Armor identifier (e.g., pl999_0000)",
        default="pl999_0000",
    )

    armor_name: bpy.props.StringProperty(
        name="Armor Name",
        description="Display name for the armor",
        default="Custom Armor",
    )

    part_type: bpy.props.EnumProperty(
        name="Part Type",
        description="Armor part type (for single piece)",
        items=[
            ('head', "Head", "Head piece"),
            ('body', "Body", "Body/Chest piece"),
            ('arm', "Arms", "Arm/Gloves piece"),
            ('waist', "Waist", "Waist/Belt piece"),
            ('leg', "Legs", "Leg/Boots piece"),
        ],
        default='body',
    )

    clear_existing: bpy.props.BoolProperty(
        name="Clear Existing Sets",
        description="Remove all existing export sets before creating template",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return hasattr(context.scene, 'mhw_data')

    def execute(self, context):
        """Create project from template."""
        mhw = context.scene.mhw_data

        # Clear existing sets if requested
        if self.clear_existing:
            mhw.export_sets.clear()
            mhw.active_export_set_index = 0

        # Create template based on type
        if self.template == 'FULL_SET':
            create_full_armor_set(context, self.armor_id, self.armor_name)
            self.report({'INFO'}, f"Created full armor set template: {self.armor_name}")

        elif self.template == 'SINGLE':
            create_single_piece_template(context, self.armor_id, self.armor_name, self.part_type)
            self.report({'INFO'}, f"Created single piece template: {self.armor_name} - {self.part_type}")

        elif self.template == 'LAYERED':
            create_layered_armor_template(context, self.armor_id, self.armor_name)
            self.report({'INFO'}, f"Created layered armor template: {self.armor_name}")

        return {'FINISHED'}

    def invoke(self, context, event):
        """Show dialog."""
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        """Draw operator properties."""
        layout = self.layout

        layout.prop(self, 'template')
        layout.separator()

        layout.prop(self, 'armor_id')
        layout.prop(self, 'armor_name')

        # Show part type for single piece template
        if self.template == 'SINGLE':
            layout.prop(self, 'part_type')

        layout.separator()
        layout.prop(self, 'clear_existing')


class MHW_OT_SaveAsTemplate(Operator):
    """Save current export sets as a custom template"""
    bl_idname = "mhw.save_as_template"
    bl_label = "Save as Template"
    bl_options = {'REGISTER'}

    template_name: bpy.props.StringProperty(
        name="Template Name",
        description="Name for the custom template",
        default="My Template",
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        if not hasattr(context.scene, 'mhw_data'):
            return False

        mhw = context.scene.mhw_data
        return len(mhw.export_sets) > 0

    def execute(self, context):
        """Save template."""
        import json
        from pathlib import Path

        mhw = context.scene.mhw_data

        # Get addon directory
        addon_dir = Path(__file__).parent.parent
        templates_dir = addon_dir / "templates"
        templates_dir.mkdir(exist_ok=True)

        # Collect template data
        template_data = {
            "name": self.template_name,
            "export_sets": []
        }

        for export_set in mhw.export_sets:
            set_data = {
                "name": export_set.name,
                "set_name": export_set.set_name,
                "mod3_path": export_set.mod3_export_path,
                "ctc_path": export_set.ctc_export_path,
                "ccl_path": export_set.ccl_export_path,
            }
            template_data["export_sets"].append(set_data)

        # Save to JSON
        template_file = templates_dir / f"{self.template_name}.json"
        with open(template_file, 'w') as f:
            json.dump(template_data, f, indent=2)

        self.report({'INFO'}, f"Saved template: {self.template_name}")
        return {'FINISHED'}

    def invoke(self, context, event):
        """Show dialog."""
        return context.window_manager.invoke_props_dialog(self)


class MHW_OT_LoadTemplate(Operator):
    """Load a custom template"""
    bl_idname = "mhw.load_template"
    bl_label = "Load Template"
    bl_options = {'REGISTER', 'UNDO'}

    template_file: bpy.props.StringProperty(
        name="Template File",
        description="Path to template file",
        subtype='FILE_PATH',
    )

    clear_existing: bpy.props.BoolProperty(
        name="Clear Existing Sets",
        description="Remove all existing export sets before loading template",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return hasattr(context.scene, 'mhw_data')

    def execute(self, context):
        """Load template."""
        import json
        from pathlib import Path

        if not self.template_file:
            self.report({'ERROR'}, "No template file selected")
            return {'CANCELLED'}

        template_path = Path(self.template_file)
        if not template_path.exists():
            self.report({'ERROR'}, "Template file not found")
            return {'CANCELLED'}

        try:
            # Load template data
            with open(template_path, 'r') as f:
                template_data = json.load(f)

            mhw = context.scene.mhw_data

            # Clear existing sets if requested
            if self.clear_existing:
                mhw.export_sets.clear()

            # Create export sets from template
            for set_data in template_data.get("export_sets", []):
                export_set = mhw.export_sets.add()
                export_set.name = set_data.get("name", "Unnamed")
                export_set.set_name = set_data.get("set_name", "")
                export_set.mod3_export_path = set_data.get("mod3_path", "")
                export_set.ctc_export_path = set_data.get("ctc_path", "")
                export_set.ccl_export_path = set_data.get("ccl_path", "")

            # Set active to first set
            if mhw.export_sets:
                mhw.active_export_set_index = 0

            self.report({'INFO'}, f"Loaded template: {template_data.get('name', 'Unknown')}")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to load template: {e}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        """Show file browser."""
        from pathlib import Path

        addon_dir = Path(__file__).parent.parent
        templates_dir = addon_dir / "templates"

        if templates_dir.exists():
            self.template_file = str(templates_dir)

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# Classes to register
classes = (
    MHW_OT_NewFromTemplate,
    MHW_OT_SaveAsTemplate,
    MHW_OT_LoadTemplate,
)


def register():
    """Register template operators."""
    for cls in classes:
        bpy.utils.register_class(cls)

    print("  Project Templates: ✓ Registered")


def unregister():
    """Unregister template operators."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
