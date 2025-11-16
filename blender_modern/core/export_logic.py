"""
Export logic for MHW Set Organizer.

Contains the core business logic for exporting MOD3, CTC, and CCL files.
Separated from operators for better testability and code organization.
"""

from typing import List, Dict, Optional, Tuple
import os
import bpy

from .. import addon_config
from ..utils import mesh_utils, file_utils, validation


class ExportContext:
    """
    Context object for export operations.

    Stores state during export to allow proper cleanup even if errors occur.
    """

    def __init__(self):
        self.quad_saved: Dict[bpy.types.Object, bpy.types.Mesh] = {}
        self.hook_saved: Dict[bpy.types.Object, str] = {}
        self.meshes_to_delete: List[bpy.types.Mesh] = []
        self.objects_to_delete: List[bpy.types.Object] = {}
        self.object_visibility: Dict[bpy.types.Object, Dict] = {}
        self.type_properties: Dict[bpy.types.Object, str] = {}

    def restore(self, scene: bpy.types.Scene) -> None:
        """Restore all saved object states."""
        # Restore quad meshes
        for obj, original_mesh in self.quad_saved.items():
            if obj and obj.name in bpy.data.objects:
                obj.data = original_mesh

        # Delete temporary meshes and objects
        for mesh in self.meshes_to_delete:
            if mesh:
                bpy.data.meshes.remove(mesh)

        # Restore original names
        for obj, original_name in self.hook_saved.items():
            if obj and obj.name in bpy.data.objects:
                obj.name = original_name

        # Restore object visibility
        for obj, state in self.object_visibility.items():
            if obj and obj.name in scene.objects:
                obj.hide_set(state.get('hide', False))

        # Restore Type properties
        for obj, type_value in self.type_properties.items():
            if obj and obj.name in scene.objects:
                obj['Type'] = type_value


def get_valid_export_objects(
    export_set,
    scene: bpy.types.Scene,
    export_type: str = 'MOD3'
) -> List[bpy.types.Object]:
    """
    Get list of valid objects to export from a set.

    Args:
        export_set: Export set property group.
        scene: Current Blender scene.
        export_type: Type of export ('MOD3', 'CTC', 'CCL').

    Returns:
        List of objects marked for export.
    """
    valid_objects = []

    for obj_entry in export_set.eobjs:
        # Check if marked for export
        if not obj_entry.export:
            continue

        # Check object still exists
        if not obj_entry.obje or obj_entry.obje.name not in scene.objects:
            continue

        obj = obj_entry.obje

        # For CCL, only include objects marked as CCL
        if export_type == 'CCL':
            if obj.get('Type') != addon_config.TYPE_CCL:
                continue

        valid_objects.append(obj)

    return valid_objects


def apply_shape_key_to_object(
    obj: bpy.types.Object,
    method: str,
    global_key_name: Optional[str] = None,
    specific_key_name: Optional[str] = None
) -> bool:
    """
    Apply shape key to an object.

    Args:
        obj: Object to apply shape key to.
        method: Application method ('GLOBAL', 'ACTIVE', 'SPECIFIC').
        global_key_name: Name of global key (for GLOBAL method).
        specific_key_name: Name of specific key (for SPECIFIC method).

    Returns:
        True if shape key was applied, False otherwise.
    """
    if not obj.data.shape_keys:
        return False

    shape_keys = obj.data.shape_keys.key_blocks
    target_key = None

    if method == 'ACTIVE':
        # Create key from mix of all active keys
        bpy.ops.object.shape_key_add(from_mix=True)
        target_key = shape_keys[obj.active_shape_key_index]

    elif method == 'GLOBAL' and global_key_name:
        target_key = shape_keys.get(global_key_name)

    elif method == 'SPECIFIC' and specific_key_name:
        target_key = shape_keys.get(specific_key_name)

    if not target_key:
        # No valid key found, remove all shape keys
        bpy.ops.object.shape_key_remove(all=True)
        return False

    # Apply the shape key
    obj.active_shape_key_index = 0
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.blend_from_shape(shape=target_key.name)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.update()

    # Remove shape keys after applying
    bpy.ops.object.shape_key_remove(all=True)

    return True


