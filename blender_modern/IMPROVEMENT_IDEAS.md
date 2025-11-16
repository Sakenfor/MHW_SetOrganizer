# MHW Set Organizer - Improvement Ideas

## Overview
This document outlines potential improvements to make the addon more powerful, user-friendly, and aligned with modern Blender workflows and the latest versions of the external MHW tools.

---

## 1. External Tool Compatibility

### 1.1 Version Detection & Adaptation
**Current State:** Hardcoded operator names with basic error checking
**Improvement:**
- Detect installed versions of Mod3-MHW-Importer and CTC-MHW-Editor
- Display version info in addon preferences or panel
- Warn user if external tools are outdated
- Adapt to API changes automatically if possible

```python
# Example implementation
def detect_external_addon_version(addon_name):
    """Check if external addon is installed and get version."""
    if addon_name in bpy.context.preferences.addons:
        addon = bpy.context.preferences.addons[addon_name]
        return addon.module, getattr(addon.module, '__version__', 'Unknown')
    return None, None
```

### 1.2 New Features from External Tools
**Check if these features exist in latest Mod3-MHW-Importer:**
- [ ] Support for new mesh formats or LOD types
- [ ] Improved weight painting import/export
- [ ] Better material/texture handling
- [ ] Support for new armor pieces (e.g., Sunbreak additions)
- [ ] Performance optimizations for large files

**Check if these features exist in latest CTC-MHW-Editor:**
- [ ] New cloth physics parameters
- [ ] Improved constraint handling
- [ ] Better frame alignment options
- [ ] Support for new bone functions

---

## 2. Modern Blender Features (3.x/4.x)

### 2.1 Asset Browser Integration
**Priority: High**
Make export sets browsable and reusable across projects.

**Implementation:**
- Mark export sets as assets with custom metadata
- Add thumbnail generation for quick identification
- Allow drag-and-drop of export sets between files
- Create asset catalog for organizing by armor type

```python
# Operator to mark export set as asset
class MHW_OT_MarkExportSetAsAsset(Operator):
    """Mark export set as asset for asset browser"""
    bl_idname = "mhw.mark_export_set_as_asset"
    bl_label = "Mark as Asset"

    def execute(self, context):
        export_set = context.scene.mhw_data.export_sets[...]
        # Create data-block to represent set
        # Mark as asset
        # Generate thumbnail
        return {'FINISHED'}
```

### 2.2 Geometry Nodes Support
**Priority: Medium**
Integrate with Blender's procedural modeling system.

**Ideas:**
- Preset geometry node setups for common armor modifications
- Auto-apply modifiers for symmetry, subdivision, etc.
- Procedural LOD generation
- Automated UV unwrapping helpers

### 2.3 Collections-Based Organization
**Priority: High**
Use Blender's native collections for better scene organization.

**Implementation:**
- Auto-create collection for each export set
- Use collection color coding by armor part
- Link/instance collections across scenes
- Collection hierarchy matching game structure

```python
def create_export_set_collection(export_set_name, armor_part):
    """Create and organize collection for export set."""
    collection = bpy.data.collections.new(export_set_name)
    bpy.context.scene.collection.children.link(collection)

    # Set color by armor part
    color_map = {
        'head': 'COLOR_01',
        'body': 'COLOR_02',
        'arm': 'COLOR_03',
        'waist': 'COLOR_04',
        'leg': 'COLOR_05',
    }
    collection.color_tag = color_map.get(armor_part, 'COLOR_08')
    return collection
```

### 2.4 Improved Material Workflow
**Priority: Medium**
Better integration with Blender's shader nodes.

**Features:**
- Material presets for MHW armor types
- Automatic PBR texture setup
- Batch material assignment
- Material library browser
- Preview rendering with game-accurate lighting

---

## 3. Workflow Enhancements

### 3.1 Quick Actions & Shortcuts
**Priority: High**
Speed up common operations.

**Features:**
- Quick add object to active export set (keyboard shortcut)
- One-click duplicate export set with all settings
- Quick toggle visibility of export set objects
- Fast switch between export sets (pie menu)
- Context menu integration (right-click on object)

```python
# Example: Add to active export set from context menu
def mhw_object_context_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.operator("mhw.add_to_active_export_set", icon='ADD')

def register():
    bpy.types.VIEW3D_MT_object_context_menu.append(mhw_object_context_menu)
```

### 3.2 Preset System
**Priority: Medium**
Save and reuse common configurations.

**Types of Presets:**
- Export settings presets (LOD, normals, weights, etc.)
- Path templates for different mod types
- CTC copy configurations
- Full export set templates by armor type

```python
# Store presets as JSON
{
    "name": "High Quality Export",
    "split_normals": true,
    "highest_lod": true,
    "coerce_fourth": true,
    "import_textures": true
}
```

### 3.3 Batch Operations
**Priority: Medium**
Operations on multiple objects/sets at once.

