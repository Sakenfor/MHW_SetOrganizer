"""
Weight transfer logic for MHW Set Organizer.

Handles transferring vertex weights between meshes, including
tag-based transfer and weight cleaning operations.
"""

from typing import List, Dict, Optional, Set
import bmesh
import bpy

from .. import addon_config
from ..utils import mesh_utils, bone_utils


def get_tagged_objects(
    export_set,
    tag_name: str
) -> List:
    """
    Get objects with a specific tag from an export set.

    Args:
        export_set: Export set property group.
        tag_name: Tag to search for.

    Returns:
        List of object entries that have the tag.
    """
    tagged = []

    for obj_entry in export_set.eobjs:
        if not obj_entry.obje or not obj_entry.tag:
            continue

        # Tags are comma-separated
        tags = [t.strip() for t in obj_entry.tag.split(',') if t.strip()]

        if tag_name in tags:
            tagged.append(obj_entry)

    return tagged


def build_tag_dictionary(
    source_set,
    target_set
) -> Dict[str, Dict[str, List]]:
    """
    Build a dictionary of source and target objects for each tag.

    Args:
        source_set: Source export set.
        target_set: Target export set.

    Returns:
        Dictionary mapping tag names to {'Source': [...], 'Target': [...]}.
    """
    tag_dict = {}

    # Get tags from both sets
    all_tags = set()

    for obj_entry in source_set.eobjs:
        if obj_entry.tag:
            tags = [t.strip() for t in obj_entry.tag.split(',') if t.strip()]
            all_tags.update(tags)

    for obj_entry in target_set.eobjs:
        if obj_entry.tag:
            tags = [t.strip() for t in obj_entry.tag.split(',') if t.strip()]
            all_tags.update(tags)

    # Build dictionary
    for tag in all_tags:
        tag_dict[tag] = {
            'Source': get_tagged_objects(source_set, tag),
            'Target': get_tagged_objects(target_set, tag)
        }

    return tag_dict


def create_weight_transfer_copy(
    source_obj: bpy.types.Object,
    bone_mapping: Dict[str, bpy.types.Object],
    material_filter: Optional[List] = None,
    scene: Optional[bpy.types.Scene] = None
) -> Optional[bpy.types.Object]:
    """
    Create a copy of source object with remapped bone names for weight transfer.

    Args:
        source_obj: Source mesh object.
        bone_mapping: Dictionary mapping source bone names to target bones.
        material_filter: List of materials to include (None = all).
        scene: Scene to link copy to.

    Returns:
        Temporary copy object with remapped vertex groups, or None on error.
    """
    if not scene:
        scene = bpy.context.scene

    # Create copy
    copy_obj = source_obj.copy()
    copy_mesh = source_obj.data.copy()
    copy_obj.data = copy_mesh

    scene.collection.objects.link(copy_obj)
    bpy.context.view_layer.update()

    # Filter by materials if requested
    if material_filter:
        # Get material indices to keep
        keep_indices = []
        for i, slot in enumerate(source_obj.material_slots):
            if slot.material in material_filter:
                keep_indices.append(i)

        # Delete faces with other materials
        if keep_indices:
            bm = bmesh.new()
            bm.from_mesh(copy_mesh)

            faces_to_delete = [
                face for face in bm.faces
                if face.material_index not in keep_indices
            ]

            bmesh.ops.delete(bm, geom=faces_to_delete, context='FACES')
            bm.to_mesh(copy_mesh)
            bm.free()

    # Remap vertex group names
    groups_to_remove = []

    for vgroup in copy_obj.vertex_groups:
        # Check if this bone name is in the mapping
        if vgroup.name in bone_mapping:
            target_bone = bone_mapping[vgroup.name]
            vgroup.name = target_bone.name
        else:
            # No mapping found, mark for removal
            groups_to_remove.append(vgroup.name)

    # Remove unmapped groups
    for group_name in groups_to_remove:
        if group_name in copy_obj.vertex_groups:
            copy_obj.vertex_groups.remove(copy_obj.vertex_groups[group_name])

    return copy_obj


