"""
Validation utilities for MHW Set Organizer.

Provides input validation and error checking functions.
"""

from typing import Optional, Tuple
import bpy

from .. import addon_config


def validate_mesh_object(obj: Optional[bpy.types.Object]) -> Tuple[bool, str]:
    """
    Validate that an object is a valid mesh.

    Args:
        obj: Object to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if obj is None:
        return False, "No object provided"

    if obj.type != 'MESH':
        return False, f"Object '{obj.name}' is not a mesh (type: {obj.type})"

    if obj.data is None:
        return False, f"Object '{obj.name}' has no mesh data"

    return True, ""


def validate_armature_root(obj: Optional[bpy.types.Object]) -> Tuple[bool, str]:
    """
    Validate that an object can serve as an armature root.

    Args:
        obj: Object to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if obj is None:
        return False, "No root object provided"

    if obj.parent is not None:
        return False, f"Object '{obj.name}' has a parent (roots must be parentless)"

    if obj.type != 'EMPTY':
        return False, f"Root object '{obj.name}' must be an Empty (is {obj.type})"

    # Check it's not a CTC header
    if obj.get('Type') == addon_config.TYPE_CTC_HEADER:
        return False, f"Object '{obj.name}' is a CTC header, not a bone root"

    return True, ""


def validate_ctc_header(obj: Optional[bpy.types.Object]) -> Tuple[bool, str]:
    """
    Validate that an object is a valid CTC header.

    Args:
        obj: Object to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if obj is None:
        return False, "No CTC header provided"

    obj_type = obj.get('Type')
    if obj_type != addon_config.TYPE_CTC_HEADER:
        return False, f"Object '{obj.name}' is not a CTC header (Type: {obj_type})"

    return True, ""


def validate_export_set(export_set) -> Tuple[bool, list]:
    """
    Validate an export set for common issues before export.

    Args:
        export_set: Export set property group to validate.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []

    # Check armor name is set
    if not export_set.armor_name:
        errors.append("No armor name selected")

    # Check armor part is set
    if not export_set.armor_part:
        errors.append("No armor part selected")

    # Check root object is valid
    if export_set.empty_root:
        is_valid, error = validate_armature_root(export_set.empty_root)
        if not is_valid:
            errors.append(f"Invalid root: {error}")
    else:
        errors.append("No root object assigned")

    # Check for exportable objects
    valid_objects = [
        obj for obj in export_set.eobjs
        if obj.export and obj.obje is not None
    ]

    if not valid_objects:
        errors.append("No objects marked for export")

    # Validate each object
    for obj_entry in valid_objects:
        obj = obj_entry.obje
        is_valid, error = validate_mesh_object(obj)
        if not is_valid:
            errors.append(f"Object validation failed: {error}")

    return (len(errors) == 0, errors)


def validate_weight_transfer_setup(
    source: bpy.types.Object,
    target: bpy.types.Object
) -> Tuple[bool, str]:
    """
    Validate that two objects are suitable for weight transfer.

    Args:
        source: Source object for weight transfer.
        target: Target object for weight transfer.

    Returns:
        Tuple of (is_valid, error_message).
    """
    # Validate source
    is_valid, error = validate_mesh_object(source)
    if not is_valid:
        return False, f"Invalid source: {error}"

    # Validate target
    is_valid, error = validate_mesh_object(target)
    if not is_valid:
        return False, f"Invalid target: {error}"

    # Check source has vertex groups
    if len(source.vertex_groups) == 0:
        return False, f"Source object '{source.name}' has no vertex groups"

    return True, ""


def check_blender_version_compatibility() -> Tuple[bool, str]:
    """
    Check if current Blender version is compatible with this addon.

    Returns:
        Tuple of (is_compatible, version_message).
    """
    current_version = bpy.app.version
    min_version = addon_config.BLENDER_VERSION_MIN

    if current_version < min_version:
        return False, (
            f"Blender {'.'.join(map(str, min_version))}+ required, "
            f"but you have {'.'.join(map(str, current_version))}"
        )

    return True, f"Blender {'.'.join(map(str, current_version))}"


def validate_armor_name(armor_name: str, armor_database: dict) -> Tuple[bool, str]:
    """
    Validate that an armor name exists in the database.

    Args:
        armor_name: Armor name to validate.
        armor_database: Dictionary of valid armor names/IDs.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not armor_name:
        return False, "No armor name provided"

    if armor_name not in armor_database:
        return False, f"Armor '{armor_name}' not found in database"

    return True, ""


def validate_file_path(file_path: str, must_exist: bool = False) -> Tuple[bool, str]:
    """
    Validate a file path.

    Args:
        file_path: Path to validate.
        must_exist: Whether the path must already exist.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not file_path:
        return False, "No path provided"

    if must_exist:
        import os
        if not os.path.exists(file_path):
            return False, f"Path does not exist: {file_path}"

    return True, ""
