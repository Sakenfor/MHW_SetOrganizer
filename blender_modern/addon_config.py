"""
Configuration and constants for MHW Set Organizer addon.

This module contains all configuration values, magic numbers, and constants
used throughout the addon.
"""

# Addon metadata
ADDON_NAME = "MHW Set Organizer"
ADDON_VERSION = (2, 0, 0)
ADDON_AUTHOR = "Sakenfor (dp16)"
BLENDER_VERSION_MIN = (3, 0, 0)

# Bone function IDs
BONE_ID_VANILLA_MAX = 149
"""Maximum bone ID for vanilla MHW bones (0-149)."""

BONE_ID_CUSTOM_START = 150
"""Starting ID for custom/modded bones."""

BONE_ID_CUSTOM_END = 251
"""Maximum bone ID for custom bones."""

# Armor parts
ARMOR_PARTS = ['leg', 'wst', 'arm', 'body', 'helm']
"""Valid armor piece types."""

# Gender options
GENDER_OPTIONS = ['f', 'm']
"""Valid gender options for armor sets."""

# File extensions
EXT_MOD3 = '.mod3'
EXT_CTC = '.ctc'
EXT_CCL = '.ccl'

# Object types
TYPE_CTC_HEADER = 'CTC'
TYPE_CTC_CHAIN = 'CTC_Chain'
TYPE_CTC_FRAME = 'CTC_*_Frame'
TYPE_CTC_NODE = 'CTC_Node'
TYPE_SKELETON_ROOT = 'MOD3_SkeletonRoot'
TYPE_CCL = 'CCL'
TYPE_BONE = 'Bone'

# Type collections
EDITABLE_TYPES = [TYPE_CTC_FRAME, TYPE_CTC_HEADER, TYPE_CTC_CHAIN, TYPE_BONE]
ALL_CTC_TYPES = [TYPE_CTC_FRAME, TYPE_CTC_HEADER, TYPE_CTC_CHAIN, TYPE_CTC_NODE]

# Type icons (Blender icon names)
TYPE_ICONS = {
    TYPE_CTC_FRAME: 'OUTLINER_OB_LATTICE',
    TYPE_CTC_HEADER: 'FORCE_FORCE',
    TYPE_CTC_CHAIN: 'LINKED',
    TYPE_BONE: 'BONE_DATA',
}

# Type display names
TYPE_DISPLAY_NAMES = {
    TYPE_CTC_FRAME: 'Frame',
    TYPE_CTC_HEADER: 'Header',
    TYPE_CTC_CHAIN: 'Chain',
    TYPE_CTC_NODE: 'Node',
}

# Weight transfer limits
WEIGHT_LIMIT_ALL = 'All Groups'
WEIGHT_LIMIT_BELOW_150 = 'Below 150 ID'
WEIGHT_LIMIT_ABOVE_150 = 'Above 150 ID'

# Shape key application methods
SHAPE_KEY_METHOD_GLOBAL = 'Global Key Name'
SHAPE_KEY_METHOD_ACTIVE = 'Active Keys'
SHAPE_KEY_METHOD_SPECIFIC = 'Specific Keys'

# Path templates
PATH_NATIVE_TEMPLATE = 'nativePC/pl/{gender}_equip/{armorname}/{armor_part}/mod'
PATH_FILE_TEMPLATE = '{gender}_{armor_part}{armorname2}'

# Settings file
SETTINGS_FILENAME = 'MhwSettings.json'

# Vertex group limits
VG_LIMIT_4_WEIGHTS = 4
VG_LIMIT_8_WEIGHTS = 8

# Property edit lists for different types
PROPERTY_EDIT_LISTS = {
    TYPE_CTC_FRAME: ['Fixed End', 'radius', 'unknownFloatSet000'],
    TYPE_CTC_HEADER: [
        'Dampening',
        'Gravity Multiplier',
        'Low Wind Effect',
        'Medium Wind Effect',
        'Strong Wind Effect'
    ],
    TYPE_CTC_CHAIN: [
        'Snapping',
        'Tension',
        'Weightiness',
        'Cone of Motion',
        'Wind Multiplier',
        'Chain Length',
        'CCL Collision'
    ],
    TYPE_BONE: ['boneFunction', 'unkn2'],
    TYPE_CTC_NODE: [],
}

# Properties to show when collapsed
PROPERTIES_INFO_CLOSED = {
    TYPE_CTC_FRAME: [],
    TYPE_CTC_HEADER: [],
    TYPE_CTC_CHAIN: ['Snapping', 'Tension', 'Weightiness'],
    TYPE_BONE: ['boneFunction'],
    TYPE_CTC_NODE: [],
}

# Property icons
PROPERTY_ICONS = {
    'Snapping': 'FORCE_HARMONIC',
    'Tension': 'FORCE_TURBULENCE',
    'Wind Multiplier': 'FORCE_WIND',
    'boneFunction': 'FONT_DATA',
    'Weightiness': 'MOD_VERTEX_WEIGHT',
    'Cone of Motion': 'MESH_CONE',
    'Gravity Multiplier': 'FORCE_CHARGE',
}

# Type sorting order (for UI display)
TYPE_SORT_ORDER = [TYPE_CTC_CHAIN, TYPE_CTC_HEADER, TYPE_CTC_FRAME, TYPE_BONE]

# Useful modifier types
USEFUL_MODIFIERS = ['HOOK']

# Normals preservation methods
NORMALS_METHOD_SPLIT = 'Normals Split'
NORMALS_METHOD_TRANSFER = 'Normals Transfer'

# Mirror sides
MIRROR_L_TO_R = 'L>R'
MIRROR_R_TO_L = 'R>L'

# Default values
DEFAULT_SMOOTH_STRENGTH = 0.5
DEFAULT_SMOOTH_COUNT = 1
DEFAULT_CCL_SCALE = 1.0

# Help text / tooltips
HELP_TEXT = {
    'obj_info': '''You can put capsules in objects list too.
Use black dot to toggle export on/off per object.
Can freely change scene object names without editing list names again.
(same goes for 'Root' and 'CTC_header')

Use ctrl+scroll to go through objects, or click between name and the dot
to select an object.''',

    'scenes_reload': '''Refresh settings and armor 'numbers' (folder names).
Use it if you create new scene to update the settings.''',

    'append_native': '''This will append nativePC\\..etc.. to the set's
Custom Path too, when export is ran from Batch Export.

If Set's Custom Path has nativePC on, and 'UsePerSetCustompath' is on,
nativePC will be added, even if this toggle is off.''',

    'ctc_copy': '''This text will be prepended to all CTC and Bones that will be copied.

Best to use some text to easier tell apart the CTC's.''',

    'ctc_edit_update': '''Update internal names of ctc edit collection,
useful for the "Pick" prop search only ATM.

Can freely edit object names with that being said.''',

    'ctc_copy_over_props': '''Copying the props from sources, will preserve
the shifted boneFunctions if there are any, on Frame and Bone.''',
}