def transfer_weights_by_tag(
    source_set,
    target_set,
    ctc_organizer,
    bone_mapping: Dict[str, bpy.types.Object],
    scene: bpy.types.Scene
) -> Dict[str, int]:
    """
    Transfer weights between objects based on tags.

    Args:
        source_set: Source export set.
        target_set: Target export set.
        ctc_organizer: CTC organizer with transfer settings.
        bone_mapping: Dictionary mapping source bone names to target bones.
        scene: Current scene.

    Returns:
        Dictionary of stats: {'transferred': count, 'cleaned': count}.
    """
    stats = {'transferred': 0, 'cleaned': 0}

    # Build tag dictionary
    tag_dict = build_tag_dictionary(source_set, target_set)

    # Filter bone mapping by weight limit setting
    filtered_mapping = {}
    for source_name, target_bone in bone_mapping.items():
        bone_id = target_bone.get('boneFunction', 0)

        if ctc_organizer.weight_limit == 'ALL':
            filtered_mapping[source_name] = target_bone
        elif ctc_organizer.weight_limit == 'BELOW_150':
            if bone_id < addon_config.BONE_ID_CUSTOM_START:
                filtered_mapping[source_name] = target_bone
        elif ctc_organizer.weight_limit == 'ABOVE_150':
            if bone_id >= addon_config.BONE_ID_CUSTOM_START:
                filtered_mapping[source_name] = target_bone

    # Process each tag
    for tag_name, tag_objects in tag_dict.items():
        sources = tag_objects['Source']
        targets = tag_objects['Target']

        if not sources or not targets:
            continue

        # Process each source object
        for source_entry in sources:
            source_obj = source_entry.obje

            # Build material filter if configured
            material_filter = None
            material_choices = [
                mc for mc in ctc_organizer.material_choices
                if mc.obje == source_obj and mc.toggle
            ]
            if material_choices:
                material_filter = [mc.mate for mc in material_choices]

            # Create temporary copy with remapped bones
            temp_copy = create_weight_transfer_copy(
                source_obj,
                filtered_mapping,
                material_filter,
                scene
            )

            if not temp_copy:
                continue

            # Transfer to each target
            for target_entry in targets:
                target_obj = target_entry.obje

                # Skip if target doesn't accept transfer
                if not target_entry.accept_weight_transfer:
                    continue

                # Check if we should use tag-based vertex selection
                use_tag = tag_name in [
                    t.strip() for t in target_entry.tag.split(',')
                    if t.strip()
                ]

                # Create vertex group from tag if needed
                if use_tag and target_entry.tags.get(tag_name):
                    if target_entry.tags[tag_name].use:
                        # Tag-based transfer
                        temp_vgroup = mesh_utils.create_vertex_group_from_bmesh_tag(
                            target_obj,
                            tag_name
                        )

                        if temp_vgroup:
                            # Transfer only to tagged vertices
                            mesh_utils.transfer_weights(
                                temp_copy,
                                target_obj,
                                vertex_mapping='POLYINTERP_NEAREST',
                                vertex_group_filter=temp_vgroup.name
                            )

                            # Remove temporary vertex group
                            target_obj.vertex_groups.remove(temp_vgroup)
                        else:
                            # No tagged vertices, skip
                            continue
                else:
                    # Transfer to all vertices
                    mesh_utils.transfer_weights(
                        temp_copy,
                        target_obj,
                        vertex_mapping='POLYINTERP_NEAREST'
                    )

                stats['transferred'] += 1

                # Clean weights if requested
                if target_entry.accept_weight_smoothing:
                    mesh_utils.clean_vertex_weights(
                        target_obj,
                        limit_total=4 if ctc_organizer.limit_after else None,
                        clean_threshold=0.0 if ctc_organizer.clean_after else -1.0,
                        normalize=ctc_organizer.normalize_after,
                        smooth_iterations=ctc_organizer.smooth_count if ctc_organizer.smooth_after else 0,
                        smooth_factor=ctc_organizer.smooth_strength
                    )

                    stats['cleaned'] += 1

            # Remove temporary copy
            bpy.data.objects.remove(temp_copy)
            if temp_copy.data:
                bpy.data.meshes.remove(temp_copy.data)

    # Remove vertex groups not found in bone hierarchy
    if ctc_organizer.remove_vg_not_found:
        target_bone_names = set(bone_mapping.values())

        for target_entry in target_set.eobjs:
            if not target_entry.obje:
                continue

            groups_to_remove = []
            for vgroup in target_entry.obje.vertex_groups:
                # Check if group name matches any target bone
                if not any(bone.name == vgroup.name for bone in target_bone_names):
                    groups_to_remove.append(vgroup)

            for vgroup in groups_to_remove:
                target_entry.obje.vertex_groups.remove(vgroup)

    return stats


