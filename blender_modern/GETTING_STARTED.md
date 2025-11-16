# Getting Started with Modernized MHW Set Organizer

## 🎯 Current Status

This modernized version is **~10% complete**. The foundation is solid, but major functionality still needs to be implemented.

### ✅ What's Done

**Infrastructure (100%)**
- Clean folder structure with separated concerns
- Modern Python 3.10+ code with type hints
- Comprehensive utility functions
- Cross-platform path handling
- Proper error handling patterns
- All constants extracted to config file

**Utils Package (100%)**
- `file_utils.py` - File I/O, settings, paths
- `mesh_utils.py` - Mesh operations, weight transfer, normals
- `bone_utils.py` - Bone hierarchy, mirroring, validation
- `validation.py` - Input validation helpers

**Documentation (100%)**
- Migration guide from 2.79 to 4.x
- Implementation status tracker
- Module-level documentation

### 🚧 What Needs Implementation

**Properties (0%)** - NEXT PRIORITY
- Export set data structures
- CTC properties
- Settings and configuration
- Batch export properties

**Operators (0%)**
- Export operators (MOD3/CTC/CCL)
- Import operators
- CTC copy/paste
- Utility operators

**UI (0%)**
- Main panel
- UI lists
- Property displays

**Core Logic (0%)**
- Export workflow
- CTC management
- Weight transfer logic

## 🚀 How to Continue Development

### Option 1: Step-by-Step Implementation

Follow this order for best results:

#### Step 1: Properties Module (4-6 hours)
Start here because everything depends on these data structures.

1. Create `properties/export_set.py`:
   - `MHW_PG_ExportSetObject` - Individual objects in a set
   - `MHW_PG_ExportSet` - Main export set container

2. Create `properties/settings.py`:
   - `MHW_PG_Settings` - Main addon settings
   - `MHW_PG_ArmorEntry` - Armor database entries

3. Create `properties/ctc_properties.py`:
   - `MHW_PG_CTCCopySource` - CTC copy tracking
   - `MHW_PG_CTCOrganizer` - CTC copy settings

4. Create `properties/batch_export.py`:
   - `MHW_PG_SetOfSets` - Batch export container

**Test after each file:** Register the properties in Blender and verify they appear correctly.

#### Step 2: Core Logic (8-10 hours)
Extract business logic before implementing operators.

1. Create `core/export_logic.py`:
   - Functions to handle MOD3/CTC/CCL export
   - Shape key application
   - Hook modifier handling

2. Create `core/ctc_manager.py`:
   - CTC hierarchy copying
   - Bone ID management
   - Property copying

3. Create `core/weight_transfer.py`:
   - Tag-based weight transfer
   - Weight cleaning/normalization

**Test:** Write simple test scripts that call these functions directly.

#### Step 3: Operators (10-12 hours)
Now implement the UI actions using the core logic.

1. Create `operators/export_ops.py`
2. Create `operators/import_ops.py`
3. Create `operators/ctc_ops.py`
4. Create `operators/utility_ops.py`

**Test:** Each operator should work in Blender's Python console.

#### Step 4: UI (6-8 hours)
Build the interface last.

1. Create `ui/main_panel.py`
2. Create `ui/ui_lists.py`

**Test:** The addon should be fully functional at this point.

### Option 2: I Can Help You Implement

I can help implement any of the remaining modules. Just tell me which one to start with!

**Example request:**
> "Please implement the properties/export_set.py module"

**I will:**
1. Migrate the legacy property groups
2. Update to Blender 4.x API
3. Add type hints and docstrings
4. Include validation
5. Make it ready to register

## 📖 Reference: Legacy → Modern Mapping

When implementing, refer to these mappings:

### Property Groups
```python
# Legacy → Modern
mhwExpSetObj → MHW_PG_ExportSetObject
mhwExpSet → MHW_PG_ExportSet
ctc_copy_sources → MHW_PG_CTCCopySource
ctc_copy_organizer → MHW_PG_CTCOrganizer
dpMHW_help → MHW_PG_Settings
mhwSetOfSets → MHW_PG_SetOfSets
```

### Operators
```python
# Legacy → Modern
UniExporter → MHW_OT_Export
MHW_ImportManager → MHW_OT_Import
CopyCTCops → MHW_OT_CopyCTC
CopyObjectChangeVG → MHW_OT_CopyObject
```

### Functions
```python
# Legacy → Modern
o_tri() → triangulate_mesh()
weight_transfer() → transfer_weights()
all_heir() → get_all_children()
```

## 🛠️ Development Tips

### 1. Use the Utilities
Don't rewrite what's already done!

```python
# Instead of writing path concatenation:
path = base_dir + '\\' + 'subfolder' + '\\' + 'file.ext'

# Use the utility:
from ..utils import file_utils
path = file_utils.get_addon_directory() / 'subfolder' / 'file.ext'
```

### 2. Use the Constants
```python
# Instead of:
if bone_id >= 150:

# Use:
from .. import addon_config
if bone_id >= addon_config.BONE_ID_CUSTOM_START:
```

### 3. Add Validation
```python
from ..utils import validation

def execute(self, context):
    is_valid, error = validation.validate_export_set(export_set)
    if not is_valid:
        self.report({'ERROR'}, error)
        return {'CANCELLED'}
```

### 4. Type Hints Help IDEs
```python
def my_function(
    obj: bpy.types.Object,
    count: int = 1
) -> Optional[bpy.types.Mesh]:
    """Your IDE will autocomplete obj. and show you available methods!"""
```

## 🧪 Testing in Blender

### Quick Test Setup
1. Copy `blender_modern` to your Blender addons folder
2. Rename to `mhw_set_organizer_modern`
3. In Blender Text Editor, run:

```python
import sys
sys.path.append('/path/to/MHW_SetOrganizer/blender_modern')

import importlib
import blender_modern
importlib.reload(blender_modern)

blender_modern.register()
```

### Incremental Testing
After implementing each property group:

```python
import bpy
from blender_modern.properties import export_set

# Register just this module
bpy.utils.register_class(export_set.MHW_PG_ExportSet)

# Test it
test_set = bpy.context.scene.collection.add()
test_set.name = "Test"
print(test_set.name)  # Should work!
```

## 📚 Documentation Resources

- **Blender API**: https://docs.blender.org/api/current/
- **API Changes**: https://wiki.blender.org/wiki/Reference/Release_Notes/2.80/Python_API
- **Type Hints**: https://docs.python.org/3/library/typing.html
- **PEP 8 Style**: https://pep8.org/

## 🤝 Contributing

If you're improving this modernization:

1. Follow the existing patterns
2. Add docstrings to every function
3. Use type hints
4. Add validation for user inputs
5. Test in Blender before committing
6. Update `IMPLEMENTATION_STATUS.md`

## ❓ Questions?

Check these files for guidance:
- **How to structure a module?** → Look at `utils/bone_utils.py`
- **How to write docstrings?** → See examples in all utils files
- **What constants exist?** → Read `addon_config.py`
- **How to validate?** → Check `utils/validation.py`
- **Legacy code reference?** → Original files in parent directory

## 🎉 Next Steps

**Recommended path:**
1. Read through `IMPLEMENTATION_STATUS.md`
2. Look at a legacy property group in `../mhw_set_organizer.py`
3. Implement the modern version in `properties/export_set.py`
4. Test it in Blender
5. Move on to the next module

**Or just ask me to help implement any specific module!**

---

Good luck with the refactoring! The hard part (architecture) is done. Now it's just systematic migration of functionality. 🚀
