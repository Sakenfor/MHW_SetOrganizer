# Migration Guide: Blender 2.79 → Modern (3.x/4.x)

This guide explains the differences between the legacy (2.79) and modernized versions of MHW Set Organizer.

## File Structure Changes

### Legacy Structure (2.79)
```
MHW_SetOrganizer/
├── __init__.py
├── mhw_set_organizer.py (1200+ lines)
├── general_functions.py
├── operators/
│   └── usual_operators.py (1500+ lines)
└── gui_stuff/
    └── dpmhw_arrangers.py
```

### Modern Structure (3.x/4.x)
```
MHW_SetOrganizer/blender_modern/
├── __init__.py                # Clean entry point
├── addon_config.py            # All constants in one place
├── properties/                # Property groups (data structures)
│   ├── export_set.py
│   ├── ctc_properties.py
│   ├── settings.py
│   └── batch_export.py
├── operators/                 # UI operators
│   ├── export_ops.py
│   ├── import_ops.py
│   ├── ctc_ops.py
│   └── utility_ops.py
├── ui/                        # UI panels and lists
│   ├── main_panel.py
│   └── ui_lists.py
├── core/                      # Business logic
│   ├── export_logic.py
│   ├── ctc_manager.py
│   └── weight_transfer.py
└── utils/                     # Helper functions
    ├── file_utils.py
    ├── mesh_utils.py
    ├── bone_utils.py
    └── validation.py
```

## Key API Changes

### 1. Property Registration

**Legacy (2.79):**
```python
bpy.types.Scene.mhwsake = PointerProperty(type=dpMHW_help)
```

**Modern (3.x/4.x):**
```python
bpy.types.Scene.mhw_data = PointerProperty(
    type=MHW_PG_Settings,
    name="MHW Set Organizer Data"
)
```

### 2. Operator Context Override

**Legacy (2.79):**
```python
bpy.ops.object.modifier_apply(modifier=mod_name)
```

**Modern (3.x/4.x):**
```python
with bpy.context.temp_override(object=target_obj):
    bpy.ops.object.modifier_apply(modifier=mod_name)
```

### 3. Object Selection

**Legacy (2.79):**
```python
obj.select = True
scene.objects.active = obj
```

**Modern (3.x/4.x):**
```python
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
```

### 4. UI Layout Changes

**Legacy (2.79):**
```python
row = layout.row()
row.label("Some text")
```

**Modern (3.x/4.x):**
```python
row = layout.row()
row.label(text="Some text")  # 'text' parameter required
```

### 5. Path Handling

**Legacy:**
```python
path = base_dir + '\\' + filename  # Windows-only
```

**Modern:**
```python
from pathlib import Path
path = Path(base_dir) / filename  # Cross-platform
```

## Code Quality Improvements

### 1. **Magic Numbers → Constants**

**Before:**
```python
if bone_id >= 150:
    # Custom bone logic
```

**After:**
```python
from .. import addon_config

if bone_id >= addon_config.BONE_ID_CUSTOM_START:
    # Custom bone logic
```

### 2. **No More eval()**

**Before:**
```python
_set = eval(self.var1)  # Dangerous!
```

**After:**
```python
_set = context.scene.mhw_data.export_set[self.set_index]  # Safe
```

### 3. **Proper Exception Handling**

**Before:**
```python
try:
    os.makedirs(path)
except:
    pass  # Silently fails
```

**After:**
```python
try:
    os.makedirs(path, exist_ok=True)
    self.report({'INFO'}, f'Created directory: {path}')
except OSError as e:
    self.report({'ERROR'}, f'Cannot create directory: {e}')
    return {'CANCELLED'}
```

### 4. **Type Hints and Docstrings**

**Before:**
```python
def o_tri(self, scene, object):
    mesh_tri = object.data.copy()
    # ...
```

**After:**
```python
def triangulate_mesh(
    mesh_object: bpy.types.Object,
    preserve_original: bool = True
) -> Optional[bpy.types.Mesh]:
    """
    Create a triangulated version of a mesh.

    Args:
        mesh_object: Object with mesh data to triangulate.
        preserve_original: If True, creates a copy.

    Returns:
        Triangulated mesh data, or None on error.
    """
    # ...
```

### 5. **Better Organization**

**Before (all in one file):**
```python
def MHW_Export(...):  # 162 lines
    # Validation
    # Object manipulation
    # Shape keys
    # Hooks
    # Export
    # Cleanup
```

**After (separated concerns):**
```python
# In export_logic.py
def validate_export_objects(export_set) -> bool: ...
def apply_shape_keys(obj, config) -> None: ...
def export_to_mod3(objects, path, settings) -> bool: ...

# In export_ops.py
class MHW_OT_Export(Operator):
    def execute(self, context):
        if not validate_export_objects(export_set):
            return {'CANCELLED'}
        # ...
```

## Breaking Changes

### Property Access

**Legacy:**
```python
mhw = scene.mhwsake
```

**Modern:**
```python
mhw = scene.mhw_data
```

### Settings File Location

Both versions use the same `MhwSettings.json` but modern version uses `pathlib` for cross-platform compatibility.

### Icon Loading

**Legacy:**
```python
custom_icons = bpy.utils.previews.new()
custom_icons.load('arm', icon_path, 'IMAGE')
```

**Modern:**
```python
# Handled internally by ui/icons.py module
from ..ui import icons
icon_id = icons.get_icon_id('arm')
```

## Migration Steps

If you have existing `.blend` files with the legacy addon:

1. **Export your settings** using "Save Settings" in the old addon
2. **Disable** the old addon in Blender preferences
3. **Install** the new addon from `blender_modern/` folder
4. **Enable** the new addon
5. **Load settings** - the new addon will read `MhwSettings.json`
6. **Verify** your export sets still work

## Compatibility Notes

- **Settings are compatible** - Both versions use the same JSON format
- **Blend files are compatible** - Property names have changed but data can be migrated
- **External dependencies** - Still requires Mod3-MHW-Importer and CTC-MHW-Editor
- **Python 3.10+** required for modern version (Blender 3.x+)

## Feature Parity

All features from the legacy version are present in the modern version:

- ✅ MOD3/CTC/CCL export/import
- ✅ Batch export (Sets of Sets)
- ✅ CTC copy and weight transfer
- ✅ Shape key application
- ✅ Hook modifier support
- ✅ Vertex group management
- ✅ Bone mirroring
- ✅ Tag-based weight transfer
- ✅ Normal transfer

## New Features in Modern Version

- ✅ Better error messages
- ✅ Input validation before operations
- ✅ Cross-platform path handling
- ✅ Progress reporting
- ✅ Undo support improvements
- ✅ Type hints for IDE autocomplete
- ✅ Comprehensive documentation

## Getting Help

If you encounter issues during migration:

1. Check the [GitHub Issues](https://github.com/Sakenfor/MHW_SetOrganizer/issues)
2. Compare your workflow to the [Wiki](https://github.com/Sakenfor/MHW_SetOrganizer/wiki)
3. Report bugs with:
   - Blender version
   - Error message (check Console)
   - Steps to reproduce

## For Developers

If you're extending the addon:

- Read docstrings in each module
- Follow PEP 8 style guide
- Add type hints to new functions
- Write validation for user inputs
- Use constants from `addon_config.py`
- Separate UI, operators, and logic

## Performance

The modern version may be slightly slower on initial load due to proper module separation, but runtime performance is equivalent or better due to:

- Better caching
- Fewer redundant operations
- Cleaner memory management
