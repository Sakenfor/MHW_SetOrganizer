"""
Bone and armature utilities for MHW Set Organizer.

Handles bone hierarchies, bone function IDs, mirroring, and CTC node management.
"""

from typing import List, Dict, Optional, Tuple
import bpy
from mathutils import Vector, Matrix

from .. import addon_config


def get_all_children(
    obj: bpy.types.Object,
    max_depth: int = 25,
    names_only: bool = False
) -> List:
    """
    Get all children of an object recursively.

    Args:
        obj: Parent object to start from.
        max_depth: Maximum recursion depth.
        names_only: If True, returns names instead of objects.

    Returns:
        List of child objects or names.
    """
    children = []

    def recurse(current_obj: bpy.types.Object, depth: int) -> None:
        if depth > max_depth:
            return

        children.append(current_obj.name if names_only else current_obj)

        for child in current_obj.children:
            recurse(child, depth + 1)

    recurse(obj, 0)
    return children


def get_bone_by_function_id(
    root_object: bpy.types.Object,
    bone_function_id: int
) -> Optional[bpy.types.Object]:
    """
    Find a bone (empty object) by its boneFunction custom property.

    Args:
        root_object: Root of the bone hierarchy.
        bone_function_id: The boneFunction ID to search for.

    Returns:
        Object with matching boneFunction, or None if not found.
    """
    hierarchy = get_all_children(root_object)

    for obj in hierarchy:
        if obj.get('boneFunction') == bone_function_id:
            return obj

    return None


def is_custom_bone(bone_function_id: int) -> bool:
    """
    Check if a bone function ID is in the custom/modded range.

    Args:
        bone_function_id: Bone function ID to check.

    Returns:
        True if ID >= 150 (custom range), False otherwise.
    """
    return bone_function_id >= addon_config.BONE_ID_CUSTOM_START


def find_available_bone_ids(
    used_ids: List[int],
    count: int = 1
) -> List[int]:
    """
    Find available bone function IDs in the custom range.

    Args:
        used_ids: List of already-used bone IDs.
        count: Number of free IDs to find.

    Returns:
        List of available bone IDs.
    """
    free_ids = []

    for bone_id in range(addon_config.BONE_ID_CUSTOM_START, addon_config.BONE_ID_CUSTOM_END):
        if bone_id not in used_ids:
            free_ids.append(bone_id)
            if len(free_ids) >= count:
                break

    return free_ids


def detect_bone_mirror_side(bone_location: Vector) -> str:
    """
    Detect which side (L/R) a bone is on based on X coordinate.

    Args:
        bone_location: World location of the bone.

    Returns:
        'L' for left (X > 0), 'R' for right (X < 0), '' for center.
    """
    x_coord = bone_location.x

    if x_coord > 0.001:  # Small threshold for floating point
        return 'L'
    elif x_coord < -0.001:
        return 'R'
    else:
        return ''  # Center


def find_mirror_bone(
    bone: bpy.types.Object,
    bone_locations: Dict[bpy.types.Object, Tuple[Vector, Vector]]
) -> Optional[int]:
    """
    Find the mirror bone (opposite side) for a given bone.

    Args:
        bone: Bone object to find mirror for.
        bone_locations: Dictionary mapping bones to (location, mirrored_location).

    Returns:
        boneFunction ID of mirror bone, or None if not found.
    """
    if bone not in bone_locations:
        return None

    my_location, _ = bone_locations[bone]

    # Can't mirror center bones
    if abs(my_location.x) < 0.001:
        return None

    # Find closest bone on opposite side
    mirrored_location = Vector([-my_location.x, my_location.y, my_location.z])

    closest_bone = None
    closest_distance = float('inf')

    for other_bone, (other_loc, _) in bone_locations.items():
        if other_bone == bone:
            continue

        distance = (mirrored_location - other_loc).length

        if distance < closest_distance:
            closest_distance = distance
            closest_bone = other_bone

    if closest_bone and closest_bone.get('boneFunction'):
        return closest_bone['boneFunction']

    return None