def prepare_object_for_export(
    obj: bpy.types.Object,
    obj_settings,
    export_set,
    scene: bpy.types.Scene,
    context: ExportContext
) -> Optional[bpy.types.Object]:
    """
    Prepare an object for export by applying modifiers and shape keys.

    Args:
        obj: Object to prepare.
        obj_settings: Object's export settings from export set.
        export_set: Parent export set.
        scene: Current scene.
        context: Export context for tracking changes.

    Returns:
        Object to export (may be a temporary copy), or None on error.
    """
    needs_shape_keys = (
        obj_settings.apply_shape_key and
        export_set.use_shape_keys and
        obj.data.shape_keys
    )

    needs_hooks = (
        obj_settings.apply_hooks and
        any(m.type == 'HOOK' and m.object for m in obj.modifiers)
    )

    # Simple case: Just triangulate in place
    if obj_settings.preserve_quad and not needs_hooks and not needs_shape_keys:
        # Save original mesh
        context.quad_saved[obj] = obj.data

        # Triangulate
        triangulated = mesh_utils.triangulate_mesh(obj, preserve_original=True)
        obj.data = triangulated

        return obj

    # Complex case: Need to create a copy
    if needs_hooks or needs_shape_keys:
        original_name = obj.name

        # Create copy
        dummy = obj.copy()
        scene.collection.objects.link(dummy)

        # Handle mesh data
        if obj_settings.preserve_quad:
            dummy.data = mesh_utils.triangulate_mesh(dummy, preserve_original=True)
        else:
            dummy.data = obj.data.copy()

        # Track for cleanup
        context.meshes_to_delete.append(dummy.data)

        # Temporarily rename original
        temp_name = f'hooksave_{original_name}'
        obj.name = temp_name
        context.hook_saved[obj] = original_name
        dummy.name = original_name

        # Set as active
        bpy.context.view_layer.objects.active = dummy
        dummy.select_set(True)

        # Apply shape keys if needed
        if needs_shape_keys:
            shape_key_name = (
                obj_settings.shape_key_choice
                if export_set.shape_key_method == 'SPECIFIC'
                else export_set.shape_key_choice
            )

            apply_shape_key_to_object(
                dummy,
                export_set.shape_key_method,
                export_set.shape_key_choice,
                shape_key_name
            )

        # Apply hooks if needed
        if needs_hooks:
            hooks = [m for m in dummy.modifiers if m.type == 'HOOK' and m.object]
            for hook in hooks:
                with bpy.context.temp_override(object=dummy):
                    bpy.ops.object.modifier_apply(
                        modifier=hook.name,
                        apply_as='DATA'
                    )

        return dummy

    # No special handling needed
    return obj


def set_object_types_for_export(
    scene: bpy.types.Scene,
    root_object: Optional[bpy.types.Object],
    export_objects: List[bpy.types.Object],
    export_type: str,
    context: ExportContext
) -> None:
    """
    Set object Type properties for recognition by external exporters.

    Args:
        scene: Current scene.
        root_object: Root/header object for the export.
        export_objects: Objects to export.
        export_type: Type of export ('MOD3', 'CTC', 'CCL').
        context: Export context for tracking changes.
    """
    # Type resets for different export types
    type_resets = {
        'MOD3': addon_config.TYPE_SKELETON_ROOT,
        'CTC': addon_config.TYPE_CTC_HEADER,
        'CCL': addon_config.TYPE_CCL,
    }

    target_type = type_resets.get(export_type, '')

    for obj in scene.objects:
        # Save current Type if it exists
        current_type = obj.get('Type')
        if current_type and current_type in type_resets.values():
            context.type_properties[obj] = current_type
            obj['Type'] = 'aaaa'  # Temporary value to disable recognition

        # Set target object type
        if obj == root_object or (export_type == 'CCL' and obj in export_objects):
            obj['Type'] = target_type


