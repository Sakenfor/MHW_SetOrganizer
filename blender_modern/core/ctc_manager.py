"""
CTC (Cloth Physics) manager for MHW Set Organizer.

Handles copying CTC hierarchies from source to target, including:
- CTC headers, chains, frames, and nodes
- Bone hierarchies with ID remapping
- Weight transfer between meshes
- Mirror bone pairing
"""

from typing import Dict, List, Tuple, Optional, Set
import re
import bpy
from mathutils import Vector, Matrix

from .. import addon_config
from ..utils import bone_utils, mesh_utils


class CTCObjectTracker:
    """
    Tracks copied CTC objects and their relationships.

    This replaces the legacy ctcO class with a cleaner implementation.
    """

    def __init__(
        self,
        source: bpy.types.Object,
        target: Optional[bpy.types.Object],
        object_type: str,
        bone_id: int = 0,
        changed_id: int = 0
    ):
        self.source = source
        self.target = target
        self.object_type = object_type  # 'Bone', 'Header', 'Frame', 'Chain', 'Node'
        self.bone_id = bone_id
        self.changed_id = changed_id
        self.pair = None  # For mirror bone pairs

    def __repr__(self):
        return f"CTCObjectTracker({self.object_type}, {self.source.name} -> {self.target.name if self.target else 'None'})"


def get_object_type(obj: bpy.types.Object) -> str:
    """
    Determine the CTC object type from object properties.

    Args:
        obj: Object to check.

    Returns:
        Object type string ('Bone', 'Header', 'Frame', 'Chain', or 'Node').
    """
    obj_type = obj.get('TYPE') or obj.get('Type')

    if not obj_type:
        return 'Bone'

    # Map legacy type names to modern
    type_map = {
        addon_config.TYPE_CTC_HEADER: 'Header',
        'CTC': 'Header',
        addon_config.TYPE_CTC_CHAIN: 'Chain',
        addon_config.TYPE_CTC_FRAME: 'Frame',
        'CTC_*_Frame': 'Frame',
        addon_config.TYPE_CTC_NODE: 'Node',
        'CTC_Node': 'Node',
    }

    return type_map.get(obj_type, 'Bone')


def find_ctc_source_root(
    ctc_objects: List[bpy.types.Object]
) -> Optional[bpy.types.Object]:
    """
    Find the bone hierarchy root from CTC objects.

    Args:
        ctc_objects: List of CTC source objects.

    Returns:
        Root bone object, or None if not found.
    """
    for obj in ctc_objects:
        # Check if object has bone function constraint
        bone_func_con = obj.constraints.get('Bone Function')
        if not bone_func_con or not bone_func_con.target:
            continue

        # Walk up the hierarchy
        root = bone_func_con.target
        hierarchy = []

        while root is not None:
            hierarchy.append(root)
            root = root.parent

        # Root is second from top (top is usually scene root)
        if len(hierarchy) >= 2:
            return hierarchy[-2]

    return None


def find_free_bone_ids(
    existing_bones: List[bpy.types.Object],
    count: Optional[int] = None
) -> List[int]:
    """
    Find available bone function IDs in the custom range (150-251).

    Args:
        existing_bones: List of existing bones in target hierarchy.
        count: Optional limit on number of IDs to return.

    Returns:
        List of available bone IDs.
    """
    # Get used IDs
    used_ids = set()
    for bone in existing_bones:
        bone_id = bone.get('boneFunction')
        if bone_id is not None:
            used_ids.add(bone_id)

    # Find free IDs in custom range
    free_ids = []
    for bone_id in range(addon_config.BONE_ID_CUSTOM_START, addon_config.BONE_ID_CUSTOM_END + 1):
        if bone_id not in used_ids:
            free_ids.append(bone_id)
            if count and len(free_ids) >= count:
                break

    return free_ids