def mirror_bone_transform(
    source_bone: bpy.types.Object,
    target_bone: bpy.types.Object,
    insert_keyframe: bool = False
) -> None:
    """
    Mirror transformation from source bone to target bone (L<>R).

    Args:
        source_bone: Bone to copy transform from.
        target_bone: Bone to apply mirrored transform to.
        insert_keyframe: Whether to insert keyframes for animation.
    """
    # Get source transform
    source_matrix = source_bone.matrix_local
    source_translation = source_matrix.to_translation()
    source_rotation = source_matrix.to_euler()
    source_scale = source_matrix.to_scale()

    # Mirror translation (flip X)
    mirrored_translation = Vector([
        -source_translation.x,
        source_translation.y,
        source_translation.z
    ])

    # Mirror rotation (flip Y and Z axes)
    mirrored_rotation = [
        source_rotation.x,
        -source_rotation.y,
        -source_rotation.z
    ]

    # Apply to target
    target_bone.location = mirrored_translation
    target_bone.rotation_euler = mirrored_rotation
    target_bone.scale = source_scale

    # Insert keyframes if requested
    if insert_keyframe:
        target_bone.keyframe_insert(data_path='location')
        target_bone.keyframe_insert(data_path='rotation_euler')
        target_bone.keyframe_insert(data_path='scale')


def copy_bone_properties(source: bpy.types.Object, target: bpy.types.Object) -> None:
    """
    Copy custom properties from source bone to target bone.

    Args:
        source: Bone to copy properties from.
        target: Bone to copy properties to.
    """
    # Copy all custom properties
    for key, value in source.items():
        if key not in ['_RNA_UI']:  # Skip internal properties
            target[key] = value

    # Copy display properties
    target.empty_display_type = source.empty_display_type
    target.empty_display_size = source.empty_display_size
    target.show_axis = source.show_axis


def align_bone_constraint(bone: bpy.types.Object) -> bool:
    """
    Realign the 'Bone Function' constraint on a CTC node.

    Args:
        bone: Object with 'Bone Function' constraint.

    Returns:
        True if constraint was found and realigned, False otherwise.
    """
    constraint = bone.constraints.get('Bone Function')

    if not constraint or not bone.parent:
        return False

    # Recalculate inverse matrix
    constraint.inverse_matrix = bone.parent.matrix_world.inverted()

    # Refresh constraint
    constraint.target = constraint.target

    bpy.context.view_layer.update()

    return True


def create_bone_function_mapping(root_object: bpy.types.Object) -> Dict[int, bpy.types.Object]:
    """
    Create a mapping of bone function IDs to bone objects.

    Args:
        root_object: Root of bone hierarchy.

    Returns:
        Dictionary mapping boneFunction IDs to objects.
    """
    hierarchy = get_all_children(root_object)
    mapping = {}

    for obj in hierarchy:
        bone_func = obj.get('boneFunction')
        if bone_func is not None:
            mapping[bone_func] = obj

    return mapping


def get_bone_hierarchy_parent_map(root_object: bpy.types.Object) -> Dict[int, int]:
    """
    Create a mapping of bone IDs to their parent bone IDs.

    Args:
        root_object: Root of bone hierarchy.

    Returns:
        Dictionary mapping child boneFunction to parent boneFunction.
    """
    hierarchy = get_all_children(root_object)
    parent_map = {}

    for obj in hierarchy:
        bone_func = obj.get('boneFunction')
        if bone_func is not None and obj.parent:
            parent_func = obj.parent.get('boneFunction')
            if parent_func is not None:
                parent_map[bone_func] = parent_func
            else:
                parent_map[bone_func] = 0  # No parent bone function

    return parent_map


def validate_bone_hierarchy(root_object: bpy.types.Object) -> Tuple[bool, List[str]]:
    """
    Validate a bone hierarchy for common issues.

    Args:
        root_object: Root of bone hierarchy to validate.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []
    hierarchy = get_all_children(root_object)

    # Check for duplicate bone function IDs
    bone_functions = {}
    for obj in hierarchy:
        bone_func = obj.get('boneFunction')
        if bone_func is not None:
            if bone_func in bone_functions:
                errors.append(
                    f"Duplicate boneFunction {bone_func}: "
                    f"{bone_functions[bone_func].name} and {obj.name}"
                )
            else:
                bone_functions[bone_func] = obj

    # Check for broken constraints
    for obj in hierarchy:
        if obj.get('Type') == addon_config.TYPE_CTC_NODE:
            constraint = obj.constraints.get('Bone Function')
            if constraint and not constraint.target:
                errors.append(f"Node {obj.name} has Bone Function constraint with no target")

    # Check for orphaned nodes
    for obj in hierarchy:
        if not obj.parent and obj != root_object:
            errors.append(f"Orphaned object {obj.name} in hierarchy")

    return (len(errors) == 0, errors)