def hide_non_export_objects(
    scene: bpy.types.Scene,
    export_objects: List[bpy.types.Object],
    context: ExportContext
) -> None:
    """
    Hide all objects not in the export list.

    Args:
        scene: Current scene.
        export_objects: Objects to keep visible.
        context: Export context for tracking changes.
    """
    for obj in scene.objects:
        # Save current visibility
        context.object_visibility[obj] = {'hide': obj.hide_get()}

        # Hide non-export objects
        if obj not in export_objects:
            obj.hide_set(True)
        else:
            obj.hide_set(False)


def export_mod3(
    export_set,
    scene: bpy.types.Scene,
    file_path: str
) -> Tuple[bool, str]:
    """
    Export MOD3 mesh file.

    Args:
        export_set: Export set property group.
        scene: Current scene.
        file_path: Full path to export file.

    Returns:
        Tuple of (success, error_message).
    """
    try:
        bpy.ops.custom_export.export_mhw_mod3(
            filepath=file_path,
            export_hidden=False,
            coerce_fourth=export_set.coerce_fourth,
            split_normals=export_set.split_normals,
            highest_lod=export_set.highest_lod
        )
        return True, ""
    except AttributeError:
        return False, "MOD3 exporter not found. Install Mod3-MHW-Importer addon."
    except Exception as e:
        return False, f"MOD3 export failed: {e}"


def export_ctc(
    export_set,
    scene: bpy.types.Scene,
    file_path: str,
    align_frames: bool = True,
    align_nodes: bool = False
) -> Tuple[bool, str]:
    """
    Export CTC cloth physics file.

    Args:
        export_set: Export set property group.
        scene: Current scene.
        file_path: Full path to export file.
        align_frames: Whether to align frames in hierarchy.
        align_nodes: Whether to align nodes to bones.

    Returns:
        Tuple of (success, error_message).
    """
    # Align CTC if requested
    if (align_frames or align_nodes) and export_set.ctc_header:
        from ..utils import bone_utils
        # TODO: Implement alignment logic
        # This was in general_functions.py fAlignVarious
        pass

    try:
        bpy.ops.custom_export.export_mhw_ctc(filepath=file_path)
        return True, ""
    except AttributeError:
        return False, "CTC exporter not found. Install CTC-MHW-Editor addon."
    except Exception as e:
        return False, f"CTC export failed: {e}"


def export_ccl(
    export_set,
    scene: bpy.types.Scene,
    file_path: str
) -> Tuple[bool, str]:
    """
    Export CCL collision capsule file.

    Args:
        export_set: Export set property group.
        scene: Current scene.
        file_path: Full path to export file.

    Returns:
        Tuple of (success, error_message).
    """
    try:
        bpy.ops.custom_export.export_mhw_ccl(filepath=file_path)
        return True, ""
    except AttributeError:
        return False, "CCL exporter not found. Install CTC-MHW-Editor addon."
    except Exception as e:
        return False, f"CCL export failed: {e}"