def generate_ctc_object_name(
    source_obj: bpy.types.Object,
    object_type: str,
    prepend_text: str = "",
    base_name: str = "",
    type_count: int = 1,
    add_lr_suffix: bool = True,
    type_prefix: bool = False
) -> str:
    """
    Generate name for copied CTC object.

    Args:
        source_obj: Source object being copied.
        object_type: Type of object ('Bone', 'Header', etc.).
        prepend_text: Text to prepend to source name.
        base_name: Base name for renaming (empty = use source name).
        type_count: Sequential number for this type.
        add_lr_suffix: Whether to add .L/.R suffixes.
        type_prefix: Put type before name instead of after.

    Returns:
        Generated object name.
    """
    # Determine base name
    if base_name:
        if object_type == 'Header':
            obj_name = base_name
        else:
            obj_name = f"{base_name}{type_count}"
    else:
        obj_name = f"{prepend_text}{source_obj.name}"

    # Remove existing .001 style suffixes
    obj_name = re.sub(r'\.\d{3}$', '', obj_name)

    # Detect L/R suffix
    lr_suffix = ''
    if '.R' in source_obj.name:
        lr_suffix = '.R'
    elif '.L' in source_obj.name:
        lr_suffix = '.L'

    # Add type to name if not already present
    if object_type not in obj_name:
        if type_prefix:
            obj_name = f"{object_type}_{obj_name}"
        else:
            obj_name = f"{obj_name}_{object_type}"

    # Handle L/R suffix
    if add_lr_suffix:
        # Remove existing L/R
        obj_name = obj_name.replace('.R', '').replace('.L', '')
        lr_suffix = ''
    else:
        obj_name = obj_name.replace(lr_suffix, '')

    # Add final suffix
    obj_name = obj_name + lr_suffix

    # Make unique
    if bpy.data.objects.get(obj_name):
        num = 1
        base = obj_name.replace(lr_suffix, '')
        while bpy.data.objects.get(f"{base}.{num:03d}{lr_suffix}"):
            num += 1
        obj_name = f"{base}.{num:03d}{lr_suffix}"

    return obj_name


def auto_detect_lr_suffix(
    obj: bpy.types.Object,
    bone_id: int
) -> str:
    """
    Auto-detect .L/.R suffix based on object position.

    Args:
        obj: Object to check.
        bone_id: Bone function ID (only applies to custom bones >= 150).

    Returns:
        '.L', '.R', or '' based on X position.
    """
    if bone_id < addon_config.BONE_ID_CUSTOM_START:
        return ''

    x_pos = obj.matrix_world.to_translation()[0]

    if x_pos < 0:
        return '.R'
    elif x_pos > 0:
        return '.L'

    return ''


def create_ctc_object_copy(
    source_obj: bpy.types.Object,
    new_name: str,
    scene: bpy.types.Scene
) -> bpy.types.Object:
    """
    Create a copy of a CTC object (empty).

    Args:
        source_obj: Source object to copy.
        new_name: Name for new object.
        scene: Scene to link to.

    Returns:
        New object copy.
    """
    # Create new empty
    new_obj = bpy.data.objects.new(new_name, None)
    scene.collection.objects.link(new_obj)

    # Copy basic properties
    new_obj.empty_display_type = source_obj.empty_display_type
    new_obj.empty_display_size = source_obj.empty_display_size
    new_obj.show_axis = source_obj.show_axis

    return new_obj


def copy_ctc_properties(
    source_obj: bpy.types.Object,
    target_obj: bpy.types.Object,
    copy_custom_props: bool = True
):
    """
    Copy properties from source to target CTC object.

    Args:
        source_obj: Source object.
        target_obj: Target object.
        copy_custom_props: Whether to copy custom properties.
    """
    # Copy custom properties if requested
    if copy_custom_props:
        # Copy all custom properties except internal ones
        for key in source_obj.keys():
            if key not in ['_RNA_UI', 'cycles', 'cycles_visibility']:
                try:
                    target_obj[key] = source_obj[key]
                except:
                    pass  # Some properties may not be copyable