def remove_vertex_groups_before_transfer(
    target_objects: List,
    bone_mapping: Dict[str, bpy.types.Object],
    remove_range: str = 'ALL'
) -> int:
    """
    Remove vertex groups before weight transfer for cleaner results.

    Args:
        target_objects: List of target object entries.
        bone_mapping: Bone name mapping.
        remove_range: Which groups to remove ('ALL', 'BELOW_150', 'ABOVE_150').

    Returns:
        Number of groups removed.
    """
    removed_count = 0

    for obj_entry in target_objects:
        if not obj_entry.obje:
            continue

        obj = obj_entry.obje
        groups_to_remove = []

        for vgroup in obj.vertex_groups:
            # Find matching bone
            matching_bone = None
            for bone in bone_mapping.values():
                if bone.name == vgroup.name:
                    matching_bone = bone
                    break

            if not matching_bone:
                continue

            bone_id = matching_bone.get('boneFunction', 0)

            # Check if should be removed
            should_remove = False
            if remove_range == 'ALL':
                should_remove = True
            elif remove_range == 'BELOW_150':
                should_remove = bone_id < addon_config.BONE_ID_CUSTOM_START
            elif remove_range == 'ABOVE_150':
                should_remove = bone_id >= addon_config.BONE_ID_CUSTOM_START

            if should_remove:
                groups_to_remove.append(vgroup)

        # Remove groups
        for vgroup in groups_to_remove:
            obj.vertex_groups.remove(vgroup)
            removed_count += 1

    return removed_count


def build_bone_name_mapping(
    source_root: bpy.types.Object,
    target_root: bpy.types.Object,
    bone_id_changes: Optional[Dict[int, int]] = None
) -> Dict[str, bpy.types.Object]:
    """
    Build mapping from source bone names to target bone objects.

    Args:
        source_root: Source bone hierarchy root.
        target_root: Target bone hierarchy root.
        bone_id_changes: Optional dict of bone ID changes (old_id -> new_id).

    Returns:
        Dictionary mapping source bone names to target bone objects.
    """
    if bone_id_changes is None:
        bone_id_changes = {}

    # Get bone hierarchies
    source_bones = bone_utils.get_all_children(source_root)
    target_bones = bone_utils.get_all_children(target_root)

    # Build target bone lookup by function ID
    target_by_id = {}
    for bone in target_bones:
        bone_id = bone.get('boneFunction')
        if bone_id is not None:
            target_by_id[bone_id] = bone

    # Build name mapping
    mapping = {}

    for source_bone in source_bones:
        source_id = source_bone.get('boneFunction')
        if source_id is None:
            continue

        # Check if ID was changed
        target_id = bone_id_changes.get(source_id, source_id)

        # Find target bone
        target_bone = target_by_id.get(target_id)
        if target_bone:
            mapping[source_bone.name] = target_bone

    return mapping