def perform_export(
    export_set,
    context: bpy.types.Context,
    export_type: str = 'MOD3',
    align_frames: bool = True,
    align_nodes: bool = False
) -> Tuple[bool, str]:
    """
    Main export function.

    Args:
        export_set: Export set property group.
        context: Blender context.
        export_type: Type to export ('MOD3', 'CTC', 'CCL').
        align_frames: Align CTC frames (CTC only).
        align_nodes: Align CTC nodes (CTC only).

    Returns:
        Tuple of (success, error_message).
    """
    scene = context.scene
    mhw = scene.mhw_data

    # Validate export set
    is_valid, errors = validation.validate_export_set(export_set)
    if not is_valid:
        return False, f"Invalid export set: {', '.join(errors)}"

    # Get valid objects (not needed for CTC export)
    export_objects = []
    if export_type != 'CTC':
        export_objects = get_valid_export_objects(export_set, scene, export_type)

        if not export_objects:
            return False, "No objects to export"

    # Determine root object
    if export_type == 'MOD3':
        root_object = export_set.empty_root
    elif export_type == 'CTC':
        root_object = export_set.ctc_header
    else:  # CCL
        root_object = None

    # Get export path
    export_path = export_set.export_path
    if not export_path:
        return False, "No export path set"

    # Add extension
    extension = addon_config.EXT_MOD3 if export_type == 'MOD3' else \
                addon_config.EXT_CTC if export_type == 'CTC' else \
                addon_config.EXT_CCL

    full_path = export_path + extension

    # Ensure directory exists
    directory = os.path.dirname(full_path)
    if not file_utils.ensure_directory_exists(directory):
        return False, f"Cannot create export directory: {directory}"

    # Create export context for cleanup
    export_ctx = ExportContext()

    try:
        # Prepare objects for export (MOD3 only)
        prepared_objects = export_objects.copy()
        if export_type == 'MOD3':
            prepared_objects = []
            for obj in export_objects:
                # Find object settings
                obj_settings = None
                for entry in export_set.eobjs:
                    if entry.obje == obj:
                        obj_settings = entry
                        break

                if not obj_settings:
                    continue

                # Prepare object
                prepared_obj = prepare_object_for_export(
                    obj,
                    obj_settings,
                    export_set,
                    scene,
                    export_ctx
                )

                if prepared_obj:
                    prepared_objects.append(prepared_obj)

                    # Apply material name override
                    if obj_settings.material_name and len(obj_settings.material_name) > 2:
                        prepared_obj.data['material'] = obj_settings.material_name

        # Set object types for recognition
        set_object_types_for_export(
            scene,
            root_object,
            prepared_objects,
            export_type,
            export_ctx
        )

        # Hide non-export objects (MOD3 only)
        if export_type == 'MOD3':
            hide_non_export_objects(scene, prepared_objects, export_ctx)

        # Update scene
        bpy.context.view_layer.update()

        # Perform actual export
        success = False
        error_msg = ""

        if export_type == 'MOD3':
            success, error_msg = export_mod3(export_set, scene, full_path)
        elif export_type == 'CTC':
            success, error_msg = export_ctc(
                export_set, scene, full_path, align_frames, align_nodes
            )
        elif export_type == 'CCL':
            success, error_msg = export_ccl(export_set, scene, full_path)

        if success:
            print(f"✓ Successfully exported {export_type}: {full_path}")
            return True, full_path
        else:
            return False, error_msg

    finally:
        # Always restore object states
        export_ctx.restore(scene)
        bpy.context.view_layer.update()


def batch_export(
    batch_set,
    mhw_data,
    context: bpy.types.Context
) -> Tuple[int, int, List[str]]:
    """
    Export multiple sets in batch.

    Args:
        batch_set: Batch export set property group.
        mhw_data: Main MHW data property group.
        context: Blender context.

    Returns:
        Tuple of (success_count, total_count, error_messages).
    """
    success_count = 0
    total_count = 0
    errors = []

    for set_ref in batch_set.eobjs:
        if not set_ref.export:
            continue

        # Find export set by name
        export_set = None
        for exp_set in mhw_data.export_sets:
            if exp_set.name == set_ref.name:
                export_set = exp_set
                break

        if not export_set:
            errors.append(f"Set '{set_ref.name}' not found")
            continue

        # Export each type if requested
        for export_mod3, export_type in [
            (batch_set.export_mod3, 'MOD3'),
            (batch_set.export_ctc, 'CTC'),
            (batch_set.export_ccl, 'CCL')
        ]:
            if not export_mod3:
                continue

            total_count += 1

            success, message = perform_export(
                export_set,
                context,
                export_type
            )

            if success:
                success_count += 1
            else:
                errors.append(f"{set_ref.name} ({export_type}): {message}")

    return success_count, total_count, errors