**Features:**
- Batch rename objects (with regex support)
- Batch material assignment
- Batch weight transfer across sets
- Batch apply modifiers
- Batch toggle export flags

### 3.4 Smart Object Management
**Priority: Low**
Intelligent object handling.

**Features:**
- Auto-detect armor part from object name
- Suggest export set based on object type
- Warn about common issues (non-manifold, loose verts, etc.)
- Auto-fix common problems (remove doubles, recalc normals)

---

## 4. Quality of Life Features

### 4.1 Visual Feedback
**Priority: High**
Better visual indication of state.

**Features:**
- Color-code objects by export set in viewport
- Highlight objects in active export set
- Show export path directly in 3D viewport (overlay)
- Icon indicators for object status (exportable, has issues, etc.)
- Progress bars for long operations

### 4.2 Validation & Error Checking
**Priority: High**
Catch problems before export.

**Checks:**
- Missing textures or materials
- Objects with no materials
- Degenerate geometry
- Mismatched armature bindings
- CTC header errors
- File path validity
- Disk space availability

```python
class MHW_OT_ValidateExportSet(Operator):
    """Check export set for common issues before export"""
    bl_idname = "mhw.validate_export_set"
    bl_label = "Validate Export Set"

    def execute(self, context):
        export_set = get_active_export_set(context)
        issues = []

        # Check each object
        for eobj in export_set.eobjs:
            if not eobj.obje:
                issues.append(f"Empty object slot")
            elif not eobj.obje.data.materials:
                issues.append(f"{eobj.obje.name}: No materials")
            # More checks...

        if issues:
            # Show issues in popup
            self.report({'WARNING'}, f"Found {len(issues)} issues")
        else:
            self.report({'INFO'}, "Export set is valid")

        return {'FINISHED'}
```

### 4.3 History & Undo System
**Priority: Low**
Track export operations.

**Features:**
- Export history log (what was exported, when, where)
- Quick re-export with previous settings
- Undo/redo for set management operations
- Compare different export versions

### 4.4 Search & Filter
**Priority: Medium**
Find things quickly.

**Features:**
- Search export sets by name/armor
- Filter objects by type, material, tags
- Quick filter in object lists
- Saved search queries

---

## 5. Import/Export Enhancements

### 5.1 Drag & Drop Support
**Priority: Medium**
Modern file handling.

**Features:**
- Drag .mod3/.ctc/.ccl files into Blender to import
- Auto-create export set from dropped files
- Drag textures to auto-assign
- Drop .blend files to link CTC sources

### 5.2 Export Profiles
**Priority: Medium**
Different export configurations for different purposes.

**Profiles:**
- "High Quality" - Full detail, all features
- "Testing" - Quick export for iteration
- "Distribution" - Optimized for release
- "Backup" - Include all data for archival

### 5.3 Path Management Improvements
**Priority: High**
Better path handling.

**Features:**
- Path templates with variables (e.g., `${game_path}/${armor}/${part}`)
- Recent paths dropdown
- Path validation before export
- Auto-create missing directories
- Path relative to .blend file option

```python
# Path template system
template = "${game_path}/nativePC/pl/${gender}_equip/${armor}/${part}/mod"
variables = {
    'game_path': mhw.game_path,
    'gender': export_set.gender,
    'armor': export_set.armor_name,
    'part': export_set.armor_part
}
resolved = resolve_path_template(template, variables)
```

### 5.4 Export Queue
**Priority: Low**
Queue exports for batch processing.

**Features:**
- Add multiple sets to export queue
- Process queue in background
- Pause/resume queue
- Export queue persistence across sessions

---

## 6. CTC/Physics Enhancements

### 6.1 CTC Visual Helpers
**Priority: Medium**
Better visualization of cloth physics.

**Features:**
- Visualize CTC constraints in viewport
- Preview cloth simulation in Blender
- Color-code bones by CTC type
- Show influence zones
- Gizmos for editing CTC parameters

### 6.2 Weight Transfer Improvements
**Priority: High**
More robust weight transfer.

**Features:**
- Visual preview before transfer
- Multiple transfer methods (nearest surface, ray cast, etc.)
- Transfer by vertex groups
- Smoothing iterations control
- Undo support for transfers

### 6.3 Symmetry Tools
**Priority: Medium**
Mirror operations for armor.

**Features:**
- Mirror CTC setup to other side
- Symmetrize weights
- Flip CTC constraints
- Auto-detect symmetric bones

---

## 7. Documentation & Help

### 7.1 Integrated Help
**Priority: Medium**
In-addon documentation.

**Features:**
- Tooltips with detailed explanations
- Help button opening relevant wiki page
- Quick start wizard for new users
- Video tutorial links in UI
- Searchable help panel

### 7.2 Templates & Examples
**Priority: Low**
Learning resources.

**Contents:**
- Example .blend files for each armor type
- Pre-configured export sets
- Tutorial scenes
- Common patterns library

