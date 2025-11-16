"""
Import logic for MHW Set Organizer.

Handles importing MOD3, CTC, and CCL files using external import operators.
This module provides a clean interface to the external MHW importers.
"""

from typing import Tuple, Optional, Set, List
import os
import bpy

from .. import addon_config


def check_external_importer_available(file_type: str) -> Tuple[bool, str]:
    """
    Check if the external importer operator is available.

    Args:
        file_type: Type of file ('MOD3', 'CTC', or 'CCL').

    Returns:
        Tuple of (is_available, operator_id or error_message).
    """
    operator_map = {
        'MOD3': 'custom_import.import_mhw_mod3',
        'CTC': 'custom_import.import_mhw_ctc',
        'CCL': 'custom_import.import_mhw_ccl',
    }

    operator_id = operator_map.get(file_type)
    if not operator_id:
        return False, f"Unknown file type: {file_type}"

    # Check if operator exists
    try:
        # Split operator_id into module and name
        parts = operator_id.split('.')
        if len(parts) != 2:
            return False, f"Invalid operator ID: {operator_id}"

        module, name = parts
        op = getattr(bpy.ops, module, None)
        if op is None:
            return False, f"Operator module '{module}' not found. Is the MHW importer addon installed?"

        if not hasattr(op, name):
            return False, f"Operator '{operator_id}' not found. Is the MHW importer addon installed?"

        return True, operator_id

    except Exception as e:
        return False, f"Error checking for operator: {e}"


def construct_import_path(
    export_set,
    file_type: str
) -> Tuple[bool, str]:
    """
    Construct the import file path from export set settings.

    Args:
        export_set: Export set property group.
        file_type: Type of file ('MOD3', 'CTC', or 'CCL').

    Returns:
        Tuple of (success, path or error_message).
    """
    extension_map = {
        'MOD3': '.mod3',
        'CTC': '.ctc',
        'CCL': '.ccl',
    }

    extension = extension_map.get(file_type)
    if not extension:
        return False, f"Unknown file type: {file_type}"

    # Use import_path if set, otherwise use export_path
    base_path = export_set.import_path if export_set.import_path else export_set.export_path

    if not base_path:
        return False, "No import or export path configured"

    # Add extension if not already present
    if not base_path.endswith(extension):
        file_path = base_path + extension
    else:
        file_path = base_path

    return True, file_path