def build_source_bone_hierarchy(
    source_root: bpy.types.Object
) -> Dict[int, int]:
    """
    Build parent-child mapping of source bone hierarchy by bone ID.

    Args:
        source_root: Root of source bone hierarchy.

    Returns:
        Dictionary mapping child bone ID to parent bone ID.
    """
    hierarchy = {}
    all_bones = bone_utils.get_all_children(source_root)

    for bone in all_bones:
        bone_id = bone.get('boneFunction')
        if bone_id is None:
            continue

        # Get parent bone ID
        parent_id = 0
        if bone.parent:
            parent_id = bone.parent.get('boneFunction', 0)

        hierarchy[bone_id] = parent_id

    return hierarchy


def sort_ctc_tracks_by_hierarchy(
    tracks: List[CTCObjectTracker]
) -> List[CTCObjectTracker]:
    """
    Sort CTC object tracks to ensure parents are processed before children.

    Args:
        tracks: List of object trackers.

    Returns:
        Sorted list with parents first.
    """
    # Build parent lookup
    parent_map = {}
    for track in tracks:
        if track.source.parent:
            parent_map[track.source] = track.source.parent

    # Topological sort
    sorted_tracks = []
    processed = set()

    def add_with_parents(track):
        if track.source in processed:
            return

        # Add parent first
        parent = parent_map.get(track.source)
        if parent:
            parent_track = next((t for t in tracks if t.source == parent), None)
            if parent_track:
                add_with_parents(parent_track)

        sorted_tracks.append(track)
        processed.add(track.source)

    for track in tracks:
        add_with_parents(track)

    return sorted_tracks


def setup_ctc_object_hierarchy(
    tracks: List[CTCObjectTracker],
    copy_properties: bool,
    scene: bpy.types.Scene
) -> List[str]:
    """
    Set up hierarchy and properties for copied CTC objects.

    Args:
        tracks: List of object trackers (should be sorted).
        copy_properties: Whether to copy custom properties.
        scene: Current scene.

    Returns:
        List of warning messages.
    """
    warnings = []

    # Sort to ensure parents come first
    sorted_tracks = sort_ctc_tracks_by_hierarchy(tracks)

    for track in sorted_tracks:
        source = track.source
        target = track.target

        if not source or not target:
            continue

        # Set parent
        if source.parent:
            parent_track = next((t for t in tracks if t.source == source.parent), None)
            if parent_track and parent_track.target:
                try:
                    target.parent = parent_track.target
                except Exception as e:
                    warnings.append(f"Could not set parent for {target.name}: {e}")
            elif track.bone_id >= addon_config.BONE_ID_CUSTOM_START:
                warnings.append(f"Could not find parent for {target.name}")

        # Copy properties
        if copy_properties:
            copy_ctc_properties(source, target)

        # Handle type-specific setup
        if track.object_type == 'Bone':
            # Set bone function ID
            target['boneFunction'] = track.bone_id
            # Copy local transform
            target.matrix_local = source.matrix_local.copy()

        elif track.object_type == 'Frame':
            # Copy rotation
            target.rotation_euler = source.rotation_euler.copy()

            # Set bone function ID from parent
            if target.parent:
                parent_con = target.parent.constraints.get('Bone Function')
                if parent_con and parent_con.target:
                    parent_bone_id = parent_con.target.get('boneFunction')
                    if parent_bone_id is not None:
                        target['boneFunctionID'] = parent_bone_id

        elif track.object_type == 'Node':
            # Copy constraint
            source_con = source.constraints.get('Bone Function')
            if source_con:
                # Create or get constraint
                target_con = target.constraints.get('Bone Function')
                if not target_con:
                    target_con = target.constraints.new(type='CHILD_OF')
                    target_con.name = 'Bone Function'

                # Find target bone
                if source_con.target:
                    target_bone_track = next(
                        (t for t in tracks if t.source == source_con.target),
                        None
                    )
                    if target_bone_track and target_bone_track.target:
                        target_con.target = target_bone_track.target
                        # Set inverse matrix
                        if target.parent:
                            target_con.inverse_matrix = target.parent.matrix_world.inverted()

    # Update scene
    bpy.context.view_layer.update()

    return warnings


