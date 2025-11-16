"""
Validation operators for MHW Set Organizer.

Provides pre-export validation with detailed UI feedback.
"""

import bpy
from bpy.types import Operator
from ..utils import validation


class MHW_OT_ValidateExportSet(Operator):
    """Check export set for common issues before export"""
    bl_idname = "mhw.validate_export_set"
    bl_label = "Validate Export Set"
    bl_options = {'REGISTER'}

    # Store validation results for draw()
    _issues = []
    _warnings = []
    _info = []

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
        """Run validation and show results dialog."""
        self._issues = []
        self._warnings = []
        self._info = []

        mhw = context.scene.mhw_data
        export_set = mhw.export_sets[mhw.active_export_set_index]

        # Validate export set
        is_valid, errors = validation.validate_export_set(export_set, context)

        if errors:
            self._issues = errors

        # Check individual objects
        mesh_count = 0
        empty_slots = 0
        no_material_count = 0

        for eobj in export_set.eobjs:
            if not eobj.obje:
                empty_slots += 1
                self._warnings.append("Empty object slot found")
                continue

            if eobj.obje.type == 'MESH':
                mesh_count += 1

                # Check for materials
                if not eobj.obje.data.materials:
                    no_material_count += 1
                    self._warnings.append(f"{eobj.obje.name}: No materials assigned")

                # Check for degenerate geometry
                mesh = eobj.obje.data
                if hasattr(mesh, 'validate'):
                    # Count issues
                    if len(mesh.vertices) == 0:
                        self._issues.append(f"{eobj.obje.name}: No vertices")
                    elif len(mesh.polygons) == 0:
                        self._issues.append(f"{eobj.obje.name}: No faces")

        # Check paths
        if not export_set.export_path:
            self._warnings.append("Export path not configured")

        # Check root and CTC header
        if export_set.empty_root:
            is_valid_root, error = validation.validate_root_object(export_set.empty_root)
            if not is_valid_root:
                self._issues.append(f"Invalid root: {error}")
        else:
            self._warnings.append("No skeleton root assigned")

        if export_set.ctc_header:
            is_valid_ctc, error = validation.validate_ctc_header(export_set.ctc_header)
            if not is_valid_ctc:
                self._issues.append(f"Invalid CTC header: {error}")

        # Info
        self._info.append(f"Export Set: {export_set.name}")
        self._info.append(f"Mesh Objects: {mesh_count}")
        if export_set.armor_name:
            self._info.append(f"Armor: {export_set.armor_name}")
        self._info.append(f"Part: {export_set.armor_part.capitalize()}")
        self._info.append(f"Gender: {'Female' if export_set.gender == 'f' else 'Male'}")

        # Show dialog with results
        return context.window_manager.invoke_props_dialog(self, width=400)

    def execute(self, context):
        """Execute after dialog confirmation."""
        if self._issues:
            self.report({'ERROR'}, f"Validation found {len(self._issues)} issue(s)")
            return {'CANCELLED'}
        elif self._warnings:
            self.report({'WARNING'}, f"Validation found {len(self._warnings)} warning(s)")
            return {'FINISHED'}
        else:
            self.report({'INFO'}, "Export set is valid")
            return {'FINISHED'}

    def draw(self, context):
        """Draw validation results dialog."""
        layout = self.layout

        # Info section
        if self._info:
            box = layout.box()
            box.label(text="Export Set Info:", icon='INFO')
            for info in self._info:
                box.label(text=info)

        # Issues section
        if self._issues:
            box = layout.box()
            box.label(text=f"Issues ({len(self._issues)}):", icon='ERROR')
            for issue in self._issues:
                row = box.row()
                row.label(text=issue, icon='CANCEL')

        # Warnings section
        if self._warnings:
            box = layout.box()
            box.label(text=f"Warnings ({len(self._warnings)}):", icon='ERROR')
            for warning in self._warnings:
                row = box.row()
                row.label(text=warning, icon='INFO')

        # All clear
        if not self._issues and not self._warnings:
            box = layout.box()
            box.label(text="Export set is valid!", icon='CHECKMARK')
            box.label(text="Ready to export")

        layout.separator()
        if self._issues:
            layout.label(text="Fix issues before exporting", icon='ERROR')


class MHW_OT_ValidateBatchSet(Operator):
    """Validate all export sets in active batch"""
    bl_idname = "mhw.validate_batch_set"
    bl_label = "Validate Batch Set"
    bl_options = {'REGISTER'}

    _results = []

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        scene = context.scene
        if not hasattr(scene, 'mhw_data'):
            return False

        mhw = scene.mhw_data
        if not mhw.batch_sets or mhw.active_batch_index >= len(mhw.batch_sets):
            return False

        return True

    def invoke(self, context, event):
        """Run validation on all sets in batch."""
        self._results = []

        mhw = context.scene.mhw_data
        batch_set = mhw.batch_sets[mhw.active_batch_index]

        # Validate each set in batch
        for set_ref in batch_set.sets:
            if not set_ref.export:
                continue

            # Find export set
            set_name = set_ref.export_set or set_ref.name
            export_set = None
            for exp_set in mhw.export_sets:
                if exp_set.name == set_name:
                    export_set = exp_set
                    break

            if not export_set:
                self._results.append({
                    'name': set_name,
                    'status': 'error',
                    'message': 'Export set not found'
                })
                continue

            # Validate
            is_valid, errors = validation.validate_export_set(export_set, context)

            if errors:
                self._results.append({
                    'name': export_set.name,
                    'status': 'error',
                    'message': f"{len(errors)} issue(s) found"
                })
            else:
                self._results.append({
                    'name': export_set.name,
                    'status': 'ok',
                    'message': 'Valid'
                })

        return context.window_manager.invoke_props_dialog(self, width=400)

    def execute(self, context):
        """Execute after dialog."""
        error_count = sum(1 for r in self._results if r['status'] == 'error')

        if error_count > 0:
            self.report({'WARNING'}, f"{error_count} set(s) have issues")
        else:
            self.report({'INFO'}, "All sets are valid")

        return {'FINISHED'}

    def draw(self, context):
        """Draw batch validation results."""
        layout = self.layout

        mhw = context.scene.mhw_data
        batch_set = mhw.batch_sets[mhw.active_batch_index]

        layout.label(text=f"Batch: {batch_set.name}", icon='PRESET')
        layout.separator()

        if not self._results:
            layout.label(text="No sets to validate", icon='INFO')
            return

        box = layout.box()
        box.label(text=f"Validation Results ({len(self._results)} sets):")

        for result in self._results:
            row = box.row()

            if result['status'] == 'ok':
                row.label(text=result['name'], icon='CHECKMARK')
                row.label(text=result['message'])
            else:
                row.label(text=result['name'], icon='ERROR')
                row.label(text=result['message'])


# Classes to register
classes = (
    MHW_OT_ValidateExportSet,
    MHW_OT_ValidateBatchSet,
)


def register():
    """Register validation operators."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister validation operators."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