def import_mod3(
    export_set,
    context: bpy.types.Context,
    file_path: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Import MOD3 file using external importer.

    Args:
        export_set: Export set with import settings.
        context: Blender context.
        file_path: Optional override path (uses export_set path if None).

    Returns:
        Tuple of (success, error_message).
    """
    # Check if external importer is available
    is_available, result = check_external_importer_available('MOD3')
    if not is_available:
        return False, result

    # Construct file path if not provided
    if file_path is None:
        success, path_or_error = construct_import_path(export_set, 'MOD3')
        if not success:
            return False, path_or_error
        file_path = path_or_error

    # Check if file exists
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"

    # Set render engine to Cycles (required by importer)
    original_engine = context.scene.render.engine
    context.scene.render.engine = 'CYCLES'

    try:
        # Call external import operator
        result = bpy.ops.custom_import.import_mhw_mod3(
            filepath=file_path,
            clear_scene=export_set.clear_scene,
            maximize_clipping=export_set.maximize_clipping,
            high_lod=export_set.high_lod,
            import_header=export_set.import_header,
            import_meshparts=export_set.import_meshparts,
            import_textures=export_set.import_textures,
            import_materials=export_set.import_materials,
            load_group_functions=export_set.load_group_functions,
            texture_path=export_set.texture_path,
            import_skeleton=export_set.import_skeleton,
            weight_format=export_set.weight_format,
        )

        if result == {'FINISHED'}:
            return True, f"Successfully imported: {file_path}"
        else:
            return False, f"Import operator returned: {result}"

    except Exception as e:
        return False, f"Error during import: {e}"

    finally:
        # Restore original render engine
        context.scene.render.engine = original_engine


def import_ctc(
    export_set,
    context: bpy.types.Context,
    file_path: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Import CTC file using external importer.

    Args:
        export_set: Export set with import settings.
        context: Blender context.
        file_path: Optional override path (uses export_set path if None).

    Returns:
        Tuple of (success, error_message).
    """
    # Check if external importer is available
    is_available, result = check_external_importer_available('CTC')
    if not is_available:
        return False, result

    # Construct file path if not provided
    if file_path is None:
        success, path_or_error = construct_import_path(export_set, 'CTC')
        if not success:
            return False, path_or_error
        file_path = path_or_error

    # Check if file exists
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"

    try:
        # Call external import operator
        result = bpy.ops.custom_import.import_mhw_ctc(
            filepath=file_path,
            missingFunctionBehaviour=export_set.ctc_missing_function_behaviour
        )

        if result == {'FINISHED'}:
            return True, f"Successfully imported: {file_path}"
        else:
            return False, f"Import operator returned: {result}"

    except Exception as e:
        return False, f"Error during import: {e}"


def import_ccl(
    export_set,
    context: bpy.types.Context,
    file_path: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Import CCL file using external importer.

    Args:
        export_set: Export set with import settings.
        context: Blender context.
        file_path: Optional override path (uses export_set path if None).

    Returns:
        Tuple of (success, error_message).
    """
    # Check if external importer is available
    is_available, result = check_external_importer_available('CCL')
    if not is_available:
        return False, result

    # Construct file path if not provided
    if file_path is None:
        success, path_or_error = construct_import_path(export_set, 'CCL')
        if not success:
            return False, path_or_error
        file_path = path_or_error

    # Check if file exists
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"

    try:
        # Call external import operator
        result = bpy.ops.custom_import.import_mhw_ccl(
            filepath=file_path,
            missingFunctionBehaviour=export_set.ccl_missing_function_behaviour,
            scale=export_set.ccl_scale
        )

        if result == {'FINISHED'}:
            return True, f"Successfully imported: {file_path}"
        else:
            return False, f"Import operator returned: {result}"

    except Exception as e:
        return False, f"Error during import: {e}"


def perform_import(
    export_set,
    context: bpy.types.Context,
    import_type: str,
    file_path: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Main import function that routes to appropriate importer.

    Args:
        export_set: Export set with import settings.
        context: Blender context.
        import_type: Type of import ('MOD3', 'CTC', or 'CCL').
        file_path: Optional override path.

    Returns:
        Tuple of (success, error_message).
    """
    import_functions = {
        'MOD3': import_mod3,
        'CTC': import_ctc,
        'CCL': import_ccl,
    }

    import_func = import_functions.get(import_type)
    if not import_func:
        return False, f"Unknown import type: {import_type}"

    return import_func(export_set, context, file_path)


def post_import_processing(
    export_set,
    context: bpy.types.Context,
    import_type: str,
    add_to_export_set: bool = True
) -> Tuple[bool, str]:
    """
    Post-process imported objects (add to export set, validate, etc.).

    Args:
        export_set: Export set to add objects to.
        context: Blender context.
        import_type: Type of import that was performed.
        add_to_export_set: Whether to add imported objects to export set.

    Returns:
        Tuple of (success, error_message).
    """
    if not add_to_export_set:
        return True, "No post-processing requested"

    # Get newly imported objects (they will be selected)
    imported_objects = [obj for obj in context.selected_objects]

    if not imported_objects:
        return True, "No objects imported or selected"

    # Add objects to export set based on type
    added_count = 0

    for obj in imported_objects:
        # Check if object is already in export set
        already_exists = any(
            entry.obje == obj
            for entry in export_set.eobjs
        )

        if already_exists:
            continue

        # Determine if object should be added based on type
        should_add = False

        if import_type == 'MOD3':
            # Add mesh objects and skeleton roots
            if obj.type == 'MESH':
                should_add = True
            elif obj.type == 'EMPTY' and obj.get('TYPE') == addon_config.TYPE_SKELETON_ROOT:
                should_add = True
                # Set as root if not already set
                if export_set.empty_root is None:
                    export_set.empty_root = obj

        elif import_type == 'CTC':
            # Add CTC headers and chains
            if obj.type == 'EMPTY':
                obj_type = obj.get('TYPE')
                if obj_type in [addon_config.TYPE_CTC_HEADER, addon_config.TYPE_CTC_CHAIN]:
                    should_add = True

                # Set CTC header if not already set
                if obj_type == addon_config.TYPE_CTC_HEADER and export_set.ctc_header is None:
                    export_set.ctc_header = obj

        elif import_type == 'CCL':
            # Add CCL objects
            if obj.type == 'EMPTY' and obj.get('TYPE') == addon_config.TYPE_CCL:
                should_add = True

        if should_add:
            entry = export_set.eobjs.add()
            entry.obje = obj
            entry.export = True
            added_count += 1

    return True, f"Added {added_count} imported objects to export set"


def batch_import(
    export_sets: List,
    context: bpy.types.Context,
    import_type: str,
    add_to_export_sets: bool = True
) -> Tuple[bool, str]:
    """
    Import files for multiple export sets.

    Args:
        export_sets: List of export sets to import.
        context: Blender context.
        import_type: Type of import ('MOD3', 'CTC', or 'CCL').
        add_to_export_sets: Whether to add imported objects to export sets.

    Returns:
        Tuple of (success, summary_message).
    """
    success_count = 0
    error_count = 0
    errors = []

    for export_set in export_sets:
        # Perform import
        success, message = perform_import(export_set, context, import_type)

        if success:
            success_count += 1

            # Post-process if requested
            if add_to_export_sets:
                post_import_processing(export_set, context, import_type, True)
        else:
            error_count += 1
            errors.append(f"{export_set.name}: {message}")

    # Build summary message
    summary = f"Import completed: {success_count} succeeded, {error_count} failed"
    if errors:
        summary += "\n\nErrors:\n" + "\n".join(errors)

    return error_count == 0, summary