def find_mirror_bone_pairs(
    tracks: List[CTCObjectTracker],
    bone_locations: Dict[bpy.types.Object, Tuple[Vector, Vector]]
) -> Dict[str, List[CTCObjectTracker]]:
    """
    Find mirror bone pairs for L/R linking.

    Args:
        tracks: List of bone trackers.
        bone_locations: Dictionary of bone locations (world and mirrored).

    Returns:
        Dictionary mapping mirror IDs to lists of paired trackers.
    """
    pairs = {}

    for track in tracks:
        if track.object_type != 'Bone' or not track.target:
            continue

        # Check if bone has a mirror
        mirror_offset = bone_utils.find_mirror_bone(track.source, bone_locations)
        if mirror_offset is None:
            continue

        # Create mirror ID
        mirror_id = str(track.bone_id + mirror_offset)

        if mirror_id not in pairs:
            pairs[mirror_id] = []
        pairs[mirror_id].append(track)

    return pairs


def link_mirror_pairs(
    mirror_pairs: Dict[str, List[CTCObjectTracker]]
) -> int:
    """
    Link mirror bone pairs together.

    Args:
        mirror_pairs: Dictionary of mirror pairs.

    Returns:
        Number of pairs linked.
    """
    linked_count = 0

    for mirror_id, tracks in mirror_pairs.items():
        if len(tracks) != 2:
            continue

        track1, track2 = tracks
        track1.pair = track2.target
        track2.pair = track1.target
        linked_count += 1

    return linked_count


