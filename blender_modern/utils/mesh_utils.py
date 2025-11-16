"""
Mesh manipulation utilities for MHW Set Organizer.

Handles mesh operations like triangulation, normal transfer, and vertex group management.
"""

from typing import Optional, List
import bmesh
import bpy
from mathutils import Vector


def triangulate_mesh(mesh_object: bpy.types.Object, preserve_original: bool = True) -> Optional[bpy.types.Mesh]:
    """
    Create a triangulated version of a mesh.

    Args:
        mesh_object: Object with mesh data to triangulate.
        preserve_original: If True, creates a copy. If False, modifies in place.

    Returns:
        Triangulated mesh data, or None on error.

    Example:
        >>> tri_mesh = triangulate_mesh(my_object, preserve_original=True)
        >>> temp_obj.data = tri_mesh
    """
    if mesh_object.type != 'MESH':
        return None

    # Create copy if preserving original
    if preserve_original:
        mesh_data = mesh_object.data.copy()
    else:
        mesh_data = mesh_object.data

    # Triangulate using bmesh
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh_data)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh_data)
        mesh_data.update(calc_edges=True)
    finally:
        bm.free()

    return mesh_data


def transfer_normals(
    source: bpy.types.Object,
    target: bpy.types.Object,
    method: str = 'TRANSFER'
) -> bool:
    """
    Transfer custom normals from source to target mesh.

    Args:
        source: Object to copy normals from.
        target: Object to apply normals to.
        method: Transfer method - 'TRANSFER' or 'DIRECTIONAL'.

    Returns:
        True if successful, False otherwise.
    """
    if source.type != 'MESH' or target.type != 'MESH':
        return False

    # Ensure we're in object mode
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Create appropriate modifier
    modifier_name = 'MHW_NormalTransfer'

    # Remove existing modifier if present
    if modifier_name in target.modifiers:
        target.modifiers.remove(target.modifiers[modifier_name])

    if method == 'DIRECTIONAL':
        mod = target.modifiers.new(modifier_name, "NORMAL_EDIT")
        mod.target = source
        mod.mode = 'DIRECTIONAL'
        mod.use_direction_parallel = True
    else:  # TRANSFER
        mod = target.modifiers.new(modifier_name, "DATA_TRANSFER")
        mod.use_loop_data = True
        mod.loop_mapping = "NEAREST_POLYNOR"
        mod.data_types_loops = {'CUSTOM_NORMAL'}
        mod.object = source

    # Select only target for applying
    bpy.ops.object.select_all(action='DESELECT')
    target.select_set(True)
    bpy.context.view_layer.objects.active = target

    # Apply modifier
    try:
        # Use override for Blender 3.x+ compatibility
        with bpy.context.temp_override(object=target):
            bpy.ops.object.modifier_apply(modifier=modifier_name)
        return True
    except Exception as e:
        print(f"Error applying normal transfer: {e}")
        return False


def transfer_weights(
    source: bpy.types.Object,
    target: bpy.types.Object,
    vertex_mapping: str = 'POLYINTERP_NEAREST',
    vertex_group_filter: Optional[str] = None
) -> bool:
    """
    Transfer vertex weights from source to target mesh.

    Args:
        source: Object to copy weights from.
        target: Object to apply weights to.
        vertex_mapping: Method for mapping vertices (NEAREST, TOPOLOGY, etc.).
        vertex_group_filter: Optional vertex group name to limit transfer.

    Returns:
        True if successful, False otherwise.
    """
    if source.type != 'MESH' or target.type != 'MESH':
        return False

    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    modifier_name = f'MHW_WeightTransfer_{source.name}'

    # Remove existing modifier if present
    if modifier_name in target.modifiers:
        target.modifiers.remove(target.modifiers[modifier_name])

    # Create data transfer modifier
    mod = target.modifiers.new(modifier_name, type='DATA_TRANSFER')
    mod.use_vert_data = True
    mod.data_types_verts = {'VGROUP_WEIGHTS'}
    mod.vert_mapping = vertex_mapping
    mod.object = source

    if vertex_group_filter:
        mod.vertex_group = vertex_group_filter

    # Apply modifier
    bpy.context.view_layer.objects.active = target
    target.select_set(True)

    try:
        with bpy.context.temp_override(object=target):
            bpy.ops.object.modifier_apply(modifier=modifier_name)
        return True
    except Exception as e:
        print(f"Error transferring weights: {e}")
        return False