---

## 8. Advanced Features

### 8.1 Scripting API
**Priority: Low**
Expose functionality to Python scripts.

```python
# Example API usage
import mhw_organizer

# Create export set programmatically
export_set = mhw_organizer.create_export_set(
    name="My Armor",
    armor_id="pl999_0000",
    part="body",
    gender="f"
)

# Add objects
for obj in bpy.context.selected_objects:
    mhw_organizer.add_to_export_set(export_set, obj)

# Export
mhw_organizer.export_set(export_set, types=['MOD3', 'CTC'])
```

### 8.2 Integration with External Tools
**Priority: Low**
Connect with other modding tools.

**Ideas:**
- Export directly to game folder with automatic backup
- Integration with texture editing tools
- Communicate with mesh optimization tools
- Export for previewing in model viewers

### 8.3 Collaboration Features
**Priority: Very Low**
Multi-user workflows.

**Features:**
- Export set sharing (import/export .json configs)
- Team library of reusable components
- Version control integration hints
- Conflict detection for shared files

---

## 9. Performance Optimizations

### 9.1 Lazy Loading
**Priority: Medium**
Don't load everything at once.

**Features:**
- Load external CTC sources on demand
- Lazy populate dropdowns
- Cache expensive operations
- Background loading of previews

### 9.2 Batch Processing
**Priority: Medium**
Optimize bulk operations.

**Features:**
- Multi-threaded export (if safe)
- Batch import with progress tracking
- Parallel validation checks
- Optimized collection operations

---

## 10. UI/UX Improvements

### 10.1 Panel Reorganization
**Priority: Low**
Make UI more intuitive.

**Ideas:**
- Tabbed interface for major sections
- Customizable panel layout
- Pin frequently used settings to top
- Collapsible advanced options
- Icon-based quick actions

### 10.2 Contextual UI
**Priority: Medium**
Show relevant options based on context.

**Features:**
- Hide irrelevant options based on armor part
- Show different options for MOD3 vs CTC export
- Adaptive UI based on external addons installed
- Beginner vs Advanced mode toggle

### 10.3 Keyboard Shortcuts
**Priority: Low**
Power user features.

**Shortcuts:**
- `Q` - Quick export active set
- `Shift+Q` - Batch export
- `Ctrl+Shift+A` - Add to active export set
- `Alt+E` - Export set menu (pie menu)
- `Ctrl+Alt+V` - Validate export set

---

## Implementation Priority

### Phase 1: Critical Improvements (Do First)
1. External tool version detection
2. Collections-based organization
3. Path management improvements
4. Validation & error checking
5. Weight transfer improvements

### Phase 2: High-Value Features
1. Asset browser integration
2. Quick actions & shortcuts
3. Preset system
4. Visual feedback enhancements
5. Search & filter

### Phase 3: Nice-to-Have
1. Drag & drop support
2. CTC visual helpers
3. Batch operations
4. Export profiles
5. Integrated help

### Phase 4: Advanced/Future
1. Geometry nodes support
2. Scripting API
3. Collaboration features
4. Advanced UI customization

---

## Questions to Research

Before implementing improvements, check:

1. **Mod3-MHW-Importer latest version:**
   - Repository: https://github.com/AsteriskAmpersand/Mod3-MHW-Importer
   - What's the latest version?
   - Any breaking API changes since 2019?
   - New features we should support?
   - Does it work with Blender 4.x?

2. **CTC-MHW-Editor latest version:**
   - Repository: https://github.com/AsteriskAmpersand/CTC-MHW-Editor
   - What's the latest version?
   - Any new physics parameters?
   - Does it work with Blender 4.x?

3. **MHW modding community:**
   - What are common pain points?
   - What features do modders request most?
   - Are there new modding techniques we should support?
   - Has Iceborne/Sunbreak added new requirements?

4. **Competing tools:**
   - What do other MHW modding tools offer?
   - Can we learn from their workflows?
   - Are there gaps we can fill?

---

## Backward Compatibility Considerations

When implementing improvements:

1. **Preserve existing .blend files:**
   - Don't break files made with current version
   - Provide migration path if data structure changes
   - Test with old files

2. **Gradual migration:**
   - Make new features opt-in initially
   - Deprecate old methods slowly
   - Provide warnings before removing features

3. **Documentation:**
   - Document changes clearly
   - Provide upgrade guide
   - Note breaking changes prominently

---

## Community Feedback

To prioritize these improvements:

1. Create GitHub discussion or poll
2. Ask MHW modding community which features they need
3. Track which issues/features get most requests
4. Do user testing with actual modders
5. Iterate based on feedback

---

## Conclusion

This is a comprehensive list of potential improvements. The actual implementation should be driven by:
- User needs and requests
- Compatibility with latest external tools
- Available development time
- Maintaining code quality and stability

Start with high-impact, low-complexity improvements (Phase 1) and expand from there based on feedback.