def perform_ctc_copy(
    source_ctc_header: bpy.types.Object,
    source_objects: List[bpy.types.Object],
    target_root: bpy.types.Object,
    export_set,
    ctc_organizer,
    scene: bpy.types.Scene,
    copy_from_external: bool = False
) -> Tuple[bool, str, List[CTCObjectTracker]]:
    """
    Main function to copy CTC hierarchy from source to target.

    Args:
        source_ctc_header: Source CTC header object.
        source_objects: List of source CTC objects to copy.
        target_root: Target bone hierarchy root.
        export_set: Target export set.
        ctc_organizer: CTC organizer with copy settings.
        scene: Current scene.
        copy_from_external: Whether copying from external blend file.

    Returns:
        Tuple of (success, message, list of trackers).
    """
    if not target_root:
        return False, "No target root specified", []

    # Get target bone hierarchy
    target_bones = bone_utils.get_all_children(target_root)
    target_by_id = {
        bone.get('boneFunction'): bone
        for bone in target_bones
        if bone.get('boneFunction') is not None
    }

    # Find source bone root
    source_root = find_ctc_source_root(source_objects)
    if not source_root:
        return False, "Could not find source bone hierarchy root", []

    # Get source bones
    source_bones = bone_utils.get_all_children(source_root)

    # Build bone location map for mirror detection
    bone_locations = {}
    for bone in source_bones:
        world_loc = bone.matrix_world.to_translation()
        mirror_loc = Vector([-world_loc.x, world_loc.y, world_loc.z])
        bone_locations[bone] = (world_loc, mirror_loc)

    # Find free bone IDs
    free_ids = find_free_bone_ids(target_bones)

    # Filter source objects based on enabled chains
    if ctc_organizer.entries:
        filtered_objects = []
        for obj in source_objects:
            # Check if object is in a disabled chain
            disabled = False
            for entry in ctc_organizer.entries:
                if not entry.toggle:
                    # Check if obj is in this chain's hierarchy
                    chain_objects = bone_utils.get_all_children(entry.chain)
                    if obj in chain_objects:
                        disabled = True
                        break

            if not disabled:
                filtered_objects.append(obj)

        source_objects = filtered_objects

    # Get or create CTC copy source tracker
    ctc_copy_src = None
    for src in export_set.ctc_copy_sources:
        if src.source == source_ctc_header:
            ctc_copy_src = src
            break

    if not ctc_copy_src:
        ctc_copy_src = export_set.ctc_copy_sources.add()
        ctc_copy_src.name = source_ctc_header.name
        ctc_copy_src.source = source_ctc_header
        ctc_copy_src.target = target_root

    # Load existing tracks
    existing_tracks = {}
    changed_ids = {}
    for track in ctc_copy_src.copy_src_track:
        if track.bone_id:
            existing_tracks[track.bone_id] = track
        if track.changed_id:
            changed_ids[track.bone_id] = track

    # Process settings
    prepend_text = ctc_organizer.prepend_text if hasattr(ctc_organizer, 'prepend_text') else ""
    base_name = ctc_organizer.base_name if hasattr(ctc_organizer, 'base_name') else ""
    add_lr = ctc_organizer.add_lr_suffixes if hasattr(ctc_organizer, 'add_lr_suffixes') else True
    type_prefix = ctc_organizer.type_name_prefix if hasattr(ctc_organizer, 'type_name_prefix') else False

    # Create object trackers
    trackers = []
    type_counts = {'Bone': 1, 'Header': 1, 'Frame': 1, 'Chain': 1, 'Node': 1}

    # Handle CTC header
    target_header = export_set.ctc_header
    if not target_header:
        # Create copy of header
        header_name = generate_ctc_object_name(
            source_ctc_header, 'Header', prepend_text, base_name,
            type_counts['Header'], add_lr, type_prefix
        )
        target_header = create_ctc_object_copy(source_ctc_header, header_name, scene)
        export_set.ctc_header = target_header

    # Create tracker for header
    header_tracker = CTCObjectTracker(source_ctc_header, target_header, 'Header')
    trackers.append(header_tracker)

    # Copy remaining objects
    for source_obj in source_objects:
        if source_obj == source_ctc_header:
            continue  # Already handled

        # Determine object type
        obj_type = get_object_type(source_obj)

        # Check if already copied
        bone_id = source_obj.get('boneFunction', 0)
        existing_track = existing_tracks.get(bone_id)

        target_obj = None
        if existing_track and existing_track.o2:
            target_obj = existing_track.o2
        elif obj_type == 'Bone' and bone_id and bone_id < addon_config.BONE_ID_CUSTOM_START:
            # Use existing vanilla bone
            target_obj = target_by_id.get(bone_id)

        # Create new object if needed
        if not target_obj:
            # Generate name
            obj_name = generate_ctc_object_name(
                source_obj, obj_type, prepend_text, base_name,
                type_counts[obj_type], add_lr, type_prefix
            )

            # Auto-detect L/R if needed
            if add_lr and obj_type == 'Bone' and bone_id >= addon_config.BONE_ID_CUSTOM_START:
                lr_suffix = auto_detect_lr_suffix(source_obj, bone_id)
                if lr_suffix and not obj_name.endswith(('.L', '.R')):
                    obj_name += lr_suffix

            # Create object
            target_obj = create_ctc_object_copy(source_obj, obj_name, scene)

        # Handle bone ID assignment
        final_bone_id = bone_id
        final_changed_id = 0

        if obj_type == 'Bone' and bone_id:
            # Check for ID conflict
            if bone_id >= addon_config.BONE_ID_CUSTOM_START and target_by_id.get(bone_id):
                # Need to reassign ID
                if free_ids:
                    final_changed_id = bone_id
                    final_bone_id = free_ids.pop(0)
                else:
                    return False, f"No free bone IDs available for {source_obj.name}", trackers

        # Create tracker
        tracker = CTCObjectTracker(source_obj, target_obj, obj_type, final_bone_id, final_changed_id)
        trackers.append(tracker)

        # Increment type counter
        type_counts[obj_type] += 1

    # Set up hierarchy and properties
    warnings = setup_ctc_object_hierarchy(trackers, ctc_organizer.copy_props, scene)

    # Find and link mirror pairs
    mirror_pairs = find_mirror_bone_pairs(trackers, bone_locations)
    pairs_linked = link_mirror_pairs(mirror_pairs)

    # Save trackers to property group
    ctc_copy_src.copy_src_track.clear()
    for tracker in trackers:
        track_entry = ctc_copy_src.copy_src_track.add()
        track_entry.caster = tracker.source
        track_entry.o2 = tracker.target
        track_entry.ttype = tracker.object_type
        track_entry.bone_id = tracker.bone_id
        track_entry.changed_id = tracker.changed_id
        if tracker.pair:
            track_entry.pair = tracker.pair

    # Build success message
    message = f"Copied {len(trackers)} CTC objects"
    if pairs_linked:
        message += f", linked {pairs_linked} mirror pairs"
    if warnings:
        message += f"\nWarnings: {'; '.join(warnings)}"

    return True, message, trackers