def remove_unused_vertex_groups(mesh_object: bpy.types.Object) -> int:
    """
    Remove vertex groups that have no vertices with weight > 0.

    Args:
        mesh_object: Object to clean vertex groups from.

    Returns:
        Number of vertex groups removed.
    """
    if mesh_object.type != 'MESH':
        return 0

    # Check which groups are actually used
    groups_used = {i: False for i in range(len(mesh_object.vertex_groups))}

    for vertex in mesh_object.data.vertices:
        for group in vertex.groups:
            if group.weight > 0.0:
                groups_used[group.group] = True

    # Remove unused groups (iterate in reverse to avoid index issues)
    removed_count = 0
    for group_index in sorted(groups_used.keys(), reverse=True):
        if not groups_used[group_index]:
            try:
                mesh_object.vertex_groups.remove(
                    mesh_object.vertex_groups[group_index]
                )
                removed_count += 1
            except (IndexError, RuntimeError):
                pass

    return removed_count


def clean_vertex_weights(
    mesh_object: bpy.types.Object,
    limit_total: Optional[int] = None,
    clean_threshold: float = 0.0,
    normalize: bool = True,
    smooth_iterations: int = 0,
    smooth_factor: float = 0.5
) -> bool:
    """
    Clean and normalize vertex weights on a mesh.

    Args:
        mesh_object: Object to clean weights on.
        limit_total: Maximum number of weights per vertex (None = no limit).
        clean_threshold: Remove weights below this value.
        normalize: Whether to normalize all weights.
        smooth_iterations: Number of smoothing passes (0 = no smoothing).
        smooth_factor: Smoothing strength (0.0 to 1.0).

    Returns:
        True if successful, False otherwise.
    """
    if mesh_object.type != 'MESH':
        return False

    # Set up context
    bpy.ops.object.select_all(action='DESELECT')
    mesh_object.select_set(True)
    bpy.context.view_layer.objects.active = mesh_object

    try:
        # Enter edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')

        # Limit total weights per vertex
        if limit_total:
            bpy.ops.object.vertex_group_limit_total(limit=limit_total)

        # Smooth weights
        if smooth_iterations > 0:
            bpy.ops.object.vertex_group_smooth(
                group_select_mode='ALL',
                factor=smooth_factor,
                repeat=smooth_iterations
            )
            # Re-apply limit after smoothing
            if limit_total:
                bpy.ops.object.vertex_group_limit_total(limit=limit_total)

        # Clean low-weight vertices
        if clean_threshold > 0:
            bpy.ops.object.vertex_group_clean(
                group_select_mode='ALL',
                limit=clean_threshold
            )

        # Normalize weights
        if normalize:
            bpy.ops.object.vertex_group_normalize_all(lock_active=False)

        # Deselect and return to object mode
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        return True

    except Exception as e:
        print(f"Error cleaning vertex weights: {e}")
        # Ensure we return to object mode
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        return False


def get_vertices_by_bmesh_layer(
    mesh_object: bpy.types.Object,
    layer_name: str
) -> List[int]:
    """
    Get vertex indices that have a specific BMesh integer layer set to 1.

    This is used for tag-based weight transfer.

    Args:
        mesh_object: Mesh object to query.
        layer_name: Name of the integer layer (tag name).

    Returns:
        List of vertex indices with the tag.
    """
    if mesh_object.type != 'MESH':
        return []

    # Must be in edit mode to access BMesh
    current_mode = bpy.context.mode
    if current_mode != 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='EDIT')

    mesh_data = mesh_object.data
    bm = bmesh.from_edit_mesh(mesh_data)
    bm.verts.ensure_lookup_table()

    # Check if layer exists
    if layer_name not in bm.verts.layers.int:
        if current_mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='OBJECT')
        return []

    # Get vertices with tag set to 1
    layer = bm.verts.layers.int[layer_name]
    tagged_verts = [
        vert.index for vert in bm.verts
        if vert[layer] == 1
    ]

    # Return to original mode
    if current_mode != 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='OBJECT')

    return tagged_verts


def create_vertex_group_from_bmesh_tag(
    mesh_object: bpy.types.Object,
    tag_name: str,
    group_name: Optional[str] = None
) -> Optional[bpy.types.VertexGroup]:
    """
    Create a vertex group from vertices tagged in BMesh layer.

    Args:
        mesh_object: Object to add vertex group to.
        tag_name: BMesh layer name (tag).
        group_name: Name for vertex group (defaults to tag_name).

    Returns:
        Created vertex group, or None if tag not found.
    """
    if mesh_object.type != 'MESH':
        return None

    vertex_indices = get_vertices_by_bmesh_layer(mesh_object, tag_name)

    if not vertex_indices:
        return None

    group_name = group_name or f'tag_{tag_name}'

    # Remove existing group if present
    if group_name in mesh_object.vertex_groups:
        mesh_object.vertex_groups.remove(mesh_object.vertex_groups[group_name])

    # Create new group
    vgroup = mesh_object.vertex_groups.new(name=group_name)

    # Add vertices
    for vert_index in vertex_indices:
        vgroup.add([vert_index], 1.0, 'ADD')

    return vgroup