def perform_ctc_copy_with_weights(
    source_ctc_header: bpy.types.Object,
    source_objects: List[bpy.types.Object],
    source_export_set,
    target_export_set,
    ctc_organizer,
    context: bpy.types.Context,
    copy_from_external: bool = False
) -> Tuple[bool, str]:
    """
    Complete CTC copy operation including weight transfer.

    This is the main entry point that combines:
    1. CTC hierarchy copying
    2. Weight transfer from source to target meshes
    3. Weight cleaning

    Args:
        source_ctc_header: Source CTC header.
        source_objects: List of source CTC objects.
        source_export_set: Source export set.
        target_export_set: Target export set.
        ctc_organizer: CTC organizer with settings.
        context: Blender context.
        copy_from_external: Whether source is from external file.

    Returns:
        Tuple of (success, message).
    """
    scene = context.scene

    # Determine target root
    target_root = None
    if ctc_organizer.use_active_object:
        target_root = context.active_object if not target_export_set.empty_root else target_export_set.empty_root
    else:
        target_root = target_export_set.empty_root if target_export_set.empty_root else context.active_object

    if not target_root:
        return False, "No target root object specified"

    # Perform CTC copy if requested
    trackers = []
    if ctc_organizer.copy_ctc_hierarchy:
        success, message, trackers = perform_ctc_copy(
            source_ctc_header,
            source_objects,
            target_root,
            target_export_set,
            ctc_organizer,
            scene,
            copy_from_external
        )

        if not success:
            return False, message

    # Build bone name mapping for weight transfer
    bone_mapping = {}
    changed_id_mapping = {}

    for tracker in trackers:
        if tracker.object_type == 'Bone' and tracker.target:
            bone_mapping[tracker.source.name] = tracker.target

            if tracker.changed_id:
                changed_id_mapping[tracker.changed_id] = tracker.bone_id

    # Also add existing bones from target hierarchy
    from . import weight_transfer
    target_bones = bone_utils.get_all_children(target_root)

    # Get source bone root for additional bone mapping
    source_root = find_ctc_source_root(source_objects)
    if source_root:
        source_bones = bone_utils.get_all_children(source_root)

        # Build complete bone mapping
        full_mapping = weight_transfer.build_bone_name_mapping(
            source_root,
            target_root,
            changed_id_mapping
        )
        bone_mapping.update(full_mapping)

    # Perform weight transfer if requested
    if ctc_organizer.transfer_weights:
        # Build tag dictionary
        tag_dict = weight_transfer.build_tag_dictionary(source_export_set, target_export_set)

        # Perform transfer
        stats = weight_transfer.transfer_weights_by_tag(
            source_export_set,
            target_export_set,
            ctc_organizer,
            bone_mapping,
            scene
        )

        message += f"\nWeight transfer: {stats['transferred']} transfers, {stats['cleaned']} cleaned"

    return True, message
